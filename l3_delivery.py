"""Reproducible L3 evidence; no change to existing L1/L2 archives."""
import copy
import json
import platform
import subprocess
import sys
import zipfile
from argparse import Namespace
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from reproduce import ROOT,write_json,write_csv,verify_manifest,git_info
from l3 import analyse,validate,decision,SEED,NOISE_DRAWS,COORD


def result_payload(prior,a,commit):
    result=copy.deepcopy(prior)
    result['pipeline_commit']=commit
    result['L3']=dict(map=a['map'].tolist(),features=a['features'],
                      resolution_probe_pitch=a['resolution'],detection_limit_fraction=a['noise']['delta95'],
                      **{'pass':a['decision']['pass'],'confidence':a['decision']['confidence']})
    return result


def figures(out,a,repeats,group):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.fonttype':'none',
                         'svg.hashsalt':'QXU6028-L3','axes.spines.top':False,
                         'axes.spines.right':False,'legend.frameon':False})
    def save(fig,name):
        fig.savefig(out/(name+'.png'),dpi=220,metadata={'Software':'G05 L3 pipeline'})
        fig.savefig(out/(name+'.svg'),metadata={'Date':None})
        plt.close(fig)
    def heat(ax,m,title,limit=None):
        limit=float(np.max(abs(m))) if limit is None else limit
        im=ax.imshow(np.asarray(m).reshape(10,10),origin='lower',extent=(-3,3,-3,3),
                     interpolation='nearest',cmap='RdBu_r',vmin=-limit,vmax=limit)
        ax.set(xlabel='x (probe pitch)',ylabel='y (probe pitch)',title=title)
        return im
    fig,ax=plt.subplots(figsize=(7,6),layout='constrained')
    im=heat(ax,a['map'],f'{group} | L3 zero-mean reconstruction')
    fig.colorbar(im,ax=ax,label='Non-uniformity (fraction; supplied model scale)')
    for f,marker in zip(a['features'],['^','v']):
        ax.scatter(f['x_probe_pitch'],f['y_probe_pitch'],marker=marker,s=70,
                   facecolors='none',edgecolors='black',linewidths=1.2)
    extrema='; '.join(f"{f['sign']}: ({f['x_probe_pitch']:.1f}, {f['y_probe_pitch']:.1f}), {f['amplitude_fraction']:+.4f}"
                     for f in a['features'])
    fig.supxlabel(extrema+'\n'+a['decision']['status'].replace('_',' ').upper(),fontsize=9)
    save(fig,'L3_map')

    fig,axes=plt.subplots(2,2,figsize=(11,9),layout='constrained')
    ax=axes[0,0]
    ax.loglog([r['roughness'] for r in a['scan']],[r['residual'] for r in a['scan']],'o-',color='#255E78')
    for r in a['scan']:
        ax.annotate(f"{r['multiplier']:g}x",(r['roughness'],r['residual']),xytext=(5,5),textcoords='offset points',fontsize=8)
    ref=a['scan'][2]; ax.scatter(ref['roughness'],ref['residual'],marker='*',s=130,color='#B25827',zorder=3)
    ax.margins(.22); ax.set(xlabel='Roughness norm ||Lm||',ylabel='Residual norm ||Am - dmean||',
                          title='A | Regularisation sensitivity (star: reference)')
    ax=axes[0,1]
    ax.semilogy(np.arange(1,101),a['singular_values'],'-',color='#255E78')
    ax.set(xlabel='Singular-value index',ylabel='Singular value',title='B | Forward-matrix spectrum')
    limit=max(float(np.max(abs(p['response'][1]))) for p in a['psfs'])
    for ax,p,label in zip(axes[1],a['psfs'],['C','D']):
        row,col=p['position']; q,psf,width=p['response']
        im=heat(ax,psf,f'{label} | Injected ({COORD[col]:.1f}, {COORD[row]:.1f}); width {width:.3f}',limit)
        ax.scatter(COORD[col],COORD[row],marker='x',color='black',s=50)
        fig.colorbar(im,ax=ax,label='Point response (unit input)')
    fig.supxlabel('Widths: positive-weight moment-equivalent FWHM in probe pitches, not direct half-height measurements.',fontsize=9)
    save(fig,'L3_method')

    fig,axes=plt.subplots(1,2,figsize=(11,4.5),layout='constrained')
    ax=axes[0]; x=np.arange(128)
    for j,d in enumerate(repeats): ax.plot(x,d,alpha=.45,lw=.7,label=f'Repeat {j+1}')
    ax.errorbar(x,a['mean'],yerr=a['noise']['sigma'],fmt='.',ms=2,capsize=1,
                color='#255E78',elinewidth=.7,label='Mean +/- 1 sample SD')
    ax.set(xlabel='Channel index (0-based)',ylabel='Reading (supplied scale)',title='A | Three repeated scans')
    ax.legend(fontsize=8,loc='best')
    ax=axes[1]; ax.hist(a['noise']['maxima'],bins=25,color='#A8C7D4',edgecolor='white')
    ax.axvline(a['noise']['delta95'],color='#B25827',ls='--',label=f"95th percentile = {a['noise']['delta95']:.5f}")
    ax.set(xlabel='Maximum absolute noise-map amplitude (fraction)',ylabel='Simulation count',title='B | 500 noise-only reconstructions')
    ax.legend(fontsize=8)
    fig.supxlabel('SD: ddof=1 across 3 scans; simulation uses SD without division by sqrt(3). Not pixelwise confidence bars.',fontsize=9)
    save(fig,'L3_noise')


def run_l3(args):
    data=args.data_dir.resolve(); out=args.out.resolve()
    # Reject before creating files, including accidental overwrites of prior-phase archives.
    protected=[ROOT,ROOT/'outputs'/'L1',ROOT/'outputs'/'L2',ROOT/'outputs'/'archive']
    if (out==ROOT or out.is_relative_to(data) or data.is_relative_to(out)
            or out.is_relative_to(ROOT/'data')
            or any(out==p or out.is_relative_to(p) or p.is_relative_to(out) for p in protected[1:])):
        raise ValueError('L3 output must be separate from data and existing phase archives')
    threshold=getattr(args,'l3_threshold',None)
    decision(0,0,threshold)
    commit=git_info(); integrity=verify_manifest(data)
    meta=json.loads((data/'L3_meta.json').read_text(encoding='utf-8'))
    template=json.loads((data/'results_template.json').read_text(encoding='utf-8'))
    manifest=json.loads((data/'manifest.json').read_text(encoding='utf-8'))
    if any(len({obj[k] for obj in [meta,template,manifest]})!=1 for k in ['group','dataset_set']):
        raise ValueError('L3 group or dataset mismatch')
    if meta['npix']!=10 or meta['schema_version']!='QXU6028-data-v1':
        raise ValueError('Unsupported L3 geometry or schema')
    A=np.load(data/'L3_A.npy',allow_pickle=False)
    repeats=np.loadtxt(data/'L3_d.csv',delimiter=','); validate(A,repeats)
    print('L3: input checks passed; reconstructing and estimating resolution/noise.',flush=True)
    a=analyse(A,repeats,threshold)
    out.mkdir(parents=True,exist_ok=True)
    # Reuse the existing, unchanged L2 workflow in an isolated child output directory.
    from l2_delivery import run_l2
    prior_out=out/'prerequisites_L2'
    run_l2(Namespace(data_dir=data,out=prior_out))
    prior=json.loads((prior_out/'results.json').read_text(encoding='utf-8'))
    result=result_payload(prior,a,commit)
    checks=[]
    def check(name,value,limit):
        value=float(value); ok=bool(np.isfinite(value) and value<=limit)
        checks.append(dict(check=name,observed=value,upper_limit=limit,passed=ok))
        if not ok: raise ValueError(f'{name}: {value} exceeds {limit}')
    inv=a['inverse']; m=a['map']; noise=a['noise']
    check('A_row_sum',np.max(abs(A.sum(axis=1))),1e-11)
    check('gradient_shape',int(inv.L.shape!=(180,100)),0)
    check('gradient_constant_mode',np.max(abs(inv.L@np.ones(100))),1e-14)
    check('projector_idempotence',np.max(abs(inv.P@inv.P-inv.P)),1e-12)
    check('map_zero_mean',abs(m.mean()),1e-12)
    check('finite_map',np.count_nonzero(~np.isfinite(m)),0)
    check('map_length',abs(len(m)-100),0)
    check('zero_input',np.max(abs(inv.solve(np.zeros(128)))),1e-14)
    check('batch_vs_single',np.max(abs(inv.solve(noise['noise'][:3])-np.stack([inv.solve(d) for d in noise['noise'][:3]]))),1e-10)
    check('noise_maps_zero_mean',np.max(abs(noise['maps'].mean(axis=1))),1e-12)
    check('detection_percentile',abs(noise['delta95']-np.percentile(noise['maxima'],95)),0)
    check('L3_schema_keys',len(set(result['L3'])^set(template['L3'])),0)
    check('top_schema_keys',len(set(result)^set(template)),0)
    check('finite_positive_resolution',int(not (np.isfinite(a['resolution']) and a['resolution']>0)),0)
    summary=dict(group=meta['group'],eta=inv.eta,eta0=inv.eta0,eta_multiplier=1,
                 threshold=threshold,decision=a['decision'],amplitude_fraction=a['amplitude'],
                 detection_limit_fraction=noise['delta95'],resolution_probe_pitch=a['resolution'],
                 point_resolutions=[dict(row=p['position'][0],column=p['position'][1],
                                         equivalent_FWHM_probe_pitch=p['response'][2]) for p in a['psfs']],
                 mean_map=float(m.mean()),features=a['features'],noise_seed=SEED,noise_draws=NOISE_DRAWS,
                 sigma_min=float(noise['sigma'].min()),sigma_median=float(np.median(noise['sigma'])),sigma_max=float(noise['sigma'].max()),
                 chosen_residual=a['scan'][2]['residual'],chosen_roughness=a['scan'][2]['roughness'],
                 map_change_norms=[float(np.linalg.norm(r['map']-m)) for r in a['scan']],
                 submission_ready=a['decision']['pass'] is not None,
                 warning='Missing threshold or borderline decision is not a final Boolean submission.' if a['decision']['pass'] is None else '')
    write_json(out/'results.json',result); write_json(out/'summary.json',summary)
    write_json(out/'checks.json',checks); write_json(out/'input_integrity.json',integrity)
    write_csv(out/'L3_map.csv',[dict(row=i//10,column=i%10,x_probe_pitch=float(COORD[i%10]),y_probe_pitch=float(COORD[i//10]),amplitude_fraction=float(v)) for i,v in enumerate(m)])
    write_csv(out/'L3_channels.csv',[dict(channel=j,repeat_1=float(repeats[0,j]),repeat_2=float(repeats[1,j]),repeat_3=float(repeats[2,j]),mean=float(a['mean'][j]),sample_SD=float(noise['sigma'][j]),predicted=float((A@m)[j]),residual=float((A@m-a['mean'])[j])) for j in range(128)])
    write_csv(out/'L3_eta_scan.csv',[{k:v for k,v in r.items() if k!='map'} for r in a['scan']])
    write_csv(out/'L3_singular_values.csv',[dict(index=j+1,singular_value=float(v)) for j,v in enumerate(a['singular_values'])])
    write_csv(out/'L3_noise_maxima.csv',[dict(draw=j,max_abs_fraction=float(v)) for j,v in enumerate(noise['maxima'])])
    for name,array in [('L3_noise_vectors',noise['noise']),('L3_noise_maps',noise['maps']),
                       ('L3_eta_maps',np.stack([r['map'] for r in a['scan']])),
                       ('L3_point_inputs',np.stack([p['response'][0] for p in a['psfs']])),
                       ('L3_point_responses',np.stack([p['response'][1] for p in a['psfs']]))]:
        np.save(out/(name+'.npy'),array,allow_pickle=False)
    figures(out,a,repeats,meta['group'])
    note=f'''{meta['group']} L3 checkpoint — {a['decision']['status'].upper()}
{a['decision']['confidence']}

Method. Practical Methods Guide pp. 10-13: average three scans; project out
the constant map; use adjacent-pixel first differences and the prescribed
least-squares system with 1e-9 I. eta0={inv.eta0:.12g}; multiplier=1.
Five multipliers 0.01, 0.1, 1, 10, 100 are diagnostic, not a hidden tuning step.
Coordinates are pixel centres from -2.7 to 2.7 in probe pitches; row=y,
column=x, zero-based indices, row-major flattening. No absolute offset is
recoverable. Values retain the supplied model's fractional scale: no new
conversion from L1 or L2 is invented. Their results are recomputed for context.

Results. Maximum absolute map amplitude={a['amplitude']:.9g}.
Extrema (not an exhaustive list of independent defects):
{json.dumps(a['features'],indent=2)}
Residual norm={summary['chosen_residual']:.9g}; roughness={summary['chosen_roughness']:.9g}.
Map changes across the eta scan (Euclidean norm relative to reference):
{json.dumps(summary['map_change_norms'])}
Report sensitivity as a limitation; an attractive smooth map is not proof
that the true pattern or amplitudes have been recovered without bias.

Resolution. Inject unit pixels at (row,column)=(5,5) and (2,2), subtract
their mean, forward-model and invert with the real-data solver and eta.
On this coarse grid use the guide's positive-weight radial second moment:
sigma^2=sum(max(response,0)*r^2)/(2*sum(max(response,0))), width=2.355*sigma.
Widths={json.dumps(summary['point_resolutions'])}.
Conservative two-position equivalent FWHM={a['resolution']:.9g} probe pitches.
This is a moment-equivalent width, not a directly measured half-height
crossing, an isotropy proof, or a worst-case bound over every possible location.

Noise. Each of 128 SD estimates uses three repeats, ddof=1; min/median/max=
{summary['sigma_min']:.6g}/{summary['sigma_median']:.6g}/{summary['sigma_max']:.6g}.
Draw {NOISE_DRAWS} independent Gaussian channel-noise vectors, seed {SEED}.
Use repeat SD, NOT SD/sqrt(3), exactly as the guide prescribes. Invert all
vectors with the same solver and take the 95th percentile (linear method)
of max(abs(noise map)): delta95={noise['delta95']:.9g} fraction.
This is a global noise-only detection threshold, not a pixelwise 95% CI,
not a posterior pass probability, and not a correction for inversion bias.
Three repeats give limited noise information; channel correlations and
non-Gaussian errors are not represented by this prescribed simulation.

Decision. {a['decision']['confidence']}
For classroom threshold t use a+delta95<t for clear pass, a-delta95>t for
clear fail, otherwise borderline. Missing threshold or borderline leaves
pass=null, explicitly not the completed final-submission Boolean.

Figures. Map: nearest-pixel display with symmetric zero-centred colour scale;
triangles mark global extrema. Method: eta sensitivity, singular values and
two PSFs; crosses locate injected pixels. Noise: three raw scans and mean
+/-1 sample SD (n=3), plus the distribution of 500 global noise maxima.
SVG labels are editable; source data accompany the checkpoint directory.
Feature object keys are a documented project convention, not an asserted
teacher-specified inner schema. No contribution signatures are generated.

Reproduce: python reproduce.py --data-dir data/regular_G05 --phase L3
Add --l3-threshold VALUE only after receiving the actual classroom value.
Pipeline commit: {commit}
'''
    (out/'brief_note.txt').write_text(note,encoding='utf-8')
    zh=f'''# {meta['group']} L3 结果解读

状态：**{a['decision']['status']}**。课堂阈值未提供时，计算完成不等于合格判定完成，不能作为完整最终提交。

- 本图是相对于零均值的非均匀分布，无法恢复晶圆的整体偏移量。
- 主结果使用老师默认 eta={inv.eta:.9g}。五档参数的差异保存在敏感性表和地图数组，不根据图好看与否挑选参数。
- 最大绝对幅度：{a['amplitude']:.6g}（给定模型的 fraction 尺度）。
- 主要正负极值：{json.dumps(a['features'],ensure_ascii=False)}。坐标单位为探针间距，不是毫米；它们不代表已经识别全部真实缺陷。
- 两个注入位置的等效 FWHM：{[p['response'][2] for p in a['psfs']]}，取较大值 **{a['resolution']:.5f} 个探针间距**。
- 此宽度来自正权重二阶矩，是粗网格的等效分辨率，并非直接读出半高轮廓，也不是所有位置的最差上界。
- 500 次模拟的 95% 噪声检测限：**{noise['delta95']:.7f}**。随机种子 {SEED}，三次重复的样本标准差 ddof=1，不额外除以根号3。

原始扫描图的误差棒表示重复数据的标准差；95% 检测限表示整张噪声地图最大绝对值的分位数，不能解释为每个像素的置信区间。它也不包含平滑带来的偏差。独立高斯噪声及仅三次重复是分析限制。

判定：{a['decision']['confidence']}
收到老师阈值后才能比较幅度加减检测限与阈值，得到明确通过、明确不通过或临界。当前不能编造阈值，也不能将待定当成不合格。

L1/L2 在新输出内重新计算用于结果汇总，不改旧归档；指南未规定额外尺度换算，因此不擅自乘入 L1 修正或 L2 能隙。
源数据表、正则化地图、点响应、噪声样本和日志均已保留。版本：{commit}。
'''
    (out/'L3_readme_zh.md').write_text(zh,encoding='utf-8')
    (out/'commit_hash.txt').write_text(commit+'\n',encoding='ascii')
    (out/'STATUS.txt').write_text(a['decision']['confidence']+'\n',encoding='utf-8')
    import matplotlib
    write_json(out/'environment.json',dict(run_utc=datetime.now(timezone.utc).isoformat(),python=sys.version,
               numpy=np.__version__,matplotlib=matplotlib.__version__,platform=platform.platform(),executable=sys.executable,
               data_dir=str(data),command=[sys.executable,*sys.argv],noise_seed=SEED,noise_draws=NOISE_DRAWS))
    (out/'run_log.txt').write_text('\n'.join([f'Phase L3; commit {commit}',subprocess.list2cmdline([sys.executable,*sys.argv]),
                *[f"PASS {c['check']}: {c['observed']:.12g} <= {c['upper_limit']:.12g}" for c in checks],
                json.dumps(summary,ensure_ascii=False)])+'\n',encoding='utf-8')
    names=['results.json','brief_note.txt','commit_hash.txt','STATUS.txt','L3_readme_zh.md','summary.json']
    names += [stem+'.'+ext for stem in ['L3_map','L3_method','L3_noise'] for ext in ['png','svg']]
    bundle_path=out/f"{meta['group']}_L3_Checkpoint.zip"
    with zipfile.ZipFile(bundle_path,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for name in names:
            info=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,(out/name).read_bytes())
    with zipfile.ZipFile(bundle_path) as z:
        if z.testzip() is not None or json.loads(z.read('results.json'))!=result:
            raise ValueError('L3 ZIP validation failed')
    print(json.dumps(summary,indent=2),flush=True)

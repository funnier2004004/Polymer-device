"""L2 evidence, figures and submission package built only from raw course inputs."""
import hashlib
import json
import platform
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
from l1 import KB, count, mobility
from l2 import load_pairs, normalize, transport, model_library, fit, bootstrap, SEED, BOOTSTRAPS
from reproduce import ROOT, git_info, verify_manifest, write_json, write_csv


def ef_plot_data(indices, pairs, central, library):
    """One shared inferred EF per measured pair; never fit either channel alone."""
    return dict(indices=np.asarray(indices), ef=central['trajectory'], xy=central['xy'],
                sd=pairs.std(axis=1,ddof=1)/central['scales'],
                predicted=library['xy'][central['selected'],central['assigned']])


def figures(out, indices, pairs, central, library, boot, brackets, group):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,
                         'axes.spines.top':False,'axes.spines.right':False,
                         'svg.fonttype':'none','svg.hashsalt':'QXU6028-L2','legend.frameon':False})
    mean,sd = pairs.mean(axis=1),pairs.std(axis=1,ddof=1)
    low,median,high = boot['trajectory_percentiles']
    ef_data = ef_plot_data(indices,pairs,central,library)
    def raw(ax, channel):
        for r,colour in enumerate(('#A5B7C2','#BCC6AE','#D5B8A4')):
            ax.plot(indices,pairs[:,r,channel],'.-',ms=3,lw=.7,color=colour,label=f'Repeat {r+1}')
        ax.errorbar(indices,mean[:,channel],yerr=sd[:,channel],fmt='o-',ms=2.5,lw=1,
                    capsize=2,color='#255E78',label='Mean +/- 1 sample SD')
        if channel == 0:
            ax.axhline(0,color='#555555',lw=.8)
            for left,right in brackets:
                ax.axvspan(left,right,color='#DBB75E',alpha=.35)
        ax.set(xlabel='Measurement index',ylabel=('$R_H$' if channel==0 else '$R_s$')+' (supplied scale)')
        ax.ticklabel_format(axis='y',style='sci',scilimits=(0,0))
        ax.legend(fontsize=7.5,loc='best')
    def model(ax):
        for j,colour,style in [(0,'#7D8790','--'),(central['best_gap'],'#AA582D','-')]:
            label='Cone' if j==0 else f'Best hard-gap: {library["gaps"][j]:g} kBT'
            ax.plot(*library['xy'][j].T,style,color=colour,lw=1.8,label=label)
        ax.scatter(*central['xy'].T,s=19,facecolors='white',edgecolors='#235F7C',zorder=3,label='Mean measured pairs')
        ax.axvline(0,color='#CCCCCC',lw=.7,zorder=0)
        ax.set(xlabel=r'Normalized $R_H$',ylabel=r'Normalized $R_s$',xlim=(-1.08,1.08),ylim=(0,1.10))
        ax.legend(fontsize=8,loc='center',bbox_to_anchor=(.5,.44))
        ax.text(.5,.72,f'Selected: {central["model"]}\nRMS cone = {central["residuals"][0]:.5f}\nRMS gap = {central["residuals"][central["best_gap"]]:.5f}',
                transform=ax.transAxes,va='center',ha='center',fontsize=8,
                bbox=dict(facecolor='white',alpha=.85,edgecolor='none',pad=2))
    def trajectory(ax):
        ax.fill_between(indices,low,high,color='#A8C7D4',alpha=.7,label='Bootstrap 16-84% interval')
        ax.plot(indices,central['trajectory'],'o-',color='#255E78',lw=1.4,ms=3,label='Fit to repeat means')
        ax.axhline(0,color='#999999',lw=.8,ls='--')
        ax.set(xlabel='Measurement index',ylabel=r'Assigned $E_F$ (eV)')
        ax.legend(fontsize=8,loc='best')
    def save(fig,name):
        fig.savefig(out/f'{name}.png',dpi=220,metadata={'Software':'G05 L2 pipeline'})
        fig.savefig(out/f'{name}.svg',metadata={'Date':None})
        plt.close(fig)
    def channel_vs_ef(ax, channel):
        selected = central['selected']
        symbol = r'$R_H$' if channel == 0 else r'$R_s$'
        ax.plot(library['ef'],library['xy'][selected,:,channel],color='#AA582D',lw=1.7,
                label=f'Selected {central["model"]} model')
        ax.errorbar(ef_data['ef'],ef_data['xy'][:,channel],yerr=ef_data['sd'][:,channel],
                    fmt='o',ms=3.5,mfc='white',mec='#255E78',ecolor='#255E78',
                    elinewidth=.8,capsize=2,label='Measured mean +/- scaled sample SD',zorder=3)
        ax.axvline(0,color='#BBBBBB',lw=.7,ls='--',zorder=0)
        if channel == 0:
            ax.axhline(0,color='#BBBBBB',lw=.7,zorder=0)
        ax.set(xlabel=r'$E_F$ (eV; inferred for measured points)',ylabel='Normalized '+symbol)
        ax.legend(fontsize=7.5,loc='best')
    fig,axes = plt.subplots(2,2,figsize=(11.6,8.8),layout='constrained')
    raw(axes[0,0],0); raw(axes[0,1],1); model(axes[1,0]); trajectory(axes[1,1])
    for ax,title in zip(axes.flat,['A  Hall channel and neutrality','B  Sheet-resistance channel',
                                  'C  Joint model comparison','D  Fermi-level trajectory']):
        ax.set_title(title,loc='left',fontweight='bold',fontsize=11,pad=14)
    fig.suptitle(f'{group} | L2 paired transport inference',fontsize=15)
    save(fig,'L2_four_panel')
    for name,draw,title in [('L2_model',model,'Joint transport model comparison'),
                            ('L2_trajectory',trajectory,'Fermi-level trajectory')]:
        fig,ax = plt.subplots(figsize=(7.2,5),layout='constrained')
        draw(ax); ax.set_title(f'{group} | {title}',pad=14)
        save(fig,name)
    for channel,name in [(0,'L2_RH_vs_EF'),(1,'L2_Rs_vs_EF')]:
        fig,ax=plt.subplots(figsize=(7.2,5.4),layout='constrained')
        channel_vs_ef(ax,channel)
        ax.set_title(f'{group} | '+('Hall coefficient' if channel==0 else 'Sheet resistance')+' versus Fermi level',pad=14)
        fig.supxlabel('Measured-point EF is inferred jointly from RH and Rs; not an independent validation.',fontsize=8)
        save(fig,name)
    fig,axes=plt.subplots(3,2,figsize=(11.6,13.2),layout='constrained')
    raw(axes[0,0],0); raw(axes[0,1],1); model(axes[1,0]); trajectory(axes[1,1])
    channel_vs_ef(axes[2,0],0); channel_vs_ef(axes[2,1],1)
    titles=['A  Hall channel and neutrality','B  Sheet-resistance channel',
            'C  Joint model comparison','D  Fermi-level trajectory',
            'E  Hall channel versus Fermi level','F  Sheet resistance versus Fermi level']
    for ax,title in zip(axes.flat,titles):
        ax.set_title(title,loc='left',fontweight='bold',fontsize=11,pad=14)
    fig.suptitle(f'{group} | L2 joint fit and Fermi-level comparison',fontsize=15)
    fig.supxlabel('E/F: shared inferred EF for measured pairs; scaled sample SD only; not independent validation.',fontsize=9)
    save(fig,'L2_six_panel')


def run_l2(args):
    data,out = args.data_dir.resolve(),args.out.resolve()
    if out==ROOT or data.is_relative_to(out) or out.is_relative_to(data) or out.is_relative_to(ROOT/'data') or out.is_relative_to(ROOT/'outputs'/'L1'):
        raise ValueError('L2 output must be separate from raw inputs and archived L1 outputs')
    commit = git_info()
    integrity = verify_manifest(data)
    meta = json.loads((data/'L2_meta.json').read_text(encoding='utf-8'))
    params = json.loads((data/'L1_params.json').read_text(encoding='utf-8'))
    result = json.loads((data/'results_template.json').read_text(encoding='utf-8'))
    manifest = json.loads((data/'manifest.json').read_text(encoding='utf-8'))
    for key in ('group','dataset_set'):
        if len({obj[key] for obj in (meta,params,result,manifest)}) != 1:
            raise ValueError(f'Input {key} mismatch')
    if meta['schema_version'] != 'QXU6028-data-v1' or result['schema_version'] != 'QXU6028-results-v1':
        raise ValueError('Unsupported schema')
    indices,pairs = load_pairs(data/'L2_data.csv')
    temperature = float(meta['T_K'])
    mean,sd = pairs.mean(axis=1),pairs.std(axis=1,ddof=1)
    brackets = [[int(indices[j]),int(indices[j+1])] for j in range(len(indices)-1) if mean[j,0]*mean[j+1,0] < 0]
    exact_zero = indices[mean[:,0]==0].tolist()
    if not brackets and not exact_zero:
        raise ValueError('No Hall neutrality crossing in measured means; investigate before fitting')
    print('L2: verified paired repeats and raw Hall sign change.',flush=True)
    library = model_library(temperature)
    central = fit(mean,library)
    print('L2: candidate curves fitted; running 200 paired bootstrap draws.',flush=True)
    boot = bootstrap(pairs,library)
    q16,q50,q84 = map(float,boot['gap_percentiles'])
    selected,best = central['selected'],central['best_gap']
    rcone,rgap = float(central['residuals'][0]),float(central['residuals'][best])
    improvement = 1-rgap/rcone if rcone>0 else 0.
    trajectory_q = boot['trajectory_percentiles']
    warnings = []
    if .4 <= boot['hard_gap_fraction'] <= .6:
        warnings.append('Model selection is unstable under repeat resampling (hard-gap frequency near 0.5).')
    if library['gaps'][best] in (.5,8.):
        warnings.append('The best hard-gap candidate is on the gap-grid boundary.')
    edge_count = int(np.sum((central['assigned']==0)|(central['assigned']==len(library['ef'])-1)))
    if edge_count:
        warnings.append(f'{edge_count} mean-fit EF assignments lie at the EF-grid boundary.')
    if central['gap_kT'] < 1:
        warnings.append('A sub-thermal gap is not resolved by the prescribed selection rule; cone does not prove exactly zero gap.')
    warnings.append('Bootstrap frequencies are resampling stability measures, not posterior probabilities or proof of model correctness.')
    checks = []
    def check(name,value,limit=0.):
        value=float(value)
        ok=bool(np.isfinite(value) and value<=limit)
        checks.append(dict(check=name,observed=value,upper_limit=limit,passed=ok))
        if not ok: raise ValueError(f'{name}: {value} exceeds {limit}')
    xy,scales = normalize(mean)
    check('normalized_sign_changes_preserved',np.count_nonzero(np.sign(xy[:,0])!=np.sign(mean[:,0])))
    check('RH_max_abs',abs(np.max(np.abs(xy[:,0]))-1),1e-14)
    check('Rs_max',abs(np.max(xy[:,1])-1),1e-14)
    check('trajectory_length',abs(len(central['trajectory'])-len(indices)))
    check('finite_trajectory',np.count_nonzero(~np.isfinite(central['trajectory'])))
    check('bootstrap_pairs_preserved',np.max(np.abs(boot['sampled_pairs']-pairs[np.arange(len(indices))[None,:],boot['draws']])))
    for gap in (0.,1.,5.,8.):
        rh,rs,n,p = transport(np.array([-.08,0.,.08]),temperature,gap)
        check(f'population_symmetry_gap_{gap}',np.max(np.abs(n/p[::-1]-1)),1e-10)
        check(f'RH_odd_gap_{gap}',abs((rh[0]+rh[-1])/rh[-1]),1e-10)
        check(f'Rs_even_gap_{gap}',abs(rs[0]/rs[-1]-1),1e-10)
        check(f'neutrality_gap_{gap}',abs((p[1]-n[1])/(p[1]+n[1])),1e-10)
    ef,t,c,rho = [params[k] for k in ('EF_op_eV','T','c','rho_ohm_sq')]
    nf=count(ef,t,c,fermi_referenced=True); nb=count(ef,t,c,fermi_referenced=False)
    result['L1']=dict(correction_factor=nb/nf,n_fermi_op_cm2=nf,mobility_corrected_cm2_Vs=mobility(nf,rho))
    result['L2']=dict(model=central['model'],Eg_kT=central['gap_kT'],Eg_uncertainty_kT=(q84-q16)/2,
                      EF_trajectory_eV=central['trajectory'].tolist())
    result['pipeline_commit']=commit
    template = json.loads((data/'results_template.json').read_text())
    check('schema_L2_keys',len(set(result['L2'])^set(template['L2'])))
    check('L3_left_unfilled',int(result['L3']!=template['L3']))
    summary = dict(group=meta['group'],temperature_K=temperature,measurement_count=len(indices),
                   repeat_count=3,neutrality_brackets=brackets,exact_zero_indices=exact_zero,
                   normalization_scales=scales.tolist(),model=central['model'],Eg_kT=central['gap_kT'],
                   Eg_eV=central['gap_kT']*KB*temperature,cone_residual=rcone,best_gap_residual=rgap,
                   best_gap_candidate_kT=float(library['gaps'][best]),relative_residual_improvement=improvement,
                   bootstrap_seed=SEED,bootstrap_count=BOOTSTRAPS,gap_p16_kT=q16,gap_median_kT=q50,gap_p84_kT=q84,
                   Eg_uncertainty_kT_convention='Half width of bootstrap [16th,84th] percentile interval; project convention.',
                   hard_gap_selection_fraction=boot['hard_gap_fraction'],EF_min_eV=float(central['trajectory'].min()),
                   EF_max_eV=float(central['trajectory'].max()),EF_boundary_assignment_count=edge_count,
                   EF_grid_step_eV=float(library['ef'][1]-library['ef'][0]),gap_grid_step_kT=.25,warnings=warnings)
    out.mkdir(parents=True,exist_ok=True)
    for name,value in [('results',result),('input_integrity',integrity),('checks',checks),('L2_summary',summary)]:
        write_json(out/f'{name}.json',value)
    rows=[]
    for j,i in enumerate(indices):
        rows.append(dict(measurement_index=int(i),RH_mean=mean[j,0],RH_sample_SD=sd[j,0],
                         Rs_mean=mean[j,1],Rs_sample_SD=sd[j,1],RH_normalized=xy[j,0],Rs_normalized=xy[j,1],
                         nearest_model_index=int(central['assigned'][j]),distance=central['distances'][j],
                         EF_eV=central['trajectory'][j],EF_p16_eV=trajectory_q[0,j],EF_median_eV=trajectory_q[1,j],EF_p84_eV=trajectory_q[2,j]))
    write_csv(out/'L2_pairs_and_trajectory.csv',rows)
    ef_data=ef_plot_data(indices,pairs,central,library)
    write_csv(out/'L2_EF_comparison.csv',[
        dict(measurement_index=int(i),EF_inferred_eV=ef_data['ef'][j],
             RH_normalized=ef_data['xy'][j,0],Rs_normalized=ef_data['xy'][j,1],
             RH_normalized_sample_SD=ef_data['sd'][j,0],Rs_normalized_sample_SD=ef_data['sd'][j,1],
             RH_model_at_assigned_EF=ef_data['predicted'][j,0],
             Rs_model_at_assigned_EF=ef_data['predicted'][j,1]) for j,i in enumerate(indices)])
    write_csv(out/'L2_residual_scan.csv',[dict(model='cone' if j==0 else 'hard_gap',Eg_kT=float(gap),
              rms=float(central['residuals'][j]),selected=j==selected) for j,gap in enumerate(library['gaps'])])
    curve_rows=[]
    for j,gap in enumerate(library['gaps']):
        for k,x in enumerate(library['ef']):
            rh,rs,n,p=library['raw'][j,k]
            curve_rows.append(dict(model='cone' if j==0 else 'hard_gap',Eg_kT=gap,EF_eV=x,n=n,p=p,
                                   RH_model_scale=rh,Rs_model_scale=rs,RH_normalized=library['xy'][j,k,0],Rs_normalized=library['xy'][j,k,1]))
    write_csv(out/'L2_model_library.csv',curve_rows)
    draw_rows=[]
    for b in range(BOOTSTRAPS):
        for j,i in enumerate(indices):
            draw_rows.append(dict(bootstrap=b,measurement_index=int(i),repeat=int(boot['draws'][b,j])+1,
                RH_raw=boot['sampled_pairs'][b,j,0],Rs_raw=boot['sampled_pairs'][b,j,1],
                EF_eV=boot['trajectories'][b,j],Eg_kT=boot['gaps'][b],model='hard_gap' if boot['selected'][b] else 'cone'))
    write_csv(out/'L2_bootstrap_draws.csv',draw_rows)
    write_json(out/'L2_bootstrap_residuals.json',dict(seed=SEED,gaps_kT=library['gaps'].tolist(),
              residuals=boot['residuals'].tolist(),selected_model_indices=boot['selected'].tolist()))
    figures(out,indices,pairs,central,library,boot,brackets,meta['group'])
    device = ('The resolved hard gap supports considering switching applications relative to an ideal cone, but '
              'these transport fits alone do not demonstrate an on/off ratio, contact performance or a working transistor.'
              if selected else 'The cone selection is consistent with sensor/interconnect consideration; it does not prove high '
              'sensitivity or rule out a sub-thermal gap. A switching claim needs additional evidence.')
    note=f'''{meta['group']} L2 checkpoint: joint Hall and sheet-resistance inference

Question and source. Which of the prescribed cone and symmetric hard-gap V
models describes the paired transport series? Methods: Practical Methods Guide
pp. 6-9; outputs and interpretation: Assessment Brief pp. 3-4. RH and Rxx_raw
(treated as the Rs channel in the guide) are supplied simulated measurements.

Data and method. There are {len(indices)} measurement indices with three paired
repeats each, at {temperature:g} K. The raw mean Hall sign changes in {brackets}.
Average by index, retain sample SD (ddof=1), then normalize RH by max(abs(RH))
and Rs by max(Rs) separately. Preserve the RH sign and measurement order.
The guide defines n by integrating g*f above EF and p by integrating g*(1-f)
below EF. RH=(p-n)/(e*(p+n)^2), Rs=1/(e*mu*(p+n)). Use e=mu=c=1 in the
model library; fixed scale factors cancel during separate normalization.
No L1 correction factor is multiplied into normalized L2 channels.
Energy grid: -2.5 to 2.5 eV, 4,000 points. EF grid: -8 to +9 kBT, 400 points.
Cone gap=0; hard-gap grid=0.50 to 8.00 kBT, increment=0.25 kBT.
Match each normalized pair to the nearest point on each complete normalized
model curve. No sorting by Hall value, smoothing or manual trajectory edits.

Mean-fit result. Cone RMS={rcone:.9f}; best hard-gap RMS={rgap:.9f}; improvement
relative to cone={100*improvement:.3f}%. Best hard-gap candidate={library['gaps'][best]:.2f} kBT.
Select hard-gap only if its RMS is strictly below 0.85*cone RMS and gap>=1 kBT.
Selected model={central['model']}; central Eg={central['gap_kT']:.2f} kBT
({summary['Eg_eV']:.8f} eV at {temperature:g} K). Assigned EF ranges from
{summary['EF_min_eV']:.8f} to {summary['EF_max_eV']:.8f} eV.

Uncertainty. Following the guide, independently draw one whole paired repeat
at each index, renormalize, and refit with the same selection rule; 200 draws,
NumPy default_rng seed={SEED}. Selected-gap median={q50:.2f} kBT;
16th-84th percentile interval=[{q16:.2f}, {q84:.2f}] kBT.
Hard-gap selection frequency={boot['hard_gap_fraction']:.3f}.
Eg_uncertainty_kT={(q84-q16)/2:.3f} means HALF the interval width, a documented
project convention because the supplied template does not define that field's
type or statistical meaning. The full endpoints and median are saved separately.
Central JSON values come from the repeat-mean fit, not the bootstrap median.
Pointwise EF bands are 16th-84th bootstrap percentiles, not simultaneous bands.

Limits. Model and gap-grid assumptions, normalization and discretization can
cause systematic uncertainty beyond repeat resampling. The gap increment is
0.25 kBT; EF grid spacing={summary['EF_grid_step_eV']:.8f} eV. A narrow interval
must not be read as greater resolution than the candidate grid. There are
{edge_count} central EF assignments at an EF boundary.
{' '.join(warnings)}

Device implication. {device}

Figures. A/B: three raw repeated series, means and +/-1 sample SD; Hall zero
line and mean sign-change bracket. C: separately normalized paired means,
cone and best hard-gap model, with the selected model and residuals identified.
D: EF assigned to repeat means and pointwise bootstrap 16th-84th interval.
Additional E/F panels (also exported separately): normalized RH and Rs versus
EF with the selected model curve and measured means at the SAME jointly
inferred EF for each measurement pair. Vertical bars are sample SD divided
by the corresponding fixed mean-data normalization scale, not confidence
intervals and not uncertainty in that normalization factor. EF uncertainty
is shown in panel D. The measured-point EF values are inferred, not independently
measured; these panels explain the joint fit and are not independent validation.
The four-panel original is retained alongside the expanded six-panel summary.
Small model-curve kinks from the prescribed discrete integration masks are
retained without smoothing; they are not claimed as new material features.
Raw-channel axes use the supplied scale; physical units were not specified
in the data metadata and are not invented. All source values are retained.

Reproduce: python reproduce.py --data-dir data/regular_G05 --phase L2
Pipeline commit: {commit}
L1 is recomputed in this JSON; the previously archived L1 package is untouched.
L3 remains unfilled. AI use is disclosed in records/ai_usage_log.md; students
must review the physics and record their own contributions before submission.
'''
    (out/'brief_note.txt').write_text(note,encoding='utf-8')
    cn=f'''# G05 L2 结果解读

本次按老师第 6–9 页的方法，从 RH/Rs 成对模拟测量反推材料模型。51 个测量序号各有 3 次重复。

四幅图的读法：A 看霍尔系数变号和重复波动；B 看方块电阻变化；C 用两种归一化模型曲线同时解释两个通道；D 读取反推出的费米能级轨迹。

新增 E/F 两幅图把选定模型的 RH(EF)、Rs(EF) 理论曲线分别与测量均值叠加。同一测量序号的两个通道使用完全相同的联合推断 EF，没有分别重新拟合。横轴上测量点的 EF 不是独立测得的，不能把吻合当成新的独立验证。纵向误差条为样本标准差除以对应的固定归一化尺度，不包含归一化因子本身的不确定性，也不是置信区间；EF 不确定性见 D 图。两张单图和六面板总图均已输出，原四面板图保留。数据表 L2_EF_comparison.csv 保存每个点的共同 EF、归一化均值、标准差与匹配模型预测值。

平均 RH 变号区间：{brackets}。cone 残差 {rcone:.6f}，最佳 hard-gap 残差 {rgap:.6f}，改善 {improvement*100:.2f}%。按老师规则选择 **{central['model']}**，平均数据拟合得到 **Eg={central['gap_kT']:.2f} kBT={summary['Eg_eV']*1000:.3f} meV**。

200 次成对重复抽样采用固定种子 {SEED}，hard-gap 选择比例 {boot['hard_gap_fraction']*100:.1f}%；gap 中位数 {q50:.2f} kBT，16–84% 区间 [{q16:.2f}, {q84:.2f}] kBT。JSON 的 Eg_uncertainty_kT={(q84-q16)/2:.3f} 是该区间半宽，并非“最佳值上下各加减它”就能恢复原区间；完整端点见 summary。主结果仍取重复均值拟合。

EF 轨迹范围 {summary['EF_min_eV']:.6f} 到 {summary['EF_max_eV']:.6f} eV。图中误差条是原始重复的样本标准差；轨迹色带是 bootstrap 16–84% 分位区间，二者含义不同。

模型选择频率不是真实模型的后验概率。以上判断仅在老师给定的 cone/hard-gap 候选及相同迁移率形式内成立。能隙网格步长 0.25 kBT；重复测量不能量化模型错误及全部系统误差。{'存在明确能隙，支持进一步考虑开关用途；尚不能据此证明真实晶体管的开关比或性能。' if selected else '结果支持无隙模型，但不排除小于热尺度的能隙；器件用途仍需其他证据。'}

L1 与 L2 沿用课程的费米窗口定义；L2 单独归一化消除了固定比例因子，因此没有把 L1 修正系数再乘到 RH 或 Rs 上。原始通道单位未被材料明确给出，图中只注明 supplied scale。

结果、曲线、抽样和检查全部来自代码，未读取隐藏真值。当前 commit 为 `{commit}`。原 L1 checkpoint 的哈希保持不变，L2 使用新代码版本。成员贡献与签字仍需本人审核和补充。
'''
    (out/'L2_readme_zh.md').write_text(cn,encoding='utf-8')
    (out/'commit_hash.txt').write_text(commit+'\n',encoding='ascii')
    import matplotlib
    write_json(out/'environment.json',dict(run_utc=datetime.now(timezone.utc).isoformat(),python=sys.version,
               numpy=np.__version__,matplotlib=matplotlib.__version__,platform=platform.platform(),
               command=[sys.executable,*sys.argv],data_dir=str(data),bootstrap_seed=SEED))
    log=[f'Phase=L2 group={meta["group"]} commit={commit}',
         'Command: '+subprocess.list2cmdline([sys.executable,*sys.argv]),f'Input integrity: {len(integrity)} files passed',
         *[f'PASS {r["check"]}: {r["observed"]} <= {r["upper_limit"]}' for r in checks],
         f'Selected={central["model"]} Eg_kT={central["gap_kT"]}',
         f'Bootstrap={BOOTSTRAPS} seed={SEED}; hard_gap_fraction={boot["hard_gap_fraction"]}',
         *['LIMITATION: '+s for s in warnings],'Completed successfully']
    (out/'run_log.txt').write_text('\n'.join(log)+'\n',encoding='utf-8')
    names=['results.json','brief_note.txt','commit_hash.txt','L2_EF_comparison.csv']+[f'{stem}.{ext}' for stem in ('L2_model','L2_trajectory','L2_four_panel','L2_RH_vs_EF','L2_Rs_vs_EF','L2_six_panel') for ext in ('png','svg')]
    archive=out/f'{meta["group"]}_L2_Checkpoint.zip'
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as bundle:
        for name in names:
            info=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED
            bundle.writestr(info,(out/name).read_bytes())
    with zipfile.ZipFile(archive) as bundle:
        if bundle.testzip() is not None or json.loads(bundle.read('results.json'))!=result:
            raise ValueError('L2 checkpoint verification failed')
    print(json.dumps(dict(model=central['model'],Eg_kT=central['gap_kT'],gap_interval=[q16,q84],
                         checks=len(checks),checkpoint=str(archive)),indent=2))

"""All-phase report generation and explicitly invoked blind-run interface."""
import json
import shutil
from argparse import Namespace
from pathlib import Path
import numpy as np
from reproduce import ROOT,git_info,verify_manifest,write_json,write_csv


def configuration(threshold=None):
    config=json.loads((ROOT/'course_config.json').read_text(encoding='utf-8'))
    if threshold is not None:
        config['l3_threshold']=threshold; config['threshold_source']='Explicit --l3-threshold override'
    from l3 import decision
    decision(0,0,config['l3_threshold'])
    return config


def eta_diagnostics(a,repeats,threshold):
    from l3 import Inverse,decision
    expected=float(np.linalg.norm(a['noise']['sigma'])/np.sqrt(3))
    rows=[]
    for candidate in a['scan']:
        inv=Inverse(a['inverse'].A,candidate['eta'])
        maximum=float(np.max(abs(candidate['map'])))
        delta=float(np.percentile(np.max(abs(inv.solve(a['noise']['noise'])),axis=1),95))
        rows.append(dict(multiplier=candidate['multiplier'],eta=candidate['eta'],amplitude=maximum,
                         residual=candidate['residual'],roughness=candidate['roughness'],
                         residual_to_mean_noise=candidate['residual']/expected if expected>0 else None,
                         map_change_norm=float(np.linalg.norm(candidate['map']-a['map'])),delta95=delta,
                         decision=decision(maximum,delta,threshold)['status']))
    return rows


def validate_blind(data):
    for name in ['manifest.json','results_template.json','L1_params.json','L2_meta.json','L3_meta.json']:
        path=data/name
        if not path.is_file(): raise ValueError(f'Missing blind input: {name}')
        obj=json.loads(path.read_text(encoding='utf-8'))
        if obj.get('group')!='G05' or obj.get('dataset_set')!='blind':
            raise ValueError('Blind mode accepts only G05 blind data')


def run_all(args):
    from reproduce import run
    from l3_delivery import run_l3
    out=args.out.resolve()
    if out.exists(): raise ValueError('Use a new empty output path to preserve previous evidence')
    config=configuration(args.l3_threshold)
    if hasattr(args,'threshold_source'): config['threshold_source']=args.threshold_source
    # L3 guards data/archive targets before it creates any files.
    run_l3(Namespace(data_dir=args.data_dir,out=out/'L3',l3_threshold=config['l3_threshold'],
                     threshold_source=config['threshold_source']))
    run(Namespace(data_dir=args.data_dir,out=out/'L1'))
    shutil.copytree(out/'L3/prerequisites_L2',out/'L2')
    for name in ['results.json','commit_hash.txt','run_log.txt']:
        shutil.copy2(out/'L3'/name,out/name)
    write_json(out/'configuration.json',config)
    (out/'REVISION_NOTE.txt').write_text(
        'L1: carrier-density plot added; original numbers unchanged.\n'
        'L2: thermal smoothing and device interpretation expanded; original inference unchanged.\n'
        'L3: actual classroom threshold 0.030 applied; default eta0 retained.\n'
        'Eta sensitivity uses candidate-specific noise propagation. Low noise limits exclude smoothing bias.\n'
        'L1/L2/L3 links are conceptual unless an explicit numerical dependency is implemented.\n'
        'Historical packages and real blind submission records remain separate.\n',encoding='utf-8')


def run_blind(args):
    out=args.out.resolve()
    if out.exists(): raise ValueError('Blind output must be new: never overwrite a historical run')
    validate_blind(args.data_dir.resolve()); verify_manifest(args.data_dir.resolve())
    commit=git_info()
    run_all(args)
    payload=json.loads((out/'results.json').read_text(encoding='utf-8'))
    if payload['pipeline_commit']!=commit: raise ValueError('Blind commit mismatch')
    write_json(out/'blind_results.json',payload)
    (out/'pipeline_commit.txt').write_text(commit+'\n',encoding='ascii')
    with (out/'run_log.txt').open('a',encoding='utf-8') as handle:
        handle.write('Explicit blind interface run; no upload or QMplus timestamp implied.\n')

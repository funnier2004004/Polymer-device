"""Audit this G05 display-only revision against the preserved local previous release."""
import csv
import hashlib
import json
from pathlib import Path
import numpy as np
from reproduce import ROOT, write_json


def main():
    old=ROOT/'outputs/archive/L2_6299ffe15dc8/L2'
    new=ROOT/'outputs/L2'
    def read(root,name): return json.loads((root/name).read_text(encoding='utf-8'))
    def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
    old_result,new_result=read(old,'results.json'),read(new,'results.json')
    old_commit=old_result.pop('pipeline_commit'); new_commit=new_result.pop('pipeline_commit')
    checks={'result_fields_unchanged':old_result==new_result,
            'summary_unchanged':read(old,'L2_summary.json')==read(new,'L2_summary.json')}
    unchanged=['L2_bootstrap_draws.csv','L2_bootstrap_residuals.json','L2_residual_scan.csv',
               'L2_pairs_and_trajectory.csv','L2_model_library.csv','checks.json','input_integrity.json',
               'L2_four_panel.png','L2_four_panel.svg','L2_model.png','L2_model.svg',
               'L2_trajectory.png','L2_trajectory.svg']
    comparisons=[dict(file=name,old_sha256=sha(old/name),new_sha256=sha(new/name),
                      identical=sha(old/name)==sha(new/name)) for name in unchanged]
    with (new/'L2_EF_comparison.csv').open(encoding='utf-8',newline='') as f: rows=list(csv.DictReader(f))
    with (new/'L2_pairs_and_trajectory.csv').open(encoding='utf-8',newline='') as f: source=list(csv.DictReader(f))
    with (new/'L2_model_library.csv').open(encoding='utf-8',newline='') as f: models=list(csv.DictReader(f))
    scales=read(new,'L2_summary.json')['normalization_scales']
    model=new_result['L2']['model']; gap=new_result['L2']['Eg_kT']
    selected=[r for r in models if r['model']==model and float(r['Eg_kT'])==gap]
    checks['all_51_measurements_present']=len(rows)==len(source)==51
    checks['shared_EF_matches_joint_fit']=all(float(r['EF_inferred_eV'])==ef and r['measurement_index']==s['measurement_index']
        for r,s,ef in zip(rows,source,new_result['L2']['EF_trajectory_eV']))
    checks['measured_means_and_scaled_SD_correct']=all(
        float(r[f'{channel}_normalized'])==float(s[f'{channel}_normalized']) and
        np.isclose(float(r[f'{channel}_normalized_sample_SD']),float(s[f'{channel}_sample_SD'])/scales[k],rtol=1e-14,atol=0)
        for r,s in zip(rows,source) for k,channel in enumerate(('RH','Rs')))
    checks['predictions_at_shared_assigned_EF']=all(
        float(r[f'{channel}_model_at_assigned_EF'])==float(selected[int(s['nearest_model_index'])][f'{channel}_normalized'])
        and float(r['EF_inferred_eV'])==float(selected[int(s['nearest_model_index'])]['EF_eV'])
        for r,s in zip(rows,source) for channel in ('RH','Rs'))
    # The prior package is a preserved exact copy verified at archival time.
    checks['old_zip_preserved']=sha(old/'G05_L2_Checkpoint.zip')=='f86271430ab928172ca8345faF58c73cad5575b247840d385e5e67dae4ee97d7'.lower()
    passed=all(checks.values()) and all(r['identical'] for r in comparisons)
    report=dict(old_commit=old_commit,new_commit=new_commit,checks=checks,comparisons=comparisons,all_passed=bool(passed))
    write_json(ROOT/'outputs/L2_display_revision_audit.json',report)
    print(json.dumps(dict(checks=checks,unchanged_files=len(comparisons),all_passed=bool(passed)),indent=2))
    if not passed: raise SystemExit('Display revision audit failed')


if __name__=='__main__': main()

"""Verify all-phase delivery against archived values and a clean source clone."""
import json
import hashlib
import subprocess
import sys
import tempfile
from pathlib import Path
from reproduce import ROOT,git_info,write_json


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main(delivered):
    commit=git_info(); parent=ROOT.parent
    baseline=json.loads((ROOT/'records/revision_archive_hashes.json').read_text(encoding='utf-8'))
    unchanged=all((parent/k).is_file() and sha(parent/k)==v for k,v in baseline.items())
    if not unchanged: raise ValueError('Historical archive changed')
    qa=ROOT/'qa'; qa.mkdir(exist_ok=True)
    audit=Path(tempfile.mkdtemp(prefix='revision_',dir=qa)); clone=audit/'clean'
    subprocess.run(['git','clone','--no-hardlinks',str(ROOT),str(clone)],check=True)
    config=json.loads((delivered/'configuration.json').read_text(encoding='utf-8'))
    command=[sys.executable,'reproduce.py','--phase','all','--out','qa/fresh']
    if config['threshold_source']=='Explicit --l3-threshold override':
        command+=['--l3-threshold',str(config['l3_threshold'])]
    for label,cmd in [('tests',[sys.executable,'-m','unittest','-q']),('run',command)]:
        p=subprocess.run(cmd,cwd=clone,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (audit/(label+'.txt')).write_text(p.stdout+p.stderr,encoding='utf-8')
        if p.returncode: raise ValueError(f'{label} failed: {audit}')
    def files(root): return {p.relative_to(root).as_posix():p for p in root.rglob('*') if p.is_file() and p.name not in ['environment.json','run_log.txt','verification_report.json']}
    a,b=files(delivered),files(clone/'qa/fresh')
    comparisons={k:sha(a[k])==sha(b[k]) for k in a.keys()&b.keys()}
    new=json.loads((delivered/'results.json').read_text())
    old=json.loads((ROOT/'outputs/L3/results.json').read_text())
    prior=all(new[k]==old[k] for k in ['L1','L2'])
    l3=all(new['L3'][k]==old['L3'][k] for k in ['map','features','resolution_probe_pitch','detection_limit_fraction'])
    old2=parent/'G05_coursework/outputs/L2'; new2=delivered/'L2'
    evidence={p.name:sha(p)==sha(new2/p.name) for p in old2.iterdir() if p.suffix=='.csv' or p.name in ['L2_summary.json','L2_bootstrap_residuals.json']}
    report=dict(commit=commit,archive_files=len(baseline),archives_unchanged=unchanged,L1_L2_values_unchanged=prior,
                L3_estimates_unchanged=l3,L2_evidence=evidence,deterministic_files=len(comparisons),comparisons=comparisons,
                excluded='environment.json and run_log.txt: paths and run times',audit_directory=str(audit),
                all_passed=unchanged and prior and l3 and a.keys()==b.keys() and all(comparisons.values()) and all(evidence.values()))
    write_json(delivered/'verification_report.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['comparisons','L2_evidence']},indent=2))
    if not report['all_passed']: raise SystemExit('Verification failed')


if __name__=='__main__': main(Path(sys.argv[1]).resolve() if len(sys.argv)>1 else ROOT/'outputs/revision_2026_11_20/all_final')

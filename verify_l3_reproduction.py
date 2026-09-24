"""Clean clone, full output-tree audit and immutable prior-archive check."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
from reproduce import ROOT,git_info,write_json


def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main(archive_root,delivered):
    commit=git_info()
    baseline=json.loads((ROOT/'records/L3_prior_archive_hashes.json').read_text(encoding='utf-8'))
    def archives_ok():
        return all((archive_root/name).is_file() and digest(archive_root/name)==sha for name,sha in baseline.items())
    if not archives_ok(): raise ValueError('Prior archive is missing or changed before verification')
    qa=ROOT/'qa'; qa.mkdir(exist_ok=True)
    audit=Path(tempfile.mkdtemp(prefix=f'L3_{commit[:12]}_',dir=qa)); clone=audit/'clean_checkout'
    subprocess.run(['git','clone','--no-hardlinks',str(ROOT),str(clone)],check=True)
    for label,cwd,cmd in [('clean_tests',clone,[sys.executable,'-m','unittest','-v']),
                         ('clean_run',clone,[sys.executable,'reproduce.py','--data-dir','data/regular_G05','--phase','L3','--out','qa/fresh_output'])]:
        proc=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True,encoding='utf-8',errors='replace')
        (audit/(label+'.txt')).write_text(proc.stdout+proc.stderr,encoding='utf-8')
        if proc.returncode: raise RuntimeError(f'{label} failed; inspect {audit}')
    fresh=clone/'qa/fresh_output'
    def files(directory):
        return {p.relative_to(directory).as_posix():p for p in directory.rglob('*')
                if p.is_file() and p.name not in ['environment.json','run_log.txt']}
    left,right=files(delivered),files(fresh)
    if left.keys()!=right.keys(): raise ValueError('Deterministic output file lists differ')
    comparisons=[dict(file=k,identical=digest(left[k])==digest(right[k]),sha256=digest(left[k])) for k in sorted(left)]
    new=json.loads((delivered/'results.json').read_text(encoding='utf-8'))
    old=json.loads((archive_root/'outputs/L2/results.json').read_text(encoding='utf-8'))
    regression=all(new[phase]==old[phase] for phase in ['L1','L2'])
    # Entire old numerical L2 supporting evidence remains identical in the new child output.
    old_l2=archive_root/'outputs/L2'; child=delivered/'prerequisites_L2'
    numerical_names=[p.name for p in old_l2.iterdir() if p.suffix in ['.npy','.csv'] or p.name in ['L2_summary.json','L2_bootstrap_residuals.json']]
    l2_evidence={n:digest(old_l2/n)==digest(child/n) for n in numerical_names}
    with zipfile.ZipFile(delivered/'G05_L3_Checkpoint.zip') as z:
        zip_ok=z.testzip() is None and json.loads(z.read('results.json'))==new and z.read('commit_hash.txt').decode().strip()==commit
    report=dict(commit=commit,audit_directory=str(audit),comparisons=comparisons,
                prior_archive_files=len(baseline),prior_archives_unchanged=archives_ok(),
                L1_L2_regression=regression,L2_numerical_evidence=l2_evidence,zip_integrity=zip_ok,
                exclusions='environment.json and run_log.txt at each depth: timestamps and paths differ',
                environment='Clean source clone and empty outputs, same installed dependencies',
                all_passed=all(x['identical'] for x in comparisons) and regression and all(l2_evidence.values()) and archives_ok() and zip_ok)
    write_json(ROOT/'outputs/clean_reproduction_L3.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['comparisons','L2_numerical_evidence']},indent=2))
    if not report['all_passed']: raise SystemExit('L3 reproduction verification failed')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive-root',type=Path,required=True,help='Original coursework checkout with preserved L1/L2 outputs')
    parser.add_argument('--delivered',type=Path,default=ROOT/'outputs/L3')
    args=parser.parse_args(); main(args.archive_root.resolve(),args.delivered.resolve())

"""Clean-source, empty-output verification without overwriting archived L1 evidence."""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from reproduce import ROOT, git_info, write_json


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(phase):
    commit=git_info()
    qa=ROOT/'qa'; qa.mkdir(exist_ok=True)
    audit=Path(tempfile.mkdtemp(prefix=f'{phase}_{commit[:12]}_',dir=qa))
    clone=audit/'clean_checkout'
    baseline={str(p.relative_to(ROOT)):digest(p) for p in (ROOT/'outputs'/'L1').rglob('*') if p.is_file()}
    subprocess.run(['git','clone','--no-hardlinks',str(ROOT),str(clone)],check=True)
    original_out=audit/'original_output'
    clean_out=clone/'qa'/'fresh_output'
    records=[]
    for label,cwd,command in [
        ('original_tests',ROOT,[sys.executable,'-m','unittest','-v']),
        ('original_run',ROOT,[sys.executable,'reproduce.py','--phase',phase,'--out',str(original_out)]),
        ('clean_tests',clone,[sys.executable,'-m','unittest','-v']),
        ('clean_run',clone,[sys.executable,'reproduce.py','--phase',phase,'--out',str(clean_out)])
    ]:
        proc=subprocess.run(command,cwd=cwd,text=True,encoding='utf-8',errors='replace',capture_output=True)
        (audit/f'{label}.txt').write_text(proc.stdout+proc.stderr,encoding='utf-8')
        records.append(dict(label=label,command=command,cwd=str(cwd),returncode=proc.returncode))
        if proc.returncode: raise RuntimeError(f'{label} failed; see {audit}')
    excluded={'environment.json','run_log.txt'}
    names={p.name for p in original_out.iterdir() if p.is_file()}-excluded
    if names != {p.name for p in clean_out.iterdir() if p.is_file()}-excluded:
        raise RuntimeError('Output file sets differ')
    comparisons=[dict(file=name,original_sha256=digest(original_out/name),clean_sha256=digest(clean_out/name),
                      identical=digest(original_out/name)==digest(clean_out/name)) for name in sorted(names)]
    old=json.loads((ROOT/'outputs'/'L1'/'results.json').read_text())['L1']
    new=json.loads((original_out/'results.json').read_text())['L1']
    l1_equal=old==new
    archive_unchanged=all((ROOT/name).is_file() and digest(ROOT/name)==sha for name,sha in baseline.items())
    passed=bool(comparisons) and all(r['identical'] for r in comparisons) and l1_equal and archive_unchanged
    report=dict(phase=phase,commit=commit,audit_directory=str(audit),runs=records,comparisons=comparisons,
                L1_numerical_regression_passed=l1_equal,archived_L1_unchanged=archive_unchanged,
                L1_archive_sha256=baseline,all_passed=passed,
                exclusions='environment.json and run_log.txt contain expected path/time differences',
                environment_note='Clean committed source and empty output directories; same installed Python dependencies.')
    dest=ROOT/'outputs'/f'clean_reproduction_{phase}.json'
    write_json(dest,report)
    print(json.dumps(dict(phase=phase,commit=commit,compared_files=len(comparisons),
                         L1_unchanged=archive_unchanged,L1_regression=l1_equal,all_passed=passed,report=str(dest)),indent=2))
    if not passed: raise SystemExit('Reproducibility verification failed')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase',choices=['L1','L2'],default='L2')
    main(parser.parse_args().phase)

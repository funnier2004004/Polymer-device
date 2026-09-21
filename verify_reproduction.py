"""Clone the committed source and retain independently regenerated output comparisons."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from reproduce import ROOT, git_info, write_json


def main():
    commit = git_info()
    qa = ROOT / 'qa'
    qa.mkdir(exist_ok=True)
    clone = qa / ('clean_checkout_' + commit[:12])
    if clone.exists():
        raise SystemExit('Clean-check directory already exists; retain it and use a new commit for a new audit.')
    subprocess.run(['git', 'clone', '--no-hardlinks', str(ROOT), str(clone)], check=True)
    records = []
    for label, cwd, command in [
        ('original_tests', ROOT, [sys.executable, '-m', 'unittest', '-v']),
        ('original_run', ROOT, [sys.executable, 'reproduce.py', '--data-dir', 'data/regular_G05', '--phase', 'L1']),
        ('clean_tests', clone, [sys.executable, '-m', 'unittest', '-v']),
        ('clean_run', clone, [sys.executable, 'reproduce.py', '--data-dir', 'data/regular_G05', '--phase', 'L1'])
    ]:
        result = subprocess.run(command, cwd=cwd, text=True, encoding='utf-8',
                                errors='replace', capture_output=True)
        (qa / f'{label}_{commit[:12]}.txt').write_text(result.stdout + result.stderr, encoding='utf-8')
        records.append(dict(label=label, command=command, cwd=str(cwd), returncode=result.returncode))
        if result.returncode:
            raise RuntimeError(f'{label} failed; inspect saved output')
    original_out = ROOT / 'outputs' / 'L1'
    clean_out = clone / 'outputs' / 'L1'
    comparisons = []
    for path in sorted(original_out.iterdir()):
        if path.name in ('environment.json', 'run_log.txt') or not path.is_file():
            continue
        first = hashlib.sha256(path.read_bytes()).hexdigest()
        second = hashlib.sha256((clean_out/path.name).read_bytes()).hexdigest()
        comparisons.append(dict(file=path.name, original_sha256=first,
                                clean_sha256=second, identical=first == second))
    passed = bool(comparisons) and all(r['identical'] for r in comparisons)
    record = dict(commit=commit, clean_checkout=str(clone), runs=records,
                  comparisons=comparisons, all_identical=passed,
                  excluded=['environment.json and run_log.txt contain expected path/command differences'],
                  environment_note='Clean committed source; same installed pinned Python dependencies.')
    write_json(ROOT/'outputs'/'clean_reproduction.json', record)
    print(json.dumps(record, indent=2))
    if not passed:
        raise SystemExit('Clean-run output comparison failed')


if __name__ == '__main__':
    main()

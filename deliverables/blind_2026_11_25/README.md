# G05 blind-data run on 25 November 2026

This directory archives the actual G05 blind-data execution performed at
**01:18:17–01:18:26 China time (UTC+08:00)** on 25 November 2026.
It is separate from the regular-data analysis in `../revised_2026_11_20`.
No QMplus upload, historical classroom submission, timed-window compliance or
hidden-truth score is established by this archive.

## Generating version and outputs

The unchanged pipeline was frozen at
`cb12dbde0158881df9bfe940302fbc20379016cb` for this execution.
The later commit publishing this directory is an **archive commit**, not the
generating version. Do not replace the hash in the output files with the archive
commit. The original tests passed: 31 tests; the generated phase checks passed:
L1 51, L2 24, L3 14. `frozen_tests.log` retains the test output.

| File | Purpose |
|---|---|
| `blind_results.json` | Completed G05 blind numerical output in the supplied schema |
| `run_log.txt` | Actual timestamps, complete captured terminal output and original pipeline-generated log |
| `pipeline_commit.txt` | Frozen generating commit |
| `execution_record.json` | Commands, timestamps, exit codes and environment settings |
| `input_preparation.json` | Input manifest verification and template-name adapter |
| `decision_check.json` | Direct threshold and noise-margin decision comparison |
| `frozen_tests.log` | Original 31-test run |
| `SHA256SUMS.txt` | Byte-level hashes of every other file in this directory |

Summary: L1 correction factor **3.65816264177**; L2 **cone**, with central
`Eg_kT=0` under the prescribed selection rule; L3 maximum absolute map amplitude
**0.0409232639445**, giving **clear fail** against 0.030. The direct blind-README
threshold rule and the pipeline's noise-margin decision both give fail.
The L2 trajectory has **58** points from **174** paired-repeat rows. The unchanged
regular-data output remains hard-gap, `Eg_kT=2.25`; the two datasets must not be
mixed. A cone selection does not prove an exactly zero physical gap, and a
material fail is not a software-test failure.

## Inputs and unchanged calculation

Use only the teacher's original `blind_G05` folder from the released data archive.
All nine manifest entries were checked for byte size and SHA-256. Raw teacher
inputs are not republished in this directory.

The teacher supplies an empty `blind_results.json`, while the existing interface
expects `results_template.json`. Preparation added a **byte-identical copy** under
that second filename. The original empty file, manifest and measured data were
not edited. The completed output here must not be confused with that empty input
template. No algorithm, model grid, bootstrap/noise seed, regularisation strength
or threshold was changed to inspect these data.

## Reproduce from the frozen commit

Place the teacher's original `blind_G05` folder beside a new repository clone.
Use Python 3.12 and the pinned dependencies. From a new parent directory:

```text
git clone https://github.com/funnier2004004/Polymer-device.git G05_blind_reproduce
cd G05_blind_reproduce
git checkout cb12dbde0158881df9bfe940302fbc20379016cb
python -m pip install -r requirements.txt
python -m unittest -v
python -c "from pathlib import Path; import shutil; p=Path('../blind_G05'); shutil.copyfile(p/'blind_results.json', p/'results_template.json')"
python reproduce.py --phase blind --data-dir ../blind_G05 --out ../G05_blind_rerun
```

The output directory must not already exist. `execution_record.json` records the
actual software command and single-thread BLAS environment used for the archived
run (`OPENBLAS_NUM_THREADS=1`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`). Set those
environment variables before running if comparing floating-point outputs at the
tightest tolerances. Paths, timestamps and terminal formatting may differ in a
new run. All numerical evidence and plots from the original execution are also
retained in the separately supplied local material package.

## Interpretation and disclosure

The best hard-gap candidate improved the L2 residual by only about **2.615%** and
was at the lower gap-grid boundary, so it did not meet the frozen selection rule.
Noise-only map limits exclude smoothing bias and model discrepancy. The frozen
L3 method plot has dense roughness-axis tick labels for this narrow data range;
its numerical table remains available in the local analysis evidence.

OpenAI Codex desktop prepared and ran this calculation, verified and archived the
files, and drafted these instructions at the user's request. These activities are
not asserted to be independent student work. No new signature or personal
contribution was inferred. Publishing the evidence does not upload anything to
QMplus or notify the lecturer through a separate message.

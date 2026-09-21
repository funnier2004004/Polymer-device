"""One-command L1 evidence and checkpoint generation from untouched group data."""
import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
from l1 import KB, NA, E_CHARGE, EMAX, POINTS, count, closed_count, correction, crossing, mobility

ROOT = Path(__file__).resolve().parent
os.environ.setdefault('MPLCONFIGDIR', str(ROOT / '.mplconfig'))


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n', encoding='utf-8')


def verify_manifest(data_dir):
    manifest = json.loads((data_dir / 'manifest.json').read_text(encoding='utf-8'))
    rows = []
    for item in manifest['files']:
        path = (data_dir / item['name']).resolve()
        if not path.is_relative_to(data_dir.resolve()):
            raise ValueError('Manifest file outside data directory')
        raw = path.read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        ok = len(raw) == item['bytes'] and actual == item['sha256']
        rows.append(dict(file=item['name'], bytes=len(raw), sha256=actual, passed=ok))
    if not rows or not all(row['passed'] for row in rows):
        raise ValueError('Raw-data integrity check failed: ' + json.dumps(rows))
    return rows


def git_info():
    def git(*args):
        return subprocess.check_output(['git', '-C', str(ROOT), *args], text=True, encoding='utf-8').strip()
    commit = git('rev-parse', 'HEAD')
    if git('status', '--porcelain', '--untracked-files=normal'):
        raise ValueError('Commit source/data/records changes before generating a checkpoint')
    return commit


def write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def make_figure(out, sweep, dense, op, crossings, group):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'svg.fonttype': 'none', 'svg.hashsalt': 'QXU6028-L1',
                         'axes.linewidth': .8, 'legend.frameon': False})
    fig, ax = plt.subplots(figsize=(7.2, 4.8), layout='constrained')
    ax.plot([r['EF_eV'] for r in dense], [r['correction_factor'] for r in dense],
            color='#256781', lw=1.8, label='Finite-temperature model')
    ax.scatter([r['EF_eV'] for r in sweep], [r['correction_factor'] for r in sweep],
               facecolors='white', edgecolors='#256781', s=28, zorder=3,
               label='Supplied band count / calculated Fermi count')
    for target, x in crossings.items():
        value = float(target)
        ax.hlines(value, 0, x, color='#888888', lw=.8, linestyle='--')
        ax.vlines(x, 1, value, color='#888888', lw=.8, linestyle='--')
        ax.scatter([x], [value], marker='s', color='#666666', s=24, zorder=4)
        ax.annotate(f'C = {value:g}: {x:.5f} eV', (x, value), xytext=(10, -23),
                    textcoords='offset points', fontsize=9)
    x, y = op['EF_op_eV'], op['correction_factor']
    ax.scatter([x], [y], marker='*', s=120, color='#B25827', zorder=5)
    ax.annotate(f'Operating point\n{x:.7f} eV, C = {y:.5f}', (x, y),
                xytext=(.115, 3.0), textcoords='data', fontsize=9, color='#8C431C',
                arrowprops={'arrowstyle': '-', 'color': '#B25827', 'lw': .8})
    ax.set(xlabel=r'Fermi level, $E_F$ (eV)',
           ylabel=r'Correction factor, $C=n_{\mathrm{band}}/n_{\mathrm{Fermi}}$',
           xlim=(0, .265), ylim=(.8, 6.7), title=f'{group} | L1 carrier-count correction at {op["T_K"]:g} K')
    ax.legend(loc='upper left', fontsize=8)
    fig.savefig(out / 'L1_correction.png', dpi=220, metadata={'Software': 'G05 L1 pipeline'})
    fig.savefig(out / 'L1_correction.svg', metadata={'Date': None})
    plt.close(fig)


def run(args):
    data_dir = args.data_dir.resolve()
    out = args.out.resolve()
    if out == ROOT or out.is_relative_to(ROOT / 'data') or out.is_relative_to(data_dir) or data_dir.is_relative_to(out):
        raise ValueError('Output must be separate from input data and repository root')
    commit = git_info()
    integrity = verify_manifest(data_dir)
    params = json.loads((data_dir / 'L1_params.json').read_text(encoding='utf-8'))
    manifest = json.loads((data_dir / 'manifest.json').read_text(encoding='utf-8'))
    template = json.loads((data_dir / 'results_template.json').read_text(encoding='utf-8'))
    for name in ('group', 'dataset_set'):
        if params[name] != template[name] or params[name] != manifest[name]:
            raise ValueError(f'{name} does not match across inputs')
    if params['schema_version'] != 'QXU6028-data-v1' or template['schema_version'] != 'QXU6028-results-v1':
        raise ValueError('Unsupported course schema')
    with (data_dir / 'L1_data.csv').open(encoding='utf-8', newline='') as handle:
        data = [{k: float(v) for k, v in row.items()} for row in csv.DictReader(handle)]
    if not data or not all(np.isfinite(v) for r in data for v in r.values()):
        raise ValueError('Empty or non-finite L1 input')
    t, c, ef, rho = (params[k] for k in ('T', 'c', 'EF_op_eV', 'rho_ohm_sq'))
    checks = []

    def check(name, observed, expected, tolerance, *, relative=False):
        error = abs(observed - expected) / abs(expected) if relative else abs(observed - expected)
        row = dict(check=name, observed=float(observed), expected=float(expected),
                   tolerance=tolerance, error=float(error), relative=relative, passed=bool(error <= tolerance))
        checks.append(row)
        if not row['passed']:
            raise ValueError('Physics check failed: ' + json.dumps(row))

    # Absolute tolerance 0.01 for rounded published reference values; not scorer tolerance.
    for x, expected in [(0., 1.), (.073, 2.), (.1, 2.6), (.2, 5.1)]:
        check(f'published_gate_EF_{x}_300K', correction(x, 300, c), expected,
              1e-12 if x == 0 else .01)
    sweep = []
    for row in data:
        x = row['EF_eV']
        nf = count(x, t, c, fermi_referenced=True)
        nb = count(x, t, c, fermi_referenced=False)
        check(f'CSV_band_count_{x}', nb, row['n_band_cm2'], 1e-5, relative=True)
        check(f'closed_count_{x}', nf, closed_count(x, t, c), 5e-6, relative=True)
        check(f'sheet_resistance_{x}', row['rho_ohm_sq'], rho, 1e-10, relative=True)
        sweep.append(dict(EF_eV=x, n_band_supplied_cm2=row['n_band_cm2'],
                          n_band_recomputed_cm2=nb, n_fermi_cm2=nf,
                          n_fermi_closed_cm2=closed_count(x, t, c),
                          correction_factor=row['n_band_cm2']/nf,
                          mobility_band_cm2_Vs=mobility(row['n_band_cm2'], rho),
                          mobility_corrected_cm2_Vs=mobility(nf, rho)))
    if not np.all(np.diff([r['EF_eV'] for r in sweep]) > 0):
        raise ValueError('Sweep must be ordered by increasing EF')
    check('strictly_increasing_supplied_sweep', float(np.all(np.diff([r['correction_factor'] for r in sweep]) > 0)), 1, 0)
    nb = count(ef, t, c, fermi_referenced=False)
    nf = count(ef, t, c, fermi_referenced=True)
    factor = nb / nf
    op = dict(EF_op_eV=ef, T_K=t, c=c, rho_ohm_sq=rho, n_band_op_cm2=nb,
              n_fermi_op_cm2=nf, n_fermi_closed_cm2=closed_count(ef, t, c),
              correction_factor=factor, mobility_band_cm2_Vs=mobility(nb, rho),
              mobility_corrected_cm2_Vs=mobility(nf, rho))
    check('operating_closed_form', nf, closed_count(ef, t, c), 5e-6, relative=True)
    check('mobility_ratio', op['mobility_corrected_cm2_Vs']/op['mobility_band_cm2_Vs'], factor, 1e-12, relative=True)
    check('mobility_SI_crosscheck', mobility(nf, rho), 1e4/(E_CHARGE*(nf*1e4)*rho), 1e-12, relative=True)
    check('DoS_slope_cancellation', correction(ef,t,2*c), factor, 1e-12, relative=True)
    for label, referenced in [('band', False), ('fermi', True)]:
        fine = count(ef, t, c, fermi_referenced=referenced, points=40001)
        coarse = nf if referenced else nb
        check(f'operating_grid_refinement_{label}', coarse, fine, 5e-6, relative=True)
    check('operating_grid_refinement_factor', factor, correction(ef,t,c,points=40001), 5e-6, relative=True)
    crossings = {str(target): crossing(target,t,c,sweep[0]['EF_eV'],sweep[-1]['EF_eV']) for target in (2,4)}
    for target, x in crossings.items():
        check(f'crossing_{target}', correction(x,t,c), float(target), 1e-10)
    dense = [dict(EF_eV=float(x), correction_factor=correction(float(x),t,c))
             for x in np.linspace(0, sweep[-1]['EF_eV'], 301)]
    check('dense_curve_monotonic', float(np.all(np.diff([r['correction_factor'] for r in dense]) > 0)), 1, 0)
    template['pipeline_commit'] = commit
    template['L1'] = {k: op[k] for k in template['L1']}
    if set(template['L1']) != {'correction_factor','n_fermi_op_cm2','mobility_corrected_cm2_Vs'}:
        raise ValueError('Unexpected L1 keys')
    if not all(np.isfinite(v) and v > 0 for v in template['L1'].values()):
        raise ValueError('L1 JSON requires positive finite outputs')
    out.mkdir(parents=True, exist_ok=True)
    write_json(out/'results.json', template)
    write_json(out/'input_integrity.json', integrity)
    write_json(out/'checks.json', checks)
    write_json(out/'operating_point.json', op)
    write_json(out/'crossings.json', crossings)
    write_csv(out/'L1_sweep.csv', sweep)
    write_csv(out/'L1_curve.csv', dense)
    make_figure(out, sweep, dense, op, crossings, params['group'])
    note = f'''{params['group']} L1 checkpoint: finite-temperature carrier-count correction

Method. Following Practical Methods Guide pp. 3-5, integrate N_A*c*E*f(E;EF,T)
from 0 to 2.5 eV for n_band and from EF to 2.5 eV for n_Fermi, with 20,001
points and trapezoidal integration. T = {t:g} K. Use supplied n_band values
for sweep markers; recompute both integrals at the exact operating EF.

Results. At EF = {ef:.14f} eV and rho = {rho:.10f} ohm/sq:
n_band = {nb:.9e} cm^-2; n_Fermi = {nf:.9e} cm^-2;
C = {factor:.9f}; mu_band = {op['mobility_band_cm2_Vs']:.6f} cm^2/(V s);
mu_corrected = {op['mobility_corrected_cm2_Vs']:.6f} cm^2/(V s).
C = 2 at EF = {crossings['2']:.9f} eV; C = 4 at {crossings['4']:.9f} eV.

Interpretation. As positive doping grows, n_band includes more occupied states
below EF, whereas the Fermi-referenced count retains states above EF. At high
positive EF the former grows approximately quadratically and the latter
linearly, so their ratio increases. At fixed measured sheet resistance,
mu = 1/(e*n*rho), so mu_corrected/mu_band = C. This is a model-dependent
extracted mobility, not evidence that the sample's scattering changed.

Quantified advice. Under an inverse-carrier-density sensitivity model with all
other factors fixed, use {factor:.5f} times the band-count sensitivity estimate
(a {(factor-1)*100:.2f}% increase relative to that estimate). This is conditional
device advice, not an independently measured sensor response.

Checks and limits. Neutrality and the three rounded positive-EF gates pass.
The numerical Fermi count agrees with the supplied closed form, and doubling
the integration resolution passes a 5e-6 relative tolerance. These are numerical
checks, not experimental confidence intervals. L1 supplies no measurement
uncertainties for T, c or rho, so no experimental uncertainty is invented.
The closed expression assumes an infinite upper limit; at this group's 300 K
operating range its thermal tail beyond 2.5 eV is negligible at our tolerance.

Figure. Open circles use the 12 supplied band-count values; the solid curve
recalculates both counts. The star is the exact operating point; squares mark
C=2 and C=4 crossings. This is a deterministic model sweep, not replicate data.

Reproduction: python reproduce.py --data-dir data/regular_G05 --phase L1
Pipeline commit: {commit}
L2 and L3 fields are intentionally unfilled in this L1 checkpoint.
'''
    (out/'brief_note.txt').write_text(note, encoding='utf-8')
    (out/'commit_hash.txt').write_text(commit+'\n', encoding='ascii')
    import matplotlib
    environment = dict(python=sys.version, numpy=np.__version__, matplotlib=matplotlib.__version__,
                       platform=platform.platform(), executable=sys.executable,
                       data_dir=str(data_dir), command=[sys.executable,*sys.argv],
                       constants=dict(kB_eV_K=KB, NA_atoms_cm2=NA, e_C=E_CHARGE, Emax_eV=EMAX, points=POINTS))
    write_json(out/'environment.json', environment)
    (out/'run_log.txt').write_text('\n'.join([
        'Phase: L1', f'Group: {params["group"]}', f'Commit: {commit}',
        'Command: '+subprocess.list2cmdline([sys.executable,*sys.argv]),
        f'Input integrity: {len(integrity)} files passed',
        *[f'PASS {r["check"]}: observed={r["observed"]:.12g}; error={r["error"]:.4g}; tolerance={r["tolerance"]}' for r in checks],
        'L1 results: '+json.dumps(template['L1']), 'Completed successfully'])+'\n', encoding='utf-8')
    files = ['results.json','L1_correction.png','L1_correction.svg','brief_note.txt','commit_hash.txt']
    zip_path = out/f'{params["group"]}_L1_Checkpoint.zip'
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as bundle:
        for name in files:
            info = zipfile.ZipInfo(name, date_time=(2026,1,1,0,0,0))
            info.compress_type = zipfile.ZIP_DEFLATED
            bundle.writestr(info, (out/name).read_bytes())
    with zipfile.ZipFile(zip_path) as bundle:
        if bundle.testzip() is not None or json.loads(bundle.read('results.json')) != template:
            raise ValueError('Checkpoint archive verification failed')
    print(json.dumps({'checks_passed':len(checks), 'L1':template['L1'],
                      'crossings':crossings, 'checkpoint':str(zip_path)}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, default=ROOT/'data'/'regular_G05')
    parser.add_argument('--phase', choices=['L1'], required=True)
    parser.add_argument('--out', type=Path, default=ROOT/'outputs'/'L1')
    run(parser.parse_args())

"""Methods Guide pp. 6-9: paired transport inverse problem, no hidden-truth access."""
import csv
import numpy as np
from l1 import KB, NA

SEED = 602805
BOOTSTRAPS = 200


def load_pairs(path):
    groups = {}
    with path.open(encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != ['measurement_index','repeat','R_H_raw','R_xx_raw']:
            raise ValueError('Unexpected L2 columns')
        for row in reader:
            i, repeat = int(row['measurement_index']), int(row['repeat'])
            if i < 0 or repeat not in (1,2,3):
                raise ValueError('Invalid measurement index or repeat ID')
            pair = [float(row['R_H_raw']),float(row['R_xx_raw'])]
            if not np.all(np.isfinite(pair)) or pair[1] <= 0:
                raise ValueError('L2 pair must be finite with positive Rs')
            group = groups.setdefault(i,{})
            if repeat in group:
                raise ValueError('Duplicate measurement/repeat pair')
            group[repeat] = pair
    if not groups or any(set(g) != {1,2,3} for g in groups.values()):
        raise ValueError('Every measurement requires three complete paired repeats')
    indices = np.array(sorted(groups))  # Preserve the numbered measurement sequence, not RH/EF order.
    if len(indices) < 2 or np.any(np.diff(indices) != 1):
        raise ValueError('Measurement indices must form an unbroken sequence')
    return indices, np.array([[groups[i][r] for r in (1,2,3)] for i in indices])


def normalize(pairs):
    pairs = np.asarray(pairs,dtype=float)
    if pairs.ndim != 2 or pairs.shape[1] != 2 or len(pairs) == 0:
        raise ValueError('Expected N x 2 paired channels')
    if not np.all(np.isfinite(pairs)) or np.any(pairs[:,1] <= 0):
        raise ValueError('Channels must be finite and Rs positive')
    scales = np.array([np.max(np.abs(pairs[:,0])),np.max(pairs[:,1])])
    if np.any(scales <= 0):
        raise ValueError('Cannot normalize an all-zero Hall channel')
    return pairs/scales, scales


def transport(ef, temperature, gap_kT, c=1.):
    if not np.isfinite(temperature) or temperature <= 0 or not np.isfinite(gap_kT) or gap_kT < 0 or not np.isfinite(c) or c <= 0:
        raise ValueError('Invalid transport parameters')
    ef = np.atleast_1d(np.asarray(ef,dtype=float))
    if not np.all(np.isfinite(ef)) or np.any(np.abs(ef) >= 2.5):
        raise ValueError('EF outside energy integration range')
    energy = np.linspace(-2.5,2.5,4000)
    f = 1/(np.exp(np.clip((energy[None,:]-ef[:,None])/(KB*temperature),-60,60))+1)
    # For gap=0 this is exactly the ideal cone; edge inclusivity matches the guide.
    g = c*np.maximum(np.abs(energy)-gap_kT*KB*temperature/2,0.)
    n = NA*np.trapezoid(np.where(energy[None,:] >= ef[:,None],g*f,0.),energy,axis=1)
    p = NA*np.trapezoid(np.where(energy[None,:] <= ef[:,None],g*(1-f),0.),energy,axis=1)
    # e=mu=1 is permitted: fixed scales cancel in separate normalization.
    rh = (p-n)/(p+n)**2
    rs = 1/(p+n)
    return rh,rs,n,p


def model_library(temperature):
    ef = np.linspace(-8*KB*temperature,9*KB*temperature,400)
    gaps = np.r_[0.,np.arange(.5,8.001,.25)]
    curves,raw,scales = [],[],[]
    for gap in gaps:
        rh,rs,n,p = transport(ef,temperature,gap)
        pair = np.column_stack([rh,rs])
        xy,scale = normalize(pair)
        curves.append(xy); scales.append(scale)
        raw.append(np.column_stack([rh,rs,n,p]))
    return dict(ef=ef,gaps=gaps,xy=np.asarray(curves),raw=np.asarray(raw),scales=np.asarray(scales))


def nearest(data_xy, model_xy):
    d2 = ((np.asarray(data_xy)[:,None,:]-np.asarray(model_xy)[None,:,:])**2).sum(axis=2)
    assigned = d2.argmin(axis=1)
    distances = np.sqrt(d2[np.arange(len(d2)),assigned])
    return float(np.sqrt(np.mean(distances**2))), assigned, distances


def choose_model(r_cone,r_gap,gap_kT):
    return bool(r_gap < .85*r_cone and gap_kT >= 1.)


def fit(pairs, library):
    xy, scales = normalize(pairs)
    results = [nearest(xy,curve) for curve in library['xy']]
    residuals = np.array([r[0] for r in results])
    best_gap = int(1+np.argmin(residuals[1:]))
    selected = best_gap if choose_model(residuals[0],residuals[best_gap],library['gaps'][best_gap]) else 0
    assigned = results[selected][1]
    return dict(xy=xy,scales=scales,residuals=residuals,best_gap=best_gap,selected=selected,
                model='hard_gap' if selected else 'cone',gap_kT=float(library['gaps'][selected]),
                assigned=assigned,trajectory=library['ef'][assigned],distances=results[selected][2])


def bootstrap(pairs, library, seed=SEED, repeats=BOOTSTRAPS):
    rng = np.random.default_rng(seed)
    draws = rng.integers(0,3,size=(repeats,len(pairs)))
    sampled = pairs[np.arange(len(pairs))[None,:],draws]
    fits = [fit(pair,library) for pair in sampled]
    gaps = np.array([r['gap_kT'] for r in fits])
    trajectories = np.array([r['trajectory'] for r in fits])
    return dict(draws=draws,sampled_pairs=sampled,gaps=gaps,trajectories=trajectories,
                selected=np.array([r['selected'] for r in fits]),
                residuals=np.array([r['residuals'] for r in fits]),
                gap_percentiles=np.percentile(gaps,[16,50,84]),
                trajectory_percentiles=np.percentile(trajectories,[16,50,84],axis=0),
                hard_gap_fraction=float(np.mean([r['selected'] != 0 for r in fits])))

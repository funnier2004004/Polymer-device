# L2 implementation record

Date: 2026-09-23. Group G05. Source: supplied Practical Methods Guide pp. 6–9, Assessment Brief pp. 3–4. No hidden truth or unpublished papers are used.

## Definitions and computational choices

Use the course's Fermi-window populations: n=NA integral_EF^2.5 g(E)f(E)dE, p=NA integral_-2.5^EF g(E)[1-f(E)]dE. RH=(p-n)/(e*(p+n)^2) and Rs=1/(e*mu*(p+n)). This sign convention is used exactly; do not replace it with a generic single-carrier shortcut. Both carriers share the guide's single mobility parameter.

Cone: g=c|E|. Hard gap: g=0 for |E|<=Eg/2, otherwise c(|E|-Eg/2). Model curves use c=e=mu=1; fixed multiplicative factors cancel under independent channel normalization. L1 is recalculated in the new JSON, but its correction factor is NOT multiplied into the normalized L2 observations. This is the specific link between the phases, not an arbitrary rescaling.

Use 4,000 energy points over [-2.5,2.5] eV, inclusive; 400 EF points over [-8,+9] kBT; gaps 0.50 to 8.00 kBT in 0.25 increments plus the cone. Keep the exact np.where integration masks in the guide. Do not interpolate, smooth, or change the prescribed grid to obtain a preferred result.

Preserve the two measured channels within each (measurement_index,repeat) row. Reject missing, duplicate or nonfinite rows and nonpositive Rs. Process the original numbered measurement sequence. Means use three repeats; raw error bars use sample SD, ddof=1. Locate the mean RH sign crossing before normalization; do not subtract an offset or force a zero datum.

Normalize mean RH by its maximum absolute value and mean Rs by its maximum. Every complete model curve is normalized by its own independent maxima. Fit by nearest point in 2D, equal weighting in normalized coordinates, with RMS over all measurement points. The hard-gap winner must improve RMS by strictly more than 15% and have Eg>=1 kBT; otherwise return cone, Eg=0. Ties in a candidate search use the first minimum in the specified grid, as np.argmin does in the guide.

Bootstrap follows the guide's specific resampling protocol, not an invented average-of-three resampling: choose one complete repeat pair independently at each index; renormalize and repeat the same model selection. NumPy default_rng seed 602805; 200 replicates. Record all draws (with actual repeat IDs), paired values, trajectories, selected gaps, and full candidate residuals.

## Interpretation of output

`model` uses `cone` or `hard_gap`. The template contains null placeholders rather than typed validation rules. `Eg_uncertainty_kT` is explicitly a project convention: half of (p84-p16). This scalar is not necessarily a symmetric interval about the central fit. Full endpoints and median appear in L2_summary.json, the note, and Chinese explanation. Central Eg and trajectory come from fitting the repeat means. Trajectory bands are pointwise 16–84% bootstrap percentiles. A selection frequency is not a posterior probability.

Report finite grid resolution, edge assignments and boundary best gaps; flag a resampling hard-gap frequency in [0.4,0.6] as near 0.5. This flag is an interpretation aid, not a modification of the teacher's 15% selection rule. The narrow interval cannot establish accuracy beyond the fixed candidate set or account for contact/mobility/model errors. Device advice is conditional on the selected model, not a claim of measured transistor or sensor performance.

## Figure contract

Display extension: retain the original A–D figures, add E: normalized RH versus EF and F: normalized Rs versus EF. Both use the same 51 joint-fit EF assignments and the selected model's full prescribed EF grid. Plot measured means without connecting or reordering them. Scale each vertical sample SD by the SAME mean-data channel normalization factor as the fitted observations. This conditional SD does not include uncertainty in the estimated normalization factor. Show EF uncertainty only in the existing trajectory panel D. Clearly label EF as inferred for measured points and state that this is not independent validation. Export a 3x2 six-panel summary (11.6 x 13.2 inches) plus 7.2 x 5.4 inch individual comparisons, PNG 220 dpi and editable SVG. Source CSV includes shared EF, observed normalized means/SD and predicted values at the assigned model point.

Python/Matplotlib only; quantitative four-panel evidence grid, 11.6 x 8.8 inches, 220 dpi PNG and editable-text SVG. A/B distinguish raw repeats and mean +/- sample SD; C compares both candidate families and identifies the selected model; D shows the central trajectory and resampling interval. Separate 7.2 x 5 inch model/trajectory exports support the required checkpoint. No assumed physical units on raw channels: metadata only supplies raw scales. Every plotted value is retained in model-library, paired-data, trajectory, and bootstrap CSVs.

## Validation and archival

Test normalization/sign, pairing rejection, neutrality and symmetry, exact synthetic model curves, nearest-point order, and 15% boundary conditions. Check independent redraw reproducibility. Rare hole populations computed with the exact guide's 1-f can incur about 2.3e-12 relative subtraction error; population symmetry tolerance is 1e-10, much smaller than data noise. Preserve the formula rather than pretending the error is new physics.

Each checkpoint uses an actual committed clean source state. L1's tracked archive is never regenerated in place during L2. The new verifier uses two empty output directories, compares deterministic files, independently recomputes L1 numbers, and hashes every archived L1 file before/after. Environment/path-dependent logs are retained but excluded from byte equality. Output schema keeps L3 unfilled. No public repository or QMplus upload is performed.

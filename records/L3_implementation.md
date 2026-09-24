# G05 L3 execution ledger

Approved plan: G05 L3 reconstruction, resolution and detection limit (user message).
Source authority: Practical Methods Guide pp. 10-13; original materials remain untouched.
Base commit: 1c5898af3f76b10fa27db813a3db31f5122965b3.

## Tasks and contracts
1. Core: validate 128x100 A and 3x128 repeats; prescribed projected inverse, five eta values,
   extrema, two moment-FWHM point tests, 500 noise draws with seed 60280503, threshold decision.
2. Delivery: reuse L1/L2 computations without modifying their archives; preserve JSON keys;
   map/method/noise PNG+editable SVG, source data, bilingual notes, commit and ZIP.
3. Audit: regression, archive hashes, clean-clone deterministic reproduction, visual QA, review.

Pre-flight: core returns finite row-major maps and scalar diagnostics; delivery translates to
the existing template. Missing threshold must produce pass=null and explicit pending text;
this is not a schema-complete final submission. No incompatible interfaces found.

Ruling: native worktree creation failed because the desktop workspace root is the parent
of the repository. Used a separate sibling Git worktree on branch g05-l3; no existing
archive was moved. Outputs will be delivered with an explicit source-worktree path.

Baseline: existing 15 tests passed before implementation.

Task 1 complete: eight core tests first failed because L3 was absent, then the full
23-test suite passed. Task 2 tests first failed on missing delivery and CLI threshold;
after implementation all 25 tests passed. No deliberate physics errors were introduced.
Task 3: initial archive baseline captures 63 files from L1, L2 and the earlier L2 archive.
Source scale convention: the existing schema names detection_limit_fraction; retain this
fractional model scale, with no extra conversion using L1 or L2 unsupported by the guide.

## Figure contract
Python quantitative maps and diagnostic grids. Claim: the data support a regularised
zero-mean estimate with measured numerical resolution/noise limits, not an absolute map
or a pass/fail decision without the classroom threshold. Map: 7x6 inches, symmetric
diverging scale; method: 11x9 inches, eta trade-off and central/off-centre PSFs; noise:
11x4.5 inches, measured repeats and simulation maxima. PNG 220 dpi and editable SVG.
Source tables preserve all displayed data; no interpolation that invents spatial detail.
Risks: coordinate transposition, unsupported percent scale, mislabelled SD/CI,
moment width mistaken for direct FWHM, missing threshold silently treated as pass.

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

Initial full run: eta=0.0013309924629099211; max|map|=0.04648813409955846;
two moment widths=1.4442950156533239 and 1.3034888535482658 probe pitches;
delta95=2.6979634193645296e-5. Missing threshold remains null.
Initial clean clone audit passed, including all 63 prior archive hashes and L1/L2
numerical regression. This is preliminary evidence; final commit is rerun after review.
Visual QA caught E07 (legend overlap), confirmed by a failing bounding-box test,
then fixed by moving the raw-channel legend outside the axes. Full suite: 26 passing.
All three updated figure previews inspected; no clipping or overlapping labels remains.
The reference residual is 30.573 times the estimated mean-data noise norm. Added this
diagnostic and a caution that noise detection limits exclude regularisation bias.
This does not change the approved eta or the guide's detection-limit simulation.

Final independent review: core formulas and numerical tests aligned with the guide;
no critical numerical finding. One important archive-protection gap and one initially
minor threshold-audit gap found. Regraded the latter as important to the promised
optional-threshold workflow. Both received failing regression tests before fixes.
The first now protects all registered worktree data and archived phase directories;
the second propagates the recorded threshold into the clean run. See E08/E09.
No deferred minor findings remain.

Reviewer exclusions settled: visual QA and full reproduction are checked by the main
agent; hidden truth/calibration are unavailable and not invented; actual pass/fail is
pending the missing threshold; live blind test/upload remain outside this request.
Development branch and output workspace are retained locally rather than merged or
published. This preserves the earlier checkout; use the explicit L3 source directory.

Final fix-pass suite: 28 tests passed, including cross-worktree archive rejection,
threshold propagation, and rendered legend geometry. Git path decoding in the new
test was corrected to UTF-8 after inspecting the actual bytes (E10). All source/data/
record changes are committed before generating final artifacts. The final audit is
stored at outputs/clean_reproduction_L3.json to avoid a self-referential commit hash.

## Figure contract
Python quantitative maps and diagnostic grids. Claim: the data support a regularised
zero-mean estimate with measured numerical resolution/noise limits, not an absolute map
or a pass/fail decision without the classroom threshold. Map: 7x6 inches, symmetric
diverging scale; method: 11x9 inches, eta trade-off and central/off-centre PSFs; noise:
11x4.5 inches, measured repeats and simulation maxima. PNG 220 dpi and editable SVG.
Source tables preserve all displayed data; no interpolation that invents spatial detail.
Risks: coordinate transposition, unsupported percent scale, mislabelled SD/CI,
moment width mistaken for direct FWHM, missing threshold silently treated as pass.

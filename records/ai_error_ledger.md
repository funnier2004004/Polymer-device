# AI error ledger

## Report-guidance correction, 2026-11-20

E11: Earlier material review concluded the L3 threshold was unavailable. The supplied
session slides page 15 explicitly states PASS when max|m| <=0.030 (3.0% reference
conductivity). Inspection during the new-material audit detected the omitted page.
Corrected committed configuration to 0.030 and regenerated the decision with the
existing guide confidence rule. Original pending packages remain historical evidence.
This is a missed-source/decision error; it is not a fabricated formula error.

## L3 observed error, 2026-09-24

E07: The initial noise diagnostic used an automatic in-axis legend. Visual inspection
showed its text overlapping the raw scan lines. A rendered-geometry regression test
then failed because the legend bounding box overlapped the measurement axes.
Cause: automatic placement cannot find a blank region in this dense trace. Moved the
legend above the axes and retained the geometry test; this is a figure-layout error,
not a fabricated physics error. Also changed the detection-limit legend to significant
digits so a value near 2.698e-5 is not rounded to an uninformative 0.00003.

E08: Initial L3 output guard protected only the current worktree's archive paths,
not those in the original sibling checkout. Independent review used a read-only
probe (stopped before writing), and a regression test reproduced three unprotected
archive targets. The guard now resolves all registered Git worktree roots and
rejects overlapping data/L1/L2/archive destinations. No archive was overwritten.
Category: filesystem safety bug, not a physics error.

E09: Initial clean-clone audit omitted an optional supplied L3 threshold, which
would compare a thresholded delivery against a pending result. Review detected it;
a test failed before a threshold-aware command builder was added. The audit now
reuses the delivered summary's threshold. Current G05 still has no threshold.
Category: reproducibility-interface bug, not a physics error.

E10: The new archive-guard test initially decoded Git's UTF-8 Chinese directory
using the Windows default encoding. It constructed a different, non-existing path
and still failed after the production guard was fixed. Inspection of Git's raw
bytes identified the encoding mismatch; explicit UTF-8 decoding fixes the test.
Production worktree parsing already decoded UTF-8. Category: test/path encoding error.

Record only observed errors. Do not create deliberate mistakes to meet a mark target.

| ID | Actual AI action or claim | Evidence detecting it | Correction | Category / status |
|---|---|---|---|---|
| E01 | During preparation, attempted to read regular_G05-era files from the earlier top-level data layout (the actual attempted example paths used regular_G01) | File-not-found output; directory listing showed the supplied pack had moved under data/ | Re-resolved the current data layout and subsequently used data/03_Regular_Data/regular_G05 | File-path error; not a physics error and not offered as an 8-mark physics-ledger example |
| E02 | Assumed bundled Python had Matplotlib installed when checking imports | ModuleNotFoundError: No module named matplotlib | Provisioned a project-local environment and installed the pinned plotting dependency; physics still uses the teacher's NumPy definitions | Environment assumption; not a physics error |
| E03 | First generated plot placed the operating-point annotation over the model curve | Visual inspection of the first PNG showed text intersecting the rising curve | Moved the annotation into the blank upper-left area and regenerated the figure and checkpoint | Figure-layout error; not a physics error |

| E04 | L2 population-symmetry test initially required relative tolerance 1e-12 for every gap | At gap=8 kBT, EF=+/-0.08 eV, the exact guide's 1-f subtraction produced relative difference 2.2924e-12 (absolute population difference 0.0048492 on about 2.115e9) | Inspected gap=0,1,5,8 cases, retained the prescribed formula and set population-symmetry tolerance to 1e-10; retested neutrality, RH oddness and Rs evenness | Over-strict numerical test assumption; not a confirmed physics-model error |
| E05 | Documentation edits initially used an invalid patch structure or an incomplete exact-match context | Patch tool rejected a duplicate target operation and an unmatched ledger paragraph | Reissued a supported file replacement and exact paragraph edit, then checked the resulting diff | Editing-tool error; not a physics error |
| E06 | Initial L2 model-plot legend overlapped the lower branches, and the residual text box occupied part of the upper branch | Visual inspection of the four-panel and standalone model PNGs | Moved both legend and residual text into the empty interior of the model loop; regenerated and rechecked | Figure-layout error; not a physics error |

No genuine AI-generated physics-model error has been confirmed at this stage. Reference-value differences between the brief and methods guide are documented as a source discrepancy, not falsely attributed to AI. The teacher normally expects at least two genuine physics-error examples for full ledger marks; that requirement remains unfulfilled until such errors actually occur and are documented.

Future entries must preserve the actual claim/code, failed check with observed and expected values, correction, physical reason, verification and relevant commit. Students should add only events they can substantiate.

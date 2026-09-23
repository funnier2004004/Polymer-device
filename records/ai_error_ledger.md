# AI error ledger

Record only observed errors. Do not create deliberate mistakes to meet a mark target.

| ID | Actual AI action or claim | Evidence detecting it | Correction | Category / status |
|---|---|---|---|---|
| E01 | During preparation, attempted to read regular_G05-era files from the earlier top-level data layout (the actual attempted example paths used regular_G01) | File-not-found output; directory listing showed the supplied pack had moved under data/ | Re-resolved the current data layout and subsequently used data/03_Regular_Data/regular_G05 | File-path error; not a physics error and not offered as an 8-mark physics-ledger example |
| E02 | Assumed bundled Python had Matplotlib installed when checking imports | ModuleNotFoundError: No module named matplotlib | Provisioned a project-local environment and installed the pinned plotting dependency; physics still uses the teacher's NumPy definitions | Environment assumption; not a physics error |
| E03 | First generated plot placed the operating-point annotation over the model curve | Visual inspection of the first PNG showed text intersecting the rising curve | Moved the annotation into the blank upper-left area and regenerated the figure and checkpoint | Figure-layout error; not a physics error |

| E04 | L2 population-symmetry test initially required relative tolerance 1e-12 for every gap | At gap=8 kBT, EF=+/-0.08 eV, the exact guide's 1-f subtraction produced relative difference 2.2924e-12 (absolute population difference 0.0048492 on about 2.115e9) | Inspected gap=0,1,5,8 cases, retained the prescribed formula and set population-symmetry tolerance to 1e-10; retested neutrality, RH oddness and Rs evenness | Over-strict numerical test assumption; not a confirmed physics-model error |
| E05 | Two documentation edits initially used an invalid patch structure or an incomplete exact-match context | Patch tool rejected a duplicate target operation and an unmatched ledger paragraph | Reissued a supported file replacement and exact paragraph edit, then checked the resulting diff | Editing-tool error; not a physics error |

No genuine AI-generated physics-model error has been confirmed at this stage. Reference-value differences between the brief and methods guide are documented as a source discrepancy, not falsely attributed to AI. The teacher normally expects at least two genuine physics-error examples for full ledger marks; that requirement remains unfulfilled until such errors actually occur and are documented.

Future entries must preserve the actual claim/code, failed check with observed and expected values, correction, physical reason, verification and relevant commit. Students should add only events they can substantiate.

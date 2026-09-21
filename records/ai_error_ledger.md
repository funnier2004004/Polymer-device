# AI error ledger

Record only observed errors. Do not create deliberate mistakes to meet a mark target.

| ID | Actual AI action or claim | Evidence detecting it | Correction | Category / status |
|---|---|---|---|---|
| E01 | During preparation, attempted to read regular_G05-era files from the earlier top-level data layout (the actual attempted example paths used regular_G01) | File-not-found output; directory listing showed the supplied pack had moved under data/ | Re-resolved the current data layout and subsequently used data/03_Regular_Data/regular_G05 | File-path error; not a physics error and not offered as an 8-mark physics-ledger example |
| E02 | Assumed bundled Python had Matplotlib installed when checking imports | ModuleNotFoundError: No module named matplotlib | Provisioned a project-local environment and installed the pinned plotting dependency; physics still uses the teacher's NumPy definitions | Environment assumption; not a physics error |

No genuine AI-generated physics error has been confirmed at this stage. Reference-value differences between the brief and methods guide are documented as a source discrepancy, not falsely attributed to AI. The teacher normally expects at least two genuine physics-error examples for full ledger marks; that requirement remains unfulfilled until such errors actually occur and are documented.

Future entries must preserve the actual claim/code, failed check with observed and expected values, correction, physical reason, verification and relevant commit. Students should add only events they can substantiate.

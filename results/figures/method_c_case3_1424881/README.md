# PBS 1424881 cycle mesh evidence

Seven full-view physical mesh images and a seven-panel overview use the same x/y framing and equal aspect ratio. Six tip zooms use x from the same-numbered state JSON and y=70 mm as requested; each spans 8 x 8 mm. Cycle 7's tip-zoom file is an explicit missing-state placeholder, not a rendered mesh inset. No tip position was inferred. Red crosses locate the requested zoom centre; these are not damage contours.

The authentic scratch decks contain **7043, 7699, 7809, 8477, 9468, 16741, 25900** elements. These differ from the supplied counts for Cycles 1–4 and 7. Counts come from actual `*ELEMENT` records, checked with an independent block-count parser. Source hashes and modification times matched before and after read-only acquisition. The files were neither moved nor overwritten. Reading can update filesystem access times; preservation claims concern file content and modification times.

`manifest.json` lists every PNG hash and source count, source deck/state hashes, and the common viewport. `source_integrity.json` records before/after source integrity. `review_evidence.json` records verification and limitations. Mesh geometry alone does not establish convergence, damage evolution, or scientific acceptance.

Rendering was performed in a fresh partial clone on `codex/render-1424881-meshes`. No AGY checkout, session, coordination, orchestrator, deck or test-suite file was changed. No PBS job or solver was run; the user-stated cumulative count of 71 is preserved. Main remains unmodified by this work; merge is pending AGY release.

Reproduction: `py -3 results/figures/method_c_case3_1424881/render_meshes.py` from the isolated repository root, with matplotlib/numpy installed and the read-only acquisition JSON in `.git/acquired.json`. Acquisition records use `name`, `exists`, base64 `data`, `sha256`, and `mtime_ns` for the seven exact `_PHYS.inp` and matching `_state.json` filenames. Large acquisition data is intentionally not committed. Fetch authentic sources from the stated scratch run directory, verify hashes against the manifest, and never generate a substitute state for Cycle 7.

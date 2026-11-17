# F1850 existing-donor recovery and reconstruction

Master OPEN. Zero new PBS; cumulative 36 unchanged. F1849 candidate source remains unchanged. Existing source ODBs opened read-only; no donor solve. This is offline CONSTRUCTED_DAMAGE_ENVELOPE comparison, not native MISESERI or causal prediction.

|Case|F1779 count|Fresh count|Quads %|min detJ|max AR|far/core|
|---|---:|---:|---:|---:|---:|---:|
|1|20232|20193|97.30|1.026e-06|2.469|1.919|
|2|17280|17280|97.25|4.939e-07|2.646|2.205|
|3|9975|45009|97.29|0.001136|2.922|2.004|
|5|15330|4375|96.59|6.472e-06|2.525|1.338|

Case2 and Case5 reproduce F1849 counts exactly (17,280 and 4,375). Case1 is 20,193 versus 20,232 (-0.19%); no exact reproduction claimed. Case3 is 45,009 versus 9,975 (+351.22%). A uniform damage strategy is therefore not qualified as reproducing F1779 across four benchmarks. Case3 F1779 used selected stress-recovery states, and Case5 used native stress-error fields, so their original counts are not damage-framework controls.

## Accessible donor evidence
Four compact JSON snapshots contain every selected element connectivity, node coordinate, and MISESERI/MISESAVG/EVOL value used for remeshing, plus original ODB hash, size, step and frame metadata. Local reconstruction read-back confirmed exact scalar field equality before remeshing. These are lossless sizing-input snapshots, not complete ODB/physics histories. The repository forbids committing binary ODBs, so text snapshots provide a reviewable alternative to the requested reduced binary ODB. Reviewer must decide whether this evidence is sufficient.
Case1 reuses an existing envelope; Case2 reuses calibrated envelope v2. Their construction history is not newly reconstructed. Case3 is constructed from genuine existing Step-2 SDV1, every fifth frame plus final, with frozen damage thresholds. Case5 snapshot preserves the F1849 constructed envelope. All source hashes and sampled frames are in the summary and snapshots.

## Preserved implementation failures
Initial export failed on numpy.float32 JSON coordinates; fixed by explicit float conversion before writing. Remote wrapper timed out after 60 s, but exact-target inspection proved both exports completed; no duplicate export or solver submission. First CAE reconstruction failed because 2D nodes need two coordinates; corrected. Python2/3 JSON float serialization hashes differ, so canonical text hashes are validated under Python3 and actual scalar values separately round-trip under CAE. Explicit constructed-driver flag restored. Failed incomplete ODB retained locally and excluded from Git.

## Limitations
Element counts, geometric validity and visual localization do not establish fracture accuracy. No new fracture solves were run. Critical-region masks are inherited audits and are not future crack instructions. No parameter tuning or framework change was performed to hide negative cases. More complete per-donor provenance and generic performance remain subject to independent review.

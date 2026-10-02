# Implementation Decision Map

| Decision | Default | Evidence Needed To Change | Current Status |
|---|---|---|---|
| Active Thesis Task | Task 5: Reproduce Reference Results WITH Mesh Refinement | Supervisor instruction | **ACTIVE (TASK 5) — Solver Job 1398807 RUNNING** |
| Task 4 Milestone | Python Adaptive Remeshing Implementation | Supervisor instruction | **COMPLETE_VERIFIED_END_TO_END (0 mismatches, 11/11 tests PASS)** |
| First reproduction target | Pandey & Kumar (2025) Mode-I Single-Edge Notch Benchmark | Supervisor requires another benchmark first | **SET TO MODE-I (Task 5: Proposed Adaptive PFM solver 1398807)** |
| Datacheck status | Mandatory before production submission | Predeclared validation gate | **1398806.mmaster02 COMPLETED (EXIT: 0, 0 errors)** |
| Production solver status | PBS execution on cluster | Live scheduler telemetry | **1398807.mmaster02 RUNNING on mnode097/0** |
| Evolving remesh | Mandatory thesis branch after state-transfer proof | Supervisor explicitly removes it from scope | **Enabling Cycle-2 completed & closed** |
| Tolerances | Provisional only until approved | Supervisor-approved numeric gates | Predeclared errorTarget 1%–5% enforced |
| Runtime | Local/static validation first; HPC after maintenance/qualification | Local Abaqus availability and license confirmation | 11/11 regression tests PASS locally + Headless CAE smoke test PASS on cluster |
| Coarsening | Disabled for first irreversible-fracture baseline (`coarseningFactor=NOT_ALLOWED`) | Specific verified reason to allow coarsening | Enforced per Pandey & Kumar (2025) Listing 1 |
| Validation claim | Requires predeclared quantitative and qualitative gates | No exception | Enforced |
| Git initialization | Separate explicit decision | User asks to initialize repository | Maintained |

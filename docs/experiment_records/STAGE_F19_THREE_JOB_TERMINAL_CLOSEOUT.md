# Stage F19 three-job terminal closeout

Task `F19-AUTHORIZED-THREE-JOB-EXECUTION` executed exactly `M2IRRROLLCTL5`
(`1381758.mmaster02`), `M2IRRROLLFORCE5` (`1381759.mmaster02`), and
`M2RMREG6` (`1381760.mmaster02`) from preparation `d63181c3c4a58d173b7d2ca0c96af10e3ccd9fbd`.
Authorization `c81906a27b4f11028e3818c62da272d7f4a41cae` is consumed at 3/3.
No retry, replacement, rerun, qdel, qmove, or additional submission occurred.

## Scheduler

All jobs ran on `mnode099` in `normal_imfdfkmq` with 1 CPU and 8 GB.

| Job | PBS exit | Walltime | CPU | Memory |
|---|---:|---:|---:|---:|
| control | 11 | 00:03:07 | 00:00:24 | 355832 kb |
| forced | 11 | 00:02:47 | 00:00:24 | 352656 kb |
| adaptive | 1 | 00:00:06 | 00:00:01 | 214996 kb |

Exact qstat and tracejob records are retained under
`runs/hpc/stage_f/f19_f18_failure_closeout_and_three_job_repair_preparation/evidence/`.

## Rollback lanes

Both Abaqus analyses completed to `U1 = 0.006000000052 mm`, reaching the same
peak RF1 `0.0347024991061` at `U1 = 0.000720000011 mm`. Control completed 100
increments with zero cutbacks; forced completed 101 increments with one
deliberate cutback. Final RF1 was `0.000192419156` and `0.000184308137`.

The flag-I/O harness passed. Penalty activation occurred four times in control
and six times in forced; the first trigger was step 2, increment 4, element 6,
integration point 1. Forced returned `PNEWDT=0.5`; control returned no
reduction. Extracted fields are finite; minimum SDV15 change is
`-5.9604645e-8`, and minimum SDV16 change is zero.

The extractor generated `rf_u_work_history.csv`, `fixed_point_history.csv`,
and `diagnostic_energy_history.csv`, while the frozen analyzer required
differently named tables. Both lanes therefore classify as
`penalty_activation_evidence_incomplete`; response equivalence and
accepted-state rollback are not qualified.

## Adaptive lane

The compatibility helper passed under Abaqus Python 2.7.15, and source-ODB
hash/readability plus output-directory checks passed. CAE then failed because
Abaqus Python rejected a generator in `sum(len(x.elements) for x in
m.parts.values())`. There were zero solver, adaptivity-process, native-remesh,
candidate, datacheck, and refined-analysis executions. Classification:
`native_adaptive_region_construction_failed`.

Telegram START and terminal evidence passed for all three jobs; PBS email is
best-effort. The inventory covers 52 collected lightweight files plus itself.
ODBs remain scratch-only and are not committed. No figures were generated
because the formal rollback comparison gate is incomplete.

Final classification:
`f19_rollback_activation_observed_but_comparison_evidence_incomplete_and_adaptive_construction_failed`.
This does not establish rollback equivalence, native adaptive construction,
remeshing, mesh/time convergence, H1/H2 behavior, scalability, parallel
safety, experimental validation, or paper-level agreement.

Closure revision: `PENDING_METADATA_COMMIT`.

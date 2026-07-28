# Current project state

Updated: 2026-07-28
Protocol version: 1
Classification: `stage_f_mode_ii_h1_uniform_solver_submitted`

## Git

| Item | Value |
|---|---|
| Active job ID | `1379433.mmaster02` |
| H1 datacheck job ID | `1379431.mmaster02` |
| H1 baseline preparation revision | `3b44b375b42dfd0cf88c7f3e82d0ea80c4ef7f0d` |
| Active agent | none |
| Active task | **F2-H1-SOLVER** submitted (`stage_f_mode_ii_h1_uniform_solver_submitted`) |

## Submission boundary (critical)

```text
Current task: F2-H1-SOLVER submitted
Status: stage_f_mode_ii_h1_uniform_solver_submitted
active_job_id: 1379433.mmaster02
datacheck_authorized: false (consumed)
solver_authorized: false (consumed)
submission_approved: false
execution_authorized: false
maximum_jobs_now: 0
automatic_retry_authorized: false
```

Stage F Mode-II H1 uniform reference solver job `1379433.mmaster02` submitted and currently running (`stage_f_mode_ii_h1_uniform_solver_submitted`).
Requested resources: 1 CPU, 32 GB RAM, 06:00:00 walltime on queue `entry_imfdfkmq` (execution host: `mnode104/0`).
Telegram `SUBMITTED` notification received (`telegram_ok event=SUBMITTED job=1379433.mmaster02`).
Submission evidence recorded in `runs/hpc/stage_f/mode_ii_h1/solver_submission/1379433.mmaster02/`.

## Stage F H1 baseline package

- Package: `models/generated/mode_ii/h1_uniform_serial`
- Mesh size: $h_1 = 0.0025\text{ mm}$ ($h_1/\ell_c = 0.1667$)
- Element count: 12,064 physical, 36,192 layered (UEL/UMAT)
- Node count: 12,382
- Fortran `N_ELEM`: 12,064 (byte-identical UEL/UMAT formulation)
- Deck SHA-256: `613398be7cd1c9061cbb469beb4130188512a2f6d25cf3d78b6364eb3255342f`
- Source SHA-256: `745db8fcfb612895e0289f4533c90d204cc9b2ade3678a035614feeb308b5ead`

## Next Task

`F2-H1-SOLVER-CLOSE`: Close out, collect evidence, and scientifically classify Stage F Mode-II H1 uniform reference solver job `1379433.mmaster02`.

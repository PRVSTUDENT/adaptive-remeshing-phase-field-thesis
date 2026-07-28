# Current project state

Updated: 2026-07-28
Protocol version: 1
Classification: `stage_f_mode_ii_h1_uniform_serial_validation_fail`

## Git

| Item | Value |
|---|---|
| Active job ID | none |
| Closed H1 solver job ID | `1379433.mmaster02` |
| H1 datacheck job ID | `1379431.mmaster02` |
| H1 baseline preparation revision | `3b44b375b42dfd0cf88c7f3e82d0ea80c4ef7f0d` |
| Active agent | none |
| Active task | **F2-H1-SOLVER-CLOSE** complete (`stage_f_mode_ii_h1_uniform_serial_validation_fail`) |

## Submission boundary (critical)

```text
Current task: F2-H1-SOLVER-CLOSE complete
Status: complete_failed
Classification: stage_f_mode_ii_h1_uniform_serial_validation_fail
active_job_id: none
datacheck_authorized: false (consumed)
solver_authorized: false (consumed)
submission_approved: false
execution_authorized: false
maximum_jobs_now: 0
automatic_retry_authorized: false
```

Stage F Mode-II H1 uniform reference solver job `1379433.mmaster02` has finished execution and has been closed out.
- **Abaqus Solver:** `Abaqus JOB mode_ii_h1_serial COMPLETED` (2,500 increments total, exit code 0).
- **Scheduler & Resources:** Walltime `00:42:59`, CPU time `00:41:26`, Memory `1,064,056 KB` (~1.01 GB) on host `mnode104/0`.
- **Scientific Classification:** `stage_f_mode_ii_h1_uniform_serial_validation_fail` (pre-peak damage $d = 0.2747 < 0.50$ at loading endpoint $U_1 = 0.010\text{ mm}$).
- **Evidence Path:** `runs/hpc/stage_f/mode_ii_h1/evidence/1379433.mmaster02/`.

## Stage F H1 baseline package

- Package: `models/generated/mode_ii/h1_uniform_serial`
- Mesh size: $h_1 = 0.0025\text{ mm}$ ($h_1/\ell_c = 0.1667$)
- Element count: 12,064 physical, 36,192 layered (UEL/UMAT)
- Node count: 12,382
- Fortran `N_ELEM`: 12,064
- Deck SHA-256: `613398be7cd1c9061cbb469beb4130188512a2f6d25cf3d78b6364eb3255342f`
- Source SHA-256: `745db8fcfb612895e0289f4533c90d204cc9b2ade3678a035614feeb308b5ead`

## Next Action

Wait for explicit human decision regarding Stage F Mode-II loading endpoint expansion. All submission flags remain false (`maximum_jobs_now = 0`).

# Current project state

Updated: 2026-07-26
Protocol version: 1
Classification: `stage_f_mode_ii_h0_serial_fail`

## Git

| Item | Value |
|---|---|
| Operational submission revision | `5b092853419e8e8829d7f4c024ce3ea78d131740` |
| Authorization revision | `44d928a00f77c3e6b0515c3d045b1be2ab4bb9a9` |
| Datacheck revision | `4ff884c23b3b7bcefbffd0605fd8d2bf5f1b400b` |
| Active agent | none |
| Active task | **F1-J1** failed_execution_blocked |

## Submission boundary (critical)

```text
Current task: F1-J1 complete (failed)
Status: stage_f_mode_ii_h0_serial_fail
solver_job_id: 1378919.mmaster02 (PBS exit 7; staging fail)
routed_queue: normal_imfdfkmq
datacheck_job_id: 1378911.mmaster02 (pass)
solver_preparation_complete: true
solver_authorized: false (consumed by job submission)
submission_approved: true
solver_submissions_used: 1
maximum_solver_submissions: 1
automatic_retry_authorized: false
maximum_additional_jobs_now: 0
```

F1-J1 serial solver job `1378919.mmaster02` failed before Abaqus launch with PBS `Exit_status = 7` due to runtime staging deck hash mismatch (`stage_f_mode_ii_h0_serial_staging_fail`).
The single authorized solver submission is fully consumed (`solver_submissions_used: 1`). No additional qsub submissions or retry executions are permitted (`automatic_retry_authorized: false`).
Downstream task F2 remains **blocked**.

## Stage F package (submission consumed, failed execution)

- Package: `models/generated/mode_ii/h0_serial`
- Auth file: `runs/hpc/stage_f/mode_ii_h0/MODE_II_H0_AUTHORIZATION.json`
- Prep record: `runs/hpc/stage_f/mode_ii_h0/solver_prep/F1_J1_PREPARATION.json`
- Experiment record: `docs/experiment_records/STAGE_F1_J1_MODE_II_SERIAL_BASELINE.md`
- Evidence path: `runs/hpc/stage_f/mode_ii_h0/evidence/1378919.mmaster02/`
- Deck SHA-256: `32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b`
- Source SHA-256: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`

## Next actions

1. Wait for explicit human instruction/decision regarding F1-J1 failure and authorization policy.
2. Downstream tasks (F2+) remain blocked.

## Dirty paths

Pre-existing local porcelain remains preserved; not cleaned.

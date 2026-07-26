# Current project state

Updated: 2026-07-26
Protocol version: 1
Classification: `stage_f_mode_ii_h0_solver_submitted`

## Git

| Item | Value |
|---|---|
| Operational submission revision | `5b092853419e8e8829d7f4c024ce3ea78d131740` |
| Authorization revision | `44d928a00f77c3e6b0515c3d045b1be2ab4bb9a9` |
| Datacheck revision | `4ff884c23b3b7bcefbffd0605fd8d2bf5f1b400b` |
| Active agent | `gemini-antigravity` |
| Active task | **F1-J1** submitted_running |

## Submission boundary (critical)

```text
Current task: F1-J1 submitted_running
Status: stage_f_mode_ii_h0_solver_submitted
solver_job_id: 1378919.mmaster02
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

F1-J1 serial solver job `1378919.mmaster02` has been submitted and is currently executing (`job_state = R`, host `mnode098/0`).
The single authorized solver submission is fully consumed (`solver_submissions_used: 1`). No additional qsub submissions or retry executions are permitted.

## Stage F package (submitted & running)

- Package: `models/generated/mode_ii/h0_serial`
- Auth file: `runs/hpc/stage_f/mode_ii_h0/MODE_II_H0_AUTHORIZATION.json`
- Prep record: `runs/hpc/stage_f/mode_ii_h0/solver_prep/F1_J1_PREPARATION.json`
- Deck SHA-256: `32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b`
- Source SHA-256: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`
- Resource plan: 1 CPU, 16 GB RAM, 04:00:00 walltime, queue `entry_imfdfkmq` -> `normal_imfdfkmq`

## Next actions

1. Monitor job `1378919.mmaster02` to completion.
2. Upon completion, verify evidence, extraction, and validation outputs, and record closure state.

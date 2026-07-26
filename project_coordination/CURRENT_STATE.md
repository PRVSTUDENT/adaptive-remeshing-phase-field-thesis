# Current project state

Updated: 2026-07-26
Protocol version: 1
Classification: `stage_f_mode_ii_h0_solver_authorized`

## Git

| Item | Value |
|---|---|
| Authorization parent revision | `b52b92a3162571d0e6d8817a8e027adb74d54464` |
| Datacheck revision | `4ff884c23b3b7bcefbffd0605fd8d2bf5f1b400b` |
| Requalification parent revision | `309e65c09ead47659c26e6b03f0cf9f410755bd5` |
| Active agent | none |
| Active task | **F1-J1** ready_pending_submission_approval |

## Authorization boundary (critical)

```text
Current task: F1-J1-AUTH complete -> F1-J1 ready_pending_submission_approval
Status: stage_f_mode_ii_h0_solver_authorized
datacheck_job_id: 1378911.mmaster02 (pass)
solver_preparation_complete: true
solver_authorized: true
submission_approved: false
solver_submissions_used: 0
maximum_solver_submissions: 1
automatic_retry_authorized: false
maximum_additional_jobs_now: 0
```

F1-J1 serial solver submission is **authorized** in metadata (`solver_authorized: true`), but submission remains strictly **blocked** pending separate explicit submission approval (`submission_approved: false`). No qsub or solver job execution is authorized without separate explicit human submission approval.

## Stage F package (solver authorized, submission pending)

- Package: `models/generated/mode_ii/h0_serial`
- Auth file: `runs/hpc/stage_f/mode_ii_h0/MODE_II_H0_AUTHORIZATION.json`
- Prep record: `runs/hpc/stage_f/mode_ii_h0/solver_prep/F1_J1_PREPARATION.json`
- Deck SHA-256: `32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b`
- Source SHA-256: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`
- Resource plan: 1 CPU, 16 GB RAM, 04:00:00 walltime, queue `entry_imfdfkmq`

## Next actions

1. Wait for separate explicit human submission approval for F1-J1 serial solver job submission.

## Dirty paths

Pre-existing local porcelain remains preserved; not cleaned.

# Current project state

Updated: 2026-07-26
Protocol version: 1
Classification: `stage_f_mode_ii_h0_serial_preparation_requalified`

## Git

| Item | Value |
|---|---|
| Authorization parent revision | `cddf916c8422f5f87152205f078e5e8f019e1afd` |
| Datacheck revision | `4ff884c23b3b7bcefbffd0605fd8d2bf5f1b400b` |
| Requalification parent revision | `b8da554a2ef443156095be959f0dca10005c26f8` |
| Active agent | none |
| Active task | **F1-J1-AUTH** ready_pending_authorization |

## Authorization boundary (critical)

```text
Current task: F1-J1-PREP-R1 complete -> F1-J1-AUTH ready
Status: stage_f_mode_ii_h0_serial_preparation_requalified
datacheck_job_id: 1378911.mmaster02 (pass)
solver_preparation_complete: true
solver_authorized: false
solver_submissions_used: 0
maximum_solver_submissions: 1
automatic_retry_authorized: false
maximum_additional_jobs_now: 0
```

F1-J1-PREP-R1 serial solver requalification is complete.
Full solver analysis remains strictly **unauthorized**. No F1-J1 submission or job execution is authorized without a separate explicit `F1-J1-AUTH` authorization commit and submission approval.

## Stage F package (solver prepared & requalified, unauthorized)

- Package: `models/generated/mode_ii/h0_serial`
- Auth file: `runs/hpc/stage_f/mode_ii_h0/MODE_II_H0_AUTHORIZATION.json`
- Prep record: `runs/hpc/stage_f/mode_ii_h0/solver_prep/F1_J1_PREPARATION.json`
- Deck SHA-256: `32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b`
- Source SHA-256: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`
- Resource plan: 1 CPU, 16 GB RAM, 04:00:00 walltime, queue `entry_imfdfkmq`

## Next actions

1. **F1-J1-AUTH**: Wait for explicit human authorization commit for serial solver execution
2. Solver execution remains unauthorized until explicit separate human authorization.

## Dirty paths

Pre-existing local porcelain remains preserved; not cleaned.

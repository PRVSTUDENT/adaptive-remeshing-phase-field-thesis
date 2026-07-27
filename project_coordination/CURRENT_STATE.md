# Current project state

Updated: 2026-07-27
Protocol version: 1
Classification: `stage_f_mode_ii_h0_second_replacement_solver_submitted`

## Git

| Item | Value |
|---|---|
| R2 replacement submission revision | `69d4d0a6ade66f4c0a1ea47020eb6e8916c11abd` |
| R2 replacement authorization revision | `93fcad353693ca6348b2d683317c7da86d34d493` |
| Evidence verifier commit | `7f61c182aaa480b20647410546007d0ee20a3132` |
| R2 preparation parent revision | `e262f30666811bcd52a09332ca03b6677566df3b` |
| R1 replacement submission revision | `46cf420b995ff6b2f74fecfc10fb1bb4411feaac` |
| R1 replacement authorization revision | `2f6a0f6efc992b85c9ae79ff9006ebadd9bf81d8` |
| Original submission revision | `5b092853419e8e8829d7f4c024ce3ea78d131740` |
| Datacheck revision | `4ff884c23b3b7bcefbffd0605fd8d2bf5f1b400b` |
| Active agent | none |
| Active task | **F1-J1-R2** submitted (`stage_f_mode_ii_h0_second_replacement_solver_submitted`) |

## Submission boundary (critical)

```text
Current task: F1-J1-R2 submitted (pending execution outcome)
Status: stage_f_mode_ii_h0_second_replacement_solver_submitted
active_job_id: 1378942.mmaster02
source_failure_job_ids: 1378919.mmaster02, 1378920.mmaster02 (both authorizations consumed)
replacement_r2_authorized: false (single submission authorization consumed by 1378942.mmaster02)
submission_approved: true
execution_authorized: false
maximum_jobs_now: 0
automatic_retry_authorized: false
```

Both initial solver run `1378919.mmaster02` (F1-J1) and replacement solver run `1378920.mmaster02` (F1-J1-R1) consumed their single authorized submissions and failed before Abaqus launch due to staging validation defects.
Task `F1-J1-R2` was explicitly approved and submitted to PBS queue `entry_imfdfkmq` under job ID `1378942.mmaster02`. The R2 authorization record `runs/hpc/stage_f/mode_ii_h0/replacement_r2/MODE_II_H0_R2_AUTHORIZATION.json` has been consumed (`solver_submissions_used: 1`, `solver_job_id: 1378942.mmaster02`). No further submissions or retries are permitted.
Downstream task F2 remains **blocked**.

## Stage F package (R2 replacement solver submitted, job 1378942.mmaster02)

- Package: `models/generated/mode_ii/h0_serial`
- Active PBS Job ID: `1378942.mmaster02`
- Queue: `entry_imfdfkmq` (routed to `normal_imfdfkmq`)
- Staging Verifier Script: `scripts/validation/verify_mode_ii_h0_runtime_staging.py`
- Pre-Solver Smoke Script: `scripts/validation/run_pre_solver_smoke.py`
- Local Smoke Bundle: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence_r3/local/EVIDENCE_BUNDLE_MANIFEST.json`
- Cluster Smoke Bundle: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence_r3/cluster_login/EVIDENCE_BUNDLE_MANIFEST.json`
- R2 Authorization Record: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/MODE_II_H0_R2_AUTHORIZATION.json`
- Deck SHA-256: `32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b`
- Source SHA-256: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`

## Next actions

1. Monitor job `1378942.mmaster02` execution via `qstat`.
2. Upon job completion, collect logs, verify runtime staging contract, extract results, and record closure.
3. Downstream tasks (F2+) remain blocked.

## Dirty paths

Pre-existing local porcelain remains preserved; not cleaned.

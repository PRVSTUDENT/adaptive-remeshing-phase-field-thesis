# Current project state

Updated: 2026-07-26
Protocol version: 1
Classification: `stage_f_mode_ii_h0_replacement_solver_submitted`

## Git

| Item | Value |
|---|---|
| Replacement submission revision | `46cf420b995ff6b2f74fecfc10fb1bb4411feaac` |
| Replacement authorization revision | `2f6a0f6efc992b85c9ae79ff9006ebadd9bf81d8` |
| Replacement preparation revision | `61438db7a6b21b4677fb44693288638e5a104a92` |
| Original submission revision | `5b092853419e8e8829d7f4c024ce3ea78d131740` |
| Datacheck revision | `4ff884c23b3b7bcefbffd0605fd8d2bf5f1b400b` |
| Active agent | `gemini-antigravity` |
| Active task | **F1-J1-R1** submitted_running |

## Submission boundary (critical)

```text
Current task: F1-J1-R1 submitted_running
Status: stage_f_mode_ii_h0_replacement_solver_submitted
replacement_job_id: 1378920.mmaster02 (running on mnode098/0)
routed_queue: normal_imfdfkmq
source_failure_job_id: 1378919.mmaster02 (original authorization consumed 1/1)
replacement_authorized: false (consumed by job 1378920.mmaster02)
replacement_submissions_used: 1
maximum_replacement_submissions: 1
submission_approved: true
automatic_retry_authorized: false
maximum_additional_jobs_now: 0
```

Replacement solver job `1378920.mmaster02` was submitted to queue `entry_imfdfkmq` and routed to `normal_imfdfkmq` on host `mnode098/0`.
The single replacement solver authorization is fully consumed (`replacement_submissions_used: 1`). No additional qsub submissions or retries are permitted (`automatic_retry_authorized: false`).

## Stage F package (replacement submitted, running)

- Package: `models/generated/mode_ii/h0_serial`
- Replacement auth file: `runs/hpc/stage_f/mode_ii_h0/replacement_r1/MODE_II_H0_R1_AUTHORIZATION.json`
- Replacement prep record: `runs/hpc/stage_f/mode_ii_h0/replacement_r1/F1_J1_R1_PREPARATION.json`
- Replacement job ID: `1378920.mmaster02`
- Deck SHA-256: `32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b`
- Source SHA-256: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`

## Next actions

1. Monitor PBS job `1378920.mmaster02` without intervention until completion.
2. Collect outputs and run result validation.

## Dirty paths

Pre-existing local porcelain remains preserved; not cleaned.

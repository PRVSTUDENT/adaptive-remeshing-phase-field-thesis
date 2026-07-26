# Current project state

Updated: 2026-07-26
Protocol version: 1
Classification: `stage_f_mode_ii_h0_replacement_solver_authorized`

## Git

| Item | Value |
|---|---|
| Parent authorization revision | `bfb89b30d9494d9fa130574f0a0591c8c3152258` |
| Replacement preparation revision | `61438db7a6b21b4677fb44693288638e5a104a92` |
| Original submission revision | `5b092853419e8e8829d7f4c024ce3ea78d131740` |
| Original auth revision | `44d928a00f77c3e6b0515c3d045b1be2ab4bb9a9` |
| Datacheck revision | `4ff884c23b3b7bcefbffd0605fd8d2bf5f1b400b` |
| Active agent | none |
| Active task | **F1-J1-R1** ready_pending_submission_approval |

## Authorization boundary (critical)

```text
Current task: F1-J1-R1 ready_pending_submission_approval
Status: stage_f_mode_ii_h0_replacement_solver_authorized
source_failure_job_id: 1378919.mmaster02 (original authorization consumed 1/1)
replacement_authorized: true
replacement_submissions_used: 0
maximum_replacement_submissions: 1
submission_approved: false
execution_authorized: false
maximum_additional_jobs_now: 0
```

Replacement solver authorization record created in `runs/hpc/stage_f/mode_ii_h0/replacement_r1/MODE_II_H0_R1_AUTHORIZATION.json`.
Submission remains **blocked** (`submission_approved: false`, `execution_authorized: false`) until separate explicit submission approval is granted.

## Stage F package (replacement authorized, submission pending approval)

- Package: `models/generated/mode_ii/h0_serial`
- Original auth file: `runs/hpc/stage_f/mode_ii_h0/MODE_II_H0_AUTHORIZATION.json` (consumed 1/1)
- Replacement auth file: `runs/hpc/stage_f/mode_ii_h0/replacement_r1/MODE_II_H0_R1_AUTHORIZATION.json`
- Replacement prep record: `runs/hpc/stage_f/mode_ii_h0/replacement_r1/F1_J1_R1_PREPARATION.json`
- Deck SHA-256: `32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b`
- Source SHA-256: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`

## Next actions

1. Wait for separate explicit human submission approval for task F1-J1-R1.
2. Downstream Stage F tasks (F2+) remain blocked.

## Dirty paths

Pre-existing local porcelain remains preserved; not cleaned.

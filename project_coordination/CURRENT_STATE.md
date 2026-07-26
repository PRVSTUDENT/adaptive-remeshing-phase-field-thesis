# Current project state

Updated: 2026-07-26
Protocol version: 1
Classification: `stage_f_mode_ii_h0_serial_replacement_prepared_unauthorized`

## Git

| Item | Value |
|---|---|
| Preparation parent revision | `d569775f7c5b4ce109260ff3892499476ccd7b5d` |
| Operational submission revision | `5b092853419e8e8829d7f4c024ce3ea78d131740` |
| Authorization revision | `44d928a00f77c3e6b0515c3d045b1be2ab4bb9a9` |
| Datacheck revision | `4ff884c23b3b7bcefbffd0605fd8d2bf5f1b400b` |
| Active agent | none |
| Active task | **F1-J1-R1-AUTH** ready_pending_decision |

## Authorization boundary (critical)

```text
Current task: F1-J1-R1-PREP complete -> F1-J1-R1-AUTH ready_pending_decision
Status: stage_f_mode_ii_h0_serial_replacement_prepared_unauthorized
source_failure_job_id: 1378919.mmaster02 (consumed 1/1)
staging_defect_repaired: true (offline dual-deck contract verified)
replacement_authorized: false
submission_approved: false
solver_submissions_used: 1 (original authorization)
maximum_solver_submissions: 1
automatic_retry_authorized: false
maximum_additional_jobs_now: 0
```

The M-090 staging defect has been repaired offline and verified by unit tests.
Replacement solver submission remains strictly **unauthorized**. No job execution or qsub submission is permitted without an explicit human replacement decision and separate authorization record.

## Stage F package (replacement prepared, unauthorized)

- Package: `models/generated/mode_ii/h0_serial`
- Auth file: `runs/hpc/stage_f/mode_ii_h0/MODE_II_H0_AUTHORIZATION.json`
- Replacement prep: `runs/hpc/stage_f/mode_ii_h0/replacement_r1/F1_J1_R1_PREPARATION.json`
- Replacement record: `docs/experiment_records/STAGE_F1_J1_R1_MODE_II_REPLACEMENT_PREPARATION.md`
- Deck SHA-256: `32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b`
- Source SHA-256: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`

## Next actions

1. Wait for explicit human decision on whether a replacement authorization decision (F1-J1-R1-AUTH) should be created.
2. Downstream Stage F tasks (F2+) remain blocked.

## Dirty paths

Pre-existing local porcelain remains preserved; not cleaned.

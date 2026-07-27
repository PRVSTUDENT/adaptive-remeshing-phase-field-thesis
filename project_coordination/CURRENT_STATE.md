# Current project state

Updated: 2026-07-27
Protocol version: 1
Classification: `stage_f_mode_ii_h0_second_replacement_provenance_qualified_unauthorized`

## Git

| Item | Value |
|---|---|
| Runtime provenance commit | `620a4e01038991b89cef70091afb03e70c6922f7` |
| R2 preparation parent revision | `440ff8a22fcfd7a2674ad9ec5de76d2b0f8b271b` |
| R1 replacement submission revision | `46cf420b995ff6b2f74fecfc10fb1bb4411feaac` |
| R1 replacement authorization revision | `2f6a0f6efc992b85c9ae79ff9006ebadd9bf81d8` |
| R1 replacement preparation revision | `61438db7a6b21b4677fb44693288638e5a104a92` |
| Original submission revision | `5b092853419e8e8829d7f4c024ce3ea78d131740` |
| Datacheck revision | `4ff884c23b3b7bcefbffd0605fd8d2bf5f1b400b` |
| Active agent | none |
| Active task | **F1-J1-R2-PREP-R2** complete (`stage_f_mode_ii_h0_second_replacement_provenance_qualified_unauthorized`) |

## Submission boundary (critical)

```text
Current task: F1-J1-R2-PREP-R2 complete (provenance qualified unauthorized)
Status: stage_f_mode_ii_h0_second_replacement_provenance_qualified_unauthorized
source_failure_job_ids: 1378919.mmaster02, 1378920.mmaster02 (both authorizations consumed)
replacement_r2_authorized: false (offline & login-node preparation/qualification only; no authorization granted)
submission_approved: false
maximum_jobs_now: 0
automatic_retry_authorized: false
```

Both initial solver run `1378919.mmaster02` (F1-J1) and replacement solver run `1378920.mmaster02` (F1-J1-R1) consumed their single authorized submissions and failed before Abaqus launch due to staging validation defects.
Task `F1-J1-R2-PREP-R2` successfully qualified the Mode-II pre-solver smoke semantics and evidence provenance chain. Removed `"MODE_II_H0_SERIAL_ok": true` from pre-solver smoke status, added `"pre_solver_smoke_ok": true`, and verified raw `null` return codes for non-invoked tools. The smoke runner `run_pre_solver_smoke.py` now directly generates complete evidence bundles with SHA-256 manifest verification (`EVIDENCE_BUNDLE_MANIFEST.json`). Pre-solver smoke passed on cluster login node (`mlogin01.hrz.tu-freiberg.de`) with real module loading (`module_environment_loaded=true`), verified Abaqus executable (`/syscomp/abaqus/2023/Commands/abaqus`), PBS exit code 0, 0 Abaqus invocations, and 0 ODB files. Complete cluster bundle was copied and all file hashes verified (`PASSED: ALL BUNDLE HASHES VERIFIED`).
No replacement authorization or qsub submission is permitted (`replacement_r2_authorized: false`).
Downstream task F2 remains **blocked**.

## Stage F package (R2 replacement provenance qualified, unauthorized)

- Package: `models/generated/mode_ii/h0_serial`
- Staging Verifier Script: `scripts/validation/verify_mode_ii_h0_runtime_staging.py`
- Pre-Solver Smoke Script: `scripts/validation/run_pre_solver_smoke.py`
- Local Smoke Bundle: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence_r2/local/EVIDENCE_BUNDLE_MANIFEST.json`
- Cluster Smoke Bundle: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence_r2/cluster_login/EVIDENCE_BUNDLE_MANIFEST.json`
- R2 Replacement Prep Record: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/F1_J1_R2_PREPARATION.json`
- R2 Replacement Experiment Record: `docs/experiment_records/STAGE_F1_J1_R2_MODE_II_REPLACEMENT_PREPARATION.md`
- Deck SHA-256: `32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b`
- Source SHA-256: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`

## Next actions

1. Wait for explicit human instruction/decision regarding R2 replacement authorization (`F1-J1-R2-AUTH`).
2. Downstream tasks (F2+) remain blocked.

## Dirty paths

Pre-existing local porcelain remains preserved; not cleaned.

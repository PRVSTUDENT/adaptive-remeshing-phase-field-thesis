# Current project state

Updated: 2026-07-27
Protocol version: 1
Classification: `stage_f_mode_ii_h0_second_replacement_runtime_qualified_unauthorized`

## Git

| Item | Value |
|---|---|
| Main repair commit | `217b684cc5611377e495442728e39d350d01eb61` |
| R2 preparation parent revision | `4f67bd2c8fd0a1a1c2e57d8dba54cd16a2ff2a36` |
| R1 replacement submission revision | `46cf420b995ff6b2f74fecfc10fb1bb4411feaac` |
| R1 replacement authorization revision | `2f6a0f6efc992b85c9ae79ff9006ebadd9bf81d8` |
| R1 replacement preparation revision | `61438db7a6b21b4677fb44693288638e5a104a92` |
| Original submission revision | `5b092853419e8e8829d7f4c024ce3ea78d131740` |
| Datacheck revision | `4ff884c23b3b7bcefbffd0605fd8d2bf5f1b400b` |
| Active agent | none |
| Active task | **F1-J1-R2-PREP-R1** complete (`stage_f_mode_ii_h0_second_replacement_runtime_qualified_unauthorized`) |

## Submission boundary (critical)

```text
Current task: F1-J1-R2-PREP-R1 complete (runtime qualified unauthorized)
Status: stage_f_mode_ii_h0_second_replacement_runtime_qualified_unauthorized
source_failure_job_ids: 1378919.mmaster02, 1378920.mmaster02 (both authorizations consumed)
replacement_r2_authorized: false (offline & login-node preparation/qualification only; no authorization granted)
submission_approved: false
maximum_jobs_now: 0
automatic_retry_authorized: false
```

Both initial solver run `1378919.mmaster02` (F1-J1) and replacement solver run `1378920.mmaster02` (F1-J1-R1) consumed their single authorized submissions and failed before Abaqus launch due to staging validation defects.
Task `F1-J1-R2-PREP-R1` successfully qualified the Mode-II pre-solver smoke path on both local Windows (`runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence/local/SMOKE_SUMMARY.json`) and cluster login node (`runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence/cluster_login/SMOKE_SUMMARY.json`). Cluster login smoke passed with actual module loading (`module_environment_loaded=true`), verified Abaqus executable (`/syscomp/abaqus/2023/Commands/abaqus`), PBS exit code 0, zero Abaqus invocations, and zero ODB files. Restored fail-closed module loading in PBS script for solver runs.
No replacement authorization or qsub submission is permitted (`replacement_r2_authorized: false`).
Downstream task F2 remains **blocked**.

## Stage F package (R2 replacement runtime qualified, unauthorized)

- Package: `models/generated/mode_ii/h0_serial`
- Staging Verifier Script: `scripts/validation/verify_mode_ii_h0_runtime_staging.py`
- Pre-Solver Smoke Script: `scripts/validation/run_pre_solver_smoke.py`
- Local Smoke Summary: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence/local/SMOKE_SUMMARY.json`
- Cluster Smoke Summary: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence/cluster_login/SMOKE_SUMMARY.json`
- R2 Replacement Prep Record: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/F1_J1_R2_PREPARATION.json`
- R2 Replacement Experiment Record: `docs/experiment_records/STAGE_F1_J1_R2_MODE_II_REPLACEMENT_PREPARATION.md`
- Deck SHA-256: `32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b`
- Source SHA-256: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`

## Next actions

1. Wait for explicit human instruction/decision regarding R2 replacement authorization.
2. Downstream tasks (F2+) remain blocked.

## Dirty paths

Pre-existing local porcelain remains preserved; not cleaned.

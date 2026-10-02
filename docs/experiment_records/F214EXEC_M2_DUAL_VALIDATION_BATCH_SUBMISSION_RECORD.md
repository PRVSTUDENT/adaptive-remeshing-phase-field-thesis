# Mode-II Dual Validation Batch Submission Record (R7 and PK10R2)

**Task ID**: `F214EXEC-M2-DUAL-VALIDATION-BATCH-SUBMISSION1`  
**Date**: 17 August 2026  
**Status**: `SUBMISSION EXECUTED / PBS IDS RECORDED / RUNNING ON CLUSTER / GATES PRESERVED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

Under direct human authorization, the `M2_DUAL_VALIDATION_BATCH_R7_PK10R2` validation batch was verified and submitted to the HPC cluster.

### Submission Summary
1. **Job 1: Same-Mesh Restart Validation (Revision R7)**
   - **Job Name**: `M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7`
   - **PBS Job ID**: `1390037.mmaster02`
   - **Initial Status**: `R` (Running)
   - **Requested Resources**: 1 CPU, 16 GB RAM, 24:00:00 walltime
   - **Directory**: `projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7`
2. **Job 2: Corrected Topology Validation (Revision R2)**
   - **Job Name**: `M2CORR_PK10R2_TOPOLOGY_CORRECTED`
   - **PBS Job ID**: `1390038.mmaster02`
   - **Initial Status**: `Q` (Queued)
   - **Requested Resources**: 1 CPU, 16 GB RAM, 24:00:00 walltime
   - **Directory**: `projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED`

---

## 2. Pre-Submission Package Hashes Verification (100% Match)

| Package | Artifact | Relative Path | Verified Cluster SHA256 |
| :--- | :--- | :--- | :--- |
| **R7** | Input Deck | `.../M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7.inp` | `d20edf3a13f024b4ccb981dd86ec82fd7e91ba611451694b9cf313d0affcf750` |
| **R7** | UEL Subroutine | `.../f44_mixed_uel_restart_stateinit.for` | `de8326dfd28e66a82ba38496ee63869b86b5959e2cc35b010ebb28ae1dec6438` |
| **R7** | State Include | `.../PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp` | `9bd16f9a27cf7c7aa398af31f7e3c754bfab5e9ecf2825fd835dbd1340bd51e5` |
| **R7** | U3 Include | `.../PK10R1_INC29_U3_ONLY_BOUNDARY.inp` | `f54e4fefb92308ec302322cf4183cfa62ae5f89eeb37f1d8727034ea1ce167b8` |
| **R7** | Launcher | `.../submit_job.sh` | `36e5f0080dc8b947f384bb793f2a2251fb102c1b53cabf2cc22cb4601f89b827` |
| **PK10R2**| Input Deck | `.../M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp` | `667897fc42ee134be434cb5bc543796ce47ffd2024ec4d6c01d20e0abbd987be` |
| **PK10R2**| UEL Subroutine | `.../f42_mixed_uel.for` | `e0865b5eba43c14d21a733e72717e157d65c778319e6556e5eca8ab222364e58` |
| **PK10R2**| Launcher | `.../submit_job.sh` | `3532540a3c56c5e2a1baaf43d46c33ec71fc31f76dffde5eb9c7602291bffea4` |

---

## 3. Scientific Governance & Submission Invariants

- `same_mesh_restart_validation` = `SUBMITTED_RUNNING`
- `batch_name` = `M2_DUAL_VALIDATION_BATCH_R7_PK10R2`
- `job_1_name` = `M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7`
- `job_1_pbs_id` = `1390037.mmaster02`
- `job_2_name` = `M2CORR_PK10R2_TOPOLOGY_CORRECTED`
- `job_2_pbs_id` = `1390038.mmaster02`
- `total_submissions` = `2` (maximum allowed: 2)
- `qsub_called` = `true` (2 calls)
- `qdel_called` = `false`, `qmove_called` = `false`
- `git_commit_called` = `false`, `git_push_called` = `false`

# Mode-II Dual Validation Replacement Batch Submission Record (R7 and PK10R2)

**Task ID**: `F217EXEC-M2-DUAL-VALIDATION-REPLACEMENT-BATCH-SUBMISSION1`  
**Date**: 17 August 2026  
**Status**: `REPLACEMENT JOBS SUBMITTED / PBS IDS RECORDED / QUEUED ON CLUSTER / GATES PRESERVED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

Under direct human authorization, the environment-corrected replacement jobs for `M2_DUAL_VALIDATION_BATCH_R7_PK10R2` were re-verified and submitted to the HPC cluster.

### Submission Summary
1. **Job 1: Same-Mesh Restart Validation (Revision R7)**
   - **Job Name**: `M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7`
   - **PBS Job ID**: `1390042.mmaster02`
   - **Initial Status**: `Q` (Queued)
   - **Requested Resources**: 1 CPU, 16 GB RAM, 24:00:00 walltime, Queue `entry_imfdfkmq`
   - **Directory**: `projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7`
   - **Launcher Hash (Corrected)**: `ba75bbe2a4f3b6ced22f872d3264e8750eae8304b8d9852b164ac1c300944440`
2. **Job 2: Corrected Topology Validation (Revision R2)**
   - **Job Name**: `M2CORR_PK10R2_TOPOLOGY_CORRECTED`
   - **PBS Job ID**: `1390043.mmaster02`
   - **Initial Status**: `Q` (Queued)
   - **Requested Resources**: 1 CPU, 16 GB RAM, 24:00:00 walltime, Queue `entry_imfdfkmq`
   - **Directory**: `projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED`
   - **Launcher Hash (Corrected)**: `c0dc769e9a21488e8dd9b6e315ac7a5b9b1ba0ee684dd32a4633798940c14ed3`

---

## 2. Pre-Submission Package Hashes Verification (100% Match)

| Package | Artifact | Relative Path | Verified Cluster SHA256 |
| :--- | :--- | :--- | :--- |
| **R7** | Input Deck | `.../M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7.inp` | `d20edf3a13f024b4ccb981dd86ec82fd7e91ba611451694b9cf313d0affcf750` |
| **R7** | UEL Subroutine | `.../f44_mixed_uel_restart_stateinit.for` | `de8326dfd28e66a82ba38496ee63869b86b5959e2cc35b010ebb28ae1dec6438` |
| **R7** | State Include | `.../PK10R1_INC29_PRIMARY_STATE_BOUNDARY.inp` | `9bd16f9a27cf7c7aa398af31f7e3c754bfab5e9ecf2825fd835dbd1340bd51e5` |
| **R7** | U3 Include | `.../PK10R1_INC29_U3_ONLY_BOUNDARY.inp` | `f54e4fefb92308ec302322cf4183cfa62ae5f89eeb37f1d8727034ea1ce167b8` |
| **R7** | Binary State | `.../PK10R1_INC29_COMMITTED_STATE_REPLAY_RECONSTRUCTED.bin` | `9ad133d73332fa24e4c35eab9d49505d30232d30ff5b9f49372d361f833cccea` |
| **R7** | Launcher (NEW) | `.../submit_job.sh` | `ba75bbe2a4f3b6ced22f872d3264e8750eae8304b8d9852b164ac1c300944440` |
| **PK10R2**| Input Deck | `.../M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp` | `667897fc42ee134be434cb5bc543796ce47ffd2024ec4d6c01d20e0abbd987be` |
| **PK10R2**| UEL Subroutine | `.../f42_mixed_uel.for` | `e0865b5eba43c14d21a733e72717e157d65c778319e6556e5eca8ab222364e58` |
| **PK10R2**| Launcher (NEW) | `.../submit_job.sh` | `c0dc769e9a21488e8dd9b6e315ac7a5b9b1ba0ee684dd32a4633798940c14ed3` |

---

## 3. Scientific Governance & Submission Invariants

- `same_mesh_restart_validation` = `SUBMITTED_RUNNING`
- `batch_name` = `M2_DUAL_VALIDATION_BATCH_R7_PK10R2`
- `job_1_name` = `M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7`
- `job_1_pbs_id` = `1390042.mmaster02`
- `job_2_name` = `M2CORR_PK10R2_TOPOLOGY_CORRECTED`
- `job_2_pbs_id` = `1390043.mmaster02`
- `total_submissions` = `2` (maximum allowed: 2)
- `qsub_called` = `true` (2 calls)
- `qdel_called` = `false`, `qmove_called` = `false`
- `git_commit_called` = `false`, `git_push_called` = `false`

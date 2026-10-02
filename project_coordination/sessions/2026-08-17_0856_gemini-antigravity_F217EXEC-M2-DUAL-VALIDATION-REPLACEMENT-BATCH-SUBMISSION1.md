# Session: 2026-08-17 08:56 - F217 M2 Dual Validation Replacement Batch Submission

**Task ID**: `F217EXEC-M2-DUAL-VALIDATION-REPLACEMENT-BATCH-SUBMISSION1`  
**Agent**: `gemini-antigravity`  
**Start Commit**: `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`  

---

## 1. Objectives & Scope

- Execute authorized HPC submission of environment-corrected replacement validation batch.
- Re-verify frozen scientific package hashes and corrected launcher hashes on cluster.
- Re-verify notification gates and unchanged execution resources (1 CPU, 16 GB, 24:00:00, queue `entry_imfdfkmq`).
- Submit exactly two validation jobs via `qsub`:
  1. `M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7`
  2. `M2CORR_PK10R2_TOPOLOGY_CORRECTED`
- Record returned PBS job IDs. Zero additional/retry jobs submitted.

---

## 2. Actions Executed

1. **Re-Verified Cluster Package Hashes (100% Match)**:
   - R7 Package: INP (`d20edf3a...`), UEL (`de8326df...`), State Inc (`9bd16f9a...`), U3 Inc (`f54e4fef...`), Binary (`9ad133d7...`), Launcher (`ba75bbe2...`).
   - PK10R2 Package: INP (`667897fc...`), UEL (`e0865b5e...`), Launcher (`c0dc769e...`).
2. **Submitted Replacement Jobs via `qsub` on HPC Cluster**:
   - Job 1 (`M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7`) $\implies$ **PBS Job ID = `1390042.mmaster02`** (Queued)
   - Job 2 (`M2CORR_PK10R2_TOPOLOGY_CORRECTED`) $\implies$ **PBS Job ID = `1390043.mmaster02`** (Queued)
3. **Documentation & Registries Updated**:
   - Created `docs/experiment_records/F217EXEC_M2_DUAL_VALIDATION_REPLACEMENT_SUBMISSION_RECORD.md`.
   - Updated `TASK_LEDGER.csv`, `ARTIFACT_REGISTRY.csv`, `CURRENT_STATE.md`.

---

## 3. Active Scientific Invariants

- `same_mesh_restart_validation` = `SUBMITTED_RUNNING`
- `batch_name` = `M2_DUAL_VALIDATION_BATCH_R7_PK10R2`
- `job_1_pbs_id` = `1390042.mmaster02`
- `job_2_pbs_id` = `1390043.mmaster02`
- `total_submissions` = `2` (maximum limit: 2)
- `qsub_called` = `true` (2 calls)
- `qdel_called` = `false`, `qmove_called` = `false`
- `git_commit_called` = `false`, `git_push_called` = `false`

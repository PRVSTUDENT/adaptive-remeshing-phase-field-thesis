# Session: 2026-08-17 09:28 - F222 M2 PK10R2 Repaired Submission

**Task ID**: `F222EXEC-M2-PK10R2-REPAIRED-SUBMISSION1`  
**Agent**: `gemini-antigravity`  
**Start Commit**: `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`  

---

## 1. Objectives & Scope

- Execute authorized HPC submission of repaired `M2CORR_PK10R2_TOPOLOGY_CORRECTED` benchmark.
- Re-run fail-closed notification preflight gate.
- Re-verify package hashes on cluster.
- Submit exactly one job via `qsub` with requested resources (1 CPU, 16 GB, 24:00:00, queue `entry_imfdfkmq`).
- Record returned PBS Job ID and initial status. Zero additional jobs submitted.

---

## 2. Actions Executed

1. **Re-Ran Notification Preflight Gate**:
   - `verify_notification_preflight.sh` exited 0 with valid mode 600 permissions and function bindings.
2. **Re-Verified Package Hashes on Cluster (100% Match)**:
   - INP: `25cb7673a8e6914956821d9716f10393089409e4ac7fad41a24b744e5f3edbce`
   - UEL: `e0865b5eba43c14d21a733e72717e157d65c778319e6556e5eca8ab222364e58`
   - Launcher: `1481b0ad2e8ee89bfa31c6569106e436fc79db5ba5e481383e56c1a72eef407d`
   - Preflight: `c336b87bcca24c33f1867d1cd470c0a7d061cb87d5c1ccbb80d3d7928642814b`
3. **Submitted Repaired PK10R2 via `qsub`**:
   - Returned PBS Job ID: **`1390056.mmaster02`** (Initial State: `R` - Running).
4. **Documentation & Registries Updated**:
   - Created `docs/experiment_records/F222EXEC_M2_PK10R2_REPAIRED_SUBMISSION_RECORD.md`.
   - Updated `TASK_LEDGER.csv`, `ARTIFACT_REGISTRY.csv`, `CURRENT_STATE.md`.

---

## 3. Preserved Scientific Invariants

- `same_mesh_restart_validation` = `VALIDATED`
- `repaired_pk10r2_pbs_id` = `1390056.mmaster02`
- `total_submissions` = `1` (maximum limit: 1)
- `qsub_called` = `true` (1 call)
- `qdel_called` = `false`, `qmove_called` = `false`
- `git_commit_called` = `false`, `git_push_called` = `false`

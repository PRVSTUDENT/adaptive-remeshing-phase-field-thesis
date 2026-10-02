# Repaired Mode-II PK10R2 Benchmark Submission Record

**Task ID**: `F222EXEC-M2-PK10R2-REPAIRED-SUBMISSION1`  
**Date**: 17 August 2026  
**Status**: `REPAIRED JOB SUBMITTED / PBS ID RECORDED / JOB RUNNING / GATES PRESERVED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

Under direct human authorization, the repaired and qualified `M2CORR_PK10R2_TOPOLOGY_CORRECTED` benchmark was verified against all pre-submission gates and submitted to the HPC cluster.

### Submission Summary
- **Job Name**: `M2CORR_PK10R2_TOPOLOGY_CORRECTED`
- **PBS Job ID**: **`1390056.mmaster02`**
- **Initial Status**: **`R`** (Running)
- **Requested Resources**: 1 CPU, 16 GB RAM, 24:00:00 walltime, Queue `entry_imfdfkmq`
- **Execution Directory**: `projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R2_TOPOLOGY_CORRECTED`

---

## 2. Pre-Submission Gate & Package Cryptographic Verification (100% Match)

1. **Pre-Submission Notification Gate**:
   - `verify_notification_preflight.sh` output: `[PREFLIGHT SUCCESS] Notification pre-submission gate passed: configuration valid, mode 600, all helpers verified.` (Exit Code 0).
   - PBS Email: `#PBS -m abe` and `#PBS -M Pruthviraja.Reddy-Vandavagali@student.tu-freiberg.de,pr21vyci@mailserver.tu-freiberg.de`.
   - Telegram: Active hooks in `submit_job.sh` and `submit_job.pbs`.
2. **Cryptographic Hashes Verified on Cluster**:
   - Input Deck (`M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp`): `25cb7673a8e6914956821d9716f10393089409e4ac7fad41a24b744e5f3edbce`
   - Fortran Subroutine (`f42_mixed_uel.for`): `e0865b5eba43c14d21a733e72717e157d65c778319e6556e5eca8ab222364e58`
   - Launcher Script (`submit_job.sh`): `1481b0ad2e8ee89bfa31c6569106e436fc79db5ba5e481383e56c1a72eef407d`
   - Notification Helper (`job_notifications.sh`): `96756a681d2d36c11b36b89288f631f8ecc9537543c2c745a4bae1b425984b47`
   - Preflight Script (`verify_notification_preflight.sh`): `c336b87bcca24c33f1867d1cd470c0a7d061cb87d5c1ccbb80d3d7928642814b`

---

## 3. Scientific Governance & Submission Invariants

- `same_mesh_restart_validation` = `VALIDATED` (`1390042.mmaster02` preserved)
- `repaired_pk10r2_job_name` = `M2CORR_PK10R2_TOPOLOGY_CORRECTED`
- `repaired_pk10r2_pbs_id` = `1390056.mmaster02`
- `total_submissions_count` = `1` (exactly 1 submitted)
- `qsub_called` = `true` (1 call)
- `qdel_called` = `false`, `qmove_called` = `false`
- `git_commit_called` = `false`, `git_push_called` = `false`

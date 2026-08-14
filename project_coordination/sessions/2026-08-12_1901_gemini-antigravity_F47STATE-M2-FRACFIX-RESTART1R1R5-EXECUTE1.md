# Session Handoff Report: F47STATE-M2-FRACFIX-RESTART1R1R5-EXECUTE1

**Date**: 12 August 2026  
**Agent**: Gemini Antigravity  
**Task ID**: `F47STATE-M2-FRACFIX-RESTART1R1R5-EXECUTE1`  
**Protocol Version**: 1  

---

## 1. Task Objective

Execute the single authorized production scientific state-transfer restart submission for frozen candidate **`M2STATE_FRACFIX_RESTART1R1R5`** under explicit standalone human authorization. Zero unauthorized retries (`automatic_retry = false`), zero `qdel` calls, zero `qmove` calls.

---

## 2. Pre-Submission Preflight Verification

1. **Read-Only Scheduler Check**:
   - Executed `qstat -u pr21vyci` on `mlogin01.hrz.tu-freiberg.de`.
   - Result: 0 running or queued jobs (`capacity_available = true`).
2. **Exact Package Hashes**:
   - Verified SHA256 hashes of all 9 package files locally and remotely on `mlogin01`.
   - Result: 100% match with frozen candidate `M2STATE_FRACFIX_RESTART1R1R5`.
3. **Guarded Submission Wrapper Execution**:
   - Executed `bash submit_m2state_fracfix_restart1r1r5.sh` from candidate remote directory `/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R5/`.
   - Preflight hash verification passed 100% cleanly.
   - Result: PBS assigned Job ID **`1388886.mmaster02`**.

---

## 3. Authorized Execution Summary

- **Authorization Verification**:
  - `direct_human_authorization_found = true`
  - `MAX_SUBMISSIONS = 1`
  - `AUTHORIZED_JOB_COUNT = 1`
  - `authorization_consumed = true`
  - `M2STATE_FRACFIX_RESTART1R1R5_submission_count = 1`

- **PBS Job ID**: `1388886.mmaster02`
- **Job Name**: `M2STATE_FRACFIX_RESTART1R1R5`
- **Queue**: `entry_imfdfkmq` (routed to `normal_imfdfkmq`)
- **State**: `Q` (QUEUED in cluster scheduler)
- **Requested Resources**: `select=1:ncpus=1:mpiprocs=1:mem=8gb:ompthreads=1`, `walltime=24:00:00`
- **Dual-Channel Notifications**: Enabled (`#PBS -m abe`, `#PBS -M pr21vyci@mailserver.tu-freiberg.de`, `job_notifications.sh` terminal traps, `notify_start`).
- **Owner**: `pr21vyci@mlogin01.cluster`

---

## 4. Milestone & Governance

- `direct_human_authorization_found` = `true`
- `submission_authorization_valid` = `true`
- `authorization_consumed` = `true`
- `execution_identity` = `EXECUTION_IDENTITY_R1R1R5_MATCH`
- `automatic_retry` = `false`
- `qdel_called` = `false`
- `qmove_called` = `false`
- `new_submission_authorized` = `false`
- Single authorized job `1388886.mmaster02` is active and queued in the cluster scheduler.

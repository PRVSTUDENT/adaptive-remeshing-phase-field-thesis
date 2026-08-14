# Session Handoff Report: F46STATE-M2-FRACFIX-RESTART1R1R4-EXECUTE1

**Date**: 12 August 2026  
**Agent**: Gemini Antigravity  
**Task ID**: `F46STATE-M2-FRACFIX-RESTART1R1R4-EXECUTE1`  
**Protocol Version**: 1  

---

## 1. Task Objective

Execute the single authorized production scientific state-transfer restart submission for frozen candidate **`M2STATE_FRACFIX_RESTART1R1R4`** under explicit standalone human authorization. Zero unauthorized retries (`automatic_retry = false`), zero `qdel` calls, zero `qmove` calls.

---

## 2. Pre-Submission Preflight Verification

1. **Read-Only Scheduler Check**:
   - Executed `qstat -u pr21vyci` on `mlogin01.hrz.tu-freiberg.de`.
   - Result: 0 running or queued jobs (`capacity_available = true`).
2. **License Gate & Environment**:
   - License check: `license_server_reachable = true`, `standard_tokens_free = 146`, `license_ready_for_serial_standard_job = true`.
   - Environment: Abaqus 2023 (`/cluster/application/abaqus/2023/Commands/abaqus`), Intel Fortran 2024.2.0 (`ifort 2021.13.0`).
3. **Exact Remote Package Hashes**:
   - Re-verified SHA256 hashes of all 9 files in `/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R4/`.
   - Result: 100% match with frozen candidate `M2STATE_FRACFIX_RESTART1R1R4`. `wrapper CR_count = 0`, `PBS CR_count = 0`.
4. **Candidate Regression & Direct Dry-Run**:
   - `python3 -m unittest -v tests/unit/test_m2state_fracfix_restart1r1r4.py` -> **32 / 32 PASS**.
   - `bash submit_m2state_fracfix_restart1r1r4.sh --dry-run` -> **RC = 0** (`DRY-RUN COMPLETE: Preflight passed cleanly`).

---

## 3. Authorized Execution

- **Authorization Verification**:
  - `direct_human_authorization_found = true`
  - `MAX_SUBMISSIONS = 1`
  - `AUTHORIZED_JOB_COUNT = 1`
- **Submission Invocation**:
  - Command: `qsub M2STATE_FRACFIX_RESTART1R1R4.pbs` from candidate remote directory.
  - Result: PBS assigned Job ID **`1388878.mmaster02`**.
  - `authorization_consumed = true`
  - `M2STATE_FRACFIX_RESTART1R1R4_submission_count = 1`

---

## 4. Scheduler Monitoring & Status

- **PBS Job ID**: `1388878.mmaster02`
- **Job Name**: `M2STATE_FRACFIX_RESTART1R1R4`
- **Queue**: `entry_imfdfkmq` (routed to `normal_imfdfkmq`)
- **State**: `R` (RUNNING on compute node `mnode098/0`)
- **Requested Resources**: `select=1:ncpus=1:mpiprocs=1:mem=8gb`, `walltime=24:00:00`
- **Dual-Channel Notifications**: Enabled (`#PBS -m abe`, `#PBS -M pr21vyci@mailserver.tu-freiberg.de`, `job_notifications.sh` terminal traps, `notify_start`).
- **Owner**: `pr21vyci@mlogin01.cluster`

---

## 5. Milestone & Governance

- `direct_human_authorization_found` = `true`
- `submission_authorization_valid` = `true`
- `authorization_consumed` = `true`
- `execution_identity` = `EXECUTION_IDENTITY_R1R1R4_MATCH`
- `automatic_retry` = `false`
- `qdel_called` = `false`
- `qmove_called` = `false`
- `new_submission_authorized` = `false`
- Single authorized job `1388878.mmaster02` is active and running in the cluster scheduler. Solver execution results will be scientifically evaluated upon job completion.

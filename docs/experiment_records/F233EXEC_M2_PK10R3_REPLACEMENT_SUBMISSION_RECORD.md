# Execution Record: M2CORR_PK10R3_REFINED_TIP Replacement Submission

**Task ID**: `F233EXEC-M2-PK10R3-REPLACEMENT-AUTHORIZATION-AND-SUBMISSION1`  
**Date**: 17 August 2026  
**Failed Predecessor Preserved in Lineage**: `1390097.mmaster02` (`MODULE_COMPILER_FAILURE`)  
**Submitted Job ID**: **`1390098.mmaster02`**  
**Job Status**: `RUNNING / INITIAL_STATE_R / SIDECAR_ACTIVE / SUBMITTED_NOTIFICATION_DISPATCHED / GATES_PRESERVED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

Exactly one technically corrected replacement job **`M2CORR_PK10R3_REFINED_TIP`** was authorized and submitted to the TU Freiberg PBS cluster.

- **Predecessor Ingestion**: `1390097.mmaster02` was preserved in provenance as `MODULE_COMPILER_FAILURE`.
- **Pre-Submission Preflight**: Dual-channel notification transport and secure config permissions (mode 600) were verified.
- **Login-Node Sidecar**: Detached sidecar daemon was started on `mlogin01` (`PID 2932554`).
- **Submission**: `qsub submit_job.pbs` returned PBS Job ID **`1390098.mmaster02`**.
- **Initial State**: `qstat -x 1390098.mmaster02` confirmed state **`R`** (Running) on `normal_imfdfkmq`.
- **SUBMITTED Event**: Dispatched via HTTPS (Telegram HTTP 200) and local MTA.

---

## 2. Frozen Scientific Package & Hashes

| Artifact | Repo File Path | Cryptographic SHA-256 Hash | Verification Status |
| :--- | :--- | :--- | :--- |
| **INP Deck** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/M2CORR_PK10R3_REFINED_TIP.inp` | `68fe0ff24272fca78ab76a771671c2bb8f65c4d99d8421aae93851d1401f192c` | **FROZEN UNCHANGED** |
| **UEL Subroutine** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/f42_mixed_uel.for` | `e0865b5eba43c14d21a733e72717e157d65c778319e6556e5eca8ab222364e58` | **FROZEN UNCHANGED** |
| **PBS Launcher** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/submit_job.pbs` | `e5b18276cc56921168de77a292844c71eaf2080b245a5f3ddb8b7c5f2e501ce9` | **QUALIFIED REPAIRED** |
| **Notification Shell** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/job_notifications.sh` | `96756a681d2d36c11b36b89288f631f8ecc9537543c2c745a4bae1b425984b47` | **FROZEN UNCHANGED** |
| **Manifest** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/manifest.json` | `c54696f1595e4665c9ddd56029fc0cd528bd3d9c196afe6d02be371bb1926b8e` | **UPDATED** |

---

## 3. Job Execution & Initial Scheduler Monitoring

- **Job Name**: `M2PK10R3_REFTIP`
- **PBS Job ID**: `1390098.mmaster02`
- **Initial Query (`qstat -x 1390098.mmaster02`)**:
  ```text
  Job id            Name             User              Time Use S Queue
  ----------------  ---------------- ----------------  -------- - -----
  1390098.mmaster02 M2PK10R3_REFTIP  pr21vyci          00:00:00 R normal_imfdfkmq
  ```
- **Login Sidecar Daemon**: `ACTIVE (PID 2932554)` on `mlogin01`
- **SUBMITTED Event Dispatch**:
  ```json
  {
    "event": "SUBMITTED",
    "job_id": "1390098.mmaster02",
    "telegram": {
      "channel": "telegram",
      "transport_ack": true,
      "status_code": 200,
      "human_delivery_observed": false
    },
    "email": {
      "channel": "email",
      "transport_ack": true,
      "exit_code": 0,
      "recipient": "pr21vyci@mailserver.tu-freiberg.de",
      "human_delivery_observed": false
    }
  }
  ```

---

## 4. Scientific Governance & Preserved Invariants

```text
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = false
selected_production_history_operator = UNRESOLVED
nonmatching_transfer_algorithm_scientifically_unblocked = false
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
telegram_delivery_observed = true (prior smoke test)
email_delivery_observed = true (prior smoke test)
notification_pre_submission_gate_passed = true
```

```text
new_submission_authorized = false
qsub_called = true (Job 1390098.mmaster02)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

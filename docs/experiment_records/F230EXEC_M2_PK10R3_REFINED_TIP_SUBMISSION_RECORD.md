# Execution Record: M2CORR_PK10R3_REFINED_TIP Authorization and Submission

**Task ID**: `F230EXEC-M2-PK10R3-REFINED-TIP-AUTHORIZATION-AND-SUBMISSION1`  
**Date**: 17 August 2026  
**Status**: `JOB_SUBMITTED / SIDECAR_ACTIVE / INITIAL_STATE_CAPTURED / GATES_PRESERVED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

Following explicit human verification of dual-channel notification delivery (`telegram_delivery_observed = true`, `email_delivery_observed = true`), the pre-submission gate was cleared.

The persistent login-node notification sidecar was started on `mlogin01` (PID 2917848), and exactly one authorized diagnostic HPC job **`M2CORR_PK10R3_REFINED_TIP`** was submitted to the cluster via `qsub`.

- **PBS Job ID**: **`1390097.mmaster02`**
- **Initial PBS State**: `E` (Entering / Routing to execution node `normal_imfdfkmq`)
- **Requested Resources**: 1 CPU, 16 GB RAM, 24:00:00 walltime, queue `entry_imfdfkmq`

---

## 2. Frozen Scientific Package & Hashes

| Artifact | Repo File Path | Cryptographic SHA-256 Hash |
| :--- | :--- | :--- |
| **INP Deck** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/M2CORR_PK10R3_REFINED_TIP.inp` | `68fe0ff24272fca78ab76a771671c2bb8f65c4d99d8421aae93851d1401f192c` |
| **UEL Subroutine** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/f42_mixed_uel.for` | `e0865b5eba43c14d21a733e72717e157d65c778319e6556e5eca8ab222364e58` |
| **PBS Launcher** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/submit_job.pbs` | `193ec4ae1b5e1a42b09c9497cae88467b808e5de83061f1d63b94028b0b08611` |
| **Notification Shell** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/job_notifications.sh` | `96756a681d2d36c11b36b89288f631f8ecc9537543c2c745a4bae1b425984b47` |
| **Package Manifest** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/manifest.json` | `4a7512a8ad11c20e2063b5ee87ffac1791c0455662d0ac0b90acac10cba54045` |
| **Generator Script** | `scripts/model_generation/build_pk10r3_refined_tip_candidate.py` | `c8169de0fb7f228e379bc0f6fb44e9c0a9cf363033d7896d4f893045691272f8` |

---

## 3. Job Identification & Submission Details

- **Job Name**: `M2PK10R3_REFTIP`
- **Submission Directory**: `/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP`
- **PBS Job ID**: `1390097.mmaster02`
- **Initial Query (`qstat -x 1390097.mmaster02`)**:
  ```text
  Job id            Name             User              Time Use S Queue
  ----------------  ---------------- ----------------  -------- - -----
  1390097.mmaster02 M2PK10R3_REFTIP  pr21vyci          00:00:01 E normal_imfdfkmq
  ```
- **Login Sidecar Daemon**: `ACTIVE (PID 2917848)` on `mlogin01`

---

## 4. Scientific Governance & Preserved Invariants

```text
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = false
selected_production_history_operator = UNRESOLVED
nonmatching_transfer_algorithm_scientifically_unblocked = false
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
email_delivery_observed = true
notification_pre_submission_gate_passed = true
```

```text
new_submission_authorized = false
qsub_called = true (exactly one job: 1390097.mmaster02)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

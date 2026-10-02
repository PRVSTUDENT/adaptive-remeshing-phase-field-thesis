# Stage-D Continuous Target Control Diagnostic Submission Record

**Task ID**: `F266SUB-M2-STAGE-D-CONTINUOUS-TARGET-CONTROL-SUBMISSION1`  
**Date**: 18 August 2026  
**Status**: `JOB_SUBMITTED / SCHEDULER_RUNNING / DUAL_CHANNEL_NOTIFICATIONS_ACTIVE / GATES_HELD_CONSERVATIVE`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Submission Identity & Scheduler Evidence

- **PBS Job ID**: `1390439.mmaster02`
- **Package Name**: `M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL`
- **Job Name**: `M2_STAGE_D_CONT_CTRL`
- **Target Mesh**: 8,836 physical quads, 9,072 physical nodes + RP 99999 (exact Stage-D nonmatching grid).
- **Execution Host**: `mnode097/0`
- **Queue**: `normal_imfdfkmq` (routed from `entry_imfdfkmq`)
- **Resources Allocated**: 1 CPU, 16 GB RAM, 24:00:00 Walltime.
- **Job State**: `R` (RUNNING)
- **Mail Recipient**: `pr21vyci@mailserver.tu-freiberg.de` (`Mail_Points = abe`)
- **Login-Node Watcher Sidecar**: `ACTIVE (PID 811775)`

---

## 2. Frozen Cryptographic SHA-256 Hashes

```text
=============================================================================================================
Package Artifact                                      SHA-256 Checksum
----------------------------------------------------  -------------------------------------------------------
M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.inp      cfef365e4509f1c5ae84463f93640e38142ff3623dcdb91778da80e9ac2e0d00
f44_mixed_uel_restart_stateinit.for                   bd2f207cc60302798877ad02b3ba0cd2ac5d3b6f437a5e5f510b4b924597a09f
submit_job.pbs                                        62d868b900bcfb143fcf4f686e514cb34c0d145784413ca7b69942d143b1c1ec
manifest.json                                         9a98db257321288bbd4bc40e7a2b97c0f135ea5dc2356c38260905156640ca84
one_difference_scientific_manifest.json               c3e3dd20c4e1ff9e2ad71ee31eb5c5553eeb40a9a1eb40989adcf4177d468165
=============================================================================================================
```

---

## 3. Mandatory Notification Preflight Results

- **Telegram Channel**: `PASSED (rc=0, transport ACK HTTP 200)`
- **Email Channel (`pr21vyci@mailserver.tu-freiberg.de`)**: `PASSED (rc=0, mailx exit 0)`
- **Sidecar Lifecycle Monitor**: Persistent daemon running under PID 811775 on `mlogin01`.

---

## 4. Preserved Conservative Scientific Invariants

```text
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = true
selected_production_history_operator = HOST_NEAREST_GP_WITH_NONNEGATIVE_IRREVERSIBILITY
stage_d_nonmatching_transfer_validation = UNDER_FORENSIC_REVIEW
nonmatching_transfer_algorithm_scientifically_unblocked = false
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
email_delivery_observed = true
notification_pre_submission_gate_passed = true
new_submission_authorized = true (Single diagnostic job 1390439.mmaster02 submitted)
qsub_called = true (Job 1390439.mmaster02 active)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

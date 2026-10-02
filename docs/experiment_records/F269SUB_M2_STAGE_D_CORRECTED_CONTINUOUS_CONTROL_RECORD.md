# Mode-II Stage-D Corrected Continuous Target Control Submission Record

**Task ID**: `F269SUB-M2-STAGE-D-CORRECTED-CONTINUOUS-CONTROL-SUBMISSION1`  
**Date**: 18 August 2026  
**Status**: `JOB_SUBMITTED / SCHEDULER_RUNNING / TRUE_VIRGIN_MODE_VERIFIED / DUAL_CHANNEL_NOTIFICATIONS_ACTIVE / GATES_HELD_CONSERVATIVE`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Package Rebuild & Isolated Ingestion Correction

- **Correction Applied**: Removed hardcoded fallback path (`.../M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/STAGE_D_COMMITTED_STATE.bin`) and parent fallback (`../`) in `f44_mixed_uel_restart_stateinit.for`.
- **Strict Logic**: `UEXTERNALDB (LOP=0)` strictly tests local `STAGE_D_COMMITTED_STATE.bin` in cwd. When absent, it deterministically zero-initializes all `SV_ELEM_NODAL_PHASE_COM` and all four-GP `SV_H_COMMITTED` arrays and logs:
  ```text
  INFO: Virgin analysis mode - zeroing all phase and history arrays
  ```
- **Invalidation Notice**: Job `1390439.mmaster02` is formally recorded as scientifically invalid for this diagnostic due to unintended state ingestion and must never be reused as the virgin continuous baseline.

---

## 2. Frozen Cryptographic SHA-256 Checksums

```text
=============================================================================================================
Package Artifact                                      SHA-256 Checksum
----------------------------------------------------  -------------------------------------------------------
M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.inp      cfef365e4509f1c5ae84463f93640e38142ff3623dcdb91778da80e9ac2e0d00
f44_mixed_uel_restart_stateinit.for                   c9d9db38e15741c54ab828ff936faced83799ea62d3eb2b490aec0c8e55aab16
submit_job.pbs                                        62d868b900bcfb143fcf4f686e514cb34c0d145784413ca7b69942d143b1c1ec
manifest.json                                         27d53086ebba2120dc9559c5d01211e0dc4ae945bfb85848bb2fb5b8823298c5
one_difference_scientific_manifest.json               384cbf9d332612b7a42b1575231713fe668102ff937d1d23b3f2ff47c5d4a13f
=============================================================================================================
```

---

## 3. Qualification & Preflight Verification

1. **Path & Security Audit**: `audit_no_fallback_paths.py` passed (0 fallback paths present).
2. **Datacheck Qualification on Cluster**: Passed `Exit 0` (`Abaqus JOB M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL COMPLETED`).
3. **Virgin Mode Verification**: Verified `INFO: Virgin analysis mode - zeroing all phase and history arrays` in solver log.
4. **Dual-Channel Preflight**:
   - Telegram smoke test: `PASSED (rc=0, transport ACK HTTP 200)`
   - Email smoke test (`pr21vyci@mailserver.tu-freiberg.de`): `PASSED (rc=0, mailx exit 0)`
   - Persistent Watcher: `ACTIVE (PID 811775)` on `mlogin01`.

---

## 4. Submission Accounting & Initial Scheduler Evidence

- **Exact Returned PBS Job ID**: **`1390446.mmaster02`**
- **Job Name**: `M2_STAGE_D_CONT_CTRL`
- **Execution Host**: `mnode097/0`
- **Queue**: `normal_imfdfkmq` (routed from `entry_imfdfkmq`)
- **Resources**: `select=1:ncpus=1:mem=16gb`, `walltime=24:00:00`
- **Job State**: `R` (RUNNING)
- **Mail Parameters**: `Mail_Points = abe`, `Mail_Users = pr21vyci@mailserver.tu-freiberg.de`

```text
Job Id: 1390446.mmaster02
    Job_Name = M2_STAGE_D_CONT_CTRL
    Job_Owner = pr21vyci@mlogin01.cluster
    job_state = R
    queue = normal_imfdfkmq
    server = mmaster02
    exec_host = mnode097/0
    exec_vnode = (mnode097[0]:ncpus=1:mem=16777216kb)
    Mail_Points = abe
    Mail_Users = pr21vyci@mailserver.tu-freiberg.de
    Output_Path = mlogin01.cluster:.../M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/pbs.out
    Error_Path = mlogin01.cluster:.../M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/pbs.err
    Resource_List.mem = 16gb
    Resource_List.ncpus = 1
    Resource_List.walltime = 24:00:00
```

---

## 5. Preserved Conservative Scientific Invariants

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
new_submission_authorized = true (Single corrected diagnostic job 1390446.mmaster02 submitted)
qsub_called = true (Job 1390446.mmaster02 active)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

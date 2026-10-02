# Mode-II Stage-D Explicit Architecture Mode Continuous Control Submission Record

**Task ID**: `F271SUB-M2-STAGE-D-EXPLICIT-MODE-CONTINUOUS-CONTROL-SUBMISSION1`  
**Date**: 18 August 2026  
**Status**: `JOB_SUBMITTED / SCHEDULER_RUNNING / EXPLICIT_MODE_ACTIVE / DUAL_CHANNEL_NOTIFICATIONS_ACTIVE / GATES_HELD_CONSERVATIVE`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Architecture-Level Execution Mode Implementation

- **Explicit Input-Controlled Mode (`PROPS(7)`)**:
  - `PROPS(7) = 0.D0` (`MODE_VIRGIN_CONTINUOUS`):
    - `UEXTERNALDB (LOP=0)`: Strictly zero-initializes all committed and trial arrays (`SV_ELEM_NODAL_PHASE_COM/TRL`, `SV_H_COMMITTED/TRL`); never ingests any state binary file.
    - `UEL`: Active history accumulation $\mathcal{H}_{n+1} = \max(\mathcal{H}_n, \psi_+)$ is active from Step 1 Increment 1 without any step number restriction (`IF (I_EXEC_MODE .EQ. 0) THEN IF (POS_M .GT. HIST) HIST = POS_M`).
  - `PROPS(7) = 1.D0` (`MODE_STAGED_TRANSFER_RESTART`):
    - `UEXTERNALDB (LOP=0)`: Strictly requires local `STAGE_D_COMMITTED_STATE.bin` in cwd; fails closed with fatal abort (`CALL XIT`) if `MODE_STAGED.flag` is set and file is missing.
    - `UEL`: History accumulation is frozen during `KSTEP <= 2` (`STATE_LOAD`, `MECH_EQUILIBRATION`) and activates at `KSTEP > 2` (`PHASE_RELEASE`, `CONTINUATION`).
- **Invalidation Notice**: Both previous continuous runs (`1390439.mmaster02` due to unintended state ingestion, and `1390446.mmaster02` due to `KSTEP > 2` history freeze) are formally recorded as scientifically invalid for this diagnostic and superseded by `1390447.mmaster02`.

---

## 2. Frozen Cryptographic SHA-256 Checksums

```text
=============================================================================================================
Package Artifact                                      SHA-256 Checksum
----------------------------------------------------  -------------------------------------------------------
M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.inp      d4412b3abece283d514e2612d6b17e76dc92a8d4bcaa10694315dbba49291b2c
f44_mixed_uel_restart_stateinit.for                   62e35f74bbeccd3f5b1ac67312b79211f4ccb75648ae20dbb8985cb577fe1aab
submit_job.pbs                                        62d868b900bcfb143fcf4f686e514cb34c0d145784413ca7b69942d143b1c1ec
manifest.json                                         27d53086ebba2120dc9559c5d01211e0dc4ae945bfb85848bb2fb5b8823298c5
one_difference_scientific_manifest.json               384cbf9d332612b7a42b1575231713fe668102ff937d1d23b3f2ff47c5d4a13f
=============================================================================================================
```

---

## 3. Qualification & Preflight Verification

1. **Path Audit**: Audited package with `audit_no_fallback_paths.py` (0 fallback paths present).
2. **Datacheck Qualification on Cluster**: Passed `Exit 0` (`Abaqus JOB M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL COMPLETED`).
3. **Virgin Mode Verification**: Verified `INFO: Virgin analysis mode - zeroing all phase and history arrays` in datacheck `.msg` and `.dat`.
4. **Dual-Channel Preflight on `mlogin01`**:
   - Telegram smoke test: `PASSED (rc=0, transport ACK HTTP 200)`
   - Email smoke test (`pr21vyci@mailserver.tu-freiberg.de`): `PASSED (rc=0, mailx exit 0)`
   - Login-Node Persistent Watcher Sidecar: `ACTIVE (PID 811775)`

---

## 4. Submission Accounting & Initial Scheduler Evidence

- **Exact Returned PBS Job ID**: **`1390447.mmaster02`**
- **Job Name**: `M2_STAGE_D_CONT_CTRL`
- **Queue**: `normal_imfdfkmq` (routed from `entry_imfdfkmq`)
- **Execution Host**: `mnode097/0`
- **Allocated Resources**: `select=1:ncpus=1:mem=16gb`, `walltime=24:00:00`
- **Job State**: `R` (RUNNING)
- **Mail Parameters**: `Mail_Points = abe`, `Mail_Users = pr21vyci@mailserver.tu-freiberg.de`

```text
Job Id: 1390447.mmaster02
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
new_submission_authorized = true (Single corrected diagnostic job 1390447.mmaster02 submitted)
qsub_called = true (Job 1390447.mmaster02 active)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

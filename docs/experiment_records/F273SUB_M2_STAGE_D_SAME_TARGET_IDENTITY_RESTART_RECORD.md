# Mode-II Stage-D Same-Target-Mesh Identity Staged Restart Submission Record

**Task ID**: `F273SUB-M2-STAGE-D-SAME-TARGET-IDENTITY-RESTART-SUBMISSION1`  
**Date**: 18 August 2026  
**Status**: `JOB_SUBMITTED / SCHEDULER_RUNNING / IDENTITY_TRANSFER_INSTALLED / DUAL_CHANNEL_NOTIFICATIONS_ACTIVE / GATES_HELD_CONSERVATIVE`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Experimental Design & Handoff State Provenance

- **Diagnostic Purpose**: Isolate state transfer/interpolation shock from staged restart/active-set mechanics on the exact Stage-D target mesh (8,836 quads).
- **Source Handoff State**:
  - **Job ID**: `1390447.mmaster02` (Successful virgin continuous run)
  - **Step**: `ShearStep`
  - **Frame Index**: `17`
  - **Increment**: `17`
  - **Step Time**: `0.2102578`
  - **Physical Prescribed Displacement**: $U_1 = 0.01051289\text{ mm}$
  - **Reaction Force**: $RP\_RF_1 = 0.1259158\text{ kN}$
  - **Max Nodal Phase Field Damage**: $d_{\max} = 0.3043182$
  - **Max GP Strain Energy History**: $\max \mathcal{H} = 909.5172\text{ MPa}$
- **Identity Transfer Mapping**:
  - Exact $1 \to 1$ nodal identity mapping of $u_1, u_2, d$ across all 9,073 physical nodes.
  - Exact $1 \to 1$ element 4-GP strain energy $\mathcal{H}$ computed directly via UEL kinematics across all 8,836 physical quads.
  - Zero spatial interpolation, zero smoothing, zero projection, and zero mesh distortion.
- **Staged Restart Sequence**:
  - Step 1: `STATE_INSTALL` (Install transferred $u_1, u_2, d$, load $\mathcal{H}$ from `STAGE_D_COMMITTED_STATE.bin`)
  - Step 2: `MECH_EQUILIBRATION` (Equilibrate displacement while $d$ is locked)
  - Step 3: `PHASE_RELEASE` (Release $d$ locking, allow phase relaxation)
  - Step 4: `CONTINUATION` (Monotonic shear loading from $U_1 = 0.01051289\text{ mm} \to 0.050000\text{ mm}$)
- **Explicit Execution Mode**: `PROPS(7) = 1.0` (`MODE_STAGED_TRANSFER_RESTART`) and `MODE_STAGED.flag`.

---

## 2. Frozen Cryptographic SHA-256 Checksums

```text
=============================================================================================================
Package Artifact                                      SHA-256 Checksum
----------------------------------------------------  -------------------------------------------------------
M2CORR_STAGE_D_SAME_TARGET_IDENTITY_RESTART_VAL.inp   5c4fcdf3dd80b1ca83ef9d051c5ce8f371c63abfccea9175c2682e338c76b8e0
f44_mixed_uel_restart_stateinit.for                   863090488269b5cf14b244ec405727b47aee9329b91146e72f67499443d08062
submit_job.pbs                                        1ed19c98ddd941329b49d0e6f817775e9523271154206da335c3b768b60f4f3a
STAGE_D_COMMITTED_STATE.bin                           d571ed56fc8998483b8939fcb4ecab6856ef6a2ce8706ae2cec68fddf9e63436
STAGE_D_PRIMARY_STATE_BOUNDARY.inp                    b9e7fe475d40a02cb4274944d18ec9e59bf461d3600f60742f36bc4551ee661c
STAGE_D_U3_ONLY_BOUNDARY.inp                          7cb5a3d7cb0efb32fae1a2f643e2e83fb90f671c68e14e21a2c3f5ea78794833
MODE_STAGED.flag                                      25988d119761e7a124aad8bb7ba19350ccd9bf0b8de9070b56adb57f62b2981b
manifest.json                                         e84a2d8d85f67a2119eb3ae3e430349b1ff58ffdf7ee2a259dd1a5ea1e4bf37d
one_difference_scientific_manifest.json               eeefae4d4fbb1c7a82df31b017b203a95c80ceecf3a67035c91db028d8440733
=============================================================================================================
```

---

## 3. Predeclared Scientific Diagnostic Interpretation

1. **Case A (Identity Restart Reproduces Continuous Run)**:
   - If this identity same-mesh staged restart reproduces the continuous `1390447.mmaster02` post-peak continuation curve through the critical interval $U_1 \in [0.010143\text{ mm}, 0.011251\text{ mm}]$ without encountering early `dt_min` cutback failure, this conclusively establishes that the defect in `1390279.mmaster02` is caused by the **nonmatching state transfer / interpolation operator**, and neither the target mesh nor the staged restart architecture is at fault.
2. **Case B (Identity Restart Diverges Post-Release)**:
   - If this run exhibits comparable post-release divergence despite exact identity state installation, the defect resides in the **staged restart / displacement boundary / active-set implementation**, and the nonmatching operator must not be blamed yet.

---

## 4. Qualification & Pre-Submission Preflight

1. **Path Audit**: Audited package with `audit_no_fallback_paths.py` (0 fallback paths present).
2. **Datacheck Qualification on Cluster**: Standard datacheck passed with `Exit 0` (`Abaqus JOB M2CORR_STAGE_D_SAME_TARGET_IDENTITY_RESTART_VAL COMPLETED`).
3. **Dual-Channel Preflight on `mlogin01`**:
   - Telegram smoke test: `PASSED (rc=0, transport ACK HTTP 200)`
   - Email smoke test (`pr21vyci@mailserver.tu-freiberg.de`): `PASSED (rc=0, mailx exit 0)`
   - Login-Node Persistent Watcher Sidecar: `ACTIVE (PID 811775)`

---

## 5. Submission Accounting & Initial Scheduler Evidence

- **Exact Returned PBS Job ID**: **`1390449.mmaster02`**
- **Job Name**: `M2_STAGE_D_ID_RST`
- **Queue**: `normal_imfdfkmq` (routed from `entry_imfdfkmq`)
- **Execution Host**: `mnode097/0`
- **Allocated Resources**: `select=1:ncpus=1:mem=16gb`, `walltime=24:00:00`
- **Job State**: `R` (RUNNING)
- **Mail Parameters**: `Mail_Points = abe`, `Mail_Users = pr21vyci@mailserver.tu-freiberg.de`

```text
Job Id: 1390449.mmaster02
    Job_Name = M2_STAGE_D_ID_RST
    Job_Owner = pr21vyci@mlogin01.cluster
    job_state = R
    queue = normal_imfdfkmq
    server = mmaster02
    exec_host = mnode097/0
    exec_vnode = (mnode097[0]:ncpus=1:mem=16777216kb)
    Mail_Points = abe
    Mail_Users = pr21vyci@mailserver.tu-freiberg.de
    Output_Path = mlogin01.cluster:.../M2CORR_STAGE_D_SAME_TARGET_IDENTITY_RESTART_VAL/pbs.out
    Error_Path = mlogin01.cluster:.../M2CORR_STAGE_D_SAME_TARGET_IDENTITY_RESTART_VAL/pbs.err
    Resource_List.mem = 16gb
    Resource_List.ncpus = 1
    Resource_List.walltime = 24:00:00
```

---

## 6. Preserved Conservative Scientific Invariants

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
new_submission_authorized = true (Single diagnostic job 1390449.mmaster02 submitted)
qsub_called = true (Job 1390449.mmaster02 active)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

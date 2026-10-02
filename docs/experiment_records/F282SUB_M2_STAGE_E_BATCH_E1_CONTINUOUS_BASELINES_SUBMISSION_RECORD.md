# Mode-II Stage-E Batch E1 Target-Mesh Continuous Baselines Submission Record

**Task ID**: `F282PREP-M2-STAGE-E-BATCH-E1-CONTINUOUS-BASELINES-PREPARATION1`  
**Date**: 18 August 2026  
**Status**: `BATCH_E1_SUBMITTED / JOBS_RUNNING / DUAL_CHANNEL_NOTIFICATIONS_ACTIVE / STAGE_E_REMAINS_BLOCKED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Batch E1 Summary & Submitted Packages

Batch E1 establishes the independent virgin-continuous baselines on the two Stage-E target meshes to isolate mesh discretization effects from subsequent state-transfer effects in Batch E2:

```text
===================================================================================================================================================================
Job Name                                       PBS Job ID        Mesh Type      Nodes   Quads   h_tip (mm)   h_max (mm)  h_tip/l0  Exec Host / Queue    Status
---------------------------------------------  ----------------  -------------  ------  ------  -----------  ----------  --------  -------------------  -------
M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL   1390489.mmaster02 Refined Target 34,027  33,600  0.002000     0.020000    0.1333    mnode097/0 (normal)  RUNNING
M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL 1390490.mmaster02 Coarse Target  8,416   8,200   0.005000     0.030000    0.3333    mnode097/1 (normal)  RUNNING
===================================================================================================================================================================
```

---

## 2. Remote Qualification & Datacheck Evidence

- **Compilation & Linking**: Intel Fortran 2021.13.0 + GCC 11.4.0 completed with Exit 0 for both packages.
- **Abaqus Standard Datacheck**:
  - `M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL`: **Exit 0** (`Abaqus JOB COMPLETED`).
  - `M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL`: **Exit 0** (`Abaqus JOB COMPLETED`).
- **Virgin-State Isolation**: Verified that neither package contains or searches for a state binary. Initial trial and committed phase/history fields are zeroed at startup (`PROPS(7) = 0.0`).
- **Dual-Channel Preflight Smoke Tests**:
  - Email: `rc=0` (pr21vyci@mailserver.tu-freiberg.de via mailx)
  - Telegram: `rc=0` (HTTP 200 OK)

---

## 3. Package Checksums (SHA-256)

### Refined Continuous Target Package (`M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL`):
```json
{
  "M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL.inp": "0b3017a55ca22340ae35767b453a277703e23dd22eeec75dd36605e54c0eec86",
  "f44_mixed_uel_restart_stateinit.for": "863090488269b5cf14b244ec405727b47aee9329b91146e72f67499443d08062",
  "submit_job.pbs": "0b8a3df04cb591a457ea5e9c011e4bf51a0293eece8ca0709a32c25cb1fbf9db"
}
```

### Coarsened Continuous Target Package (`M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL`):
```json
{
  "M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL.inp": "97793d4f8285514f09d84699ae8b1d9bf6c1ec37d11bf430b05b4b768e1ce2fa",
  "f44_mixed_uel_restart_stateinit.for": "863090488269b5cf14b244ec405727b47aee9329b91146e72f67499443d08062",
  "submit_job.pbs": "a143b44b8061e8ce09b9f71c4c8152e46b94098939c0f991f868c2d58309df55"
}
```

---

## 4. Preserved Scientific Gates

```text
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = true
selected_production_history_operator = HOST_ISOPARAMETRIC_BILINEAR_WITH_LOCAL_GP_BOUNDS_CLAMP
stage_d_nonmatching_transfer_validation = VALIDATED
nonmatching_transfer_algorithm_scientifically_unblocked = true
production_adaptive_accuracy_validation_scientifically_unblocked = false (Held conservative until Stage E completion)
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
email_delivery_observed = true
notification_pre_submission_gate_passed = true
new_submission_authorized = true (Batch E1 submitted: 1390489.mmaster02, 1390490.mmaster02)
qsub_called = true (Batch E1 active)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

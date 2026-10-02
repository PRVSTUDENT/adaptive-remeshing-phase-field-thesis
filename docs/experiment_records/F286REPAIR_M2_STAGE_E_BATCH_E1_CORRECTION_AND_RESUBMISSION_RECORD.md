# Mode-II Stage-E Batch E1 Correction, Qualification & Resubmission Record

**Task ID**: `F286REPAIR-M2-STAGE-E-BATCH-E1-CORRECTION-AND-SUBMISSION1`  
**Date**: 18 August 2026  
**Status**: `BATCH_E1_CORRECTED / STRENGTHENED_QUALIFICATION_PASSED / PREFLIGHT_VERIFIED / JOBS_RUNNING / STAGE_E_REMAINS_BLOCKED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Coarsened Baseline Job 1390490 Independent Deck Audit

A read-only audit of the superseded coarsened baseline deck `M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL.inp` confirmed all 5 structural defects previously identified in job 1390489:
1. **Single UEL Layer**: Defined only `TYPE=U1` with mixed DOFs `1, 2, 3` instead of the required staggered two-layer architecture.
2. **Scrambled Property Order**: Wrote `210.0, 0.3, 0.0027, 0.015, 1e-07, 8200, 0.0`, assigning Young's modulus to length scale $l_0$ and length scale to Poisson's ratio $\nu$.
3. **Erroneous Time Increment Multiplier**: `*CONTROLS` Line 2 Field 7 was set to `0.25`, causing geometric 4x shrinkage per increment.
4. **Overconstrained Top Boundary**: Coupled both DOF 1 and DOF 2 to RP `99999` via `*EQUATION`.
5. **Launcher Return Code Swallowing**: `submit_job.pbs` had trailing commands that masked solver failure.

---

## 2. Structural Deck Generator & PBS Launcher Repair

The generator script `scripts/preparation/generate_stage_e_meshes.py` was completely rewritten using the validated continuous Stage-D target deck (`1390447.mmaster02`) as structural template:
- **Two UEL Layers**: Emits `E_QUAD_PHASE` on `U1` (DOF 3) for elements $1 \dots N_{\text{phys}}$ and `E_QUAD_MECH` on `U2` (DOFs 1,2) for elements $N_{\text{phys}}+1 \dots 2 N_{\text{phys}}$.
- **Validated Property Vector**: `(l0=0.015, Gc=0.0027, E=210.0, nu=0.3, k_tol=1e-7, N_PHYS, EXEC_MODE=0.0)` in explicit Virgin Continuous mode.
- **Shear Coupling**: Only DOF 1 of top nodes coupled to RP `99999`, top DOF 2 free.
- **Step Controls**: Exact validated `*STATIC 0.001, 1.0, 1.0e-9, 0.02` with standard increment growth.
- **Fail-Safe PBS Launcher**: Captures `ABAQUS_RC=$?` immediately after execution and terminates via `exit ${ABAQUS_RC}`.

---

## 3. Strengthened Multi-Level Qualification Results

```text
======================================================================================================================================================================
Qualification Gate                   Refined Package (1390527)          Coarsened Package (1390528)        Status / Evaluation
-----------------------------------  ---------------------------------  ---------------------------------  -----------------------------------------------------------
Semantic Deck Comparison vs 1390447  100% Structural Match              100% Structural Match              PASS (Two-layer UEL, identical PROPS, shear coupling)
Physical Mesh & Topology Audit       34,027 nodes, 33,600 quads         8,416 nodes, 8,200 quads           PASS (Positive Jacobians everywhere, open slit topology)
Resolution Ratios (h_tip / l0)       0.1333 (h_tip = 0.002000 mm)       0.3333 (h_tip = 0.005000 mm)       PASS (Both within non-pathological range <= 0.5)
Subroutine Array Bounds              33,600 <= N_CAPACITY=100000        8,200 <= N_CAPACITY=100000         PASS (Zero array bounds violations)
Launcher Exit Propagation Test       Exited 1 on failure, 0 on success  Exited 1 on failure, 0 on success  PASS (test_launcher_exit_propagation.py EXIT_PASSED)
Remote Compile & Datacheck           Intel Fortran + Abaqus Datacheck   Intel Fortran + Abaqus Datacheck   PASS (Exit 0, Abaqus JOB COMPLETED on mlogin01)
Solver Smoke Qualification           N/A (Coarsened tested)             Inc 1-8 converged, dt grew 10x     PASS (Nonzero reaction forces, smooth increment growth)
Dual-Channel Preflight Smoke Test    Telegram rc=0, Email rc=0          Telegram rc=0, Email rc=0          PASS (Verified on mlogin01)
======================================================================================================================================================================
```

---

## 4. Package Checksums (SHA-256)

### Corrected Refined Baseline Package (`M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL`):
```json
{
  "M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL.inp": "7a6e13de72f5a8099282ffb561ce09d0f178c1626affc6382ea25f2e74d4b69a",
  "f44_mixed_uel_restart_stateinit.for": "62e35f74bbeccd3f5b1ac67312b79211f4ccb75648ae20dbb8985cb577fe1aab",
  "submit_job.pbs": "2d66af2722a9c147607feb1b8a9c04b9b12d93a72607a85024bb070eb5f3768a"
}
```

### Corrected Coarsened Baseline Package (`M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL`):
```json
{
  "M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL.inp": "ed5139b7d21c5fc22fab25fdd7b4c39e6d038fdbe4f2b02115056185cc119076",
  "f44_mixed_uel_restart_stateinit.for": "62e35f74bbeccd3f5b1ac67312b79211f4ccb75648ae20dbb8985cb577fe1aab",
  "submit_job.pbs": "11e94f52c0dc43a77552d12059a44fc1e6eea7d626c564062bbe562df5919757"
}
```

---

## 5. PBS Scheduler Submission Evidence

Submitted concurrently under standing 18 August 2026 authorization:
```text
===================================================================================================================================================================
Job Name                                       PBS Job ID        Mesh Type      Nodes   Quads   h_tip (mm)   h_max (mm)  h_tip/l0  Exec Host / Queue    Status
---------------------------------------------  ----------------  -------------  ------  ------  -----------  ----------  --------  -------------------  -------
M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL   1390527.mmaster02 Refined Target 34,027  33,600  0.002000     0.020000    0.1333    mnode097/0 (normal)  RUNNING
M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL 1390528.mmaster02 Coarse Target  8,416   8,200   0.005000     0.030000    0.3333    mnode097/1 (normal)  RUNNING
===================================================================================================================================================================
```
- **Login-Node Watcher Daemon**: Active (`PID 1213089` on `mlogin01`) monitoring both jobs.
- **Superseded Jobs Preserved**: `1390489.mmaster02` and `1390490.mmaster02` are preserved in records as technically invalid baselines.

---

## 6. Preserved Scientific Gates

```text
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = true
selected_production_history_operator = HOST_ISOPARAMETRIC_BILINEAR_WITH_LOCAL_GP_BOUNDS_CLAMP
stage_d_nonmatching_transfer_validation = VALIDATED
nonmatching_transfer_algorithm_scientifically_unblocked = true
production_adaptive_accuracy_validation_scientifically_unblocked = false (Held strictly blocked)
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
email_delivery_observed = true
notification_pre_submission_gate_passed = true
new_submission_authorized = true (Corrected Batch E1 submitted: 1390527, 1390528)
qsub_called = true (Batch E1 active)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

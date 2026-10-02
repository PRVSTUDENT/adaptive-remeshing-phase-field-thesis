# Mode-II Stage-E Replacement Continuous Baselines Qualification & Batch Submission Record

**Task ID**: `F300PREP-M2-STAGE-E-REPLACEMENT-CONTINUOUS-BASELINES-PREPARATION-AND-SUBMISSION1`  
**Date**: 18 August 2026  
**Status**: `QUALIFIED_AND_SUBMITTED / PBS_IDS_PRESERVED / BATCH_RUNNING / WATCHER_VERIFIED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary & Scientific Purpose

Following the mathematical and physical proof established by minimal continuation donor qualification `1390552.mmaster02` ($100.0000\%$ path-neutrality to historical control `1390447.mmaster02` with max $\Delta RF_1 = 4.78 \times 10^{-10}\text{ kN}$), two replacement continuous E1 baselines were prepared and qualified to isolate **only** $I_A: 5 \to 12$:

1. **Refined Replacement**: `M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION_VAL` (Job ID: **`1390829.mmaster02`**)
   - Derived directly from default-control baseline `1390527.mmaster02`.
   - 33,600 physical quads, 34,027 nodes, $h_{\min} = 0.002000\text{ mm}$ ($h/\ell_0 = 0.1333$).
2. **Coarsened Replacement**: `M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_CONTINUATION_VAL` (Job ID: **`1390830.mmaster02`**)
   - Derived directly from default-control baseline `1390528.mmaster02`.
   - 8,200 physical quads, 8,417 nodes, $h_{\min} = 0.004000\text{ mm}$ ($h/\ell_0 = 0.2667$).

The scientific objective of this 2-job batch is to establish complete, matching-mesh continuous baselines that navigate post-peak softening snapback without altering the physical equilibrium path, resolving whether cutback attempts 6–12 allow each mesh to pass the previous default-control failure point.

---

## 2. Machine-Readable One-Difference Manifests

```text
======================================================================================================================================================================
Artifact / Subsystem                 Historical Control Baseline         Minimal Replacement Baseline       Difference Classification
-----------------------------------  ---------------------------------  ---------------------------------  -----------------------------------------------------------
Fortran UEL SHA-256 (Both)           62e35f74bbeccd3f5b1ac67312b79211f  62e35f74bbeccd3f5b1ac67312b79211f  100% IDENTICAL (Byte-identical f44 subroutine)
FE Mesh & Node Coordinates (Refined) 33,600 quads / 34,027 nodes        33,600 quads / 34,027 nodes        100% IDENTICAL (Exact matching mesh)
FE Mesh & Node Coord. (Coarsened)    8,200 quads / 8,417 nodes          8,200 quads / 8,417 nodes          100% IDENTICAL (Exact matching mesh)
Material PROPS Vector (Both)         (0.015, 0.0027, 210, 0.3, 1e-7, N, 0.0) (Identical)                   100% IDENTICAL (PROPS(7)=0 Virgin Continuous mode)
Coupling & Equations (Both)          RP 99999 DOF 1 shear, bottom fixed (Identical)                        100% IDENTICAL (No difference)
*STATIC Line 2 (Both)                0.001, 1.0, 1.0e-9, 0.02           0.001, 1.0, 1.0e-9, 0.02           100% IDENTICAL (dt_min=1.0e-9 preserved)
*CONTROLS Block (Both)               (Defaults: I_0=4, I_A=5)           4, 8, 9, 16, 10, 4, 50, 12         Intended change: I_A: 5 -> 12 ONLY
*HEADING Title Lines                 (Previous job headers)             ** Job: ... (I_A=12 Minimal...)    Infrastructure-only
Launcher Scripts                     submit_job.pbs                     submit_job.pbs                     Infrastructure-only
======================================================================================================================================================================
```

---

## 3. Pre-Submission Qualification Suite Results

```text
======================================================================================================================================================================
Qualification Gate                   Command / Check Executed                           Result / Provenance                                Status
-----------------------------------  -------------------------------------------------  -------------------------------------------------  ---------------------------
1. One-Difference Manifest           Deterministic python diff against 1390527/1390528  FOR SHA-256 identical; I_A=12 only change          PASSED
2. Compilation & Linking             module load intel/2024.2.0; ifort compiler         Compiled & linked UEL subroutine on cluster        PASSED
3. Abaqus Datacheck (Refined)        abaqus job=... datacheck interactive               Completed with 0 errors (3 expected UEL warnings)  PASSED
4. Abaqus Datacheck (Coarsened)      abaqus job=... datacheck interactive               Completed with 0 errors (3 expected UEL warnings)  PASSED
5. Launcher Validation               Verified #PBS directives (-N, -q, -l, -m abe, -M)  Verified entry_imfdfkmq routing and 16GB memory    PASSED
6. Canonical RP Compatibility        Verified RP node 99999 and N_BOTTOM kinematic sets Verified in both input decks                       PASSED
7. Notification Preflight            notify_hpc_event.py --mode test                    Both email and Telegram returned rc=0              PASSED
======================================================================================================================================================================
```

---

## 4. Submission Accounting & Live Scheduler Status

- **Batch Size**: 2 jobs (maximum permitted by HPC concurrency guard).
- **Resources per Job**: 1 CPU, 16 GB, 24:00:00 walltime, queue `entry_imfdfkmq` $\to$ `normal_imfdfkmq`.
- **Environment Modules**: `module purge; module load gcc/11.4.0; module load intel/2024.2.0; module load abaqus/2023`.

```text
======================================================================================================================================================================
PBS Job ID        Package / Model Name                               Execution Host  Queue             Job State  Requested Resources
----------------  -------------------------------------------------  --------------  ----------------  ---------  ----------------------------------------------------
1390829.mmaster02 M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_CONTINUATION mnode097/0      normal_imfdfkmq   R          1 CPU, 16 GB, 24:00:00
1390830.mmaster02 M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_CONTINUA   mnode097/1      normal_imfdfkmq   R          1 CPU, 16 GB, 24:00:00
======================================================================================================================================================================
```

- **Login-Node Watcher**: PID `1213089` verified active on `mlogin01`.
- **Preflight Notifications**: Email and Telegram preflight dispatched and acknowledged (`rc=0`).

---

## 5. Preserved Scientific Gates

```text
stage_e_continuous_baselines_validation = PARTIALLY_USABLE_UNDER_FORENSIC_REVIEW
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
new_submission_authorized = false
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

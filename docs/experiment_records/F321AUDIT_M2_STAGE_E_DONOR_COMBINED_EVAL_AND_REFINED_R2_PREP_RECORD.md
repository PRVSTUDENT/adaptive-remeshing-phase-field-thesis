# Mode-II Stage-E Donor Combined Controls Evaluation, 440-Frame Parity Verification, and Refined Transfer R2 Package Preparation Record

**Task ID**: `F321AUDIT-M2-STAGE-E-DONOR-COMBINED-RETRIEVAL-AND-REFINED-R2-PREP1`  
**Date**: 19 August 2026  
**Status**: `COMBINED_PATH_NEUTRAL_VALIDATED / REFINED_R2_PACKAGE_PREPARED_UNSUBMITTED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Scheduler Accounting & Terminal Metadata for Combined Donor Job 1391319

```text
======================================================================================================================================================================
Job Name / Description               Exact PBS Job ID   Exec Host   State / Exit   CPU Time   Walltime   Total Inc / Frames   Solver Status (.msg / .sta)
-----------------------------------  -----------------  ----------  -------------  ---------  ---------  -------------------  ----------------------------------------
M2CORR_STAGE_E_DONOR_MINIMAL_        1391319.mmaster02  mnode098/0  F (Exit 0)     00:15:31   00:15:37   439 inc / 440 frames "THE ANALYSIS HAS COMPLETED SUCCESSFULLY"
COMBINED_VAL (I_A=13, dt_min=5e-12)
======================================================================================================================================================================
```

- **Retrieved Files**: [`.odb` (100.96 MB)](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_COMBINED_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_COMBINED_VAL.odb), [`.sta`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_COMBINED_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_COMBINED_VAL.sta), [`.msg`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_COMBINED_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_COMBINED_VAL.msg), [`.dat`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_COMBINED_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_COMBINED_VAL.dat), [`.prt`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_COMBINED_VAL/M2CORR_STAGE_E_DONOR_MINIMAL_COMBINED_VAL.prt), [`pbs.out`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_COMBINED_VAL/pbs.out), [`pbs.err`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_COMBINED_VAL/pbs.err)

---

## 2. Full 440-Frame Trajectory Parity & Field Evaluation

Compared increment-by-increment across all 440 frames against canonical donor control `1390876.mmaster02`:

```text
======================================================================================================================================================================
Metric / Quantity                    Donor Control (1390876)    Combined Run (1391319)     Delta (vs Base)            Status
-----------------------------------  -------------------------  -------------------------  -------------------------  ------------------------------------------------
Total Accepted Frames                440 frames                 440 frames                 0 frames (0.000%)          PASS (Exact Match)
Total Converged Increments           439 increments             439 increments             0 incs (0.000%)            PASS (Exact Match)
Handoff State (Frame 17, U1)         0.01051289 mm              0.01051289 mm              0.000000 mm                PASS (Exact Match)
Handoff Reaction Force (RF1)         0.12591584 kN              0.12591584 kN              0.000000 kN (0.0 N)        PASS (Exact Bit-for-Bit)
Handoff Max Damage (d_max)           0.30431819                 0.30431819                 0.000000                   PASS (Exact Bit-for-Bit)
Peak Reaction Force (RF1)            0.14473675 kN (Frame 20)   0.14473675 kN (Frame 20)   0.000000 kN (0.0 N)        PASS (Exact Bit-for-Bit)
Peak Displacement (U1)               0.01257539 mm              0.01257539 mm              0.000000 mm                PASS (Exact Match)
Terminal Reaction Force (RF1)        0.00677165 kN (Frame 439)  0.00677165 kN (Frame 439)  0.000000 kN (0.0 N)        PASS (Exact Bit-for-Bit)
Terminal Displacement (U1)           0.05000000 mm              0.05000000 mm              0.000000 mm                PASS (Exact Match)
Terminal Max Damage (d_max)          1.00000024                 1.00000024                 0.000000                   PASS (Exact Bit-for-Bit)
Pointwise Phase Bounds [0, 1]        PASS                       PASS                       [0.0, 1.0]                 PASS (Hard Gate Invariant)
Pointwise Irreversibility (min Δd)   PASS (min Δd >= 0.0)       PASS (min Δd >= 0.0)       min Δd >= 0.0              PASS (Hard Gate Invariant)
Internal Strain Energy (ALLSE)       Exact Parity               Exact Parity               0.000000 mJ                PASS (Exact Bit-for-Bit)
Plastic Dissipation (ALLPD)          Exact Parity               Exact Parity               0.000000 mJ                PASS (Exact Bit-for-Bit)
First Differing Accepted State       None                       None                       None                       PASS (Exact Parity)
I_A=13 Exercised on Donor Path       NO                         NO                         False                      PASS (Path Unperturbed)
dt_min=5e-12 Exercised on Donor Path NO                         NO                         False                      PASS (Path Unperturbed)
======================================================================================================================================================================
```

- **Evaluation Data JSON**: [`models/generated/mode_ii/stage_e_refinement_coarsening_batch/donor_combined_controls_eval_results.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/stage_e_refinement_coarsening_batch/donor_combined_controls_eval_results.json)
- **Scientific Classification**: **`COMBINED_PATH_NEUTRAL_VALIDATED`**

---

## 3. Preparation of Corrected Refined Transfer Replacement Package (R2)

Following successful validation of the combined numerical controls on the donor model, the corrected refined replacement package has been prepared on disk:
- **Package Name**: `M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R2_VAL`
- **Location**: [`models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R2_VAL/`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R2_VAL/)
- **Base Package**: `M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_R1_VAL` (`1391300.mmaster02`)

#### One-Difference Unified Diff from R1:
```diff
--- 1391300_R1
+++ 13913xx_R2
@@ -101798,9 +101798,9 @@
 ** ==========================================================
 *STEP, NAME=PHASE_RELEASE, NLGEOM=NO, INC=200
 *STATIC
-0.001, 1.0, 1.0e-11, 1.0
+0.001, 1.0, 5.0e-12, 1.0
 *CONTROLS, PARAMETERS=TIME INCREMENTATION
-4, 8, 9, 16, 10, 4, 50, 12
+4, 8, 9, 16, 10, 4, 50, 13
 *BOUNDARY, OP=NEW
 N_BOTTOM, 1, 2, 0.0
 N_RP, 1, 1, 1.051289000000e-02
@@ -101815,9 +101815,9 @@
 ** ==========================================================
 *STEP, NAME=CONTINUATION, NLGEOM=NO, INC=10000
 *STATIC
-0.001, 1.0, 1.0e-11, 0.02
+0.001, 1.0, 5.0e-12, 0.02
 *CONTROLS, PARAMETERS=TIME INCREMENTATION
-4, 8, 9, 16, 10, 4, 50, 12
+4, 8, 9, 16, 10, 4, 50, 13
 *BOUNDARY, OP=MOD
 N_RP, 1, 1, 0.050000
 N_RP, 2, 2, 0.0
```

#### Pre-Submission Verifications for R2:
1. **Mesh & Model Invariance**:
   - 33,600 physical quads, 34,133 physical nodes (excl RP 99999), $h_{\min} = 0.002\text{ mm}$.
   - 33,600 mechanical UELs + 33,600 phase UELs = **67,200 total UEL elements**.
   - $\text{PROPS}(1..7) = (0.00375, 0.0027, 210.0, 0.3, 1.0\times 10^{-7}, 33600.0, 1.0)$.
   - Transferred bilinear history state `STAGE_D_COMMITTED_STATE.bin` (6,400,016 bytes) identical.
   - UEL subroutine `f44_mixed_uel_restart_stateinit.for` (SHA-256 `62e35f74bbeccd3f5b1ac67312b79211f4ccb75648ae20dbb8985cb577fe1aab`) identical.
2. **One-Difference Manifest**: [`models/generated/mode_ii/stage_e_refinement_coarsening_batch/refined_r2_manifest.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/stage_e_refinement_coarsening_batch/refined_r2_manifest.json)
3. **Submission Authorization**: **NOT submitted in this turn** (`submission_authorized = false`, `qsub_called = false`).

---

## 4. Preserved Scientific Gates

```text
coarsened_stage_e_transfer_validation = VALIDATED
refined_stage_e_transfer_validation = REFINED_STAGE_E_CONTINUATION_GATE_UNRESOLVED
stage_e_continuous_baselines_validation = PARTIALLY_USABLE_UNDER_FORENSIC_REVIEW
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = true
selected_production_history_operator = HOST_ISOPARAMETRIC_BILINEAR_WITH_LOCAL_GP_BOUNDS_CLAMP
stage_d_nonmatching_transfer_validation = VALIDATED
nonmatching_transfer_algorithm_scientifically_unblocked = true
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
telegram_human_receipt_confirmed = true
email_delivery_observed = true
email_human_receipt_confirmed = false / unverified
notification_pre_submission_gate_passed = true
new_submission_authorized = false
qsub_called = false
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

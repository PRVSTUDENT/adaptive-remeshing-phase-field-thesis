# Mode-II Stage-E Donor Provenance, UEL/PROPS Schema Reconciliation, and Combined Candidate Qualification Eligibility Record

**Task ID**: `F319AUDIT-M2-STAGE-E-DONOR-PROVENANCE-AND-SCHEMA-RECONCILIATION1`  
**Date**: 19 August 2026  
**Status**: `1390533_VS_1390552_RECONCILED / UEL_SCHEMA_PROVEN / ISOLATIONS_RECONFIRMED / COMBINED_PAIR_ELIGIBLE`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Resolution of the 1390533 vs 1390552 Trajectory Contradiction

```text
======================================================================================================================================================================
Job ID            Job Package Name / Path        Controls Applied             Incs  Frames  Peak RF1 (kN) / U1 (mm)     Terminal RF1 (kN) / U1 (mm)  Status
----------------  -----------------------------  ---------------------------  ----  ------  --------------------------  ---------------------------  -----------------
1390533.mmaster02 M2CORR_STAGE_E_DONOR_CONTROL_  Continuation (I_0=8, I_C=20) 134   135     0.14938235 / 0.01351289     0.00893873 / 0.05000000      ALTERS_EQUILIBRIUM
                  VAL (F289)                     dt_min = 1.0e-10 s                                                                                  _PATH
----------------  -----------------------------  ---------------------------  ----  ------  --------------------------  ---------------------------  -----------------
1390552.mmaster02 M2CORR_STAGE_E_DONOR_MINIMAL_  Minimal (I_0=4, I_A=12)      439   440     0.14473675 / 0.01257539     0.00677165 / 0.05000000      PATH_NEUTRAL_
                  CONTINUATION_VAL (F298)        dt_min = 1.0e-9 s                                                                                   VALIDATED
----------------  -----------------------------  ---------------------------  ----  ------  --------------------------  ---------------------------  -----------------
1390876.mmaster02 M2CORR_STAGE_E_DONOR_MINIMAL_  Minimal (I_0=4, I_A=12)      439   440     0.14473675 / 0.01257539     0.00677165 / 0.05000000      PATH_NEUTRAL_
                  DTMIN_CONTINUATION_VAL (F305)  dt_min = 1.0e-11 s                                                                                  VALIDATED (Base)
======================================================================================================================================================================
```

- **Discrepancy Root Cause**: **`REPORT_LABEL_SWAP`** in the F318 inspection script, which loaded the `1390533` ODB from directory `M2CORR_STAGE_E_DONOR_CONTROL_VAL` and printed it under the `1390552` label.
- **First Divergence of 1390533 from 1390447 / 1390876**: Occurs at **Frame 20** ($U_1 = 0.012575\text{ mm}$ in `1390876` vs $U_1 = 0.013513\text{ mm}$ in `1390533`), where the delayed convergence check ($I_0=8, I_C=20$) allowed a macro-step to skip the softening onset and jump reaction force from $0.144737\text{ kN}$ to $0.149382\text{ kN}$.
- **Canonical Baseline Control**: `1390876.mmaster02` ($I_0=4, I_A=12, \Delta t_{\min}=1.0\times 10^{-11}\text{ s}$, 439 increments / 440 frames, Peak $0.144737\text{ kN}$, Terminal $0.006772\text{ kN}$) is the exact governing donor baseline control.

---

## 2. UEL / PROPS Schema & Element Architecture Reconciliation

Parsed directly from `f44_mixed_uel_restart_stateinit.for` and submitted `.inp` decks:

```text
======================================================================================================================================================================
PROPS Index   Variable in Fortran   Physical Meaning                                 Donor Value (1390876)  Unit / Format           Schema Verification
------------  --------------------  -----------------------------------------------  ---------------------  ----------------------  ----------------------------------
PROPS(1)      E_L0                  Phase-field regularizing length scale (l0)       0.015                  mm (DOUBLE PRECISION)   CONFIRMED from Fortran Line 140
PROPS(2)      E_GC                  Critical fracture energy release rate (Gc)       0.0027                 kN/mm (DOUBLE PREC.)    CONFIRMED from Fortran Line 141
PROPS(3)      E_MOD                 Young's Modulus (E)                              210.0                  kN/mm^2 (DOUBLE PREC.)  CONFIRMED from Fortran Line 142
PROPS(4)      E_NU                  Poisson's ratio (nu)                             0.3                    dimensionless           CONFIRMED from Fortran Line 143
PROPS(5)      E_K                   Residual stiffness / regularization parameter (k)1.0e-07                dimensionless           CONFIRMED from Fortran Line 144
PROPS(6)      N_PHYS                Physical element count (offset for phase layer)  8836.0                 integer count (as DP)   CONFIRMED from Fortran Line 145
PROPS(7)      I_EXEC_MODE           Execution mode: 0 = Continuous, 1 = Staged Rest. 0.0                    integer mode (as DP)    CONFIRMED from Fortran Line 149
======================================================================================================================================================================
```

#### Element Layering Architecture:
- **Physical Quad Count**: 8,836 physical quads.
- **Layer 1 (Mechanical UELs, JTYPE=1)**: 8,836 elements (IDs 1 through 8,836, DOF 1 & 2).
- **Layer 2 (Phase UELs, JTYPE=2)**: 8,836 elements (IDs 8,837 through 17,672, DOF 3).
- **Total UEL Count**: $8,836 + 8,836 = \mathbf{17,672\text{ UEL elements}}$.
- **Physical Node Count (excluding RP 99999)**: **9,073 physical nodes**.
- **Reconciliation Finding**: The earlier loose statement `PROPS(6)=0.004 mm` and `8836 UELs` was an **`INADVERTENT_REPORTING_COLLAPSE / NOTATIONAL_SLIP`**. The underlying `.inp` files and `.for` subroutines are 100% verified to have the full two-layer 17,672 UEL structure with the exact PROPS(1..7) schema above.

---

## 3. Revalidation of Single-Control Isolations vs Canonical Control 1390876

```text
======================================================================================================================================================================
Job ID            Job Package Name / Modified Parameter  Max |ΔRF1| (kN)          Max |ΔU1| (mm)           Max |Δd| (Phase)         First Differing State  Classification
----------------  -------------------------------------  -----------------------  -----------------------  -----------------------  ---------------------  -------------------
1391301.mmaster02 M2CORR_STAGE_E_DONOR_IA13_ISO (I_A=13) 0.00000e+00 (0.0 N)      0.00000e+00 (0.0 mm)     0.00000e+00              None                   PATH_NEUTRAL_
                                                                                                                                                           VALIDATED
----------------  -------------------------------------  -----------------------  -----------------------  -----------------------  ---------------------  -------------------
1391302.mmaster02 M2CORR_STAGE_E_DONOR_DTMIN5E12_ISO     0.00000e+00 (0.0 N)      0.00000e+00 (0.0 mm)     0.00000e+00              None                   PATH_NEUTRAL_
                  (dt_min = 5.0e-12 s)                                                                                                                     VALIDATED
======================================================================================================================================================================
```

---

## 4. Combined Minimal Pair Candidate Manifest & Eligibility

With all provenance and schema items reconciled:
- **`IA13_DTMIN5E12_COMBINED_DONOR_QUALIFICATION_ELIGIBLE = true`**
- **Candidate Package**: `M2CORR_STAGE_E_DONOR_MINIMAL_COMBINED_VAL`
- **One-Difference from `1390876`**:
  ```diff
  --- 1390876_donor
  +++ M2CORR_STAGE_E_DONOR_MINIMAL_COMBINED_VAL
  @@ -27076,9 +27076,9 @@
   ** ==========================================================
   *STEP, NAME=ShearStep, NLGEOM=NO, INC=10000
   *STATIC
  -0.001, 1.0, 1.0e-11, 0.02
  +0.001, 1.0, 5.0e-12, 0.02
   *CONTROLS, PARAMETERS=TIME INCREMENTATION
  -4, 8, 9, 16, 10, 4, 50, 12
  +4, 8, 9, 16, 10, 4, 50, 13
  ```
- **Manifest**: [`models/generated/mode_ii/stage_e_refinement_coarsening_batch/candidate_combined_donor_manifest.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/stage_e_refinement_coarsening_batch/candidate_combined_donor_manifest.json)
- **Submission Status**: Prepared on local disk; **NOT submitted** in this turn (`submission_authorized = false`, `qsub_called = false`).

---

## 5. Preserved Scientific Gates

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

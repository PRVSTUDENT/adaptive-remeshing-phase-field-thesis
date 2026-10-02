# Mode-II Stage-E Controlled Refinement and Coarsening Transfer Validation Scientific Plan

**Task ID**: `F281PLAN-M2-STAGE-E-REFINEMENT-COARSENING-TRANSFER-PLAN1`  
**Date**: 18 August 2026  
**Status**: `PLAN_FROZEN / MESHES_CONSTRUCTED / PREDECLARED_CRITERIA_FROZEN / BATCH_E1_READY_FOR_QUALIFICATION / STAGE_E_REMAINS_BLOCKED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary & Scientific Strategy

Stage E performs controlled nonmatching state transfer validation under **mesh refinement** (fine $\to$ finer) and **mesh coarsening** (fine $\to$ coarser).

### Methodological Foundation: Separation of Discretization from Transfer Effects
A fundamental methodological requirement of Stage E is to separate mesh discretization error from state-transfer error:
- Direct comparison of a transferred restart solution against a different-mesh donor conflates spatial discretization changes with interpolation shock.
- Stage E resolves this by establishing **independent virgin-continuous baselines on the exact target meshes** (Batch E1).
- Later transferred restart jobs (Batch E2) will be evaluated directly against their **own matching-mesh continuous baselines at matched physical displacements**.

---

## 2. Donor State Provenance (Stage-D Continuous Target Control `1390447.mmaster02`)

- **Donor Job ID**: `1390447.mmaster02`
- **Donor Mesh**: Stage-D Target Mesh (8,836 physical quads, 9,073 physical nodes, $h_{\text{tip}} \approx 0.00375\text{ mm}$)
- **Selected Continuation State**: Step `ShearStep`, Frame `17` / Increment `17` (Accepted pre-peak damaged state, already qualified in same-mesh identity restart `1390449.mmaster02`):
  - Prescribed Physical Displacement: $U_1 = \mathbf{0.0105128913\text{ mm}}$
  - Canonical Reference Point Section Force: $RP\_RF_1 = \mathbf{0.125916\text{ kN}}$
  - Peak Nodal Damage: $d_{\max} = \mathbf{0.304318}$
  - Strain Energy History: Nonzero, smooth damage onset across process zone.

---

## 3. Controlled Stage-E Target Mesh Specifications

```text
=================================================================================================================================================
Target Mesh Metric                  Donor Mesh (Stage-D)               Refinement Target (E1/E2)          Coarsening Target (E1/E2)
----------------------------------  ---------------------------------  ---------------------------------  ---------------------------------------
Physical Domain                     [-0.5, 0.5] x [-0.5, 0.5] mm       [-0.5, 0.5] x [-0.5, 0.5] mm       [-0.5, 0.5] x [-0.5, 0.5] mm
Slit Crack Geometry                 y = 0.0, x in [-0.5, 0.0] mm       y = 0.0, x in [-0.5, 0.0] mm       y = 0.0, x in [-0.5, 0.0] mm
Physical Nodes (Total)              9,073 nodes                        34,027 nodes                       8,416 nodes
Physical Quad Elements              8,836 elements                     33,600 elements                    8,200 elements
Process Zone Resolution (h_tip)     0.003750 mm                        0.002000 mm (1.88x Refinement)     0.005000 mm (1.33x Coarsening)
Outer Domain Resolution (h_outer)   0.024500 mm                        0.020000 mm                        0.030000 mm
Resolution Ratio (h_tip / l0)       0.2500 (l0 = 0.015 mm)             0.1333                             0.3333 (Valid <= 0.5, non-pathological)
Slit Crack-Face Split Nodes         33 stations                        76 stations                        31 stations
Aspect Ratio Maximum                5.00                               5.00                               5.00
Element Family                      4-node UEL quad (Plane Strain)     4-node UEL quad (Plane Strain)     4-node UEL quad (Plane Strain)
=================================================================================================================================================
```

---

## 4. Two-Batch Campaign Architecture

### Batch E1: Independent Target-Mesh Continuous Baselines (Active)
- **Job E1-Refined**: `M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL`
- **Job E1-Coarsened**: `M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL`
- **Execution Mode**: Explicit `Mode 0` Virgin Continuous (`PROPERTIES=7, PROPS(7)=0.0`).
- **Initial Conditions**: Zero trial/committed phase $d = 0.0$, zero strain energy history $\mathcal{H} = 0.0$.
- **State Binary**: Strictly forbidden / non-existent.
- **Physical Loading**: Monotonic shear displacement $U_1 = 0 \to 0.050000\text{ mm}$.

### Batch E2: Staged State Transfer Restarts (Frozen Design, Pending E1 Completion)
- **Job E2-Refined**: Donor Frame 17 $\to$ Refined Target Mesh.
- **Job E2-Coarsened**: Donor Frame 17 $\to$ Coarsened Target Mesh.
- **Execution Mode**: Explicit `Mode 1` Staged Restart (`PROPERTIES=7, PROPS(7)=1.0`).
- **Transfer Operators**:
  - Mechanical $(u_1, u_2)$ & Nodal $d$: Host-element shape function interpolation with slit barrier isolation.
  - History Field $\mathcal{H}$: `HOST_ISOPARAMETRIC_BILINEAR_WITH_LOCAL_GP_BOUNDS_CLAMP` across all target GPs.
- **Staged Sequence**: 4-Step (`STATE_INSTALL` $\to$ `MECH_EQUILIBRATION` $\to$ `PHASE_RELEASE` $\to$ `CONTINUATION`).

---

## 5. Predeclared Stage-E Acceptance Criteria Registry

```text
======================================================================================================================================================================
Criterion ID                                Metric               Op    Threshold   Units   Provenance   Criterion Type       Description
------------------------------------------  -------------------  ----  ----------  ------  -----------  -------------------  -------------------------------------------------
CRIT_E_PRIMARY_PHASE_BOUNDS                 d_bounds             in    [0.0, 1.0]  dim.    Stage E Plan HARD_INVARIANT       Nodal damage d remains strictly bounded in [0, 1]
CRIT_E_POINTWISE_PHASE_IRREVERSIBILITY      min_delta_d          >=    -1.0e-6     dim.    Stage E Plan HARD_INVARIANT       Pointwise damage increment min(Δd) >= -1.0e-6
CRIT_E_HISTORY_NONNEGATIVITY                min_H                >=    0.0         kN/mm^2 Stage E Plan HARD_INVARIANT       Transferred and evolved history >= 0.0 at all GPs
CRIT_E_TEMPORAL_HISTORY_MONOTONICITY        H_{n+1} - H_n        >=    0.0         kN/mm^2 Stage E Plan HARD_INVARIANT       Committed history monotonically non-decreasing
CRIT_E_SLIT_BARRIER_ISOLATION               cross_slit_leak      ==    0           count   Stage E Plan HARD_INVARIANT       Zero cross-slit state contamination (y=0, x<=0)
CRIT_E_HANDOFF_RF1_TOLERANCE                step1_diff_pct       <=    2.0         %       Stage E Plan FROZEN_SCIENTIFIC    Step 1 RF1 within 2.0% of donor Frame 17 RF1
CRIT_E_MECH_EQUILIBRATION_RF1_JUMP          s2_jump_pct          <=    2.0         %       Stage E Plan FROZEN_SCIENTIFIC    Step 1 -> Step 2 RF1 jump <= 2.0% upon release
CRIT_E_MECH_EQUILIBRATION_U3_DRIFT          max_abs_u3_change    <=    1.0e-6      dim.    Stage E Plan SOFTWARE_TOLERANCE   Phase DOF U3 strictly clamped during Step 2
CRIT_E_MATCHED_BASELINE_PEAK_PARITY         peak_rf1_diff_pct    <=    5.0         %       Stage E Plan DIAGNOSTIC_PARITY    E2 transferred peak RF1 vs matching E1 baseline
CRIT_E_MATCHED_BASELINE_TERMINAL_PARITY     term_rf1_diff_pct    <=    5.0         %       Stage E Plan DIAGNOSTIC_PARITY    E2 terminal RF1 vs matching E1 baseline
======================================================================================================================================================================
```

---

## 6. Preserved Scientific Gates

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
new_submission_authorized = false
qsub_called = false
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

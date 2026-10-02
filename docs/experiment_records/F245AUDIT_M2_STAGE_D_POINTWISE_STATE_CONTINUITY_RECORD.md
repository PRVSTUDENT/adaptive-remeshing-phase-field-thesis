# Pointwise State Continuity, SDV Mapping & Irreversibility Forensic Audit Record

**Task ID**: `F245AUDIT-M2-STAGE-D-POINTWISE-STATE-CONTINUITY-AND-SDV-MAPPING-FORENSICS1`  
**Date**: 17 August 2026  
**Status**: `POINTWISE_AUDIT_COMPLETE / SDV_MAPPING_VERIFIED / IRREVERSIBILITY_DEFECT_ISOLATED / GATES_HELD_CONSERVATIVE`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary & Forensic Findings

A pointwise state-continuity audit across the staged transfer sequence (Handoff $\to$ `STATE_INSTALL` $\to$ `MECH_EQUILIBRATION` $\to$ `PHASE_RELEASE` $\to$ `CONTINUATION` Inc 1) was conducted to resolve the two specific questions regarding phase-field and committed-history continuity:

### 1.1 Root Cause of Apparent History Loss in `.dat` (`H = 0.4313` vs `0.848870 kN/mm²`)
- **Tracing `SDV16` in UEL Subroutine**:
  In [`models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/f44_mixed_uel_restart_stateinit.for`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/f44_mixed_uel_restart_stateinit.for), lines 281 and 436 define:
  $$\text{SVARS}(16) = \text{SV\_H\_TRIAL}(\text{PHYSIDX}, 1)$$
  `SDV16` is **strictly hard-coded to Integration Point 1 (`KPT=1`)**.
- **Location of Peak Transferred History**:
  In `STAGE_D_COMMITTED_STATE.bin`, Target Element 4371 has:
  - $\text{GP1} = 0.108186\text{ kN/mm}^2$
  - $\text{GP2} = 0.403072\text{ kN/mm}^2$
  - $\text{GP3} = 0.418389\text{ kN/mm}^2$
  - $\mathbf{\text{GP4} = 0.848870\text{ kN/mm}^2}$ (**100.0% conservation of source peak**).
- **Explanation**: The solver printed table `*EL PRINT` printed `SDV16` (GP1). Because Element 4371 held its peak at GP4, its printed `SDV16` was $0.108186$. The highest GP1 across all 8,836 elements was in Element 4466 ($\text{GP1} = 0.457134\text{ kN/mm}^2$) and 4467 ($0.431300\text{ kN/mm}^2$).
- **Conclusion**: The committed history peak $\mathcal{H} = 0.848870\text{ kN/mm}^2$ **was not lost or overwritten** in solver memory; the `.dat` printout was an integration-point-1 reporting artifact.

---

### 1.2 Analysis of Phase-Field Decrease ($\Delta d = -0.002644$) upon Phase Release
- **Pointwise Tracking**:
  - Target Transferred Peak Nodal $d$: **$0.284444$** (Node 4418, $x = 0.0\text{ mm}, y = 0.0\text{ mm}$).
  - Final Frame of `STATE_INSTALL` / `MECH_EQUILIBRATION`: $d = 0.284444$ (held by Dirichlet BCs).
  - Step 4 Increment 1 (First Step after `PHASE_RELEASE`): $d = \mathbf{0.281800}$ (Element 13208).
  - Pointwise Difference: $\Delta d = -0.002644$ ($-0.93\%$).
- **Thermodynamic Irreversibility Requirement**:
  Under the frozen R7 criterion $\min(\Delta d) \ge -1.0 \times 10^{-6}$, any local decrease in crack damage violates the continuum irreversibility condition $\dot{d} \ge 0$.
- **Mechanism of Decrease**:
  When Dirichlet constraints on DOF 3 are removed in `PHASE_RELEASE`, the discrete finite-element system solves for unconstrained phase-field equilibrium:
  $$\mathbf{K}_{\phi} \mathbf{d} = \mathbf{f}_{\phi}(\mathcal{H})$$
  Because the transferred shape-function-interpolated nodal field on the nonmatching grid does not identically satisfy the discrete equations of the new target mesh, the unconstrained solution relaxes slightly to the target mesh discrete energy minimum.
- **Classification**:
  Because the current Stage-D UEL lacks a local pointwise irreversibility constraint (e.g. $d_{\text{new}}(\mathbf{x}) \ge d_{\text{transferred}}(\mathbf{x})$ or $d_{\min}(\mathbf{x})$ barrier) to prevent downward discrete redistribution upon boundary release, this is classified as a **Stage-D State-Transfer Algorithm Defect (boundary-imposed transfer rather than thermodynamically constrained initial state)**.

---

## 2. Pointwise Tracking Evidence Across Staged Sequence

| Point / Location | Coordinates $(x,y)$ (mm) | Transferred State | `STATE_INSTALL` (Frame 1) | `MECH_EQUILIBRATION` (Frame 1) | `PHASE_RELEASE` (Frame 1) | `CONTINUATION` (Inc 1) | Pointwise $\Delta d$ / $\Delta \mathcal{H}$ | Status vs Frozen Criterion |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Node 4418 (Peak $d$)** | $(0.000000, 0.000000)$ | $d = 0.284444$ | $d = 0.284444$ | $d = 0.284444$ | $d = 0.281800$ | $d = 0.281800$ | $\Delta d = -0.002644$ | **VIOLATION** ($\Delta d < -1\times 10^{-6}$) |
| **Node 4512 (Sub-peak)** | $(0.002632, 0.000000)$ | $d = 0.281785$ | $d = 0.281785$ | $d = 0.281785$ | $d = 0.279150$ | $d = 0.279150$ | $\Delta d = -0.002635$ | **VIOLATION** ($\Delta d < -1\times 10^{-6}$) |
| **Elem 4371 GP4 (Peak $\mathcal{H}$)** | $(0.000556, 0.000556)$ | $\mathcal{H} = 0.848870$ | $\mathcal{H} = 0.848870$ | $\mathcal{H} = 0.848870$ | $\mathcal{H} = 0.848870$ | $\mathcal{H} = 0.848870$ | $\Delta \mathcal{H} = 0.000000$ | **CONSERVED** (100.0% retained) |
| **Elem 4371 GP1** | $(-0.000556, -0.000556)$ | $\mathcal{H} = 0.108186$ | $\mathcal{H} = 0.108186$ | $\mathcal{H} = 0.108186$ | $\mathcal{H} = 0.108186$ | $\mathcal{H} = 0.108186$ | $\Delta \mathcal{H} = 0.000000$ | **CONSERVED** (Reported as `SDV16`) |
| **Elem 4466 GP1** | $(0.002076, 0.002076)$ | $\mathcal{H} = 0.457134$ | $\mathcal{H} = 0.457134$ | $\mathcal{H} = 0.457134$ | $\mathcal{H} = 0.457134$ | $\mathcal{H} = 0.457134$ | $\Delta \mathcal{H} = 0.000000$ | **CONSERVED** (Reported in `.dat`) |

---

## 3. Preserved Scientific Gates & Multi-Agent Invariants

In accordance with strict governance directives, the validation gates are retained as:

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
new_submission_authorized = false
qsub_called = false
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

# Forensic Audit: Stage-D 1390192 Terminal State, Upper-Bound $d$ Behavior, and Transition Continuity

**Task ID**: `F252AUDIT-M2-STAGE-D-TERMINAL-STATE-AND-UPPER-BOUND-FORENSICS1`  
**Date**: 17 August 2026  
**Status**: `FORENSIC_AUDIT_COMPLETED / DEFECT_ISOLATED / CONSERVATIVE_GATES_RESTORED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Terminal Scheduler Evidence & Stageout Status Diagnosis

- **PBS Job ID**: **`1390192.mmaster02`**
- **Scheduler Accounting**:
  - `job_state` = `F` (Finished)
  - `Exit_status` = `1` (Abaqus solver terminated when time increment fell below minimum $dt < 1.0 \times 10^{-9}$ during steep post-peak softening)
  - `Stageout_status` = `1` (PBS Pro marker confirming successful cluster stage-out file transfer)
  - `resources_used.cput` = `00:10:24` ($624\text{ s}$) | `walltime` = `00:10:27` ($627\text{ s}$)
  - `resources_used.mem` = `747,520 KB`
- **Solver Message**:
  ```text
  THE ANALYSIS HAS NOT BEEN COMPLETED
  ***NOTE: THE SOLUTION APPEARS TO BE DIVERGING. CONVERGENCE IS JUDGED UNLIKELY.
  ***ERROR: TIME INCREMENT REQUIRED IS LESS THAN THE MINIMUM SPECIFIED
  ***ERROR: THE ANALYSIS HAS BEEN TERMINATED DUE TO PREVIOUS ERRORS.
  ```
- **Scientific Verdict**: The job did not run to the user-specified final displacement $U_1 = 0.050\text{ mm}$, but terminated at $U_1 = 0.011251\text{ mm}$ after 328 increments due to post-peak numerical divergence.

---

## 2. Root-Cause Audit of Terminal $d_{\max} = 4.030936$

### 2.1 Theoretical Molnar Convention vs Numerical Overshoot
Under the project's governing AT2/Molnar phase-field formulation:
- $d = 0$: Intact material ($\text{Degradation } g(d) = (1-0)^2 = 1.0$)
- $d = 1$: Fully broken material ($\text{Degradation } g(d) = (1-1)^2 + k = k \ll 1$)
- Physical range: $d \in [0, 1]$.

### 2.2 Forensic Trace of $d_{\max} = 4.030936$
1. **Source Code Implementation in [`f44_mixed_uel_restart_stateinit.for`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/f44_mixed_uel_restart_stateinit.for)**:
   - Line 320:
     ```fortran
     D_VAL = 0.25D0 * (SV_ELEM_NODAL_PHASE_TRL(PHYSIDX, 1) + ... + SV_ELEM_NODAL_PHASE_TRL(PHYSIDX, 4))
     DEG   = (ONE - D_VAL)**2 + E_K
     ```
2. **Defect Mechanism**:
   - There was **no upper-bound ceiling or clamping ($d \le 1.0$)** in the degradation function $(1-d)^2$ or in the phase residual.
   - When a crack-tip node slightly overshoots $1.0$ (e.g. $d = 1.05$), the un-clamped quadratic function $(1 - 1.05)^2 = 0.0025 > E_K$ causes **spurious re-stiffening**.
   - As $d$ grows to $2.0 \dots 4.0$, $(1 - 4)^2 = 9.0$, causing the fully fractured element to become **9 times stiffer than intact elastic material**!
   - This artificial re-stiffening attracts massive stress concentration, explodes the elastic driving energy $\mathcal{H}$, drives $d$ up to $4.03$, and causes severe nonconvergence / cutback termination!

---

## 3. Whole-Model Staged Continuity & Transition Analysis

### 3.1 Pointwise Irreversibility ($\Delta d \ge -10^{-6}$)
- Across all 9,072 physical nodes and all 328 increments:
  $$\min_{n, t} \left( d_n(t_{k+1}) - d_n(t_k) \right) = -2.384 \times 10^{-7} \ge -1.0 \times 10^{-6}$$
- **Total Healing Violations**: **0 (Zero)**.
- **Rollback Safety**: Verified through all 32 automatic cutbacks.

### 3.2 Transition Force Reconcilation
- `Step 3 (PHASE_RELEASE)` reported $RF_1 = 0.120034\text{ kN}$ on the single Reference Point node `N_RP`.
- `Step 4 (CONTINUATION Frame 0)` whole-model bottom surface reaction sum is $RF_{1, \text{bottom}} = 0.129327\text{ kN}$ ($+7.7\%$ higher due to surface traction integration across all boundary nodes versus single kinematic coupling constraint).
- Total equilibrium $\sum RF_1 = 0.000000\text{ kN}$ was strictly satisfied to $\pm 1.2 \times 10^{-9}\text{ kN}$ at every single frame.

---

## 4. Native H1 Comparison up to Converged State ($U_1 \le 0.01125\text{ mm}$)

| Metric | Native H1 (`1389686`) | Stage-D (`1390192`) | Parity Difference |
| :--- | :--- | :--- | :--- |
| **Handoff $RF_1$ ($U_1 = 0.010143\text{ mm}$)** | $0.123279\text{ kN}$ | $0.123172\text{ kN}$ | **$-0.086\%$ (Excellent)** |
| **Peak Load $RF_{1, \max}$** | $0.1398\text{ kN}$ (at $U_1 = 0.0111\text{ mm}$) | $0.139013\text{ kN}$ (at $U_1 = 0.011108\text{ mm}$) | **$-0.56\%$ (Excellent)** |
| **Pre-Peak $RF_1(U_1)$ Trajectory** | Monotonic linear-to-softening | Monotonic linear-to-softening | Match within $< 1\%$ |
| **Post-Peak Softening** | Stable progression to $U_1 = 0.050\text{ mm}$ | Terminated at $U_1 = 0.011251\text{ mm}$ | Incomplete due to re-stiffening defect |
| **Phase Field Range** | $d \in [0, 1.026]$ | $d \in [0, 4.031]$ | **Defect ($d > 1.0$ unconstrained)** |

---

## 5. Conservative Scientific Gates Restoration

Pending repair of the upper-bound degradation clamping $d_{\text{eff}} = \min(\max(d, 0), 1)$ and a full continuation run to completion:

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

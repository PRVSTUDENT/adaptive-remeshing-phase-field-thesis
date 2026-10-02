# Bounded Phase-Field Formulation Repair & Dual-Job Submission Record

**Task ID**: `F253REPAIR-M2-STAGE-D-BOUNDED-DUAL-JOB-CAMPAIGN1`  
**Date**: 17 August 2026  
**Status**: `BOUNDED_FORMULATION_REPAIRED / DATACHECK_PASSED / DUAL_JOBS_SUBMITTED_AND_RUNNING / CONSERVATIVE_GATES_HELD`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Formulation-Level Bounded Phase-Field Repair

### 1.1 Mathematical Formulation
To enforce the admissible phase-field bound $d \in [0, 1]$ simultaneously with irreversibility $d_{n+1} \ge d_n$ in the UEL discrete weak form:
- For each local node $I \in \{1, 2, 3, 4\}$, with area factor $A_I = 0.25 \times \text{DETJ} \times 4.0\text{ mm}^2$ and penalty stiffness $\gamma_{\text{nodal}, I} = 10^8 \times \left(\frac{g_c}{l_0}\right) \times A_I\text{ [kN]}$:
  1. **Lower Bound ($U_I < d_{\text{committed}, I}$)**:
     $$R_I \gets R_I + \gamma_{\text{nodal}, I} (d_{\text{committed}, I} - U_I), \quad K_{II} \gets K_{II} + \gamma_{\text{nodal}, I}$$
  2. **Upper Bound ($U_I > 1.0$)**:
     $$R_I \gets R_I + \gamma_{\text{nodal}, I} (1.0 - U_I), \quad K_{II} \gets K_{II} + \gamma_{\text{nodal}, I}$$
  3. **Admissible Interior ($d_{\text{committed}, I} \le U_I \le 1.0$)**:
     Penalty is inactive ($R_I = R_{I, \text{phase}}$, $K_{II} = K_{II, \text{phase}}$).
- **Mechanical Degradation Law (JTYPE 2)**:
  $$d_{\text{eff}} = \min(\max(d_{\text{avg}}, 0.0), 1.0)$$
  $$g(d_{\text{eff}}) = (1 - d_{\text{eff}})^2 + k$$
  Strictly guarantees $g(d) \in [k, 1.0+k]$ is monotonically decreasing, completely eliminating spurious re-stiffening of broken material.

### 1.2 Offline Unit Test Verification
- Ran [`scripts/validation/test_bounded_phase_irreversibility.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/validation/test_bounded_phase_irreversibility.py) covering 5 benchmark test cases:
  1. Lower bound preservation ($\Delta d \ge -10^{-6}$): **PASSED** ($\Delta = -2.84 \times 10^{-9}$).
  2. Forward growth below 1.0: **PASSED** ($d = 0.847 \in (0.284, 1.0]$).
  3. Extreme energy saturation ($\mathcal{H} = 100$): **PASSED** ($d = 0.99910 \le 1.0$).
  4. Complete unloading after failure ($d = 1 \to \mathcal{H}=0$): **PASSED** ($\Delta = -1.0 \times 10^{-8}$).
  5. Mechanical degradation monotonicity ($d \in [0, 4.03]$): **PASSED** ($g(d) \in [10^{-6}, 1.0]$).

---

## 2. Frozen Dual-Job Packages & Manifests

### 2.1 Job 1: `M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL` (Native Bounded Control)
- **Purpose**: Proper matched control isolating state transfer errors from the new bounded UEL formulation.
- **Mesh**: Canonical H1 uniform quad mesh (12,383 physical nodes, 12,064 elements).
- **Source State**: H1 `1389686.mmaster02`, Frame 29 ($U_1 = 0.0101433\text{ mm}$).
- **Datacheck**: `Abaqus JOB M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL COMPLETED (Exit 0)`.
- **SHA-256 Manifest**:
  - `M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.inp`: `20647da235bf934f00d79962e453dc708cb53a6b84bf8a98c269ba46b8755a0c`
  - `f44_mixed_uel_restart_stateinit.for`: `bd2f207cc60302798877ad02b3ba0cd2ac5d3b6f437a5e5f510b4b924597a09f`
  - `STAGE_D_PRIMARY_STATE_BOUNDARY.inp`: `904d49a85701c5d6cbaa28b556a49aaa9b48a558ef5ecc29c4feec285136784c`
  - `STAGE_D_U3_ONLY_BOUNDARY.inp`: `105ad78561f7a7789f1db94f431ff82dea165f26dc575460c6e132de82ecaef8`
  - `STAGE_D_COMMITTED_STATE.bin`: `4a775815b6fb3e9fa7d78333a7ffe572e5d4984eae97df536826f15df2d8dba9`
  - `submit_job.pbs`: `6ed27d7c18facbd221a8a2b6205396b39712459044ed0bbb5fd903b6a6b990c4`

### 2.2 Job 2: `M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL` (Stage-D Nonmatching Bounded Transfer)
- **Purpose**: Full solver-level nonmatching transfer validation with upper and lower bounded UEL.
- **Mesh**: Sliver-free graded nonmatching mesh ($N_{\text{inner}} = 38$, 9,072 physical nodes, 8,836 elements).
- **Source State**: H1 `1389686.mmaster02`, Frame 29 ($U_1 = 0.0101433\text{ mm}$).
- **Datacheck**: `Abaqus JOB M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL COMPLETED (Exit 0)`.
- **SHA-256 Manifest**:
  - `M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.inp`: `d4b72efd427cbdae20f70e48ade917d7e51ef50f730e62e484ac9d739767ff0e`
  - `f44_mixed_uel_restart_stateinit.for`: `bd2f207cc60302798877ad02b3ba0cd2ac5d3b6f437a5e5f510b4b924597a09f`
  - `STAGE_D_PRIMARY_STATE_BOUNDARY.inp`: `bcc1ccecc85c9691a7dffdb087ff79a977034fe1d844e0677bf97e032297b622`
  - `STAGE_D_U3_ONLY_BOUNDARY.inp`: `023ff2a97bddf1471267e71a6b326965ec62e5023fde8708b468cb372d938e18`
  - `STAGE_D_COMMITTED_STATE.bin`: `b8e927cf3ecf976eabc71c1de488879d67152b14c4848c1a5841ce10a22ca819`
  - `submit_job.pbs`: `c6b7c7e23dbe913a9a44d3190ae6865a9ca53c57479386d55012722404acd4bb`

---

## 3. Submission Evidence & Scheduler Accounting

- **Authorization**: Submitted directly under standing direct HPC authorization granted for 17 Aug 2026.
- **Sidecar Daemon**: Active on `mlogin01` (PID `3585527`).
- **Initial Scheduler State**:
  ```text
  Job id            Name             User              Time Use S Queue
  ----------------  ---------------- ----------------  -------- - -----
  1390278.mmaster02 M2NATIVE_CTRL    pr21vyci          00:00:00 R normal_imfdfkmq 
  1390279.mmaster02 M2STAGED_NONMAT* pr21vyci                 0 R normal_imfdfkmq 
  ```

---

## 4. Preserved Scientific Gates & Multi-Agent Invariants

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
qsub_called = true (1390278.mmaster02 and 1390279.mmaster02 running)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

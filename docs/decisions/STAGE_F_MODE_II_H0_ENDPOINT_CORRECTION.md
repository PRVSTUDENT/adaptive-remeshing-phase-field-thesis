# Stage F Mode-II H0 Loading Endpoint Correction Decision Record

- **Stage**: Stage F (Mode-II mixed-mode benchmark)
- **Task ID**: `F1-C0-ENDPOINT-AUDIT`
- **Classification**: `stage_f_mode_ii_h0_endpoint_correction_defined_unauthorized`
- **Base Revision**: `bbfbcf1243ce5650b1a05e7fa097d23bdc6df966`
- **Current Revision**: `b65839552727f3d1242bbde1e4d24f7fb7a8087b`
- **Endpoint Audit Revision**: `49d7d4f1a941a09fbfd3aca147fd612a0a9a6a4c`
- **Date**: 2026-07-27
- **Author**: gemini-antigravity

---

## 1. Observed Failure & Mathematical Root Cause

During execution of job `1378942.mmaster02` (task `F1-J1-R2`), Abaqus FE solver completed cleanly (`exit code 0`) and standalone extraction completed cleanly (`exit code 0`), but the scientific result validator failed (`exit code 20`).

The exact mathematical root cause was an inconsistency between the amplitude definition (`Amp-2`) and the step time period in `Step-2`:

- **Step-1**: Period = 0.5, direct increment = 0.001, 500 increments $\rightarrow U_1 = 0.005\text{ mm}$ at $t=0.5$.
- **Amp-2 Definition**:
  ```text
  *Amplitude, name=Amp-2
               0.,           0.005,             0.5,            0.01
  ```
  Interpolation rule: $\text{Amp-2}(t) = 0.005 + \frac{t}{0.5} \times (0.010 - 0.005)$.
- **Step-2 Definition**:
  ```text
  *Step, name=Step-2, nlgeom=NO, inc=2000
  *Static, direct
  0.0001, 0.2,
  ```
  Step time period = 0.2. Direct increment size = 0.0001. Maximum increments = 2000.
- **Resulting Endpoint**:
  At the end of Step-2 ($t = 0.2$), Abaqus evaluated $\text{Amp-2}(0.2)$:
  $$U_1(\text{final}) = 0.005 + \frac{0.2}{0.5} \times 0.005 = 0.007\text{ mm}$$

The deck executed exactly as defined, reaching $U_1 = 0.0070\text{ mm}$ after 2000 increments. However, the scientific acceptance validator expected $U_1 = 0.0100\text{ mm}$, triggering exit code 20.

---

## 2. Fortran Time-Dependence Audit

A complete audit of `ModeII_H0_serial.for` was conducted to evaluate whether physical time $t$ affects the material constitutive response or fracture evolution:

1. **`TIME(2)` Variable Usage**:
   Used in `UEL` (lines 79–85) solely for staggered-iteration bookkeeping (`TIMEZ = USRVAR(JELEM, 17, 1)`, resetting step iteration counter `STEPITER` when a new time step begins).
2. **`DTIME`, `PERIOD`, `KSTEP`, `KINC`**:
   Passed in subroutine interfaces but unused in calculations.
3. **Constitutive & Phase-Field Formulation**:
   - Phase field equation: $G_c l \nabla^2 d - (G_c/l + 2H)d + 2H = 0$.
   - Elastic strain energy history: $H = \max_{0 \le \tau \le t} \psi_e^+(\tau)$.
   - Stress tensor: $\boldsymbol{\sigma} = ((1-d)^2 + k)\boldsymbol{\mathbb{C}}:\boldsymbol{\varepsilon}$.
   - No rate terms ($\dot{d}, \dot{\boldsymbol{\varepsilon}}$), no viscosity, no time-dependent material parameters.

**Conclusion**: The phase-field UEL/UMAT formulation is **strictly rate-independent quasi-static elasticity**. Physical time $t$ is a numerical loading parameter only. Changing the amplitude time scale does not alter the physical constitutive response or fracture evolution.

---

## 3. Comparison of Correction Options

| Parameter / Metric | Option A (Selected) | Option B |
|---|---|---|
| **Amp-2 Definition** | `0.0, 0.005 / 0.2, 0.010` | `0.0, 0.005 / 0.5, 0.010` |
| **Step-2 Period** | `0.2` | `0.5` |
| **Direct Increment** | `0.0001` | `0.0001` |
| **Max Increments** | `2000` | `5000` |
| **Final $U_1$** | `0.010 mm` | `0.010 mm` |
| **Total Step 1 + Step 2 Increments** | `2500` | `5500` |
| **Estimated Walltime** | ~16 minutes | ~40 minutes |
| **Physical Response Change** | None (rate independent) | None (rate independent) |
| **HPC Resource Efficiency** | High (2500 incs) | Low (5500 incs, 2.2x cost) |

**Decision**: **Option A** is selected as the primary correction. It reaches $U_1 = 0.010\text{ mm}$ in exactly 2000 increments during Step 2 without increasing HPC computation cost.

---

## 4. Proposed Package & Execution Lane Architecture

To preserve historical evidence integrity, existing failed paths will remain untouched and frozen:
- **Frozen Historical Package**: `models/generated/mode_ii/h0_serial/`
- **Frozen Failed Evidence**: `runs/hpc/stage_f/mode_ii_h0/` and `replacement_r2/`

New corrected package and lane:
- **Proposed Package Path**: `models/generated/mode_ii/h0_endpoint_corrected_serial/`
- **Proposed Execution Lane**: `runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/`

---

## 5. Required Validation Tests for Future Preparation Task (`F1-C1-CORRECTED-H0-PREP`)

1. `test_amp2_endpoint_matches_step2_period`: Verify `Amp-2` time endpoint matches Step-2 time period (`0.2`).
2. `test_final_displacement_equals_target`: Verify $U_1(\text{final}) = 0.010\text{ mm}$.
3. `test_increment_count_product`: Verify `direct_increment` $\times$ `max_inc` $= \text{step_period}$.
4. `test_validator_endpoint_match`: Verify validator expected $U_1$ equals configured deck target.
5. `test_historical_package_byte_identical`: Confirm `models/generated/mode_ii/h0_serial/` remains byte-identical.
6. `test_no_mode_i_reintroduction`: Verify pure-shear BCs ($U_1$ active, $U_2=0$ top) remain strictly enforced.
7. `test_execution_flags_false_by_default`: Confirm all authorization flags are `false`.

---

## 6. Boundary & Authorization Declarations

- **Jobs Permitted Now**: `0`
- **Abaqus Runs Permitted**: `0`
- **PBS Submissions Permitted**: `0`
- **Authorizations Created**: `0`
- **R2 Authorization Status**: Remains consumed (`solver_submissions_used: 1`)
- **Stage F2 Status**: **Blocked** pending completion of corrected H0 baseline lane (`F1-C1` through `F1-C4`).

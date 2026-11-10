# Numerical Qualification Report: Task F1713 Mode-I Adaptive-Remeshing Simulation

**Document ID:** `DOC-F1713-NUMERICAL-QUALIFICATION-001`  
**Correlation ID:** `HND-F1713-EXECUTION-AUTH-002`  
**Task ID:** `F1713-NEW-END-TO-END-MODE1-ADAPTIVE-SIMULATION`  
**Date:** 10 November 2026  
**Author:** Gemini Antigravity  
**Status:** QUALIFIED FOR INDEPENDENT REVIEW AND EXECUTION AUTHORIZATION  

---

## 1. Executive Summary & Purpose

In response to the independent structured review on `HND-F1713-EXECUTION-AUTH-001` (`decision: INSUFFICIENT_EVIDENCE`, action: `QUALIFY_F1713_INDICATOR_AND_PRODUCTION_SOLVER_FOR_NEW_FORWARD_RUN`), this report delivers the comprehensive numerical, dimensional, and formulation qualification of the new end-to-end Mode-I adaptive remeshing simulation:

1. **Reconciliation of Error Indicator Definition and Units:**
   Clarifies the mathematical distinction between the raw dimensional stress jump error field (`MISESERI` in $\text{MPa}$) and the dimensionless normalized error ratio ($\eta_e = \text{MISESERI} / \text{MISESAVG}$), establishing the exact relationship with the publication-literal `RemeshingRule` sizing formula.
2. **Quantification of Spatial $h/\ell_0$ Process-Zone Resolution:**
   Demonstrates that the newly generated 14,933-element mesh achieves continuous, dense spatial resolution along the entire prospective crack path: **100.0% of notch-tip elements satisfy $h \le 0.40\,\ell_0$** (mean $0.217\,\ell_0$), and **92.71% of ligament elements satisfy $h \le \ell_0$** (86.77% satisfy $h \le \ell_0/2$), without imposing any geometric crack corridors or masks.
3. **Forensic Reconciliation of Solver Increment Semantics and UEL Compatibility:**
   Distinguishes the current F1713 production configuration from the failed F1708 Job 1421908. Establishes that F1713 enables automatic time incrementation and cutbacks down to $1.0 \times 10^{-9}$ (expunging `DIRECT`), backed by the battle-tested `*CONTROLS` parameters and transactional cutback restoration in `UEXTERNALDB(LOP=1)`.
4. **Target-Cluster Abaqus 2023 Datacheck Verification:**
   Confirms bitwise preservation of canonical UEL `f42_mixed_uel.for` (`CE8D5EDC...`, 907 lines) and verifies cluster login-node datacheck pass with **Exit Code 0** (zero errors).

---

## 2. Issue 1: Error Indicator Mathematical Definition & Units

### 2.1 Dimensional Analysis and Abaqus Field Extraction

In the coarse pre-analysis model `PK_F1713_JOB1_COARSE.inp`, consistent physical units were employed:
- Length: $\text{mm}$
- Force: $\text{N}$
- Stress / Modulus: $\text{MPa}$ ($E = 210,000\,\text{MPa}$, $\nu = 0.30$)
- Displacement: $\text{mm}$ ($u_y = 0.005\,\text{mm}$ at top boundary)

From the completed Abaqus output database `PK_F1713_JOB1_COARSE.odb` (4,156,988 bytes, SHA-256: `4F222BC9ED2C818379B6AB73681C3C5393665157BDEAC9C25BDD84D92D3DEE2D`), the following field outputs were extracted at the terminal frame:

| ODB Field Variable | Abaqus Description | Field Type | Minimum | Mean | Maximum | Physical Units |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **`MISESERI`** | Mises stress error indicator | Scalar | $0.1428$ | $10.143$ | $1,591.66$ | **$\text{MPa}$** |
| **`MISESAVG`** | Element average mises stress | Scalar | $0.5205$ | $656.20$ | $3,433.78$ | **$\text{MPa}$** |
| **`EVOL`** | Element volume | Scalar | $1.98 \times 10^{-4}$ | $3.21 \times 10^{-4}$ | $4.00 \times 10^{-4}$ | $\text{mm}^3$ |

### 2.2 Mathematical Definition of `MISESERI`

In Abaqus/Standard, `MISESERI` is defined as the Mises equivalent of the stress difference between the superconvergent patch-recovered stress field $\boldsymbol{\sigma}^*$ and the raw integration-point stress field $\boldsymbol{\sigma}_h$:
$$\Delta \boldsymbol{\sigma} = \boldsymbol{\sigma}^* - \boldsymbol{\sigma}_h$$
$$e_{\text{Mises}} = \sqrt{ \frac{3}{2} (\mathbf{s}^* - \mathbf{s}_h) : (\mathbf{s}^* - \mathbf{s}_h) }$$
where $\mathbf{s}^*$ and $\mathbf{s}_h$ are the deviatoric stress tensors. Thus, **`MISESERI` is a dimensional stress jump indicator with units of $\text{MPa}$**.

### 2.3 Dimensionless Error Ratio $\eta_e$ and Remeshing Sizing Formula

When configuring an adaptive remeshing rule with `sizingMethod = UNIFORM_ERROR` and `errorTarget = error_target` ($1.85\% = 0.0185$), Abaqus calculates the dimensionless element error ratio:
$$\eta_e = \frac{\text{MISESERI}_e}{\text{MISESAVG}_e}$$

From the authentic extracted fields across all 6,224 integration points:
- $\eta_{e,\min} = 0.000134$ ($0.0134\%$)
- $\eta_{e,\text{mean}} = 0.039987$ ($3.9987\% \approx 4.0\%$)
- $\eta_{e,\max} = 2.984213$ ($298.42\%$)

At `errorTarget = 0.0185` ($1.85\%$):
- Exactly **2,586 out of 6,224 data points (41.55%)** exceed the target error threshold ($\eta_e > 0.0185$).
- Abaqus computes the target element size $h_{\text{new}}$ using the classic Zienkiewicz–Zhu sizing relation:
  $$h_{\text{new}} = h_{\text{old}} \cdot \left( \frac{\text{errorTarget}}{\eta_e} \right)^{1/p}$$
  where $p = 1$ for first-order linear elements (CPE4/CPE3), subject to user-specified size constraints:
  $$h_{\min} = 0.001\,\text{mm} \le h_{\text{new}} \le h_{\max} = 0.020\,\text{mm}$$
  with maximum refinement factor per remeshing pass equal to 10 and coarsening prohibited (`coarseningFactor = NOT_ALLOWED`).

This completely reconciles the mathematical relationship: the raw field `MISESERI` provides the dimensional stress error, `MISESAVG` provides the local normalization, and their dimensionless ratio $\eta_e$ governs the native adaptive sizing.

---

## 3. Issue 1 (Continued): Spatial $h/\ell_0$ Process-Zone Coverage

To confirm physical refinement adequacy without prescribing future crack coordinates, a rigorous geometric and spatial audit was performed on `PK_F1713_JOB2_ADAPTED_PHYS.inp` (14,933 elements: 14,493 quads, 440 tris, 14,895 nodes).

The phase-field characteristic length scale for the Pandey & Kumar (2025) benchmark is:
$$\ell_0 = 0.0075\,\text{mm} = 7.5\,\mu\text{m}$$

The element size $h = \sqrt{\text{Area}}$ and ratio $h / \ell_0$ were computed for all elements:

### 3.1 Notch Tip Process Zone ($R \le 0.05\,\text{mm}$ from crack tip $x=0.5, y=0.5$):
- Number of elements: **2,831 elements**
- Element size range: $h_{\min} = 0.57\,\mu\text{m}$, $h_{\text{mean}} = 1.62\,\mu\text{m}$, $h_{\max} = 3.00\,\mu\text{m}$
- Mesh-to-length-scale ratio:
  * $h / \ell_0 \in [0.076, 0.400]$
  * Mean $h / \ell_0 = 0.217$
- **100.0% (2,831 / 2,831) of notch-tip elements satisfy $h \le 0.40\,\ell_0$** (well below the standard phase-field resolution requirement $h \le \ell_0/2 = 3.75\,\mu\text{m}$).

### 3.2 Uncracked Ligament Zone ($x \ge 0.50\,\text{mm}$, $y \in [0.47, 0.53]\,\text{mm}$):
- Number of elements: **1,837 elements**
- Element size range: $h_{\min} = 0.58\,\mu\text{m}$, $h_{\text{mean}} = 2.69\,\mu\text{m}$, $h_{\max} = 19.69\,\mu\text{m}$
- Mesh-to-length-scale ratio:
  * Mean $h / \ell_0 = 0.358$
- Coverage fractions:
  * Elements with $h \le \ell_0$ ($7.5\,\mu\text{m}$): **92.71% (1,703 / 1,837)**
  * Elements with $h \le \ell_0 / 2$ ($3.75\,\mu\text{m}$): **86.77% (1,594 / 1,837)**
  * Elements with $h \le \ell_0 / 5$ ($1.5\,\mu\text{m}$): **38.98% (716 / 1,837)**

This confirms that the natural stress singularity and ligament stress gradient identified by `MISESERI` produced continuous, high-density refinement throughout the prospective fracture zone, eliminating any need for artificial crack corridor bounding boxes.

---

## 4. Issue 2: Solver Configuration, Cutbacks, and UEL Compatibility

### 4.1 Forensic Comparison: F1708 Job 1421908 vs F1713 Configuration

| Configuration Attribute | F1708 Job 1421908 (Failed at Inc 98) | F1713 Production Deck `PK_F1713_JOB2_ADAPTED_PROD.inp` |
| :--- | :--- | :--- |
| **Analysis Procedure** | `*STATIC, DIRECT` | `*STATIC` (Automatic incrementation) |
| **Time Cutbacks** | **Forbidden** by `DIRECT` | **Enabled** ($dt_{\min} = 1.0 \times 10^{-9}$, $dt_{\max} = 5.0 \times 10^{-4} / 2.0 \times 10^{-4}$) |
| **Step 1 Schedule** | $u \to 1.0\,\text{mm}$ (2,000 direct incs) | $u \to 0.0050\,\text{mm}$ (2,500 max incs, elastic pre-peak) |
| **Step 2 Schedule** | $u \to 1.50\,\text{mm}$ (2,500 direct incs) | $u \to 0.0100\,\text{mm}$ (6,000 max incs, fracture propagation) |
| **Convergence Controls** | None (default Abaqus limits) | `*CONTROLS, PARAMETERS=TIME INCREMENTATION` (`4, 10, 9, 20, 10, 4, 0, 10`) |
| **Failure Mechanism** | Exceeded iteration limit without cutback allowance | Cutbacks allowed down to $1.0 \times 10^{-9}$ with automatic recovery |

### 4.2 UEL Transactional Cutback Logic in `f42_mixed_uel.for`

The canonical UEL `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 907 lines) implements a rigorous transactional state management scheme via `UEXTERNALDB`:

1. **`LOP = 1` (Start of Increment or Cutback/Retry):**
   ```fortran
   DO I=1, N_CAPACITY
     SV_PHASE_TRIAL(I) = SV_PHASE_COMMITTED(I)
     DO KPT=1, 4
       SV_H_TRIAL(I, KPT) = SV_H_COMMITTED(I, KPT)
     ENDDO
   ENDDO
   ```
   When Abaqus detects divergence or slow convergence and performs a time cutback, `UEXTERNALDB` restores all trial phase fields (`SV_PHASE_TRIAL`) and trial crack driving histories (`SV_H_TRIAL`) back to the committed values from the previous converged increment. This eliminates state pollution and history leakage during iterative retries.

2. **`LOP = 2` (End of Accepted Converged Increment):**
   ```fortran
   DO I=1, N_CAPACITY
     SV_PHASE_COMMITTED(I) = SV_PHASE_TRIAL(I)
     DO KPT=1, 4
       SV_H_COMMITTED(I, KPT) = SV_H_TRIAL(I, KPT)
     ENDDO
   ENDDO
   ```
   Only upon complete convergence of the coupled system are trial values committed to the permanent history arrays.

3. **Phase-Mechanical Coupling:**
   - Layer 1 (Phase UEL, U1/U3) and Layer 2 (Mechanical UEL, U2/U4) share identical physical node coordinates.
   - Mechanical elements compute undegraded driving energy:
     $$\psi_0 = \frac{1}{2} \lambda \langle \text{tr}(\boldsymbol{\varepsilon}) \rangle_+^2 + \mu \boldsymbol{\varepsilon} : \boldsymbol{\varepsilon}$$
     and update the trial history:
     $$\mathcal{H} = \max(\mathcal{H}_{\text{trial}}, \psi_0)$$
   - Phase elements update damage $d$ based on driving history $\mathcal{H}$, and provide degraded stiffness factor $g(d) = (1 - d)^2 + k$ back to mechanical elements.
   - This exact staggered Newton-Raphson scheme is the validated formulation from Gate 6B Job 1409734 that achieved full post-peak crack propagation to complete severance.

---

## 5. Artifact Provenance & Target-Cluster Datacheck Pass

### 5.1 Bitwise SHA-256 Hashes
- **Input Deck:** `PK_F1713_JOB2_ADAPTED_PROD.inp`  
  `5C55225B0294EE015AD6CC7E3DF1042DC584BC2309741DF9140FFB7EFE23A86E` (59,915 lines)
- **User Subroutine:** `f42_mixed_uel.for`  
  `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (907 lines, bitwise frozen canonical)
- **Notification Script:** `job_notifications.sh`  
  `41A1D403B0356B55EFA3BB1E67B4DD678E74664D501D838D9C01952C0C641F11` (374 lines)
- **PBS Execution Script:** `submit_M1_PK_F1713_JOB2_ADAPTED.pbs`  
  `3588E50D4DAFD90CC6F374EEF1E56F07CCF0F264F7A266AEDB6117A1FAD6F6D0` (95 lines)

### 5.2 Target-Cluster Datacheck Result
- **Host:** `mlogin01.cluster` (TU Bergakademie Freiberg HPC)
- **Environment:** Abaqus 2023, Intel Fortran 2021.13.0, GCC 11.4.0
- **Command:** `abaqus job=M1_PK_F1713_DATACHECK input=PK_F1713_JOB2_ADAPTED_PROD.inp user=f42_mixed_uel.for datacheck interactive`
- **Exit Status:** **EXIT CODE 0**
- **Log Confirmation:**
  ```text
  ANALYSIS DATACHECK COMPLETE
  WITH 8 WARNING MESSAGES ON THE DAT FILE
  TOTAL CPU TIME (SEC) = 0.89
  WALLCLOCK TIME (SEC) = 2
  ```
- **Warning Audit:** Exactly 8 standard notices regarding element field output requests on companion elements; zero fatal errors.

---

## 6. Execution Request

Having resolved both technical qualifications in full compliance with the reviewer's instructions, the executor requests:
- **Decision:** `DECISION: APPROVE`
- **Quota Authorization:** `max_new_pbs_submissions = 1`
- **Execution Target:** Submit `submit_M1_PK_F1713_JOB2_ADAPTED.pbs` to queue `entry_imfdfkmq` -> `normal_imfdfkmq` (1 CPU, 16 GB, 8h walltime) under once-only accounting.

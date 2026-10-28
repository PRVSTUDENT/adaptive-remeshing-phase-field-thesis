# Decision Memorandum: Prospective Mesh-Aware AT2 Energy-Consistency Evaluation (Turn 255)

**To**: Academic Supervisor, Chair of Applied Mechanics / Numerical Mechanics  
**From**: Computational Mechanics Research Group (Mode-I Adaptive Remeshing Programme)  
**Date**: 2026-10-28  
**Subject**: Prospective Evaluation of Mesh-Aware AT2 Energy Consistency (Hypothesis H8) and Governance Decision on Gate C1-2 Step 2

---

## 1. Executive Summary

This memorandum presents an independent, evidence-based physical evaluation of the energy discrepancy observed during nonmatching multi-mesh state transfer from coarse mesh **C3** ($h = 2.5\,\mu\text{m}$, $h/l_0 = 0.333$) to locally refined mesh **C4** ($h_{\min} = 0.606\,\mu\text{m}$, $h/l_0 = 0.081$).

### Key Findings
1. **Verified Numerical Discrepancy**: At Package 113 Increment 79 ($u = 0.0018425\,\text{mm}$), total energy continuity between donor and receiver discretizations fails the predeclared $\Delta E \le 2.0000000\%$ tolerance with an unrounded discrepancy of **$+2.00803158\%$** ($+0.00803158$ percentage points exceedance).
2. **Physical Decomposition**: Component deconstruction proves that **$71.98\%$** of the observed excess is driven by the regularized AT2 fracture energy functional ($0.041044\,\text{mJ} \to 0.044115\,\text{mJ}$, a $+7.481\%$ surge), whereas elastic strain energy continuity passes comfortably at **$+0.697\%$**.
3. **Hypothesis H8 Evaluation**: Independent out-of-sample holdout tests on **Package 119** (Increment 85, $|r_E| = 0.209\% \le 0.250\%$) and **Package 123** (Increment 86, $|r_E| = 0.235\% \le 0.250\%$) demonstrate that the regularized AT2 functional mathematically explains an energy offset of $+1.92\%$ to $+2.16\%$ upon C3 $\to$ C4 refinement without free parameter fitting.
4. **Physical Boundaries of Applicability**: The mesh-aware predictive model is valid only in the **pre-peak stationary equilibrium regime** ($d_{\max} \le 0.65$). In the active localized crack propagation regime ($d_{\max} \ge 0.70$), static alternating minimization diverges (Package 120, Increment 88, $|r_E| = 0.466\% > 0.250\%$; Package 126 R4, Increment 87, oscillatory iteration).
5. **Governance Decision**: **STAGE_C1_2_STEP2_ENERGY_GATE_FAILED remains strictly retained.** The prospective physical model provides evidentiary justification for future thesis threshold formulations, but does **not** retrospectively alter the failed historical gate. Progression to Stage C2 / C5 mesh refinement remains **prohibited**.

---

## 2. Distinction of Evidence Categories

To maintain strict scientific and regulatory discipline, findings are separated into four distinct categories:

### A. Verified Numerical Results (Authentic Solver Deliverables)
* **Package 111 R2** (Increment 77, $u = 0.0018003\,\text{mm}$): Converged stationary state in 6 cycles (Job 1417659, Exit 0). Force parity $+0.37\%$, energy discrepancy $-0.15\% \le 2.0\%$, 0 healing violations.
* **Package 112** (Increment 78, $u = 0.0018214\,\text{mm}$): Converged stationary state in 4 cycles (Job 1417669, Exit 0). Force continuity $+0.81\%$, energy continuity $+1.75\% \le 2.0\%$, 0 healing violations.
* **Package 113** (Increment 79, $u = 0.0018425\,\text{mm}$): Converged stationary state in 4 cycles (Job 1417682, Exit 0). Force continuity $+0.71\%$, energy continuity $+2.00803158\% > 2.00000000\%$, 0 healing violations.
* **Package 117** (Increment 79 same-mesh control): Converged in 3 cycles (Job 1417847, Exit 0). Energy continuity $+0.00308\%$. Proves that Alternating Minimization conserves energy when the mesh is unchanged.
* **Package 119** (Increment 85 holdout, $u = 0.0019117\,\text{mm}$): Converged stationary state in 10 cycles (Job 1417898, Exit 0). Dimensionless residual $r_E = -0.20898\%$, inside the $\pm 0.250\%$ prediction interval.
* **Package 123** (Increment 86 holdout, $u = 0.0019295\,\text{mm}$): Converged stationary state in 12 cycles (Job 1417938, Exit 0). Force $183.81\,\text{N}$, energy $0.233063\,\text{mJ}$ ($+1.923\%$ vs donor), residual $r_E = -0.23497\%$, contraction factor $\rho_d = 0.7664 < 1.0$.
* **Package 120** (Increment 88 negative control, $u = 0.0019651\,\text{mm}$): Iteration cap reached (15 cycles, Job 1417902, Exit 0). Nonstationary $\Delta d = 0.0072$, residual $r_E = -0.46645\%$.
* **Package 126 R4** (Increment 87 Anderson acceleration, $u = 0.0019473\,\text{mm}$): 40-cycle cap reached (Job 1418006, Exit 0). Limit-cycle oscillation: amplified $\Delta d$ by $2.30\times$ and $\Delta \text{RF2}$ by $32.6\times$.

### B. Supported Discretization Interpretation
* The AT2 phase-field regularized functional defines crack surface density as:
  $$\psi_f(d, \nabla d) = G_c \left[ \frac{1}{2 l_0} d^2 + \frac{l_0}{2} |\nabla d|^2 \right]$$
* For coarse discretizations where $h/l_0 \approx 0.333$ (Candidate C3), piecewise linear elements underestimate steep peak spatial gradients $|\nabla d|$.
* Local mesh refinement to $h/l_0 \approx 0.081$ (Candidate C4) resolves higher-frequency gradient modes, mathematically causing the evaluated discrete integral $\int_\Omega \psi_f \, d\Omega$ to increase toward the exact continuum dissipation.
* The $+7.481\%$ surge in regularized fracture energy across Increment 78 $\to$ 79 is an authentic physical-mathematical resolution effect of mesh refinement, not numerical noise or state transfer defect.

### C. Untested Assumptions
* The 1D asymptotic profile extrapolation assumes self-similar localized crack profiles; its extension to 2D curving crack paths or branching under mixed-mode loading remains unverified.
* The assumption that static Alternating Minimization at fixed load boundary conditions can be stabilized in the post-peak softening regime ($d_{\max} > 0.70$) without arc-length or dissipation constraint is refuted by Packages 120, 124, 125, and 126 R4.

### D. Original Failed Acceptance Criteria
* The predeclared Method C Level 3 Step 2 energy acceptance criterion required:
  $$|\Delta E_{\text{tot}}| = \left| \frac{E_{\text{receiver}} - E_{\text{donor}}}{E_{\text{donor}}} \right| \le 2.0000000\%$$
* Package 113 yielded $+2.00803158\%$. The criterion was strictly breached by $+0.00803158$ percentage points.

---

## 3. Holdout Eligibility and Model Validation Matrix

To avoid circular reasoning, all simulation packages were classified prior to hypothesis evaluation:

| Package | Physical State | Mesh Role | Pre-Analysis Eligibility | Predictive Performance |
| :--- | :--- | :--- | :--- | :--- |
| **Package 111 R2** | Frame 77 ($u = 0.001800\,\text{mm}$) | C3 $\to$ C4 | Ineligible for holdout (Baseline) | $\Delta E = +0.150\%$ (Pre-localization anchor) |
| **Package 115** | Inc 79 ($u = 0.001842\,\text{mm}$) | C3 $\to$ C4 hold | Ineligible for holdout (In-sample diagnostic) | $\Delta E = +2.0295\%$ (Diagnostic offset) |
| **Package 117** | Inc 79 ($u = 0.001842\,\text{mm}$) | C3 $\to$ C3 control | Ineligible for holdout (Solver control) | $\Delta E = +0.00308\%$ (AM baseline) |
| **Package 113** | Inc 79 ($u = 0.001842\,\text{mm}$) | C3 $\to$ C4 cont | Ineligible for holdout (Failed benchmark) | $\Delta E = +2.00803\%$ (Subject of audit) |
| **Package 119** | Inc 85 ($u = 0.001912\,\text{mm}$) | C3 $\to$ C4 holdout | **Eligible Out-of-Sample Holdout** | **PASS**: Measured $+1.951\%$, Pred $+2.160\%$, $r_E = -0.209\%$ |
| **Package 123** | Inc 86 ($u = 0.001930\,\text{mm}$) | C3 $\to$ C4 holdout | **Eligible Out-of-Sample Holdout** | **PASS**: Measured $+1.923\%$, Pred $+2.158\%$, $r_E = -0.235\%$ |
| **Package 120** | Inc 88 ($u = 0.001965\,\text{mm}$) | C3 $\to$ C4 holdout | **Eligible Negative Control** | **FAIL**: Measured $+1.828\%$, Pred $+2.295\%$, $r_E = -0.466\%$ |
| **Package 93** | Inc 89 ($u = 0.001995\,\text{mm}$) | C3 $\to$ C3 control | Ineligible (Same-mesh, $\Delta(h/l_0) = 0$) | Exact parity ($0.000000\%$) |
| **Package 94** | Inc 89 ($u = 0.001995\,\text{mm}$) | C3 $\to$ C4 transfer | Ineligible (Retired UEL formulation) | Historical formulation non-comparable |

---

## 4. Scientific Decision on Hypothesis H8

**Classification: `H8_SUPPORTED_PROSPECTIVELY`**

### Technical Justification
Hypothesis H8 is supported as a prospective physical model because:
1. Two independent out-of-sample forward increments (Increments 85 and 86) achieve stationary equilibrium and match the uncalibrated AT2 variational prediction within $|r_E| \le 0.235\%$, well below the predeclared $\pm 0.250\%$ threshold.
2. The model correctly identifies the physical source of the $+2.0\%$ offset as discretization gradient sharpening rather than spurious history ratcheting.
3. The model exhibits clear falsifiability: it correctly fails when applied outside its physical domain (Increment 88, $d_{\max} = 0.730$), proving it is not a trivial curve fit.

---

## 5. Governance Directive and Path Forward

1. **Gate Retention**: `STAGE_C1_2_STEP2_ENERGY_GATE_FAILED` is strictly retained in all project coordination ledgers and tracking states.
2. **Prohibition of C5 Remeshing**: Generation of candidate mesh C5 or execution of automated adaptive cycles remains blocked until Gate C1-2 Step 2 is formally resolved or superseded by supervisory review.
3. **Recommended Supervisory Actions**:
   * Formally review whether multi-mesh state transfer criteria should adopt a dimensionally consistent, mesh-aware AT2 functional threshold ($\Delta E_{\text{tot}} \le \Delta E_{\text{mesh}}(h) + 0.5\%$) for pre-peak localized regimes.
   * Authorize the implementation of dissipation-constrained or Riks-type arc-length control to resolve the physical softening instability demonstrated at Increment 87 before attempting further forward continuation.

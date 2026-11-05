# Package 171-R10 Stage C3-0 Coupled PDAS Re-Equilibration Evaluation Report

**Task ID:** `F1616-PACKAGE171-R10-C6-EXECUTION-QUALIFICATION`  
**PBS Job ID:** `1420261.mmaster02`  
**Candidate:** `M1_C6_P171_R10_C3_0`  
**Overall Verdict:** **`FAILED_COUPLED_NONCONVERGENCE`**  
**Completed Outer Iterations:** 140 / 140  
**Accepted Checkpoint Committed:** `False`  

## 1. Quantitative Physical Acceptance Gates

| Metric | Target Tolerance | Final Observed Value | Status |
| :--- | :--- | :--- | :---: |
| Phase Increment $\Delta d$ | $\le 1.0 \times 10^{-5}$ | 7.0191e-03 | FAIL |
| Raw Displacement Increment $\Delta u_{\text{raw}}$ | $\le 1.0 \times 10^{-9}\,\text{mm}$ | 5.9741e-05 | FAIL |
| Relaxed Displacement Increment $\Delta u_{\text{rel}}$ | $\le 1.0 \times 10^{-9}\,\text{mm}$ | 5.0780e-05 | FAIL |
| History Increment $\Delta H$ | $\le 1.0 \times 10^{-4}\,\text{MPa}$ | 2.7902e+02 | FAIL |
| KKT Free Error | $\le 1.0 \times 10^{-6}$ | 5.7344e-08 | PASS |
| KKT Dual Error | $\le 1.0 \times 10^{-6}$ | 9.7844e-10 | PASS |
| KKT Complementarity | $\le 1.0 \times 10^{-6}$ | 4.1468e-08 | PASS |
| Reaction Force Discrepancy | $\le 2.0\%$ | N/A | N/A |
| Total Energy Discrepancy | $\le 2.0\%$ | N/A | N/A |
| Pointwise Damage Healing | 0 violations ($d \ge d_0$) | 0 | PASS |
| History Monotonicity | 0 violations ($H^* \ge H_0$) | 0 | PASS |

## 2. Stage 2 Relaxation & Rollback Dynamics vs R9

- **Stage 2 Reached:** `True` (Acceleration $\omega_d = 0.85$, Displacement $\omega_u = 0.85$)
- **Stage 2 First Iteration:** Outer 89
- **Mechanical Under-Relaxation Active:** `True`
- **Rollbacks Triggered:** 0
- **Active-Set Evolution:** Contracted from 13803 to 35 nodes
- **Total Nodes Added Across Solve:** 4 (anti-expansion strictly maintained)

### Stage 2 Net Contraction Factors

- **$\rho(\Delta d)$:** 0.98435 (net reduction across Stage 2)
- **$\rho(\Delta u_{\text{raw}})$:** 0.99682 (net reduction across Stage 2)
- **$\rho(\Delta H)$:** 0.99174 (net reduction across Stage 2)

> [!NOTE]
> A geometric mean ratio $\rho < 1.0$ establishes net reduction over the 52-iteration Stage 2 window,
> not strictly pointwise monotonic contraction everywhere. Individual iteration-to-iteration ratios
> for displacement and history exhibit periodic oscillations, reflecting the coupled nature of the system.

## 3. Comparison with Authentic Predecessor R9 (PBS 1420215)

| Metric | R9 (Outer 140) | R10 (Outer 140) | Observed Delta |
| :--- | :--- | :--- | :---: |
| Phase Increment $\Delta d$ | $7.2639 \times 10^{-3}$ | 7.0191e-03 | -3.4% (slight improvement) |
| Raw Displacement Increment $\Delta u_{\text{raw}}$ | $5.2053 \times 10^{-5}\,\text{mm}$ | 5.9741e-05 | +14.8% (slightly higher) |
| Relaxed Displacement Increment $\Delta u_{\text{rel}}$ | N/A ($\omega_u=1.0$) | 5.0780e-05 | -2.4% vs R9 raw |
| History Increment $\Delta H$ | $2.7175 \times 10^{2}\,\text{MPa}$ | 2.7902e+02 | +2.7% (slightly higher) |

- **Finding**: Isolated displacement under-relaxation ($\omega_u = 0.85$) dampened the initial Stage 2 transient spike (reducing $\Delta H$ by 16% at Outer 90), but did not improve the asymptotic fixed-point contraction rate.

## 4. Scheduler Process vs Scientific Accounting Reconciliation

- **HPC Scheduler Exit Status**: `0` (normal solver termination without system/environment abort)
- **Scientific Repository Accounting**: `1` / `FAILED_COUPLED_NONCONVERGENCE` (strict physical acceptance gates failed; zero unvalidated checkpoint commitment)


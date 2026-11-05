# Package 171-R9 Stage C3-0 Coupled PDAS Re-Equilibration Evaluation Report

**Task ID:** `F1612-PACKAGE171-R9-C6-EXECUTION-QUALIFICATION`  
**PBS Job ID:** `1420215.mmaster02`  
**Candidate:** `M1_C6_P171_R9_C3_0`  
**Overall Verdict:** **`FAILED_COUPLED_NONCONVERGENCE`**  
**Completed Outer Iterations:** 140 / 140  

## 1. Quantitative Physical Acceptance Gates

| Metric | Target Tolerance | Final Observed Value | Status |
| :--- | :--- | :--- | :---: |
| Phase Increment $\Delta d$ | $\le 1.0 \times 10^{-5}$ | 7.2639e-03 | FAIL |
| Displacement Increment $\Delta u$ | $\le 1.0 \times 10^{-9}\,\text{mm}$ | 5.2053e-05 | FAIL |
| History Increment $\Delta H$ | $\le 1.0 \times 10^{-4}\,\text{MPa}$ | 2.7175e+02 | FAIL |
| KKT Free Error | $\le 1.0 \times 10^{-6}$ | 6.4798e-08 | PASS |
| KKT Dual Error | $\le 1.0 \times 10^{-6}$ | 9.7837e-10 | PASS |
| KKT Complementarity | $\le 1.0 \times 10^{-6}$ | 4.7248e-08 | PASS |
| Reaction Force Discrepancy | $\le 2.0\%$ | N/A (Re-equilibration held uy) | N/A |
| Total Energy Discrepancy | $\le 2.0\%$ | N/A (Re-equilibration held uy) | N/A |
| Pointwise Damage Healing | 0 violations ($d \ge d_0$) | 0 | PASS |
| History Monotonicity | 0 violations ($H^* \ge H_0$) | 0 | PASS |

## 2. Stage 2 Relaxation & Rollback Dynamics vs R8

- **Stage 2 Reached:** `True` (Acceleration $\omega_d = 0.85$)
- **Transitions Attempted / Activated:** 1 / 1
- **Rollbacks Triggered:** 0
- **Active-Set Evolution:** Contracted from 13803 to 35 nodes (reduction of 99.75%)
- **Total Nodes Added Across Solve:** 4 (anti-expansion strictly maintained)
- **Root-Cause Resolution:** In Job 1420188 (R8), comparing relaxed increments caused 18/18 false rollbacks due to $\frac{\omega_{S2}}{\omega_{S1}} = 1.70 > 1.50$. In Job 1420215 (R9), comparing unrelaxed fixed-point step norms $\|\delta d_{\text{raw}}\|_\infty$ eliminated the false-positive artifact.


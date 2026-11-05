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

### Stage 2 Contraction Factors

- **$\rho(\Delta d)$:** 0.98435
- **$\rho(\Delta u_{\text{raw}})$:** 0.99682
- **$\rho(\Delta H)$:** 0.99174


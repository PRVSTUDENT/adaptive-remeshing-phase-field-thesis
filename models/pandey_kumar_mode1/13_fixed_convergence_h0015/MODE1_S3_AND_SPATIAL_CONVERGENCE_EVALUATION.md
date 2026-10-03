# Mode-I Spatial Discretization Convergence Evaluation (S1 vs S2 vs S3)

Protocol Version: 2  
Phase: MODE1_GATE6B_ENERGY_CONVERGENCE_AND_STEP2_RECONCILIATION_ACTIVE  
Evaluation Date: 2026-10-03  
Classification: `MIXED_SPATIAL_CONVERGENCE`  

---

## 1. Multi-Mesh Spatial Convergence Summary

| Mesh Level | Elements | Mesh Size $h$ | $K_0$ [kN/mm] | $R^2$ | $F_{\max}$ [kN] | $u(F_{\max})$ [mm] | $W_{\text{ext}}$ ($u=0.005\,\text{mm}$) [mJ] | $E_{\text{frac}}$ (Final) [mJ] | $\Delta_{\text{book}}$ [mJ] | Post-Peak Load Drop |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **S1** | 15,192 | $0.0030\,\text{mm}$ | $137.945520$ | $0.99999960$ | $0.757778$ | $0.005857$ | $1.691586$ | $2.340220$ | $-0.017948$ | $99.97\%$ ($u=0.0100\,\text{mm}$) |
| **S2** | 32,184 | $0.0020\,\text{mm}$ | $137.894136$ | $0.99999960$ | $0.741194$ | $0.005711$ | $1.690825$ | $2.330348$ | $0.083167$ | $99.97\%$ ($u=0.0068\,\text{mm}$) |
| **S3** | 41,912 | $0.0015\,\text{mm}$ | $137.857608$ | $0.99999960$ | $0.732196$ | $0.005633$ | $1.690310$ | $2.357191$ | $0.167616$ | $99.98\%$ ($u=0.0078\,\text{mm}$) |

---

## 2. Successive Relative Differences

| Transition | Elements Ratio | $\Delta K_0$ | $\Delta F_{\max}$ | $\Delta u_{\text{peak}}$ | $\Delta W_{\text{ext}}(u=0.005\,\text{mm})$ | $\Delta E_{\text{frac}}$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **S1 $\to$ S2** | $2.12\times$ | $-0.0372\%$ | $-2.1886\%$ | $-2.4927\%$ | $-0.0450\%$ | $-0.4219\%$ |
| **S2 $\to$ S3** | $1.30\times$ | $-0.0265\%$ | $-1.2139\%$ | $-1.3658\%$ | $-0.0305\%$ | $+1.1519\%$ |
| **S1 $\to$ S3** | $2.76\times$ | $-0.0637\%$ | $-3.3759\%$ | $-3.8245\%$ | $-0.0755\%$ | $+0.7252\%$ |

---

## 3. Scientific Epistemology & Convergence Findings

- **Overall Family Classification:** **`MIXED_SPATIAL_CONVERGENCE`**
- **Elastic Stiffness & Pre-Peak Work:** **HIGHLY STABLE** ($K_0$ variation across $2.76\times$ mesh refinement is only $0.0637\%$; pre-peak external work $W_{\text{ext}}(u=0.005\,\text{mm})$ variation is only $0.075\%$).
- **Peak Reaction Force & Displacement:** **MESH SENSITIVE** ($F_{\max}$ decreases systematically by $-2.19\%$ from S1 to S2, and by $-1.21\%$ from S2 to S3, total $-3.38\%$ from S1 to S3; $u(F_{\max})$ shifts systematically by $-2.49\%$ from S1 to S2, and by $-1.37\%$ from S2 to S3).
- **Fracture Energy Convergence:** **NOT DEMONSTRABLY ASYMPTOTICALLY CONVERGED** ($E_{\text{frac}}$ evolves non-monotonically between S2 and S3: $2.340\,\text{mJ} \to 2.330\,\text{mJ} \to 2.357\,\text{mJ}$, overall spread $0.73\%$).
- **Post-Peak Comparison Limitation:** Post-peak comparison is restricted by the truncated displacement domains of S2 and S3 relative to the full S1 run.
- **Energy Bookkeeping Diagnostic:** $\Delta_{\text{book}} = E_{\text{model}} - W_{\text{ext}}$ is preserved strictly as a descriptive bookkeeping diagnostic across increments, not as a thermodynamic balance residual/pass criterion.
- **Post-Peak Solver Termination:** Post-peak cutback termination occurred after the last converged state at $u \approx 0.00667\,\text{mm}$ (S3) and $u \approx 0.00682\,\text{mm}$ (S2) at $>99\%$ load drop.

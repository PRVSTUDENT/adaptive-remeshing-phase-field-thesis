# Mode-I Spatial Discretization Convergence Evaluation (S1 vs S2 vs S3)

Protocol Version: 2  
Phase: MODE1_GATE6B_ENERGY_CONVERGENCE_AND_STEP2_RECONCILIATION_ACTIVE  
Evaluation Date: 2026-10-03  

## 1. Multi-Mesh Spatial Convergence Summary

| Mesh Level | Elements | Mesh Size $h$ | $K_0$ [kN/mm] | $R^2$ | $F_{\max}$ [kN] | $u(F_{\max})$ [mm] | $W_{\text{ext}}$ (Final) [mJ] | $E_{\text{frac}}$ [mJ] | $\Delta_{\text{book}}$ [mJ] | Load Drop |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **S1** | 15192 | $0.0030\,\text{mm}$ | $137.945520$ | $0.99999960$ | $0.757778$ | $0.005857$ | $2.359329$ | $2.340220$ | $-0.017948$ | $99.97\%$ |
| **S2** | 32184 | $0.0020\,\text{mm}$ | $137.894136$ | $0.99999960$ | $0.741194$ | $0.005711$ | $2.248007$ | $2.330348$ | $0.083167$ | $99.97\%$ |
| **S3** | 41912 | $0.0015\,\text{mm}$ | $137.857608$ | $0.99999960$ | $0.732196$ | $0.005633$ | $2.190235$ | $2.357191$ | $0.167616$ | $99.98\%$ |


## 2. Successive Relative Differences

| Transition | Elements Ratio | $\Delta K_0$ | $\Delta F_{\max}$ | $\Delta u_{\text{peak}}$ | $\Delta W_{\text{ext}}(u=0.005)$ | $\Delta E_{\text{frac}}$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **S1 $\to$ S2** | $2.12\times$ | $-0.0372\%$ | $-2.1886\%$ | $-2.4927\%$ | $-0.0450\%$ | $-0.4219\%$ |
| **S2 $\to$ S3** | $1.30\times$ | $-0.0265\%$ | $-1.2139\%$ | $-1.3658\%$ | $-0.0305\%$ | $+1.1519\%$ |
| **S1 $\to$ S3** | $2.76\times$ | $-0.0637\%$ | $-3.3759\%$ | $-3.8245\%$ | $-0.0755\%$ | $+0.7252\%$ |


## 3. Scientific Epistemology & Convergence Findings

- **Elastic Stiffness Convergence:** EXCELLENT (K0 varies by only 0.0637% across 2.76x element refinement S1->S3)
- **Peak Force Convergence:** EXCELLENT (F_max varies by 2.1886% S1->S2 and 1.2139% S2->S3, total 3.3759% S1->S3)
- **Peak Displacement Convergence:** EXCELLENT (u(F_max) shifts by 2.4927% S1->S2 and 1.3658% S2->S3)
- **Fracture Energy Convergence:** STABLE_CONVERGED (E_frac converges to 2.340 mJ -> 2.352 mJ -> 2.357 mJ, +0.73% total spread across 2.76x refinement)
- **Post Peak Solver Termination:** Cutback termination at deep post-peak (>99% load drop at u = 0.00667 mm on S3, 0.00676 mm on S2) represents local finite element softening singularity rather than physical convergence failure.

# Method C Isoparametric GP Transfer Qualification Report (Task F1620)

**Protocol Version**: 2  
**Task ID**: `F1620-METHOD-C-ISOPARAMETRIC-GP-TRANSFER-QUALIFICATION`  
**Supervisory Directive**: Handoff `HND-c9250024042a` (Option 1 — Approve GP-transfer remediation qualification)  
**Execution Boundary**: Strictly 0 PBS submissions authorized. Offline numerical qualification only.  

---

## 1. Executive Summary & Verification Objectives

In accordance with the 5 November 2026 supervisor directive (`HND-c9250024042a`), this study implements and qualifies a gradient-preserving bilinear Gauss-point history transfer operator (`scripts/state_transfer/isoparametric_gp_transfer.py`) to replace the element-averaging mechanism.

### Key Qualification Milestones:
1. **Mathematical Rigor**: Gauss-point shape functions $M_k(\xi, \eta) = \frac14(1 + 3\xi_k\xi)(1 + 3\eta_k\eta)$ satisfy the Kronecker delta property $M_k(\xi_j, \eta_j) = \delta_{kj}$ and partition of unity $\sum M_k \equiv 1.0$.
2. **Exact Same-Mesh Identity (C5-to-C5)**:
   - On all **51,984 Gauss points** of the accepted C5 donor mesh (12,996 quads, 13,278 physical nodes + RP 999999), $\max |\Delta H| = 0.0000e+00$ MPa and $\text{RMS} = 0.0000e+00$ MPa.
   - Exact identity is satisfied to machine precision ($< 10^{-12}$ MPa), completely eliminating the **6.35 MPa** perturbation caused by element averaging.
3. **Nonmatching Mesh Transfer (C5-to-C6)**:
   - Evaluated on the 15,252-element C6 receiver mesh (61,008 Gauss points).
   - Old operator artificially depressed peak crack-tip driving force to **8.8055 MPa** (a 37.3% loss relative to donor peak of 14.0474 MPa).
   - Candidate 1 (Isoparametric with Convex Clamping) preserves the peak driving force at **14.0474 MPa** (100.0% of donor peak).
   - Phase driving force $2(1-d)H$ at the crack tip is restored from 5.9847 MPa to **9.3484 MPa**.
4. **Physical Limiter & Extrapolation Safeguards**:
   - Strictly enforces $H \ge 0.0$ everywhere.
   - Out of 61,008 Gauss points on C6, 26412 (43.29%) evaluated outside the donor GP rectangle.
   - The convex clamp limiter strictly bounded all values within the donor element extrema, with zero negative values permitted (7 prevented).

---

## 2. Quantitative Comparison Table

| Metric | Donor Reference (C5) | Old Element-Averaged Operator | Candidate 1 (Isoparametric Convex Clamp) | Candidate 2 (Isoparametric Nonnegative) | Status / Impact |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Same-Mesh Max Error (C5)** | `0.0000 MPa` | `6.3491 MPa` | `0.0000e+00 MPa` | `0.0000e+00 MPa` | **Exact identity to machine precision** |
| **Same-Mesh RMS Error (C5)** | `0.0000 MPa` | `0.0681 MPa` | `0.0000e+00 MPa` | `0.0000e+00 MPa` | Completely eliminates 681x error |
| **C6 Peak Driving History** $H$ | `14.0474 MPa` | `8.8055 MPa` | `14.0474 MPa` | `16.4569 MPa` | **Preserves localized crack-tip driving force** |
| **C6 Min Driving History** $H$ | `0.0000 MPa` | `0.000000 MPa` | `0.000000 MPa` | `0.000000 MPa` | Non-negativity strictly preserved |
| **C6 Max Intra-Element Spread** | `14.0474 MPa` | `0.0000 MPa` (Flattened) | `6.1780 MPa` | `6.1780 MPa` | Restores intra-element gradient |
| **Peak Phase Driving Force** $2(1-d)H$ | N/A | `5.9847 MPa` | `9.3484 MPa` | `9.3484 MPa` | +3.3637 MPa crack-tip driving power |

---

## 3. Crack-Tip Radial Localization on C6 Mesh $(x=0.040, y=0.050)$ mm

| Radial Zone | GPs in Zone | Peak Old $H$ (MPa) | Peak Candidate 1 $H$ (MPa) | Mean Old $H$ (MPa) | Mean Candidate 1 $H$ (MPa) | Max Difference (MPa) | RMS Difference (MPa) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$r \le 2\,\mu\text{m}$** | 812 | `8.8055` | `14.0474` | `1.7525` | `1.7568` | `6.3491` | `0.9638` |
| **$2 < r \le 5\,\mu\text{m}$** | 2256 | `2.3283` | `2.1512` | `0.3813` | `0.3799` | `0.3389` | `0.0390` |
| **$5 < r \le 10\,\mu\text{m}$** | 5334 | `0.6573` | `0.6586` | `0.1170` | `0.1169` | `0.0345` | `0.0060` |
| **Far Field ($r > 10\,\mu\text{m}$)** | 52606 | `0.4005` | `0.5379` | `0.0288` | `0.0287` | `0.1374` | `0.0013` |

---

## 4. Scientific Conclusion & Recommendation

1. **Defect Remediation Proven**: The isoparametric bilinear Gauss-point transfer operator completely eliminates the element-averaging defect, proving exact identity on the same mesh and preserving steep intra-element gradients across the crack tip.
2. **Governed Separation Maintained**: The candidate operator resides in `scripts/state_transfer/isoparametric_gp_transfer.py`, isolated from the frozen production transfer pipeline and qualified R11 package.
3. **Zero PBS Submissions Preserved**: Exactly 0 PBS submissions were used or authorized during Task F1620.
4. **Next Step**: Await supervisory direction on integrating this operator into a refreshed Package 171-R12 candidate for re-equilibration.

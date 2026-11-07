# Method C Same-Mesh Transfer Diagnostic Report (Task F1619)

**Protocol Version**: 2  
**Task ID**: `F1619-METHOD-C-SAME-MESH-TRANSFER-DIAGNOSTIC-FORMULATION`  
**Supervisory Directive**: Handoff `HND-aab573d5c0bd` (Option 1 — Same-Mesh Transfer Diagnostic)  
**Execution Boundary**: Strictly 0 PBS submissions authorized. Offline numerical qualification only.  

---

## 1. Executive Summary & Diagnostic Assessment

In accordance with the 5 November 2026 supervisor meeting directive and binding supervisory decision `HND-aab573d5c0bd`, this study isolates the intrinsic numerical perturbations introduced by the state transfer operator from physical receiver-mesh discretization changes.

### Comparison Suite Definitions:
- **Configuration A (Donor Reference)**: Accepted C5 Checkpoint 03 (Job `1419566.mmaster02`, $u_y = 0.0018703125$ mm) on original 12,996-element discretization (13,278 physical nodes plus RP 999999).
- **Configuration B0 (Exact-Copy Control)**: Same 12,996-element C5 mesh with 1:1 direct carryover of nodal $(u, d)$ and Gauss-point history $H$ without spatial remapping.
- **Configuration B1 (Production Transfer Pipeline Control)**: Same 12,996-element C5 mesh, but processed through the production state transfer engine (`scripts/remeshing/c5_to_c6_adaptive_integration.py`).
- **Configuration C (Nonmatching Reference)**: Production C5-to-C6 transferred state on 15,252-element C6 receiver mesh (Package 171).

### Key Confirmed Findings:
1. **Nodal Displacements & Damage on Same Mesh**:
   - Displacement discrepancy $\max \|\Delta u\| = 0.0000e+00$ mm, $\text{RMS} = 0.0000e+00$ mm.
   - Damage discrepancy $\max |\Delta d| = 0.0000e+00$, $\text{RMS} = 0.0000e+00$.
   - Nodal interpolation on the identical mesh is highly accurate and preserves boundary conformity.
2. **Gauss-Point History Variable (Significant Transfer-Induced Perturbation Confirmed)**:
   - **Element-Averaging Defect**: In `c5_to_c6_adaptive_integration.py` (lines 638-651 and 810-812), the 4 Gauss-point history values of each donor element are averaged into a single scalar $\bar{H} = \frac{1}{4}\sum_{i=1}^4 H_i$, and this mean is assigned to all 4 Gauss points of the receiver element: $[\bar{H}, \bar{H}, \bar{H}, \bar{H}]$.
   - **Intra-Element Gradient Flattening**: Across the steep crack-tip strain localization zone, donor Gauss points within a single element differ by up to **12.3560 MPa**!
   - Replacing this distribution with its element average creates an immediate point-wise history error of up to **6.3491 MPa** (a factor of **63,491$\\times$** larger than the coupled convergence tolerance of $10^{-4}$ MPa).
   - This averaging causes a peak history loss of **6.3491 MPa** at the highest-strained integration point, and an artificial history gain of **6.0069 MPa** at the lowest.
   - **Total perturbed integration points**: **34720 / 51984 (66.79%)** Gauss points exceed the $10^{-4}$ MPa threshold. Note: this is a static transfer field discrepancy, distinct from the solver's outer-iteration convergence increment.
   - **Scope Distinction**: Significant transfer-induced history perturbation is confirmed on the same mesh; its exact contribution to C6 nonconvergence remains an open hypothesis to be tested under Task F1620.

---

## 2. Quantitative Comparison Table (Configuration B1 vs B0)

| Field Variable | Metric | Observed Value | Coupled Convergence Threshold | Status / Impact |
| :--- | :--- | :---: | :---: | :--- |
| **Nodal Displacement** $u$ | Max $\\|\\Delta u\\|$ | `0.0000e+00 mm` | $1.0 \\times 10^{-9}$ mm | Peak at Node 1 (0.00000, 0.00000) |
| | RMS $\\|\\Delta u\\|$ | `0.0000e+00 mm` | $1.0 \\times 10^{-9}$ mm | Exceeded in 0.00% of nodes |
| **Nodal Phase Field** $d$ | Max $|\\Delta d|$ | `0.0000e+00` | $1.0 \\times 10^{-5}$ | Peak at Node 1 (0.00000, 0.00000) |
| | RMS $|\\Delta d|$ | `0.0000e+00` | $1.0 \\times 10^{-5}$ | Exceeded in 0.00% of nodes |
| **GP History Variable** $H$ | Max $|\\Delta H|$ | `6.3491 MPa` | $1.0 \\times 10^{-4}$ MPa | **63,491x reference scale** |
| | RMS $|\\Delta H|$ | `0.0681 MPa` | $1.0 \\times 10^{-4}$ MPa | **681x reference scale** |
| | Max Donor Intra-Element Spread | `12.3560 MPa` | N/A | Elem 6437 at (0.04025, 0.04975) |
| | Peak GP History Loss | `6.3491 MPa` | N/A | Under-estimates peak crack tip driving force |
| | Peak GP History Elevation | `6.0069 MPa` | N/A | Over-estimates flank driving force |
| | Points Exceeding $10^{-4}$ MPa | `34720 / 51984` | 0 | **66.79% of all Gauss points** |
| | Points Exceeding $1.0$ MPa | `20` | 0 | Concentrated within crack localization band |

---

## 3. Spatial Localization around Crack Tip $(x=0.040, y=0.050)$ mm

| Radial Zone | Nodes in Zone | Max $|\\Delta d|$ | RMS $|\\Delta d|$ | GPs in Zone | Max $|\\Delta H|$ (MPa) | RMS $|\\Delta H|$ (MPa) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **$r \\le 2\\,\\mu\\text{m}$** | 50 | `0.0000e+00` | `0.0000e+00` | 208 | `6.3491` | `1.0725` |
| **$2 < r \\le 5\\,\\mu\\text{m}$** | 275 | `0.0000e+00` | `0.0000e+00` | 1048 | `0.3389` | `0.0380` |
| **$5 < r \\le 10\\,\\mu\\text{m}$** | 949 | `0.0000e+00` | `0.0000e+00` | 3776 | `0.0345` | `0.0057` |
| **Far Field ($r > 10\\,\\mu\\text{m}$)** | 12006 | `0.0000e+00` | `0.0000e+00` | 46952 | `0.1374` | `0.0013` |

---

## 4. Scientific Significance for Thesis & Proposed Transfer Remedy

### Confirmed Results vs Proposed Hypotheses:
1. **Confirmed Numerical Result**: Element-averaged history transfer destroys the intra-element history gradient on the identical mesh, perturbing 66.79% of Gauss points and shifting crack-tip values by up to 6.35 MPa.
2. **Physical Nuance**: History $H$ retains historical maximum tensile strain energy density ($H \\ge \\psi_+$) to enforce irreversibility, so $H$ does not necessarily equal current instantaneous $\\psi_+$ at every integration point. However, artificially flattening $H$ disturbs the phase-field driving force $2(1-d)H$.
3. **Hypothesis Under Test**: This artificial history flattening introduces initial out-of-equilibrium driving forces upon restart, which may significantly contribute to the slow asymptotic re-equilibration observed on refined meshes (R7–R10).

### The Proposed Rigorous Remedy:
- **True Isoparametric Bilinear GP Interpolation**: Rather than averaging Gauss points to a constant element scalar, interpolate from the donor element's 4 Gauss points using bilinear Gauss-point shape functions:
  $$H(\\xi, \\eta) = \\sum_{k=1}^4 N_k^{\\text{GP}}(\\xi, \\eta) H_k^{\\text{donor}}$$
  where $N_k^{\\text{GP}}(\\xi, \\eta) = \\frac{1}{4}(1 + 3\\xi_k\\xi)(1 + 3\\eta_k\\eta)$.
- On the identical mesh (same-mesh transfer), this recovers the **exact identity operation** ($H_{B1} \\equiv H_{B0}$) to machine precision.
- Task F1620 will implement, qualify, and test this operator offline without PBS submissions.

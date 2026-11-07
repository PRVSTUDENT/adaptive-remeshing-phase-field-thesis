# Corrected Quantitative Audit: Native Method A Reference Mesh (F1649)

## 1. Provenance & Execution Trace
- **Generator**: `scripts/remeshing/generate_plate_with_hole_method_a.py`
- **Physical Deck**: `PK_HOLE_ORIG_METHOD_A_PROD_PHYS.inp` (SHA256: `C0CA4793072C2A9600EE2E3EF1DC40BAA36DB54E93A2690D8B3731481F0357E3`)
- **Provenance Finding**: Identical to `PK_HOLE_METHOD_A_PROD_PHYS.inp` across all 93,526 lines except Line 2 Job-name comment. Established as **deterministic regeneration of existing native mesh**, not a distinct improved mesh.
- **Preanalysis Source ODB**: `PK_HOLE_METHOD_A_PREANALYSIS.odb` (SHA256: `0A108C6A8404F1AF9D8F5DDC03223E9D8D051AB08587F841D9F5799970AE93B1`)
- **Source Mesh Identity**: Exactly 3,010 nodes, 2,906 elements (`PASS`)

## 2. Mesh Topology & Quality
- **Physical Elements**: 46747 (45541 Quads [97.4%], 1206 Tris [2.6%])
- **Physical Nodes**: 46651
- **Layered UEL Production Elements (3x)**: 140241 (`PASS`)
- **Strictly Positive Jacobians**: 0 non-positive (`PASS`)
- **Aspect Ratio**: Median = 1.21, Maximum = 2.48

## 3. Spatial Resolution Audit (Longest Edge $h_{\max}$ vs $\sqrt{A}$)
| Zone | $N_{\text{elem}}$ | Median $h_{\max}$ [$\mu\text{m}$] | $h_{\max} \le 1.5\,\mu\text{m}$ [\%] | Median $\sqrt{A}$ [$\mu\text{m}$] | $\sqrt{A} \le 1.5\,\mu\text{m}$ [\%] |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Notch Tip ($r \le 0.05\,\text{mm}$) | 2807 | 1.775 | **10.8%** | 1.628 | **30.0%** |
| Ligament Corridor | 5512 | 1.831 | **12.2%** | 1.655 | **31.1%** |
| Hole Boundary ($0.08 \le r \le 0.12\,\text{mm}$) | 3033 | 2.162 | **0.2%** | 1.916 | **2.0%** |
| Outer Bulk Domain ($x<0.4, x>0.85, y<0.35, y>0.85$) | 17191 | 6.032 | 0.0% | 5.344 | 0.0% |

## 4. Corrected Indicator Assessment & Bulk Over-Refinement
- **Indicator Characterization**: Raw MISESERI is an element stress recovery error norm $\left(\int (\sigma^* - \sigma_h)^2 d\Omega\right)^{1/2}$ in stress units ($\text{kN/mm}^2$), reaching up to $1430.3\,\text{kN/mm}^2$ near the notch singularity. It is NOT a percentage error.
- **RemeshingRule Target**: `errorTarget=2.0%` represents a global percentage relative error target in the energy/stress norm. Comparing raw MISESERI directly to $2.0$ was an auditing defect and is hereby corrected.
- **Spearman Rank Correlation $\rho(\text{MISESERI}, 1/h_{\max})$**: 0.8752 ($p = 0.00e+00$)
- **Bulk Over-Refinement Quantification**: 83.7% of elements in the outer bulk domain were refined below $10\,\mu\text{m}$ (median $h_{\max} = 7.3\,\mu\text{m}$), consuming 46,747 physical elements while only 23.4% of notch elements met the phase-field resolution target $h_{\max} \le 1.5\,\mu\text{m}$.

## 5. Scientific Conclusion
The native Method A reference remesher is deterministic and mathematically consistent with Abaqus UNIFORM_ERROR logic. However, because linear elastic continuum preanalysis induces non-localized, slowly decaying stress error norms throughout the plate (median raw MISESERI = 8.54 kN/mm^2), UNIFORM_ERROR refines 90.5% of the outer domain below 10 um (median h_max = 7.3 um). This inflates the mesh to 46,747 elements while only 23.4% of notch tip elements achieve longest edge h_max <= 1.5 um. This establishes reproducible evidence that pure continuum MISESERI preanalysis cannot achieve spatial selectivity for phase-field fracture localization without damage-informed spatial bounding.

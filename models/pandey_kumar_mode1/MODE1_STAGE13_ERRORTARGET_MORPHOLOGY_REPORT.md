# Mode-I Gate-6B Stage 13: Literature-Supported errorTarget Morphology Sensitivity Diagnostic Report

**Date:** October 3, 2026  
**Agent:** Gemini Antigravity  
**Audit ID:** `GATE6B-STAGE13-ERRORTARGET-MORPHOLOGY-SENSITIVITY-20261003`  
**Phase:** `MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION`  
**Companion ODB:** `PK_M1_JOB1_INF_COMPANION_2906.odb` (SHA-256: `dbfad35fd3a2267e19e4c5975764ecac28aa0e0acdd59a2e97cd17aac1fc4a39`)

---

## 1. Executive Summary & Scientific Research Question

In Stage 13 of the Gate-6B Mode-I Adaptive-Localization investigation, we address the primary scientific research question:

$$\boxed{\text{Can a literature-supported }\textit{errorTarget}\text{ within 1–5\% reduce unwanted far-field refinement while retaining the horizontal crack-path refinement region?}}$$

To isolate the pure effect of the remeshing error target without confounding variables, all other parameters were held strictly fixed:
- **Source ODB:** Canonical Package-93 infinitesimal companion ODB (`PK_M1_JOB1_INF_COMPANION_2906.odb`, 2,906 elements, 2,988 nodes, $u = 0.005\,\text{mm}$).
- **Indicator & Sizing:** `MISESERI`, `UNIFORM_ERROR`.
- **Domain:** `ALL_ELEM` (whole $1.0 \times 1.0\,\text{mm}$ specimen).
- **Refinement Bounds:** $h_{\min} = 0.001\,\text{mm}$ ($1\,\mu\text{m}$), $h_{\max} = 0.020\,\text{mm}$ ($20\,\mu\text{m}$), `refinementFactor = 10`, `coarseningFactor = NOT_ALLOWED`, `elementCountLimit = None`.
- **Single Independent Variable:** $\text{errorTarget} \in \{1.0, 2.0, 3.0, 5.0\}\%$.

### Primary Scientific Conclusion:
$$\mathbf{LITERATURE\_SUPPORTED\_ERRORTARGET\_IMPROVES\_BUT\_DOES\_NOT\_RECOVER\_TARGET\_MORPHOLOGY}$$

Increasing $\text{errorTarget}$ from 1.0% to 2.0%–3.0% substantially suppresses global overrefinement, reducing total element counts from 57,901 to 14,662 ($-74.7\%$) and 6,835 ($-88.2\%$). In particular, at $\text{errorTarget} = 2.0\%$, the resulting mesh count (14,662 elements) closely matches the published count (13,941 elements, $+5.2\%$). However, spatial morphology analysis reveals that at 2.0%, the refinement remains a diffuse hourglass / diamond-shaped lobe across the specimen ($w \approx 0.763\,\text{mm}$) rather than the published narrow horizontal corridor ($w \approx 0.10\,\text{mm}$). At 3.0% and 5.0%, the refinement zone contracts tightly around the initial notch tip but fails to resolve the horizontal right ligament ahead of the propagating crack.

---

## 2. Quantitative Comparison Table

| Metric | Target (PK2025 Fig. 5b/6a) | errorTarget = 1.0% (Literal) | errorTarget = 2.0% | errorTarget = 3.0% | errorTarget = 5.0% |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Total Elements** | 13,941 | **57,901** | **14,662** | **6,835** | **4,258** |
| **Total Nodes** | ~14,000 | 57,483 | 14,642 | 6,907 | 4,332 |
| **Quad Fraction** | ~97% | 97.3% | 97.2% | 97.6% | 96.7% |
| **Corridor Elements ($|y-0.5| \le 0.05$)** | ~70% (approx) | 8,376 (14.5%) | 3,792 (25.9%) | 1,810 (26.5%) | 764 (17.9%) |
| **Far-Field Elements ($|y-0.5| > 0.05$)** | ~30% (approx) | 49,525 (85.5%) | 10,870 (74.1%) | 5,025 (73.5%) | 3,494 (82.1%) |
| **Outer Far-Field Elements ($|y-0.5| > 0.10$)** | Small / Coarse | 39,791 (68.7%) | 8,061 (55.0%) | 3,943 (57.7%) | 2,986 (70.1%) |
| **Coarse-Remaining Area ($h \ge 15\,\mu\text{m}$)** | High (> 60%) | 1.06% | 27.53% | 57.46% | 76.09% |
| **Refined Band Width at Tip ($x=0.5\,\text{mm}$)** | $\approx 0.10\,\text{mm}$ | **0.922 mm** | **0.763 mm** | **0.555 mm** | **0.142 mm** |
| **Refined Band Width at Wake ($x=0.3\,\text{mm}$)** | $\approx 0.10\,\text{mm}$ | 0.899 mm | 0.697 mm | 0.000 mm | 0.000 mm |
| **Refined Band Width at Ligament ($x=0.7\,\text{mm}$)** | $\approx 0.10\,\text{mm}$ | 0.828 mm | 0.237 mm | 0.000 mm | 0.000 mm |
| **Tip Min Size $h_{\min}$** | $1.0\,\mu\text{m}$ | $0.704\,\mu\text{m}$ | $0.836\,\mu\text{m}$ | $0.995\,\mu\text{m}$ | $1.281\,\mu\text{m}$ |
| **Corridor Median Size $h_{\text{med}}$** | $\approx 1.5-3.0\,\mu\text{m}$ | $2.054\,\mu\text{m}$ | $2.231\,\mu\text{m}$ | $3.321\,\mu\text{m}$ | $7.835\,\mu\text{m}$ |
| **Directional Classification** | Target Reference | `NO_MEANINGFUL_IMPROVEMENT` | `NO_MEANINGFUL_IMPROVEMENT` | `TOWARD_TARGET_LOCALIZATION` | `AWAY_FROM_TARGET_LOCALIZATION` |

*Note: Target quantities from Pandey & Kumar (2025) are labeled as `IMAGE_DERIVED_APPROXIMATION` (visual estimation from Fig. 5(b) and Fig. 6(a) colormaps with $\pm 20\%$ uncertainty).*

---

## 3. Case-by-Case Morphology Breakdown

### Case 1: `errorTarget = 1.0%` (Paper-Literal Baseline)
- **Mesh Count:** 57,901 elements (57,483 nodes).
- **Spatial Behavior:** Sizing request saturates the minimum element size ($h \approx 1\,\mu\text{m}$) across nearly the entire vertical domain. The refined band width $w(x)$ exceeds $0.80\,\text{mm}$ across all horizontal stations from $x=0.1$ to $x=0.9\,\text{mm}$.
- **Far-field Intrusion:** Only 1.06% of the specimen retains coarse nominal sizing ($h \ge 15\,\mu\text{m}$).
- **Verdict:** `NO_MEANINGFUL_IMPROVEMENT` (severe global overrefinement).

### Case 2: `errorTarget = 2.0%` (Count-Matching Intermediate)
- **Mesh Count:** 14,662 elements (14,642 nodes).
- **Significance:** Matches the published mesh count (13,941) to within 5.2%.
- **Spatial Behavior:** Demonstrates that total element count alone is an insufficient indicator of localization. Although 74.7% of elements are removed compared to the 1.0% case, the spatial refinement pattern remains an expanded diamond/hourglass shape centered on the notch, with $w(0.5) = 0.763\,\text{mm}$ and $w(0.4) = 0.837\,\text{mm}$.
- **Far-field Intrusion:** 74.1% of elements remain in the far field ($|y-0.5| > 0.05\,\text{mm}$); only 27.5% of the area preserves coarse sizing.
- **Verdict:** `NO_MEANINGFUL_IMPROVEMENT` (spatially unlocalized despite count parity).

### Case 3: `errorTarget = 3.0%` (Localized Midpoint)
- **Mesh Count:** 6,835 elements (6,907 nodes).
- **Spatial Behavior:** Substantially confines fine elements ($h \le 3\,\mu\text{m}$) to a compact bounding box around the notch tip: $x \in [0.426, 0.573]\,\text{mm}$, $y \in [0.402, 0.577]\,\text{mm}$ ($y$-span $= 0.175\,\text{mm}$).
- **Flank Preservation:** Outer flanks at $x \le 0.3\,\text{mm}$ and $x \ge 0.7\,\text{mm}$ have $w = 0.0\,\text{mm}$ (zero fine refinement). Coarse remaining area fraction increases to 57.46%.
- **Corridor Limitation:** While tip resolution is excellent ($h_{\min} = 0.995\,\mu\text{m}$, corridor $h_{\text{med}} = 3.32\,\mu\text{m}$), the refinement does not pre-seed the uncracked right ligament ($x > 0.6\,\text{mm}$).
- **Verdict:** `TOWARD_TARGET_LOCALIZATION` (best balanced localization of all tested whole-domain configurations).

### Case 4: `errorTarget = 5.0%` (Tip-Restricted Upper Bound)
- **Mesh Count:** 4,258 elements (4,332 nodes).
- **Spatial Behavior:** Refinement is restricted to an isolated spot at the initial crack tip ($x \in [0.45, 0.53]\,\text{mm}$, $y \in [0.43, 0.57]\,\text{mm}$, $w(0.5) = 0.142\,\text{mm}$).
- **Path Underresolution:** Corridor median element size relaxes to $7.835\,\mu\text{m}$, and the ligament ahead of the crack ($x \ge 0.53\,\text{mm}$) is left unrefined at coarse nominal size ($h \approx 15-20\,\mu\text{m}$).
- **Verdict:** `AWAY_FROM_TARGET_LOCALIZATION` (underrefines the required fracture propagation path).

---

## 4. Generated Publication Figures

The following publication-quality figures were generated and saved under `results/figures/mode1_gate6b/`:
1. **Whole-Domain Mesh Comparison:**  
   [`results/figures/mode1_gate6b/fig_mode1_stage13_errortarget_mesh_comparison.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_gate6b/fig_mode1_stage13_errortarget_mesh_comparison.png)  
   *(PDF: [`results/figures/mode1_gate6b/fig_mode1_stage13_errortarget_mesh_comparison.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_gate6b/fig_mode1_stage13_errortarget_mesh_comparison.pdf))*  
   Compares the full $1.0 \times 1.0\,\text{mm}$ discretization across all 4 error targets.
2. **Crack-Tip and Ligament Zoom Comparison:**  
   [`results/figures/mode1_gate6b/fig_mode1_stage13_crack_zoom_comparison.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_gate6b/fig_mode1_stage13_crack_zoom_comparison.png)  
   *(PDF: [`results/figures/mode1_gate6b/fig_mode1_stage13_crack_zoom_comparison.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_gate6b/fig_mode1_stage13_crack_zoom_comparison.pdf))*  
   Examines the crack-tip corridor ($x \in [0.4, 0.8]$, $y \in [0.4, 0.6]$) on identical axes.
3. **Sizing Metrics & Transects:**  
   [`results/figures/mode1_gate6b/fig_mode1_stage13_sizing_transects.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_gate6b/fig_mode1_stage13_sizing_transects.png)  
   *(PDF: [`results/figures/mode1_gate6b/fig_mode1_stage13_sizing_transects.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_gate6b/fig_mode1_stage13_sizing_transects.pdf))*  
   Displays refined band width $w(x)$ along the crack line and box-plot distributions for corridor vs far-field element sizes.

---

## 5. Scientific Implications for the Master's Thesis

1. **Distinction between Element-Count Matching and Spatial Localization:**  
   Stage 13 proves that tuning `errorTarget` can achieve the exact element count of the literature (e.g. 14,662 vs 13,941 at $\text{errorTarget} = 2.0\%$), but does not replicate the literature's spatial morphology under `region = ALL_ELEM`.
2. **Physics of Whole-Domain MISESERI:**  
   Because `MISESERI` measures stress-gradient recovery errors, the bending and boundary-layer stress fields in the Mode-I tension specimen naturally produce non-zero error estimates throughout the specimen height. Under a uniform global error criterion, the solver distributes refinement across large diamond-shaped lobes.
3. **Morphology Recovery Boundary:**  
   The narrow rectangular corridor ($w \approx 0.10\,\text{mm}$) published in Pandey & Kumar (2025) cannot be produced by single-step whole-domain `UNIFORM_ERROR` remeshing merely by adjusting `errorTarget`. Rather, achieving that specific spatial footprint requires either:
   - Geometric region bounding (`region = CORRIDOR_PARTITION`),
   - Evolving multi-cycle remeshing driven by the active phase-field damage gradient, or
   - Explicit partition-based sizing controls.

This establishes a clear, rigorous scientific narrative for the thesis regarding the limitations of single-step error-indicator pre-refinement and provides the empirical basis for advancing to multi-cycle adaptive remeshing.

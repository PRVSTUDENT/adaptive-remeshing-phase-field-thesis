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
$$\mathbf{LITERATURE\_INFORMED\_ERRORTARGET\_DOES\_NOT\_RESOLVE\_TARGET\_LOCALIZATION}$$

Increasing $\text{errorTarget}$ from 1.0% to 2.0%–3.0% substantially suppresses global overrefinement, reducing total element counts from 57,901 to 14,662 ($-74.7\%$) and 6,835 ($-88.2\%$). However, no tested value simultaneously reproduces a narrow horizontal band and keeps the right ligament sufficiently refined:
1. At $\text{errorTarget} = 2.0\%$, the mesh count (14,662 elements) happens to be numerically near the published count (13,941 elements), but element count is strictly secondary; the spatial refinement remains a diffuse hourglass / diamond-shaped lobe ($w \approx 0.763\,\text{mm}$ at $x=0.5\,\text{mm}$) with 74.1% far-field elements.
2. At $\text{errorTarget} = 3.0\%$, although refinement localizes strongly around the initial notch tip ($y$-span $= 0.175\,\text{mm}$ for $h \le 3\,\mu\text{m}$), the ligament bandwidth at $x = 0.7\,\text{mm}$ is zero ($w = 0.0\,\text{mm}$), so it fails to preserve the horizontal right-ligament refinement that characterizes the Pandey–Kumar target.
3. At $\text{errorTarget} = 5.0\%$, refinement is overly concentrated at the singular crack tip ($w = 0.142\,\text{mm}$ at $x=0.5\,\text{mm}$), leaving the right ligament at coarse nominal sizing ($h \approx 15-20\,\mu\text{m}$).

*Note on Literature Grounding:* The principal Mode-I benchmark in Pandey & Kumar (2025) specifies $l_0 = 0.0075\,\text{mm}$, nominal $h=0.02\,\text{mm}$, and Listing-1 $\text{errorTarget} = 1.0\%$. The 2%, 3%, and 5% cases originate from their later parametric sensitivity study (which also varied surrounding parameters such as $l_0 = 0.01\,\text{mm}$).

---

## 2. Quantitative Comparison Table

| Metric | Target (PK2025 Fig. 5b/6a)* | errorTarget = 1.0% (Literal) | errorTarget = 2.0% | errorTarget = 3.0% | errorTarget = 5.0% |
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
| **Directional Classification** | Target Reference | `NO_MEANINGFUL_IMPROVEMENT` | `NO_MEANINGFUL_IMPROVEMENT` | `NO_MEANINGFUL_IMPROVEMENT` | `AWAY_FROM_TARGET_LOCALIZATION` |

*Note: Target quantities from Pandey & Kumar (2025) are labeled as `IMAGE_DERIVED_APPROXIMATION` (visual estimation from Fig. 5(b) and Fig. 6(a) colormaps with $\pm 20\%$ uncertainty).*

---

## 3. Case-by-Case Morphology Breakdown

### Case 1: `errorTarget = 1.0%` (Paper-Literal Baseline)
- **Mesh Count:** 57,901 elements (57,483 nodes).
- **Spatial Behavior:** Sizing request saturates the minimum element size ($h \approx 1\,\mu\text{m}$) across nearly the entire vertical domain. The refined band width $w(x)$ exceeds $0.80\,\text{mm}$ across all horizontal stations from $x=0.1$ to $x=0.9\,\text{mm}$.
- **Far-field Intrusion:** Only 1.06% of the specimen retains coarse nominal sizing ($h \ge 15\,\mu\text{m}$).
- **Verdict:** `NO_MEANINGFUL_IMPROVEMENT` (severe global overrefinement).

### Case 2: `errorTarget = 2.0%` (Literature Sensitivity)
- **Mesh Count:** 14,662 elements (14,642 nodes).
- **Spatial Behavior:** Although total element count is close to the published 13,941, total count is strictly a secondary metric. Spatially, the refinement pattern remains an expanded diamond/hourglass shape centered on the notch ($w = 0.763\,\text{mm}$ at $x=0.5\,\text{mm}$).
- **Far-field Intrusion:** 74.1% of elements remain in the far field ($|y-0.5| > 0.05\,\text{mm}$); only 27.5% of the area preserves coarse sizing.
- **Verdict:** `NO_MEANINGFUL_IMPROVEMENT` (spatially unlocalized).

### Case 3: `errorTarget = 3.0%` (Literature Sensitivity)
- **Mesh Count:** 6,835 elements (6,907 nodes).
- **Spatial Behavior:** Substantially confines fine elements ($h \le 3\,\mu\text{m}$) to a compact bounding box around the notch tip: $x \in [0.426, 0.573]\,\text{mm}$, $y \in [0.402, 0.577]\,\text{mm}$ ($y$-span $= 0.175\,\text{mm}$).
- **Flank Preservation:** Outer flanks at $x \le 0.3\,\text{mm}$ have $w = 0.0\,\text{mm}$. Coarse remaining area fraction increases to 57.46%.
- **Ligament Deficiency:** Because the refined band width at $x = 0.7\,\text{mm}$ drops to $w = 0.0\,\text{mm}$, the uncracked right ligament ahead of the propagating crack is not refined.
- **Verdict:** `NO_MEANINGFUL_IMPROVEMENT` (fails to resolve the horizontal right ligament).

### Case 4: `errorTarget = 5.0%` (Literature Sensitivity)
- **Mesh Count:** 4,258 elements (4,332 nodes).
- **Spatial Behavior:** Refinement is restricted to an isolated spot at the initial crack tip ($x \in [0.45, 0.53]\,\text{mm}$, $y \in [0.43, 0.57]\,\text{mm}$, $w(0.5) = 0.142\,\text{mm}$).
- **Path Underresolution:** Corridor median element size relaxes to $7.835\,\mu\text{m}$, and the ligament ahead of the crack ($x \ge 0.53\,\text{mm}$) is left unrefined at coarse nominal size ($h \approx 15-20\,\mu\text{m}$).
- **Verdict:** `AWAY_FROM_TARGET_LOCALIZATION` (underrefines the required fracture propagation path).

---

## 4. Generated Publication Figures

The following publication-quality figures are preserved under `results/figures/mode1_gate6b/`:
1. **Whole-Domain Mesh Comparison:** [`results/figures/mode1_gate6b/fig_mode1_stage13_errortarget_mesh_comparison.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_gate6b/fig_mode1_stage13_errortarget_mesh_comparison.png) (and [`.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_gate6b/fig_mode1_stage13_errortarget_mesh_comparison.pdf))
2. **Crack-Tip and Ligament Zoom Comparison:** [`results/figures/mode1_gate6b/fig_mode1_stage13_crack_zoom_comparison.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_gate6b/fig_mode1_stage13_crack_zoom_comparison.png) (and [`.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_gate6b/fig_mode1_stage13_crack_zoom_comparison.pdf))
3. **Sizing Metrics & Transects:** [`results/figures/mode1_gate6b/fig_mode1_stage13_sizing_transects.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_gate6b/fig_mode1_stage13_sizing_transects.png) (and [`.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode1_gate6b/fig_mode1_stage13_sizing_transects.pdf))

---

## 5. Scientific Summary

Stage 13 demonstrates that varying `errorTarget` systematically reduces overall element counts and suppresses far-field mesh refinement. However, under whole-domain `UNIFORM_ERROR` remeshing on the elastic companion state, no tested `errorTarget` value simultaneously produces a narrow horizontal corridor around $y=0.5\,\text{mm}$ and preserves sufficient refinement along the uncracked right ligament.

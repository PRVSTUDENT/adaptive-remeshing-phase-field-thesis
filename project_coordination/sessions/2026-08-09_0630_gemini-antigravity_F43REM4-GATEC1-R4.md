# Session Report: F43REM4-GATEC1-R4 Phase-Field Resolution-Coverage and Crack-Corridor Audit

- **Task ID**: `F43REM4-GATEC1-R4`
- **Agent**: `gemini-antigravity`
- **Date**: `2026-08-09`
- **Starting Commit**: `d9221c4fe6a7468f82b9ba4fd3fc2689fcc2cda5`
- **Status**: `complete_pass`
- **Gate C1 Localization**: `PASS`
- **Best Adaptive Candidate**: `F43REM4_MM`
- **Gate C1 Phase-Field Resolution**: `HOLD`
- **Final Production Mesh Selected**: `false`
- **Final Selected Candidate**: `none`
- **Recommended Next Stage**: `human_decision_on_crack_corridor_coverage_tradeoff`

---

## 1. Executive Summary

This session executed a rigorous offline audit to evaluate whether candidate meshes `PK1`, `PK5`, and `MM` satisfy phase-field resolution requirements along the actual fracture process zone and Mode-II crack corridor emanating from the notch tip:
1. **Separation of Concerns**: Confirmed that `min(h) < l0/2` does not imply that the entire fracture process zone or crack corridor is resolved to $h \le l_0/2$.
2. **Localization vs Resolution Trade-Off**:
   - `F43REM4_MM` achieves the highest adaptive localization efficiency ($5.07\times$ top-1% enrichment, $2.79\times$ top-5% enrichment with 2,206 elements) and reaches $h_{\min} = 0.3004 l_0$ right at the notch singularity. However, along the prospective shear crack corridor (top 5% MISESERI), its median size is $h \approx 0.82 l_0$, and only $3.0\%$ of its elements satisfy $h_{\text{area}} \le l_0/2$.
   - `F43REM4_PK5` provides denser process-zone coverage ($h_{\text{median}} \approx 0.60 l_0$, $10.6\%$ with $h \le l_0/2$, and $26.7\%$ with minimum edge $\le l_0/2$) with 4,894 elements (14.7k 3-layer UEL elements).
   - `F43REM4_PK1` provides unbroken $h \le 0.5 l_0$ coverage ($84.9\%$ of top-5% elements), but functions as a near-global uniform mesh of 21,397 elements (64.2k 3-layer UEL elements) with no density contrast.
3. **Decisive Classification**:
   - `Gate_C1_localization = PASS`
   - `best_adaptive_candidate = F43REM4_MM`
   - `Gate_C1_phase_field_resolution = HOLD`
   - `final_production_mesh_selected = false`
   - `Gate_C1 = HOLD` (awaiting human supervisor alignment on the trade-off between MM's superior economy vs PK5's denser corridor coverage).

---

## 2. Frozen Input Deck Lineage & Parameters

All three candidates were evaluated without modifying their frozen decks ($l_0 = 0.015\text{ mm}$):

| Candidate | Source Job ID | Deck SHA-256 Hash | Physical Nodes | Physical Elements | Sizing Method & Rule Parameters |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PRE3 (Baseline)** | `1385461.mmaster02` | `3309a6331a...` | 3,799 | 3,716 | Uniform initial reference pre-analysis mesh |
| **F43REM4_PK1** | `1385573.mmaster02` | `c21198b1e3...` | 21,429 | 21,397 | `UNIFORM_ERROR`, `errorTarget = 1.0%`, `refinementFactor = 10` |
| **F43REM4_PK5** | `1385574.mmaster02` | `87ab62c411...` | 4,998 | 4,894 | `UNIFORM_ERROR`, `errorTarget = 5.0%`, `refinementFactor = 10` |
| **F43REM4_MM** | `1385575.mmaster02` | `d404356d5c...` | 2,294 | 2,206 | `MINIMUM_MAXIMUM`, `maxSolutionErrorTarget = 5.0%`, `minSolutionErrorTarget = 1.0%` |

---

## 3. Percentile Region Resolution Fractions ($l_0 = 0.015\text{ mm}$)

### 3.1 Candidate MM (`1385575.mmaster02`)
| Region | Refined Elements | $h_{\text{area}} \le 1.0 l_0$ | $h_{\text{area}} \le 0.5 l_0$ | $h_{\text{area}} \le 1/3 l_0$ | $\min(e) \le 1.0 l_0$ | $\min(e) \le 0.5 l_0$ | $\min(e) \le 1/3 l_0$ | $\max(e) \le 1.0 l_0$ | $\max(e) \le 0.5 l_0$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Top 1%** | 130 | 100.0% | **4.6%** | 1.5% | 100.0% | **19.2%** | 0.0% | 88.5% | 0.8% |
| **Top 5%** | 332 | 68.7% | **3.0%** | 0.6% | 79.5% | **8.4%** | 0.0% | 50.6% | 0.3% |
| **Top 10%** | 473 | 51.4% | **2.1%** | 0.4% | 62.8% | **5.9%** | 0.0% | 36.4% | 0.2% |
| **Top 20%** | 684 | 36.8% | **1.5%** | 0.3% | 47.4% | **4.1%** | 0.0% | 25.3% | 0.1% |

### 3.2 Candidate PK5 (`1385574.mmaster02`)
| Region | Refined Elements | $h_{\text{area}} \le 1.0 l_0$ | $h_{\text{area}} \le 0.5 l_0$ | $h_{\text{area}} \le 1/3 l_0$ | $\min(e) \le 1.0 l_0$ | $\min(e) \le 0.5 l_0$ | $\min(e) \le 1/3 l_0$ | $\max(e) \le 1.0 l_0$ | $\max(e) \le 0.5 l_0$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Top 1%** | 190 | 100.0% | **12.6%** | 1.1% | 100.0% | **41.6%** | 0.0% | 100.0% | 1.6% |
| **Top 5%** | 611 | 97.9% | **10.6%** | 0.3% | 99.0% | **26.7%** | 0.3% | 92.3% | 1.1% |
| **Top 10%** | 898 | 88.3% | **8.5%** | 0.6% | 93.1% | **19.6%** | 0.9% | 75.3% | 1.1% |
| **Top 20%** | 1380 | 74.2% | **5.7%** | 0.4% | 85.4% | **13.0%** | 0.6% | 55.9% | 0.7% |

### 3.3 Candidate PK1 (`1385573.mmaster02`)
| Region | Refined Elements | $h_{\text{area}} \le 1.0 l_0$ | $h_{\text{area}} \le 0.5 l_0$ | $h_{\text{area}} \le 1/3 l_0$ | $\min(e) \le 1.0 l_0$ | $\min(e) \le 0.5 l_0$ | $\min(e) \le 1/3 l_0$ | $\max(e) \le 1.0 l_0$ | $\max(e) \le 0.5 l_0$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Top 1%** | 251 | 100.0% | **82.5%** | 0.4% | 100.0% | **98.4%** | 4.8% | 100.0% | 60.6% |
| **Top 5%** | 1234 | 100.0% | **84.9%** | 2.8% | 100.0% | **98.1%** | 7.4% | 100.0% | 59.5% |
| **Top 10%** | 2484 | 100.0% | **86.9%** | 3.5% | 100.0% | **98.4%** | 11.3% | 100.0% | 60.0% |
| **Top 20%** | 4959 | 100.0% | **88.1%** | 3.8% | 100.0% | **98.6%** | 12.8% | 100.0% | 61.5% |

---

## 4. Percentile Region Sizing Distributions ($h_{\text{area}} / l_0$)

| Candidate | Region | Median | p75 | p90 | p95 | Maximum |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **MM** | Top 1% | 0.6650 | 0.7276 | 0.8223 | **0.8930** | 0.9604 |
| **MM** | Top 5% | 0.8170 | 1.0790 | 1.2623 | **1.3595** | 1.5834 |
| **MM** | Top 10% | 0.9718 | 1.2623 | 1.4585 | **1.5884** | 2.0015 |
| **MM** | Top 20% | 1.1658 | 1.4452 | 1.6318 | **1.7642** | 2.2444 |
| **PK5** | Top 1% | 0.5356 | 0.5641 | 0.5966 | **0.6497** | 0.7527 |
| **PK5** | Top 5% | 0.6033 | 0.7294 | 0.8723 | **0.9389** | 1.3257 |
| **PK5** | Top 10% | 0.6906 | 0.8897 | 1.0188 | **1.1124** | 1.3458 |
| **PK5** | Top 20% | 0.8420 | 1.0051 | 1.1254 | **1.1739** | 1.4752 |
| **PK1** | Top 1% | 0.4820 | 0.4925 | 0.5098 | **0.5315** | 0.5803 |
| **PK1** | Top 5% | 0.4686 | 0.4894 | 0.5097 | **0.5279** | 0.6091 |
| **PK1** | Top 10% | 0.4637 | 0.4858 | 0.5068 | **0.5247** | 0.6091 |
| **PK1** | Top 20% | 0.4573 | 0.4817 | 0.5044 | **0.5227** | 0.6352 |

---

## 5. Connected Mode-II Crack-Corridor Geometric Audit

Connecting from the notch tip $(0.0, 0.0)$ across the high-MISESERI process zone:

| Connected Corridor | PRE3 Elements | Corridor Area ($mm^2$) | Candidate | Refined Elements | Area Fraction $h \le 0.5 l_0$ | Area Fraction $h \le 1/3 l_0$ | Median $h/l_0$ | p95 $h/l_0$ | Largest Under-Resolved Section ($mm^2$) | Distance from Notch Tip ($mm$) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Top 1% Connected** | 26 | 0.0089 | **MM** | 80 | **0.4%** | 0.0% | 0.6813 | 0.9171 | 0.00899 | 0.0036 |
| **Top 1% Connected** | 26 | 0.0089 | **PK5** | 135 | **13.6%** | 0.5% | 0.5313 | 0.6539 | 0.00741 | 0.0036 |
| **Top 1% Connected** | 26 | 0.0089 | **PK1** | 174 | **71.1%** | 0.2% | 0.4733 | 0.5428 | 0.00228 | 0.0176 |
| **Top 5% Connected** | 114 | 0.0359 | **MM** | 208 | **0.4%** | 0.0% | 0.8053 | 1.3209 | 0.03636 | 0.0068 |
| **Top 5% Connected** | 114 | 0.0359 | **PK5** | 402 | **7.3%** | 0.1% | 0.5926 | 0.8518 | 0.02726 | 0.0097 |
| **Top 5% Connected** | 114 | 0.0359 | **PK1** | 764 | **81.1%** | 0.9% | 0.4613 | 0.5280 | 0.00247 | 0.0156 |
| **Top 10% Connected** | 191 | 0.0580 | **MM** | 268 | **0.3%** | 0.0% | 0.9031 | 1.4263 | 0.05848 | 0.0296 |
| **Top 10% Connected** | 191 | 0.0584 | **PK5** | 529 | **5.1%** | 0.1% | 0.6390 | 1.0490 | 0.04168 | 0.0025 |
| **Top 10% Connected** | 191 | 0.0580 | **PK1** | 1259 | **81.9%** | 1.1% | 0.4570 | 0.5293 | 0.00247 | 0.0156 |

---

## 6. Connected Fine-Mesh Path Analysis

| Candidate | Path Connected at $h \le 0.50 l_0$ | Continuous Reach Distance ($mm$) | Connected Elements Count | Path Connected at $h \le 0.75 l_0$ | Continuous Reach Distance ($mm$) | Connected Elements Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **F43REM4_MM** | **`False`** | 0.0000 | 0 | **`True`** | 0.0817 | 84 |
| **F43REM4_PK5** | **`False`** | 0.0263 | 4 | **`True`** | 0.1541 | 392 |
| **F43REM4_PK1** | **`True`** | 0.7019 | 17,524 | **`True`** | 0.7019 | 21,357 |

---

## 7. Required Extraction Summary Metrics

```text
MM_top1_fraction_h_le_l0_over_2 = 0.0462
MM_top5_fraction_h_le_l0_over_2 = 0.0301
MM_top10_fraction_h_le_l0_over_2 = 0.0211

PK5_top1_fraction_h_le_l0_over_2 = 0.1263
PK5_top5_fraction_h_le_l0_over_2 = 0.1064
PK5_top10_fraction_h_le_l0_over_2 = 0.0846

PK1_top1_fraction_h_le_l0_over_2 = 0.8247
PK1_top5_fraction_h_le_l0_over_2 = 0.8493
PK1_top10_fraction_h_le_l0_over_2 = 0.8692

MM_top5_p95_h_over_l0 = 1.3595
PK5_top5_p95_h_over_l0 = 0.9389
PK1_top5_p95_h_over_l0 = 0.5279

MM_connected_fine_corridor = false
PK5_connected_fine_corridor = false
PK1_connected_fine_corridor = true

best_adaptive_candidate = MM
final_selected_candidate = none
Gate_C1 = HOLD
next_stage = human_decision_on_crack_corridor_coverage_tradeoff
```

---

## 8. Standalone Visual Artifacts

The vector SVG visual maps have been generated in the figures directory:
1. [`f43rem4_mm_crack_corridor_audit.svg`](file:///d:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/figures/f43rem4_mm_crack_corridor_audit.svg)
2. [`f43rem4_pk5_crack_corridor_audit.svg`](file:///d:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/figures/f43rem4_pk5_crack_corridor_audit.svg)
3. [`f43rem4_pk1_crack_corridor_audit.svg`](file:///d:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/figures/f43rem4_pk1_crack_corridor_audit.svg)

---

## 9. Authority Boundary

- `execution_authorized`: `false`
- `submission_approved`: `false`
- `replacement_authorized`: `false`
- `maximum_jobs_now`: `0`
- `automatic_retry`: `false`
- `new_qsub_called`: `false`
- `new_HPC_submissions`: `0`
- `running_jobs`: `0`
- `queued_jobs`: `0`

# Anti-Deviation Card: Gate 5 — Abaqus Software Release Sensitivity (2022 vs 2023)

**Card ID**: `ANTI_DEVIATION_CARD_GATE5_ABAQUS_2022_VS_2023`  
**Date**: 2026-09-10  
**Phase**: Task 4 / Gate 5 Protocol  
**Governing Priority**: Priority B (Publication Element Count Discrepancy: 13,941 vs 71,320 elements)  
**Parent Investigation**: `docs/supervisor_reports/PRIORITY_B_REPRODUCIBILITY_MATRIX_AND_AUTHOR_QUERY.md`

---

## 1. Objective & Hypothesis

### 1.1 Research Question
Does the Dassault Systemes Abaqus/CAE and solver release difference between **Abaqus 2022** and **Abaqus 2023** account for the finite element count discrepancy in the Mode-I benchmark of Pandey & Kumar (2025) (published $N_{el} = 13,941$ vs our literal 1% reconstruction $N_{el} = 71,320$)?

### 1.2 Hypothesis Under Test
Pandey & Kumar (2025, Sec. 4.1) report:
> *"The number of elements in the initial coarse mesh is 2,500, which after 1 cycle of adaptive remeshing with an error target of 1% increases to 13,941 elements."*

The authors omit the specific Abaqus release and build numbers used. If the internal sizing heuristic in Dassault's Superconvergent Patch Recovery (SPR) or the error-to-element-size mapping in `m.adaptiveRemesh()` was modified or re-scaled between Abaqus 2022 and 2023, the exact same input specification could produce $N_{el} = 13,941$ under 2022 and $N_{el} = 71,320$ under 2023.

---

## 2. Experimental Controls & Isolation Protocol

To guarantee single-factor isolation without cross-contamination:

| Control Parameter | Specification | Verification Status |
|:---|:---|:---|
| **Isolated Factor** | Abaqus Software Release | Tested: `Abaqus 2022` vs `Abaqus 2023` |
| **Release 2023 Build** | `2022_09_28-20.11.55 183150` | Verified on `mnode097.cluster` |
| **Release 2022 Build** | `2021_09_15-19.57.30 176069` | Verified on `mnode097.cluster` |
| **Geometry** | $[0, 1] \times [0, 1]\,\text{mm}$ square plate | Fixed |
| **Notch / Seam** | Sharp slit seam at $y = 0.5\,\text{mm}, 0 \le x \le 0.5\,\text{mm}$ | Fixed |
| **Initial Coarse Mesh** | Coarse mesh ($N_{el} = 2,906$, advancing front quad-dominated) | Identical |
| **Pre-Analysis Formulation** | Linear Plane Strain continuum elements (`CPE4` quads + `CPE3` tris) | Canonical |
| **Pre-Analysis Boundary Conditions** | Bottom $u_2 = 0$, pin $(0,0)$ $u_1 = 0$, top $u_1 = 0, u_2 = 0.005\,\text{mm}$ | Identical |
| **Error Indicator Request** | `MISESERI`, `MISESAVG`, `EVOL` | Identical |
| **Remeshing Rule** | `name='RR: 1'`, `variable='MISESERI'`, `sizingMethod=UNIFORM_ERROR` | Identical (Listing 1) |
| **Error Target** | `errorTarget = 1.0` ($1\%$) and `2.0` ($2\%$) | Literal Publication / Sensitivity Values |
| **Element Size Limits** | $h_{\min} = 0.001\,\text{mm}$, $h_{\max} = 0.02\,\text{mm}$ | Identical (Listing 1) |
| **Sizing Bounds** | `coarseningFactor = NOT_ALLOWED`, `refinementFactor = 10` | Identical (Listing 1) |
| **Adaptive Cycles** | Exactly 1 pass (`m.adaptiveRemesh(odb=o1)` called once) | Identical |
| **ODB Provenance** | Pre-analysis solved from scratch within each release | Zero cross-release ODB passing |

---

## 3. Pre-Declared Falsification Criteria & Decision Rules

| Outcome Classification | Measured Element Count ($N_{el}$) | Physical Interpretation & Next Action |
|:---|:---|:---|
| **`RELEASE_DEPENDENCE_CONFIRMED`** | $13,941 \pm 5\%$ ($13,244 \le N_{el} \le 14,638$) | **Confirmed**: Discrepancy is fully explained by Abaqus version differences. Pandey & Kumar (2025) utilized Abaqus 2022 (or an earlier build sharing its sizing algorithm). Sizing logic was revised in 2023. Close Priority B as solved. |
| **`NO_RELEASE_EFFECT_DETECTED_FOR_THE_TESTED_CPE4_MODE1_CONFIGURATION`** | $71,320 \pm 0\%$ ($N_{el} = 71,320$ identically) | **Falsified**: Dassault's adaptive remeshing sizing engine is strictly invariant between 2022 and 2023. Software release between these two versions is ruled out as the root cause. Direct next investigation to unstated parameters in publication text. |
| **`PARTIAL_RELEASE_SHIFT`** | Intermediate ($15,000 < N_{el} < 65,000$) | **Partial Effect**: Sizing algorithm changed, but other factors also contribute. Inspect spatial element distribution across 5 evaluation regions. |

---

## 4. Execution & Closure Evidence (Job `1404373.mmaster02`)

1. **Predecessor Confound Identification**: Jobs `1404364` ($58,679$ elems) and `1404365` ($15,396$ elems) executed `CPS4` Plane Stress input decks, confounding release comparison with formulation shift. Both jobs were retired (`RETIRED_ABAQUS_RELEASE_COMPARISON_DUE_TO_CONFOUNDED_INPUTS`).
2. **Clean Exact-Twin Execution (Job `1404373.mmaster02`)**:
   - Executed clean script `run_gate5_exact_release_twin.py` in `/scratch9/pr21vyci/gate5_exact_release_twin/` on compute node `mnode097.cluster`.
   - **Pre-Analysis Stress Error Field**: 5,812 `MISESERI` values matched bit-for-bit across Abaqus 2022 and 2023.
   - **1% Refined Mesh**: Both Abaqus 2022 and 2023 generated **71,320 elements** (69,441 quads, 1,879 tris, 70,845 nodes), with byte-for-byte identical uncommented `.inp` decks (`1PCT_IDENTICAL_WITHOUT_COMMENTS`).
   - **2% Refined Mesh**: Both Abaqus 2022 and 2023 generated **17,687 elements** (17,194 quads, 493 tris, 17,688 nodes), with byte-for-byte identical uncommented `.inp` decks (`2PCT_IDENTICAL_WITHOUT_COMMENTS`).
3. **Formal Epistemic Conclusion**: **`NO_RELEASE_EFFECT_DETECTED_FOR_THE_TESTED_CPE4_MODE1_CONFIGURATION`**. Software release differences between Abaqus 2022 and 2023 are decisively ruled out as the cause of the discrepancy.

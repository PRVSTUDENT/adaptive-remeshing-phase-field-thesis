# Mode-I Adaptive-Direction Evidence Package & Spatial Localization Audit

## 1. Executive Summary & Purpose

This package provides the complete, self-contained evidence base for the **spatial localization, corridor width, and computational efficiency audit** of the Mode-I adaptive remeshing workflow (Pandey & Kumar, 2025, *CMES* 144(3), 3251–3276).

### Governed Direction Classifications

| Candidate Mesh | Stage of Origin | Element Count | Direction Classification | Key Forensic Finding |
| :--- | :---: | :---: | :---: | :--- |
| **`PK_M1_STEP2_62K_JOB1409585`** | Step-2 Propagated Crack | $62,057$ | **`AWAY_FROM_TARGET_LOCALIZATION`** | Refines a broad cloud across the entire right half-plate ($x \in [0.5, 1.0]$) because it was driven by moving crack tip stress fields. **Frozen as diagnostic evidence only; rejected as the production adaptive workflow.** |
| **`PK_M1_JOB2_ADAPTED_1PCT`** | Step-1 Pre-Analysis | $42,318$ | **`NO_MEANINGFUL_IMPROVEMENT`** (Efficiency) | Forms the narrow horizontal corridor, but $64.0\%$ ($27,090$ elements) are placed in the uncracked far field ($y > 0.6$ or $y < 0.4$) due to `UNIFORM_ERROR` relative error equilibration on the background stress. |
| **`PK_M1_JOB2_ADAPTED_2PCT`** | Step-1 Pre-Analysis | $10,253$ | **`TOWARD_TARGET_LOCALIZATION`** | Preserves high crack-tip resolution ($h \approx 1\text{--}2\,\mu\text{m}$) and narrow corridor while suppressing far-field over-refinement by $>75\%$, matching the $\sim 14\text{k}$ element-count scale of Pandey & Kumar. |

---

## 2. Pre-Analysis Model & MISESERI Error Indicator Provenance

### Analytical & Epistemological Definition
* **Physical Indicator**: $\mathrm{MISESERI}$ is the Abaqus Mises stress discretization/error indicator associated with the recovered stress solution:
  $$\mathrm{MISESERI} = \sqrt{\frac{3}{2}\mathbf{s}_e : \mathbf{s}_e}$$
* **Nature of Variable**: It is an element-field error indicator derived from stress recovery on the linear-elastic continuum stress field $\mathbf{\sigma}_h$. It is **NOT phase-field error, NOT damage error** ($d \equiv 0$ in the pre-analysis).
* **Coarse Model Structure**: $1.0 \times 1.0\,\text{mm}$ square plate with a sharp zero-gap horizontal seam along $y=0.5\,\text{mm}$ ($0 \le x \le 0.5\,\text{mm}$), discretized with **2,906 finite elements** (2,818 CPE4 + 88 CPE3) and 2,988 nodes.
* **Spatial Singularity Marking**:
  - Peak crack tip $\mathrm{MISESERI} = 1.0836\,\text{MPa}$ at $(x=0.5, y=0.5)$.
  - Far-field mean $\mathrm{MISESERI} = 0.0075\,\text{MPa}$ ($>144\times$ singularity-to-farfield ratio).
  - Data file: [`canonical_mode1_coarse_miseseri_2906.csv`](canonical_mode1_coarse_miseseri_2906.csv).

---

## 3. Quantitative Zone Breakdown & Far-Field Burden

The table below summarizes the spatial distribution of finite elements across the $1.0 \times 1.0\,\text{mm}$ domain:

| Zone Name | Region Definition | 1.0% Target Count | 1.0% Pct of Total | 1.0% Mean $h$ [$\mu\text{m}$] | 2.0% Target Count | 2.0% Pct of Total | 2.0% Mean $h$ [$\mu\text{m}$] |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`Core_Corridor`** | Ligament core ($x \in [0.5, 1.0], y \in [0.45, 0.55]$) | **4,396** | 10.39% | 2.70 | **1,263** | 12.32% | 4.78 |
| **`Extended_Corridor`** | Ligament transition ($x \in [0.5, 1.0], y \in [0.40, 0.60]$) | **3,753** | 8.87% | 3.15 | **706** | 6.89% | 6.88 |
| **`Slit_Wake`** | Crack wake ($x \in [0.0, 0.5], y \in [0.40, 0.60]$) | **7,079** | 16.73% | 3.03 | **2,813** | 27.44% | 4.43 |
| **`Far_Field_Upper`** | Upper far field ($y > 0.60\,\text{mm}$) | **16,064** | 37.96% | 4.59 | **3,203** | 31.24% | 10.23 |
| **`Far_Field_Lower`** | Lower far field ($y < 0.40\,\text{mm}$) | **11,026** | 26.06% | 5.50 | **2,268** | 22.12% | 12.49 |
| **Total Domain** | Full $1.0 \times 1.0\,\text{mm}$ Plate | **42,318** | 100.00% | 4.47 | **10,253** | 100.00% | 8.65 |

### Root Cause of Far-Field Refinement in 1.0% Target
In `UNIFORM_ERROR` sizing, Abaqus sizes elements to achieve a uniform relative error $\eta_{\text{target}} = 1.0\%$ relative to the domain average equivalent stress. Because the far-field tensile stress is non-zero, demanding $\le 1.0\%$ relative error everywhere forces Abaqus to refine far-field elements down to $h \approx 4\text{--}5\,\mu\text{m}$ rather than leaving them at the coarse background $h_{\max} = 20\,\mu\text{m}$. Combined with `coarseningFactor=NOT_ALLOWED`, this creates a massive far-field discretization overhead ($>27,000$ elements in far-field alone).

Relaxing the target to $2.0\%$ allows the far-field elements to remain at $h \approx 10\text{--}13\,\mu\text{m}$ ($>75\%$ reduction in far-field element count), while keeping $h \approx 1\text{--}2\,\mu\text{m}$ at the crack tip.

---

## 4. Comparison Against Pandey & Kumar (2025) Fig. 5(b) & Fig. 6(a)

1. **Singularity Spatial Structure (Fig. 6(a))**:
   - The recovered error indicator from Job-1 pre-analysis matches Fig. 6(a) with a singular peak at the crack tip $(0.5, 0.5)$ and steep decay into the far field.
2. **Corridor Localization (Fig. 5(b))**:
   - Both the 1.0% and 2.0% pre-analysis meshes form a horizontal refined corridor along the expected fracture plane $y=0.5\,\text{mm}$.
   - The Step-2 62k mesh deviates completely by refining a diffuse triangle over $x \in [0.5, 1.0]$, proving it was produced from the wrong physical stage.
3. **Element-Count Scale**:
   - Pandey & Kumar report $\sim 13,941$ elements.
   - The 2.0% pre-analysis mesh ($10,253\text{--}17,687$ elements across seeding variants) reproduces this scale accurately.
   - The 1.0% pre-analysis mesh ($42,318\text{--}71,320$ elements) reflects the publication information limitation accepted by the supervisor on 17-Sep-2026.

---

## 5. Artifact Manifest & Verification Hashes

| File Name | Role | File Size | SHA-256 Hash |
| :--- | :--- | :---: | :--- |
| [`PK_M1_PRE_UEL_CORRECTED.inp`](PK_M1_PRE_UEL_CORRECTED.inp) | Exact Pre-Analysis Deck | 331,185 bytes | `D8B64ADAD5B761C1AEB59B8C1FE2E8A4959D74CB673061760C8C06680AFB6D32` |
| [`execute_mode1_native_adaptive_remesh.py`](execute_mode1_native_adaptive_remesh.py) | Native Remeshing Driver | 5,691 bytes | `63C851923C136C421E6BE51307AAC2F659F4F86E1DC82E56FD152C8FE14C6B70` |
| [`canonical_mode1_coarse_miseseri_2906.csv`](canonical_mode1_coarse_miseseri_2906.csv) | Centroid MISESERI Dataset | 240,154 bytes | `8DFEF5190913A95624BE7A93092234E0234957918A6BC6FC3E4662CF4220ADC8` |
| [`fig_mode1_miseseri_spatial_distribution.png`](fig_mode1_miseseri_spatial_distribution.png) | 2D MISESERI Spatial Plot | 1,143,518 bytes | `7D7AC2619075EE43084E8BE0233085DC1E0DEA365EF9ED59285A19AA2F346562` |
| [`PK_M1_JOB2_ADAPTED_1PCT.inp`](PK_M1_JOB2_ADAPTED_1PCT.inp) | 1.0% Adapted Input Deck | 5,517,143 bytes | `028A604FFECAF37454309D4A4C6A966A79BEED72B3BC76AC59413B4E467B74C6` |
| [`PK_M1_JOB2_ADAPTED_2PCT.inp`](PK_M1_JOB2_ADAPTED_2PCT.inp) | 2.0% Adapted Input Deck | 1,218,784 bytes | `B3D3B99F43BD1E0CC9C40B8FF1179AC950B37DEDF963DD9092113753274BA685` |
| [`fig_mode1_mesh_comparison_1pct_vs_2pct.png`](fig_mode1_mesh_comparison_1pct_vs_2pct.png) | 4-Panel Mesh & Zoom Figure | 4,557,627 bytes | `BC34AF85F1EE40F51D70308BC0A670004BD4EAE66EF1D3B8E1F40CAD71B22542` |
| [`ADAPTIVE_ZONE_QUANTITATIVE_TABLE.csv`](ADAPTIVE_ZONE_QUANTITATIVE_TABLE.csv) | Quantitative Zone Statistics | 776 bytes | `3127CE508AD205758540DF228072DE2672FC9C99ADB8E29AD49DD1D3582DAA6D` |
| [`ADAPTIVE_DIRECTION_EVIDENCE_SUMMARY.json`](ADAPTIVE_DIRECTION_EVIDENCE_SUMMARY.json) | Machine-Readable Audit Summary | 4,522 bytes | `877726600287E7BD4EDAF9C3A6DB8D24644F7CDDED68B443256B33840EE5B23F` |
| [`README.md`](README.md) | Audit Documentation Report | ~7 KB | Updated |

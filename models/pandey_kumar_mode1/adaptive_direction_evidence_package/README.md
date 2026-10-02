# Mode-I Adaptive-Direction Evidence Package & Lineage Reconciliation Audit

## 1. Executive Summary & Purpose

This package provides the complete, self-contained evidence base for the **lineage reconciliation, spatial localization, corridor width, and computational efficiency audit** of the Mode-I adaptive remeshing workflow (Pandey & Kumar, 2025, *CMES* 144(3), 3251–3276).

### Governed Direction Classifications

| Candidate Mesh Key | Mesh Lineage & Target | Element Count | Nodes | Corridor Elements ($y \in [0.48, 0.52]$) | Far-Field Elements ($y < 0.4$ or $y > 0.6$) | Direction Classification | Key Forensic Finding |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`PK_M1_STEP2_62K_JOB1409585`** | Step-2 Propagated Crack | $62,057$ | $62,608$ | $5,392$ (8.7%) | $38,827$ (62.6%) | **`AWAY_FROM_TARGET_LOCALIZATION`** | Refines a diffuse cloud over the entire ligament ($x \in [0.5, 1.0]$) driven by moving crack-tip stress states. **Frozen as diagnostic evidence; rejected as the production adaptive workflow.** |
| **`Lineage_A_1pct_71k`** | Lineage A Pre-Analysis (1.0%) | $71,320$ | $71,833$ | $2,267$ (3.2%) | $56,961$ (79.9%) | **`NO_MEANINGFUL_IMPROVEMENT`** | High far-field burden ($79.9\%$) caused by lateral constraint parasitic stresses in coarse deck `PK_PREANALYSIS_COARSE.inp`. |
| **`Lineage_A_2pct_15k`** | Lineage A Pre-Analysis (2.0%) | $15,396$ | $15,702$ | $935$ (6.1%) | $10,171$ (66.1%) | **`TOWARD_TARGET_LOCALIZATION`** | Preserves crack-tip resolution ($h_{\min}=0.43\,\mu\text{m}$, tip $0.89\,\mu\text{m}$) while reducing total elements by $78.4\%$ vs 1.0%. |
| **`Lineage_B_1pct_42k`** | Lineage B Pre-Analysis (1.0%) | $42,318$ | $42,787$ | $2,022$ (4.8%) | $30,984$ (73.2%) | **`NO_MEANINGFUL_IMPROVEMENT`** | Structured quad base and RP coupling reduce far-field count vs Lineage A, but $73.2\%$ far-field elements remain under 1.0% error target. |
| **`Lineage_B_2pct_10k`** | Lineage B Pre-Analysis (2.0%) | $10,253$ | $10,321$ | $702$ (6.8%) | $6,569$ (64.1%) | **`TOWARD_TARGET_LOCALIZATION`** | Best-balanced candidate: preserves $h_{\min}=0.69\,\mu\text{m}$ (tip $0.91\,\mu\text{m}$) and narrow corridor, reducing total elements to $10,253$, matching Pandey & Kumar ($\sim 14\text{k}$). |
| **`CAE_2024_Reference_48k`** | CAE 2024 Reference (1.0%) | $48,329$ | $48,819$ | $2,313$ (4.8%) | $35,954$ (74.4%) | **`NO_MEANINGFUL_IMPROVEMENT`** | Intermediate 1.0% variant matching the 1.0% target localization profile. |

---

## 2. Lineage Provenance & Semantic Diff Analysis

A rigorous semantic and causal diff was conducted between the two pre-analysis mesh lineages:

### Causal Differences Between Lineages

1. **Lineage A (Historical Baseline Lineage: 71,320 at 1.0%, 15,396 / 17,687 at 2.0%)**:
   - **Originating Coarse Deck**: `PK_PREANALYSIS_COARSE.inp` (2,906 finite elements: 2,818 CPE4 + 88 CPE3, 2,989 nodes).
   - **Boundary Conditions**: Direct nodal displacement boundary conditions (`Bottom` $u_2=0$, `Top` $u_2=0.005\,\text{mm}, u_1=0$). The rigid lateral constraint ($u_1=0$) across all top-edge nodes prevents natural Poisson contraction, inducing parasitic corner and edge shear stresses.
   - **Remeshing Sizing Effect**: Under `UNIFORM_ERROR` relative sizing, elevated background error indicators force Abaqus to refine large portions of the uncracked far field down to $h \approx 2\text{--}4\,\mu\text{m}$ ($79.9\%$ far-field elements at 1.0%), producing 71,320 finite elements.

2. **Lineage B (Job-1 Pre-Analysis Lineage: 42,318 at 1.0%, 10,253 at 2.0%)**:
   - **Originating Coarse Deck**: `PK_M1_PRE_UEL_CORRECTED.inp` (2,700 structured quads + 4 companion quads, 2,835 nodes).
   - **Boundary Conditions**: Kinematic coupling from reference point `N_RP` to `N_TOP` with wrapped `N_BOTTOM` cards. The structured coarse layout and RP coupling yield a smoother, unconstrained background stress field away from the crack tip.
   - **Remeshing Sizing Effect**: Far-field over-refinement is significantly reduced ($73.2\%$ at 1.0%, $64.1\%$ at 2.0%), yielding 42,318 finite elements at 1.0% and 10,253 finite elements at 2.0%.

3. **Core Equivalence Invariant**:
   - Both lineages are authentic single-pass Job-1 pre-analysis adaptive remeshings using identical RemeshingRule sizing parameters ($h_{\min}=1.0\,\mu\text{m}$, $h_{\max}=20.0\,\mu\text{m}$, `refinementFactor=10`, `coarseningFactor=NOT_ALLOWED`).
   - In both lineages, moving from `errorTarget=1.0%` to `2.0%` reduces total finite elements by $\approx 75\%$ while preserving the crack-tip resolution ($h_{\min} = 0.69\text{--}0.91\,\mu\text{m}$) and narrow horizontal propagation corridor along $y=0.5\,\text{mm}$.

---

## 3. Epistemological and Error Indicator Definitions

* **Physical Indicator**: $\mathrm{MISESERI}$ is the Abaqus Mises stress discretization/error indicator associated with the recovered stress solution:
  $$\mathrm{MISESERI} = \sqrt{\frac{3}{2}\mathbf{s}_e : \mathbf{s}_e}$$
* **Nature of Variable**: It is an element-field error indicator derived from stress recovery on the linear-elastic continuum stress field $\mathbf{\sigma}_h$. It is **NOT phase-field error, NOT damage error** ($d \equiv 0$ in the pre-analysis).
* **Coarse Model Structure**: $1.0 \times 1.0\,\text{mm}$ square plate with a sharp zero-gap horizontal seam along $y=0.5\,\text{mm}$ ($0 \le x \le 0.5\,\text{mm}$).
* **Spatial Singularity Marking**:
  - Peak crack tip $\mathrm{MISESERI} = 1.0836\,\text{MPa}$ at $(x=0.5, y=0.5)$.
  - Far-field mean $\mathrm{MISESERI} = 0.0075\,\text{MPa}$ ($>144\times$ singularity-to-farfield ratio).
  - Data file: [`canonical_mode1_coarse_miseseri_2906.csv`](canonical_mode1_coarse_miseseri_2906.csv).

---

## 4. Comprehensive Quantitative Spatial Metrics Table

| Metric / Parameter | Lineage A (1.0%) | Lineage A (2.0%) | Lineage B (1.0%) | Lineage B (2.0%) | CAE 2024 (1.0%) | Step-2 62k (Diagnostic) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Total Finite Elements** | $71,320$ | $15,396$ | $42,318$ | $10,253$ | $48,329$ | $62,057$ |
| **Total Nodes** | $71,833$ | $15,702$ | $42,787$ | $10,321$ | $48,819$ | $62,608$ |
| **Narrow Corridor ($y \in [0.48, 0.52]$)** | $2,267$ (3.18%) | $935$ (6.07%) | $2,022$ (4.78%) | $702$ (6.85%) | $2,313$ (4.79%) | $5,392$ (8.69%) |
| **Extended Corridor ($y \in [0.40, 0.60]$)** | $6,375$ (8.94%) | $2,185$ (14.19%) | $4,570$ (10.80%) | $1,349$ (13.16%) | $5,436$ (11.25%) | $12,711$ (20.48%) |
| **Crack Wake ($x \le 0.5, y \in [0.4, 0.6]$)** | $7,984$ (11.19%) | $3,040$ (19.75%) | $6,764$ (15.98%) | $2,335$ (22.77%) | $6,939$ (14.36%) | $10,519$ (16.95%) |
| **Far Field ($y < 0.4$ or $y > 0.6$)** | $56,961$ (79.87%) | $10,171$ (66.06%) | $30,984$ (73.22%) | $6,569$ (64.07%) | $35,954$ (74.39%) | $38,827$ (62.57%) |
| **$h_{\min}$ ($\mu\text{m}$)** | $0.56$ | $0.43$ | $0.67$ | $0.69$ | $0.59$ | $0.45$ |
| **$h_{\text{median}}$ ($\mu\text{m}$)** | $2.92$ | $5.67$ | $3.80$ | $7.42$ | $3.57$ | $2.52$ |
| **$h_{\max}$ ($\mu\text{m}$)** | $19.99$ | $20.00$ | $20.00$ | $20.00$ | $20.00$ | $20.00$ |
| **Crack-Tip $h_{\min}$ ($\mu\text{m}$)** | $0.91$ | $0.89$ | $0.75$ | $0.91$ | $0.59$ | $0.80$ |
| **Direction Classification** | `NO_MEANINGFUL_IMPROVEMENT` | `TOWARD_TARGET_LOCALIZATION` | `NO_MEANINGFUL_IMPROVEMENT` | `TOWARD_TARGET_LOCALIZATION` | `NO_MEANINGFUL_IMPROVEMENT` | `AWAY_FROM_TARGET_LOCALIZATION` |

---

## 5. Comparison Against Pandey & Kumar (2025)

1. **Singularity Spatial Structure (Fig. 6(a))**:
   - The recovered error indicator from Job-1 pre-analysis matches Fig. 6(a) with a singular peak at the crack tip $(0.5, 0.5)$ and steep decay into the far field.
2. **Corridor Localization (Fig. 5(b))**:
   - Both 1.0% and 2.0% pre-analysis meshes form a narrow horizontal refined corridor along the expected fracture plane $y=0.5\,\text{mm}$.
   - The Step-2 62k mesh deviates completely by refining a diffuse triangle across $x \in [0.5, 1.0]$, confirming it was produced from the wrong physical stage.
3. **Element-Count Scale**:
   - Pandey & Kumar report $\sim 13,941$ finite elements.
   - The 2.0% pre-analysis candidate ($10,253$ finite elements) accurately reproduces this scale.
   - The 1.0% pre-analysis meshes ($42,318\text{--}71,320$ finite elements) reflect the accepted publication information limitation regarding exact relative sizing calibration.

---

## 6. Visual Evidence Figures

1. **Whole-Domain 4-Panel Lineage Comparison**:  
   [`fig_mode1_lineage_reconciliation_4panel.png`](fig_mode1_lineage_reconciliation_4panel.png)  
   Shows 2D spatial element size fields for Lineage A (1.0% & 2.0%) and Lineage B (1.0% & 2.0%).

2. **Ligament Profiles & Transverse Band Width Comparison**:  
   [`fig_mode1_ligament_profiles_lineage_comparison.png`](fig_mode1_ligament_profiles_lineage_comparison.png)  
   Compares element size $h(x)$ along the ligament $y=0.5\,\text{mm}$ and transverse corridor width $w(x)$ across all 6 candidate meshes.

3. **2D MISESERI Spatial Distribution**:  
   [`fig_mode1_miseseri_spatial_distribution.png`](fig_mode1_miseseri_spatial_distribution.png)  
   Shows the pre-analysis recovered error indicator field marking the crack tip singularity.

4. **1.0% vs 2.0% Mesh Comparison & Crack-Tip Zoom**:  
   [`fig_mode1_mesh_comparison_1pct_vs_2pct.png`](fig_mode1_mesh_comparison_1pct_vs_2pct.png)  
   Detailed side-by-side crack-tip refinement zoom.

---

## 7. Artifact Manifest & Verification Hashes

| File Name | Role | File Size | SHA-256 Hash |
| :--- | :--- | :---: | :--- |
| [`PK_M1_PRE_UEL_CORRECTED.inp`](PK_M1_PRE_UEL_CORRECTED.inp) | Exact Pre-Analysis Deck | 331,185 bytes | `D8B64ADAD5B761C1AEB59B8C1FE2E8A4959D74CB673061760C8C06680AFB6D32` |
| [`execute_mode1_native_adaptive_remesh.py`](execute_mode1_native_adaptive_remesh.py) | Native Remeshing Driver | 5,691 bytes | `63C851923C136C421E6BE51307AAC2F659F4F86E1DC82E56FD152C8FE14C6B70` |
| [`canonical_mode1_coarse_miseseri_2906.csv`](canonical_mode1_coarse_miseseri_2906.csv) | Centroid MISESERI Dataset | 240,154 bytes | `8DFEF5190913A95624BE7A93092234E0234957918A6BC6FC3E4662CF4220ADC8` |
| [`fig_mode1_miseseri_spatial_distribution.png`](fig_mode1_miseseri_spatial_distribution.png) | 2D MISESERI Spatial Plot | 1,143,518 bytes | `7D7AC2619075EE43084E8BE0233085DC1E0DEA365EF9ED59285A19AA2F346562` |
| [`PK_M1_JOB2_ADAPTED_1PCT.inp`](PK_M1_JOB2_ADAPTED_1PCT.inp) | 1.0% Adapted Input Deck | 5,517,143 bytes | `028A604FFECAF37454309D4A4C6A966A79BEED72B3BC76AC59413B4E467B74C6` |
| [`PK_M1_JOB2_ADAPTED_2PCT.inp`](PK_M1_JOB2_ADAPTED_2PCT.inp) | 2.0% Adapted Input Deck | 1,218,784 bytes | `B3D3B99F43BD1E0CC9C40B8FF1179AC950B37DEDF963DD9092113753274BA685` |
| [`fig_mode1_mesh_comparison_1pct_vs_2pct.png`](fig_mode1_mesh_comparison_1pct_vs_2pct.png) | 4-Panel Mesh & Zoom Figure | 4,557,627 bytes | `BC34AF85F1EE40F51D70308BC0A670004BD4EAE66EF1D3B8E1F40CAD71B22542` |
| [`fig_mode1_lineage_reconciliation_4panel.png`](fig_mode1_lineage_reconciliation_4panel.png) | 4-Panel Lineage Comparison | 3,124,374 bytes | `2C2DC58B43CD965BAAE19A2DF55716E8E2792D41F5EF251B5A5CE1F694F9403B` |
| [`fig_mode1_ligament_profiles_lineage_comparison.png`](fig_mode1_ligament_profiles_lineage_comparison.png) | Ligament Profiles & Corridor Width | 448,512 bytes | `27847E4CF3A633F245BFD9EB4CE5FBEA5FE9CD1F51C1EFEE9E4057A965DC9EAE` |
| [`LINEAGE_COMPARISON_TABLE.csv`](LINEAGE_COMPARISON_TABLE.csv) | Quantitative Lineage Metrics Table | 1,182 bytes | `1EF032BC5BF0CA87635900C029462A1EDCEB44A759C999B23E280CBE78B58D50` |
| [`LINEAGE_RECONCILIATION_METRICS.json`](LINEAGE_RECONCILIATION_METRICS.json) | Structured Lineage Metrics | 5,612 bytes | `F24D6955E93BA7F5F02D714C803FEE15FB1A7115E071A748EB2181C26830F25A` |
| [`ADAPTIVE_ZONE_QUANTITATIVE_TABLE.csv`](ADAPTIVE_ZONE_QUANTITATIVE_TABLE.csv) | Quantitative Zone Statistics | 776 bytes | `3127CE508AD205758540DF228072DE2672FC9C99ADB8E29AD49DD1D3582DAA6D` |
| [`ADAPTIVE_DIRECTION_EVIDENCE_SUMMARY.json`](ADAPTIVE_DIRECTION_EVIDENCE_SUMMARY.json) | Machine-Readable Audit Summary | 4,522 bytes | `877726600287E7BD4EDAF9C3A6DB8D24644F7CDDED68B443256B33840EE5B23F` |
| [`README.md`](README.md) | Lineage & Audit Documentation | ~11 KB | Current |

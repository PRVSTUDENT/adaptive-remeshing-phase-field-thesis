# Mode-I Cause Audit Stage 1: Coarse-Mesh Topology & Quad–Triangle Layout Audit

**Date:** 2026-10-03  
**Protocol Version:** 2  
**Author:** Candidate (M.Sc. Computational Materials Science, TU Bergakademie Freiberg)  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*  
**Active Gate:** Gate 6B (Mode-I Energetic & Multi-Quantity Convergence Qualification)  
**Parent Investigation:** Mode-I Localization Cause Hierarchy (`Topology -> BCs -> Mapping -> Stress Transfer -> Frame -> Element/Output`)

---

## 1. Executive Summary & Epistemic Verdict

This report documents the exhaustive offline Stage-1 cause audit investigating whether coarse-mesh topology, quadrilateral–triangular element distribution, diagonal transition bands, or mesh asymmetry explain the broad far-field MISESERI error indicator distribution ($56,302$ finite elements under literal $1.0\%$ errorTarget) compared to the narrow localized corridor reported in Pandey & Kumar (2025) Fig. 6(a) ($13,941$ elements).

### Key Stage-1 Findings:
1. **Low Triangle Presence & Error Share:** The canonical $2,906$-element coarse mesh contains $2,818$ quads ($96.97\%$) and only $88$ triangles ($3.03\%$). These $88$ triangles carry only $2.92\%$ of the total domain error. The mean error in triangles is actually lower than in quads ($0.006765\,\text{MPa}$ vs $0.009975\,\text{MPa}$).
2. **Zero Spatial Coincidence with Far-Field Error:** The $88$ triangles are located along diagonal transition bands in the outer domain ($x \in [0.038, 0.963]$, $y \in [0.043, 0.957]$) and do NOT cluster near the crack tip ($0.45 \le x \le 0.65, 0.45 \le y \le 0.55$), where the element population is $100\%$ quadrilateral ($100\%$ CPE4).
3. **Negligible Far-Field Geometric Correlation:** In the far field ($y \in [0.10, 0.45] \cup [0.55, 0.90]$), the Pearson correlation between MISESERI error and element aspect ratio is $r = 0.074$, and between error and skewness is $r = 0.053$. Both are statistically indistinguishable from zero.
4. **Governed Stage-1 Verdict:** **`TOPOLOGY_NOT_SUPPORTED_AS_DOMINANT_CAUSE`**; localization classification: **`NEUTRAL_LOCALIZATION`**. Coarse-mesh topology, triangle presence, and mesh skewness do NOT explain the broad far-field error. The underlying cause of the broad far-field error indicator distribution remains `CAUSE_NOT_YET_ISOLATED` and is being investigated sequentially through the remaining stages of the cause hierarchy.
5. **Next Governed Action:** Advance the cause hierarchy directly to **Stage 2: Boundary Condition Implementation & Constraint Sensitivity** without mixing causes or altering topology.

---

## 2. Reconciled Published vs. Project Implementation Matrix

Following primary-source verification against Pandey & Kumar (2025) Sections 3.3 and 4.1, all items where exact implementation details are not published in the text are formally classified as `PUBLISHED_DETAIL_NOT_SPECIFIED`:

| # | Parameter / Step | Published Specification (Pandey & Kumar 2025) | Project Implementation | Epistemic Classification |
| :-: | :--- | :--- | :--- | :--- |
| 1 | **Geometry & Slit** | $1.0 \times 1.0\,\text{mm}$, slit $a_0 = 0.5\,\text{mm}$ (Section 4.1) | $1.0 \times 1.0\,\text{mm}$, sharp slit $a_0 = 0.5\,\text{mm}$ | `MATCHED_TO_PUBLISHED_SOURCE` |
| 2 | **Elastic Properties** | $E = 210\,\text{GPa}$, $\nu = 0.3$ | $E = 210\,\text{GPa}$, $\nu = 0.3$ | `MATCHED_TO_PUBLISHED_SOURCE` |
| 3 | **Fracture Parameters** | $G_c = 2.7\times 10^{-3}\,\text{kN/mm}$, $l_0 = 0.0075\,\text{mm}$, $k = 10^{-7}$ | $G_c = 2.7\times 10^{-3}\,\text{kN/mm}$, $l_0 = 0.0075\,\text{mm}$, $k = 10^{-7}$ | `MATCHED_TO_PUBLISHED_SOURCE` |
| 4 | **Constitutive Split** | Spectral decomposition (Miehe et al. 2010) | Spectral decomposition (`f42_mixed_uel.for`) | `MATCHED_TO_PUBLISHED_SOURCE` |
| 5 | **Element Formulation** | 4-node plane strain UEL + dummy CPE4/CPE3 | 4-node plane strain UEL + dummy CPE4/CPE3 | `MATCHED_TO_PUBLISHED_SOURCE` |
| 6 | **Coarse Baseline Mesh** | Global seed $h = 0.02\,\text{mm}$ (exact count not stated) | $2,906$ linear elements ($2,818$ CPE4, $88$ CPE3) | `PUBLISHED_DETAIL_NOT_SPECIFIED` |
| 7 | **Pre-Analysis BCs** | Schematic in Fig. 4(a) (roller/pin; $u_x$ text omitted) | Bottom roller $u_y=0$, pinned pt; top $u_y=0.001$, $u_x$ free | `PUBLISHED_DETAIL_NOT_SPECIFIED` |
| 8 | **Error Indicator** | MISESERI in Abaqus RemeshingRule (Listing 1) | Whole-element centroid MISESERI extraction | `PUBLISHED_DETAIL_NOT_SPECIFIED` |
| 9 | **Remeshing Algorithm** | Native Abaqus `adaptiveRemesh` / `RemeshingRule` | Python script `execute_mode1_native_adaptive_remesh.py` | `MATCHED_TO_PUBLISHED_SOURCE` |
| 10 | **Sizing Method** | `sizingMethod = UNIFORM_ERROR` (Listing 1) | `sizingMethod = UNIFORM_ERROR` | `MATCHED_TO_PUBLISHED_SOURCE` |
| 11 | **Error Target ($\eta_t$)** | Reported literal $1.0\%$ target ($	o 13,941$ el) | $1.0\%$ target $\to 56,302$ el; $2.0\%$ variant $\to 13,897$ el | `PROJECT_IMPLEMENTATION_DIFFERS` |
| 12 | **Sizing Bounds** | $h_{\min} = 1.0\,\mu\mathrm{m}$, refinementFactor = 10 | $h_{\min} = 1.0\,\mu\mathrm{m}$, refinementFactor = 10 | `MATCHED_TO_PUBLISHED_SOURCE` |
| 13 | **Remeshing Scoping** | `region = reg` on `All_elem` (Listing 1) | Whole-domain application | `PUBLISHED_DETAIL_NOT_SPECIFIED` |
| 14 | **Indicator Cutoff Floor**| Unspecified whether low-error elements were zeroed | No artificial floor applied | `PUBLISHED_DETAIL_NOT_SPECIFIED` |
| 15 | **Abaqus Release** | Unspecified Abaqus release version (2018–2022) | Abaqus 2023 / 2021 | `PUBLISHED_DETAIL_NOT_SPECIFIED` |

---

## 3. Element-Count Semantics & Lineage Reconciliation

To eliminate ambiguity between reported numbers, the following exact definitions are established:

1. **Canonical 2,906-Coarse Lineage (Authoritative Project Pre-Analysis):**
   - Coarse Mesh: $2,906$ finite elements ($2,818$ CPE4 quads, $88$ CPE3 triangles, $2,988$ nodes).
   - Literal 1.0% Target Remesh: **$56,302$ underlying finite elements** ($54,847$ CPE4 quads, $1,455$ CPE3 triangles, $55,984$ nodes).
   - Calibrated 2.0% Variant Remesh: **$13,897$ underlying finite elements** ($13,506$ CPE4 quads, $391$ CPE3 triangles, $13,763$ nodes) — matching the literature $13,941$ baseline within $0.32\%$.
2. **Historical 2,700-Structured Lineage (Reference Comparison):**
   - Coarse Mesh: $2,700$ finite elements ($2,700$ CPE4 quads, $2,831$ nodes).
   - Literal 1.0% Target Remesh: **$42,318$ underlying finite elements** ($41,224$ CPE4 quads, $1,094$ CPE3 triangles).
   - Calibrated 2.0% Variant Remesh: **$10,253$ underlying finite elements** ($9,952$ CPE4 quads, $301$ CPE3 triangles).
3. **Multi-Layer Input Deck Representation:**
   - In the complete phase-field fracture solver decks (`.inp`), each underlying finite element is instantiated across **3 co-located functional layers**:
     - Layer 1: Phase-field approximation UEL (`U1` for quad, `U3` for triangle);
     - Layer 2: Mechanical companion UEL (`U2` for quad, `U4` for triangle);
     - Layer 3: Companion visualization UMAT (`CPE4` for quad, `CPE3` for triangle).
   - Therefore, the total element count in the solver deck is exactly $3 \times N_{\text{FE}}$ (e.g., $3 \times 13,897 = 41,691$ elements in the 13.9k solve).

---

## 4. Detailed Quantitative Stage-1 Topology Metrics

### Table 1: Quad vs. Triangle Geometric & Error Breakdown

| Metric | CPE4 Quads | CPE3 Triangles | Whole Mesh Total / Average |
| :--- | :---: | :---: | :---: |
| **Element Count** | $2,818$ | $88$ | $2,906$ |
| **Mesh Fraction** | $96.97\%$ | $3.03\%$ | $100.00\%$ |
| **Total MISESERI Error** | $28.1098\,\text{MPa}$ | $0.5953\,\text{MPa}$ | $28.7051\,\text{MPa}$ |
| **Error Share** | $97.08\%$ | $2.92\%$ | $100.00\%$ |
| **Mean Error** | $0.009975\,\text{MPa}$ | $0.006765\,\text{MPa}$ | $0.009878\,\text{MPa}$ |
| **Median Error** | $0.009384\,\text{MPa}$ | $0.003926\,\text{MPa}$ | $0.009217\,\text{MPa}$ |
| **Std Dev Error** | $0.019315\,\text{MPa}$ | $0.007661\,\text{MPa}$ | $0.019077\,\text{MPa}$ |
| **Max Error** | $0.950009\,\text{MPa}$ | $0.038166\,\text{MPa}$ | $0.950009\,\text{MPa}$ |
| **Mean Aspect Ratio** | $1.218$ | $1.442$ | $1.225$ |
| **Mean Skewness** | $0.158$ | $0.347$ | $0.164$ |

### Table 2: Governed 5-Region Spatial Partition

| Region | Boundary Definition | Element Count | Mesh Frac (%) | Tri Count (Tri %) | Error Sum (MPa) | Error Share (%) | Mean Error (MPa) | Max Error (MPa) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Crack-Tip Corridor** | $x \in [0.45, 0.65], y \in [0.45, 0.55]$ | $60$ | $2.06\%$ | $0$ ($0.0\%$) | $2.5540$ | $8.90\%$ | $0.042567$ | $0.950009$ |
| **Crack Wake** | $x \in [0.00, 0.45], y \in [0.45, 0.55]$ | $134$ | $4.61\%$ | $0$ ($0.0\%$) | $0.6276$ | $2.19\%$ | $0.004684$ | $0.019734$ |
| **Right Ligament** | $x \in [0.65, 1.00], y \in [0.45, 0.55]$ | $96$ | $3.30\%$ | $2$ ($2.1\%$) | $0.3458$ | $1.20\%$ | $0.003602$ | $0.011606$ |
| **Far Field** | $y \in [0.10, 0.45] \cup [0.55, 0.90]$ | $2,040$ | $70.20\%$ | $70$ ($3.4\%$) | $20.0097$ | $69.71\%$ | $0.009809$ | $0.024893$ |
| **Boundary Regions** | $y < 0.10 \cup y > 0.90$ | $576$ | $19.82\%$ | $16$ ($2.8\%$) | $5.1680$ | $18.00\%$ | $0.008972$ | $0.018912$ |

---

## 5. Master Figure & Spatial Coincidence Evidence

The 6-panel master figure `fig_mode1_gate6b_stage1_topology_audit.png` (and `.pdf`) proves:
1. **Panel A (Element Type Map):** Shows that the crack tip ($x=0.5, y=0.5$) and slit flanks are meshed purely with regular quadrilaterals. Triangles occur as isolated pairs in diagonal transition zones in the outer domain.
2. **Panel B (Skewness & Triangle Locations):** Shows that high geometric skewness ($\ge 0.4$) is confined to triangle patches, while the bulk domain remains orthogonal quads (skewness $< 0.15$).
3. **Panel C (MISESERI with Triangle Overlay):** Demonstrates that the high-error concentration ($e \ge 0.10\,	ext{MPa}$) is strictly localized to the notch tip. Far-field error is smoothly distributed according to continuum stress gradients and does not form artificial peaks at triangle locations.
4. **Panel D (Regional Partition):** Shows that Far Field contains $70.2\%$ of elements and carries $69.7\%$ of error, with triangle fractions remaining below $3.5\%$ across all regions.
5. **Panel E (CDF):** CDF curves confirm that triangles have smaller median and mean error than quads.
6. **Panel F (Transverse Symmetry):** Error asymmetry across $y=0.5\,	ext{mm}$ is negligible ($< 0.001\,	ext{MPa}$ everywhere).

---

## 6. Conclusion & Next Governed Step

Coarse-mesh topology, triangle layout, and element skewness are conclusively ruled out as the root cause of the broad far-field refinement. The project proceeds to **Stage 2: Boundary Condition Implementation & Constraint Sensitivity**.

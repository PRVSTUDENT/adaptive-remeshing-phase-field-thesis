# Gate-5 Coarse Pre-Analysis Source Provenance & MISESERI Dataset Reconciliation

**Document Reference:** `GATE5_SOURCE_PREANALYSIS_PROVENANCE_RECONCILIATION.md`  
**Date:** September 14, 2026  
**Status:** `AUTHORITATIVE_SOURCE_PROVENANCE_VERIFIED`  
**Core Purpose:** Resolve the provenance distinction between the historical 3,930-row `MISESERI` CSV and the canonical 2,906-element Mode-I pre-analysis mesh, establishing exact physical and algorithmic identity from raw primary evidence.

---

## 1. Executive Summary & Provenance Resolution

1. **Source of 3,930-Row CSV (Job `1379893.mmaster02`, `M2MISER1`):**
   - Belongs strictly to the **Stage-F4 Mode-II shear benchmark pre-analysis**, where an asymmetric shear specimen geometry was discretized with **$3,930$ finite elements**.
   - An extraction script recorded 1 value per finite element, producing the $3,930$-row CSV (SHA-256 `49b0c5f7a784f361...`).
   - In early report drafts (September 1, 2026), this Mode-II dataset was used to generate an illustrative Figure 3.1 error contour, creating subsequent confusion in Mode-I documentation.
   - **Correction:** The $3,930$ dataset is NOT the Mode-I pre-analysis mesh and NOT a Molnár benchmark; it is the historical Mode-II shear pre-analysis.

2. **Source of Canonical Mode-I Pre-Analysis (2,906 Elements):**
   - In strict fidelity to Pandey & Kumar (2025, Section 4.1, p. 3265), the Mode-I square plate ($1.0 \times 1.0\,\text{mm}$, seam $a_0 = 0.5\,\text{mm}$) is seeded globally at $h_{\text{cms}} = 0.02\,\text{mm}$.
   - Standard Abaqus CAE meshing generates exactly **$2,906$ finite elements ($2,818$ CPE4 quads $+ 88$ CPE3 triangles) and $2,988$ mesh nodes**.
   - In the resulting pre-analysis ODB (`DEBUG_PRE.odb` / `JOB1_CPE4_1PCT.odb`), `frame.fieldOutputs['MISESERI']` contains exactly **$2,906$ values** ($1$ scalar error value per element at location `WHOLE_ELEMENT`).
   - Sizing range: $\min = 1.4052 \times 10^{-4}\,\text{kN/mm}^2$, $\text{median} = 5.7808 \times 10^{-3}\,\text{kN/mm}^2$, $\max = 1.007057\,\text{kN/mm}^2$.

3. **Resolution of the "5,812 Values" Hypothesis:**
   - Raw ODB inspection confirms that `len(fo.values) = 2,906`, exactly matching the element count with distribution `{1: 2906}`. The previous 5,812 figure was a speculative multiplicity hypothesis and is formally retired.

4. **Refined Mesh Outcome:**
   - Executing the literal published RemeshingRule (Listing 1: `errorTarget=1.0`, $h_{\min}=0.001$, $h_{\max}=0.020$, `refinementFactor=10`, `coarseningFactor=NOT_ALLOWED`) on the 2,906-element canonical pre-analysis generates exactly **$71,320$ finite elements and $70,845$ nodes**, invariant across Abaqus 2019, 2021, 2022, and 2023.

---

## 2. Comprehensive Provenance Reconciliation Table

| Artifact | Benchmark | Job / PBS ID | Source Mesh Elements | Element Formulation | MISESERI Value Count | Output Position | Step / Frame | Extractor | Raw SHA-256 / File Hash | Evidence Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `miseseri_preanalysis_elements.csv` | Mode-II Shear Pre-Analysis (Stage F4) | `1379893.mmaster02` (`M2MISER1`) | $3,930$ finite elements | Co-located UEL + UMAT (`CPE4`/`CPE3` facsimile) | $3,930$ values ($1$ / element) | `WHOLE_ELEMENT` | `Step-1`, Frame 10 ($u_1 = 0.0010\,\text{mm}$) | PBS Python Exporter | CSV: `49b0c5f7a784f361...`<br>ODB: `bfcdbec08669774a...` | `HISTORICAL_MODE_II_SHEAR_EVIDENCE` (Preserved in `runs/stage_f4/`) |
| `DEBUG_PRE.odb` / `JOB1_CPE4_1PCT.odb` | Mode-I Tensile Pre-Analysis ($1.0 \times 1.0\,\text{mm}$, $a_0 = 0.5\,\text{mm}$) | `1404373` (2022/2023), `1404968` (2021), `1405052` / Native 2019 | $2,906$ finite elements ($2,818$ CPE4 + $88$ CPE3, $2,988$ nodes) | Linear Elastic Continuum Plane Strain (`CPE4` + `CPE3`) | $2,906$ values ($1$ / element) | `WHOLE_ELEMENT` | `Step-1`, Frame 10 ($u_2 = 0.0050\,\text{mm}$) | Native Abaqus CAE / `odbAccess` | ODB: `5427660` bytes<br>Coord: `5e16c65397e57e30...`<br>Conn: `f86dd0165c0a782c...` | `AUTHORITATIVE_CANONICAL_MODE1_PREANALYSIS` (100% publication faithful) |
| `JOB2_REFINED_CPE4_1PCT.inp` | Mode-I Adapted Mesh Reconstruction (Nominal 1.0%) | `1404373` (2022/2023), `1404968` (2021), Native 2019 GA | Derived from $2,906$-element pre-analysis | Linear Elastic Continuum Plane Strain (`CPE4` + `CPE3`) | N/A (`adaptiveRemesh`) | N/A | N/A | Abaqus CAE `Job.writeInput()` | Substantive Lines: $142,268$<br>Node Coord: `116f2e2042afddf8...`<br>Conn: `3077676490a5457c...` | `AUTHORITATIVE_REFINED_MESH_VERIFIED` ($71,320$ el: $69,443$ CPE4 + $1,877$ CPE3, $70,845$ nodes) |

---

## 3. Publication Workflow Single-Pass Evidence

Pandey & Kumar (2025) explicitly define their framework as a **single-pass pre-refinement** before the phase-field fracture simulation:
1. **Abstract (p. 3251):** *"The proposed Python-based framework integrates the preanalysis, sufficient mesh refinement, and subsequent phase-field model-based numerical analysis with user-defined subroutines in a single streamlined pass."*
2. **Section 3.1 (p. 3261):** *"The mesh refinement consists of two simultaneous steps: first reporting the error indicator as field output variables (from step I to step II in Fig. 2) and then remeshing the designated regions so the error estimate is within the tolerance limit."*
3. **Section 4.1 (p. 3265):** *"The specimen is initially discretized with a global mesh size of 0.02 mm without local mesh refinement. A remeshing rule that governs the remesh region and global and local mesh size is established based on the MISESERI error indicator in the Abaqus utility for the whole specimen using Python scripting... The adaptive remesh is then incorporated with a global mesh size of 0.02 mm and locally refined mesh size $h = 0.001\,\text{mm}$, comprising 13,941 linear quadratic and triangular elements..."*

**Epistemic Conclusion:** There is zero textual or algorithmic basis in the publication for an iterative multi-pass remeshing loop during the fracture step. The $\approx 13,941$ element count is the direct result of the single pre-refinement step on the coarse model.

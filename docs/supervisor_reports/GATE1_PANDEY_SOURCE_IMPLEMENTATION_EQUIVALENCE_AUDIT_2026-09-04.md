# Gate 1 Source-to-Implementation Equivalence Audit: Pandey & Kumar (2025) vs. Local Abaqus Models (Jobs 1398090, 1401091, 1401159)

**Document Identifier:** `docs/supervisor_reports/GATE1_PANDEY_SOURCE_IMPLEMENTATION_EQUIVALENCE_AUDIT_2026-09-04.md`  
**Audit Date:** 2026-09-04  
**Audit Scope:** Comprehensive Source-to-Code Equivalence Audit of Mode-I Standard PFM Benchmark across All Local Implementations & Conventional Mesh Convergence Inventory  
**Primary Published Paper:** Pandey, P., & Kumar, S. (2025). *Adaptive Finite Element Phase-Field Modeling of Brittle Fracture Using Error Indicator Approach*. Computer Modeling in Engineering & Sciences (CMES), Vol. 144, No. 3, pp. 3251–3276. DOI: `10.32604/cmes.2025.067858` (`Literature review/TSP_CMES_67858.pdf`)  
**Secondary Foundation Source:** Molnár, G., & Gravouil, A. (2017). *2D and 3D Abaqus implementation of a robust staggered phase-field solution for modeling brittle fracture*. Finite Elements in Analysis and Design, Vol. 130, pp. 27–38. (`Literature review/Gergely Molnár⁎.pdf`)  
**Local Evaluated Conventional Cases:**
1. **Job `1398090.mmaster02`:** Clamped-top ($u_x = 0$), isotropic degradation, structured mesh ($15{,}192$ quads), $F_{\max} = 0.757778\,\mathrm{kN}, u = 0.005857\,\mathrm{mm}, K_0 = 137.945520\,\mathrm{kN/mm}$. (**Authoritative Project Fixed-Mesh Anchor**)
2. **Job `1401091.mmaster02`:** Free-top (roller $u_x$ free), isotropic degradation, structured mesh ($15{,}192$ quads), $F_{\max} = 0.764998\,\mathrm{kN}, u = 0.006072\,\mathrm{mm}, K_0 = 134.4610\,\mathrm{kN/mm}$. (**Harmonized Boundary Case**)
3. **Job `1401159.mmaster02`:** Free-top (roller $u_x$ free), Miehe spectral split, structured mesh ($15{,}192$ quads), $F_{\max} = 0.777126\,\mathrm{kN}, u = 0.006098\,\mathrm{mm}, K_0 = 134.4713\,\mathrm{kN/mm}$. (**Spectral Diagnostic Case**)
**Governing Literature Reference Target:** $\sim 0.758\,\mathrm{kN}$ at $\sim 0.005860\,\mathrm{mm}$ (`GOVERNING_PROJECT_REFERENCE_PENDING_RECONCILIATION`, Pandey & Kumar, 2025, Fig. 7(a))  
**New Conflicting Digitization Status:** `NEW_CONFLICTING_DIGITIZATION` (Standard PFM: $0.7348\,\mathrm{kN}$; Proposed PFM: $0.7205\,\mathrm{kN}$; Raster Upper Limit: $0.7424\,\mathrm{kN}$)  
**Governing Supervisor Rule:** *"We need to have understood everything related to the first model before we increase complexity."*  
**Gate 1 Status:** `OPEN_PENDING_SUPERVISOR_DETERMINATION`

---

## 1. Executive Summary & Epistemic Grounding

This audit establishes a rigorous, item-by-item comparison between the primary literature specification for the Mode-I benchmark (**Pandey & Kumar, 2025**) and all existing local conventional finite element implementations.

### Epistemic Classification Scheme:
- **`PAPER_EXPLICIT`**: Directly and unambiguously stated in the publication text, tables, or governing equations.
- **`FIGURE_CONSISTENT_BUT_NOT_EXPLICIT`**: Deduced from published schematics/drawings but omitted from the explicit text.
- **`LOCAL_IMPLEMENTATION_VERIFIED`**: Verified in the local Fortran source, Abaqus input deck, or solver output.
- **`UNPUBLISHED/UNRESOLVED`**: Not specified, documented, or resolved in the primary literature.
- **`CONSISTENT_WITH_COMPENSATING_EFFECTS_NOT_CAUSALLY_ISOLATED`**: Observed data trends match a multi-factor hypothesis, but the full factorial design required to mathematically isolate interactions is incomplete.

---

## 2. Item-by-Item Source-to-Model Equivalence Matrix

```text
================================================================================================================================================================================
ITEM / DIMENSION              PRIMARY PAPER (PANDEY 2025)             JOB 1398090 (ANCHOR)      JOB 1401091 (ISOTROPIC)   JOB 1401159 (SPECTRAL)    EPISTEMIC CLASSIFICATION
================================================================================================================================================================================
1. Geometry                   Omega = 1.0 x 1.0 mm square plate       1.0 x 1.0 mm square plate 1.0 x 1.0 mm square plate 1.0 x 1.0 mm square plate PAPER_EXPLICIT / VERIFIED
2. Crack Representation       Edge crack a_0 = 0.5 mm at y=0.5 mm     Zero-gap seam (90 nodes)  Zero-gap seam (90 nodes)  Zero-gap seam (90 nodes)  FIGURE_CONSISTENT_BUT_NOT_EXPLICIT
   - Exact FE Construction    Text does not specify seam/duplicate    45 duplicate node pairs   45 duplicate node pairs   45 duplicate node pairs   UNPUBLISHED/UNRESOLVED
3. Bottom Boundary Condition  Bottom y fixed (u_y=0); origin pinned   Bottom u_y=0; origin pinned Bottom u_y=0; origin pinned Bottom u_y=0; origin pinned PAPER_EXPLICIT / VERIFIED
4. Top Boundary Condition     Prescribed u_y; no lateral symbol       Top u_x=0 (clamped)       Top u_x free (roller)     Top u_x free (roller)     FIGURE_CONSISTENT_BUT_NOT_EXPLICIT
5. Kinematic Stress State     NOT STATED in text (neither CPS nor CPE) 2D Plane Strain (CPE4)    2D Plane Strain (CPE4)    2D Plane Strain (CPE4)    UNPUBLISHED/UNRESOLVED
6. Mesh Density & Topology    26,282 mixed quad/tri elements          15,192 pure quad elements 15,192 pure quad elements 15,192 pure quad elements PAPER_EXPLICIT / TOPOLOGY_DIFF
   - Corridor Resolution h    h = 0.003 mm (Section 4.1, Table 2)     h = 0.00286 - 0.00301 mm  h = 0.00286 - 0.00301 mm  h = 0.00286 - 0.00301 mm  PAPER_EXPLICIT / VERIFIED
7. Prescribed Loading Steps   Step 1: u=0.005 mm; Step 2: u=0.010 mm  Step 1: 2000 incs fixed   Step 1: 2000 incs fixed   Step 1: 2000 incs fixed   PAPER_EXPLICIT / VERIFIED
   - Exact Tabular Schedule   "Tabular amplitudes" (table unprinted)  Fixed dt=5e-4 / 2e-4      Fixed dt=5e-4, auto S2    Fixed dt=5e-4, auto S2    UNPUBLISHED/UNRESOLVED
8. Energy Decomposition       Miehe anisotropic spectral split [32]   Isotropic degradation     Isotropic degradation     Miehe spectral split [32] PAPER_EXPLICIT / VERIFIED
9. Elastic Constants          E = 210 GPa, nu = 0.3                   E = 210 kN/mm^2, nu = 0.3 E = 210 kN/mm^2, nu = 0.3 E = 210 kN/mm^2, nu = 0.3 PAPER_EXPLICIT / VERIFIED
10. Fracture Parameters       G_c = 2.7 N/mm, l_0 = 0.0075 mm         G_c = 2.7e-3, l_0=0.0075  G_c = 2.7e-3, l_0=0.0075  G_c = 2.7e-3, l_0=0.0075  PAPER_EXPLICIT / VERIFIED
11. Residual Stiffness k      Published range k in [10^-7, 10^-11]    k = 1.0e-7 (PROPS(5))     k = 1.0e-7 (PROPS(5))     k = 1.0e-7 (PROPS(5))     WITHIN_PUBLISHED_RANGE
12. Degradation Function      Quadratic g(d) = (1-d)^2 + k            g(d) = (1-d)^2 + k        g(d) = (1-d)^2 + k        g(d) = (1-d)^2 + k        PAPER_EXPLICIT / VERIFIED
13. Damage Irreversibility    Strain history H = max_t (psi_0^+)      H = max(H_old, POS_M)     H = max(H_old, POS_M)     H = max(H_old, PSI_PLUS)  PAPER_EXPLICIT / VERIFIED
14. Phase-Field Integration   Standard AT2; integration details omit  Element-average D_AVG     Element-average D_AVG     Element-average D_AVG     UNPUBLISHED/UNRESOLVED
15. Solution Strategy         Staggered alternate minimization [72]   Block-diagonal *Static    Block-diagonal *Static    Block-diagonal *Static    PAPER_EXPLICIT / ARCH_DIFF
16. Solver Controls           NOT DISCLOSED in publication            Default Abaqus/Standard   Default Abaqus/Standard   Default Abaqus/Standard   UNPUBLISHED/UNRESOLVED
================================================================================================================================================================================
```

---

## 3. Closeness Ranking: Which Model is Closest to the Published Formulation?

### Finding: Job 1401159 (`PK_M1_SPEC_S`) is Mathematically and Physically Closest to the Published Paper
1. **Energy Decomposition Equivalence:**
   Pandey & Kumar explicitly state in Section 4.1 (p. 3264): *"To simulate this problem, the anisotropic strain energy decomposition of Miehe et al. [32] with staggered implementation [72] in Abaqus is considered."*  
   - Jobs 1398090 and 1401091 used an un-split isotropic degradation formulation.
   - **Job 1401159 is the only local model that implements the true Miehe anisotropic spectral decomposition**.

2. **Boundary Condition Equivalence:**
   Fig. 4(a) depicts the top boundary with an upward arrow without horizontal restraint symbols.
   - Job 1398090 applied an artificial lateral constraint ($u_x = 0$).
   - **Jobs 1401091 and 1401159 implement the unconstrained roller top ($u_x$ free)**, matching the physical benchmark intent.

3. **Material, Geometric, and Variational Equivalence:**
   Job 1401159 matches geometry ($1\times 1\,\mathrm{mm}$), seam length ($a_0 = 0.5\,\mathrm{mm}$), material parameters ($E=210\,\mathrm{GPa}, \nu=0.3$), fracture properties ($G_c=2.7\,\mathrm{N/mm}, l_0=7.5\,\mu\mathrm{m}$), residual stiffness ($k=10^{-7} \in [10^{-7}, 10^{-11}]$), and quadratic AT2 formulation.

---

## 4. Status of the Historical $\sim 0.758\,\mathrm{kN}$ Anchor: Compensating Effects Analysis

```text
========================================================================================================================
MODEL / CONFIGURATION             TOP BC       ENERGY FORMULATION   K_0 [kN/mm]   F_max [kN]   u(F_max) [mm]  EXIT STATUS
========================================================================================================================
Job 1398090 (Fixed Anchor)        u_x = 0      Isotropic            137.9455      0.757778     0.005857       Exit 0 (7000 incs)
Job 1401091 (Harmonized Isotropic) u_x free     Isotropic            134.4610      0.764998     0.006072       Exit 1 (6297 incs)
Job 1401159 (Harmonized Spectral)  u_x free     Miehe Spectral       134.4713      0.777126     0.006098       Exit 1 (3124 incs)
[4th Cell: Clamped + Spectral]    u_x = 0      Miehe Spectral       -- NOT RUN -- -- NOT RUN -- -- NOT RUN --   MISSING CELL
Nominal Literature Target         u_x free(?)  Miehe Spectral(?)    ~138.0(?)     ~0.7580      ~0.005860      Published Target
Re-digitized Standard PFM         u_x free(?)  Miehe Spectral(?)    ~134.5        0.734831     0.005743       Raster Fig. 7(a)
========================================================================================================================
```

### Epistemic Classification of Anchor Discrepancy:
- In Job 1398090, clamping the top edge ($u_x = 0$) increased initial stiffness by $+2.59\%$ ($137.95\,\mathrm{kN/mm}$ vs $134.46\,\mathrm{kN/mm}$) and shifted peak displacement from $0.006072\,\mathrm{mm}$ down to $0.005857\,\mathrm{mm}$. Concurrently, isotropic degradation lowered the peak load relative to the spectral formulation ($0.7650\,\mathrm{kN}$ vs $0.7771\,\mathrm{kN}$).
- While these two opposing trends are consistent with compensating effects, the full $2 \times 2$ factorial matrix (BC $\times$ Formulation) is incomplete because the clamped-top + spectral cell was never executed.
- Therefore, in strict compliance with epistemic governance, this mechanism is classified as:  
  **`CONSISTENT_WITH_COMPENSATING_EFFECTS_NOT_CAUSALLY_ISOLATED`**.

---

## 5. Conventional Fixed-Mesh Convergence Inventory

An exhaustive repository search across all historical runs and directories was conducted to inventory all existing Mode-I conventional fixed-mesh resolution evidence:

```text
=============================================================================================================================================================================
JOB ID / RUN IDENTIFIER   MESH TYPE / RESOLUTION     BC / SPLIT TYPE      F_max [kN]  u_peak [mm]  K_0 [kN/mm]  POST-PEAK COVERAGE   UEL ENERGY STATUS  COMPUTATIONAL COST
=============================================================================================================================================================================
1398090.mmaster02         15,192 quad (h = 0.003 mm) Clamped / Isotropic  0.757778    0.005857     137.9455     99.9694% drop        NOT POPULATED      7000 incs, 06:31:14 (Wall)
1401091.mmaster02         15,192 quad (h = 0.003 mm) Roller / Isotropic   0.764998    0.006072     134.4610     99.9639% drop        NOT POPULATED      6297 incs, 05:58:23 (Wall)
1401159.mmaster02         15,192 quad (h = 0.003 mm) Roller / Spectral    0.777126    0.006098     134.4713      3.6382% drop        NOT POPULATED      3124 incs, 02:49:56 (Wall)
=============================================================================================================================================================================
```

### Audit Assessment of Gate-1 Conventional Mesh-Convergence Basis:
1. **Identical Mesh Topology Across All Conventional Runs:** All three existing conventional fixed-mesh runs share the **single identical $15{,}192$-element mesh ($h = 0.003\,\mathrm{mm}$)**.
2. **Spatial Mesh-Convergence Status:** A conventional fixed-mesh spatial convergence series (e.g. demonstrating that $h = 0.003\,\mathrm{mm}$ is spatially converged against a finer fixed mesh $h = 0.001\text{--}0.0015\,\mathrm{mm}$) **does NOT exist in the repository**.
3. **Single Missing Comparison Identified:** To formally establish a complete conventional fixed-mesh convergence study under Gate 1, a **finer fixed-mesh conventional solve ($h \approx 0.001\text{--}0.0015\,\mathrm{mm}$ along the crack corridor)** under the harmonized boundary condition would be required. In strict adherence to rules, this is **identified and documented**, but **NOT created or submitted**.

---

## 6. Fig. 7(a) Digitization Provenance & Unresolved Status

```text
====================================================================================================================================================
DATASET IDENTIFIER                EXTRACTION METHOD            LEGEND MAPPING         PEAK FORCE (F_peak)  PEAK DISP (u_peak)   STATUS
====================================================================================================================================================
Governing Literature Target       Draft reports / prompt       Fixed baseline anchor  ~0.758 kN            ~0.005860 mm         GOVERNING_PROJECT_REFERENCE_PENDING_RECONCILIATION
Job 1398090.mmaster02 (Abaqus)    Solver dat extraction        Top u_x = 0 (clamped)  0.757778 kN          0.005857 mm          AUTHORITATIVE_PROJECT_FIXED_MESH_ANCHOR
Job 1401091.mmaster02 (Abaqus)    Solver dat extraction        Roller top (u_x free)  0.764998 kN          0.006072 mm          HARMONIZED_ISOTROPIC_EVALUATION
Job 1401159.mmaster02 (Abaqus)    Solver dat extraction        Roller top (u_x free)  0.777126 kN          0.006098 mm          HARMONIZED_SPECTRAL_EVALUATION
New Digitization: Standard PFM    Uncompressed raster (xref)   Blue dashed line (--)  0.734831 kN          0.005743 mm          NEW_CONFLICTING_DIGITIZATION
New Digitization: Proposed PFM    Uncompressed raster (xref)   Red solid line (—)     0.720506 kN          0.005628 mm          NEW_CONFLICTING_DIGITIZATION
Raster Envelope Upper Limit       Uncompressed raster (xref)   Peak colored pixel     0.742416 kN          0.005824 mm          NEW_CONFLICTING_DIGITIZATION
====================================================================================================================================================
```

*Reconciliation Status:* The historical target ($\sim 0.758\,\mathrm{kN}$) and direct raster digitization ($0.7348\,\mathrm{kN}$) remain preserved as **`UNRESOLVED_DIGITIZATION_CONFLICT`** pending supervisor determination.

---

## 7. Scientific Epistemology: VERIFIED vs UNRESOLVED Findings

### 7.1 VERIFIED Findings (Defensible Facts):
1. **Three-Tier Conventional Model Hierarchy:**
   - Job 1398090: Clamped-top, isotropic baseline ($F_{\max} = 0.7578\,\mathrm{kN}, K_0 = 137.9455\,\mathrm{kN/mm}$).
   - Job 1401091: Roller-top, isotropic baseline ($F_{\max} = 0.7650\,\mathrm{kN}, K_0 = 134.461\,\mathrm{kN/mm}$).
   - Job 1401159: Roller-top, Miehe spectral split ($F_{\max} = 0.7771\,\mathrm{kN}, K_0 = 134.471\,\mathrm{kN/mm}$).
2. **Closeness Ranking:** Job 1401159 is mathematically and physically closest to the published formulation of Pandey & Kumar (2025).
3. **Data Availability Boundary:** Full spatial fields $d(\mathbf{x})$, $\mathcal{H}(\mathbf{x})$, and $\psi^+(\mathbf{x})$ were not written to the ODB files (only node 999999 was requested for `U` and `RF`), and UEL internal energy arrays are not populated by Abaqus.
4. **Governing Anchor Preserved:** Job 1398090 remains the project fixed-mesh anchor unless modified by supervisor decision.

### 7.2 UNRESOLVED Findings (Open Scientific Questions):
1. **Literature Target Reconciliation:** Whether the true physical reference in Pandey & Kumar Fig. 7(a) is $\sim 0.758\,\mathrm{kN}$ or $0.7348\,\mathrm{kN}$ remains an open question (`UNRESOLVED_DIGITIZATION_CONFLICT`).
2. **Compensating Effects Proof Status:** The cancellation mechanism in Job 1398090 is `CONSISTENT_WITH_COMPENSATING_EFFECTS_NOT_CAUSALLY_ISOLATED` due to the missing clamped + spectral cell.
3. **Conventional Fixed-Mesh Convergence Basis:** No multi-resolution fixed-mesh study exists locally to prove spatial convergence of the $15{,}192$-element mesh.

---

## 8. Gate-1 Status

- **Gate 1 Status:** **`OPEN_PENDING_SUPERVISOR_DETERMINATION`**
- All 3 local models (1398090, 1401091, 1401159) are audited, documented, and cross-compared against published literature.

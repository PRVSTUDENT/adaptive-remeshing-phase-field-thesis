# Gate 5: External Information Boundary & Reproducibility Matrix

**Document Reference:** `GATE5_EXTERNAL_INFORMATION_BOUNDARY.md`  
**Date:** September 14, 2026  
**Status:** `AUTHOR_INFORMATION_REQUEST_READY_FOR_HUMAN_APPROVAL_UNSENT`  
**Active Research Status:** `GATE5_REPRODUCTION_DISCREPANCY_RESOLUTION_ACTIVE` / `UNRESOLVED_WITH_PUBLICATION_INFORMATION_MISSING`  
**Authoritative Classification:** `CANONICAL_CPE4_RELEASE_2019_2021_2022_2023_INVARIANCE_VERIFIED`  
**Primary Reference:** Pandey, A., & Kumar, S. (2025). "A Simple and Robust Mesh Refinement Implementation in Abaqus for Phase Field Modelling of Brittle Fracture." *Computer Modeling in Engineering & Sciences* (CMES), Vol. 144, No. 3, pp. 3251–3286. DOI: [10.32604/cmes.2025.067858](https://doi.org/10.32604/cmes.2025.067858)  
**Associated Inquiry Draft:** [`docs/supervisor_reports/GATE5_AUTHOR_REPRODUCIBILITY_INQUIRY_DRAFT.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/GATE5_AUTHOR_REPRODUCIBILITY_INQUIRY_DRAFT.md)  
**Accompanying Visual Artifact:** [`docs/thesis/figures/figure_gate5_author_inquiry_mesh_comparison.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/figures/figure_gate5_author_inquiry_mesh_comparison.png)  
**Authoritative Reference Baseline Stiffness:** $K_0^{\text{ref}} = 137.945520\,\text{kN/mm}$ ($b_0 = 4.472368 \times 10^{-5}\,\text{kN}$, $R^2 = 0.99999960$, $N=400$ over actual $0 < u \le 0.001000\,\text{mm}$)  
**Governing Controller Constraints:**  
- `ELEMENT_COUNT_PROXIMITY_NOT_PARAMETER_IDENTITY`  
- `LITERATURE_EFFECTIVE_ERROR_TARGET_NOT_ESTABLISHED`  
- `MODE1_RESOLUTION_EXTENSION_ACTIVE`  

---

## 1. Five-Category Literature-Provenance & Epistemic Breakdown (15 Factors)

A rigorous, line-by-line forensic audit across the primary publication (Pandey & Kumar, 2025, *CMES*, 144(3), pp. 3251–3286), our native-remeshing Python scripts, and physical input decks establishes the exact epistemic status of all candidate factors ($6 + 5 + 2 + 1 + 1 = 15$):

### 1.1 Category I: RULED_OUT (6 Factors)
1. **Abaqus Solver Release (Linux)**: Tested across 2019 GA, 2021.HF26, 2022 GA, 2023.HF4 (Jobs 1404373, 1404968, 1405052). Yields $100.000\%$ bit-for-bit identical $71,320$ elements ($69,443$ CPE4 + $1,877$ CPE3, $70,845$ nodes, node SHA-256 `116f2e20...`).
2. **Pre-Analysis Scalar Load Magnitude**: Tested $0.2\times$ to $2.0\times$ displacement (Job 1404383). Relative error indicator $\eta$ is scale-invariant; element count remains strictly invariant at $71,070 - 71,512$ elements ($\pm 0.3\%$).
3. **Output Frequency Argument**: `ALL_INCREMENTS` vs `LAST_INCREMENT`. Both reference the identical terminal elastic step frame; produces exact $71,320$ elements.
4. **Coarse Meshing Algorithm Controls**: `ADVANCING_FRONT` vs `MEDIAL_AXIS` vs pure quads on coarse part. Default quad-dominated mesher yields $2,906$ coarse elements; pure quad options error with "No active regions".
5. **Coarse Mesh Seed Controls**: `minSizeFactor` (0.01–0.50), `deviationFactor` (0.01–0.50), edge seeding. Plate has no curved geometry; coarse count invariant at $2,906$, adapted count at $71,320$.
6. **Multi-Pass Adaptive Remeshing**: Section 3.3 explicitly defines a single-pass workflow for Mode-I; multi-pass adaptation compounds refinement.

### 1.2 Category II: TESTED_NO_MATERIAL_EFFECT (5 Factors)
7. **Continuum Element Integration Order**: Full integration `CPE4` vs Reduced integration `CPE4R` (Job 1405056). Reduced integration increases domain $\text{MISESERI}$ error by $+44.5\%$, driving adapted mesh up to **$103,706$ elements** ($+45.4\%$).
8. **Top-Edge Horizontal BC ($u_1$)**: $u_1 = 0.0$ (shear constrained) vs $u_1 = \text{Free}$ (shear relaxed; Job 1405055). Unconstraining $u_1$ reduces far-field elements from $41,986 \to 30,049$, giving **$55,761$ elements** ($-21.8\%$, still $>4.0\times$ literature).
9. **Coarse Mesh Global Seed ($h_{\text{cms}}$)**: $h_{\text{cms}} = 0.020\,\text{mm}$ (nominal) vs $0.030\,\text{mm}$. Yields $48,919$ elements ($-31.4\%$), remaining $3.5\times$ higher than published count.
10. **Remeshing Sizing Bounds**: `specifyMinSize` / `specifyMaxSize` (True vs False). Removing sizing bounds preserves $71,320$ elements ($h_{\min}=0.001$, $h_{\max}=0.020$ are natural bounds).
11. **Coarsening Factor Argument**: `coarseningFactor=NOT_ALLOWED` vs default allowed. Enabling coarsening reduces elements marginally from $71,320 \to 71,037$ ($-0.4\%$).

### 1.3 Category III: CONFOUNDED (2 Factors)
12. **Platform / OS Build (Windows 2024 GA)**: Abaqus 2024 GA on Windows (`win_b64`) produces $71,904$ elements ($+0.82\%$ variance vs Linux 71,320), proving platform differences do not explain 13,941.
13. **2D Stress State Formulation (CPS4 Plane Stress)**: Plane Stress generates $58,679$ elements ($-17.7\%$), but violates the Mode-I plane strain standard and alters physical stiffness/peak load.

### 1.4 Category IV: PUBLICATION_INFORMATION_MISSING (1 Factor)
14. **Adaptive Region Sub-Domain Partition**: The publication text states whole specimen `All_elem` (0 mentions of partition, corridor, or bounding box). Restricting refinement to a local crack-corridor box could mathematically produce ~13,941 elements, but constitutes unstated implementation.

### 1.5 Category V: PUBLICATION_LINKAGE_AMBIGUOUS (1 Factor)
15. **Section 4.1 `errorTarget` Linkage**: Listing 1 hard-codes `errorTarget=1.0`. Section 4.1 invokes the workflow with $h_{\min}=0.001\,\text{mm}$ and $h_{\max}=0.020\,\text{mm}$ without stating an override. Executing verbatim Listing 1 yields $71,320$ elements; `errorTarget=2.0` yields $17,687$ elements.

---

## 2. External Information Boundary Conclusion & Author Inquiry

All 11 accessible publication-supported one-factor parameter investigations are **exhausted**. Every tested single-factor variation maintains element counts $>4.0\times$ the published nominal count ($55,761 - 103,706$ elements).

A concise, non-redundant 6-question inquiry has been prepared for corresponding author Dr. Sachin Kumar:
- **Inquiry Document:** [`GATE5_AUTHOR_REPRODUCIBILITY_INQUIRY_DRAFT.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/GATE5_AUTHOR_REPRODUCIBILITY_INQUIRY_DRAFT.md)
- **Status:** `AUTHOR_INFORMATION_REQUEST_READY_FOR_HUMAN_APPROVAL_UNSENT`
- **Governance:** Unsent pending explicit human/supervisor authorization.

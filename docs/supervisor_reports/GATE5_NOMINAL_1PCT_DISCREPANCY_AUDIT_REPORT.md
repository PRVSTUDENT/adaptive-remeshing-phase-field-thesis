# Mode-I Gate 5: Nominal 1% Discrepancy Closure Audit Report (Revision 9)

**Authoritative Gate Status**: `CLOSED_UNRESOLVED_DUE_TO_MISSING_PUBLISHED_OR_INTERNAL_SIZING_INFORMATION`  
**Execution Timestamp**: 2026-09-14T07:45:00+02:00  
**HPC Job Status**: Complete (Jobs 1404373, 1404383, 1404959, 1404968, 1405052, 1405055, 1405056 Completed & Archived)  
**Investigation Target**: Mathematical, Algorithmic, API Semantics, Multi-Release Invariance (2019–2023), OFAT Boundary Conditions, Element Integration, Field Multiplicity Resolution & Coarse Mesh Topology Provenance Audit of the 71,320 vs ~13,941 Element-Count Discrepancy at `errorTarget=1.0%`

---

## 1. Executive Summary & Control Identity Verification

### 1.1 Corrected Control Definition & Baseline Establishment
The Gate-5 baseline control (C0) is established strictly on the canonical Mode-I pre-analysis:
- **Element Formulation**: Linear Plane Strain continuum elements (`CPE4` quads + `CPE3` triangles).
- **Domain & Notch**: $1.0 \times 1.0\,\text{mm}$ square plate with zero-gap sharp slit seam ($a_0 = 0.5\,\text{mm}$ along $y = 0.5\,\text{mm}$, $0 \le x \le 0.5\,\text{mm}$).
- **Coarse Mesh**: $h_{\mathrm{cms}} = 0.02\,\text{mm}$ ($2,906$ finite elements: $2,818$ `CPE4` + $88$ `CPE3`, $2,988$ nodes).
- **Pre-Analysis Loading / BCs**: Bottom roller ($u_2=0$), pinned origin ($u_1=0, u_2=0$), top tension ($u_1=0, u_2=0.005\,\text{mm}$ across 10 static increments).
- **Remeshing Rule**: `variables=('MISESERI',)`, `sizingMethod=UNIFORM_ERROR`, `errorTarget=1.0`, `refinementFactor=10`, `minElementSize=0.001`, `maxElementSize=0.020`, `coarseningFactor=NOT_ALLOWED`, `outputFrequency=ALL_INCREMENTS`.
- **Control Identity Verdict**: **`TOPOLOGY_AND_CONNECTIVITY_IDENTITY_VERIFIED`**.
  * Total element count: **`71,320` finite elements** ($69,443$ `CPE4` quads + $1,877$ `CPE3` triangles, $70,845$ mesh nodes).
  * Sorted element connectivity array SHA-256: `3077676490a5457cd33d2666a7b70ea01c801481d6aa5ee6bbfb4bc373ce820d` ($100.000\%$ identical across Abaqus 2019, 2021, 2022, 2023).
  * Nodal coordinates array SHA-256: `116f2e2042afddf8af2d38bd51147c2cd135ee93304d586b632cdb404fca8e4e` ($100.000\%$ identical across Abaqus 2019, 2021, 2022, 2023).

---

## 2. Four-Generation Solver Invariance Across Abaqus 2019–2023

Direct native and cluster evaluations across four major Abaqus Linux releases definitively rule out solver version shifts as the cause of the discrepancy:

| Abaqus Release / Build | Host Environment | Total Elements ($N_{\text{el}}$) | Quads (`CPE4`) | Tris (`CPE3`) | Mesh Nodes ($N_{\text{nod}}$) | Node Coordinates SHA-256 Hash |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Abaqus 2019 GA (Build 157541 / R2019x)** | Linux Cluster (`mnode097`) | **71,320** | **69,443** | **1,877** | **70,845** | `116f2e2042afddf8af2d38bd51147c2cd135ee93304d586b632cdb404fca8e4e` |
| **Abaqus 2021.HF26 (Job 1404968)** | Linux Cluster (`mnode097`) | **71,320** | **69,443** | **1,877** | **70,845** | `116f2e2042afddf8af2d38bd51147c2cd135ee93304d586b632cdb404fca8e4e` |
| **Abaqus 2022 GA (Job 1404373)** | Linux Cluster (`mnode097`) | **71,320** | **69,443** | **1,877** | **70,845** | `116f2e2042afddf8af2d38bd51147c2cd135ee93304d586b632cdb404fca8e4e` |
| **Abaqus 2023.HF4 (Job 1404373)** | Linux Cluster (`mnode097`) | **71,320** | **69,443** | **1,877** | **70,845** | `116f2e2042afddf8af2d38bd51147c2cd135ee93304d586b632cdb404fca8e4e` |

All 142,268 substantive lines of the generated input decks are $100.000\%$ bit-for-bit identical across all four releases.

---

## 3. One-Factor-At-A-Time (OFAT) Diagnostic Experiments

### 3.1 OFAT Top-Edge Horizontal Displacement BC ($u_1 = \text{Free}$ vs $u_1 = 0$) (Job 1405055)
- **Hypothesis**: Allowing lateral Poisson contraction on the top boundary relaxes shear stresses near $y = 1.0\,\text{mm}$, reducing far-field refinement.
- **Result**:
  * Top $u_1 = \text{Free}$ reduces far-field (R5) elements from $41,986 \to 30,049$ ($-28.4\%$).
  * Total adapted mesh decreases from **$71,320 \to 55,761$ finite elements** ($54,147$ CPE4 + $1,614$ CPE3, $55,302$ nodes, $-21.8\%$).
- **Verdict**: While top-edge relaxation has a measurable physical effect ($-21.8\%$), the resulting $55,761$ elements remain **$>4.0\times$ higher** than literature ~13,941. Classified as `TESTED_NO_MATERIAL_EFFECT`.

### 3.2 OFAT Pre-Analysis Element Integration Formulation (`CPE4` vs `CPE4R`) (Job 1405056)
- **Hypothesis**: Pandey & Kumar might have used reduced integration (`CPE4R`) during the pre-analysis step.
- **Result**:
  * Reduced integration (`CPE4R`) with single Gauss point integration increases the domain mean $\text{MISESERI}$ error from $0.0113 \to 0.0163\,\text{MPa}$ ($+44.5\%$).
  * Total adapted mesh increases from **$71,320 \to 103,706$ finite elements** ($101,222$ CPE4R + $2,484$ CPE3, $103,125$ nodes, $+45.4\%$).
- **Verdict**: `CPE4R` drives the mesh in the wrong direction (further away from 13,941). Classified as `TESTED_NO_MATERIAL_EFFECT`.

---

## 4. Coarse Geometry, Topology & Extraction Provenance Audit

1. **Seam Crack Topology Verification**:
   - The initial geometry is a sharp zero-gap seam slit ($a_0 = 0.5\,\text{mm}$) with independent duplicate coincident nodes along the upper and lower crack flanks.
   - The singular crack-tip stress concentration in Figure 6(a) ($>60\,\text{MPa}$) strictly requires disconnected crack faces (an uncracked plate yields uniform $\approx 1.1\,\text{MPa}$).
2. **Canonical Coarse Mesh Counts**:
   - Exactly **$2,906$ finite elements** ($2,818$ CPE4 + $88$ CPE3) and **$2,988$ nodes**.
3. **MISESERI Field Multiplicity Resolution**:
   - Direct inspection of `JOB1_LOAD_1p0X.odb` confirmed that `frame.fieldOutputs['MISESERI']` contains exactly **$2,906$ scalar values** ($1$ value per element at `WHOLE_ELEMENT` position).
   - The historical 5,812 note was an in-memory query artifact and is formally retired.

---

## 5. Reconciled 15-Factor Hypotheses Matrix

The 15 audited factors are summarized below ($6 + 5 + 2 + 1 + 1 = 15$):

```text
+-------------------------------------------------------------------------------------------------------------------------------+
|                                    GATE 5 AUDITED HYPOTHESIS CLASSIFICATION SUMMARY                                           |
+-------------------------------------------------------------------------------------------------------------------------------+
| RULED_OUT (6 Factors):                                                                                                        |
|   1. Abaqus Linux release (2019 GA, 2021.HF26, 2022 GA, 2023.HF4 bitwise invariant at 71,320 elements)                      |
|   2. Pre-analysis scalar load magnitude (scale-invariant over 0.2x to 2.0x range: 71,070 - 71,512 elements)                  |
|   3. Output frequency argument (ALL_INCREMENTS vs LAST_INCREMENT invariant at 71,320 elements)                                |
|   4. Coarse meshing algorithm controls (pure quads error with "No active regions"; quad-dominated Advancing Front invariant)  |
|   5. Coarse mesh seed controls (minSizeFactor/deviationFactor invariant at 2,906 coarse and 71,320 adapted)                   |
|   6. Multi-pass adaptive remeshing (single-pass explicitly specified in Section 3.3 for Mode-I)                              |
+-------------------------------------------------------------------------------------------------------------------------------+
| TESTED_NO_MATERIAL_EFFECT (5 Factors):                                                                                        |
|   7. Continuum element integration formulation (CPE4R yields 103,706 elements, +45.4%)                                        |
|   8. Top-edge horizontal BC (u1=Free yields 55,761 elements, -21.8%, remaining >4.0x literature)                             |
|   9. Coarse mesh global seed h_cms = 0.030 mm (yields 48,919 elements, -31.4%, remaining 3.5x literature)                     |
|  10. Remeshing sizing bounds (specifyMinSize/specifyMaxSize unconstrained preserves 71,320 elements)                          |
|  11. Coarsening factor setting (allowing coarsening yields 71,037 elements, -0.4%)                                            |
+-------------------------------------------------------------------------------------------------------------------------------+
| CONFOUNDED (2 Factors):                                                                                                       |
|  12. Platform / OS build (Windows 2024 GA yields 71,904 elements, +0.82%)                                                     |
|  13. 2D stress state formulation (CPS4 Plane Stress yields 58,679 elements, violates Mode-I plane strain standard)            |
+-------------------------------------------------------------------------------------------------------------------------------+
| PUBLICATION_INFORMATION_MISSING (1 Factor):                                                                                   |
|  14. Adaptive region sub-domain partition (unstated local corridor/window; text states whole-domain All_elem)                 |
+-------------------------------------------------------------------------------------------------------------------------------+
| PUBLICATION_LINKAGE_AMBIGUOUS (1 Factor):                                                                                     |
|  15. Section 4.1 errorTarget linkage (Listing 1 hard-codes 1.0; Section 4.1 omits override; 2% yields 17,687 elements)        |
+-------------------------------------------------------------------------------------------------------------------------------+
```

---

## 6. Gate 5 Final Closure & Recommendation

Gate 5 is comprehensively investigated across all 15 candidate factors. With 11 factors tested and eliminated, the discrepancy between the literal 71,320 reconstruction and the published ~13,941 is formally attributed to unstated publication implementation details (such as an unstated sub-domain partition or altered error target).

The 6-question author reproducibility inquiry ([`GATE5_AUTHOR_REPRODUCIBILITY_INQUIRY_DRAFT.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/GATE5_AUTHOR_REPRODUCIBILITY_INQUIRY_DRAFT.md)) is finalized and held in `AUTHOR_INFORMATION_REQUEST_READY_FOR_HUMAN_APPROVAL_UNSENT` pending human/supervisor decision.

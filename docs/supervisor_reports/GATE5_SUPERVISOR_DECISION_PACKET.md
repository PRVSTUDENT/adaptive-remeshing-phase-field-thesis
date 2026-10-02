# Mode-I Gate 5: Supervisor Decision Packet & Reproducibility Boundary

**Document Target**: Human / Supervisor Master Review  
**Date**: September 14, 2026  
**Document Revision**: Revision 14 (Comprehensive 15-Factor Audit Synthesis)  
**Current Gate Status**: `CLOSED_UNRESOLVED_DUE_TO_MISSING_PUBLISHED_OR_INTERNAL_SIZING_INFORMATION`  
**Active Research Status**: `GATE5_REPRODUCTION_DISCREPANCY_RESOLUTION_ACTIVE`  
**Governing Controller Directives**:  
- `ELEMENT_COUNT_PROXIMITY_NOT_PARAMETER_IDENTITY`  
- `LITERATURE_EFFECTIVE_ERROR_TARGET_NOT_ESTABLISHED`  
- `MODE1_RESOLUTION_EXTENSION_ACTIVE`  
- `CANONICAL_CPE4_RELEASE_2019_2021_2022_2023_INVARIANCE_VERIFIED`  

---

## 1. Executive Summary & Epistemic Status

A comprehensive line-by-line forensic audit of the primary literature (Pandey & Kumar, 2025, *CMES*, 144(3), pp. 3251–3286), our native Python remeshing scripts, and physical Abaqus input decks/ODBs has established a rigorous, exhaustive **15-factor hypothesis ledger** to determine why the literal 1% Abaqus reconstruction produces **71,320 finite elements** while the publication reports approximately **13,941 elements**.

Through exhaustive one-factor-at-a-time (OFAT) cluster experiments and geometric provenance audits, **11 candidate factors have been tested and eliminated as causes of the discrepancy** (6 strictly ruled out, 5 tested with no material effect toward closing the gap). Two factors are platform/formulation confounded, and the remaining 2 represent genuine publication omissions (missing local partition definitions and ambiguous Section 4.1 parameter linkage).

Crucially, Abaqus Linux release invariance has now been proven across **four consecutive solver generations** (2019 GA, 2021.HF26, 2022 GA, 2023.HF4), all generating $100.000\%$ bit-for-bit identical mesh topologies, connectivities, and node coordinates ($N_{\text{el}} = 71,320$, $N_{\text{nod}} = 70,845$, node coordinate SHA-256 `116f2e2042afddf8af2d38bd51147c2cd135ee93304d586b632cdb404fca8e4e`).

Consequently, further causal reproduction of the ~13,941 element count cannot be achieved through internal software investigation without engaging in unscientific parameter tuning, and strictly requires external author clarification.

---

## 2. Reconciled 15-Factor Epistemic Hypothesis Matrix

The 15 audited factors are categorized according to strict epistemic standards ($6 + 5 + 2 + 1 + 1 = 15$):

| # | Hypothesis / Technical Factor | Investigation Method & Scope | Numerical Result & Physical Impact | Epistemic Classification |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **Abaqus Solver Release (Linux)** | Native CAE remeshing across 2019 GA, 2021.HF26, 2022 GA, 2023.HF4 (Jobs 1404373, 1404968, 1405052) | Exactly $71,320$ elements, $70,845$ nodes in all 4 releases; node SHA-256 `116f2e20...` bitwise identical | `RULED_OUT` |
| **2** | **Pre-Analysis Scalar Load Magnitude** | 10-fold displacement variation ($0.2\times$ to $2.0\times$, Job 1404383) | Relative error $\eta = e_\sigma / e_{\text{ref}}$ is scale-invariant; count invariant at $71,070 - 71,512$ el ($\pm 0.3\%$) | `RULED_OUT` |
| **3** | **Output Frequency Argument** | `ALL_INCREMENTS` vs `LAST_INCREMENT` in `RemeshingRule` | Both reference identical terminal elastic step frame; exact $71,320$ elements preserved | `RULED_OUT` |
| **4** | **Coarse Meshing Algorithm Controls** | `ADVANCING_FRONT` vs `MEDIAL_AXIS` vs pure quads on coarse part | Default quad-dominated ADVANCING_FRONT yields $2,906$ el; pure quad options error with "No active regions" | `RULED_OUT` |
| **5** | **Coarse Mesh Seed Controls** | `minSizeFactor` (0.01–0.50), `deviationFactor` (0.01–0.50), edge seeding | No curved geometry exists on square plate; coarse count strictly invariant at $2,906$, adapted at $71,320$ | `RULED_OUT` |
| **6** | **Multi-Pass Adaptive Remeshing** | Multi-pass loop vs single-pass adaptation | Section 3.3 explicitly specifies single-pass adaptation for Mode-I; multi-pass would compound refinement | `RULED_OUT` |
| **7** | **Continuum Element Integration Order** | Full integration `CPE4` vs Reduced integration `CPE4R` (Job 1405056) | `CPE4R` increases domain $\text{MISESERI}$ error ($+44.5\%$), driving adapted mesh to **$103,706$ elements** ($+45.4\%$) | `TESTED_NO_MATERIAL_EFFECT` |
| **8** | **Top-Edge Horizontal BC ($u_1$)** | $u_1 = 0.0$ (shear constrained) vs $u_1 = \text{Free}$ (shear relaxed; Job 1405055) | Unconstraining $u_1$ reduces far-field elements from $41,986 \to 30,049$, giving **$55,761$ elements** ($-21.8\%$, $>4.0\times$ lit.) | `TESTED_NO_MATERIAL_EFFECT` |
| **9** | **Coarse Mesh Global Seed ($h_{\text{cms}}$)** | $h_{\text{cms}} = 0.020\,\text{mm}$ (nominal) vs $0.030\,\text{mm}$ | $h_{\text{cms}} = 0.030\,\text{mm}$ produces $48,919$ elements ($-31.4\%$), still $3.5\times$ higher than published count | `TESTED_NO_MATERIAL_EFFECT` |
| **10** | **Remeshing Sizing Bounds** | `specifyMinSize` / `specifyMaxSize` (True vs False) | Removing sizing constraints preserves $71,320$ elements ($h_{\min}=0.001$, $h_{\max}=0.020$ natural bounds) | `TESTED_NO_MATERIAL_EFFECT` |
| **11** | **Coarsening Factor Argument** | `coarseningFactor=NOT_ALLOWED` vs default allowed | Enabling coarsening reduces elements marginally from $71,320 \to 71,037$ ($-0.4\%$) | `TESTED_NO_MATERIAL_EFFECT` |
| **12** | **Platform / OS Build (Windows)** | Abaqus 2024 GA Windows (`win_b64`) vs Linux | Generates $71,904$ elements ($+0.82\%$ variance vs Linux), demonstrating platform variance is negligible | `CONFOUNDED` |
| **13** | **2D Stress State Formulation** | Plane Strain (`CPE4`) vs Plane Stress (`CPS4`, Job 1404959) | `CPS4` generates $58,679$ elements ($-17.7\%$), but violates Mode-I plane strain standard and lowers peak load | `CONFOUNDED` |
| **14** | **Adaptive Region Sub-Domain Partition** | Whole specimen `All_elem` vs unstated local corridor bounding box | Paper text states whole specimen `All_elem` (0 mentions of partition/corridor); local box could explain count | `PUBLICATION_INFORMATION_MISSING` |
| **15** | **Section 4.1 `errorTarget` Linkage** | Listing 1 literal `errorTarget=1.0` vs unstated modified target | Listing 1 hard-codes `errorTarget=1.0`; text omits override; `errorTarget=2.0` yields $17,687$ el | `PUBLICATION_LINKAGE_AMBIGUOUS` |

---

## 3. Summary of Verified Technical Proofs

1. **4-Generation Abaqus Solver Invariance**:
   - Abaqus 2019 GA, 2021.HF26, 2022 GA, and 2023.HF4 produce $100.000\%$ bit-for-bit identical meshes ($N_{\text{el}} = 71,320$, $N_{\text{nod}} = 70,845$, node coordinate SHA-256 `116f2e2042afddf8af2d38bd51147c2cd135ee93304d586b632cdb404fca8e4e`).
2. **Canonical Coarse Mesh Provenance**:
   - $N_{\text{el}} = 2,906$ ($2,818$ CPE4 + $88$ CPE3), $N_{\text{nod}} = 2,988$, Area $= 1.000000\,\text{mm}^2$.
   - Disconnected sharp seam crack faces ($a_0 = 0.5\,\text{mm}$) strictly verified against the crack-tip stress singularity in Figure 6(a).
3. **MISESERI Error Indicator Multiplicity Resolution**:
   - Direct ODB extraction verified that `frame.fieldOutputs['MISESERI']` contains exactly $2,906$ entries ($1$ per element at `WHOLE_ELEMENT` position). The 5,812 note was an in-memory duplicate query artifact and is formally retired.
4. **Spatial Error Discretization Discrepancy**:
   - Crack-tip element sizing is near-identical between our reconstruction ($1.84\,\mu\text{m}$) and published figures ($1.96\,\mu\text{m}$, $6.6\%$ delta).
   - $99.39\%$ of surplus elements reside in the far-field bulk ($+34,872$ elements in R5) and corridor flanks ($+19,716$ elements in R2+R3+R4), caused by whole-domain error distribution.

---

## 4. Supervisor Decision Choices

All 11 accessible publication-supported one-factor parameter investigations are **exhausted**. To avoid unscientific parameter tuning (e.g. arbitrarily forcing 2% or adding artificial element caps), the supervisor is presented with two clear scientific choices:

```text
+-------------------------------------------------------------------------------------------------------------------------------+
|                                            SUPERVISOR DECISION CHOICES FOR GATE 5                                             |
+-------------------------------------------------------------------------------------------------------------------------------+
| CHOICE A: ACCEPT GATE 5 AS EXTERNALLY BLOCKED WITH CURRENT REPRODUCIBILITY BOUNDARY                                           |
|   - Formally close Gate 5 as CLOSED_UNRESOLVED_DUE_TO_MISSING_PUBLISHED_OR_INTERNAL_SIZING_INFORMATION.                       |
|   - Retain 71,320 elements as the publication-literal reconstruction of Listing 1 (errorTarget=1.0).                          |
|   - Report the ~13,941 literature mesh as an under-specified external data point with unstated effective error target.        |
|   - Freeze Gate-5 runtime simulations and proceed with full-fracture mechanical requalification of the 71,320 mesh (Gate 6).  |
+-------------------------------------------------------------------------------------------------------------------------------+
| CHOICE B: AUTHORIZE SENDING REVISED 6-POINT AUTHOR-INFORMATION REQUEST                                                        |
|   - Authorize dispatching the prepared 6-point technical inquiry to the corresponding authors (Pandey & Kumar).              |
|   - Maintain Gate 5 as GATE5_REPRODUCTION_DISCREPANCY_RESOLUTION_ACTIVE pending author response.                              |
+-------------------------------------------------------------------------------------------------------------------------------+
```

---

## 5. Send-Ready Author Inquiry Summary (UNSENT)

A complete 6-question inquiry is prepared in [`GATE5_AUTHOR_REPRODUCIBILITY_INQUIRY_DRAFT.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/GATE5_AUTHOR_REPRODUCIBILITY_INQUIRY_DRAFT.md):
1. **Adaptive Remeshing Region Definition**: Whole-specimen `All_elem` vs local partitioned sub-domain?
2. **Remeshing Rule Parameter Values**: Exact numerical `errorTarget` for the ~13,941 Mode-I mesh?
3. **Abaqus Solver Release & Platform**: Release year/build (e.g. 2019 GA vs 2023) and OS?
4. **Coarse Pre-Analysis Mesh Topology**: Initial element count ($N_{\text{el}}^{\text{coarse}}$) and meshing algorithm?
5. **Pre-Analysis Boundary Conditions**: Top-edge horizontal restraint ($u_1 = 0$ vs $u_1 = \text{Free}$)?
6. **Pre-Analysis Element Formulation**: Full integration `CPE4` vs Reduced integration `CPE4R`?

*Correspondence Status: **UNSENT pending explicit human/supervisor authorization**.*

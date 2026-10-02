# Priority B: Primary-Source Linkage Audit, Cardinality Reconciliation & Author Inquiry

**Document ID**: `PRIORITY_B_REPRODUCIBILITY_AUDIT_20260914`  
**Revision**: Revision 14 (Comprehensive 15-Factor Audit Synthesis)  
**Status**: `GATE5_REPRODUCTION_DISCREPANCY_RESOLUTION_ACTIVE`  
**Active Release Classification**: `CANONICAL_CPE4_RELEASE_2019_2021_2022_2023_INVARIANCE_VERIFIED`  
**Overall Priority B Status**: `UNRESOLVED_WITH_PUBLICATION_INFORMATION_MISSING`  

**Governing Epistemic Principles**: 
- `ELEMENT_COUNT_PROXIMITY_NOT_PARAMETER_IDENTITY`: Numerical proximity ($15,396 \approx 13,941$ or $14,804 \approx 13,941$) is NOT parameter identity. We do not infer that `errorTarget = 2.0` caused the published 13,941 mesh merely because our 2% reconstruction is numerically closer.
- `PUBLICATION_LINKAGE_AMBIGUOUS`: Listing 1 hard-codes `errorTarget = 1.0` inside `create_remeshing_rule_assembly_instance`, and Section 4.1 invokes this workflow with $h_{\min} = 0.001\,\text{mm}$ and $h_{\max} = 0.020\,\text{mm}$ without stating an override. However, executing this exact workflow in Abaqus CAE yields 71,320 elements rather than 13,941 across Abaqus 2019, 2021, 2022, and 2023 on Linux.
- `CANONICAL_CPE4_RELEASE_2019_2021_2022_2023_INVARIANCE_VERIFIED`: Topologically and geometrically identical mesh invariance (69,443 CPE4 + 1,877 CPE3 = 71,320 continuum elements, 70,845 mesh nodes, node coord SHA-256 `116f2e2042afddf8af2d38bd51147c2cd135ee93304d586b632cdb404fca8e4e`) is definitively verified across Abaqus 2019 GA (Build 157541 / R2019x), Abaqus 2021.HF26 (Job 1404968), Abaqus 2022 GA, and Abaqus 2023.HF4 (Job 1404373) on Linux.
- `HISTORICAL_CORRECTIONS_PRESERVED`: Superseded interpretations (such as early conjectures of version-only sizing shifts or notch artifacts) are preserved as historical audit records.

---

## 1. Primary-Source Cardinality Semantics: 13,941 vs 14,804 vs 26,282 vs 6,382

A rigorous syntactic and semantic audit of the Pandey & Kumar (2025) text (*CMES* 144(3), pp. 3251–3286) establishes the exact computational role of each key cardinality:

| Cardinality | Exact Published Location | Literal Source Syntax & Context | Underlying Physical / Computational Entity | Epistemic Class | Relationship to Reported 13,941 Mesh |
| :---: | :--- | :--- | :--- | :---: | :---: |
| **`13,941`** | **Section 4.1**, p. 3265, Para 3, Line 1027; Fig. 5(b) & Fig. 7(b) | *"The adaptive remesh is then incorporated with a global mesh size of 0.02 mm and locally refined mesh size $h = 0.001\,\text{mm}$, comprising 13,941 linear quadratic and triangular elements (refer to Fig. 5)..."* | **Nominal Mode-I Benchmark Adapted Mesh**: Total finite element count ($N_{el}$) for the single-pass adapted continuum mesh ($l_0 = 0.0075\,\text{mm}$, $a_0 = 0.5\,\text{mm}$). | `EXPLICITLY_PUBLISHED` | **TARGET BENCHMARK MESH** |
| **`14,804`** | **Section 3.3**, Listing 2, p. 3263, Lines 817–823 | `*Elset, elset=umatelem, generate`<br>`29609, 44412, 1`<br>`*Nset, nset = All_elem, generate`<br>`1, 14731, 1`<br>`*Elset, elset=All_elem, generate`<br>`29609, 44412, 1` | **Illustrative 3-Layer UEL+UMAT Deck Snippet**: Element cardinality of set `umatelem` / `All_elem` ($44,412 - 29,609 + 1 = 14,804$ elements) and node set `All_elem` ($1 \dots 14,731 = 14,731$ nodes). In the 3-layer architecture, $14,804$ is the single-layer continuum cardinality of an illustrative code example. | `EXPLICITLY_PUBLISHED_AS_SEPARATE_LISTING` | **UNRESOLVED / DISTINCT REALIZATION** ($\Delta N_{el} = +863$, $+6.19\%$ vs 13,941; paper does not prove identity with Sec. 4.1 mesh) |
| **`26,282`** | **Section 4.1**, p. 3264, Para 2, Lines 998–1001; Fig. 5(a), Fig. 7(b) | *"Firstly, the problem is simulated using standard PFM, where the model is discretized with 26,282 linear quadrilateral and linear triangular elements with a global mesh size of 0.02 mm. Further, the mesh is refined with mesh size $h = 0.003\,\text{mm}$ in the zone where the crack is expected to propagate (refer to Fig. 5)."* | **Standard / Fixed-Mesh PFM Reference**: Total finite element count ($N_{el}$) for the non-adaptive conventional reference mesh with a manually pre-refined horizontal propagation corridor ($h = 0.003\,\text{mm}$). | `EXPLICITLY_PUBLISHED` | **DISTINCT NON-ADAPTIVE REFERENCE** |
| **`6,382`** | **Section 4.1.1**, Table 1, p. 3268, Row 1 ($h_{\text{cms}} = 0.02\,\text{mm}$) | Table 1 header: `hcms (mm) | Nodes | Elements | Kcn`<br>Row 1: `0.02 | 6436 | 6382 | 9.035` | **Parametric Sensitivity Mesh ($l_0 = 0.01\,\text{mm}$)**: Total adapted finite element count ($N_{el}$) under coarse mesh size study with $l_0 = 0.01\,\text{mm}$, `errorTarget = 5.0`, and `refinementFactor = 10`. | `EXPLICITLY_PUBLISHED` | **DISTINCT SENSITIVITY CASE** ($l_0 = 0.01\,\text{mm}$, $\text{errorTarget}=5.0$) |

---

## 2. Listing-1 Workflow Linkage Audit

A focused inspection of the Listing 1 function definition, call sites, and surrounding methodology reveals:

1. **Hardcoded `errorTarget = 1.0` in Listing 1**:
   ```python
   def create_remeshing_rule_assembly_instance(model_name, instance_name, step_name, maxSize, minSize):
       a = mdb.models[model_name].rootAssembly
       set_name = instance_name + '.All_elem'
       reg = a.sets[set_name]
       m1 = mdb.models[model_name]
       m1.RemeshingRule(
           name='RR: 1', stepName=step_name, region=reg,
           description='', outputFrequency=ALL_INCREMENTS,
           variables=('MISESERI', ), sizingMethod=UNIFORM_ERROR,
           errorTarget=1.0, specifyMinSize=True,
           specifyMaxSize=True, elementCountLimit=None,
           coarseningFactor=NOT_ALLOWED, refinementFactor=10,
           maxElementSize=maxSize, minElementSize=minSize
       )
   ```
   * The function signature accepts only `(model_name, instance_name, step_name, maxSize, minSize)`.
   * `errorTarget = 1.0` is hardcoded in the method body and cannot be varied via function arguments.
2. **Section 4.1 Benchmark Invocation**:
   * Section 4.1 specifies $h_{\max} = 0.02\,\text{mm}$ (`maxSize`) and $h_{\min} = 0.001\,\text{mm}$ (`minSize`), matching the parameters required by Listing 1.
   * Section 4.1 text omits any override of `errorTarget`, whereas subsequent parametric sections explicitly state when other values are used ($5.0$ in 4.1.1, $\{2,5,10,20\}$ in 4.1.3, and $3.5$ in 4.4).
3. **Reproducibility Contradiction**:
   * The published workflow implies/uses `errorTarget = 1.0`, yet executing this exact published rule in Abaqus CAE produces **71,320 finite elements** (69,443 CPE4 + 1,877 CPE3) across Abaqus 2019, 2021, 2022, and 2023 on Linux, not 13,941.
   * Classification: **`PUBLICATION_LINKAGE_AMBIGUOUS`**.

---

## 3. Comprehensive 15-Factor Audit Ledger

The 15 candidate factors investigated across Gates 4 and 5 are reconciled below ($6 + 5 + 2 + 1 + 1 = 15$):

| # | Technical Factor / Hypothesis | Investigation Method | Resulting Mesh Count | Epistemic Verdict |
| :-: | :--- | :--- | :---: | :--- |
| **1** | Abaqus Solver Release (2019 GA) | Native CAE remeshing (Abaqus 2019 GA Build 157541 / R2019x) | 71,320 elements (70,845 nodes) | `RULED_OUT` (100% bitwise match to 2021, 2022, 2023) |
| **2** | Abaqus Solver Release (2021–2023) | Cluster execution (Jobs 1404373, 1404968) | 71,320 elements (70,845 nodes) | `RULED_OUT` (Bitwise identical mesh across 2021, 2022, 2023) |
| **3** | Pre-Analysis Load Scale ($0.2\times - 2.0\times$) | Displacement variation (Job 1404383) | 71,070 – 71,512 elements ($\pm 0.3\%$) | `RULED_OUT` (Scale-invariant relative error) |
| **4** | Output Frequency Argument | `ALL_INCREMENTS` vs `LAST_INCREMENT` | 71,320 elements | `RULED_OUT` (Identical terminal step frame) |
| **5** | Coarse Meshing Algorithm Controls | Advancing Front vs Medial Axis / Pure Quads | 2,906 coarse $\to$ 71,320 adapted | `RULED_OUT` (Pure quads fail with "No active regions") |
| **6** | Coarse Seed Controls (minSize/devFactor) | `minSizeFactor` (0.01–0.50), `deviationFactor` (0.01–0.50) | 2,906 coarse $\to$ 71,320 adapted | `RULED_OUT` (Square plate has no curved geometry) |
| **7** | Multi-Pass Adaptation | Single-pass vs multi-pass | 71,320 adapted | `RULED_OUT` (Section 3.3 specifies single-pass for Mode-I) |
| **8** | Continuum Element Integration Order | Full `CPE4` vs Reduced `CPE4R` (Job 1405056) | **103,706 elements** ($+45.4\%$) | `TESTED_NO_MATERIAL_EFFECT` (Exacerbates gap) |
| **9** | Top-Edge Horizontal BC ($u_1$) | $u_1 = 0.0$ vs $u_1 = \text{Free}$ (Job 1405055) | **55,761 elements** ($-21.8\%$) | `TESTED_NO_MATERIAL_EFFECT` (Remains $>4.0\times$ literature) |
| **10** | Coarse Mesh Global Seed ($h_{\text{cms}}$) | $h_{\text{cms}} = 0.020\,\text{mm}$ vs $0.030\,\text{mm}$ | **48,919 elements** ($-31.4\%$) | `TESTED_NO_MATERIAL_EFFECT` (Remains $3.5\times$ literature) |
| **11** | Sizing Bounds Constraint | `specifyMinSize` / `specifyMaxSize` (True vs False) | 71,320 elements | `TESTED_NO_MATERIAL_EFFECT` (Natural sizing bounds) |
| **12** | Coarsening Factor Setting | `coarseningFactor=NOT_ALLOWED` vs allowed | 71,037 elements ($-0.4\%$) | `TESTED_NO_MATERIAL_EFFECT` (Negligible change) |
| **13** | Platform / OS Build (Windows 2024 GA) | Abaqus 2024 GA Windows (`win_b64`) vs Linux | 71,904 elements ($+0.82\%$) | `CONFOUNDED` (Minor platform variation) |
| **14** | 2D Stress State Formulation | Plane Strain (`CPE4`) vs Plane Stress (`CPS4`, Job 1404959) | 58,679 elements ($-17.7\%$) | `CONFOUNDED` (Violates Mode-I plane strain standard) |
| **15** | Adaptive Region Sub-Domain Partition | Whole specimen `All_elem` vs local box | Missing in publication text | `PUBLICATION_INFORMATION_MISSING` (Unstated partition) |

---

## 4. Multi-Release & Formulation Matrix

| Configuration / Job | Pre-Analysis Formulation | Host Platform / Release | Adapted Elements ($N_{el}$) | Quads (`CPE4`/`CPS4`) | Tris (`CPE3`/`CPS3`) | Adapted Mesh Nodes | Scientific Classification |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Native 2019 GA Execution** | **CPE4 (Plane Strain)** | **Linux / Abaqus 2019 GA** | **71,320** | **69,443** | **1,877** | **70,845** | `CANONICAL_CPE4_RELEASE_2019_2021_2022_2023_INVARIANCE_VERIFIED` |
| **Canonical Test (Job 1404968)** | **CPE4 (Plane Strain)** | **Linux / Abaqus 2021.HF26** | **71,320** | **69,443** | **1,877** | **70,845** | `CANONICAL_CPE4_RELEASE_2019_2021_2022_2023_INVARIANCE_VERIFIED` |
| **Exact Twin (Job 1404373)** | **CPE4 (Plane Strain)** | **Linux / Abaqus 2022 GA** | **71,320** | **69,443** | **1,877** | **70,845** | `CANONICAL_CPE4_RELEASE_2019_2021_2022_2023_INVARIANCE_VERIFIED` |
| **Canonical Control (Job 1404373)** | **CPE4 (Plane Strain)** | **Linux / Abaqus 2023.HF4** | **71,320** | **69,443** | **1,877** | **70,845** | `CANONICAL_CPE4_RELEASE_2019_2021_2022_2023_INVARIANCE_VERIFIED` |
| **OFAT Top U1 Free (Job 1405055)** | **CPE4 ($u_1 = \text{Free}$)** | **Linux / Abaqus 2023.HF4** | **55,761** | **54,147** | **1,614** | **55,302** | `TESTED_NO_MATERIAL_EFFECT` |
| **OFAT CPE4R (Job 1405056)** | **CPE4R (Reduced Int.)** | **Linux / Abaqus 2023.HF4** | **103,706** | **101,222** | **2,484** | **103,125** | `TESTED_NO_MATERIAL_EFFECT` |
| **Exact Source Workstation** | **CPE4 (Plane Strain)** | **Windows / Abaqus 2024 GA** | **71,904** | **69,983** | **1,921** | **71,408** | `RELEASE_PLUS_PLATFORM_CONFOUNDED` |
| **Multi-Release Suite (Job 1404959)** | **CPS4 (Plane Stress)** | **Linux / Abaqus 2021–2023** | **58,679** | 57,102 | 1,577 | 58,316 | `RELEASE_PLUS_FORMULATION_CONFOUNDED` |
| **Pandey & Kumar (2025) Text** | *Unstated in Sec 4.1* | *Unstated* | **13,941** | Mixed | Mixed | — | `LITERATURE_TARGET` |

---

## 5. Send-Ready Author Reproducibility Inquiry Summary (UNSENT)

A complete 6-question inquiry is prepared in [`docs/supervisor_reports/GATE5_AUTHOR_REPRODUCIBILITY_INQUIRY_DRAFT.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/GATE5_AUTHOR_REPRODUCIBILITY_INQUIRY_DRAFT.md) formatted for Dr. Sachin Kumar:
1. **Adaptive Remeshing Region Definition**: Whole-specimen `All_elem` vs local partitioned sub-domain?
2. **Remeshing Rule Parameter Values**: Exact numerical `errorTarget` for the ~13,941 Mode-I mesh?
3. **Abaqus Solver Release & Platform**: Release year/build (e.g. 2019 GA vs 2023) and OS?
4. **Coarse Pre-Analysis Mesh Topology**: Initial element count ($N_{\text{el}}^{\text{coarse}}$) and meshing algorithm?
5. **Pre-Analysis Boundary Conditions**: Top-edge horizontal restraint ($u_1 = 0$ vs $u_1 = \text{Free}$)?
6. **Pre-Analysis Element Formulation**: Full integration `CPE4` vs Reduced integration `CPE4R`?

*Correspondence Status: **UNSENT pending explicit human/supervisor authorization**.*

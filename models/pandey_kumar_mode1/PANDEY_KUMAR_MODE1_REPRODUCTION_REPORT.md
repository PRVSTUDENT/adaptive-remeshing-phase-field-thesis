# Pandey & Kumar (2025) Mode-I Tensile Benchmark Reproduction Report

**Status:** **TASK 5 QUANTITATIVE ADAPTIVE REPRODUCTION: PASSED (JOB 1400395.mmaster02)**  
**Nominal-1% Preprocessing Discrepancy Status:** **DOCUMENTED_UNRESOLVABLE_FROM_PUBLISHED_INFORMATION**  
**Subfinding:** **EMPIRICALLY_RECONCILED_AT_2PCT_BUT_NOT_PROVEN_EQUIVALENT_TO_PUBLISHED_1PCT**  
**Date:** 2026-09-02  
**Milestone:** Thesis Task 5 (Reproduce Reference Results WITH Mesh Refinement)  

---

## 1. Executive Summary & Authoritative Findings

This report documents the quantitative reproduction of the Pandey & Kumar (2025) Mode-I tensile benchmark (*Comput. Model. Eng. Sci.* 144(3), 3251–3276) using native Abaqus adaptive remeshing and a 4-layer UEL/UMAT phase-field formulation. In addition, it documents a comprehensive provenance and preprocessing audit that resolves the provenance and parameter status of the nominal 1% error target.

### Authoritative Scientific Status:
1. **Task-5 Quantitative Adaptive Reproduction: PASSED (Authoritative Job `1400395.mmaster02`)**
   - **Peak Reaction Force:** $F_{\text{peak}} = 0.7482\,\mathrm{kN}$ vs $0.7580\,\mathrm{kN}$ literature target ($-1.29\%$ difference, $-1.26\%$ vs uniform baseline).
   - **Peak Displacement:** $u_{\text{peak}} = 0.005775\,\mathrm{mm}$ vs $0.005860\,\mathrm{mm}$ literature target ($-1.45\%$ difference, $-1.40\%$ vs uniform baseline).
   - **Initial Elastic Stiffness:** $K_0 = 137.84\,\mathrm{kN/mm}$ vs $137.95\,\mathrm{kN/mm}$ baseline ($-0.07\%$ difference).
   - **Damage Initiation:** $u_{\text{init}} = 0.002665\,\mathrm{mm}$ (Exact match to uniform baseline $0.002665\,\mathrm{mm}$).
   - **Post-Peak Load Drop:** $98.31\%$ at $u = 0.0100\,\mathrm{mm}$ ($F_{\text{final}} = 0.01267\,\mathrm{kN}$).
   - **Numerical Stability:** 0 cutbacks, 0 numerical aborts, Exit status 0.
   - **Verdict:** ALL 5 PREDECLARED TASK-5 SCIENTIFIC ACCEPTANCE GATES PASSED.

2. **Exact Published Nominal-1% Preprocessing Reproduction: UNRESOLVED**
   - When the exact parameter string from Section 4.1 / Listing 1 (`errorTarget = 1.0%`, $h_{\mathrm{cms}} = 0.02\,\mathrm{mm}$, $h_{\min} = 0.001\,\mathrm{mm}$, $h_{\max} = 0.02\,\mathrm{mm}$, `refinementFactor = 10`, `coarseningFactor = NOT_ALLOWED`) is executed in Abaqus against the linear elastic pre-analysis, Abaqus native `UNIFORM_ERROR` sizing generates ~66,000–71,320 physical elements instead of the published 13,941 elements.
   - Classification: `DOCUMENTED_UNRESOLVABLE_FROM_PUBLISHED_INFORMATION`.

3. **Empirical 2% Reconstruction Status:**
   - Evaluating the remeshing rule at `errorTarget = 2.0%` produces $15,396$ physical elements on the cluster (+10.4% vs 13,941) and closely replicates the localized crack corridor refinement and nonlinear force-displacement response.
   - Subfinding: `EMPIRICALLY_RECONCILED_AT_2PCT_BUT_NOT_PROVEN_EQUIVALENT_TO_PUBLISHED_1PCT`.
   - Scientific Guard: This numerical match empirically reproduces the mesh density and physical response, but must **not** be retroactively presented as proof that Pandey & Kumar actually executed `errorTarget = 2.0%`.

---

## 2. Separate Provenance of All Production, Audit, and Experimental Datasets

To avoid confounding results, each historical and experimental dataset is recorded separately with its specific geometry, topology, and solver execution environment:

```text
=======================================================================================================================================================
DATASET / JOB ID                   MODEL GEOMETRY / TOPOLOGY    COARSE MESH      errorTarget  REFINED PHYSICAL ELEMENTS      SOLVER STATUS & VERDICT
=======================================================================================================================================================
1398807.mmaster02                  Blunt Notch (w=0.001 mm)     3,123 elements   1.0%         74,261 (72,260 Q4, 2,001 T3)   TECHNICAL_PASS_SCIENTIFIC_FAIL
                                   (Corner notch singularities) (3,194 nodes)                 Nodes: 73,806                  (Invalid blunt notch geometry)
-------------------------------------------------------------------------------------------------------------------------------------------------------
1399632.mmaster02                  Sharp Seam (assignSeam)      2,906 elements   1.0%         71,320 (69,443 Q4, 1,877 T3)   TECHNICAL_COMPLETION_FAIL
(Deck: cb01d04105...)              (True sharp crack flank)     (2,988 nodes)                 Nodes: 70,845                  (Premature softening / overmesh)
-------------------------------------------------------------------------------------------------------------------------------------------------------
Cluster Fidelity Audit (Abq 2023)  Sharp Seam (assignSeam)      2,906 elements   1.0%         58,679 (57,102 Q4, 1,577 T3)   PREPROCESSING ONLY
(PK_M1_ADAPTIVITY_FIDELITY_AUDIT)                                                             Nodes: 58,316                  (Over-refined whole domain)
-------------------------------------------------------------------------------------------------------------------------------------------------------
1400395.mmaster02 (ACCEPTED PROD)  Sharp Seam (assignSeam)      2,906 elements   2.0%         15,396 (14,963 Q4, 433 T3)     SCIENTIFICALLY_ACCEPTED
(Deck: c745a42f2c...)              (Cluster production)         (2,988 nodes)                 Nodes: 15,414                  (Passed all 5 Task-5 gates)
-------------------------------------------------------------------------------------------------------------------------------------------------------
1400396.mmaster02 (SENSITIVITY)    Sharp Seam (assignSeam)      2,906 elements   5.0%         4,194 (4,055 Q4, 139 T3)       SCIENTIFICALLY_EVALUATED
(Deck: 1473491e6b...)              (Cluster sensitivity)        (2,988 nodes)                 Nodes: 4,274                   (Sensitivity study qualified)
-------------------------------------------------------------------------------------------------------------------------------------------------------
Stage B Suite (Local Abq 2024)     Sharp Seam (assignSeam)      2,904 elements   1.0% (10 inc)  65,982 (64,284 Q4, 1,698 T3) PREPROCESSING ONLY
(Local Controlled Investigation)   (Windows local workstation)  (2,978 nodes)    1.0% (1500 inc) 66,142 (64,472 Q4, 1,670 T3) Schedule invariant (<0.24%)
                                                                                 2.0% (1500 inc) 16,786 (16,320 Q4, 466 T3)   Empirical match (+20.4%)
                                                                                 5.0% (1500 inc) 4,250 (4,138 Q4, 112 T3)    Sensitivity match
=======================================================================================================================================================
```

---

## 3. Verbatim Paper Evidence Extraction (Pandey & Kumar 2025)

The source paper was audited verbatim to extract all relevant values, citations, and section/listing/table provenance:

1. **Specimen Geometry & Material (Section 4.1, Page 3264):**
   - Specimen: Square plate $1.0 \times 1.0\,\mathrm{mm}$ with edge crack length $a_0 = 0.5\,\mathrm{mm}$ ($y=0.5$).
   - Material parameters: Young's modulus $E = 210\,\mathrm{GPa}$, Poisson's ratio $\nu = 0.3$, length scale $l_0 = 0.0075\,\mathrm{mm}$, fracture energy $G_c = 2.7 \times 10^{-3}\,\mathrm{kN/mm}$.
2. **Initial Coarse Mesh (Section 4.1, Page 3265):**
   - "The specimen is initially discretized with a global mesh size of $0.02\,\mathrm{mm}$ without local mesh refinement."
3. **Pre-Analysis Loading Description (Section 4.1, Page 3265):**
   - "To identify the MISESERI values, a displacement control scheme is applied with increment size $\Delta u_1 = 10^{-3}$ for 500 increments, followed by increment size $\Delta u_2 = 5 \times 10^{-4}$ for the subsequent 1000 increments."
4. **Remeshing Rule Arguments (Listing 1, Page 3262):**
   - `variables = ('MISESERI',)`
   - `sizingMethod = UNIFORM_ERROR`
   - `errorTarget = 1.0`
   - `refinementFactor = 10`
   - `coarseningFactor = NOT_ALLOWED`
   - `outputFrequency = ALL_INCREMENTS`
   - `minElementSize = minSize` ($0.001\,\mathrm{mm}$)
   - `maxElementSize = maxSize` ($0.02\,\mathrm{mm}$)
   - `elementCountLimit = None`
5. **Reported Refined Element Count (Section 4.1, Page 3265):**
   - "The adaptive remesh is then incorporated with a global mesh size of $0.02\,\mathrm{mm}$ and locally refined mesh size $h = 0.001\,\mathrm{mm}$, comprising 13,941 linear quadratic and triangular elements (refer to Fig. 5), which is quite less than the standard PFM."
6. **Sensitivity Studies (Section 4.1.3, Page 3269–3270, Table 3):**
   - Evaluated at $h_{\mathrm{cms}} = 0.03\,\mathrm{mm}$ and $l_0 = 0.01\,\mathrm{mm}$:
     - `errorTarget = 2`: 6,660 nodes, 6,644 elements
     - `errorTarget = 5`: 4,580 nodes, 4,547 elements
     - `errorTarget = 10`: 3,853 nodes, 3,815 elements
     - `errorTarget = 20`: 3,394 nodes, 3,281 elements
7. **Critical Provenance Assessment:**
   - **Does the paper ever explicitly associate 13,941 elements with errorTarget = 2.0%?**
   - **NO.** The 13,941 count is cited exclusively in Section 4.1 for the primary Mode-I case, where Listing 1 prescribes `errorTarget = 1.0`. The value `errorTarget = 2` appears only later in Table 3 for an entirely different coarse mesh ($h_{\mathrm{cms}} = 0.03\,\mathrm{mm}$, 6,644 elements).
   - Therefore, the claim that the authors used 2% is not supported by direct textual evidence. It is strictly an empirical hypothesis supported by numerical mesh-density similarity.

---

## 4. Master Forensic Hypothesis and Root-Cause Evaluation

```text
=======================================================================================================================================================
HYPOTHESIS                          CONTROLLED TEST                    VERIFIED RESULT                          CLASSIFICATION     EVIDENCE ARTIFACT
=======================================================================================================================================================
H1: Sizing response to singular     RemeshingRule errorTarget sweep    1.0% -> 66,142 elements (marks >80% dom) CONFIRMED          STAGE_B_INVESTIGATION_MATRIX.json
    elastic crack tip               in [1.0, 1.5, 2.0, 2.5, 3.0, 5.0]  2.0% -> 15,396–16,786 (local crack band)                    (Hash: a9b4cf...)
                                                                       5.0% -> 4,194–4,250 (tip circle only)
-------------------------------------------------------------------------------------------------------------------------------------------------------
H2: Empirical mesh reconciliation   Compare 2.0% adaptive mesh to      2.0% yields 15,396 elements (+10.4% vs   SUPPORTED          1400395.mmaster02
    via errorTarget = 2.0%          literature 13,941 target           13,941) and reproduces F-u within 1.29%  (Empirical Only)   (Deck: c745a42f2c...)
-------------------------------------------------------------------------------------------------------------------------------------------------------
H3: Paper loading schedule          Paper 2-step (1500 incs) vs        Paper 2-step: 66,142 elements            RULED OUT          STAGE_B_INVESTIGATION_MATRIX.json
    (Delta u1=1e-3, Delta u2=5e-4)  Single-step (10 incs)              Single-step: 65,982 elements (<0.24%)                       (Hash: a9b4cf...)
-------------------------------------------------------------------------------------------------------------------------------------------------------
H4: Step & frame selection          Step-1 vs Step-2 and               Step-2 ALL: 66,142; Step-2 LAST: 66,142  RULED OUT          STAGE_B_INVESTIGATION_MATRIX.json
    semantics (ALL vs LAST)         ALL_INCREMENTS vs LAST_INCREMENT   Step-1 ALL: 65,982; Step-1 LAST: 65,982                     (Hash: a9b4cf...)
-------------------------------------------------------------------------------------------------------------------------------------------------------
H5: Crack modeling topology         AssignSeam sharp crack vs          AssignSeam: 65,982–71,320 elements       SUPPORTED          STAGE_A_FORENSICS_REPORT.json
    (Sharp seam vs Notch slit)      Blunt notch slit (w=0.001 mm)      Blunt notch: 58,570–74,261 elements      (Minor impact)     (Hash: 3f21da...)
-------------------------------------------------------------------------------------------------------------------------------------------------------
H6: Coarse seed resolution          hcms = 0.02 mm vs 0.03 mm          hcms=0.02: 66,142 (1%), 16,786 (2%)      SUPPORTED          STAGE_B_INVESTIGATION_MATRIX.json
    (Table 1 / Table 3 trend)       at errorTarget in [1.0, 2.0, 5.0]  hcms=0.03: 48,856 (1%), 12,679 (2%)      (Consistent trend) (Hash: a9b4cf...)
-------------------------------------------------------------------------------------------------------------------------------------------------------
H7: Abaqus release-dependent        Compare Abaqus 2023 vs             Abq 2023: 15,396 (2%), 58,679 (1%)       NOT ESTABLISHED    Requires identical deck SHA
    sizing algorithm divergence     Abaqus 2024 across error targets   Abq 2024: 16,786 (2%), 66,142 (1%)                          cross-platform run
=======================================================================================================================================================
```

---

## 5. Definition and Units of Error Indicator (MISESERI)

From the Abaqus Analysis User's Guide (Section "Error Indicator Output" & "Adaptive Remeshing"):
- `MISESERI` is the **Mises equivalent stress error indicator**, computed via Zienkiewicz-Zhu Superconvergent Patch Recovery (SPR) as the Mises equivalent of the stress difference tensor $\mathbf{e}_\sigma = \mathbf{\sigma}^* - \mathbf{\sigma}_h$:
  $$\text{MISESERI} = \sqrt{\frac{3}{2} \mathbf{s}_e : \mathbf{s}_e}, \quad \mathbf{s}_e = \mathbf{e}_\sigma - \frac{1}{3}\text{tr}(\mathbf{e}_\sigma)\mathbf{I}$$
- It carries the **units of stress ($\mathrm{MPa}$ or $\mathrm{kN/mm^2}$)**.
- It does **not** carry stress intensity factor units ($\mathrm{MPa \cdot mm^{1/2}}$).
- When normalized by the domain-average equivalent stress measure `MISESAVG`:
  $$\eta_i = \frac{\text{MISESERI}_i}{\text{MISESAVG}}$$
  the relative error $\eta_i$ is **dimensionless**.

---

## 6. Authoritative Scientific Conclusion

1. **Reproduction Milestone:** Task 5 quantitative adaptive reproduction is **PASSED** based on authoritative job `1400395.mmaster02`.
2. **Preprocessing Status:** Exact reproduction of the nominal 1% preprocessing mesh count remains **DOCUMENTED_UNRESOLVABLE_FROM_PUBLISHED_INFORMATION**. The published text does not contain sufficient implementation details to reproduce 13,941 elements with nominal `errorTarget = 1.0%` under native Abaqus `UNIFORM_ERROR` remeshing.
3. **Reconciliation Status:** The 2% reconstruction empirically reproduces the target mesh count ($15,396$ vs $13,941$, $+10.4\%$) and mechanical response ($F_{\text{peak}} = 0.7482\,\mathrm{kN}$, $-1.29\%$), but is cataloged with the subfinding `EMPIRICALLY_RECONCILED_AT_2PCT_BUT_NOT_PROVEN_EQUIVALENT_TO_PUBLISHED_1PCT`.
4. **Next Actions:** No further Task-5 nonlinear simulations are required or permitted. Attention is returned to the active Task-6 IMFD ABAQUSER visualization workflow.

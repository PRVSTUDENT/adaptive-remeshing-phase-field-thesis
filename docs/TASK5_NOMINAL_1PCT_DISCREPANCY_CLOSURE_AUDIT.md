# Task 5 Provenance Closure Audit: Pandey & Kumar Mode-I Nominal-1% Mesh Discrepancy

**Audit Scope:** Forensic Evaluation of the Nominal 1.0% errorTarget Mesh-Density Discrepancy in Pandey & Kumar (2025) Mode-I Adaptive Remeshing  
**Date:** 2026-09-02  
**Final Scientific Status:** **DOCUMENTED_UNRESOLVABLE_FROM_PUBLISHED_INFORMATION**  
**Subfinding:** **EMPIRICALLY_RECONCILED_AT_2PCT_BUT_NOT_PROVEN_EQUIVALENT_TO_PUBLISHED_1PCT**  
**Authoritative Quantitative Reproduction Job:** `1400395.mmaster02` (2.0% Adaptive Refinement, 15,396 Elements, $F_{\text{peak}} = 0.7482\,\mathrm{kN}$, $-1.29\%$ error vs target, **Preserved & Qualified**)

---

## 1. Problem Statement & Audit Objectives

The Pandey & Kumar (2025) Mode-I benchmark paper (*Comput. Model. Eng. Sci.* 144(3), 3251–3276) reports:
- In Section 4.1 (text) and Listing 1 (Python code): `errorTarget = 1.0%`, initial coarse mesh $h_{\mathrm{cms}} = 0.02\,\mathrm{mm}$, $h_{\min} = 0.001\,\mathrm{mm}$, $h_{\max} = 0.02\,\mathrm{mm}$, resulting in an adaptive mesh of **13,941 linear quadratic and triangular elements**.
- Direct Abaqus reconstruction with sharp seam (`1399632.mmaster02`): Produced **71,320 physical elements** ($69,443$ Quad4, $1,877$ Tri3) when executed with `errorTarget = 1.0%`.
- An earlier blunt-notch trial (`1398807.mmaster02`) produced **74,261 physical elements** ($72,260$ Quad4, $2,001$ Tri3) due to corner notch stress concentrations and was rejected.

This controlled audit was conducted to isolate the exact cause of this mesh density difference and reconcile the published preprocessing instructions with numerical reality.

---

## 2. Separate Dataset Provenance

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

## 3. Verbatim Literature Evidence Extraction

From Pandey & Kumar (2025):
- **Section 4.1 (Page 3265):** "To identify the MISESERI values, a displacement control scheme is applied with increment size $\Delta u_1 = 10^{-3}$ for 500 increments, followed by increment size $\Delta u_2 = 5 \times 10^{-4}$ for the subsequent 1000 increments... The adaptive remesh is then incorporated with a global mesh size of $0.02\,\mathrm{mm}$ and locally refined mesh size $h = 0.001\,\mathrm{mm}$, comprising 13,941 linear quadratic and triangular elements (refer to Fig. 5)..."
- **Listing 1 (Page 3262):** `errorTarget = 1.0`, `refinementFactor = 10`, `sizingMethod = UNIFORM_ERROR`, `outputFrequency = ALL_INCREMENTS`, `minElementSize = 0.001`, `maxElementSize = 0.02`.
- **Table 3 (Page 3270):** Sensitivity analysis at $h_{\mathrm{cms}} = 0.03\,\mathrm{mm}$ reports `errorTarget = 2` (6,644 elements), `5` (4,547 elements), `10` (3,815 elements), `20` (3,281 elements).
- **Text Provenance Check:** The paper **never** associates 13,941 elements with `errorTarget = 2.0%`. It reports 13,941 elements directly under the primary Mode-I case where Listing 1 prescribes `errorTarget = 1.0`.

---

## 4. Controlled Hypothesis Testing and Scientific Classification

```text
=======================================================================================================================================================
HYPOTHESIS                          CONTROLLED TEST                    VERIFIED RESULT                          CLASSIFICATION     EVIDENCE ARTIFACT
=======================================================================================================================================================
H1: Sizing response to singular     RemeshingRule errorTarget sweep    1.0% -> 66,142 elements (marks >80% dom) CONFIRMED          STAGE_B_INVESTIGATION_MATRIX.json
    elastic crack tip               in [1.0, 1.5, 2.0, 2.5, 3.0, 5.0]  2.0% -> 15,396–16,786 (local crack band)
                                                                       5.0% -> 4,194–4,250 (tip circle only)
-------------------------------------------------------------------------------------------------------------------------------------------------------
H2: Empirical mesh reconciliation   Compare 2.0% adaptive mesh to      2.0% yields 15,396 elements (+10.4% vs   SUPPORTED          1400395.mmaster02
    via errorTarget = 2.0%          literature 13,941 target           13,941) and reproduces F-u within 1.29%  (Empirical Only)   (Deck: c745a42f2c...)
-------------------------------------------------------------------------------------------------------------------------------------------------------
H3: Paper loading schedule          Paper 2-step (1500 incs) vs        Paper 2-step: 66,142 elements            RULED OUT          STAGE_B_INVESTIGATION_MATRIX.json
    (Delta u1=1e-3, Delta u2=5e-4)  Single-step (10 incs)              Single-step: 65,982 elements (<0.24%)
-------------------------------------------------------------------------------------------------------------------------------------------------------
H4: Step & frame selection          Step-1 vs Step-2 and               Step-2 ALL: 66,142; Step-2 LAST: 66,142  RULED OUT          STAGE_B_INVESTIGATION_MATRIX.json
    semantics (ALL vs LAST)         ALL_INCREMENTS vs LAST_INCREMENT   Step-1 ALL: 65,982; Step-1 LAST: 65,982
-------------------------------------------------------------------------------------------------------------------------------------------------------
H5: Crack modeling topology         AssignSeam sharp crack vs          AssignSeam: 65,982–71,320 elements       SUPPORTED          STAGE_A_FORENSICS_REPORT.json
    (Sharp seam vs Notch slit)      Blunt notch slit (w=0.001 mm)      Blunt notch: 58,570–74,261 elements      (Minor impact)
-------------------------------------------------------------------------------------------------------------------------------------------------------
H6: Coarse seed resolution          hcms = 0.02 mm vs 0.03 mm          hcms=0.02: 66,142 (1%), 16,786 (2%)      SUPPORTED          STAGE_B_INVESTIGATION_MATRIX.json
    (Table 1 / Table 3 trend)       at errorTarget in [1.0, 2.0, 5.0]  hcms=0.03: 48,856 (1%), 12,679 (2%)      (Consistent trend)
-------------------------------------------------------------------------------------------------------------------------------------------------------
H7: Abaqus release-dependent        Compare Abaqus 2023 vs             Abq 2023: 15,396 (2%), 58,679 (1%)       NOT ESTABLISHED    Requires identical deck SHA
    sizing algorithm divergence     Abaqus 2024 across error targets   Abq 2024: 16,786 (2%), 66,142 (1%)                          cross-platform run
=======================================================================================================================================================
```

---

## 5. Physical Mechanism and Definition of MISESERI

In the Abaqus Analysis User's Guide, `MISESERI` is defined as the Mises equivalent of the stress error tensor:
$$\mathbf{e}_\sigma = \mathbf{\sigma}^* - \mathbf{\sigma}_h, \quad \text{MISESERI} = \sqrt{\frac{3}{2}\mathbf{s}_e : \mathbf{s}_e}$$
- **Units:** `MISESERI` carries units of **stress ($\mathrm{MPa}$)**.
- In linear elasticity of a cracked body, stresses scale as $\sigma_{ij} \sim K_I / \sqrt{2\pi r} \propto u$.
- Because both `MISESERI` and domain-average stress `MISESAVG` scale linearly with $u$, the relative error $\eta_i = \text{MISESERI}_i / \text{MISESAVG}$ is **dimensionless and strictly time/scale-invariant** across all pre-analysis increments and frames.
- At $\eta_{\mathrm{target}} = 1.0\%$, the threshold is so strict that elements across $>80\%$ of the entire $1 \times 1\,\mathrm{mm}$ plate exceed the error target, forcing refinement down to $h \sim 0.001–0.0035\,\mathrm{mm}$ and yielding ~66,000–71,320 elements.

---

## 6. Authoritative Closure Summary

1. **Task-5 Quantitative Adaptive Reproduction:** **PASSED**, authoritative production job `1400395.mmaster02` ($F_{\text{peak}} = 0.7482\,\mathrm{kN}$, $-1.29\%$ error vs target, 0 cutbacks, Exit 0).
2. **Exact Published Nominal-1% Preprocessing Reproduction:** **DOCUMENTED_UNRESOLVABLE_FROM_PUBLISHED_INFORMATION**.
3. **Empirical 2% Reconstruction:** Reconciles the mesh density ($15,396$ vs $13,941$, $+10.4\%$) and mechanical response, but is not proven to be identical to the paper's nominal script parameters.
4. **Preservation:** Job `1400395.mmaster02` is preserved as the accepted quantitative reproduction.

# Technical Progress Report & Reconciliation Summary: Task 5 & Task 6 Final Production Closure

- **Author**: Pruthviraja Reddy Vandavagali (Matr. Nr. 68865)
- **Programme**: Master Thesis, Computational Materials Science, TU Bergakademie Freiberg
- **1st Examiner (Supervisor)**: Prof. Dipl.-Ing. Björn Kiefer, Ph.D.
- **2nd Examiner (Reviewer)**: Dr.-Ing. Stephan Roth
- **Institution**: Chair of Applied Mechanics – Solid Mechanics, Institute of Mechanics and Fluid Dynamics
- **Date**: 02 September 2026
- **Status**: **`TASK_5_ACCEPTED_AND_NOMINAL_1PCT_DISCREPANCY_PROVENANCE_CLOSED`**

---

## 1. Executive Purpose of this Document

This progress report documents the completion and formal closure of **Thesis Task 5** (Pandey & Kumar 2025 Mode-I Tensile Benchmark Reproduction with Adaptive Remeshing) and summarizes the forensic resolution of the **nominal-1% mesh discrepancy**.

### Key Deliverables & Outcomes:
1. **Task-5 Quantitative Adaptive Reproduction: PASSED (Authoritative Job `1400395.mmaster02`)**
   - Passes all 5 predeclared Task-5 scientific acceptance gates.
   - Peak Reaction Force: $F_{\text{peak}} = 0.7482\,\mathrm{kN}$ vs $0.7580\,\mathrm{kN}$ target ($-1.29\%$ error).
   - Peak Displacement: $u_{\text{peak}} = 0.005775\,\mathrm{mm}$ vs $0.005860\,\mathrm{mm}$ target ($-1.45\%$ error).
   - Initial Elastic Stiffness: $K_0 = 137.84\,\mathrm{kN/mm}$ vs $137.95\,\mathrm{kN/mm}$ ($-0.07\%$ difference).
   - Numerical Stability: 0 cutbacks, 0 numerical warnings, 7,000 fixed increments, Exit status 0.

2. **Nominal-1% Preprocessing Mesh Discrepancy: AUDITED & RECONCILED**
   - **Published Literature Citation:** Listing 1 cites `errorTarget = 1.0%` on $h_{\mathrm{cms}} = 0.02\,\mathrm{mm}$, reporting $\approx 13,941$ elements.
   - **Numerical Reconstruction Reality:** Executing native Abaqus advancing-front `UNIFORM_ERROR` remeshing at `errorTarget = 1.0%` on a cracked linear elastic body produces ~66,000–71,320 elements.
   - **Forensic Status:** `DOCUMENTED_UNRESOLVABLE_FROM_PUBLISHED_INFORMATION`.
   - **Empirical Subfinding:** `EMPIRICALLY_RECONCILED_AT_2PCT_BUT_NOT_PROVEN_EQUIVALENT_TO_PUBLISHED_1PCT`.
   - **Scientific Guard:** The 2.0% reconstruction ($15,396$ elements, $+10.4\%$ match) reproduces the localized crack-corridor refinement and the experimental force-displacement curve, but is not retroactively claimed to be proven identical to the authors' nominal script listing.

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

## 3. Systematic Hypothesis Testing & Cause Isolation

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

## 4. Current Campaign Status & Next Steps

1. **Task 5:** Closed and fully reconciled. Job `1400395.mmaster02` is preserved as the authoritative quantitative reproduction (`SCIENTIFICALLY_ACCEPTED`). Exact published nominal-1% preprocessing reproduction is classified as `DOCUMENTED_UNRESOLVABLE_FROM_PUBLISHED_INFORMATION`.
2. **Task 6:** Formally classified as **`TASK6_BLOCKED_EXTERNAL_ABAQUSER_DEPENDENCY`**, while preserving **`COMPANION_VISUALIZATION_BRIDGE_FULLY_VERIFIED`** under Job `1400408.mmaster02`:
   - **Companion Bridge Parity:** 0.000000% mechanical difference vs Task 5 across all 7,028 increments, confirming zero parasitic stiffness.
   - **Phase Field Overshoot:** Peak overshoot bounded at $\max(d) = 1.00518084$ (+0.52% excess across 0.175% of elements) and relaxes to $1.004512$ at fracture completion without growing. Proven to originate in the solved UEL field (`FORMULATION_LEVEL_NOT_VISUALIZATION_TRANSFER`), with detailed mechanism cataloged as `POSSIBLE_FORMULATION_DISCRETIZATION_CAUSE`.
   - **Authentic IMFD ABAQUSER Dependency:** The external post-processing tool (Roth et al., 2012/2014, GACM) requires internal IMFD access and is not present in the accessible environment (`REQUIRES_IMFD_INTERNAL_ACCESS`).
   - **Supervisor Action Item:** Formal closure of the proposal deliverable requires IMFD provision of the authentic ABAQUSER post-processing script/binary. Once received, it can be applied directly to existing verified ODB results (`PK_MODE1_PROPOSED_PFM_VIS.odb`) in post-processing without requiring additional solver runs.
3. **Active Next Phase:** Task 7 remains paused until this external dependency boundary is formally aligned.

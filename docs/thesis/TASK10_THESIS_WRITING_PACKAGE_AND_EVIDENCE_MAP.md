# Master Thesis Writing Package & Full Evidence Traceability Map

**Thesis Title:** Application of Built-in Adaptive Remeshing and Mesh Refinement Features in Abaqus to Fracture Simulations Using Phase-Field User Elements  
**Author:** Master Thesis Candidate  
**Date:** September 3, 2026  
**Governing Task:** Task 10 (Thesis Writing Preparation)  
**Status:** **`TASK10_THESIS_WRITING_PACKAGE_READY`**  
**Evidence Provenance:** Tasks 1–9 Verified Solvers, Datasets, Scripts, and Ledgers

---

## 1. Proposal-Aligned Thesis Chapter Outline

```text
=======================================================================================================================================================
CHAPTER   TITLE                                                         CORRESPONDING PROPOSAL WORK PACKAGE & SCOPE
=======================================================================================================================================================
Chap 1    Introduction & Motivation                                     Task 1 & Proposal Background: Computational fracture, PFF vs discrete cracks
Chap 2    Phase-Field Fracture Theory & User-Element Formulation        Task 1: Variational formulation, AT1/AT2, split models, UEL/UMAT coupling
Chap 3    Literature Review: Adaptive Refinement & IMFD ABAQUSER        Task 2: Pandey & Kumar (2025), Molnar (2017), Diddige (2025), Roth (2012)
Chap 4    Native Abaqus Adaptive Remeshing & Python Pipeline            Task 4: SPR stress error indicator MISESERI, RemeshingRule, boundary preservation
Chap 5    Verification of Reference Baseline Without Refinement         Task 3: Standard uniform crack-band solve (Job 1398090, <0.03% error)
Chap 6    Adaptive Refinement Reproduction & Discrepancy Reconciliation Task 5: 2.0% reproduction (Job 1400395), nominal-1% forensic closure
Chap 7    Visualization Integration & External Dependency Boundary      Task 6: Companion facsimile UMAT bridge (Job 1400408) & ABAQUSER status
Chap 8    Fracture Benchmarks, Sensitivity Studies, & Meshing Rules     Tasks 7 & 8: INC2X (1400738), 3% mesh (1400739), 5% mesh (1400396), guidelines
Chap 9    Technical Workflow & Implementation Manual for Future Users   Task 9: Step-by-step reproduction guide, scripts, subroutine architecture
Chap 10   Conclusions & Outlook                                         Task 10: Summary of achievements, parameter rules, future work
=======================================================================================================================================================
```

---

## 2. Comprehensive Thesis Evidence Map

```text
=======================================================================================================================================================
CHAPTER / TOPIC          VERIFIED PBS JOBS   SCIENTIFIC STATUS          EVIDENCE ARTIFACTS / REPOSITORY PATHS                  KEY ACCEPTANCE GATES
=======================================================================================================================================================
Chap 1: Introduction     --                  DOCUMENTED                 docs/thesis/CHAP01_INTRODUCTION_AND_THEORY.tex         Thesis proposal scope
Chap 2: PFF Theory       1398090 (ref)       SCIENTIFICALLY_ACCEPTED    models/pandey_kumar_mode1/01_standard_pfm_reference/   Thermodynamic positivity
                                                                        models/pandey_kumar_mode1/f42_mixed_uel.for            (H >= 0, d in [0, 1])
Chap 3: Literature       --                  DOCUMENTED                 Literature review/, docs/thesis/THESIS_BIBLIOGRAPHY.tex Exact citation audit
Chap 4: Remeshing Impl.  1398806, 1399631    VERIFIED_END_TO_END        models/pandey_kumar_mode1/generate_mesh.py             Boundary preservation,
                                                                        models/pandey_kumar_mode1/execute_2pct_workflow.py     SPR error convergence
Chap 5: Task 3 Baseline  1398090.mmaster02   SCIENTIFICALLY_ACCEPTED    models/pandey_kumar_mode1/01_standard_pfm_reference/   F_peak = 0.7578 kN (-0.03%),
                                                                        PK_MODE1_STANDARD_PFM.dat, .sta, .msg, .odb            u_peak = 0.005857 mm (-0.05%)
Chap 6: Task 5 Repro     1400395.mmaster02   SCIENTIFICALLY_ACCEPTED    models/pandey_kumar_mode1/06_production_adaptive_2pct/ F_peak = 0.7482 kN (-1.29%),
                                                                        PK_MODE1_PROPOSED_PFM.dat, .sta, .msg, .odb            u_peak = 0.005775 mm (-1.45%)
                         1399632.mmaster02   DOCUMENTED_UNRESOLVABLE    docs/TASK5_NOMINAL_1PCT_DISCREPANCY_CLOSURE_AUDIT.md   Forensic 1% audit closure
Chap 7: Task 6 Vis       1400408.mmaster02   COMPANION_BRIDGE_VERIFIED  models/abaquser_visualization/task6_production_2pct/   0.000000% RF parity,
                                             TASK6_BLOCKED_DEPENDENCY   docs/supervisor_reports/TASK6_ABAQUSER_REQUEST.md      5 CAE PNG contour plots
Chap 8: Task 7 Sens.     1400738.mmaster02   SCIENTIFICALLY_EVALUATED   models/pandey_kumar_mode1/08_task7_inc_sens_2x/        INC2X: -48.4% compute time
                         1400739.mmaster02   SCIENTIFICALLY_EVALUATED   models/pandey_kumar_mode1/09_task7_mesh_sens_3pct/     3% mesh: +12.84% force error
                         1400396.mmaster02   SCIENTIFICALLY_EVALUATED   models/pandey_kumar_mode1/07_production_adaptive_5pct/ 5% mesh: +20.48% disp error
Chap 8: Task 8 Rules     --                  COMPLETE                   docs/guides/TASK8_MESHING_AND_INCREMENT_RECOMMENDATIONS errorTarget=2.0% rule
Chap 9: Task 9 Manual    --                  COMPLETE                   docs/guides/TASK9_FUTURE_USER_WORKFLOW_GUIDE.md        Step-by-step instructions
Chap 10: Conclusions     --                  COMPLETE                   docs/thesis/CHAP08_SYNTHESIS_AND_CONCLUSIONS.tex       Consolidated thesis summary
=======================================================================================================================================================
```

---

## 3. Verified Figures & Tables Inventory

All figures and tables listed below are constructed from **directly verified solver outputs and cluster artifacts**:

### 3.1 Figures Inventory
1. **Figure 1.1:** Specimen geometry, dimensions ($1.0 \times 1.0\,\mathrm{mm}$), boundary conditions, and horizontal sharp notch seam ($a=0.5\,\mathrm{mm}$).
2. **Figure 4.1:** Multi-pass mesh refinement evolution: Coarse base mesh ($2{,}906$ elements) $\rightarrow$ Intermediate pass $\rightarrow$ Final 2.0% adaptive mesh ($15{,}396$ physical elements).
3. **Figure 4.2:** Distribution of Mises stress error indicator (`MISESERI`) in Step 1, highlighting the process-zone refinement band along the notch plane ($y=0.5\,\mathrm{mm}$).
4. **Figure 5.1:** Reaction force vs prescribed displacement comparison: Task-3 fixed-mesh baseline (`1398090.mmaster02`) vs published target (*Pandey & Kumar 2025*), showing $<0.03\%$ deviation.
5. **Figure 6.1:** Reaction force vs displacement curve for accepted Task-5 2.0% adaptive reproduction (`1400395.mmaster02`) against literature benchmark.
6. **Figure 6.2:** Comparative load-displacement curves demonstrating the effect of error thresholds: $1.0\%$ (over-refined), $2.0\%$ (accepted), $3.0\%$ (numerical toughening), and $5.0\%$ (delayed localization).
7. **Figure 7.1:** Headless Abaqus/CAE phase-field damage contours ($d$) from production run `1400408.mmaster02` across 5 deformation stages ($u = 0.002, 0.005, 0.0058, 0.007, 0.010\,\mathrm{mm}$).
8. **Figure 7.2:** Point-by-point mechanical parity plot confirming exact $0.000000\%$ reaction force difference between Task 6 (`1400408`) and Task 5 (`1400395`).
9. **Figure 8.1:** Increment sensitivity comparison: Baseline $7{,}000$-increment schedule vs accelerated $3{,}500$-increment schedule (`1400738.mmaster02`), showing identical post-peak softening curves.
10. **Figure 8.2:** Mesh sizing sensitivity curves ($2.0\%$ vs $3.0\%$ vs $5.0\%$) showing the emergence of artificial numerical toughening with coarse transition elements.

### 3.2 Tables Inventory
1. **Table 5.1:** Quantitative metrics of the Task-3 fixed baseline (`1398090.mmaster02`) vs published reference.
2. **Table 6.1:** Comprehensive validation matrix of the accepted Task-5 2.0% adaptive reproduction (`1400395.mmaster02`) against all five predeclared acceptance gates.
3. **Table 6.2:** Forensic discrepancy audit of the nominal 1.0% error target reconstruction (`1399632.mmaster02`).
4. **Table 7.1:** Task-6 companion visualization bridge verification matrix (`1400408.mmaster02`), detailing mechanical parity, state transfer, and external dependency boundaries.
5. **Table 8.1:** Discretization sensitivity table ($2\%$, $3\%$, $5\%$, fixed) relating element count, local $h/l_0$, and peak errors.
6. **Table 8.2:** Load incrementation efficiency and accuracy trade-off table ($7{,}000$ vs $3{,}500$ increments).
7. **Table 8.3:** Recommended meshing, remeshing rule, and time-stepping parameter matrix for future users.

---

## 4. Preserved Scientific Governance Boundaries

1. **`SCIENTIFICALLY_ACCEPTED` Baseline:**
   - Task 3 fixed baseline (`1398090.mmaster02`) and Task 5 adaptive reproduction (`1400395.mmaster02`) are formally accepted.
2. **`SCIENTIFICALLY_EVALUATED` Sensitivity Cases:**
   - Sensitivity runs (`1400396`, `1400738`, `1400739`) are documented as parameter studies confirming the necessity of the $2.0\%$ mesh and validating $3{,}500$ increments, not substituted for the accepted reproduction.
3. **`TASK6_BLOCKED_EXTERNAL_ABAQUSER_DEPENDENCY` Boundary:**
   - The companion facsimile UMAT bridge is **`COMPANION_VISUALIZATION_BRIDGE_FULLY_VERIFIED`**.
   - The authentic IMFD ABAQUSER external tool integration is preserved as **`TASK6_BLOCKED_EXTERNAL_ABAQUSER_DEPENDENCY`** awaiting institute software provision. Task 6 is not misrepresented as complete.

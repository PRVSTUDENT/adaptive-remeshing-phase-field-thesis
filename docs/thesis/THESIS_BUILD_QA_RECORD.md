# Master Thesis Build QA & Quality Control Record

- **Document Target**: `docs/thesis/THESIS_FACULTY_BUILD.pdf`
- **Source File**: `docs/thesis/THESIS_FACULTY_BUILD.tex`
- **Compiler**: `pdfTeX, Version 3.141592653-2.6-1.40.28 (MiKTeX 25.12)`
- **Build Status**: **`PASS (Exit code 0)`**
- **Date**: 2026-08-21T16:07:20+02:00
- **Total Pages**: 57 pages
- **File Size**: 1,038,718 bytes (1.04 MB)

---

## 1. Build Verification & Stabilization Summary

| Build Pass | Command Line | Status | Output State / Notes |
| :--- | :--- | :--- | :--- |
| **Pass 1** | `pdflatex -interaction=nonstopmode -halt-on-error THESIS_FACULTY_BUILD.tex` | `PASS` | Auxiliary `.aux`, `.toc`, `.lof`, `.lot` updated; 57 pages generated. |
| **Pass 2** | `pdflatex -interaction=nonstopmode -halt-on-error THESIS_FACULTY_BUILD.tex` | `PASS` | All cross-references, figure links, table links, and TOC stabilized; zero undefined references. |

---

## 2. Included Chapters, Sections, and Structural Audit

- **Chapter 1**: Stage A Molnar Single-Notch Benchmark (pp. 1--7)
- **Chapter 2**: Representative Results and Evidence Figures (pp. 8--11)
- **Chapter 3**: Offline MISESERI Pre-Refinement for Layered Phase-Field UEL Models (pp. 12--13)
- **Chapter 4**: Controlled State Transfer for Phase-Field UEL Workflows (pp. 14--20)
- **Chapter 5**: State Transfer and Active-Set Evolution (pp. 21--22)
- **Chapter 6**: Interrupted-Transfer Checkpoint Correction and Parallelization Study (pp. 23--26)
- **Chapter 7**: Stage F: Mode-II Mixed-Mode Phase-Field Fracture Benchmark (pp. 27--37)
- **Chapter 8**: **Stage G: Production Adaptive Remeshing and Validation** (pp. 38--43)
  - Section 8.1: Introduction and Governed Methodology Ladder (Table 8.1)
  - Section 8.2: Production Discretizations and Execution Provenance (Table 8.2)
  - Section 8.3: Three-Layer Validation Framework
    - Subsection 8.3.1: Layer 1: Execution Validation
    - Subsection 8.3.2: Layer 2: Hard Physical Invariant Verification (Table 8.3)
    - Subsection 8.3.3: Layer 3: Adaptive Accuracy and Computational Efficiency (Table 8.4, Table 8.5, Figures 8.1, 8.2, 8.3)
  - Section 8.4: Energy Accounting and Methodological Limitations
  - Section 8.5: Conclusion
- **Chapter 9**: Recommendations and Decision Tree (p. 44)
- **Appendix A**: Stage A Reproducibility Appendix (pp. 45--48)
- **Bibliography**: Complete references (pp. 49--51)

---

## 3. Audit of Frozen Stage-G Values in Thesis

1. **Discretization Counts**:
   - $H_1$ Reference: $N_{\mathrm{phys}} = \mathbf{12,064}$ (12,382 nodes) $\to$ Verified.
   - $H_2$ Baseline: $N_{\mathrm{phys}} = \mathbf{33,852}$ (34,508 nodes) $\to$ Verified (corrected from prior informal 20k estimates).
   - Candidate 1 (MM): $N_{\mathrm{phys}} = \mathbf{2,206}$ (2,294 nodes) $\to$ Verified.
   - Candidate 2 (PK5): $N_{\mathrm{phys}} = \mathbf{4,894}$ (4,998 nodes) $\to$ Verified.
2. **Increment & Frame Counts**:
   - Step 1: 500 direct increments.
   - Step 2: 2,000 direct increments.
   - Total: **2,500 accepted solver increments** (72 saved ODB field frames) $\to$ Verified.
3. **Domain-A Accuracy Metrics ($0 \le U_1 \le 0.009250\,\text{mm}$)**:
   - Candidate 1 (MM) vs $H_1$: Normalized $L_2 = \mathbf{1.4249\%}$, Rel. Work $= \mathbf{0.8134\%}$, Stiffness Error $= \mathbf{0.2425\%}$ $\to$ Verified.
   - Candidate 2 (PK5) vs $H_1$: Normalized $L_2 = \mathbf{1.1467\%}$, Rel. Work $= \mathbf{0.5751\%}$, Stiffness Error $= \mathbf{0.1003\%}$ $\to$ Verified.
   - Cross-candidate mutual discrepancy: $L_2 = 0.3003\%$, Rel. Work $= 0.2370\%$ $\to$ Correctly separated.
4. **Damage Initiation ($d \ge 0.5$)**:
   - $H_1 = 0.007750\,\text{mm}$, $H_2 = 0.007750\,\text{mm}$, MM $= 0.008250\,\text{mm}$, PK5 $= 0.008250\,\text{mm}$ at saved field frames ($\Delta U_1 = 0.25\,\mu\text{m}$) $\to$ Bracketed without unevidenced causal claims.
5. **Computational Cost Ratios**:
   - $H_2$ Baseline CPU: $14,455.0\,\text{s}$ (walltime-censored at $0.009250\,\text{mm}$).
   - MM Adaptive CPU: $1,180.0\,\text{s}$ $\to$ **`12.25x scheduler-CPU ratio`**.
   - PK5 Adaptive CPU: $2,600.0\,\text{s}$ $\to$ **`5.56x scheduler-CPU ratio`**.
6. **Hard Physical Invariants**:
   - $0 \le d \le 0.9840$, $H \ge 0$, zero irreversibility/history violations independently verified across all 72 saved ODB frames under `CONTINUOUS_PHASE_ONLY`.
7. **Candidate Role Governance**:
   - MM (Primary Efficiency Candidate) and PK5 (Corridor Sensitivity Candidate) explicitly retained as `PROVISIONAL_REQUIRES_HUMAN_APPROVAL`.

---

## 4. Final Quality Control Status

- **LaTeX Syntax & Warnings**: **0 errors**, **0 undefined references**, **0 broken labels**.
- **Vector Graphics & Tables**: All 3 publication-ready PDF figures embedded cleanly at native vector resolution; all tables formatted using booktabs.
- **Thesis Scientific Milestone**: Complete simulation campaign closed; manuscript quality-control pass **`PASSED`**.

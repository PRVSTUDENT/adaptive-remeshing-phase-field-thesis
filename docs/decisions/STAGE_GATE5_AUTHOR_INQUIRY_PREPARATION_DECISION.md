# Decision Record: Gate 5 Corresponding-Author Reproducibility Inquiry Preparation

**Date:** September 13, 2026  
**Document Reference:** `STAGE_GATE5_AUTHOR_INQUIRY_PREPARATION_DECISION.md`  
**Decision Classification:** `AUTHOR_INFORMATION_REQUEST_READY_FOR_HUMAN_APPROVAL_UNSENT`  
**Governing Task:** `TASK_MODE1_GATE5_AUTHOR_INQUIRY_DRAFT`  
**Related Documents:**
- [`GATE5_AUTHOR_REPRODUCIBILITY_INQUIRY_DRAFT.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/GATE5_AUTHOR_REPRODUCIBILITY_INQUIRY_DRAFT.md)
- [`GATE5_PRIORITY_B_REMAINING_HYPOTHESIS_MATRIX.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/GATE5_PRIORITY_B_REMAINING_HYPOTHESIS_MATRIX.md)
- [`GATE5_EXTERNAL_INFORMATION_BOUNDARY.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/GATE5_EXTERNAL_INFORMATION_BOUNDARY.md)
- [`docs/thesis/figures/figure_gate5_author_inquiry_mesh_comparison.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/figures/figure_gate5_author_inquiry_mesh_comparison.png)

---

## 1. Context & Motivation

Following an exhaustive forensic audit across 13 candidate numerical, algorithmic, formulation, and software dimensions, the discrepancy between the published nominal Mode-I benchmark mesh count ($\sim 13,941$ finite elements, Section 4.1) and the publication-literal reproduction of Listing 1 ($71,320$ finite elements) has been rigorously isolated:
- Linux Abaqus releases (2021.HF26, 2022 GA, 2023.HF4) yield **identical substantive mesh topology and geometry** ($71,320$ finite elements: $69,443$ CPE4 + $1,877$ CPE3, $70,845$ nodes).
- Windows Abaqus 2024 GA yields **71,904 elements** (+0.82% variance, `RELEASE_PLUS_PLATFORM_CONFOUNDED`).
- Pre-analysis load amplitude and coarse mesh seed/algorithm controls were proven invariant.
- Listing 1 hardcodes `errorTarget=1.0`, while Section 4.1 narrative omits explicit parameter linkage for the 13,941 figure (`PUBLICATION_LINKAGE_AMBIGUOUS`).

To prevent unscientific parameter tuning (e.g. arbitrarily forcing `errorTarget=2.0`), the information boundary has been formally established.

---

## 2. Decision Summary

1. **Gate 5 Research Status**: Classified as `GATE5_REPRODUCTION_DISCREPANCY_RESOLUTION_ACTIVE` / `UNRESOLVED_WITH_PUBLICATION_INFORMATION_MISSING` until human/supervisor determination.
2. **Author Inquiry Document**: A minimal, professional 7-question technical inquiry to corresponding author Dr. Sachin Kumar has been prepared and formatted in [`GATE5_AUTHOR_REPRODUCIBILITY_INQUIRY_DRAFT.md`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/supervisor_reports/GATE5_AUTHOR_REPRODUCIBILITY_INQUIRY_DRAFT.md).
3. **Transmission Invariant**: The inquiry is marked `AUTHOR_INFORMATION_REQUEST_READY_FOR_HUMAN_APPROVAL_UNSENT` and shall **NOT** be transmitted without explicit written human/supervisor authorization.
4. **Visual Comparison Artifact**: A side-by-side comparative figure and release table has been generated at [`figure_gate5_author_inquiry_mesh_comparison.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/docs/thesis/figures/figure_gate5_author_inquiry_mesh_comparison.png) for human/supervisor review.
5. **No Speculative Solver Submissions**: No further speculative Priority-B simulations shall be submitted in this phase.

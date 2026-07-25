# WP7-F3 faculty-template integration

Date: 2026-07-25  
Classification: `wp7_faculty_template_integration_candidate`

## Decision

A clean A4 faculty-style thesis candidate has been assembled from the frozen
scientific closeout using official assignment-sheet front matter. No official
faculty `.tex`/Word template was available in the repository, so this is a
**candidate layout**, not a claim of final faculty-format compliance.

This task is documentation only. It authorizes no Abaqus, PBS, Stage-P, or
scientific execution.

## Front-matter freeze (assignment sheet)

```text
Title:
Application of Built-in Adaptive Remeshing and Mesh Refinement Features in
Abaqus to Fracture Simulations Using Phase-field User Elements

Author:
Pruthviraja Reddy Vandavagali

Matriculation number:
68865

Degree:
Master of Science

Course of study:
Master Computational Materials Science

University:
Technische Universität Bergakademie Freiberg

Faculty:
Faculty of Mechanical, Process and Energy Engineering

Institute:
Institute of Mechanics and Fluid Dynamics

Chair/Division:
Applied Mechanics – Solid Mechanics

1st Examiner (Supervisor):
Prof. Dipl.-Ing. Björn Kiefer, Ph.D.

2nd Examiner (Reviewer):
Dr.-Ing. Stephan Roth

Date of issue:
13 July 2026

Submission deadline:
12 January 2027
```

Notes:

- Siddhi Avinash Patil is **not** listed as supervisor or examiner.
- The shorter progress-report title is used only as a running title.
- The official submission date remains unset until the final hand-in day is
  known; the title page records issue date and deadline only.

## Document additions delivered

| Requirement | Delivery |
|---|---|
| Faculty title page | `docs/thesis/THESIS_FACULTY_BUILD.tex` |
| Formal abstract | `docs/thesis/THESIS_ABSTRACT.tex` |
| Bibliography + citations | `docs/thesis/THESIS_BIBLIOGRAPHY.tex` plus in-text cites in Stage A/C/recommendations and abstract |
| Five key figures | `docs/thesis/THESIS_KEY_FIGURES.tex` |
| Main-prose path cleanup | Stage D scratch absolute paths rewritten to repository/job-relative wording |
| Appendix path retention | Stage A reproducibility appendix keeps justified cluster evidence paths |

## Embedded figures

1. Baseline RF–U: `results/figures/stage_a_baseline/single_notch_rf_u_curve.png`
2. RF–U mesh comparison: `results/figures/molnar_lc015_h_convergence/01_rf_u_h0_h1_h2.png`
3. MISESERI refined comparison: `results/figures/stage_c_final/01_rf_u_h0_h1_h2_refined_v3.png`
4. Stage D workflow: `results/final/stage_d/figures/stage_d_workflow.png`
5. Active-set limitation: `results/final/stage_d/figures/violating_active_nodes_vs_displacement.png`

Captions restate withheld claims (post-peak, D3D-A1 restart, online remeshing).

## Faculty PDF build

```text
entrypoint: docs/thesis/THESIS_FACULTY_BUILD.tex
compiler: Tectonic 0.16.9 (bundled)
output: results/latex_build_wp7_f3_faculty/THESIS_FACULTY_BUILD.pdf
pages: 39
bytes: 570014
sha256: bd22c96b57175a109394725f018cf02a3770cfafea509d891afc83fb3250efcc
unresolved_references: 0
undefined_citations: 0
```

The WP7-F2 closeout hash
`bf0dbf8fb4ad306a8cbfdc0dd9ea5b60304c07299b86cdc0f2034c0c572529f8` identifies
only the 30-page scientific closeout PDF and is **not** reused here.

## Gate status

```text
front_matter_complete: true
abstract_complete: true
bibliography_resolved: true
figures_embedded_and_readable: true
absolute_machine_paths_reviewed: true
human_print_scale_review_complete: false
administrative_requirements_verified: false
supervisor_review_complete: false
ready_for_submission: false
```

`figures_embedded_and_readable: true` means the PDF embeds the five selected
figures without missing inputs and without unresolved references. Final human
print-scale readability inspection remains a separate gate.

## Remaining human actions

1. Print or PDF-zoom review of figure labels/legends at final scale.
2. Confirm page-range/imprint details for Pandey and Diddige bibliography
   entries against the published PDFs if the faculty deposit requires full
   imprint data.
3. Complete administrative portal forms and declarations.
4. Obtain supervisor/examiner sign-off.
5. Enter the actual submission date only on the hand-in day.
6. If an official faculty template is later provided, reflow this content into
   that template and recompute a new PDF SHA-256.

## Claim boundary

Unchanged from `docs/thesis/FINAL_CLAIM_MATRIX.md` and WP7 closeout:

- peak/pre-peak RF–U supported within tested scopes;
- unrestricted post-peak and crack-path mesh independence not supported;
- D2C case-specific; P3-T4 no threaded evidence; MPI/hybrid unqualified;
- D3D-A1 not an accepted mechanical restart;
- ABAQUSER externally blocked;
- validated online adaptive remeshing not claimed.

## Evidence

- `docs/thesis/THESIS_FACULTY_BUILD.tex`
- `docs/thesis/THESIS_ABSTRACT.tex`
- `docs/thesis/THESIS_BIBLIOGRAPHY.tex`
- `docs/thesis/THESIS_KEY_FIGURES.tex`
- `results/final/THESIS_FACULTY_PACKAGE_MANIFEST.json`
- `results/final/THESIS_FACULTY_PDF_RECORD.txt`
- `results/latex_build_wp7_f3_faculty/THESIS_FACULTY_BUILD.pdf` (local artifact)

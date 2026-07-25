# Thesis submission checklist

Classification: `wp7_thesis_submission_package_review_complete`  
Date: 2026-07-25

## Freeze

| Item | Value |
|---|---|
| Source revision | `fbc41bb279b97c83d53a03889f1ca9dcc748c067` |
| Substantive thesis revision | `fd12f0e992ef4769ae17872babca53784e7605d9` |
| Expected length | 30 pages |
| Verified PDF length | 30 pages |
| PDF tracked in Git | no (local/package artifact) |

## Automated checks

| Check | Result |
|---|---|
| `git diff --check` on frozen thesis/report/final paths | pass |
| `git diff --check` on full dirty worktree | fail (unrelated uncommitted handoff/docs whitespace only) |
| Checklist validator | pass |
| Repository unit tests | pass 100/100 |
| Standalone validation test scripts | pass 5/5 |
| Clean LaTeX build | pass 30 pages, Tectonic 0.16.9 |
| Final evidence-manifest validation | `final_thesis_evidence_manifest_pass` |
| Tracked ODB scan | pass (none) |
| Tracked unapproved-binary scan | pass (none) |
| Absolute-path scan (thesis sources) | review note: cluster evidence paths present in reproducibility text |
| TODO/placeholder scan (thesis sources) | pass (none) |
| LaTeX unresolved-reference scan | pass (0) |
| PDF page-count and checksum verification | pass |
| `agent_handoff/` sync utility | not run (unrelated dirty handoff state) |

## Document-content checks

| Check | Result | Notes |
|---|---|---|
| Title / author / program / supervisor / institution / date | incomplete | Closeout build has no faculty front matter |
| Abstract consistency | incomplete | No formal abstract in `THESIS_CLOSEOUT_BUILD.tex` |
| Introduction / objectives / conclusions / recommendations | pass within scope | Present as chapter objectives and final recommendations |
| Table of contents | pass | `\tableofcontents` matches included chapters/appendix |
| Figures/tables referenced and present in PDF | partial | Tables present; no `\includegraphics` in closeout PDF; Stage D PNGs exist as package sources only |
| Equation readability | pass at source level | Human final-scale check still required |
| Notation / units / terminology | pass | Consistent RF–U, H0/H1/H2-PUB, SDV15/16 usage |
| Bibliography and resolved citations | incomplete | No bibliography environment or `\cite` in closeout build |
| TODO / TBD / drafting notes | pass | None in `docs/thesis` sources |
| Accidental Windows absolute paths | pass | None in thesis sources |
| Cluster/home/scratch paths in reader-facing text | review note | Intentional evidence paths in Stage A appendix and Stage D chapter |
| Claims bounded by `FINAL_CLAIM_MATRIX.md` | pass | Supported and withheld claims both visible |
| Limitations consistent across conclusions/outlook | pass | Post-peak, D3D-A1, P3-T4, ABAQUSER, online remeshing withheld |

## Package inventory (submission candidate)

Include only when assembling the actual upload bundle:

1. `THESIS_CLOSEOUT_BUILD.pdf` (local build artifact)
2. Thesis TeX sources under `docs/thesis/` (entrypoint + chapters + appendix)
3. `docs/thesis/FINAL_CLAIM_MATRIX.md`
4. `results/final/FINAL_EVIDENCE_MANIFEST.json` and Stage D figure/table sources if reproducibility package is requested
5. This checklist, PDF record, build-warnings file, and package manifest
6. Faculty declaration / signed forms after portal check
7. SHA-256 record from `results/final/THESIS_SUBMISSION_PDF_RECORD.txt`

Do **not** include:

- ODB files
- scratch outputs
- temporary LaTeX products except the retained build log if audit requires it
- unsolicited cluster logs
- secrets, private mail, credentials, machine-specific config
- dirty unrelated `agent_handoff/` working-tree state

## Readiness flags

| Flag | Value |
|---|---|
| `scientific_content_frozen` | true |
| `submission_pdf_verified` | true |
| `administrative_requirements_verified` | false |
| `supervisor_review_complete` | false |
| `ready_for_submission` | false |

`ready_for_submission` must remain false until administrative portal requirements and final human PDF inspection are complete.

## Package README (contents)

This submission-package review freezes the scientific closeout PDF and evidence boundary at the listed revisions. It does **not** authorize simulations, reopen Stage P, or change claim scope. Before faculty upload, complete front-matter/forms against current official instructions and inspect the 30-page PDF visually.

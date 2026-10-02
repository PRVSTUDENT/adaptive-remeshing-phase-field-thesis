# Thesis report rebuild — 17 September 2026

## Preservation and scope

- Complete pre-edit backup: `../MA_AdaptiveRemeshing_Report_2026_main_BACKUP_20260917_115915/` (129 files).
- Original SHA-256 manifest: `../MA_AdaptiveRemeshing_Report_2026_main_BACKUP_20260917_115915/SOURCE_HASHES_SHA256.txt`.
- Original PDF: 54 pages, SHA-256 `010455CE7DFE828E6A93907794D179C5CB1B7CB0A541E49BFD50CBEC51240A08`.
- Rebuilt PDF baseline after the four review corrections: 18 pages, SHA-256 `3F9334541C493B9CD21D62B7D341EEA8F38CA6E3B46019ED1F6D1C1C2284D46C`.
- No Abaqus/PBS job was submitted and no solver or user-subroutine source was changed.

## Scientific and structural changes

The active report now follows the supervisor-approved Mode-I evidence boundary:

1. Introduction and phase-field foundations.
2. Mode-I benchmark and fixed-mesh reference.
3. Pandey–Kumar error-guided adaptive pre-refinement.
4. Current Mode-I qualification status and next steps.

The abstract was rewritten to distinguish verified project results, publication values, and unresolved work. The report now states that the publication's 26,282-element standard branch and 13,941-element adaptive branch are separate simulations; it does not present them as a before-and-after pair. It records the project reconstruction as 2,906 coarse finite elements and 2,906 scalar `WHOLE_ELEMENT` MISESERI values leading to 71,320 adapted finite elements using the published Listing-1 settings. The remaining 13,941-count difference is treated as an accepted publication-information limitation, not a failed tuning task.

The fixed reference and boundary-set diagnosis were rebuilt around verified values: Job 1398090 (`K0 = 137.945520 kN/mm`, `Fmax = 0.757778 kN`), corrected Job 1404933 (`K0 = 137.820804 kN/mm`, `Fmax = 0.745325 kN`), and independent elastic requalification Job 1405044 (`K0 = 138.021013 kN/mm`). The former `N_BOTTOM` formatting defect is explicitly separated from adaptive-mesh effects.

Mode-II, evolving state transfer, multi-resolution production claims, and unrelated HPC narrative were removed from the active evidential argument. They are mentioned only as deferred scope or future work. The next active sequence is energy-output exposure, global energy balance, full force–displacement comparison, spatial convergence, temporal convergence, and only then Mode-I transfer conservation.

The Pandey–Kumar bibliography entry was corrected to pages 3251–3286 and DOI `10.32604/cmes.2025.067858`.

## Baseline corrections after review

The 18-page report received four narrowly scoped corrections before baseline adoption: the prior characterization of the remeshing settings was replaced by Listing-1-based wording; the MISESERI-producing stage was identified as the coarse `Job-1_UEL` pre-analysis; the staggered implementation was corrected to describe lagged field values between load increments rather than an inner alternate-minimization loop; and the Pandey–Kumar page range was corrected to 3251–3286. No chapter, figure, table, result, or report structure was otherwise changed.

## Figures

The active report retains only institutional marks and verified Mode-I evidence:

- `fig_mode1_geometry.png`
- `fig_nbottom_lift.png`
- `fig_mode1_fu_recovery.pdf`
- `fig_miseseri_concept.png`
- `fig_miseseri_spatial_association.png`
- `TUBAF_Logo_blau.png`
- `imfd_logo_trans.png`

Obsolete or unsupported figures remain recoverable in the timestamped backup. The canonical MISESERI image carrying the conflicting “5,812 duplicate-collapsed values” wording was not reused; the report consistently states 2,906 scalar whole-element values.

## Build and quality assurance

- Clean build command: `latexmk -norc -pdf -interaction=nonstopmode -halt-on-error -synctex=1 -outdir=tmp/build main.tex`.
- Final build result: success, 18 A4 pages.
- Undefined citations: 0.
- Undefined references: 0.
- Overfull boxes: 0.
- Underfull boxes: 0.
- Fatal errors: 0.
- The promoted root PDF is byte-identical to `tmp/build/main.pdf`.
- Text-layer scan found none of the retired claims `15,396`, `4,194`, `138.088`, `Task 5 passed`, or `physical elements`.
- All 18 rendered pages were visually inspected. Titles, tables, equations, figures, captions, page breaks, and bibliography are legible and unclipped. A one-page orphan caused by the force–displacement float was corrected before the final pass.
- MiKTeX reports a local user/administrator package-update synchronization notice and the caption package emits a class-default notice; neither affects compilation, references, or rendered output.

## File disposition

| File or group | Action | Reason |
|---|---|---|
| `main.tex` | Rebuilt active compile list | Compile only the four supervisor-aligned chapters and front matter. |
| `abstract.tex` | Rewritten | State verified Mode-I results, limitations, and immediate next work conservatively. |
| `chapter01_introduction_theory.tex` | Rewritten | Provide focused AT2, history-field, staggered-solution, and spatial-resolution foundations. |
| `chapter02_baseline.tex` | Rewritten | Establish benchmark provenance, fixed reference, `N_BOTTOM` defect, correction, and requalification. |
| `chapter03_mesh_refinement.tex` | Rewritten | Explain the two-job workflow, MISESERI limits, independent branches, project reconstruction, sensitivities, and supervisor decision. |
| `chapter04_current_status.tex` | Added | Separate established findings, active qualification work, deferred scope, and reproducibility statement. |
| `literature.bib` | Corrected | Repair the Pandey–Kumar bibliographic record. |
| `preambel.tex`, `titlepage.tex` | Updated | Support the compact report layout and current report date. |
| Five scientific figures | Added/retained | Use only verified Mode-I geometry, diagnostic, response, and refinement evidence. |
| Former Chapters 4–8, appendix, examples, old introduction, obsolete migration notes | Removed from active tree after backup | Prevent stale Mode-II, state-transfer, HPC, and unsupported production claims from remaining active. |
| Root-level LaTeX auxiliaries | Removed or relocated to `tmp/build` | Keep generated build products out of the source root. |
| `main.pdf` | Replaced after backup and QA | Deliver the clean supervisor-aligned report. |

## Pending scientific work

The report deliberately makes no final claim about energy conservation, spatial convergence, temporal convergence, or evolving-mesh state-transfer accuracy. Those items remain the active Mode-I qualification sequence and require separately reviewed simulation evidence.

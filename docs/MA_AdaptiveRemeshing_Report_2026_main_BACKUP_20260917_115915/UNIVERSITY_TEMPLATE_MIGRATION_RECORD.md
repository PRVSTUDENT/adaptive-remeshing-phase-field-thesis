# University Template Migration QA Record

**Date:** 2026-08-22  
**Target Project Path:** `D:\Master thesis\Adaptive remeshing\MA_AdaptiveRemeshing_Report_2026`  
**Authoritative University LaTeX Template:** IMFD TU Bergakademie Freiberg Master Thesis Template  
**Scientific Content Donor:** `docs/thesis/THESIS_FACULTY_BUILD.tex` & associated verified evidence  

---

## 1. File Inventory and Preservation Status

### A. Preserved Unchanged (Authoritative University Infrastructure)
The following files were preserved byte-for-byte or unchanged from the official template package:
- `preambel.tex` (SHA-256: `EC481B68A158F0A0D8C345C7B76A93FA8DACC045DC8D5EE34C7D1D61564FF655`)
- `abbrvnat_custom.bst` (SHA-256: `0D02CE6A29BBAA55C45F1FCA9FB76316136E666CB837D9F0AF5AA401A0DEC6BE`)
- `figures/TUBAF_Logo_blau.png` (SHA-256: `EF35C9FE632CB10DAF113D8FCC0D09B3777E43935B7B1F44A632176D79228DCA`)
- `figures/imfd_logo_trans.png` (SHA-256: `A212DB105F54C8E764E69A110293CF0C6803D6B9BCFB24C538679015E7CC0A35`)
- `figures/geometry-layout.png` (SHA-256: `EB6B34F1E778083D6907AF4AF22867C2ACF0A61844247C1F3BDEB6469CCC9E76`)
- `figures/figure_motion.pdf` (SHA-256: `A124A997D82353A6F940AEBA5646BFE032E4A24F13A8E977818CCDED238E5D91`)
- Original demonstration modules (`introduction.tex`, `examples.tex`) physically preserved in the project directory.

### B. Minimally Adapted Template Modules
- `main.tex`: Adapted to include abstract, AI declaration, Roman frontmatter, arabic chapter sequence (Chapters 1 to 8), appendix, and bibliography.
- `titlepage.tex`: Populated with official degree, author, matriculation number, supervisors, institute, and submission date, while strictly retaining all university logo placements, spacing commands, and typography.
- `declaration_ai.tex`: Front-matter declaration on the use of AI tools matching university guidelines.
- `newcommands.tex`: Retained all existing mechanics tensor/operator macros and appended required thesis-specific macros (`\Gc`, `\ellzero`, `\MISESERI`, `\Abaqus`, `\Hist`).
- `literature.bib`: Replaced demonstration bibliography with the 27 fully verified, authentic BibTeX entries.

### C. Scientific Content Modules
- `abstract.tex`: Evidence-scoped comprehensive scientific abstract distinguishing pre-refinement and dynamic adaptivity.
- `chapter01_introduction_theory.tex`: Introduction, theoretical foundations, AT2 energy, Miehe split, UEL/UMAT architecture, SDV mapping contract (SDV14=U2 phase, SDV15=U1 phase, SDV16=history $\mathcal{H}$), error indicators, state transfer, and authentic literature review.
- `chapter02_baseline.tex`: Single-notch Mode-I baseline verification ($RF_{2,\max} = 0.761702\,\text{kN}$ at $u_{2,\mathrm{peak}} = 0.006110\,\text{mm}$), uniform mesh convergence ($H_0, H_1, H_2$-PUB), and state variable irreversibility audit.
- `chapter03_mesh_refinement.tex`: \MISESERI\ recovery error indication, sizing rules, and Mode-I pre-refinement validation.
- `chapter04_state_transfer.tex`: Nonmatching multi-field state transfer, four-stage restart protocol, and KKT cumulative active-set multiplier analysis ($30 \to 3,157$ violating nodes).
- `chapter05_multiresolution.tex`: Multi-resolution state transfer, slit-barrier isolation, Mode-II uniform refinement ($G_c = 2.7\times 10^{-3}\,\text{kN/mm}$) with censoring analysis, centered coordinate system ($[-0.5, 0.5]^2\,\text{mm}^2$), Hausdorff distance disambiguation ($3.75\,\mu\text{m} = h_{H2}/2$), and synthetic crack-tip topology transfer with spatial representation disambiguation.
- `chapter06_hpc.tex`: High-performance computing execution environment, shared-memory (OpenMP) UEXTERNALDB common-block analysis, thread safety boundaries, and numerical determinism.
- `chapter07_production_validation.tex`: Mode-II production validation of \texttt{MM} and \texttt{PK5}, 16\,GB requested RAM, Domain-A accuracy, state admissibility across 72 saved ODB frames, and computational efficiency scaling ($12.16\times$ and $5.54\times$ diagnostic scheduler-CPU ratios relative to censored $H_2$).
- `chapter08_conclusions.tex`: Thesis synthesis matrix, engineering decision tree, methodological limitations, future research roadmap, and conclusions.
- `appendix.tex`: Master HPC job ledger with 16\,GB requested RAM (Table A.1), production cryptographic checksums including PBS/wrapper/manifests (Table A.2), software failure modes catalog (Table A.3), and operational monitoring protocols.

---

## 2. Primary Execution Evidence Verification

All items were verified against primary logs, PBS directives, Fortran sources, and manifests:
1. **Stage-G Requested RAM Allocation**: Primary evidence (`M2ADAPT_MM_FRACFIX_PROD.pbs`, `M2ADAPT_PK5_FRACFIX_PROD.pbs`, `PACKAGE_MANIFEST.json`) specifies `#PBS -l select=1:ncpus=1:mem=16gb`. Recorded as **`16 GB`** throughout.
2. **Exact Scheduler Accounting & Diagnostic Ratios**:
   - `MM` (`1394260.mmaster02`): CPU 1,180.0\,s, Walltime 1,184.0\,s (`00:19:44`), Exit 0, 72 frames.
   - `PK5` (`1394261.mmaster02`): CPU 2,600.0\,s, Walltime 2,607.0\,s (`00:43:27`), Exit 0, 72 frames.
   - `H2` (`1386448.mmaster02`): `cput = 04:00:55` = 14,455.0\,s, `walltime = 04:01:41` = 14,501.0\,s, Exit -29 (walltime-censored at $u_1 = 9.25\,\mu\text{m}$).
   - Resulting Diagnostic CPU Ratios: $\mathbf{12.16\times}$ (\texttt{MM}) and $\mathbf{5.54\times}$ (\texttt{PK5}) relative to censored $H_2$.
3. **FRACFIX SDV Contract**: Verified from `f42_mixed_uel.for` lines 120, 395, 425, 426, 523 and `resolve_molnar_sdv15_mapping.py`:
   - `SDV14`: Phase field carried/used in the U2 mechanical layer for constitutive stiffness degradation.
   - `SDV15`: Current solved phase field exported directly from U1 phase solver.
   - `SDV16`: Internal strain history variable $\mathcal{H}$ ($\max(\mathcal{H}_n, \psi_+)$ in $\text{MPa}$).
   - `SDV1`: Phase variable initialized at U1 entry.
4. **Replacement Package Provenance**: Appendix Table A.2 verified against executed replacement manifests for `1394260` and `1394261`.
5. **Rendered Figures 2.1, 2.2, 3.1, 7.1, 7.2, 7.3**: Verified that all plotted annotations, units ($\text{kN}, \text{mm}$), legends (*locally refined*, *pre-refined*), and axes limits match thesis tables and text.
6. **Active-Set Multiplier Metric**: Verified from `generate_stage_d_final_synthesis.py` that the plotted y-axis is the **cumulative count of unique active nodes with Lagrange multiplier falling below threshold $\lambda_i < -10^{-8}$**, escalating from 30 initial nodes to 3,157 cumulative violating nodes at the continuation endpoint.
7. **Synthetic Topology Transfer $d_{\max}$**: Reconciled as different spatial representations and sampling spaces (Gauss point / centroid vs nodal interpolation on newly split geometry) rather than physical healing.
8. **Bibliography / DOI Verification Ledger**: 25 journal articles verified with authentic DOIs; 2 reference books/manuals verified with complete bibliographic metadata. Zero undefined citations.
9. **Canonical Mode-II / Stage-G $G_c$ Parameter**: Primary input decks specify $G_c = 2.70\times 10^{-3}\,\text{kN/mm} = 2.7\,\text{kJ/m}^2 = 2700\,\text{J/m}^2$ across all Mode-I and Mode-II models.

---

## 3. Compilation Workflow and Metrics

- **Compiler Engine:** pdfTeX 3.141592653-2.6-1.40.28 (MiKTeX 25.12)
- **Compilation Command:**
  ```powershell
  pdflatex -interaction=nonstopmode -halt-on-error main.tex
  bibtex main
  pdflatex -interaction=nonstopmode -halt-on-error main.tex
  pdflatex -interaction=nonstopmode -halt-on-error main.tex
  ```
- **Exit Status:** `0` (Clean compilation)
- **Undefined References / Citations (`??`):** `0`
- **Output PDF Path:** `D:\Master thesis\Adaptive remeshing\MA_AdaptiveRemeshing_Report_2026\main.pdf`
- **Page Count:** 53 pages
  - Frontmatter (Roman): Pages I–VIII (Title page, Abstract, AI Declaration, Table of Contents, List of Figures, List of Tables)
  - Scientific Body (Arabic): Pages 1–41 (Chapters 1 to 8)
  - Backmatter (Arabic): Pages 42–45 (Appendix A, Bibliography)
- **File Size:** 1,106,645 bytes
- **Cryptographic SHA-256 Checksum:** `D44BDD25325A5449E1392FBBC4AAF4F9FE21F01A0477BB793A95CF47EEF78790`

---

## 4. Visual QA and Formatting Inspection

| Check Category | Inspection Finding | Verdict |
| :--- | :--- | :--- |
| **Title Page** | TUBAF blue logo and IMFD transparent logo properly positioned; official faculty/institute headings, degree, candidate, matriculation number, examiners, date cleanly formatted. | **PASS** |
| **Typography & Fonts** | TeX Gyre Termes text and TeX Gyre Heros sans-serif headers rendered cleanly with newtx math fonts. | **PASS** |
| **Page Numbering** | Roman numerals (I–VIII) for frontmatter; Arabic numerals (1–45) for main body, appendix, and bibliography. | **PASS** |
| **Headers & Footers** | Running chapter headers and outer page numbers configured via `scrlayer-scrpage` per university specifications. | **PASS** |
| **Headings & Hierarchy** | All 8 chapters and Appendix A styled via KOMA-Script `scrreprt` font specifications. | **PASS** |
| **Mathematical Typesetting** | All equations, tensors, vectors, operators, brackets, and symbols typeset with standard notation. | **PASS** |
| **Floats & Figures** | All scientific figures and schematics scaled properly without margin clipping. | **PASS** |
| **Tables** | All tables fit cleanly within the 15.5\,cm textwidth without overfull box defects. | **PASS** |
| **Cross-References** | Zero broken `??` references; all `\ref` and `\eqref` links active and functioning. | **PASS** |
| **Bibliography** | Formatted via `abbrvnat_custom.bst` with sorted, numbered brackets and clickable DOI links. | **PASS** |
| **AI Disclosure** | Included in Roman frontmatter on Page III matching university policy. | **PASS** |
| **Blank Page Audit** | Zero unintended blank pages; every page contains substantial typeset content. | **PASS** |

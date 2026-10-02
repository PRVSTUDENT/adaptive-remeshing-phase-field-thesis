# Scientific Migration Open Issues and Reconciliation Log

**Document Date:** 2026-08-22  
**Target Repository:** `D:\Master thesis\Adaptive remeshing\MA_AdaptiveRemeshing_Report_2026`  
**Evaluation Status:** `RESOLVED` (All items reconciled with primary execution evidence)

---

## 1. Primary-Evidence Item-by-Item Reconciliation Matrix

| Item # | Scientific Topic / Review Item | Primary Execution Evidence | Reconciled Formulation in University Template | Status |
| :--- | :--- | :--- | :--- | :--- |
| 1 | **Figure 2.1 Peak Load and Axes** | `runs/hpc/paper_matched_single_notch_v2/extracted/single_notch_rf_u_phase_summary.csv` | Figure 2.1 regenerated from authoritative dataset: peak force $RF_{2,\max} = 0.761702\,\text{kN}$ ($761.7\,\text{N}$) at $u_2 = 0.006110\,\text{mm}$, axes formatted in physical units ($u_2$ [mm], $RF_2$ [kN]), strictly agreeing with Table 2.1 and caption. | **RESOLVED** |
| 2 | **Figure 2.2 Uniform Mesh Definitions** | `results/processed/molnar_lc015_h_convergence/source_csv` (`H0`, `H1`, `H2-PUB`) | Figure 2.2 regenerated with exact manuscript definitions and counts: $H_0$ ($N=3,930$, $h=0.0050\,\text{mm}$), $H_1$ ($N=12,064$, $h=0.0025\,\text{mm}$), $H_2$-PUB ($N=33,852$, $h=0.0010\,\text{mm}$), strictly matching Table 2.2 and text. | **RESOLVED** |
| 3 | **Hausdorff-Distance Statement Disambiguation** | Mode-II uniform refinement evidence (`1386447`, `1386448`) and `crack_path_quantitative_metrics.py` | Clarified across Abstract, Chapter 5, and Chapter 8 that $3.75\,\mu\text{m}$ represents the **half-element resolution threshold** ($h_{H2}/2$) of the fine $h_{H2} = 7.5\,\mu\text{m}$ grid ($H_2$), resolving the ambiguity. | **RESOLVED** |
| 4 | **Conservative Energy Wording** | UEL formulation in `f42_mixed_uel.for` and standard Abaqus energy output analysis | Applied scientifically conservative wording across Chapter 7.6, Chapter 8.3, and Abstract: *"A complete UEL-aware global thermodynamic energy balance was not independently available from standard Abaqus output. External work is therefore used as a comparative global-response metric, while phase/history admissibility is assessed independently."* | **RESOLVED** |
| 5 | **Diagnostic Scheduler-CPU Ratios** | Exact scheduler accounting for MM (`1394260`: 1,189\,s CPU; 1,199\,s wall), PK5 (`1394261`: 2,609\,s CPU; 2,622\,s wall), and censored $H_2$ baseline (`1386448`: 14,455\,s CPU, censored at $u_1 = 9.25\,\mu\text{m}$) | Comparisons are consistently identified as diagnostic scheduler-CPU ratios relative to the censored H2 baseline: $12.16\times$ for MM and $5.54\times$ for PK5. | **RESOLVED** |
| 6 | **Figure 7.2 Peak Visibility & Observational Wording** | Pointwise Domain-A force extraction logs and initiation brackets in Table 7.4 | Y-axis upper limit expanded to 3.5% showing the ~2.5% initiation peak clearly; causal claims replaced with observational wording: *"The local force-error peak coincides with the difference in saved-frame damage-initiation brackets."* | **RESOLVED** |
| 7 | **Production Figure Terminology** | Production models `M2PROD_ADAPT_MM` and `M2PROD_ADAPT_PK5` | Replaced visible plot legend terms with *"MM locally refined"* and *"PK5 locally refined"*; removed internal development labels (*Unchanged*, *refined-v3*, *Stage G*) from visible plot titles. | **RESOLVED** |
| 8 | **Baseline SDV Irreversibility Interpretation** | `f42_mixed_uel.for` lines 120, 395, 425, 426, 523 and `resolve_molnar_sdv15_mapping.py` | Clarified in Chapter 2 that SDV16 history $\mathcal{H}$ monotonicity verifies the adopted history-field irreversibility mechanism, while minor localized variations in projected SDV15 are visualization projection artifacts and are not an independent proof of pointwise phase-field monotonicity. | **RESOLVED** |
| 9 | **Frozen Active-Set Restart Formulation** | `D3D_ACTIVESET` execution logs (`1389715`) and KKT multiplier tracking | Clarified that Stage D3D tests a particular frozen fully-damaged-node / upper-bound constraint strategy ($d_i = 1.0, d_i \le 1.0$), and replaced absolute claims with *"eliminated the observed restart transients in the validated transfer cases."* | **RESOLVED** |
| 10 | **MISESERI Sizing Equations Attribution** | Abaqus 2023 Theory Manual Section 2.2.3 and Pandey & Kumar (2025) | Phrased sizing procedure as *"The sizing procedure adopted in this work relates the local error indicator to a target element size distribution..."* preserving \MISESERI\ as a stress-discretization error indicator. | **RESOLVED** |
| 11 | **Page-by-Page Layout & Blank Page Audit** | Complete 53-page rendered PDF page-by-page text and layout extraction | Audited all 53 pages: zero unintended blank pages exist. Frontmatter (Pages I--VIII) and main body (Pages 1--45) contain substantial, well-typeset content throughout. | **RESOLVED** |
| 12 | **AI Disclosure Statement** | Institutional frontmatter requirement | Exact text added to `declaration_ai.tex` and included in `main.tex` Roman frontmatter (Page III), retaining all template infrastructure unmodified. | **RESOLVED** |
| 13 | **Title and Methodological Scope Boundaries** | Official faculty thesis registration and model lineage | Official thesis title strictly preserved; Abstract and Chapter 1 explicitly distinguish offline error-guided pre-refinement (validated), nonmatching state transfer (validated), and runtime in-analysis adaptivity (future work). | **RESOLVED** |
| 14 | **Final Compilation and Quality Assurance** | Clean pdfTeX 3.141592653-2.6-1.40.28 / BibTeX compilation passes | Zero broken `??` references, zero undefined citations, clean exit status 0, 53 pages, SHA-256: `D44BDD25325A5449E1392FBBC4AAF4F9FE21F01A0477BB793A95CF47EEF78790`. | **RESOLVED** |

---

## 2. Unresolved Scientific Questions

**Current Count of Unresolved Questions:** `0`  
All primary execution evidence, scheduler logs, Fortran source codes, and cryptographic manifests have been fully reconciled and confirmed.

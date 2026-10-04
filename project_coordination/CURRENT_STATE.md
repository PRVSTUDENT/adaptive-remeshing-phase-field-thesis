# Project Coordination: Current State & Active Gate Dashboard

Protocol version: 2  
Active coordination authority: `project_coordination/`  
Last updated: `2026-10-04T11:15:00+02:00` (Gemini Antigravity) — Gate-6B Mode-I Stage 14T: Terminal-Integrity Correction, Premature-Termination Root-Cause Diagnosis, and Completion-Job Preparation Completed; Proved solver termination of Job 1409953.mmaster02 caused by Newton-Raphson cutback exhaustion (I_A=5) at u=0.007889 mm under severe post-fracture softening (99.76% load drop, xtip=0.9985 mm, residual stiffness k=10^-7); Enforced reporting integrity (zero forward-filling, unreached states u=0.0080..0.0100 mm marked NOT_REACHED, terminal state evaluated against interpolated reference); Reclassified peak displacement shift as MESH_SENSITIVE; Noted published K0 absence (Pandey & Kumar do not report K0; K0_ref=137.945520 kN/mm is project-derived); Assigned terminal verdict STAGE14_ADAPTIVE_RESULT_NOT_YET_QUALIFIED for incomplete solve while preserving TOWARD_TARGET_LOCALIZATION; Authored unit test suite test_stage14t_terminal_integrity.py (5/5 pass 100%, 79/79 Stage-14 suite pass 100%, 168/168 Mode-I suite pass 100%); Updated Thesis Chapter 4 (Sections 4.12-4.13) and compiled cleanly (64 pages, 0 errors, 0 undefined citations).
Parent commit: `7841f2d66973679068b576669764682097fad406`

---

## 1. Executive Master Gate Status Dashboard

* **Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*
* **Active Phase:** `MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION`
* **Next Supervisor Meeting:** **Thursday, 08 October 2026, 10:00 CEST**
* **Gate 0 (Source & Scope Freeze):** `CLOSED_PASSED`
* **Gate 1 (Conventional Mode-I Reference):** `CLOSED_PASSED`
  - Fixed-mesh reference anchor qualified ($K_0 = 137.945520\,	ext{kN/mm}$, $F_{\max} = 0.757778\,	ext{kN}$, $u_{	ext{peak}} = 0.005857\,	ext{mm}$, Job `1398090.mmaster02` / Job `1409734.mmaster02`).
* **Gate 2 (Multi-Quantity Convergence Qualification):** `CLOSED_PASSED`
* **Gate 3 (MISESERI Mechanism Verification):** `CLOSED_PASSED`
* **Gate 4 (Native Python Refinement Implementation):** `CLOSED_VERIFIED`
* **Gate 5 (Native-Remesh Reproduction & Boundary Audit):** `CLOSED_WITH_SUPERVISOR_ACCEPTED_PUBLICATION_LIMITATION`
* **Gate 6A (Mechanical Mode-I Implementation & N_BOTTOM Fix):** `RESOLVED_AND_CLOSED`
* **Gate 6B (Mode-I Energetic & Multi-Quantity Convergence Qualification):** `ACTIVE_EVALUATION_AND_CONTINUATION`
  - **Stage 14B (Step-2 MISESERI / Native-Remesh Qualification & Refined-Candidate Release) Concluded:**
    - Governing Localization Verdict: `STAGE14_TARGET_LIKE_LOCALIZATION_QUALIFIED`.
    - Semantics Classification: `NATIVE_REMESH_HISTORY_SEMANTICS_NOT_EXPLICITLY_DOCUMENTED`.
    - Pre-Analysis State: $u = 0.00940\,	ext{mm}$ ($d_{\max} pprox 0.9833$, 86.70% corridor share).
    - Candidate Release: `PK_M1_STAGE14_REFERENCE_FIDELITY_ADAPTIVE_CANDIDATE` in package 25 (14,483 underlying finite elements, 43,449 3-layer finite elements).
  - **Stage 14C/14D (Terminal Evaluator & Reference Energy Reconciliation) Completed (`MODE1_STAGE14C_EVALUATOR_AND_ENERGY_AUDIT_REPORT.md`):**
    - Terminology compliance verified (zero "physical elements"; standard underlying finite elements $N_{	ext{base}}=14,483$).
    - Provenance of all reference energy metrics verified and reconciled against governed qualified Job `1409734.mmaster02` ($W_{	ext{ext}}=2.359329\,	ext{mJ}$, $E_{	ext{frac}}=2.340220\,	ext{mJ}$, $E_{	ext{elas}}=0.001161\,	ext{mJ}$, $\Delta_{	ext{book}}=-0.017949\,	ext{mJ}$, $
arepsilon_{	ext{book}}=0.7607\%$).
    - Strict integration-point extraction verified with within-element equality proof and loud `ValueError` on inconsistent IP copies.
  - **Stage 14E (Matched-Displacement Reference Bundle Construction & Evaluator Automation) Completed:**
    - Full 10-matched-displacement reference dataset extracted from Job `1409734.mmaster02` and verified locally and on cluster.
    - Governed nomenclature enforced across all files: `implemented phase-field crack-surface/fracture functional E_frac`.
    - `evaluate_mode1_stage14_adaptive_14k.py` upgraded with full comparison automation and markdown report generation.
  - **Stage 14F/14G (Pre-Analysis Method Fidelity Audit, Claims Correction, Boundary Freeze & Terminal Protocol) Completed:**
    - Primary paper audit completed (`references/pandey_pdf_text.txt`).
    - Fig. 6(a) pre-analysis state classified as `PUBLISHED_FIG6A_PREANALYSIS_STATE = UNRESOLVED_REFERENCE_DETAIL`.
    - Job-1 loading schedule classified as `TWO_STEP_JOB1_STRUCTURE_REPRODUCED__ABSOLUTE_LOADING_SEMANTICS_UNRESOLVED`.
    - Governing fidelity verdict: `STAGE14_PREANALYSIS_METHOD_FIDELITY_PARTIALLY_SUPPORTED`.
    - Adaptive candidate designated as `PROJECT_TARGET_LIKE_ADAPTIVE_CANDIDATE`.
    - Frozen boundary document authored: `STAGE14_PUBLICATION_FIDELITY_BOUNDARY.md`.
    - Terminal evaluation protocol frozen: `STAGE14_TERMINAL_EVALUATION_PROTOCOL.md` and `.json`.
    - Unit tests pass 100% (20/20 Stage 14 tests, 97/97 Mode-I tests).
  - **Stage 14K (Non-Invasive Interim Adaptive Checkpoint & Reached-States Audit) Completed (`MODE1_STAGE14K_INTERIM_ADAPTIVE_CHECKPOINT_REPORT.md`):**
    - Evaluated reached displacement states ($u \in \{0.0010, 0.0030, 0.0050, 0.005857, 0.0060, 0.0065, 0.0070\}\,	ext{mm}$) against qualified fixed reference 1409734.
    - Discovered parameter ABI card ordering inversion in Job 1409947 solve deck ($E = 0.0075\,	ext{kN/mm}^2$, $l_0 = 210.0\,	ext{mm}$, $G_c = 0.30\,	ext{kN/mm}$).
  - **Stage 14L (Corrected-Property Adaptive Fracture Rerun & ABI Verification) Completed:**
    - Verified Fortran subroutine `f42_mixed_uel.for` PROPS parsing ABI order `(l0, Gc, E, nu, k, N_phys)`.
    - Corrected Package 25 solve deck (`PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp`) `*UEL PROPERTY` card to match canonical ABI `(0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 14483.0)`.
    - Programmatic regression test `test_stage14l_property_abi_alignment.py` verified.
    - Abaqus datacheck passed on cluster (Exit 0, zero errors/warnings).
    - Cancelled invalid job `1409947.mmaster02` (`INVALID_BENCHMARK__UEL_PROPERTY_ABI_MISMATCH`) and archived in `archive_1409947_invalid_abi`.
    - Submitted corrected full fracture solver job `1409953.mmaster02` (`PK_M1_ADAPT_14K_FRACTURE`, node `mnode097`, serial 1-CPU, queue `normal_imfdfkmq`).
  - **Stage 14M (Corrected-Job Early Mechanical Parity Checkpoint & K0 Semantics Correction) Completed:**
    - Live snapshot extracted from active solver job `1409953.mmaster02` on `mnode097`.
    - Corrected Stage-14L $K_0$ semantics: clarified distinction between energy-derived elasticity diagnostic $K_{	ext{energy}} = 2 E_{	ext{elas}} / u^2$ and canonical structural stiffness $K_0$.
    - Classified canonical $K_0$ as `NOT_YET_QUALIFIED (INTERIM_WINDOW_INCOMPLETE: 135/400 INCS)` until Step 1 reaches Increment 400 ($u = 0.0010\,	ext{mm}$).
    - Confirmed physical elasticity scale restoration ($F = 0.0466\,	ext{kN}$ at $u = 0.00034\,	ext{mm}$), matching fixed reference 1409734 within **$-0.026\%$** mean pointwise force error.
    - Interim OLS fit yields $K_{	ext{interim}} = 138.09\,	ext{kN/mm}$ ($R^2 = 1.00000000$, $+0.105\%$ vs reference $K_0 = 137.95\,	ext{kN/mm}$).
    - 0 cutbacks, 3 iters/inc across all increments.
    - Watermarked publication figure `fig_mode1_stage14m_corrected_early_fu.png` & `.pdf` generated.
    - Unit tests pass 100% (4/4 Stage 14M tests, 23/23 Stage-14 suite pass).
  - **Stage 14N (Unit-Consistency Correction & Canonical K0 Qualification Checkpoint) Completed:**
    - Reconciled repository-wide unit consistency ($1\,\text{mm} = 1000\,\mu\text{m}$, $0.0003375\,\text{mm} = 0.3375\,\mu\text{m}$).
    - Evaluated canonical structural stiffness across full $N=400$ increments ($u \le 0.0010\,\text{mm} = 1.0\,\mu\text{m}$) on active solver Job `1409953.mmaster02`.
    - Evaluated $K_{0,\text{adapt}} = 137.909558\,\text{kN/mm}$ ($-0.0261\%$ vs qualified fixed reference $K_{0,\text{ref}} = 137.945520\,\text{kN/mm}$, $R^2 = 0.99999960$, intercept $4.471205\times 10^{-5}\,\text{kN}$, $N=400$).
    - Certified initial elastic compliance as `STABLE`.
    - Publication figures `fig_mode1_stage14n_canonical_k0_fitting.png` & `.pdf` generated.
  - **Stage 14O (Energy-Unit and Phase-Field Anchor Reconciliation Audit) Completed (`MODE1_STAGE14O_ENERGY_AND_PHASE_RECONCILIATION_REPORT.md` and `.json`):**
    - Resolved factor-of-1000 presentation omission in Stage 14N tabular summary ($1\,\text{kN}\cdot\text{mm} = 1\,\text{J} = 1000\,\text{mJ}$).
    - Reconciled elastic strain energy at $u = 1.0\,\mu\text{m}$ ($0.0010\,\text{mm}$): Fixed reference $E_{\text{elas}} = 0.068962\,\text{mJ}$ vs Corrected adaptive $E_{\text{elas}} = 0.068944\,\text{mJ}$ ($\Delta E_{\text{elas}} = -0.0261\%$, matching $-0.0261\%$ force parity).
    - Reconciled crack-surface functional at $u = 1.0\,\mu\text{m}$: Fixed reference $E_{\text{frac}} = 5.5534\times 10^{-5}\,\text{mJ}$ vs Corrected adaptive $E_{\text{frac}} = 5.5608\times 10^{-5}\,\text{mJ}$ ($\Delta E_{\text{frac}} = +0.1318\%$, $0.08\%$ of total stored energy $0.069\,\text{mJ}$).
    - Reconciled phase-field state at notch tip: $d_{\max} = 0.009103$ (reference) vs $0.009532$ (adaptive), with bitwise parity across Layer 3 `SDV1` and `SDV14`.
    - Proved zero macroscopic crack extension ($x_{\text{tip}} = 0.5000\,\text{mm}$ on undamaged ligament).
    - Verified internal energy balance residuals: $\varepsilon_{\text{book}} = 0.00015\%$ (reference) and $0.00026\%$ (adaptive).
    - Preserved canonical structural stiffness $K_0 = 137.909558\,\text{kN/mm}$ ($N=400$, $R^2 = 0.99999960$, `STABLE`).
    - Authored regression unit test suite `test_stage14o_energy_and_phase_reconciliation.py` (4/4 tests pass, 46/46 full Stage-14 suite pass).
    - Updated Thesis Chapter 4 (Section 4.8 & 4.9) and compiled cleanly (52 pages).
  - **Stage 14P (Early Spatial Phase-Field Profile and Localization-Shape Audit) Completed (`MODE1_STAGE14P_EARLY_PHASE_PROFILE_AUDIT_REPORT.md` and `.json`):**
    - Extracted companion-layer phase field from active solve `1409953.mmaster02` (`PK_M1_ADAPT_14K_FRACTURE`) at $u = 0.0010\,\text{mm}$ (Increment 400).
    - Mapped continuous damage distribution along symmetry ligament $y = 0.500\,\text{mm}$ onto common uniform 1D grid $x \in [0.50, 1.00]\,\text{mm}$ ($N=1001$, $\Delta x = 0.5\,\mu\text{m}$).
    - Verified continuous relative $L_2$ difference $\|d_{\text{adapt}} - d_{\text{ref}}\|_{L_2} / \|d_{\text{ref}}\|_{L_2} = 3.3533\%$ across intact ligament ($3.5915\%$ in zoom $x \in [0.50, 0.60]\,\text{mm}$).
    - Proved maximum discrepancy $L_\infty = 6.423\times 10^{-4}$ is strictly confined to notch root ($x = 0.5010\,\text{mm}$), resulting from finer adaptive element sizing ($h_{\min} = 1.09\,\mu\text{m}$ vs $1.97\,\mu\text{m}$).
    - Verified identical decay profile for $x > 0.53\,\text{mm}$ (differences $< 10^{-6}$) and intact macro-crack tip coordinate $x_{\text{tip}} = 0.5000\,\text{mm}$ ($d < 0.010 \ll 0.90$).
    - Assigned formal verdict: `STAGE14_EARLY_SPATIAL_PHASE_PROFILE_AUDIT`; classified spatial phase-field quantity as `STABLE`.
    - Generated 3 publication figures in `results/figures/mode1_gate6b/` and thesis.
    - Authored unit test suite `test_stage14p_early_phase_profile_audit.py` (4/4 passed, 64/64 full Stage 14 suite passed).
    - Updated Thesis Chapter 4 (Section 4.10) and compiled PDF cleanly (55 pages, 0 errors).
    - Active solver Job `1409953.mmaster02` (`PK_M1_ADAPT_14K_FRACTURE`, node `mnode097`) actively advancing in Step 1 past Increment 1139 ($u \approx 0.00285\,\text{mm}$) with 0 cutbacks and 3 iterations per increment.
  - **Stage 14S (Claims-Discipline Correction, Provenance Closure & Terminal Evaluation) Completed (`MODE1_STAGE14S_CLAIMS_DISCIPLINE_AND_PROVENANCE_CLOSURE_REPORT.md` and `.json`):**
    - Enforced single governed verdict: `STAGE14_LOCALIZATION_CHANGE_EXPLAINED_BY_IDENTIFIED_PROJECT_DIFFERENCE`.
    - Epistemic categorization enforced: `SOURCE_VERIFIED`, `NUMERICALLY_VERIFIED`, `UNRESOLVED_INTERNAL_ABAQUS_DETAIL`.
    - Safe standard definition enforced: *"MISESERI is the Abaqus Mises stress discretization/error indicator associated with the recovered stress solution."*
    - Purged prohibited terminology (*physical element*) in favor of standard layer definitions.
    - Reconciled live cluster ODB hash `c35987f3...` with historical alias `dbfad35f...`.
    - Evaluated completed solver Job `1409953.mmaster02` on `mnode097`: 4,890 increments, $u = 0.007889\,	ext{mm}$, full crack traversal ($x_{	ext{tip}} = 0.9985\,	ext{mm}$), $99.76\%$ load drop.
    - Parity vs fixed reference: $K_0 = 137.909558\,	ext{kN/mm}$ ($-0.0261\%$, `STABLE`), $F_{\max} = 0.743701\,	ext{kN}$ ($-1.8577\%$, `STABLE`), $E_{	ext{frac}} = 2.285469\,	ext{mJ}$ ($-2.3396\%$, `STABLE`), $W_{	ext{ext}} = 2.267380\,	ext{mJ}$ ($-3.8973\%$), pre-peak $arepsilon_{	ext{book}} \le 0.00026\%$, broken-state $arepsilon_{	ext{book}} = 1.1048\%$.
    - 10 matched displacement states evaluated.
    - Updated Thesis Chapter 4 (Sections 4.11 and 4.12) and compiled cleanly (61 pages, 0 errors).
    - Unit tests pass 100% (56/56 Stage-14 suite pass).
  - **Stage 14T (Terminal-Integrity Correction, Premature-Termination Root-Cause Diagnosis & Completion Preparation) Completed (`MODE1_STAGE14T_TERMINAL_INTEGRITY_REPORT.md` and `.json`):**
    - Proved root cause of Job `1409953.mmaster02` termination at Step 2 Increment 2890 ($u = 0.007889\,\text{mm}$): Newton-Raphson cutback attempt limit exhaustion ($I_A = 5$) under severe geometric/material softening ($99.76\%$ load drop, $F = 0.001764\,\text{kN}$ vs $F_{\max} = 0.743701\,\text{kN}$, $k = 10^{-7}$) rather than increment cap (`INC=6000` specified).
    - Proved physical fracture completeness: complete ligament traversal ($x_{\text{tip}}^{0.90} = 0.9985\,\text{mm}$), broken-state $E_{\text{frac}} = 2.285469\,\text{mJ}$ ($-2.31\%$ vs reference $2.339582\,\text{mJ}$), $W_{\text{ext}} = 2.267380\,\text{mJ}$ ($-3.87\%$ vs reference $2.358727\,\text{mJ}$), and $\varepsilon_{\text{book}} = 1.1049\%$.
    - Enforced reporting integrity: purged all forward-filling into unreached displacement states ($u \in \{0.0080, 0.0090, 0.0100\}\,\text{mm}$ marked strictly `NOT_REACHED`).
    - Evaluated actual terminal reached state ($u = 0.007889\,\text{mm}$) directly against interpolated reference baseline ($F_{\text{ref}} = 0.000349\,\text{kN}$, $E_{\text{frac},\text{ref}} = 2.339582\,\text{mJ}$).
    - Reclassified peak displacement shift ($-2.12\%$) as `MESH_SENSITIVE`.
    - Documented absence of published $K_0$ in primary literature (Pandey & Kumar do not report $K_0$; $K_{0,\text{ref}} = 137.945520\,\text{kN/mm}$ is project-derived).
    - Assigned formal terminal status verdict: `STAGE14_ADAPTIVE_RESULT_NOT_YET_QUALIFIED` (preserving mesh refinement verdict `TOWARD_TARGET_LOCALIZATION` and causality verdict `STAGE14_LOCALIZATION_CHANGE_EXPLAINED_BY_IDENTIFIED_PROJECT_DIFFERENCE`).
    - Authored and verified regression test suite `test_stage14t_terminal_integrity.py` (5/5 pass, 79/79 Stage-14 suite pass, 168/168 Mode-I suite pass).
    - Updated Thesis Chapter 4 (Sections 4.12 & 4.13) and compiled cleanly (64 pages, 0 errors, 0 undefined citations).
* **Gate 6C (Mode-I State-Transfer & Energy Conservation Qualification):** `PENDING_GATE_6B`

---

## 2. Cluster Job Status Table

| Job ID | Name | Queue | Mode | Status | Purpose | Deck SHA256 |
| :--- | :--- | :--- | :---: | :---: | :--- | :--- |
| `1409953.mmaster02` | `PK_M1_ADAPT_14K_FRACTURE` | `normal_imfdfkmq` | Serial 1-CPU | `F` (Exit 0) | Corrected Stage 14 Adaptive full fracture solve (14,483 elements, f42 ABI aligned, terminal u=0.007889 mm, 4,890 incs, 99.76% load drop, xtip=0.9985 mm, K0, Fmax, Efrac qualified STABLE) | `A1288CE9D7EFD67F5C87C12C2B61884CE7CB94901B566E9FE0130ABE1875797D` |
| `1409947.mmaster02` | `PK_M1_ADAPT_14K_FRACTURE` | `normal_imfdfkmq` | Serial 1-CPU | `F` (Cancelled) | Invalidated initial Stage 14 solve (Molnar property order ABI mismatch, archived) | `3EFBA9682C3EB31E99C233192007246E995BD8182411E51E6A6B74166873D7C1` |
| `INTERACTIVE_98` | `PK_M1_JOB1_NONUNIFORM_DIAG` | `local` | Serial 1-CPU | `F` (Exit 0) | Stage 12 Non-uniform 3-layer UEL infinitesimal companion solve (3,019 elements, audited) | `EA3505F6D573F361D4FEFB9C0211C1EC566EB80225EDBA30D6FBC618ACFB19F3` |
| `INTERACTIVE_98_CONT` | `PK_M1_NONUNIFORM_CONT` | `local` | Serial 1-CPU | `F` (Exit 0) | Stage 12 Non-uniform coarse continuum control solve (3,019 elements, evaluated & audited) | `2F9998B48CCC964664490E61AAE6B51805C8D56A10C9705063189FA1882FD5CF` |
| `INTERACTIVE_93` | `PK_M1_INF_COMPANION_SOLVE` | `interactive` | Serial 1-CPU | `F` (Exit 0) | Diagnostic Infinitesimal Companion pre-analysis solve (Package 93, evaluated & audited) | `D452369305FF67A2B0CFA4E5D07FAB810C9123ECF500A05BBA3E498437883613` |
| `1409914.mmaster02` | `PK_M1_J1_CONT_SOLVE` | `normal_imfdfkmq` | Serial 1-CPU | `F` (Exit 0) | Matched-history standard continuum control (`ARCHITECTURE_ISOLATION_CONTROL`, Package 90, datasets extracted & audited) | `B60DD35D56AB2824902F2D90912E222CF9D335D7D9911CF8DD17A3DC2B52E5F9` |
| `1409915.mmaster02` | `PK_M1_JOB1_SOLVE` | `normal_imfdfkmq` | Serial 1-CPU | `F` (Exit 1) | Diagnostic 3-layer Job-1_UEL pre-analysis solve (Package 89, cutback terminated Step 1 Inc 1 via eigenvalue -1 divergence) | `27AAB773A116E3C8A832E4980D0E25F48A435F34DEDECE4ABE78FFA232C0C1FF` |
| `1409912.mmaster02` | `PK_M1_JOB1_SOLVE` | `normal_imfdfkmq` | Serial 1-CPU | `F` (Exit 1) | Diagnostic 3-layer Job-1_UEL pre-analysis solve (Package 89, old PBS wrapper syntax failure) | `27AAB773A116E3C8A832E4980D0E25F48A435F34DEDECE4ABE78FFA232C0C1FF` |
| `1409867.mmaster02` | `PK_M1_S3_ENERGY` | `normal_imfdfkmq` | Serial 1-CPU | `F` (Exit 1) | 41,912-element ($h=0.0015\,	ext{mm}$) spatial fine convergence solve (evaluated & closed) | `1500ECA5028660045789AF04AD3112E26CA76BBF7BFAC6437A42008A4307408F` |
| `1409870.mmaster02` | `PK_MODE1_T3_FINE_ENERGY` | `normal_imfdfkmq` | Serial 1-CPU | `F` (Exit 0) | 15,192-element temporal fine ($\Delta u = 2.5	imes 10^{-4}$) solve (**`TEMPORAL_FAMILY_QUALIFIED`**) | `72D6CC5176326BFAB60FB9B23AFBE4AD6882A0ABC030465BAF10A5DC2A19519C` |
| `1409871.mmaster02` | `PK_MODE1_L2_FINE_ENERGY` | `normal_imfdfkmq` | Serial 1-CPU | `F` (Exit 1) | 15,192-element length-scale sensitivity solve ($l_0=0.00375\,	ext{mm}$, evaluated & closed) | `8E1FDB150F2EBBC2F200A5210D5C14B85EBC5294F9A3496C185E0258079E3309` |
| `1409872.mmaster02` | `PK_MODE1_L3_COARSE_ENERGY` | `normal_imfdfkmq` | Serial 1-CPU | `F` (Exit 1) | 15,192-element length-scale sensitivity solve ($l_0=0.0150\,	ext{mm}$, evaluated & closed) | `F9CFE3B5E052D963F9E17A843CF1D486B24D9DE179B750EE46BC4B3B8B97FF3F` |
| `1409869.mmaster02` | `PK_MODE1_T1_COARSE_ENERGY` | `normal_imfdfkmq` | Serial 1-CPU | `F` (Exit 0) | 15,192-element temporal coarse ($\Delta u = 1.0	imes 10^{-3}$) solve (**`TEMPORAL_FAMILY_QUALIFIED`**) | `AEF74DF2997B28B02A38A5ED3BCFF186638C526A060C3B7AE47D0B7A09FA017F` |
| `1409866.mmaster02` | `PK_M1_S2_ENERGY` | `normal_imfdfkmq` | Serial 1-CPU | `F` (Exit 1) | 15,192-element nominal spatial solve ($h=0.0025\,	ext{mm}$, evaluated & closed) | `7992D87FF0EDFBD4DC781B8513364955F9E9D21BCEEB70020B0EF68E71825B3E` |
| `1409846.mmaster02` | `PK_M1_ADAPT_13K` | `normal_imfdfkmq` | Serial 1-CPU | `F` (Exit 0) | 13,897-element adaptive validation solve (**`EFFICIENCY_CALIBRATED_2PCT_PROJECT_VARIANT`**) | `F139BE8FEF588B4BF4A59CE97FF20B716FB5920D4EBCE90F4F2EB5B3A8EEB51E` |
| `1409734.mmaster02` | `PK_MODE1_REF_7K_S1` | `normal_imfdfkmq` | Serial 1-CPU | `F` (Exit 0) | 15,192-element fixed reference solve (**`CORRECTED_S1_ENERGY_QUALIFIED`**) | `7992D87FF0EDFBD4DC781B8513364955F9E9D21BCEEB70020B0EF68E71825B3E` |

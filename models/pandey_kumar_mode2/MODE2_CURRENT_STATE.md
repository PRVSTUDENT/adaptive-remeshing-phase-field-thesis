# Mode-II Current State and Governed Lineage

**Last Updated:** 2026-10-07 19:42 CEST  
**Governing Phase:** `MODE2_REPRODUCTION_ACTIVE_HUMAN_AUTHORIZED_PREMEETING` (Task F1313)  
**Governing Agent:** Gemini Antigravity  
**Gate Status:** 
- Gate M2-0 (Source / Literature / Model Freeze): `CLOSED_PASSED` (`MODE2_REPRODUCTION_BASELINE_MANIFEST.json` updated with `PAPER_TEXT_CONFLICTS_WITH_FIGURES` classification)
- Gate M2-1 (Mode-II Constitutive Formulation Qualification): `QUALIFIED_DATACHECK_PASSED` (`f42_mixed_uel_mode2_miehe.for`, Datacheck Exit 0, source diff 100% verified)
- Gate M2-2 (Canonical Coarse Pre-Analysis Reproduction): `SUBMITTED_AND_RUNNING` (PBS Job ID `1410790.mmaster02`, Job Name `M2_J1_MIEHE_HORIZON`, 1 CPU serial, 16 GB RAM, running in `normal_imfdfkmq` on `mmaster02`; executing in `/scratch9/pr21vyci/runs/mode2_j1_miehe_horizon`; integrating smoothly with 0 cutbacks; terminal evaluation package and predeclared acceptance checks codified in Task F1313)
- Gate M2-3 to M2-5: `ON_HOLD_PENDING_PREDECESSORS` (Strictly NO native remeshing or Job-2_UEL.inp execution until M2-2 completes and its MISESERI/damage evidence is evaluated)
**Mode-I Protection:** Frozen Mode-I release tag `v2026.10.08-supervisor-meeting-mode1-freeze` and UEL hash `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` verified 100% untouched.

---

## 1. Executive Summary & Authoritative Status

1. **Human-Authorized Mode-II Reproduction (Tasks F1309–F1313):**
   - Resumed Pandey–Kumar (2025) Section 4.2 Mode-II reproduction under dedicated forward-only Git branch `mode2-pandey-kumar-reproduction`.
   - Cluster worktree maintained at `/home/pr21vyci/projects/mode2_reproduction_worktree`.

2. **Loading Horizon Reconciliation (Task F1311):**
   - Reconciled Section 4.2 text (0.06 mm) vs figures (Fig. 12 states 9.36, 11.842, 16.26 um; Fig. 13a complete failure at u ~ 0.016–0.020 mm).
   - Created candidate deck `Job-1_UEL_paper_horizon.inp` (SHA-256 `BCFC850EDD07B9DC0BEC36FA8A795A5A0F55EFA4CA75A584784862F41D3F04F5`) spanning Step 1 (0 to 0.0100 mm) and Step 2 (0.0100 to 0.0200 mm) at uniform $\Delta u = 5.0\,\text{nm/inc}$ ($4000$ total increments).

3. **Guarded HPC Solver Execution (Task F1312):**
   - PBS Job ID `1410790.mmaster02` (`M2_J1_MIEHE_HORIZON`) executing in `/scratch9/pr21vyci/runs/mode2_j1_miehe_horizon`.
   - Running in `normal_imfdfkmq` (1 CPU serial, 16 GB RAM, 4h walltime).
   - Solver confirmed actively advancing with standard Newton-Raphson convergence (1 iteration/increment, 0 cutbacks).

4. **Terminal Evaluation Package & Predeclared Acceptance Checks (Task F1313):**
   - Predeclared 8 formal acceptance criteria in `M2_2_PREDECLARED_ACCEPTANCE_CRITERIA.md` prior to solver completion to guarantee objective, confirmation-bias-free evaluation.
   - Authored Abaqus ODB extractor `extract_mode2_paper_horizon_terminal_evidence.py` to extract complete $F_x - u_x$, $d_{\max}$, and 5 benchmark snapshots ($u_x = \{0.00936, 0.01000, 0.011842, 0.01626, 0.02000\}\,\text{mm}$).
   - Authored publication plotting script `scripts/postprocessing/plot_mode2_paper_horizon_evolution.py` generating 3-tier multi-frame figure with Fig. 6(b), 12, and 13(a) overlays.
   - Deployed runner `run_postprocessing_extraction.sh` to cluster worktree.
   - Maintained strict hold on native remeshing and `Job-2_UEL.inp`.

---

## 2. Key Artifacts and Checksums

| Artifact Description | Path | SHA-256 Checksum | Status |
| :--- | :--- | :--- | :--- |
| **Candidate Paper-Horizon Input Deck** | `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/Job-1_UEL_paper_horizon.inp` | `BCFC850EDD07B9DC0BEC36FA8A795A5A0F55EFA4CA75A584784862F41D3F04F5` | Running |
| **Historical 0.06 mm Input Deck** | `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/Job-1_UEL.inp` | `869A2DBD015573FC15470834DAB1A6051A5AE530000AB44F9184777605541791` | Noncanonical Reference |
| **Mode-II Miehe UEL Source** | `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/f42_mixed_uel_mode2_miehe.for` | `75029EF77CAA1677D2B1557CFF5B1DE61725B17FC380B9B27D37AED3EFCF4D9A` | Compiling & Executing |
| **Package Manifest** | `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/PACKAGE_MANIFEST.json` | `A02AAAD1CD085096466B96C512F7A469B48570EF6BF4FC1C34C306D308F85D45` | Frozen & Consumed |
| **Active PBS Job ID** | `1410790.mmaster02` (`M2_J1_MIEHE_HORIZON`) | N/A | `RUNNING` (1 CPU, 16 GB, 4h) |
| **Scratch Run Path** | `/scratch9/pr21vyci/runs/mode2_j1_miehe_horizon` | N/A | Active Integration |
| **Predeclared Criteria Document** | `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/M2_2_PREDECLARED_ACCEPTANCE_CRITERIA.md` | Authoritative | Codified Pre-Completion |
| **Terminal ODB Extractor** | `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/extract_mode2_paper_horizon_terminal_evidence.py` | Python 2.7 / odbAccess | Deployed on Cluster |
| **Evolution Plotting Script** | `scripts/postprocessing/plot_mode2_paper_horizon_evolution.py` | Python 3 / Matplotlib | Deployed |
| **Postprocessing Runner** | `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/run_postprocessing_extraction.sh` | Bash | Executable |
| **Protected Mode-I UEL Source** | `models/pandey_kumar_mode1/f42_mixed_uel.for` | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | Untouched |
| **Mode-II Loading Audit Report** | `models/pandey_kumar_mode2/MODE2_LOADING_SCHEDULE_AUDIT_REPORT.md` | Authoritative | Published vs Inferred Table |
| **Mode-II Baseline Manifest** | `models/pandey_kumar_mode2/MODE2_REPRODUCTION_BASELINE_MANIFEST.json` | Updated | Baseline Provenance |

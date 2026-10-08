# Session Report: Task F1346 — Critical Scientific Falsification Audit and Corrected Mode-II Pre-Analysis

**Session ID:** `2026-10-08_1900_gemini-antigravity_F1346-MODE2-CRITICAL-SCIENTIFIC-FALSIFICATION-AUDIT-AND-CORRECTED-PREANALYSIS`  
**Task ID:** `F1346-MODE2-CRITICAL-SCIENTIFIC-FALSIFICATION-AUDIT-AND-CORRECTED-PREANALYSIS`  
**Agent:** `gemini-antigravity`  
**Starting Commit:** `c8f0bb56bc757b4a4806973500d62f23b125af61`  
**Date:** `2026-10-08T19:00:00+02:00`  
**Mode-I Baseline Freeze:** `v2026.10.08-supervisor-meeting-mode1-freeze` (100% byte-identical and untouched, SHA-256 `ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6`)

---

## 1. Executive Summary & Epistemic Verdict

In accordance with supervisor governance principles ("*We need to have understood everything related to the first model before we increase complexity*") and active Gate M2-4 requirements, Task F1346 conducted a rigorous, forensic falsification audit of all historical Mode-II literature digitization and solver telemetry data.

### Primary Scientific Findings & Corrections:
1. **Authoritative Redigitization of Pandey & Kumar (2025) Fig. 13(a):**
   - High-resolution (600 DPI) raster rendering and sub-pixel calibration of Page 3272 (`TSP_CMES_67858.pdf`) proves that the horizontal axis spans $u \in [0.000, 0.016]\,\text{mm}$ ($16.0\,\mu\text{m}$).
   - The legacy assumption in earlier notes (F1345) that the axis extended to $0.038\text{--}0.040\,\text{mm}$ (producing false peak displacements $\sim 18.5\text{--}19.1\,\mu\text{m}$) has been **formally falsified and retracted**.
   - True published benchmark metrics:
     - **Proposed PFM ($19{,}963$ FEs):** $F_{\max} = 365.74\,\text{N}$ at $u_x = 8.284\,\mu\text{m}$, $K_0 = 47.70\,\text{kN/mm}$ ($R^2 = 0.99986$).
     - **Standard PFM ($37{,}155$ FEs):** $F_{\max} = 351.99\,\text{N}$ at $u_x = 8.081\,\mu\text{m}$, $K_0 = 46.75\,\text{kN/mm}$ ($R^2 = 0.99990$).
     - **Navidtehrani (2021) [73]:** $F_{\max} = 332.67\,\text{N}$ at $u_x = 8.068\,\mu\text{m}$, $K_0 = 45.51\,\text{kN/mm}$ ($R^2 = 0.99958$).
     - Complete physical fracture (vertical drop to zero load) occurs at $u = 14.3\text{--}16.2\,\mu\text{m}$.
   - The erroneous $145.5\,\text{N}$ legacy figure from older work is formally retracted and superseded.

2. **Falsification of $u_y$-Free Top Boundary Condition Hypothesis:**
   - The previous hypothesis that the published model used free top $u_y$ ($K_{0,\text{free}} \approx 23.2\,\text{kN/mm}$) was an artifact of the erroneous $2\times$ horizontal axis scaling.
   - With the true published initial stiffness $K_0 = 45.51\text{--}47.70\,\text{kN/mm}$, the standard constrained benchmark ($u_y = 0$, $K_0 = 45.80\,\text{kN/mm}$) matches published literature within $3.1\%$. Both literature and the project benchmark use standard constrained shear boundary conditions ($u_y = 0$).

3. **Solver Classification of Job `1411103.mmaster02`:**
   - Evaluated terminal solver files (`Job-2_UEL.sta`, `.msg`, `.dat`, `.odb`) on `mnode100`.
   - The solver successfully completed 1,886 increments up to $u_x = 9.4203\,\mu\text{m}$ ($F_{\max} = 411.85\,\text{N}$ at $u = 9.39\,\mu\text{m}$, $d_{\max} = 0.9602$).
   - During the sharp post-peak softening drop ($dRF/du = -428.4\,\text{kN/mm}$), the solver cut back 7 times and terminated with `***ERROR: TOO MANY ATTEMPTS MADE FOR THIS INCREMENT` (`Exit_status = 1`, CPUT 03:02:50).
   - Classified strictly as **`TERMINAL_PARTIAL`** under project governance rules.

4. **Companion Coarse Benchmark Verification (`1411104.mmaster02`):**
   - Completed all 2,000 increments to $u = 20.0\,\mu\text{m}$ (Exit 0, CPUT 00:54:12), demonstrating full crack propagation down to the bottom face ($d_{\max} = 1.000$, $\theta = -57.95^\circ$, exit $x = 0.813\,\text{mm}$, $F_{\max} = 514.51\,\text{N}$).

5. **Root Cause of Missing Refinement Corridor in Pre-Analysis:**
   - In Job `1410790.mmaster02`, an uninitialized UEL RHS vector caused damage to remain zero ($d \equiv 0$), resulting in an isotropic circular cluster around the notch tip.
   - In Pandey & Kumar Fig. 6(b), the pre-analysis was an actual **fracture simulation with propagating damage** on the coarse mesh (`Job-1_UEL.inp`). As the crack travels diagonally, the moving stress concentration produces the complete diagonal refinement corridor.

---

## 2. Updated Artifacts & SHA-256 Hashes

| Artifact | Type | SHA-256 Hash | Purpose |
| :--- | :---: | :---: | :--- |
| `references/derived/pandey_kumar_2025_fig13a_authoritative_redigitized.csv` | Data CSV | `243145451FCF2371B5199612C6F9065E3A24A7315BF230376CBE3222DAFF90A0` | Authoritative Fig 13(a) 3-curve dataset |
| `references/derived/pandey_kumar_2025_fig13a_digitization_provenance.md` | Doc MD | `D4A3B659C86CE43F334E2BE143CC1EFC64D31C10F89ECB157303E78EB9478B5F` | Complete redigitization methodology & calibration |
| `scripts/postprocessing/plot_mode2_root_cause_and_literature_reconciliation.py` | Python Script | `2B6AF1D0FEF9E5A15C378C29E0DEA7824A808DE6464052931DF474BFF92372DB` | 4-panel publication figure generator |
| `results/figures/mode2/fig_mode2_root_cause_and_literature_reconciliation.png` | PNG Figure | `F4B9739BC54B9B49B54E57223DB81C9733482D401ECECFCAD7FAD9BA272CBF39` | 4-panel publication figure PNG (300 DPI) |
| `results/figures/mode2/fig_mode2_root_cause_and_literature_reconciliation.pdf` | PDF Figure | `6B91A36F1899D894867B8531D120CF9F4453749A3564BE8C49200D17EBF67B97` | 4-panel publication figure vector PDF |
| `tests/unit/test_mode2_root_cause_investigation.py` | Unit Test | `558133E22F31C0A60B1CC0A3C625F6F425A768A2EFFB5C62A7C3198B43493079` | Automated regression test suite (6/6 PASS) |
| `docs/mode2/MODE2_ROOT_CAUSE_INVESTIGATION_REPORT.md` | Doc MD | `A029C6E49AD3C1FA06115091FE608E2928A223F286C43F27385D40FF980C5828` | Comprehensive investigation report |

---

## 3. Verification & Test Execution Results

- `pytest tests/unit/test_mode2_root_cause_investigation.py -v`:
  - `test_redigitized_fig13a_metrics`: PASSED
  - `test_retirement_of_legacy_145n_error`: PASSED
  - `test_preanalysis_scale_invariance_and_miseseri_mechanics`: PASSED
  - `test_coarse_fracture_trajectory_metrics`: PASSED
  - `test_live_adapted_solver_telemetry_consistency`: PASSED
  - `test_mode1_baseline_freeze_uncompromised`: PASSED
  - Summary: **6 passed in 0.46s (100% PASS)**.

---

## 4. Next Recommendations

1. Re-run or complete the post-peak softening convergence for Mode-II adapted fracture using stabilized time incrementation or load-controlled cutbacks.
2. Formulate the Method B load-partitioned execution package for Mode-I as specified in `docs/methods/MODE1_LOAD_PARTITION_EXPERIMENT_SPECIFICATION.md`.
3. Prepare the supervisor presentation update for the upcoming 22 October meeting.

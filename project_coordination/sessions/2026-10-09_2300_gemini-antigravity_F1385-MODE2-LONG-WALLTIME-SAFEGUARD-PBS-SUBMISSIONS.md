# Session Report: F1385 — Mode-II Long-Walltime PBS Safeguard Submissions for Fixed-Mesh Convergence Study

**Date:** 2026-10-09T22:35:00+02:00  
**Agent:** `gemini-antigravity`  
**Task ID:** `F1385-MODE2-LONG-WALLTIME-SAFEGUARD-PBS-SUBMISSIONS`  
**Starting Commit:** `a2921660`  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*  
**Active Phase:** `GATE_M2_1B_FIXED_MESH_CONVERGENCE_SAFEGUARDS_SUBMITTED`  

---

## 1. Executive Summary

Under explicit human authorization to protect the Mode-II spatial convergence study against 24-hour PBS walltime termination risk, this task investigated scheduler queue capabilities, prepared dedicated, independent safeguard packages, verified Abaqus compilation and datachecks, and submitted long-walltime safeguard simulations to `normal_imfdfkmq` on the TU Freiberg HPC cluster.

### Key Milestones Completed:
1. **PBS Queue Capability Verification:**
   - Queried queue limits via `qstat -Q -f normal_imfdfkmq`, establishing `resources_max.walltime = 336:00:00` (**14 days / 336 hours**).
   - Confirmed that 72:00:00 (fine mesh safeguard) and 48:00:00 (intermediate mesh safeguard) are 100% natively supported within `normal_imfdfkmq`.
2. **Safeguard Package Staging & Abaqus Datacheck Verification:**
   - Staged byte-identical input decks and compiled UEL Fortran source (`f42_mixed_uel_mode2_miehe.for`, SHA-256: `699B05D6C430FCE6242F8C603B45BB0783CF376451EFD52C56BC984B0CE71188`) in dedicated scratch directories:
     - `/scratch9/pr21vyci/runs/mode2_fixed_convergence/04_fine_72k_h3p75um_72h/`
     - `/scratch9/pr21vyci/runs/mode2_fixed_convergence/03_intermediate_40k_h5um_48h/`
   - Executed interactive Abaqus 2023 Datachecks on the cluster for both models:
     - `M2_FIX_FINE_72H`: `EXIT_CODE: 0` (compilation, linking, and datacheck 100% PASS).
     - `M2_FIX_INT_48H`: `EXIT_CODE: 0` (compilation, linking, and datacheck 100% PASS).
3. **Guarded Submission & Active Execution:**
   - Submitted both safeguard jobs via guarded wrappers with dual-channel notification integration:
     - **PBS Job ID `1411557.mmaster02` (`M2_FIX_FINE_72H`):** $71{,}824$ quads, $72{,}495$ nodes ($h = 3.73\,\mu\text{m} = l_0/4$), 1 CPU serial, 16 GB RAM, 72h walltime on `mnode097/0` in `normal_imfdfkmq`. State: `RUNNING`.
     - **PBS Job ID `1411558.mmaster02` (`M2_FIX_INT_48H`):** $40{,}000$ quads, $40{,}481$ nodes ($h = 5.00\,\mu\text{m} = l_0/3$), 1 CPU serial, 16 GB RAM, 48h walltime on `mnode097/1` in `normal_imfdfkmq`. State: `RUNNING`.
4. **Comprehensive Live HPC Monitoring Across All 5 Running Solves:**
   - Verified that all 5 active cluster jobs are solving steadily on dedicated cores of `mnode097` with strictly **0 cutbacks** and steady **3 Newton iterations per increment**:
     - `1411543.mmaster02` (`M2_FIX_MED_18K`, 24h): Inc 1844 ($u_x = 9.220\,\mu\text{m}$, entering fracture peak).
     - `1411544.mmaster02` (`M2_FIX_INT_40K`, 24h): Inc 833 ($u_x = 4.165\,\mu\text{m}$).
     - `1411545.mmaster02` (`M2_FIX_FINE_72K`, 24h): Inc 459 ($u_x = 2.295\,\mu\text{m}$).
     - `1411557.mmaster02` (`M2_FIX_FINE_72H`, 72h Safeguard): Inc 4+ ($u_x = 0.0020\,\mu\text{m}$).
     - `1411558.mmaster02` (`M2_FIX_INT_48H`, 48h Safeguard): Inc 8+ ($u_x = 0.0040\,\mu\text{m}$).
5. **Quality Assurance & Freeze Preservation:**
   - Authoritative unit test suite `test_mode2_f1385_long_walltime_safeguards.py` (5/5 PASS, 100%).
   - Full Mode-II regression suite (188/188 tests PASS).
   - Mode-I baseline freeze (`v2026.10.08-supervisor-meeting-mode1-freeze`) strictly untouched.

---

## 2. Active Cluster Jobs Table

| PBS Job ID | Target Discretization / Purpose | Status | Node / Queue | Walltime Limit | Allocated RAM | Current Increment & $u_x$ | Cutbacks / Iters |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `1411557.mmaster02` | `M2_FIX_FINE_72H` (72k FEs, $h=3.73\,\mu\text{m}$, Long-Walltime Safeguard) | `RUNNING` | `mnode097/0` / `normal_imfdfkmq` | 72:00:00 | 16 GB | Inc 4+ ($u_x = 0.0020\,\mu\text{m}$) | 0 cutbacks / 3 iters |
| `1411558.mmaster02` | `M2_FIX_INT_48H` (40k FEs, $h=5.00\,\mu\text{m}$, Long-Walltime Safeguard) | `RUNNING` | `mnode097/1` / `normal_imfdfkmq` | 48:00:00 | 16 GB | Inc 8+ ($u_x = 0.0040\,\mu\text{m}$) | 0 cutbacks / 3 iters |
| `1411545.mmaster02` | `M2_FIX_FINE_72K` (72k FEs, $h=3.73\,\mu\text{m}$, Original 24h Solve) | `RUNNING` | `mnode097/4` / `normal_imfdfkmq` | 24:00:00 | 16 GB | Inc 459 ($u_x = 2.295\,\mu\text{m}$) | 0 cutbacks / 3 iters |
| `1411544.mmaster02` | `M2_FIX_INT_40K` (40k FEs, $h=5.00\,\mu\text{m}$, Original 24h Solve) | `RUNNING` | `mnode097/3` / `normal_imfdfkmq` | 24:00:00 | 16 GB | Inc 833 ($u_x = 4.165\,\mu\text{m}$) | 0 cutbacks / 3 iters |
| `1411543.mmaster02` | `M2_FIX_MED_18K` (18k FEs, $h=7.46\,\mu\text{m}$, Original 24h Solve) | `RUNNING` | `mnode097/2` / `normal_imfdfkmq` | 24:00:00 | 16 GB | Inc 1844 ($u_x = 9.220\,\mu\text{m}$) | 0 cutbacks / 3 iters |

---

## 3. Provenance & Artifacts Generated

- `models/pandey_kumar_mode2/07_fixed_mesh_convergence_suite/04_fine_72k_h3p75um_72h/manifest.json`
- `models/pandey_kumar_mode2/07_fixed_mesh_convergence_suite/03_intermediate_40k_h5um_48h/manifest.json`
- `tests/unit/test_mode2_f1385_long_walltime_safeguards.py`
- `project_coordination/HPC_JOB_LEDGER.csv`
- `project_coordination/TASK_LEDGER.csv`
- `project_coordination/CURRENT_STATE.md`
- `project_coordination/ACTIVE_TASK.json`
- `project_coordination/ACTIVE_SESSION.json`

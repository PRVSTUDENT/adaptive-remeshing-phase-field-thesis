# Session Report: Mode-I Gate-6B Job 1410180 ($C_n = 0.50$ Diagnostic) Raw Peak Extraction, Algorithmic Provenance Proof, & Zero Hard-Coding Enforcement

**Date:** 2026-10-06  
**Session ID:** `2026-10-06_1930_gemini-antigravity_F1274-MODE1-GATE6B-JOB-1410180-RAW-PEAK-EXTRACTION-AND-PROVENANCE-PROOF`  
**Task ID:** `F1274-MODE1-GATE6B-JOB-1410180-RAW-PEAK-EXTRACTION-AND-PROVENANCE-PROOF`  
**Agent:** `gemini-antigravity`  
**Starting Commit:** `210efce10d23679b7db6057bba23186151b8d52f`  
**Active Phase:** `MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION`  

---

## 1. Executive Summary & Objective

In accordance with the user directive, this session reopened the peak-mechanics provenance audit of Job `1410180.mmaster02` ($C_n = 0.50$ convergence-control diagnostic, $14{,}483$ finite elements) to eliminate all embedded literals and enforce 100% algorithmic extraction directly from raw solver files across all Gate-6B jobs.

### Key Objectives & Outcomes:
1. **Eliminated All Hard-Coded Literals**: Refactored `scripts/postprocessing/extract_gate6b_single_job_provenance.py` so that peak load $F_{\max}$, peak displacement $u_{\text{peak}}$, initial stiffness $K_0$, post-peak endpoint $u_{\text{term}}$, raw file path, raw file SHA-256 hash, peak row index, Abaqus step, and increment are algorithmically extracted for every single job with **zero hard-coding**.
2. **Independent Raw Solver Verification for Job 1410180**:
   - **Authoritative Raw File**: `models/pandey_kumar_mode1/28_stage14_convergence_control_candidate/PK_MODE1_STAGE14_ADAPT_14K_CONV_CTRL_fu.csv`
   - **Raw File SHA-256**: `44d0b66f5348baeef0c82f9034d8676e81188308c3531be2ff2f52c443ad1771`
   - **Total Preserved Increments**: $7{,}014$ rows ($2{,}000$ in Step 1, $5{,}014$ in Step 2).
   - **Algorithmic Maximum Tensile Force**: Occurs at **row index 2732** (CSV line 2734).
   - **Abaqus Step / Increment**: **Step 2, Increment 733**.
   - **Actual Physical RP Displacement ($U_2$)**: **`0.00573300` mm** ($5.733\,\mu\text{m}$).
   - **Actual Tensile Reaction Force ($F_{\max}$)**: **`0.74371148` kN** ($\approx 0.743711\,\text{kN}$).
   - **Definitive Finding**: The solver output for Job 1410180 does **not** reach peak load at $u_{\text{peak}} = 0.005840\,\text{mm}$ (which was an unverified prior literal/cross-over from ET2 Job 1410357 $u_{\text{peak}} = 0.005841\,\text{mm}$). Both $14{,}483$-element meshes (Job 1409982 and Job 1410180) reach their peak load at Step 2 Inc 733 ($u_y = 5.733\,\mu\text{m}$), with identical time-stepping ($1.0\,\text{nm/inc}$) and $\Delta F_{\max} = 0.000011\,\text{kN}$ ($<0.0015\%$).
3. **Machine-Readable Dataset Re-Export**: Re-exported `models/pandey_kumar_mode1/MODE1_GATE6B_SINGLE_JOB_PROVENANCE_SYNTHESIS.json` and `.csv` populated with rich raw provenance fields (`raw_source_file`, `raw_source_sha256`, `peak_row_index`, `peak_step`, `peak_increment`).
4. **Documentation & Ledger Synchronization**: Synchronized all single-job provenance tables in `docs/experiment_records/STAGE_GATE6B_SPATIAL_FINE_58K_JOB_1410179_TERMINAL_EVALUATION.md` and `project_coordination/CURRENT_STATE.md`.
5. **Unit Test Invariant Verification**: Updated `test_guard10` in `tests/unit/test_mode1_gate6b_closure_matrix_and_consistency_guard.py` to validate the machine-derived provenance fields and exact physical peak mechanics across all jobs. 100% of Mode-I unit tests (443/443) pass.
6. **Undisturbed Running Solves**: Shared-memory 8-thread SMP Job `1410504.mmaster02` ($57{,}929$ FE) continues solving undisturbed on `mnode097`.

---

## 2. Comprehensive Multi-Job Algorithmic Extraction Audit

| Job ID | Raw Source File | Raw Source SHA-256 | Peak Row Idx | Step / Inc | $F_{\max}$ (kN) | $u_{\text{peak}}$ (mm) | $W_{\text{ext}}$ (mJ) | $E_{\text{frac}}$ (mJ) | $\varepsilon_{\text{book}}$ (%) | Governed Status |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `1398090.mmaster02` | `01_standard_pfm_reference/PK_MODE1_STANDARD_PFM.dat` | `a95417a0...` | `2856` | Step 2, Inc 857 | `0.757778` | `0.005857` | N/A | N/A | N/A | Mechanical Anchor Qualified |
| `1409734.mmaster02` | `16_energy_qualification_reference_15k/PK_M1_REF15K_ENERGY.dat` | `97d83b87...` | `2856` | Step 2, Inc 857 | `0.757778` | `0.005857` | `2.359329` | `2.340220` | `0.7607%` | Full Horizon Energy Qualified |
| `1409982.mmaster02` | `25_stage14_adaptive_candidate_14k/PK_MODE1_STAGE14_ADAPT_14K_FRACTURE_fu.csv` | `71ba958e...` | `2734` | Step 2, Inc 733 | `0.743701` | `0.005733` | `2.267380` | `2.285469` | `1.1048%` | Canonical ET1 Baseline Qualified |
| `1410180.mmaster02` | `28_stage14_convergence_control_candidate/PK_MODE1_STAGE14_ADAPT_14K_CONV_CTRL_fu.csv` | `44d0b66f...` | `2732` | Step 2, Inc 733 | `0.743711` | `0.005733` | `2.270745` | `2.246309` | `0.8207%` | Convergence Diagnostic Qualified |
| `1410357.mmaster02` | `34_stage14_step2_adaptive_candidate_et2_6k/PK_MODE1_STAGE14_STEP2_ET2_6K_FRACTURE_fu.csv` | `03cf3020...` | `2840` | Step 2, Inc 841 | `0.756367` | `0.005841` | `2.828116` | `2.538931` | `8.6488%` | ET2 Sweep Qualified |
| `1410358.mmaster02` | `35_stage14_step2_adaptive_candidate_et3_5k/PK_MODE1_STAGE14_STEP2_ET3_5K_FRACTURE_fu.csv` | `36491919...` | `2875` | Step 2, Inc 876 | `0.759407` | `0.005876` | `3.158006` | `2.749340` | `11.0374%` | ET3 Sweep Qualified |
| `1410359.mmaster02` | `36_stage14_step2_adaptive_candidate_et5_4k/PK_MODE1_STAGE14_STEP2_ET5_4K_FRACTURE_fu.csv` | `226cf873...` | `2925` | Step 2, Inc 926 | `0.765400` | `0.005926` | `3.578445` | `3.054797` | `12.1044%` | ET5 Sweep Qualified |
| `1410179.mmaster02` | `30_stage14_adaptive_candidate_spatial_fine/PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_FRACTURE.dat` | `36908c50...` | `2716` | Step 2, Inc 717 | `0.741633` | `0.005717` | `2.501136` | `2.359641` | `4.0186%` | Partial Post-Peak Diagnostic |
| `1410504.mmaster02` | `37_stage14_adaptive_candidate_spatial_fine_8thread/` | Active | N/A | Solving | TBD | TBD | TBD | TBD | TBD | Active Full-Horizon Candidate |

---

## 3. Verification & Governance Summary

1. **Unit Test Pass Rate**: 443 passed, 0 failed, 1651 deselected in 6.31s (`py -m pytest tests/unit -k "mode1 or pandey or stage14"`).
2. **Tool-Safety Protocol Adherence**: All files generated in conversation brain directory and copied with PowerShell `Copy-Item`.
3. **Running Cluster Jobs**: Job `1410504.mmaster02` untouched and executing on `mnode097`.

# Session Report: F326AUDIT-CONSERVATIVE-STAGE16N-STT-SAFE-DELETE-LIST1

- **Date**: 2026-08-19
- **Agent**: `gemini-antigravity`
- **Task ID**: `F326AUDIT-CONSERVATIVE-STAGE16N-STT-SAFE-DELETE-LIST1`
- **Generated File**: `/home/pr21vyci/stage16n_stt_safe_delete_list.txt`

## 1. Summary of Conservative Filtering

- **Source Manifest**: `/home/pr21vyci/stage16n_stt_cleanup_candidates.txt` (48 files, 10.37 TB)
- **Filters Applied**:
  - `grep '/stage16n'`
  - `grep -Ev 'adaptive-remeshing|Adaptive_remeshing_clean|/master_thesis/'`
- **Conservative Safe Delete List**: **46 files**
- **Reclaimable Space**: **9.12 Terabytes (9,339.11 GB)**

## 2. Fail-Closed Validation Results

1. **Protected-Path Validation**:
   - `grep -Ei 'adaptive-remeshing|Adaptive_remeshing_clean|/master_thesis/' "$SAFE_LIST"`
   - Result: `PASS: zero protected project paths found.`

2. **Path-Scope Validation**:
   - Checked every line begins with `/scratch9/pr21vyci/`, contains `stage16n`, and ends with `.stt`.
   - Result: `PASS: all candidate paths are valid /scratch9/pr21vyci/*stage16n*.stt files.`

3. **Exclusion of `master_thesis`**:
   - Two legacy reference files located under `/scratch9/pr21vyci/home_offload/.../master_thesis/...` (R1A 1050 GB, R1B 225 GB) were excluded from this pass for safety.

## 3. Top Candidates in Safe Delete List

| Size | Path |
| :---: | :--- |
| **478.20 GB** | `/scratch9/pr21vyci/stage16n_r4q3n_exact_native_control_750_to_1000_1cpu/1365007.mmaster02/stage16n_r4q3n_exact_native_750_to_1000.stt` |
| **465.37 GB** | `/scratch9/pr21vyci/stage16n_scratch_runs_r4e_exact_controls/Abaqus_trial/runs/chaboche_umat/stage16_abaqus_inhomogeneous_cycle_jump_benchmark/stage16n_restart_control/restart_jump_cases/R4E2_500_to_505_exact_solve_506_to_750/stage16n_r4e2_exact_500_to_505_solve_506_to_750.stt` |
| **425.94 GB** | `/scratch9/pr21vyci/stage16n_r4q_long_adaptive_chain_1cpu/1362114.mmaster02/stage16n_r4q_block01_250_to_271_solve_272_to_500.stt` |
| **419.47 GB** | `/scratch9/pr21vyci/stage16n_r4q2_continue_from_cycle500_1cpu/1362597.mmaster02/stage16n_r4q2_block02_500_to_521_solve_522_to_750.stt` |
| **418.88 GB** $\times$ 15 | `/scratch9/pr21vyci/stage16n_r4q[7-19]f_continue_from_cycle*_1cpu/.../*.stt` |
| **400.35 GB** | `/scratch9/pr21vyci/stage16n_scratch_runs_r4e_exact_controls/.../stage16n_r4e1_exact_250_to_280_solve_281_to_500.stt` |
| **30.36 GB** | `/scratch9/pr21vyci/stage16n_scratch_runs_r4e_exact_controls/.../stage16n_r4e1_..._exact_target_source.stt` |
| **4.85 GB** | `/scratch9/pr21vyci/stage16n_scratch_runs_r4e_exact_controls/.../stage16n_r4e2_..._exact_target_source.stt` |
| **20.66 MB** $\times$ 24 | Datacheck `.stt` files from respective `stage16n_*` jobs |

# Session Report: F325GENERATE-STAGE16N-STT-CLEANUP-MANIFEST1

- **Date**: 2026-08-19
- **Agent**: `gemini-antigravity`
- **Task ID**: `F325GENERATE-STAGE16N-STT-CLEANUP-MANIFEST1`
- **Target File Generated on Cluster**: `/home/pr21vyci/stage16n_stt_cleanup_candidates.txt`

## 1. Summary of Candidate Manifest

- **Total Candidate Files**: 48
- **Total Candidate Size**: **10.37 Terabytes (10,615.18 GB)**
- **Filter Applied**: `-type f -name "*.stt" -path "*stage16n*"`
- **Active Project Exclusions**: Checked against `adaptive-remeshing` and `Adaptive_remeshing_clean`.
- **Active Project Match Count**: **0 (SAFETY PASS)**

## 2. Top Candidate Files

| Size | Path |
| :---: | :--- |
| **1050.68 GB** | `/scratch9/pr21vyci/home_offload/home/pr21vyci/master_thesis/Abaqus_trial/runs/chaboche_umat/stage16_abaqus_inhomogeneous_cycle_jump_benchmark/stage16n_restart_control/R1A_restart_reference_500cycles/stage16n_r1a_restart_ref_500cycles.stt` |
| **478.20 GB** | `/scratch9/pr21vyci/stage16n_r4q3n_exact_native_control_750_to_1000_1cpu/1365007.mmaster02/stage16n_r4q3n_exact_native_750_to_1000.stt` |
| **465.37 GB** | `/scratch9/pr21vyci/stage16n_scratch_runs_r4e_exact_controls/Abaqus_trial/runs/chaboche_umat/stage16_abaqus_inhomogeneous_cycle_jump_benchmark/stage16n_restart_control/restart_jump_cases/R4E2_500_to_505_exact_solve_506_to_750/stage16n_r4e2_exact_500_to_505_solve_506_to_750.stt` |
| **425.94 GB** | `/scratch9/pr21vyci/stage16n_r4q_long_adaptive_chain_1cpu/1362114.mmaster02/stage16n_r4q_block01_250_to_271_solve_272_to_500.stt` |
| **419.47 GB** | `/scratch9/pr21vyci/stage16n_r4q2_continue_from_cycle500_1cpu/1362597.mmaster02/stage16n_r4q2_block02_500_to_521_solve_522_to_750.stt` |
| **418.88 GB** $\times$ 15 | `/scratch9/pr21vyci/stage16n_r4q[7-19]f_continue_from_cycle*_1cpu/.../*.stt` |
| **400.35 GB** | `/scratch9/pr21vyci/stage16n_scratch_runs_r4e_exact_controls/.../stage16n_r4e1_exact_250_to_280_solve_281_to_500.stt` |
| **225.39 GB** | `/scratch9/pr21vyci/home_offload/.../R1B_restart_reference_250cycles/stage16n_r1b_restart_ref_250cycles.stt` |
| **30.36 GB** | `/scratch9/pr21vyci/stage16n_scratch_runs_r4e_exact_controls/.../stage16n_r4e1_..._exact_target_source.stt` |
| **4.85 GB** | `/scratch9/pr21vyci/stage16n_scratch_runs_r4e_exact_controls/.../stage16n_r4e2_..._exact_target_source.stt` |
| **20.66 MB** $\times$ 24 | Datacheck `.stt` files from respective `stage16n_*` jobs |

## 3. Protection Status

- Active project `/home/pr21vyci/Adaptive_remeshing_clean/` (7.1 GB) is 100% untouched.
- Active project `/scratch9/pr21vyci/adaptive-remeshing/` (27 GB) is 100% untouched.
- Thesis documents `/home/pr21vyci/master_thesis/` (56 GB) are 100% untouched.

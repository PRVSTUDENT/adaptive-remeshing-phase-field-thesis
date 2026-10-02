# Session Report: F324AUDIT-HPC-STORAGE-AND-SCRATCH-INVENTORY1

- **Date**: 2026-08-19
- **Agent**: `gemini-antigravity`
- **Task ID**: `F324AUDIT-HPC-STORAGE-AND-SCRATCH-INVENTORY1`
- **Target Systems**: `tu_freiberg` cluster (`/home/pr21vyci`, `/scratch9/pr21vyci`, `/projects`)

## 1. Summary of Audit Findings

1. **Overall Cluster Volume Usage**:
   - `/scratch` (default alias): 92 TB used / 101 TB capacity (92%).
   - `/scratch9`: 18 TB used / 33 TB capacity (54%).
   - User account `pr21vyci` total usage on `/scratch9` is **13 Terabytes**.
   - User account `pr21vyci` total usage on `/home` is **~120 Gigabytes**.

2. **Root Cause of High Storage Consumption**:
   - **~12.9 Terabytes (over 99%)** of the space consumed by `pr21vyci` is located in legacy Abaqus UMAT cycle-jump benchmark runs (`stage16n_*`), primarily consisting of massive `.stt` (Abaqus restart/status scratch files) ranging from **416 GB to 1050 GB each**.
   - **Active Phase-Field Adaptive Remeshing**: Consumes only **27 GB** in `/scratch9/pr21vyci/adaptive-remeshing` and **7.1 GB** in `/home/pr21vyci/Adaptive_remeshing_clean`.

## 2. Inventory Classification (KEEP / OFFLOAD / DELETE-CANDIDATES)

| Category | Path / Artifact | Size | Description & Action |
| :--- | :--- | :---: | :--- |
| **KEEP (Active Thesis)** | `/home/pr21vyci/Adaptive_remeshing_clean/` | 7.1 GB | Active repo, models, code, UEL subroutines, Stage-D/E packages |
| **KEEP (Active Thesis)** | `/scratch9/pr21vyci/adaptive-remeshing/` | 27 GB | Phase-field solver ODBs, DAT files, Stage-F / Mode-II benchmarks |
| **KEEP (Local Home)** | `/home/pr21vyci/master_thesis/` | 56 GB | LaTeX thesis source, figures, reference data |
| **OFFLOAD CANDIDATES** | `/scratch9/pr21vyci/adaptive-remeshing/runs/*.odb` | ~10 GB | Completed benchmark ODBs (archive locally if needed) |
| **SAFE-TO-DELETE CANDIDATE** | `/scratch9/pr21vyci/stage16n_r4q*_1cpu/*.stt` | ~8.0 TB | 19 separate `.stt` scratch files (~418 GB each) from cycle-jump runs |
| **SAFE-TO-DELETE CANDIDATE** | `/scratch9/pr21vyci/home_offload/.../*.stt` | ~1.3 TB | Legacy cycle-jump reference `.stt` (1050 GB + 225 GB) |
| **SAFE-TO-DELETE CANDIDATE** | `/scratch9/pr21vyci/stage16n_scratch_runs_r4e_exact_controls/.../*.stt` | ~0.9 TB | Legacy cycle-jump `.stt` files (465 GB + 400 GB) |
| **SAFE-TO-DELETE CANDIDATE** | `/scratch9/pr21vyci/stage16n_r4q3n_exact_native_control_750_to_1000_1cpu/*.stt` | 478 GB | Legacy cycle-jump `.stt` |

Deleting or truncating only the legacy cycle-jump `.stt` scratch files will instantly free **over 10.5 Terabytes** without affecting any phase-field or adaptive-remeshing results.

# Path and environment map

## Local workstation

| Role | Path |
|---|---|
| Repository root | `D:\Master thesis\Adaptive remeshing` |
| Coordination | `project_coordination/` |
| Mode-I models | `models/pandey_kumar_mode1/` |
| Mode-II models | `models/pandey_kumar_mode2/` |
| Active session lock | `project_coordination/ACTIVE_SESSION.json` |
| Active task state | `project_coordination/ACTIVE_TASK.json` |
| Coordination dashboard | `project_coordination/CURRENT_STATE.md` |
| Execution ledgers | `project_coordination/TASK_LEDGER.csv`, `HPC_JOB_LEDGER.csv` |
| Artifact registry | `project_coordination/ARTIFACT_REGISTRY.csv` |

## HPC (TU Bergakademie Freiberg) — Canonical Storage Architecture

| Role | Path / value | Storage Policy |
|---|---|---|
| Project source repository | `/home/pr21vyci/projects/adaptive-remeshing` | **Lightweight source ONLY** (`.inp`, `.for`, `.py`, `.sh`, `.pbs`, `.md`, `.json`, `.csv`, `.tex`). Strictly zero `.odb`, `.res`, `.sim`, `.pac`, `.abq`, `.sel`, `.stt`, `.mdl`, `.023`, `.cax` permitted. |
| Production solver execution workspace | `/scratch9/pr21vyci/projects/adaptive-remeshing/` (or `/scratch/pr21vyci/projects/adaptive-remeshing/`) | **Canonical Abaqus solver execution directory**. All active `.odb`, `.dat`, `.msg`, `.sta`, `.prt`, `.log` files reside exclusively on PanFS scratch. |
| Hard Storage Guard | `if [[ "$(pwd -P)" =~ ^/home/ ]]; then exit 88; fi` | Hard execution barrier in all PBS scripts rejecting `/home/` launches. |
| Preferred queue | `normal_imfdfkmq` / `entry_imfdfkmq` | Normal production execution / fast datacheck routing |
| Abaqus toolchain | `abaqus/2023` | `/cluster/application/abaqus/2023/Commands/abaqus` |
| Compiler toolchain | `intel/2024.2.0`, `gcc/11.4.0` | `ifort` (IFORT) 2021.13.0, `gcc` 11.4.0 |
| Notification configuration | `~/.config/adaptive-remeshing/notifications.env` | Dual-channel PBS mail (`-m abe`) + Telegram webhook |

## Scientific stages (pointer only)

| Stage | Canonical anchors |
|---|---|
| Mode I Reference & Convergence | `models/pandey_kumar_mode1/01_standard_pfm_reference/`, `12_fixed_convergence_h0020/` |
| Mode I Stage 14 Adaptive Candidates | `models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/`, `28_stage14_convergence_control_candidate/`, `30_stage14_adaptive_candidate_spatial_fine/` |
| Mode II Paper-Grounded Pre-Analysis | `models/pandey_kumar_mode2/06_paper_grounded_uel_preanalysis/` |
| Thesis Report & Documentation | `MA_AdaptiveRemeshing_Report_2026/`, `docs/` |

## Inventories

| File | Content |
|---|---|
| `inventories/LOCAL_REPOSITORY_INVENTORY.csv` | sanitized local paths |
| `inventories/HPC_REPOSITORY_INVENTORY.csv` | cluster clone inventory |
| `inventories/HPC_SCRATCH_EVIDENCE_INDEX.csv` | scratch evidence metadata only |
| `inventories/INVENTORY_SUMMARY.md` | counts and exclusions |

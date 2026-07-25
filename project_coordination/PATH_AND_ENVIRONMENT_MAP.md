# Path and environment map

## Local workstation

| Role | Path |
|---|---|
| Repository root | `D:\Master thesis\Adaptive remeshing` |
| Coordination | `project_coordination/` |
| Mode-II H0 package | `models/generated/mode_ii/h0_serial/` |
| Mode-II auth | `runs/hpc/stage_f/mode_ii_h0/MODE_II_H0_AUTHORIZATION.json` |
| Stage F scripts | `scripts/hpc/stage_f/` |
| Mode-II validators | `scripts/validation/validate_mode_ii_h0_*.py` |
| Legacy agent handoff (dirty) | `agent_handoff/` |

## HPC (TU Bergakademie Freiberg)

| Role | Path / value |
|---|---|
| Project clone (typical) | `/home/pr21vyci/projects/adaptive-remeshing` |
| Scratch runs | `/scratch/pr21vyci/adaptive-remeshing/runs/` |
| Mode-II staging (planned) | `/scratch/pr21vyci/adaptive-remeshing/mode_ii_h0_staged/<revision>/` |
| Preferred queue | `entry_imfdfkmq` |
| Abaqus | `abaqus/2023` |
| Intel | `intel/2024.2.0` |
| GCC | `gcc/11.4.0` |

Exact cluster paths must be re-verified during F1-P0.

## Scientific stages (pointer only)

| Stage | Canonical anchors |
|---|---|
| Mode I / A–C | `models/generated/molnar_gravouil_2017/`, `runs/hpc/stage_c2/` |
| State transfer D | `models/state_transfer/`, `runs/hpc/stage_d3/` |
| Parallel P | `models/parallelization/`, `runs/hpc/stage_p/` — **closed; do not reopen** |
| Mode II F | `models/generated/mode_ii/`, `runs/hpc/stage_f/` |
| Thesis docs | `docs/thesis/` — packaging only when tasked |

## Inventories

| File | Content |
|---|---|
| `inventories/LOCAL_REPOSITORY_INVENTORY.csv` | sanitized local paths |
| `inventories/HPC_REPOSITORY_INVENTORY.csv` | cluster clone inventory (filled at F1-P0) |
| `inventories/HPC_SCRATCH_EVIDENCE_INDEX.csv` | scratch evidence metadata only |
| `inventories/INVENTORY_SUMMARY.md` | counts and exclusions |

# Inventory summary

Generated: 2026-07-25 during COORD-0

## Local repository inventory

| Item | Value |
|---|---|
| File | `LOCAL_REPOSITORY_INVENTORY.csv` |
| Row count (approx) | 2046 |
| Source | Live walk of workspace at COORD-0 |

### Excluded from local inventory

- `.git/`
- `.kilo/` and `node_modules/`
- `tmp/`
- `__pycache__`, `*.pyc`
- LaTeX auxiliaries (`.aux`, `.log`, `.out`, `.toc`, `.fls`, `.fdb_latexmk`, `.synctex.gz`, …)
- Local PDF build directories under `results/latex_*` and related supervisor build trees
- `*.odb`

### Not committed as-is

The raw user upload `file_list.csv` (11,706 entries including `.git`/`.kilo`) remains **untracked** and is **not** the sanitized inventory.

## HPC inventories

| File | Status |
|---|---|
| `HPC_REPOSITORY_INVENTORY.csv` | Header-only placeholder; fill during F1-P0 |
| `HPC_SCRATCH_EVIDENCE_INDEX.csv` | Header-only placeholder; fill during F1-P0 |

No ODB files are copied into `project_coordination/`.

## Dirty paths

`DIRTY_PATHS_PRESERVED.txt` captures porcelain status at COORD-0 for resume safety.

# Inventory summary

Updated: 2026-07-26 during F1-J1

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
| `HPC_REPOSITORY_INVENTORY.csv` | Header-only placeholder |
| `HPC_SCRATCH_EVIDENCE_INDEX.csv` | Recorded F1-J0 datacheck (`1378911.mmaster02`) and F1-J1 solver (`1378919.mmaster02`) scratch evidence |

No ODB files are copied into `project_coordination/`.

## Dirty paths

`DIRTY_PATHS_PRESERVED.txt` captures porcelain status for resume safety.

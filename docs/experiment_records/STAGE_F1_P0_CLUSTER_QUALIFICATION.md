# Stage F1-P0 — Mode-II H0 cluster synchronization and offline qualification

Classification: `stage_f_mode_ii_h0_cluster_qualification_pass`
Date: 2026-07-25
Agent: grok
Task: F1-P0

## Revisions

| Role | SHA |
|---|---|
| Operational repository | `97756e09caad28ebd6257f3406c7d6365eca771a` |
| Frozen Stage-F scientific package | `17240f646cf1e382396006ab635976fa22a67890` |
| Local HEAD | `97756e09caad28ebd6257f3406c7d6365eca771a` |
| GitHub main (after fetch) | `97756e09caad28ebd6257f3406c7d6365eca771a` |
| Cluster pre-sync | `8d920db09bb79846fe15697d785d37a012426638` |
| Cluster post-sync | `97756e09caad28ebd6257f3406c7d6365eca771a` |

Cluster path: `/home/pr21vyci/projects/adaptive-remeshing`

## Pre-existing dirty paths

### Local (preserved, not cleaned)

Unrelated porcelain remained: dirty/deleted `agent_handoff/*`, modified Gate-A3 docs/figures/scripts, untracked supervisor/latex/build artifacts. Not modified by F1-P0.

### Cluster (before sync)

- Tracked modifications: **none**
- Untracked PBS stdout leftovers only (preserved; no `git clean`):
  - `d3d_a1h0_dc.o1378003`, `d3d_a1h0_dc_r1.o1378004`, `d3d_a1h0_dc_r2.o1378005`
  - `p3s_serial.o1378028`, `p3sb_baseline.o1378094`, `p3sm0_serial.o1378099`
  - `p3sm1t_serial.o1378239`, `p3sm1tc_serial.o1378240`, `p3sm1r_serial.o1378241`, `p3t4_threaded.o1378242`

Sync method: `git fetch origin` + `git merge --ff-only origin/main` (no reset/hard/clean).

## Frozen package hashes (local and cluster)

| File | SHA-256 | Match |
|---|---|---|
| `ModeII_H0_serial.inp` | `32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b` | yes |
| `ModeII_H0_serial.for` | `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c` | yes |

`PACKAGE_MANIFEST.json` and `input_hashes.sha256` agree with file digests.

## Validation results

| Check | Local | Cluster |
|---|---|---|
| `check_multi_agent_bootstrap.py` | pass (lock temporarily free) | pass |
| `validate_mode_ii_h0_static.py` | `stage_f_mode_ii_h0_static_pass` | `stage_f_mode_ii_h0_static_pass` |
| `python -m py_compile` validators | pass | pass |
| `bash -n` datacheck PBS | n/a (Windows) | pass |
| `bash -n` submit wrapper | n/a (Windows) | pass |
| Prepared-state preflight | pass | pass |
| `--require-datacheck` preflight | blocked | blocked |

Authorization block reason (both sides): datacheck classification must be
`stage_f_mode_ii_h0_datacheck_authorized` because the prepared record remains
unauthorized (`datacheck_authorized=false`). Failure was **not** due to missing
files, hashes, shell syntax, or package inconsistency.

## Queue inspection

- `qstat -u pr21vyci` inspected
- No queued/running `mode_ii_h0_dc` entry
- Jobs submitted by F1-P0: **0**
- Authorization changes: **none**

## Scratch evidence

No Stage-F / Mode-II scratch outputs found under
`/scratch/pr21vyci/adaptive-remeshing` or `/scratch9/pr21vyci/adaptive-remeshing`.
Recorded in `project_coordination/inventories/HPC_SCRATCH_EVIDENCE_INDEX.csv`.

## Exact next action

**F1-J0-AUTH** — separate authorization-only commit setting
`datacheck_authorized=true` / classification
`stage_f_mode_ii_h0_datacheck_authorized` for one datacheck only.
Do **not** submit until after that commit and explicit submission approval.

# Current project state

Updated: 2026-07-25  
Classification: `multi_agent_coordination_layer_initialized`

## Git

| Item | Value |
|---|---|
| Local HEAD (at COORD-0 start) | `17240f646cf1e382396006ab635976fa22a67890` |
| Message | Prepare Stage F Mode-II H0 offline package and fail-closed lane |
| Active agent | none (`ACTIVE_SESSION.json.active = false`) |
| Active task | **F1-P0** ready (not started) |

## Scientific status

| Area | Status |
|---|---|
| Mode-I pre-refinement | Scoped single-notch closeout only |
| Evolving transfer (D) | Bounded pre-peak only; D3D-A1 mechanical restart unproven |
| ABAQUSER (WP6) | Externally blocked |
| Stage P | Scientifically closed; do not reopen |
| Thesis faculty candidate (WP7-F3) | Candidate only; not submission-ready |
| **Stage F Mode-II** | **F0 prepared; F1-J0 unauthorized** |

## Stage F freeze

- Package: `models/generated/mode_ii/h0_serial`
- Auth: `runs/hpc/stage_f/mode_ii_h0/MODE_II_H0_AUTHORIZATION.json`
- Flags: `datacheck_authorized=false`, `solver_authorized=false`, max 1 each, no retry/threads/MPI
- Static: `stage_f_mode_ii_h0_static_pass`
- Deck SHA-256: `32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b`
- Source SHA-256: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`

## Next actions (in order)

1. **F1-P0** — cluster sync + offline qualification; **submit nothing**
2. **F1-J0-AUTH** — separate authorization-only commit
3. **F1-J0** — one datacheck `mode_ii_h0_dc` after explicit approval
4. **F1-J1** — only if F1-J0 passes

## Dirty paths deliberately preserved (do not clean)

Recorded at COORD-0 from `git status --porcelain` (unrelated to Stage F):

- Dirty/deleted `agent_handoff/*` (including deleted mirrored docs)
- Modified: `docs/decisions/MOLNAR_GATE_A3_SUPERVISOR_REVIEW.md`, `docs/handoffs/MOLNAR_GATE_A3_MEETING_SUMMARY.md`, `results/figures/molnar_lc015_h_convergence/01_rf_u_h0_h1_h2.png`, `runs/hpc/stage_d3/interrupted_transfer/checkpoint/D3A_BLOCKED_STATUS.json`, `scripts/postprocessing/analyze_molnar_lc015_h_convergence.py`
- Untracked examples: `00_NOTEBOOKLM_VIDEO_BRIEF.md`, `HPC_2026/`, supervisor progress TeX/PDF, latex build dirs, stage_c2 recovery artifacts, `file_list.csv`, ODB under local one-element evidence, various `_tmp_*.sh`

Full porcelain snapshot: `inventories/DIRTY_PATHS_PRESERVED.txt`

**Do not** run `scripts/sync_agent_handoff.py` or broad clean while these remain.

## HPC job ledger

Empty for Stage F (no Mode-II jobs submitted). Historical Mode-I/D/P jobs remain in their original `runs/hpc/**` trees; optional backfill later.

## Inventories

- Local sanitized: `inventories/LOCAL_REPOSITORY_INVENTORY.csv` (~2046 rows after exclusions)
- HPC inventories: placeholders until F1-P0

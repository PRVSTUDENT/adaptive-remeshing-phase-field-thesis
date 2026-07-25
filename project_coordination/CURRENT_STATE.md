# Current project state

Updated: 2026-07-25
Protocol version: 1
Classification: `multi_agent_bootstrap_entrypoints_integrated`

## Git

| Item | Value |
|---|---|
| Coordination HEAD (pre-COORD-1) | `88ea1b68622c52c31fb9eb6c9929d9f67eb573e3` |
| F0 scientific freeze | `17240f646cf1e382396006ab635976fa22a67890` |
| Active agent | none (`ACTIVE_SESSION.json.active = false`) |
| Active task | **F1-P0** ready |
| Canonical bootstrap | `AGENTS.md` |

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
- Flags: `datacheck_authorized=false`, `solver_authorized=false`
- Deck SHA-256: `32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b`
- Source SHA-256: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`

## Multi-agent bootstrap (COORD-1)

Entry points now point at this folder:

- `AGENTS.md` (canonical)
- `.agent.md` / `adaptive_remeshing_phase_field_agent.md` (compatibility + stable rules)
- `GEMINI.md`, `GROK.md` (pointer shims)
- `README.md` notice
- `project_coordination/PROTOCOL_VERSION.json`
- Validator: `scripts/validation/check_multi_agent_bootstrap.py`

Legacy `agent_handoff/` is **not** active coordination.

## Next actions (in order)

1. **F1-P0** — cluster sync + offline qualification; **submit nothing**
2. **F1-J0-AUTH** — separate authorization-only commit
3. **F1-J0** — one datacheck after explicit approval
4. **F1-J1** — only if F1-J0 passes

## Dirty paths deliberately preserved

See `inventories/DIRTY_PATHS_PRESERVED.txt`. Do not run
`scripts/sync_agent_handoff.py` while those paths remain.

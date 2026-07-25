# Current project state

Updated: 2026-07-25  
Protocol version: 1  
Classification: `stage_f_mode_ii_h0_cluster_qualification_pass`

## Git

| Item | Value |
|---|---|
| Operational HEAD | `97756e09caad28ebd6257f3406c7d6365eca771a` |
| F0 scientific freeze | `17240f646cf1e382396006ab635976fa22a67890` |
| Local / GitHub / cluster | **identical** at operational HEAD |
| Active agent | none (release after F1-P0 commit) |
| Active task | **F1-J0-AUTH** ready (blocked until explicit approval) |

## Scientific status

| Area | Status |
|---|---|
| Mode-I pre-refinement | Scoped single-notch closeout only |
| Evolving transfer (D) | Bounded pre-peak only; D3D-A1 mechanical restart unproven |
| ABAQUSER (WP6) | Externally blocked |
| Stage P | Scientifically closed; do not reopen |
| **Stage F Mode-II** | **F0 frozen; F1-P0 cluster qualification passed; F1-J0 unauthorized** |

## Stage F freeze (unchanged)

- Package: `models/generated/mode_ii/h0_serial`
- Auth: `runs/hpc/stage_f/mode_ii_h0/MODE_II_H0_AUTHORIZATION.json`
- Flags: `datacheck_authorized=false`, `solver_authorized=false`
- Deck SHA-256: `32a25380767bbb0e9e76eb55b3bb7a97d78bb75c4f86c7e8585aa2032ce2d33b`
- Source SHA-256: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`

## F1-P0 qualification summary

- Cluster path: `/home/pr21vyci/projects/adaptive-remeshing`
- Sync: fast-forward only from `8d920db` → `97756e0`
- Static / bootstrap / py_compile / bash -n: pass
- Prepared preflight: pass
- Require-datacheck preflight: blocked (authorization false)
- Jobs submitted: 0
- Evidence: `docs/experiment_records/STAGE_F1_P0_CLUSTER_QUALIFICATION.md`
- Machine record: `runs/hpc/stage_f/mode_ii_h0/qualification/F1_P0_QUALIFICATION.json`

## Next actions (in order)

1. **F1-J0-AUTH** — separate authorization-only commit (no submit)
2. Explicit submission approval
3. **F1-J0** — one datacheck `mode_ii_h0_dc`
4. **F1-J1** — only if F1-J0 passes

## Dirty paths deliberately preserved

Local porcelain (agent_handoff, untracked builds, etc.) and cluster untracked
`*.o*` PBS logs were **not** cleaned.

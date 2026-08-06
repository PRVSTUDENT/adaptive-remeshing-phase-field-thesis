# Session report: F38 close M2RMBUILD11

- Agent: `codex`
- Starting commit: `6dde6662fa0143c7dbad4c6e8b52f63c33f88d04`
- Scope: read-only cluster evidence collection and canonical F37 terminal closeout metadata
- Submission, retry, replacement, qdel, qmove, solver, CAE, datacheck, remesh, and state-transfer calls: `0`

## Verified result

PBS job `1384181.mmaster02` is terminal failed with exit 1. It used 6 seconds walltime after 4:29:38 eligible time. Package compatibility and the embedded Python resolver probe passed. Abaqus/CAE invoked the builder through `execfile(..., __main__.__dict__)`, where `__file__` is undefined, producing `NameError` at `build_f37_geometry_backed_model.py:16` before model import. No generated deck or scientific result exists.

The scheduler facts, failure identity, and SHA-256 hashes of eight remote evidence artifacts are recorded in `runs/hpc/stage_f/f37_m2rmbuild11_static_gate/M2RMBUILD11_TERMINAL_CLOSEOUT.json`.

## Changes

- Closed the F37 task and HPC ledger entries as `cae_geometry_build_contract_failed`.
- Updated current state and active task to F38 offline diagnostic preparation pending.
- Registered the terminal closeout artifact.
- Preserved all pre-existing dirty paths.

## Validation

- Parsed `ACTIVE_SESSION.json`, `ACTIVE_TASK.json`, and the terminal closeout as JSON.
- `git diff --check` passed; only pre-existing line-ending warnings were reported.

## Next action

Prepare a distinct F38 offline-only comprehensive CAE phase diagnostic matrix package. It must not be submitted without fresh, exact human authorization.

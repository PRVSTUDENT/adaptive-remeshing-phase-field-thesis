# F17 Linux manifest repair session

Agent: codex
Task: F17-LINUX-MANIFEST-REPAIR-AND-REAUTHORIZATION-PREPARATION
Starting commit: `3435f68a1046b03a9fd77c27ca5802d9d15a0508`
Original F17 preparation: `41aaf8ee9582b4a245cf3d64cd6dbf309f752ef5`
Invalidated authorization: `b6f3478b8dae8732acb0b8126f0ec75af215ea5e`
Repair candidate: `76addd7a409c550eed52f9297b4f30b6e8647073`

## Reports produced

- `F17_MANIFEST_MISMATCH_FORENSIC_AUDIT.json`
- `F17_CLEAN_LINUX_REPRODUCIBILITY_PROOF.json`
- `STAGE_F17_LINUX_MANIFEST_REPAIR.md`
- `STAGE_F17_LINUX_MANIFEST_REPAIR_PREPARATION.md`
- this session report

## Diagnosis and changes

All ten original mismatches are classified as
`CRLF_LF_checkout_transformation`: Windows Git used `core.autocrlf=true`, the
original manifests recorded CRLF working-tree bytes, and Git/Linux used LF.
Only the two package manifests changed. Explicit 12-entry and 11-entry
allowlists and deterministic generation/validation tooling were added.
No `.gitattributes` change was made because the committed blobs were already
canonical LF bytes.

## Second clean Linux proof

Path: `/scratch/pr21vyci/adaptive-remeshing/runs/stage_f17/F17_MANIFEST_PROOF_76addd7`.
Git status: empty.
Result: failed before manifest validation because frozen `M2RMREG4.pbs` lacks
a final LF. Its last byte is decimal 99. The frozen PBS file was not changed,
and the required stop rule prevented another repair iteration.

Probe manifest SHA-256: `e9b3e47ad1fd929a77410399f88ee0b9fce59269f1854a4aa59ff449d025d8e6` (12 entries).
Region manifest SHA-256: `9a28a7448b0dd9e2f55c043a4b12b5fe20127e4a325cf88d428f844ba5d7f5ec` (11 entries).
Reproducibility classification: `f17_clean_linux_manifest_reproducibility_failed_missing_final_lf`.

Tests passed: forensic byte audit, clean detached checkout, clean Git status,
candidate checkout at exact SHA. Test failed: canonical final-LF validation of
`M2RMREG4.pbs`; subsequent manifest/contract tests were not reached.

HPC commands: read-only SSH/Git/hash diagnostics only.
Jobs submitted/PBS IDs: none.
qsub attempts/successes/failures: `0/0/0`.
Execution authorization/submission approval/maximum jobs now: `false/false/0`.
Scientific changes: none.
Dirty paths deliberately preserved: all pre-existing local and cluster paths.
Exact next action: obtain an explicit decision permitting a new preparation that adds the missing final LF and supersedes the frozen M2RMREG4 PBS hash, then rerun the full two-worktree proof.

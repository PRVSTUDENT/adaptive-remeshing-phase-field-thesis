# Stage F17 Linux manifest repair preparation

Starting SHA: `3435f68a1046b03a9fd77c27ca5802d9d15a0508`.

The package scientific/runtime files were not changed. Two package manifests
were corrected to the canonical Linux/Git-blob hashes. An explicit 12-entry
penalty-probe allowlist and 11-entry adaptive-region allowlist now drive one
deterministic validator/generator. The forensic audit is retained in
`runs/hpc/stage_f/f17_penalty_activation_and_adaptive_region_repair/`.

No qsub, Abaqus, CAE, datacheck, adaptivity, remesh, candidate generation, or
refined analysis is permitted or performed in this preparation.

## Second-clean-worktree result

Candidate `76addd7a409c550eed52f9297b4f30b6e8647073` was checked out in a
second detached Linux worktree with empty `git status --short`. The proof
stopped before manifest validation because the canonical-text validator found
that frozen `M2RMREG4.pbs` ends in byte `99` (`c`), not LF. Changing that file
would change its explicitly frozen hash, so no silent repair iteration was
performed. Classification:
`f17_clean_linux_manifest_reproducibility_failed_missing_final_lf`.

## Authorized final-LF repair

Exactly one final LF was appended to `M2RMREG4.pbs`, changing its size from
1,166 to 1,167 bytes and superseding only its PBS hash. The adaptive package's
two checksum records were updated. All other scientific/runtime hashes and
the 11-entry allowlist remain unchanged. A fresh preparation and second clean
Linux proof are required before any execution authorization.

### Final-LF qualification outcome

The repair was published as `a44c2b6651bd541bfc3bbe82479a2474af743c6c`.
The first fresh WSL2 checkout passed all 11 adaptive-region entries and then
reported `final LF missing` for frozen `M2IRRPENACT1.pbs` (2,242 bytes,
final byte 48, SHA-256 `1d233a82...`). The additional edit was not authorized,
so the second validation was not run. Qsub attempts remain zero.

### Final canonical qualification

Preparation `b4d9fad` repaired the adaptive legacy manifest. The independent
Linux worktree passed probe 12/12 twice, adaptive 11/11 twice, and 23/23
checkout-to-blob comparisons. No scheduler or scientific execution occurred.

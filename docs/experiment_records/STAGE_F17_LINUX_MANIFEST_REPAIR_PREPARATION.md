# Stage F17 Linux manifest repair preparation

Starting SHA: `3435f68a1046b03a9fd77c27ca5802d9d15a0508`.

The package scientific/runtime files were not changed. Two package manifests
were corrected to the canonical Linux/Git-blob hashes. An explicit 12-entry
penalty-probe allowlist and 11-entry adaptive-region allowlist now drive one
deterministic validator/generator. The forensic audit is retained in
`runs/hpc/stage_f/f17_penalty_activation_and_adaptive_region_repair/`.

No qsub, Abaqus, CAE, datacheck, adaptivity, remesh, candidate generation, or
refined analysis is permitted or performed in this preparation.

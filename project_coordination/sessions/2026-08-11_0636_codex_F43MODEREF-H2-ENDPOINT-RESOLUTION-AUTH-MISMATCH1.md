# F43MODEREF-H2-ENDPOINT-RESOLUTION-AUTH-MISMATCH1

The user authorized exactly one guarded H2 endpoint-resolution submission but specified `12:00:00` while simultaneously requiring the exact frozen package from `F43MODEREF-H2-ENDPOINT-RESOLUTION-PREP1`. The frozen qualified package uses `24:00:00` following the user's subsequent walltime instruction.

Fail-closed verification:

- Frozen PBS directive: `#PBS -l walltime=24:00:00`.
- Frozen PBS SHA256: `96854cf7058ecf6d7d571b758aa937bf199ec9b8a5eef90d7578e4d969f5be89`.
- Frozen manifest SHA256: `2238e1461ef9b7744f2d0b5e8b79c59a49048f465bb77a6d99d769ca2d13296e`.
- P commit/tag object: `195e37d8c4398058c0ff19e0a7d9d78d0c27d529` / `9bce2126761584debab79a9cccaf5f70afd2e4dd`.
- Q commit/tag object: `b4d3e55a9d56cfad7151dc6249d1d3c6262b55c8` / `985412bfdc54b759fab22e1dc6ece178379a4b9c`.
- P-to-Q execution-critical byte identity: PASS.
- Cluster `qstat -u pr21vyci` command completed successfully.
- Authorization/package walltime consistency: FAIL (`12:00:00` authorized versus `24:00:00` frozen).

Per the user's explicit fail-closed condition, zero jobs were submitted. No authorization record was created, no wrapper was invoked, and no `qsub`, retry, replacement, `qmove`, or `qdel` occurred. A corrected direct human authorization that explicitly names the frozen `24:00:00` package is required.

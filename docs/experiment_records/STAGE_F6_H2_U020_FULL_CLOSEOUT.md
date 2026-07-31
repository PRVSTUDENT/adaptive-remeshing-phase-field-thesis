# Stage F6 H2 u020 full-run closeout

## Provenance and execution

- Task: `F6-H2-FULL-AND-MISESERI-REMESH-API-BATCH`
- Job: `1379966.mmaster02` (`M2H2U20F1`)
- Package revision: `2249ec21fe92c6c7348d1cff653a84901828e117`
- Authorization revision: `5b5c2f4c596e419d4dcfca9cc1e80ba343f5cb82`
- Submission revision: `7a859ceeaa0e9e7477d3abcdfcdb7a0d358b0d9c`
- Runtime: Abaqus 2023, ifort 2021.13.0, one CPU, 16 GB requested
- Scheduler: `normal_imfdfkmq`, `mnode105/0`, state `F`, exit 12
- Resources used: walltime `04:43:26`, CPU time `04:37:57`,
  resident memory `1,776,392 kB`, virtual memory `7,548,580 kB`

The immutable source hashes passed. Abaqus compiled and linked the user
subroutine, completed the input processor and all 5,000 increments, and
reported `Abaqus JOB M2H2U20F1 COMPLETED`. Solver and extractor return codes
were both zero. The wrapper returned 12 because its Python-3 validator was
invoked through Abaqus 2023 Python 2.7 and stopped on
`from __future__ import annotations`. A separate Python 3.11 offline replay
completed with return code 1 and preserved the scientific failure.

## Numerical and scientific result

The run reached the prescribed endpoint:

- final displacement: `U1 = 0.019999999553 mm`
- peak reaction: `RF1 = 0.1387272626 kN` at `U1 = 0.01190000027 mm`
- final reaction: `RF1 = 0.08054406196 kN`
- post-peak force drop: `41.9407%`
- initial stiffness: `12.79115985 kN/mm` (`R² = 0.99999949`, 17 points)
- maximum phase-field value: `1.004587054`
- first `d >= 0.5`: `U1 = 0.01190000027 mm`
- first `d >= 0.9`: `U1 = 0.01219999976 mm`
- crack elements at `d >= 0.5`: 1,316
- measured crack extension: `0.730205 mm`; not ligament spanning
- framewise maximum-damage decreases: 11
- largest recorded decrease: `-1.0073185e-4`
- energy histories: unavailable from the retained ODB output request

The canonical offline validator passed 8 of 9 checks and classified the run
`stage_f_mode_ii_h2_uniform_serial_validation_fail` because its declared
framewise maximum-damage irreversibility gate did not pass. The small phase
overshoot remains within the validator's `d <= 1.01` warning band. This job
therefore establishes technical full-run completion, the H2 peak and u020
post-peak response, and endpoint attainment. It does not establish accepted
phase-field irreversibility, energy consistency, mesh convergence beyond the
previous elastic comparison, remeshing accuracy, parallel safety, or
experimental/paper-level agreement.

## Evidence and authorization boundary

Canonical evidence:
`runs/hpc/stage_f/f6_h2_full_and_miseseri_remesh_api_batch/evidence/1379966.mmaster02/`.
The 943,852,504-byte ODB remains scratch-only at
`/scratch/pr21vyci/adaptive-remeshing/runs/stage_f6/F6_20260730_122800_2249ec21/h2_u020_full/M2H2U20F1.odb`
with SHA-256
`b1e6b0bc82bc0febd5b208f81e3dd09f60a0adec91bba47e4a1ed96ac7a555bb`.
No ODB or solver database was copied into Git.

The two-job authorization is consumed at 2/2. No retry, replacement, direct
`qsub`, `qdel`, or `qmove` occurred or is authorized. Job B
`1379967.mmaster02` remains independently closed as
`abaqus_cae_start_failure`.


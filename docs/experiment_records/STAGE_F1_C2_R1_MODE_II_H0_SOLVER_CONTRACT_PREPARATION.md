# Stage F1-C2-R1 Mode-II H0 Endpoint-Corrected Serial Solver Contract Preparation Record

Date: 2026-07-28
Task ID: `F1-C2-R1-SOLVER-PREP`
Classification: `stage_f_mode_ii_h0_endpoint_corrected_serial_solver_contract_prepared_unauthorized`
Base Revision: `87ed0ead18de4dc6ad6bfa72f5273f4955218bfe`
Validated Datacheck Job ID: `1379387.mmaster02`
Preparation Revision: `f7e44ae6e7df7dcf1b7eb468eaa946b2eec9caae`

## Executive Summary

Task **`F1-C2-R1-SOLVER-PREP`** repaired and qualified the wrapper-to-PBS staging and runtime execution contract for the serial corrected Mode-II H0 baseline solver lane before any solver submission is approved.

The scientific package (`models/generated/mode_ii/h0_endpoint_corrected_serial/`) remained byte-identical. The submit wrapper [`scripts/hpc/stage_f/submit_mode_ii_h0_endpoint_corrected_serial.sh`](file:///d:/Master%20thesis/Adaptive%20remeshing/scripts/hpc/stage_f/submit_mode_ii_h0_endpoint_corrected_serial.sh) and PBS execution script [`scripts/hpc/stage_f/04_mode_ii_h0_endpoint_corrected_serial.pbs`](file:///d:/Master%20thesis/Adaptive%20remeshing/scripts/hpc/stage_f/04_mode_ii_h0_endpoint_corrected_serial.pbs) were updated to prestage both the scientific package and postprocessing/validation runtime scripts (`extract_molnar_single_notch.py`, `validate_mode_ii_h0_endpoint_corrected_results.py`, etc.), passing four required environment variables via `qsub -v`:
1. `PRESTAGED_ROOT`
2. `LOGIN_MANIFEST_PATH`
3. `PROJECT_REVISION`
4. `PRESTAGED_RUNTIME_ROOT`

The contract was fully qualified using a static solver contract validator, 195 unit tests, and a local solver staging smoke test. **0 HPC jobs were submitted, 0 Abaqus executions occurred, and solver submission remains unapproved (`solver_authorized: false`, `maximum_jobs_now: 0`).**

## Producer-Consumer Contract Map

| Variable | Producer | Consumer | Purpose / Verification |
|---|---|---|---|
| `PRESTAGED_ROOT` | Submit Wrapper | PBS Script | Staging root on HPC scratch containing package and manifest |
| `LOGIN_MANIFEST_PATH` | Submit Wrapper | PBS Script | Machine JSON manifest recording revision and SHA-256 hashes |
| `PROJECT_REVISION` | Git / Submit Wrapper | PBS Script | Full Git HEAD revision for traceability |
| `PRESTAGED_RUNTIME_ROOT` | Submit Wrapper | PBS Script | Staged directory containing extractor & validator Python scripts |
| `OMP_NUM_THREADS` | PBS Script | Runtime Environment | Set to `1` for single-thread serial execution |
| `MKL_NUM_THREADS` | PBS Script | Runtime Environment | Set to `1` for single-thread MKL execution |

## Staging & Runtime Verification

- **Deck SHA-256 (`ModeII_H0_endpoint_corrected_serial.inp`)**: `c9160d50c944de7037a9f05dc1dbccfa9718f69b198bb48659f784bac220ddef` (Pass)
- **Source SHA-256 (`ModeII_H0_endpoint_corrected_serial.for`)**: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c` (Pass)
- **Static Contract Validator**: `scripts/validation/validate_mode_ii_h0_endpoint_corrected_solver_staging_contract.py` (`stage_f_mode_ii_h0_endpoint_corrected_solver_staging_contract_pass`)
- **Local Staging Smoke**: `scripts/validation/run_mode_ii_h0_endpoint_corrected_solver_staging_smoke.py` (`stage_f_mode_ii_h0_endpoint_corrected_solver_local_staging_smoke_pass`)
- **Unit Test Suite**: `python -m unittest discover -s tests/unit` (195/195 tests passed)

## Governance & Resource Limits

- `datacheck_authorized`: `false` (consumed `1/1`)
- `solver_authorized`: `false` (contract prepared; reauthorization pending task `F1-C2-R1-SOLVER-REAUTH`)
- `solver_submissions_used`: `0`
- `maximum_solver_submissions`: `1`
- `submission_approved`: `false`
- `execution_authorized`: `false`
- `automatic_retry_authorized`: `false`
- `maximum_jobs_now`: `0`
- Downstream task F2: `blocked`

## Next Steps

1. Contract repair and qualification is complete.
2. Prepare task **`F1-C2-R1-SOLVER-REAUTH`** for human review to grant solver authorization.

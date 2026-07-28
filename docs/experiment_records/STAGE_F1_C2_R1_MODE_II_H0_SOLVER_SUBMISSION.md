# Stage F1-C2-R1 Mode-II H0 Endpoint-Corrected Serial Baseline Solver Submission Record

Date: 2026-07-28
Task ID: `F1-C2-R1-SOLVER`
Classification: `stage_f_mode_ii_h0_endpoint_corrected_serial_solver_submitted`
PBS Job ID: `1379393.mmaster02`
Execution Revision: `4d3de793e8ed37d650a0d83d9906afd0b313e661`
Solver Preparation Revision: `f7e44ae6e7df7dcf1b7eb468eaa946b2eec9caae`
Solver Correction Revision: `0a7e72a25a06428dd97e9ad1f1d134bea4404289`
Validated Datacheck Job ID: `1379387.mmaster02`
Datacheck Closeout Revision: `91d6fad0b972687380759c30a3a268515a733339`

## Executive Summary

Task **`F1-C2-R1-SOLVER`** executed the single authorized serial solver submission for the corrected Mode-II H0 baseline.

The submission was launched via guarded submission wrapper [`scripts/hpc/stage_f/submit_mode_ii_h0_endpoint_corrected_serial.sh`](file:///d:/Master%20thesis/Adaptive%20remeshing/scripts/hpc/stage_f/submit_mode_ii_h0_endpoint_corrected_serial.sh) with explicit environment flag `ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_SOLVER_SUBMIT=1` and task authorization [`/scratch/pr21vyci/adaptive-remeshing/authorizations/F1-C2-R1-SOLVER_4d3de793e8ed37d650a0d83d9906afd0b313e661.json`](file:///scratch/pr21vyci/adaptive-remeshing/authorizations/F1-C2-R1-SOLVER_4d3de793e8ed37d650a0d83d9906afd0b313e661.json).

PBS Job ID **`1379393.mmaster02`** was returned by `qsub` (wrapper exit code 0) and is currently running on cluster execution host `mnode105/0`.

## Submission Details

- **Job Name**: `mode_ii_h0_endpoint_corrected_serial`
- **Queue**: `entry_imfdfkmq` (routed to `normal_imfdfkmq`)
- **Execution Host**: `mnode105/0`
- **Job State**: `R` (Running)
- **Staging Root**: `/scratch/pr21vyci/adaptive-remeshing/mode_ii_h0_endpoint_corrected_staged/4d3de793e8ed37d650a0d83d9906afd0b313e661`
- **Login Manifest**: `/scratch/pr21vyci/adaptive-remeshing/mode_ii_h0_endpoint_corrected_staged/4d3de793e8ed37d650a0d83d9906afd0b313e661/MODE_II_H0_LOGIN_MANIFEST.json`
- **Runtime Root**: `/scratch/pr21vyci/adaptive-remeshing/mode_ii_h0_endpoint_corrected_staged/4d3de793e8ed37d650a0d83d9906afd0b313e661/runtime`
- **Corrected Input Deck SHA-256**: `c9160d50c944de7037a9f05dc1dbccfa9718f69b198bb48659f784bac220ddef`
- **Corrected Fortran Source SHA-256**: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`
- **Resource Plan**: 1 CPU / 1 MPI rank / 1 OpenMP thread / 16 GB memory / 04:00:00 walltime

## Evidence Collection

Lightweight evidence copied to [`runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/replacement_r1/solver_submission/1379393.mmaster02/`](file:///d:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/replacement_r1/solver_submission/1379393.mmaster02/):
- `operational_authorization.json`
- `wrapper_output.txt`
- `initial_qstat.txt`
- `submission_summary.json`

## Governance Boundary

- `guarded_wrapper_count`: `1`
- `direct_qsub`: `false`
- `solver_submissions_used`: `1`
- `solver_authorized`: `false`
- `execution_authorized`: `false`
- `automatic_retry_authorized`: `false`
- `maximum_jobs_now`: `0`
- Downstream task F2: `blocked`

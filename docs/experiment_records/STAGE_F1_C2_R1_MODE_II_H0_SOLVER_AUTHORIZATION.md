# Stage F1-C2-R1 Mode-II H0 Endpoint-Corrected Serial Solver Authorization Record

Date: 2026-07-28
Task ID: `F1-C2-R1-SOLVER-AUTH`
Classification: `stage_f_mode_ii_h0_endpoint_corrected_serial_solver_authorized`
Base Revision: `2ba31abc222eeca6d2bf407e298670772a549406`
Validated Datacheck Job ID: `1379387.mmaster02`
Datacheck Closeout Revision: `91d6fad0b972687380759c30a3a268515a733339`
Datacheck Submission Revision: `51b01ea6540663bab5a2b07b5f2b3e76cde3e23b`
Authorization Revision: `8cec3dbde56b08f8924d8298c05052da430dd4ba`

## Executive Summary

Task **`F1-C2-R1-SOLVER-AUTH`** reviewed the successful replacement datacheck evidence from job `1379387.mmaster02` and granted authorization for **exactly one serial baseline solver run** for the endpoint-corrected Mode-II H0 benchmark package under execution lane `runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/replacement_r1/`.

This task is an **offline authorization review only**. It does **not** submit the solver, execute Abaqus, call `qsub`, or approve operational submission. Actual solver submission requires a separate explicit human approval under task **`F1-C2-R1-SOLVER`**.

## Datacheck Gate Review Summary

- **PBS Job ID**: `1379387.mmaster02`
- **PBS Exit Status**: `0`
- **Abaqus Return Code**: `0`
- **DATACHECK_ok**: `true`
- **Datacheck Classification**: `stage_f_mode_ii_h0_endpoint_corrected_datacheck_pass`
- **Input Deck SHA-256 (`ModeII_H0_endpoint_corrected_serial.inp`)**: `c9160d50c944de7037a9f05dc1dbccfa9718f69b198bb48659f784bac220ddef`
- **Fortran UMAT SHA-256 (`ModeII_H0_endpoint_corrected_serial.for`)**: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`
- **PRESTAGED_ROOT Received**: `true`
- **LOGIN_MANIFEST_PATH Received**: `true`
- **PROJECT_REVISION Received**: `true`
- **Critical Abaqus Errors**: `0`

## Solver Job Plan & Resource Allocation

- **Job Name**: `mode_ii_h0_endpoint_corrected_serial`
- **Package Path**: `models/generated/mode_ii/h0_endpoint_corrected_serial`
- **PBS Script**: `scripts/hpc/stage_f/04_mode_ii_h0_endpoint_corrected_serial.pbs`
- **Submit Wrapper**: `scripts/hpc/stage_f/submit_mode_ii_h0_endpoint_corrected_serial.sh`
- **Queue**: `entry_imfdfkmq`
- **CPUs / MPI / OpenMP**: 1 / 1 / 1 (Serial CPU)
- **Memory**: `16 GB`
- **Walltime**: `04:00:00`
- **Maximum Authorized Solver Submissions**: `1`
- **Solver Submissions Used**: `0`

## Scope & Fail-Closed Guardrails

1. **Single Submission Limit**: Exactly 1 serial solver submission is authorized.
2. **Submission Unapproved**: Operational submission remains unapproved (`submission_approved: false`, `maximum_jobs_now: 0`).
3. **No Automatic Retry**: Automatic retry is prohibited (`automatic_retry_authorized: false`).
4. **No Parallel Execution**: MPI, OpenMP threading, and hybrid parallel execution are strictly unauthorized.
5. **Stage F2 Block**: Downstream tasks (F2 multi-mesh adaptation) remain blocked until the corrected serial H0 baseline run completes cleanly.

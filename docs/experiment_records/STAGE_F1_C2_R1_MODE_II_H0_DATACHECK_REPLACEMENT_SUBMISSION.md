# Stage F1-C2-R1 Replacement Mode-II H0 Datacheck Submission Record

Date: 2026-07-28
Task ID: `F1-C2-R1-DATACHECK`
Classification: `stage_f_mode_ii_h0_endpoint_corrected_datacheck_replacement_submitted`
Operational Approval Revision: `51b01ea6540663bab5a2b07b5f2b3e76cde3e23b`
Submitted Job ID: `1379387.mmaster02`

## Executive Summary

Task **`F1-C2-R1-DATACHECK`** executed exactly ONE guarded replacement datacheck submission for the corrected Mode-II H0 benchmark package (`models/generated/mode_ii/h0_endpoint_corrected_serial`).

Submission was executed via the repaired submission wrapper `scripts/hpc/stage_f/submit_mode_ii_h0_endpoint_corrected_datacheck.sh` under explicit human approval. The wrapper verified local package SHA-256 hashes, staged the package to login scratch, generated the login manifest, passed `PRESTAGED_ROOT`, `LOGIN_MANIFEST_PATH`, and `PROJECT_REVISION` into `qsub`, and successfully submitted job `1379387.mmaster02` to the cluster scheduler.

The single replacement authorization was immediately consumed (`datacheck_authorized: false`, `datacheck_submissions_used: 1`, `maximum_jobs_now: 0`).

## Submission Details

- **PBS Job ID**: `1379387.mmaster02`
- **Job Name**: `mode_ii_h0_endpoint_corrected_datacheck`
- **Queue**: `entry_imfdfkmq` (routed to `normal_imfdfkmq`)
- **Execution Host**: `mnode100/0`
- **Resource Plan**: 1 CPU, 16 GB RAM, 00:30:00 walltime
- **PRESTAGED_ROOT**: `/scratch/pr21vyci/adaptive-remeshing/mode_ii_h0_endpoint_corrected_staged/51b01ea6540663bab5a2b07b5f2b3e76cde3e23b`
- **LOGIN_MANIFEST_PATH**: `/scratch/pr21vyci/adaptive-remeshing/mode_ii_h0_endpoint_corrected_staged/51b01ea6540663bab5a2b07b5f2b3e76cde3e23b/MODE_II_H0_LOGIN_MANIFEST.json`
- **PROJECT_REVISION**: `51b01ea6540663bab5a2b07b5f2b3e76cde3e23b`

## Scientific Package Hashes

- **Input Deck (`ModeII_H0_endpoint_corrected_serial.inp`)**:
  `c9160d50c944de7037a9f05dc1dbccfa9718f69b198bb48659f784bac220ddef`
- **Fortran UMAT (`ModeII_H0_endpoint_corrected_serial.for`)**:
  `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`

## Governance & Limits

- `datacheck_authorized`: `false` (consumed `1/1`)
- `datacheck_submissions_used`: `1`
- `maximum_datacheck_submissions`: `1`
- `submission_approved`: `true`
- `solver_authorized`: `false`
- `automatic_retry_authorized`: `false`
- `maximum_jobs_now`: `0`

## Next Steps

Task **`F1-C2-R1-CLOSE`** will monitor job `1379387.mmaster02`, collect evidence, verify the datacheck pass status, and close out the replacement datacheck task.

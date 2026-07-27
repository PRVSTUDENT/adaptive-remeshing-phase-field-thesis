# Stage F1-C2-R1 Mode-II H0 Datacheck Replacement Staging Preparation Record

- **Stage**: Stage F (Mode-II mixed-mode benchmark)
- **Task ID**: `F1-C2-R1-PREP`
- **Classification Target**: `stage_f_mode_ii_h0_endpoint_corrected_datacheck_replacement_prepared_unauthorized`
- **Parent Revision**: `20cad4f94133635076da48eda821b50dd53a050a`
- **Source Failed Job**: `1378958.mmaster02` (`stage_f_mode_ii_h0_endpoint_corrected_datacheck_stage_fail`)
- **Date**: 2026-07-27
- **Author**: gemini-antigravity

---

## 1. Background & Root Cause Analysis

Initial datacheck job `1378958.mmaster02` failed after 3 seconds on compute node `mnode098` because `submit_mode_ii_h0_endpoint_corrected_datacheck.sh` omitted the required environment variables:
- `PRESTAGED_ROOT`
- `LOGIN_MANIFEST_PATH`
- `PROJECT_REVISION`

from the `-v` parameter list in `qsub`.

This failure was purely an **infrastructure staging contract defect**. The corrected Mode-II H0 input deck (`ModeII_H0_endpoint_corrected_serial.inp`) and Fortran source (`ModeII_H0_endpoint_corrected_serial.for`) were not executed by Abaqus and remain byte-identical to the qualified baseline.

---

## 2. Staging Contract Repairs & Improvements

1. **Guarded Submission Wrapper**: Updated [submit_mode_ii_h0_endpoint_corrected_datacheck.sh](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/hpc/stage_f/submit_mode_ii_h0_endpoint_corrected_datacheck.sh) to:
   - Perform static & preflight checks on package hashes (`c9160d50...` and `5decf4b1...`).
   - Create a task-specific login-side prestaging directory containing `MODE_II_H0_LOGIN_MANIFEST.json`.
   - Explicitly pass `-v "PRESTAGED_ROOT=${STAGE_ROOT},LOGIN_MANIFEST_PATH=${MANIFEST},PROJECT_REVISION=${REVISION}"` to `qsub`.
   - Require explicit authorization file and environment flag (`ALLOW_MODE_II_H0_ENDPOINT_CORRECTED_DATACHECK_SUBMIT=1`).

2. **Static Staging Contract Validator**: Created [validate_mode_ii_h0_endpoint_corrected_staging_contract.py](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/validation/validate_mode_ii_h0_endpoint_corrected_staging_contract.py) to statically verify mapping between submit wrapper variables and PBS script expectations (`stage_f_mode_ii_h0_endpoint_corrected_staging_contract_pass`).

3. **Mocked Submission Unit Tests**: Created [test_submit_mode_ii_h0_endpoint_corrected_datacheck.py](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_submit_mode_ii_h0_endpoint_corrected_datacheck.py) verifying all fail-closed rules and capturing mocked `qsub` arguments.

4. **Local Staging Smoke Test**: Created [run_mode_ii_h0_endpoint_corrected_staging_smoke.py](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/validation/run_mode_ii_h0_endpoint_corrected_staging_smoke.py) generating evidence under `runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/replacement_r1/smoke_evidence/local/` (`stage_f_mode_ii_h0_endpoint_corrected_staging_smoke_pass`).

5. **Cluster Login Smoke Test**: Verified cluster environment and preserved evidence under `runs/hpc/stage_f/mode_ii_h0_endpoint_corrected/replacement_r1/smoke_evidence/cluster_login/` (`stage_f_mode_ii_h0_endpoint_corrected_cluster_login_smoke_pass`).

---

## 3. Package Integrity Verification

- **Deck SHA-256**: `c9160d50c944de7037a9f05dc1dbccfa9718f69b198bb48659f784bac220ddef` (100% byte-identical)
- **Source SHA-256**: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c` (100% byte-identical)

---

## 4. Governance & Execution Limits

- **HPC Jobs Executed**: `0`
- **PBS Submissions**: `0`
- **Abaqus Executions**: `0`
- **Datacheck Authorized**: `false` (requires explicit `F1-C2-R1-AUTH` approval)
- **Solver Authorized**: `false`
- **Automatic Retry Authorized**: `false`
- **Maximum Jobs Permitted Now**: `0`
- **Stage F2 Status**: **Blocked**

# Stage F1-J1-R2 Mode-II Second Replacement Preparation Record

- **Task ID**: `F1-J1-R2-PREP`
- **Stage**: Stage F (Mode-II mixed-mode benchmark)
- **Classification**: `stage_f_mode_ii_h0_second_replacement_prepared_unauthorized`
- **Preparation Parent Revision**: `eb3c31e0f7db93248a09235f6ac87f37d78bede1`
- **Scientific Freeze Revision**: `17240f646cf1e382396006ab635976fa22a67890`
- **Source Failures**:
  - `F1-J1` (job `1378919.mmaster02`, `stage_f_mode_ii_h0_serial_staging_fail`, solver_started=false, consumed=true)
  - `F1-J1-R1` (job `1378920.mmaster02`, `stage_f_mode_ii_h0_serial_staging_fail`, solver_started=false, consumed=true)
- **Inline Staging Logic Removed**: `true` (obsolete inline `matches` dictionary replaced with executable helper)
- **Exact Runtime Helper Tested**: `true` (`scripts/validation/verify_mode_ii_h0_runtime_staging.py`)
- **Pre-Solver Smoke Local**: `pass` (`classification = stage_f_mode_ii_h0_pre_solver_smoke_pass`)
- **Pre-Solver Smoke Cluster Login**: `pass`
- **Replacement Authorized**: `false` (unauthorized; preparation only)
- **Submission Approved**: `false`
- **Jobs Submitted**: 0

## Repair Strategy & Executable Staging Helper Integration

1. **Standalone Staging Verifier Helper**:
   - Implemented `scripts/validation/verify_mode_ii_h0_runtime_staging.py` as an executable Python script supporting `--login-manifest`, `--runtime-manifest`, and `--output`.
   - Verified that login and runtime manifests match for `project_revision`, `deck_sha256`, `source_sha256`, `extractor_sha256`, `validator_sha256`, `pbs_script_sha256`, `staging_checker_sha256`, and `abaqus_deck_sha256 == deck_sha256`.
   - Guaranteed fail-closed operation writing structured `stage_f_mode_ii_h0_runtime_staging_fail` JSON on malformed or missing inputs without uncaught tracebacks.

2. **PBS Script Refactoring**:
   - `scripts/hpc/stage_f/02_mode_ii_h0_serial.pbs` now completely delegates manifest verification to `verify_mode_ii_h0_runtime_staging.py`.
   - Removed all obsolete inline manifest-comparison dictionaries (`matches[field + "_match"]`, `matches["deck_hash_match"]`).
   - Added `MODE_II_H0_PRE_SOLVER_ONLY=1` pre-solver smoke mode: executes full manifest verification and exits 0 with `stage_f_mode_ii_h0_pre_solver_smoke_pass` before invoking Abaqus or creating an ODB.

3. **Guarded Submit Wrapper**:
   - `scripts/hpc/stage_f/submit_mode_ii_h0_serial.sh` stages and hashes `verify_mode_ii_h0_runtime_staging.py` into `MODE_II_H0_LOGIN_MANIFEST.json` as `staging_checker_sha256`.

4. **Pre-Solver Smoke & Unit Verification**:
   - Pre-solver smoke test verified under repository-local staging root `tmp/smoke_stage/` with exit code 0, status `stage_f_mode_ii_h0_pre_solver_smoke_pass`, runtime staging check `stage_f_mode_ii_h0_runtime_staging_pass`, zero Abaqus calls, and zero ODB files.
   - Comprehensive unit test suite (`tests/unit/test_verify_mode_ii_h0_runtime_staging.py` and `tests/unit/test_validate_mode_ii_h0_serial_staging_contract.py`) passed (44 unit tests).
   - Staging contract validator `scripts/validation/validate_mode_ii_h0_serial_staging_contract.py` passed cleanly.

5. **Strict Authorization Boundary**:
   - Both `1378919.mmaster02` (F1-J1) and `1378920.mmaster02` (F1-J1-R1) remain consumed (`authorization_consumed: true`).
   - R2 replacement execution remains unauthorized (`replacement_authorized: false`, `submission_approved: false`, `jobs_submitted: 0`).
   - Downstream Stage F tasks (F2+) remain **blocked**.

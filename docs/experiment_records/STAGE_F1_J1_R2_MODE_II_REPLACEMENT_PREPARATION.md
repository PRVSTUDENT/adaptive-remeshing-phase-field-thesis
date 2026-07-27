# Stage F1-J1-R2 Mode-II Second Replacement Preparation Record

- **Task ID**: `F1-J1-R2-PREP-R1`
- **Stage**: Stage F (Mode-II mixed-mode benchmark)
- **Classification**: `stage_f_mode_ii_h0_second_replacement_runtime_qualified_unauthorized`
- **Preparation Parent Revision**: `4f67bd2c8fd0a1a1c2e57d8dba54cd16a2ff2a36`
- **Runtime Qualification Commit**: `217b684cc5611377e495442728e39d350d01eb61`
- **Scientific Freeze Revision**: `17240f646cf1e382396006ab635976fa22a67890`
- **Source Failures**:
  - `F1-J1` (job `1378919.mmaster02`, `stage_f_mode_ii_h0_serial_staging_fail`, solver_started=false, consumed=true)
  - `F1-J1-R1` (job `1378920.mmaster02`, `stage_f_mode_ii_h0_serial_staging_fail`, solver_started=false, consumed=true)
- **Inline Staging Logic Removed**: `true` (obsolete inline `matches` dictionary replaced with executable helper)
- **Exact Runtime Helper Tested**: `true` (`scripts/validation/verify_mode_ii_h0_runtime_staging.py`)
- **Local Smoke Evidence**: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence/local/SMOKE_SUMMARY.json`
- **Local Smoke Passed**: `true`
- **Cluster Smoke Evidence**: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence/cluster_login/SMOKE_SUMMARY.json`
- **Cluster Login Smoke Passed**: `true`
- **Cluster Modules Loaded**: `true` (`module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7`)
- **Cluster Abaqus Executable Found**: `true` (`/syscomp/abaqus/2023/Commands/abaqus`)
- **Replacement Authorized**: `false` (unauthorized; preparation only)
- **Submission Approved**: `false`
- **Jobs Submitted**: 0

## Repair Strategy & Executable Staging Helper Integration

1. **Standalone Staging Verifier Helper**:
   - Implemented `scripts/validation/verify_mode_ii_h0_runtime_staging.py` as an executable Python script supporting `--login-manifest`, `--runtime-manifest`, and `--output`.
   - Verified that login and runtime manifests match for `project_revision`, `deck_sha256`, `source_sha256`, `extractor_sha256`, `validator_sha256`, `pbs_script_sha256`, `staging_checker_sha256`, and `abaqus_deck_sha256 == deck_sha256`.
   - Guaranteed fail-closed operation writing structured `stage_f_mode_ii_h0_runtime_staging_fail` JSON on malformed or missing inputs without uncaught tracebacks.

2. **PBS Script Refactoring & Fail-Closed Environment Restoration**:
   - `scripts/hpc/stage_f/02_mode_ii_h0_serial.pbs` delegates manifest verification to `verify_mode_ii_h0_runtime_staging.py`.
   - Removed obsolete inline manifest-comparison dictionaries (`matches[field + "_match"]`, `matches["deck_hash_match"]`).
   - Restored fail-closed environment module handling: normal solver and cluster-login execution require `command -v module` and module loading; local Windows smoke may bypass modules only when both `MODE_II_H0_PRE_SOLVER_ONLY=1` and `MODE_II_H0_ALLOW_LOCAL_NO_MODULES=1` are explicitly set.
   - Fixed pre-solver smoke return-code semantics: outputs `abaqus_invoked=false`, `module_environment_loaded`, and null return codes for non-invoked tools (`abaqus_return_code=null`, `extractor_return_code=null`, `validator_return_code=null`).
   - Smoke mode creates `MODE_II_H0_PRE_SOLVER_SMOKE.ok` instead of `MODE_II_H0_SERIAL.ok`.

3. **Guarded Submit Wrapper**:
   - `scripts/hpc/stage_f/submit_mode_ii_h0_serial.sh` stages and hashes `verify_mode_ii_h0_runtime_staging.py` into `MODE_II_H0_LOGIN_MANIFEST.json` as `staging_checker_sha256`.

4. **Pre-Solver Smoke & Qualification Evidence**:
   - **Local Windows Smoke**: Passed with module bypass (`MODE_II_H0_ALLOW_LOCAL_NO_MODULES=1`), zero Abaqus invocations, zero ODB files. Evidence committed in `runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence/local/`.
   - **Cluster Login-Node Smoke**: Passed on cluster login node (`mlogin01.hrz.tu-freiberg.de`) with actual module loading (`module_environment_loaded=true`), Abaqus executable verified (`/syscomp/abaqus/2023/Commands/abaqus`), PBS exit code 0, zero Abaqus invocations, zero ODB files. Evidence committed in `runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence/cluster_login/`.
   - Comprehensive unit test suite (`tests/unit/test_verify_mode_ii_h0_runtime_staging.py`, `tests/unit/test_validate_mode_ii_h0_serial_staging_contract.py`, and `tests/unit/test_run_pre_solver_smoke.py`) passed (55 unit tests).
   - Staging contract validator `scripts/validation/validate_mode_ii_h0_serial_staging_contract.py` passed cleanly.

5. **Strict Authorization Boundary**:
   - Both `1378919.mmaster02` (F1-J1) and `1378920.mmaster02` (F1-J1-R1) remain consumed (`authorization_consumed: true`).
   - R2 replacement execution remains unauthorized (`replacement_authorized: false`, `submission_approved: false`, `jobs_submitted: 0`).
   - Downstream Stage F tasks (F2+) remain **blocked**.

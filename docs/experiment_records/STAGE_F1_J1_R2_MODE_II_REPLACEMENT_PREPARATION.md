# Stage F1-J1-R2 Mode-II Second Replacement Preparation Record

- **Task ID**: `F1-J1-R2-PREP-R2`
- **Stage**: Stage F (Mode-II mixed-mode benchmark)
- **Classification**: `stage_f_mode_ii_h0_second_replacement_provenance_qualified_unauthorized`
- **Preparation Parent Revision**: `440ff8a22fcfd7a2674ad9ec5de76d2b0f8b271b`
- **Runtime Provenance Commit**: `620a4e01038991b89cef70091afb03e70c6922f7`
- **Scientific Freeze Revision**: `17240f646cf1e382396006ab635976fa22a67890`
- **Source Failures**:
  - `F1-J1` (job `1378919.mmaster02`, `stage_f_mode_ii_h0_serial_staging_fail`, solver_started=false, consumed=true)
  - `F1-J1-R1` (job `1378920.mmaster02`, `stage_f_mode_ii_h0_serial_staging_fail`, solver_started=false, consumed=true)
- **Inline Staging Logic Removed**: `true` (obsolete inline `matches` dictionary replaced with executable helper)
- **Exact Runtime Helper Tested**: `true` (`scripts/validation/verify_mode_ii_h0_runtime_staging.py`)
- **Local Smoke Bundle**: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence_r2/local/EVIDENCE_BUNDLE_MANIFEST.json`
- **Local Bundle Verified**: `true`
- **Cluster Smoke Bundle**: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence_r2/cluster_login/EVIDENCE_BUNDLE_MANIFEST.json`
- **Cluster Bundle Verified**: `true`
- **Cluster Modules Loaded**: `true` (`module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7`)
- **Cluster Abaqus Executable Found**: `true` (`/syscomp/abaqus/2023/Commands/abaqus`)
- **Replacement Authorized**: `false` (unauthorized; preparation only)
- **Submission Approved**: `false`
- **Jobs Submitted**: 0

## Repair Strategy & Provenance Qualification

1. **Pre-Solver Smoke Semantics Repair**:
   - `scripts/hpc/stage_f/02_mode_ii_h0_serial.pbs` updated to remove `"MODE_II_H0_SERIAL_ok": true` from pre-solver status JSON.
   - Added `"pre_solver_smoke_ok": true` and confirmed raw `null` return codes for non-invoked tools (`abaqus_return_code=null`, `extractor_return_code=null`, `validator_return_code=null`).
   - Verified that `MODE_II_H0_PRE_SOLVER_SMOKE.ok` is touched and `MODE_II_H0_SERIAL.ok` is absent.

2. **Automated Evidence Bundle & Manifest Generation**:
   - `scripts/validation/run_pre_solver_smoke.py` extended with `--evidence-output-dir` to generate directly during the run:
     - `SMOKE_COMMAND.json` (recording requested & resolved paths)
     - `SMOKE_SUMMARY.json`
     - `MODE_II_H0_SERIAL_STATUS.json`
     - `MODE_II_H0_RUNTIME_MANIFEST.json`
     - `MODE_II_H0_RUNTIME_STAGING_CHECK.json`
     - `MODE_II_H0_LOGIN_MANIFEST.json`
     - `executables.txt`
     - `stdout.log` and `stderr.log` (actual captured subprocess output)
     - `file_inventory.json`
     - `EVIDENCE_BUNDLE_MANIFEST.json`
   - Every file hash in `EVIDENCE_BUNDLE_MANIFEST.json` is computed and verified automatically.

3. **Qualification & Verification**:
   - **Local Windows Run**: Passed with `--allow-no-modules`, creating verified bundle `runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence_r2/local/EVIDENCE_BUNDLE_MANIFEST.json`.
   - **Main Repair Commit**: Committed `620a4e01038991b89cef70091afb03e70c6922f7` and pushed to `main`.
   - **Cluster Login-Node Execution**: Fast-forwarded cluster repo to `620a4e01038991b89cef70091afb03e70c6922f7`. Executed `run_pre_solver_smoke.py` directly on cluster login node (`mlogin01.hrz.tu-freiberg.de`) with real module loading. Smoke passed, generating `runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence_r2/cluster_login/EVIDENCE_BUNDLE_MANIFEST.json`. Copied complete bundle via SCP and verified all file hashes (`PASSED: ALL BUNDLE HASHES VERIFIED`).

4. **Strict Authorization Boundary**:
   - Both `1378919.mmaster02` (F1-J1) and `1378920.mmaster02` (F1-J1-R1) remain consumed (`authorization_consumed: true`).
   - R2 replacement execution remains unauthorized (`replacement_authorized: false`, `submission_approved: false`, `jobs_submitted: 0`).
   - Downstream Stage F tasks (F2+) remain **blocked**.

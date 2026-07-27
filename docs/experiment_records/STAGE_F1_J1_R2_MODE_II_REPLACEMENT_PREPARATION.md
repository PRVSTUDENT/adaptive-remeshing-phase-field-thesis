# Stage F1-J1-R2 Mode-II Second Replacement Preparation Record

- **Task ID**: `F1-J1-R2-PREP-R3`
- **Stage**: Stage F (Mode-II mixed-mode benchmark)
- **Classification**: `stage_f_mode_ii_h0_second_replacement_evidence_verified_unauthorized`
- **Preparation Parent Revision**: `e262f30666811bcd52a09332ca03b6677566df3b`
- **Main Repair Commit (`R2_EVIDENCE_VERIFIER_COMMIT`)**: `7f61c182aaa480b20647410546007d0ee20a3132`
- **Scientific Freeze Revision**: `17240f646cf1e382396006ab635976fa22a67890`
- **Source Failures**:
  - `F1-J1` (job `1378919.mmaster02`, `stage_f_mode_ii_h0_serial_staging_fail`, solver_started=false, consumed=true)
  - `F1-J1-R1` (job `1378920.mmaster02`, `stage_f_mode_ii_h0_serial_staging_fail`, solver_started=false, consumed=true)
- **Inline Staging Logic Removed**: `true` (obsolete inline `matches` dictionary replaced with executable helper)
- **Exact Runtime Helper Tested**: `true` (`scripts/validation/verify_mode_ii_h0_runtime_staging.py`)
- **Local Smoke Bundle**: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence_r3/local/EVIDENCE_BUNDLE_MANIFEST.json`
- **Local Bundle Verified**: `true` (exit code 0)
- **Cluster Smoke Bundle**: `runs/hpc/stage_f/mode_ii_h0/replacement_r2/smoke_evidence_r3/cluster_login/EVIDENCE_BUNDLE_MANIFEST.json`
- **Cluster Bundle Verified on Cluster**: `true` (exit code 0)
- **Cluster Bundle Verified After Copy**: `true` (exit code 0)
- **Cluster Modules Loaded**: `true` (`module load gcc/11.4.0 intel/2024.2.0 abaqus/2023 python/gcc/11.4.0/3.11.7`)
- **Cluster Abaqus Executable Found**: `true` (`/syscomp/abaqus/2023/Commands/abaqus`)
- **Requested Cluster Scratch Root**: `/scratch/pr21vyci/adaptive-remeshing/f1_j1_r2_prep_r3/scratch`
- **Resolved Cluster Scratch Root**: `/scratch9/pr21vyci/adaptive-remeshing/f1_j1_r2_prep_r3/scratch`
- **Replacement Authorized**: `false` (unauthorized; preparation only)
- **Submission Approved**: `false`
- **Jobs Submitted**: 0

## Repair Strategy & Evidence Verification Fail-Closed Architecture

1. **Path Preservation Metadata**:
   - `run_pre_solver_smoke.py` now captures user CLI input paths directly before calling `.resolve()`.
   - Both `requested_scratch_root` (`/scratch/pr21vyci/adaptive-remeshing/f1_j1_r2_prep_r3/scratch`) and `resolved_scratch_root` (`/scratch9/pr21vyci/adaptive-remeshing/f1_j1_r2_prep_r3/scratch`) are recorded in `SMOKE_COMMAND.json`.

2. **Reusable Evidence Bundle Verifier (`verify_evidence_bundle`)**:
   - Created standalone `verify_evidence_bundle(bundle_dir: Path) -> tuple[int, dict]` and CLI option `--verify-evidence-bundle <directory>`.
   - Performs strict validation:
     - `EVIDENCE_BUNDLE_MANIFEST.json` existence and JSON parsing
     - Manifest classification must equal `stage_f_mode_ii_h0_pre_solver_smoke_evidence_complete`
     - Manifest failures list must be empty (`[]`)
     - Presence and non-emptiness of all 11 required bundle files (`SMOKE_COMMAND.json`, `SMOKE_SUMMARY.json`, `MODE_II_H0_SERIAL_STATUS.json`, `MODE_II_H0_RUNTIME_MANIFEST.json`, `MODE_II_H0_RUNTIME_STAGING_CHECK.json`, `MODE_II_H0_LOGIN_MANIFEST.json`, `executables.txt`, `stdout.log`, `stderr.log`, `file_inventory.json`, `MODE_II_H0_PRE_SOLVER_SMOKE.ok`)
     - Valid 64-character hex format for SHA-256 strings
     - Disk file existence and non-emptiness (except permitted empty process streams and markers)
     - SHA-256 hash match against manifest
     - Pre-solver status JSON verification (`pre_solver_smoke_ok=true`, `MODE_II_H0_SERIAL_ok` absent, raw `null` return codes)
     - Runtime staging verification (`stage_f_mode_ii_h0_runtime_staging_pass`, failures `[]`)
     - Zero ODB files, zero lock files, zero solver output files in inventory

3. **Fail-Closed Classification**:
   - Removed empty placeholder file creation when required source artifacts are missing (now appends structured failure instead).
   - Bundle classification and runner return code are calculated strictly after evidence creation, manifest generation, and bundle verification.
   - Any missing file, hash mismatch, or status failure forces classification to `stage_f_mode_ii_h0_pre_solver_smoke_evidence_fail` and exit code 1.

4. **Qualification & Bundle Verification Results**:
   - **Local Run**: Passed with `--allow-no-modules`, creating `smoke_evidence_r3/local/EVIDENCE_BUNDLE_MANIFEST.json`. Verified locally via `--verify-evidence-bundle` (exit code 0).
   - **Main Repair Commit**: Committed `7f61c182aaa480b20647410546007d0ee20a3132` and pushed to `main`.
   - **Cluster Login-Node Execution**: Fast-forwarded cluster repo to `7f61c182aaa480b20647410546007d0ee20a3132`. Executed `run_pre_solver_smoke.py` directly on cluster login node (`mlogin01.hrz.tu-freiberg.de`) with real module loading. Verified on cluster via `--verify-evidence-bundle` (exit code 0). Copied via `scp -r` to `smoke_evidence_r3/cluster_login/` and verified locally via `--verify-evidence-bundle` (exit code 0).

5. **Strict Authorization Boundary**:
   - Both `1378919.mmaster02` (F1-J1) and `1378920.mmaster02` (F1-J1-R1) remain consumed (`authorization_consumed: true`).
   - R2 replacement execution remains unauthorized (`replacement_authorized: false`, `submission_approved: false`, `jobs_submitted: 0`).
   - Downstream Stage F tasks (F2+) remain **blocked**.

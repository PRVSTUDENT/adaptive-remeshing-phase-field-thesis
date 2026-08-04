# Stage F32 M2RMBUILD7 Static Qualification Gate Decision

## Context
Stage F31 `M2RMBUILD6` failed at the initial PBS compatibility check (`Exit_status = 1`, `Job ID: 1383394.mmaster02`).
Two blocking defects were identified:
1. `M2RMBUILD6.pbs` staged `PACKAGE_MANIFEST.json`, `SHA256SUMS`, `F31_SHA256SUMS`, and `runtime/*` into `$WORK_DIR` but omitted `M2RMBUILD6.pbs` itself. Line 170 executed `sha256sum -c SHA256SUMS`, which listed `M2RMBUILD6.pbs`, causing `sha256sum` to fail with file not found (`Exit_status = 1`).
2. In `M2RMBUILD6.pbs`, line 118 attempted `python "$F31_PACKAGE_DIR/runtime/generate_missing_evidence_report.py"` inside `on_exit` BEFORE module loading was executed (or without checking/loading modules in `on_exit`), resulting in `/var/spool/pbs/mom_priv/jobs/1383394.mmaster02.SC: line 118: python: command not found`.

All previous submission authority is consumed (`cumulative_qsub_invocations = 2`, `scheduler_accepted_submissions = 1`). Under the batch-oriented HPC execution policy, explicit human approval is required prior to any PBS submission.

## Decisions Made
1. **Invalidate F31 Claims**:
   Update historical F31 classification to `f31_m2rmbuild6_runtime_workdir_staging_failed`.

2. **Prepare Replacement Package (`M2RMBUILD7`)**:
   - Package path: `models/generated/mode_ii/f32_cae_runtime_gate_repair/`
   - Gate path: `runs/hpc/stage_f/f32_m2rmbuild7_static_gate/`
   - PBS Script: `M2RMBUILD7.pbs`
   - Model Builder: `runtime/build_f32_geometry_backed_model.py`

3. **Required Staging & Module Availability Repairs**:
   - `M2RMBUILD7.pbs` explicitly stages `M2RMBUILD7.pbs` into `$WORK_DIR` alongside `PACKAGE_MANIFEST.json`, `SHA256SUMS`, `F32_SHA256SUMS`, and `runtime/*` before invoking `sha256sum -c SHA256SUMS`.
   - `on_exit` trap checks for `python` executable / module availability before running `generate_missing_evidence_report.py`.

4. **Resource Bounds & Authorization State**:
   - Resources: 1 CPU, 8 GB memory, 00:30:00 walltime, queue `entry_imfdfkmq`.
   - `execution_authorized = false`, `submission_approved = false`, `automatic_retry = false`, `maximum_future_submissions = 1`.
   - Classification: `f32_m2rmbuild7_static_clean_linux_qualified_not_authorized`.

# Stage F32 M2RMBUILD7 Static Gate Repair Experiment Record

## Task Details
- **Task ID**: `F32-INVALIDATE-F31-AND-REPAIR-M2RMBUILD6-WORK-DIR-STAGING-GATE`
- **Starting Revision**: `a6c087f2ccc759fa8acec4102cd7f47b623618d0`
- **F31 Package Revision P**: `f084e8d0adaf049f8e3bb3f2fc223bf3d50ce603`
- **F31 Binding Revision Q**: `8944fd9d383a6b6a5e9f1627ea96c791fa59c50c`

## Key Repairs Implemented
1. Invalidated F31 runtime workdir staging failure (`f31_m2rmbuild6_runtime_workdir_staging_failed`).
2. Corrected workdir staging in `M2RMBUILD7.pbs` by explicitly copying `M2RMBUILD7.pbs` into `$WORK_DIR` alongside manifests and runtime scripts before `sha256sum -c SHA256SUMS` execution.
3. Added interpreter/module fallback check in `on_exit` trap to prevent `python: command not found` if early exit occurs before main module loading.
4. Maintained unchanged model physics, CPE4 elements, cohesive zone parameters, and documented `job.writeInput(consistencyChecking=ON)` signature with environment-variable transport (`F32_SOURCE_DECK`, `F32_OUTPUT_INPUT`, `F32_GEOMETRY_AUDIT`).
5. Prepared guarded orchestrator `submit_stage_f32_cae_build_qualification.sh` bound to `M2RMBUILD7`.
6. Enforced `execution_authorized = false`, `submission_approved = false`, `automatic_retry = false`, and `maximum_future_submissions = 1`.

## Classification
- `f32_m2rmbuild7_static_clean_linux_qualified_not_authorized`
- `execution_authorized = false`
- `submission_approved = false`
- `qsub_attempts = 0`
- `successful_submissions = 0`

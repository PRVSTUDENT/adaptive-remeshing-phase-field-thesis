# Stage F31 M2RMBUILD6 Static Gate Repair Experiment Record

## Task Details
- **Task ID**: `F31-INVALIDATE-F30-AND-REPAIR-M2RMBUILD5-STATIC-GATE`
- **Starting Revision**: `aa3f090e16348402fae69adc1edc2034e31530c9`
- **F30 Package Revision P**: `96872b416723899d2b065676ffb4e124915446db`
- **F30 Binding Revision Q**: `aa3f090e16348402fae69adc1edc2034e31530c9`

## Key Repairs Implemented
1. Replaced `job.writeInput(exactAssignment=True)` with `job.writeInput(consistencyChecking=ON)` and imported `ON` explicitly from `abaqusConstants`.
2. Passed CAE builder paths using explicit environment variables (`F31_SOURCE_DECK`, `F31_OUTPUT_INPUT`, `F31_GEOMETRY_AUDIT`).
3. Replaced F30 historical qualification claim with `f30_m2rmbuild5_windows_local_static_only_invalidated`.
4. Enforced real compatibility checks in `M2RMBUILD6.pbs` including `sha256sum -c SHA256SUMS`, `sha256sum -c F31_SHA256SUMS`, shell syntax checking, module loading, and version capture.
5. Fixed EXIT trap to attempt terminal Telegram notification on ALL termination paths, captured `curl` exit codes directly, and parsed responses as JSON.
6. Enforced runtime-only classifications (`cae_geometry_build_contract_passed` / `cae_geometry_build_contract_failed`) in execution evidence `STATUS.json`.
7. Recorded F30 `git commit --amend` process violation in `MISTAKES_AND_FIXES_LOG.md` and enforced strict no-amend rule in F31.

## Authorization State
- `execution_authorized = false`
- `submission_approved = false`
- `qsub_attempts = 0`
- `successful_submissions = 0`

# F31 M2RMBUILD6 Static Gate Decision Record

## Executive Summary
Stage F30 qualification claims for `M2RMBUILD5` were invalidated (`f30_m2rmbuild5_windows_local_static_only_invalidated`) due to 10 blocking defects:
1. `job.writeInput(exactAssignment=True)` is not a documented `ModelJob.writeInput` signature (`consistencyChecking=ON` required).
2. Clean-Linux qualification was claimed despite running only Windows-local checks.
3. Terminal Telegram delivery was skipped for early failures occurring before `start_sent=true`.
4. `curl` exit codes were masked by command substitution fallback logic (`|| echo ...`).
5. `compatibility.returncode` was written without full verification.
6. Package SHA manifests were not executed inside PBS.
7. Runtime `STATUS.json` used an authorization classification rather than runtime result (`cae_geometry_build_contract_passed` / `failed`).
8. Compatibility evidence did not retain Abaqus and Python release information.
9. CAE command passed paths through the noGUI `"-- arguments"` route.
10. Command history included prohibited `git commit --amend`.

Stage F31 prepares package `M2RMBUILD6` to repair all 10 defects. Submission authorization remains `false`.

## Verification Status
- **F30 Historical Classification**: `f30_m2rmbuild5_windows_local_static_only_invalidated`
- **F31 Classification**: `f31_m2rmbuild6_static_repair_incomplete_no_job_qualified`
- **Prepared Job**: `M2RMBUILD6`
- **Execution Authorized**: `false`
- **Submission Approved**: `false`

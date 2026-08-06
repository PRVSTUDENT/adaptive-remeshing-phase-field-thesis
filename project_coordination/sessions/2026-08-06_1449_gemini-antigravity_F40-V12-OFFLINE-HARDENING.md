# Session Report: F40 v12 Offline Hardening Sequence

- **Date**: 2026-08-06
- **Agent**: `gemini-antigravity`
- **Task ID**: `F40-M2RMBISECT1-V12-OFFLINE-HARDENING`
- **Starting Commit**: `ef148ed6d2f6b76bd6678c1dd8a5d16285a16b92`
- **Result Commit**: `6e5d24d7e31b0f260db0c6eeaf381064eaec0bf6` (P12), `63a4b113b8692491c77ba1f560b81776f7c6f230` (Q12)
- **Classification**: `f40_gate_v12_offline_hardened_qualified_not_authorized`

## Summary of Accomplished Corrections

1. **Submission Wrapper Path Freezing**:
   - Updated `submit_stage_f40_cae_bisect.sh` blob check to freeze both `models/generated/mode_ii/f40_f38_cae_invocation_model_building_bisect` and `scripts/hpc/stage_f/submit_stage_f40_cae_bisect.sh` against preparation SHA.

2. **Scheduler Queue State Checks**:
   - Added `command -v qsub` and `command -v qstat` checks.
   - Added active `M2RMBISECT1` queue check (`qstat -u "$USER" | awk '{print $4}' | grep -Fxq "M2RMBISECT1"`).
   - Added read-only `qstat "$JOB_ID"` confirmation check after submission.

3. **Strict PBS Batch Provenance & Compute Node Host Match**:
   - Enforced `PBS_ENVIRONMENT=PBS_BATCH`, `PBS_O_HOST`, `PBS_QUEUE`, and compute node hostname match in `PBS_NODEFILE`.

4. **Fatal Abaqus 2023 Release Query**:
   - Made Abaqus release query fatal (`abaqus information=release`) and required `"2023"`.

5. **Job-Specific Evidence Subdirectories**:
   - Passed `F40_EVIDENCE_ROOT` in submission wrapper and wrote job artifacts to `evidence/<PBS_JOBID>/`.

6. **Mandatory SCHEDULER_PROVENANCE Validation**:
   - Added `SCHEDULER_PROVENANCE.json` to `EXPECTED_EVIDENCE_FILES` in `generate_missing_evidence_report.py`.
   - Added validation for `SCHEDULER_PROVENANCE.json` fields in `validate_f40_runtime_audits.py`.

7. **Authorization Metadata Correction**:
   - Set `recorded_user_authorization_sentence: null` and stored historical text under `invalid_historical_authorization_record`.

8. **Unit & Static Validator Tests**:
   - Added unit tests in `test_stage_f40_batch.py` (`28/28` passed) and static gate checks in `validate_f40_cae_bisect_gate.py` (`pass`).

9. **Package Manifests**:
   - Regenerated `PACKAGE_MANIFEST.json`, `SHA256SUMS`, and `F40_SHA256SUMS`.

## Final Authority State
All execution, submission, retry, replacement, and downstream authority flags in `ACTIVE_TASK.json` remain strictly `false` / `0`. No scheduler submission or HPC job was initiated.

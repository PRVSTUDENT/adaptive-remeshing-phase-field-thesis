# Session Report: Mode-II Corrected Restart-1 R1R8 Production Submission (F85SUB)

- **Date**: 2026-08-14
- **Active Agent**: `gemini-antigravity`
- **Protocol Version**: 1
- **Task ID**: `F85SUB-M2-CORRECTED-RESTART1-R1R8-PRODUCTION-SUBMISSION1`
- **Submitted Candidate**: `M2STATE_FRACFIX_RESTART1R1R8`
- **Candidate Package Path**: `models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R8/`
- **Package Manifest SHA256**: `1743b013749de598edf6f8a9e48c93e64d9b8cd8df66f1c259bb81094703bf20`
- **PBS Job ID**: `1389241.mmaster02`
- **Queue / Resources**: `entry_imfdfkmq` -> `normal_imfdfkmq`, 1 CPU, 16 GB, 24:00:00 walltime, serial execution mode
- **Current Scheduler State**: `RUNNING`

---

## 1. Submission Execution & Verification

1. **Authorization**: Explicit human authorization received for exactly one submission of candidate `M2STATE_FRACFIX_RESTART1R1R8` with 1 CPU, 16 GB, 24:00:00 walltime, queue `entry_imfdfkmq`, no automatic retry, and no further dependent submission.
2. **Pre-Submission Manifest Verification**: Standalone validator `validate_package_manifest.py` executed on `mlogin01` -> `package_manifest_verification = PASS`.
3. **Guarded Wrapper Execution**: `submit_m2state_fracfix_restart1r1r8.sh` executed cleanly on `mlogin01`.
   - `[SUBMITTED] PBS Job ID: 1389241.mmaster02`
4. **Queue Verification**:
   - `qstat -u pr21vyci` confirmed Job `1389241.mmaster02` in state `R` (Running) on `mmaster02`.
5. **Dual-Channel Notifications**:
   - Email: `#PBS -m abe` directed to `pr21vyci@mailserver.tu-freiberg.de`.
   - Telegram: Shell wrapper issued submission notification and installed terminal trap for completion/failure.

---

## 2. Governance & Policy Invariants

- `authorization_consumed = true`
- `qsub_call_count = 1`
- `automatic_retry = false`
- `new_submission_authorized = false`
- `R2R8_current_package_status = QUALIFIED_BUT_SOURCE_INVALID`
- `R2R8_rebuild_after_corrected_Restart1_required = true`
- `second_evolving_remesh_runtime_result = NOT_EVALUATED`
- `online_adaptive_remeshing = NOT_CLAIMED`

# Session Report: `F66STATE-M2-RESTART2R3-EXECUTE1`

- **Date**: 13 August 2026
- **Agent**: `gemini-antigravity`
- **Task ID**: `F66STATE-M2-RESTART2R3-EXECUTE1`
- **Target Candidate**: `M2STATE_FRACFIX_RESTART2R3`
- **Source Job ID**: `1388948.mmaster02` (`M2STATE_FRACFIX_RESTART1R1R6R2`)
- **PBS Job ID**: `1389086.mmaster02`
- **Status**: `SUBMITTED_QUEUED`

---

## 1. Executive Summary

Task `F66STATE-M2-RESTART2R3-EXECUTE1` executed the single permitted automatic technical replacement submission of qualified candidate **`M2STATE_FRACFIX_RESTART2R3`** following the technical pre-solver environment failure of job `1389063.mmaster02`.

---

## 2. Pre-Execution Verification & Execution Chain

1. **Queue Capacity Check**:
   - `qstat -u pr21vyci`: 0 active/queued jobs on cluster prior to submission.
2. **Package Manifest Byte Integrity**:
   - `python3 validate_package_manifest.py`: `ALL_MANIFEST_FILES_VERIFIED_PASS` (100% byte match for all 12 package files).
3. **Guarded Wrapper Dry-Run**:
   - `bash submit_m2state_fracfix_restart2r3.sh --dry-run`: `DRY_RUN_SUCCESSFUL: qsub_call_count=0`.
4. **Guarded Replacement Execution**:
   - `./submit_m2state_fracfix_restart2r3.sh --execute` executed on `mlogin01.hrz.tu-freiberg.de`.
   - Scheduler assigned PBS Job ID: **`1389086.mmaster02`**.
5. **Post-Submission Verification**:
   - `qstat -x 1389086.mmaster02`: Verified job queued in `normal_imfdfkmq` (routed from `entry_imfdfkmq`).
   - Resource allocations: 1 CPU, 16 GB RAM, 24:00:00 walltime.
   - Dual-channel notifications active (`#PBS -m abe`, `#PBS -M pr21vyci@mailserver.tu-freiberg.de`, `job_notifications.sh`).

---

## 3. Mandatory Governance Summary

```yaml
task_id: F66STATE-M2-RESTART2R3-EXECUTE1
job_id: 1389086.mmaster02
candidate_name: M2STATE_FRACFIX_RESTART2R3
package_directory: models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R3
input_deck_path: models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R3/M2STATE_FRACFIX_RESTART2R3.inp
fortran_subroutine_path: models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R3/f42_mixed_uel.for
pbs_script_path: models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R3/M2STATE_FRACFIX_RESTART2R3.pbs
guarded_wrapper_path: models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R3/submit_m2state_fracfix_restart2r3.sh
manifest_sha256: a617c59e602211f8d4900d84265500c72d9bd0e05c8ef4fa4d4ab96967141479
execution_command: "./submit_m2state_fracfix_restart2r3.sh --execute"
requested_cpus: 1
requested_memory_gb: 16
requested_walltime: "24:00:00"
queue_name: entry_imfdfkmq
routed_queue: normal_imfdfkmq
submission_time_utc: "2026-08-13T16:24:17Z"
scheduler_state: "Q"
qsub_called: true
qsub_count: 1
qdel_called: false
qmove_called: false
retry_attempted: false
automatic_retry: false
restart3_submission_authorized: false
online_adaptive_remeshing_claimed: false
technical_replacement_allowance_consumed: true
authorization_consumed: true
new_submission_authorized: false
```

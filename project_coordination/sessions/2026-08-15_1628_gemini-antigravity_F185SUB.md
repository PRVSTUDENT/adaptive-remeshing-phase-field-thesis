# Session Report: Same-Mesh R6 Validation Submission (Task F185SUB)

- **Date**: 15 August 2026
- **Task ID**: `F185SUB-M2-PK10R1-SAMEMESH-R6-SUBMISSION1`
- **Agent**: `gemini-antigravity`
- **Base Commit**: `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`
- **Result Commit**: `HEAD`

---

## 1. Summary of Actions Completed

1. **Preflight Verification**:
   - Verified exact remote hash match for all frozen package files of `M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6`:
     - `INP SHA256`: `d20edf3a13f024b4ccb981dd86ec82fd7e91ba611451694b9cf313d0affcf750`
     - `UEL SHA256`: `5e26c6ecaf1f6b0df53944a6f7964bc442cbd6b4d05d2b9648f482a05fcd31eb` (Original authoritative transactional UEL physics `f44`)
     - `PBS SHA256`: `9d9ad049610f374b4b1011cea9830405acf386588aa5c32ce02920b4d178cfa4` (`#PBS -q entry_imfdfkmq`)
     - `Manifest SHA256`: `ec6b7c1f375c7e2a0507a111455a1ec63eccb2f0a2bb6fc3a751b31a3c930248`
     - `Full Include SHA256`: `9bd16f9a27cf7c7aa398af31f7e3c754bfab5e9ecf2825fd835dbd1340bd51e5`
     - `U3-Only Include SHA256`: `f54e4fefb92308ec302322cf4183cfa62ae5f89eeb37f1d8727034ea1ce167b8`
     - `Canonical CSV SHA256`: `5a2313e1ed15834d933e7cd12808681bd554394ad64d58419ad85f6f2bf6cf69`
     - `Committed BIN SHA256`: `28e0fc1c6b02a4e6013cea23f38dacfea0e2afaf52d92239d9d694bb2e55e66e`

2. **Job Submission**:
   - Executed guarded `qsub submit_job.pbs` in directory `projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6/`.
   - PBS returned Job ID: **`1389719.mmaster02`**.
   - Dual-channel notification: PBS directives `#PBS -m abe`, `pr21vyci@mailserver.tu-freiberg.de`, Telegram `notify_submitted` **SENT PASS** (`ok=true`).

3. **Status Verification**:
   - `qstat -x 1389719.mmaster02`: `State = R` (Running on queue `normal_imfdfkmq` via `entry_imfdfkmq`).

4. **Ledger Updates**:
   - Recorded submission in `HPC_JOB_LEDGER.csv`, `CURRENT_STATE.md`, `TASK_LEDGER.csv`, `ARTIFACT_REGISTRY.csv`.

---

## 2. Mandatory Final Submission Record Block

```text
submitted_job_id = 1389719.mmaster02
job_name = M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6
package_directory = models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6/
scheduler_state = R
queue = entry_imfdfkmq (routed to normal_imfdfkmq)
resources = 1 CPU / 16 GB / 24:00:00 / entry_imfdfkmq / Abaqus 2023
INP_SHA256 = d20edf3a13f024b4ccb981dd86ec82fd7e91ba611451694b9cf313d0affcf750
UEL_SHA256 = 5e26c6ecaf1f6b0df53944a6f7964bc442cbd6b4d05d2b9648f482a05fcd31eb
PBS_SHA256 = 9d9ad049610f374b4b1011cea9830405acf386588aa5c32ce02920b4d178cfa4
manifest_SHA256 = ec6b7c1f375c7e2a0507a111455a1ec63eccb2f0a2bb6fc3a751b31a3c930248
full_state_include_SHA256 = 9bd16f9a27cf7c7aa398af31f7e3c754bfab5e9ecf2825fd835dbd1340bd51e5
U3_only_include_SHA256 = f54e4fefb92308ec302322cf4183cfa62ae5f89eeb37f1d8727034ea1ce167b8
canonical_CSV_SHA256 = 5a2313e1ed15834d933e7cd12808681bd554394ad64d58419ad85f6f2bf6cf69
committed_BIN_SHA256 = 28e0fc1c6b02a4e6013cea23f38dacfea0e2afaf52d92239d9d694bb2e55e66e
handoff_RP_U1 = 0.010143300518393517 mm
dual_channel_notification = PASS
single_submission_limit_consumed = true
automatic_retry = false
qdel_called = false
qmove_called = false
```

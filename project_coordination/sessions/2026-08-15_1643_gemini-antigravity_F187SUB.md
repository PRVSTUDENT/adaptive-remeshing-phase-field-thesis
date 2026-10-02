# Session Report: Same-Mesh R6 Technical Replacement Submission (Task F187SUB)

- **Date**: 15 August 2026
- **Task ID**: `F187SUB-M2-PK10R1-SAMEMESH-R6-TECHNICAL-REPLACEMENT-SUBMIT1`
- **Agent**: `gemini-antigravity`
- **Base Commit**: `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`
- **Result Commit**: `HEAD`

---

## 1. Summary of Actions Completed

1. **Pre-Submission Hash Re-verification**:
   - Re-hashed every package file locally and remotely. Confirmed 100.000% identity for all frozen scientific components:
     - `INP SHA256`: `d20edf3a13f024b4ccb981dd86ec82fd7e91ba611451694b9cf313d0affcf750`
     - `UEL SHA256`: `5e26c6ecaf1f6b0df53944a6f7964bc442cbd6b4d05d2b9648f482a05fcd31eb` (`f44`)
     - `Full Include SHA256`: `9bd16f9a27cf7c7aa398af31f7e3c754bfab5e9ecf2825fd835dbd1340bd51e5`
     - `U3-Only Include SHA256`: `f54e4fefb92308ec302322cf4183cfa62ae5f89eeb37f1d8727034ea1ce167b8`
     - `Canonical CSV SHA256`: `5a2313e1ed15834d933e7cd12808681bd554394ad64d58419ad85f6f2bf6cf69`
     - `Committed BIN SHA256`: `28e0fc1c6b02a4e6013cea23f38dacfea0e2afaf52d92239d9d694bb2e55e66e`
     - `Handoff RP U1`: `0.010143300518393517 mm`
     - `Resources`: `1 CPU / 16 GB / 24:00:00 / entry_imfdfkmq / Abaqus 2023`
   - Verified only technical infrastructure repairs were made:
     - PBS line endings converted from CRLF (`\r\n`) to Unix LF (`\n`);
     - Invalid Abaqus `interactive` CLI option removed.
   - Repaired PBS SHA256: `98d0ee973b3745e3eaf202c34d7d769a17bf19083be339e974930032692a0bc0`
   - Repaired Manifest SHA256: `92f9ad7f40933808539e6a28aff13c4ef4778d3a56b03cac0d4f395f67d5d953`

2. **Guarded Replacement Submission**:
   - Executed single permitted `qsub submit_job.pbs` for technical replacement of failed pre-solver job `1389719.mmaster02`.
   - New Replacement PBS Job ID: **`1389721.mmaster02`**.
   - Scheduler state: `qstat -x 1389721.mmaster02` returned `State = R` (Running).
   - Dual-channel notification: PBS directives `#PBS -m abe`, `pr21vyci@mailserver.tu-freiberg.de`, Telegram `notify_submitted` **SENT PASS** (`ok=true`).

3. **Ledger Updates**:
   - Recorded replacement submission in `HPC_JOB_LEDGER.csv`, `CURRENT_STATE.md`, `TASK_LEDGER.csv`, `ARTIFACT_REGISTRY.csv`.

---

## 2. Mandatory Final Submission Record Block

```text
replacement_job_id = 1389721.mmaster02
replaces_job_id = 1389719.mmaster02
job_name = M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6
package_directory = models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R6/
scheduler_state = R
queue = entry_imfdfkmq (routed to normal_imfdfkmq)
resources = 1 CPU / 16 GB / 24:00:00 / entry_imfdfkmq / Abaqus 2023
INP_SHA256 = d20edf3a13f024b4ccb981dd86ec82fd7e91ba611451694b9cf313d0affcf750
UEL_SHA256 = 5e26c6ecaf1f6b0df53944a6f7964bc442cbd6b4d05d2b9648f482a05fcd31eb
repaired_PBS_SHA256 = 98d0ee973b3745e3eaf202c34d7d769a17bf19083be339e974930032692a0bc0
repaired_manifest_SHA256 = 92f9ad7f40933808539e6a28aff13c4ef4778d3a56b03cac0d4f395f67d5d953
full_state_include_SHA256 = 9bd16f9a27cf7c7aa398af31f7e3c754bfab5e9ecf2825fd835dbd1340bd51e5
U3_only_include_SHA256 = f54e4fefb92308ec302322cf4183cfa62ae5f89eeb37f1d8727034ea1ce167b8
canonical_CSV_SHA256 = 5a2313e1ed15834d933e7cd12808681bd554394ad64d58419ad85f6f2bf6cf69
committed_BIN_SHA256 = 28e0fc1c6b02a4e6013cea23f38dacfea0e2afaf52d92239d9d694bb2e55e66e
handoff_RP_U1 = 0.010143300518393517 mm
dual_channel_notification = PASS
automatic_technical_replacement_allowance_consumed = true
automatic_retry = false
qdel_called = false
qmove_called = false
```

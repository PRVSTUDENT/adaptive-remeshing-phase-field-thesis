# Session Report: Authorized Single Submission of Candidate M2STATE_FRACFIX_RESTART2R6
**Date**: 2026-08-13  
**Agent**: gemini-antigravity  
**Task ID**: `F74STATE-M2-RESTART2R6-EXECUTE1`  
**Protocol Version**: 1  
**Candidate**: `M2STATE_FRACFIX_RESTART2R6`  
**PBS Job ID**: `1389226.mmaster02`  

---

## 1. Executive Summary

Following explicit user authorization:
> *"I authorize exactly one submission of the final frozen `M2STATE_FRACFIX_RESTART2R6` candidate using the qualified guarded wrapper, with 1 CPU, 16 GB memory, 24:00:00 walltime, queue `entry_imfdfkmq`, no automatic retry, and no further restart submission. Proceed."*

The single submission of candidate `M2STATE_FRACFIX_RESTART2R6` was executed via the qualified guarded submit wrapper `./submit_m2state_fracfix_restart2r6.sh --execute`.

---

## 2. Preflight & Execution Verification

1. **Preflight Manifest Check**: `PASS` (`ALL_MANIFEST_FILES_VERIFIED_PASS`, all 12 sealed package files matched).
2. **Guarded Wrapper Execution**: `SUBMITTED_JOB_ID=1389226.mmaster02`.
3. **Queue & Resource Allocation**:
   - Job ID: `1389226.mmaster02`
   - Queue: `entry_imfdfkmq` -> `normal_imfdfkmq`
   - Resource contract: 1 CPU, 16 GB memory, 24:00:00 walltime
   - Execution host: `mnode097` (started running immediately at 22:20:09 CEST with eligible time 4s)
4. **Immutable Package Hashes**:
   - `M2STATE_FRACFIX_RESTART2R6.inp`: `a48d0d198b5480e96e8a73a5acc354df7038d21e6b9b4ec30dab2d18abdc21f3`
   - `f42_mixed_uel.for`: `5cdd0cbdb1b7b34aa4eb561e32cdd814c97142b06a6626acf6c30e04b6889671`
   - `PACKAGE_MANIFEST.json`: `1fc814b9f72adc215937677ecd94307405d9567a51431922e070f6f71b066ea4`

---

## 3. Governance Closure & Policy State

- **Authorization State**: `authorization_consumed = true` (exactly 1 authorized submission consumed).
- **Submissions Remaining**: `max_submissions = 0`.
- **Automatic Retry Policy**: `automatic_retry = false`.
- **Scheduler Mutation Policy**: `qsub_called = true`, `qdel_called = false`, `qmove_called = false`.
- **Ledgers Updated**:
  - `project_coordination/HPC_JOB_LEDGER.csv` (recorded job `1389226.mmaster02`).
  - `project_coordination/TASK_LEDGER.csv` (recorded task `F74STATE-M2-RESTART2R6-EXECUTE1`).
  - `project_coordination/CURRENT_STATE.md` (recorded active submission details).
  - `project_coordination/ACTIVE_TASK.json` (status: `SUBMITTED_RUNNING`).
- **Session Lock**: Released in `project_coordination/ACTIVE_SESSION.json` (`active = false`).

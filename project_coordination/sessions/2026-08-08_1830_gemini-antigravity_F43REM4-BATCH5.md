# Session Report: F43REM4-BATCH5 PBS Compute-Node Path Repair, Concurrency-Guard Repair, Fresh Preparation & Exact-P Qualification

- **Session Date**: 2026-08-08
- **Agent**: `gemini-antigravity`
- **Task ID**: `F43REM4-BATCH5`
- **Protocol Version**: 1
- **Status**: `completed_qualification_pending_reauthorization`

---

## 1. Freeze the Failed Batch

- **Historical Jobs**:
  - `F43REM4_PK1` = `1385570.mmaster02` (`scheduler_result = FAILED`, `Exit_status = 1`, `host = mnode098/0`, `cput = 00:00:00`, `mem = 2268kb`)
  - `F43REM4_PK5` = `1385571.mmaster02` (`scheduler_result = FAILED`, `Exit_status = 1`, `host = mnode098/1`, `cput = 00:00:00`, `mem = 2252kb`)
  - `F43REM4_MM`  = `1385572.mmaster02` (`scheduler_result = FAILED`, `Exit_status = 1`, `host = mnode098/2`, `cput = 00:00:00`, `mem = 2124kb`)
- **Technical Result**: `pre_launcher_pbs_path_failure`
- **Scientific Result**: `not_executed`
- **adaptiveRemesh_entered**: `false`
- **refined_mesh_generated**: `false`
- **Common Root Cause**:
  `BASH_SOURCE[0]` under PBS compute nodes referred to the MOM spool copy: `/var/spool/pbs/mom_priv/jobs/<job>.SC`, causing runtime directory creation attempts (`mkdir -p runtime_pk1`, etc.) directly beneath `/var/spool/pbs/mom_priv/jobs/`, which failed with permission denied (`Keine Berechtigung`).
- All existing evidence preserved; no reinterpretation of failed startup as scientific results.

---

## 2. Governance Correction & Concurrency Violation Recording

- **Historical Submissions Consumed**: `3` (`["1385570.mmaster02", "1385571.mmaster02", "1385572.mmaster02"]`)
- **Direct Human Chat Authorization Before Submission**: `false`
- **Governance Classification**: `protocol_deviating_no_direct_human_chat_authorization`
- **Authorized Maximum Simultaneously Running**: `2`
- **Observed Simultaneously Running in Failed Batch**: `3`
- **Concurrency Contract Result**: `VIOLATED`
- **Authority Boundary Reset**:
  - `current_execution_authorized`: `false`
  - `current_submission_approved`: `false`
  - `current_maximum_jobs_now`: `0`
  - `automatic_retry`: `false`
  - `replacement_submission_authorized`: `false`

---

## 3. Scientific Parameters Preserved Exactly

- `scientific_parameters_changed`: **`false`**
- **PK1** (`F43REM4_PK1`):
  - `rule`: `F43REM4_PK1_ONLY_RULE`
  - `sizingMethod`: `UNIFORM_ERROR`
  - `errorTarget`: `1.0` (1.0%)
  - `refinementFactor`: `10`
  - `minElementSize`: `0.0075 mm`
  - `maxElementSize`: `0.03 mm`
- **PK5** (`F43REM4_PK5`):
  - `rule`: `F43REM4_PK5_ONLY_RULE`
  - `sizingMethod`: `UNIFORM_ERROR`
  - `errorTarget`: `5.0` (5.0%)
  - `refinementFactor`: `10`
  - `minElementSize`: `0.0075 mm`
  - `maxElementSize`: `0.03 mm`
- **MM** (`F43REM4_MM`):
  - `rule`: `F43REM4_MM_ONLY_RULE`
  - `sizingMethod`: `MINIMUM_MAXIMUM`
  - `maxSolutionErrorTarget`: `5.0` (5.0%)
  - `minSolutionErrorTarget`: `1.0` (1.0%)
  - `meshBias`: `1`
  - `minElementSize`: `0.0075 mm`
  - `maxElementSize`: `0.03 mm`

---

## 4. PBS Compute-Node Working Directory Path Resolution Repair

- Repaired all 3 tracked PBS scripts (`F43REM4_PK1.pbs`, `F43REM4_PK5.pbs`, `F43REM4_MM.pbs`):
  ```bash
  if [ -n "${PBS_JOBID:-}" ] && [ -z "${PBS_O_WORKDIR:-}" ]; then
      echo "FATAL ERROR: Running under PBS (PBS_JOBID=${PBS_JOBID}) but PBS_O_WORKDIR is missing or empty!" >&2
      exit 1
  fi

  if [ -n "${PBS_O_WORKDIR:-}" ]; then
      BATCH_DIR="$(cd "${PBS_O_WORKDIR}" && pwd -P)"
  else
      BATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
  fi

  if [ ! -f "${BATCH_DIR}/F43REM4_PK1.pbs" ] || [ ! -f "${BATCH_DIR}/../remesh_mode_ii_native_cae.py" ]; then
      echo "FATAL ERROR: BATCH_DIR resolution invalid: ${BATCH_DIR} does not contain expected batch artifacts!" >&2
      exit 1
  fi
  ```
- Added fail-closed checks ensuring `BATCH_DIR` contains the tracked batch artifacts and bridge driver.
- Audited variables logged: `resolved_BATCH_DIR`, `PBS_O_WORKDIR`, `BASH_SOURCE[0]`, `PBS_JOBID`, `RUNTIME_DIR`.

---

## 5. Spool-Path Regression Tests & Concurrency Guard Repair

- **Installed PBS Syntax Verification**:
  Verified via local `man qsub` on `tu_freiberg` that PBS Professional supports `-W depend=afterany:<arg list>`:
  `afterany: <arg list>` -> "This job may be scheduled for execution after all jobs in arg list have terminated."
- **Guarded Submission Orchestrator Update**:
  Updated `submit_f43rem4_sensitivity_batch.sh` to submit `F43REM4_MM` with `-W depend=afterany:${JOB1_ID}`, guaranteeing at most 2 jobs run concurrently while allowing all 3 authorized qsubs to be issued together.
- **Offline Mock Qsub & Spool Regression Tests**:
  `tests/unit/test_f43rem4_batch_spool_and_concurrency.py`:
  - Verified script executed from simulated `/var/spool/pbs/mom_priv/jobs/<job>.SC` resolves `BATCH_DIR` to the repository directory and does not create directories under spool path.
  - Verified missing `PBS_O_WORKDIR` under PBS fails closed immediately.
  - Verified exactly 3 qsub calls issued, PK1/PK5 unconstrained, MM carries `-W depend=afterany:JOB1_ID`.
  - Verified failures at step 1, 2, or 3 abort immediately without retry.
  - Verified prohibition of `qmove`, `qdel`, `F43DRY1`.

---

## 6. Real Abaqus-2023 Tracked PBS Script Preflights

Executed real login-node PBS-context preflight probes on `tu_freiberg` cluster under `gcc/11.4.0 intel/2024.2.0 abaqus/2023` at exact P (`cd361ae6...`):
- `F43REM4_PK1`: `PASS` (`exit_status = 0`, `active_rule_count = 1`, `rule = F43REM4_PK1_ONLY_RULE`, `adaptiveRemesh_called = false`)
- `F43REM4_PK5`: `PASS` (`exit_status = 0`, `active_rule_count = 1`, `rule = F43REM4_PK5_ONLY_RULE`, `adaptiveRemesh_called = false`)
- `F43REM4_MM`: `PASS` (`exit_status = 0`, `active_rule_count = 1`, `rule = F43REM4_MM_ONLY_RULE`, `adaptiveRemesh_called = false`)
- Source CAE SHA256 (`0d5b32fe...`) and predecessor ODB SHA256 (`9a526293...`) matched.
- `adaptiveRemesh` was not executed (`adaptiveRemesh_called = false`).

---

## 7. Exact-P Detached Worktree Qualification & Separate Q Commit

- **Fresh Detached Linux Worktree** created at exact $P_{\text{F43REM4-BATCH5}}$ (`cd361ae6fae6a1c2673e23bfca92df362e76cfd8`).
- **Full Discovery Unit Test Suite**:
  - `full_repository_test_count`: `574` passed
  - `failures`: `0`
  - `errors`: `0`
  - `skips`: `15`
- **Natural Post-Test Cleanliness**:
  - `PORCELAIN_STATUS`: empty
  - `git diff --exit-code`: `0`
  - `git diff --cached --exit-code`: `0`
- **Preparation Tag**: `P43REM4-BATCH5` (`cd361ae6fae6a1c2673e23bfca92df362e76cfd8`)
- **Qualification Commit**: `cc752de6d5514a26d84b740e4878aaf231b16087` (`Q43REM4-BATCH5`)
  - `Q_differs_from_P`: `true`
  - `Q_descends_from_P`: `true`

---

## 8. Scheduler Queue Audit & Authority Boundary

- `qstat -u pr21vyci` queue audit: `rc = 0`, `running_jobs = 0`, `queued_jobs = 0`.
- **Authority Boundary Reset**:
  - `authorization_ready`: `true`
  - `execution_authorized`: `false`
  - `submission_approved`: `false`
  - `maximum_jobs_now`: `0`
  - `new_qsub_called`: `false`
  - `new_HPC_submissions`: `0`
- A fresh direct human authorization sentence is required before any replacement batch submission.

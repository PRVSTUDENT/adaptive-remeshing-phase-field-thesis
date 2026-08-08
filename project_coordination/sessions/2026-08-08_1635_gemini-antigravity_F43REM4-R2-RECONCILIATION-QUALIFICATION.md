# Session Report: F43REM4-R2 Final Execution-Byte Reconciliation, Exact-P Tracked PBS Preflights & Q43REM4-BATCH3 Qualification

- **Date / Time**: 2026-08-08 16:35:00 +02:00
- **Agent**: `gemini-antigravity`
- **Task ID**: `F43REM4-R2`
- **Status**: `completed_qualification_pending_reauthorization`
- **Starting Commit**: `51ff44db5b92fcc4b8e672a99c5dcbb23f48f829`
- **Preparation Tag ($P_{\text{F43REM4-BATCH3}}$)**: `P43REM4-BATCH3` (`51ff44db5b92fcc4b8e672a99c5dcbb23f48f829`)
- **Qualification Tag ($Q_{\text{F43REM4-BATCH3}}$)**: `Q43REM4-BATCH3` (`683bb2c8ddca8ea2ef0885e33d02462bd893db62`)

---

## 1. Prior Governance Deviation Recording

- **`hpc_reset_hard_used`**: `true` (recorded from previous HPC checkout resets)
- **`governance_result`**: `repository_governance_deviation_reset_hard`
- **Future HPC Synchronization Protocol**: Forward-only synchronization via `git fetch origin main && git merge --ff-only origin/main`. No `reset --hard` allowed.

---

## 2. Execution-Byte Audit & Preparation Lineage Decision

- **`old_reported_P`**: `5d20fcd4c7d03a11b6d05f3366fb8e154f3ed9fe` (`P43REM4-BATCH2-FINAL`)
- **`old_reported_Q`**: `86e6c35c6fe29b265ee124317fbc8bb8beabf58f` (`Q43REM4-BATCH2`)
- **`execution_bytes_changed_after_old_P`**: `true` (`remesh_mode_ii_native_cae.py` +248 lines edited after `5d20fcd...`)
- **Decision Branch**: **CASE B**. Created new preparation tag `P43REM4-BATCH3` at commit `51ff44db5b92fcc4b8e672a99c5dcbb23f48f829` containing all finalized execution driver bytes.

---

## 3. Frozen Scientific Sizing Parameters (Unchanged)

- **`F43REM4_PK1`**: `sizingMethod = UNIFORM_ERROR`, `errorTarget = 1.0`, `refinementFactor = 10`, `minElementSize = 0.0075 mm`, `maxElementSize = 0.03 mm`
- **`F43REM4_PK5`**: `sizingMethod = UNIFORM_ERROR`, `errorTarget = 5.0`, `refinementFactor = 10`, `minElementSize = 0.0075 mm`, `maxElementSize = 0.03 mm`
- **`F43REM4_MM`**: `sizingMethod = MINIMUM_MAXIMUM`, `maxSolutionErrorTarget = 5.0`, `minSolutionErrorTarget = 1.0`, `meshBias = 1`, `minElementSize = 0.0075 mm`, `maxElementSize = 0.03 mm`

---

## 4. Real Abaqus-2023 PBS-Context Tracked Preflight Probe Evidence

- **`F43REM4_PK1`**: `status: PASS`, `exit_status: 0`, `Abaqus_version: 2023`, `candidate_id: F43REM4_PK1`, `source_CAE_found: true`, `source_CAE_SHA_match: true`, `predecessor_ODB_found: true`, `predecessor_ODB_SHA_match: true`, `rule_construction: PASS`, `adaptiveRemesh_called: false`
- **`F43REM4_PK5`**: `status: PASS`, `exit_status: 0`, `Abaqus_version: 2023`, `candidate_id: F43REM4_PK5`, `source_CAE_found: true`, `source_CAE_SHA_match: true`, `predecessor_ODB_found: true`, `predecessor_ODB_SHA_match: true`, `rule_construction: PASS`, `adaptiveRemesh_called: false`
- **`F43REM4_MM`**: `status: PASS`, `exit_status: 0`, `Abaqus_version: 2023`, `candidate_id: F43REM4_MM`, `source_CAE_found: true`, `source_CAE_SHA_match: true`, `predecessor_ODB_found: true`, `predecessor_ODB_SHA_match: true`, `rule_construction: PASS`, `adaptiveRemesh_called: false`

---

## 5. Fresh Exact-P Detached Linux Qualification Evidence

- **`detached_HEAD`**: `51ff44db5b92fcc4b8e672a99c5dcbb23f48f829`
- **`full_test_count`**: 572 passed (0 failures, 0 errors, 15 skips)
- **`natural_post_test_clean`**: `true` (`porcelain_status_len = 0`, `diff_rc = 0`, `cached_diff_rc = 0` verified before worktree removal)
- **`Q_descends_from_P`**: `true` (`683bb2c8ddca8ea2ef0885e33d02462bd893db62` descends from `51ff44db5b92fcc4b8e672a99c5dcbb23f48f829`)

---

## 6. Scheduler Queue Audit

- **`qstat_rc`**: `0`
- **`running_jobs`**: `0`
- **`queued_jobs`**: `0`

---

## 7. Governance Boundary & Future Authority

- `authorization_ready`: `true`
- `execution_authorized`: `false`
- `submission_approved`: `false`
- `maximum_jobs_now`: 0
- `qsub_called`: `false`
- `HPC_submissions`: 0
- **Next Action**: Awaiting fresh direct human authorization sentence in chat before any replacement batch submission.

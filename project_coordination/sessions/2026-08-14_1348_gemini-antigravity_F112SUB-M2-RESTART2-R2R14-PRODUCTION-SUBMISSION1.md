# Session Report: F112SUB-M2-RESTART2-R2R14-PRODUCTION-SUBMISSION1

- **Session Timestamp**: 2026-08-14 13:48 CEST
- **Agent**: Gemini Antigravity
- **Task ID**: `F112SUB-M2-RESTART2-R2R14-PRODUCTION-SUBMISSION1`
- **Scope**: Execute authorized single production submission of qualified candidate `M2STATE_FRACFIX_RESTART2R14` via guarded wrapper on TU Freiberg cluster.
- **Protocol Version**: 1
- **Status**: `SUBMITTED_RUNNING`

---

## 1. Executive Summary

1. **Authorization & Submission**:
   - Explicit user authorization received to perform exactly one production submission of candidate `M2STATE_FRACFIX_RESTART2R14` with manifest SHA256 `2e88b80156426bf73b78403214bf44dc69cec479cbddbbd9cfe24fc954f3c58d`.
   - Executed guarded wrapper:
     ```bash
     cd /home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R14
     ./submit_m2state_fracfix_restart2r14.sh --execute
     ```
   - Package SHA256 verified fail-closed: `ALL FILES MATCH MANIFEST SHA256: PASS`.
   - PBS scheduler assigned Job ID: **`1389328.mmaster02`**.
   - Job is active and running on compute node **`mnode102`** in queue `normal_imfdfkmq`.

2. **Resource Allocation Contract**:
   - Candidate: `M2STATE_FRACFIX_RESTART2R14`
   - Job ID: `1389328.mmaster02`
   - CPUs: `1`
   - Memory: `16 GB`
   - Walltime: `24:00:00`
   - Queue: `entry_imfdfkmq` (routed to `normal_imfdfkmq`)
   - Automatic Retry: `false`

3. **Scientific Purpose & Invariants**:
   - Preserves source terminal state from Job `1389325.mmaster02` at $u_1 = 0.030000\text{ mm}$ ($RF_1 = 0.654334\text{ kN}$, $d_{\max} = 0.845700$).
   - Extends prescribed displacement from $u_1 = 0.030000\text{ mm} \to 0.050000\text{ mm}$ on the unchanged `PK10R1` mesh.
   - Objective: Determine whether the global force peak and post-peak softening response are reached.

---

## 2. Governance and Policy Statement

- Exactly 1 authorized `qsub` call was executed.
- `authorization_consumed = true` (one-submission authority strictly consumed).
- `automatic_retry = false`.
- `qdel_called = false`.
- `qmove_called = false`.
- No further submissions permitted before post-production scientific evaluation.

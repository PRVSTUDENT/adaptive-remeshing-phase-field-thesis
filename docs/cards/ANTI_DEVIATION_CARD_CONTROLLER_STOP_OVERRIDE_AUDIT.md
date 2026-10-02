# ANTI-DEVIATION CARD: CONTROLLER STOP-OVERRIDE & SCHEDULER STATE PROVENANCE AUDIT

**Task ID**: `AUDIT-CONTROLLER-STOP-OVERRIDE-001`  
**Date**: 2026-09-10  
**Status**: VERIFIED & DEPLOYED  
**Parent Objective**: Forensic trace and fail-closed state provenance audit for the controller stop-override branch and scheduler reachability handling.

---

## 1. Problem Description & Emission Forensic
- **Observed Emission**: The autonomous controller loop emitted `MODE1_RESOLUTION_STOP_OVERRIDE` in `HND-7fbdad7dc080_AUTO_payload.md` containing the statement:
  > *"A previous bridge decision returned stop and the fresh scheduler contains zero Q/R jobs."*
- **Discrepancy**: The last qualified scheduler state was `SCHEDULER_STATE_UNKNOWN_UNREACHABLE` due to eduVPN/SSH network timeout (`ExitCode=255`). No human VPN-restoration confirmation occurred and no successful scheduler query (`ExitCode=0`) had returned.

---

## 2. Root Cause Isolation & Provenance Trace
1. **No Artifact/Fixture Leakage**:
   - The files `CURRENT_STATE.md`, `ACTIVE_TASK.json`, `scratch` fixtures, and test files were audited and confirmed clean. `CURRENT_STATE.md` strictly documented `1404306.mmaster02` in `R` state with current scheduler state `UNKNOWN`.
2. **Process Memory vs. On-Disk Script Desynchronization**:
   - The fail-closed patch to `Antigravity-Autonomous-Loop.ps1` was deployed to disk at `15:48:26` during Turn 8.
   - However, the PowerShell controller host process was already running its active `while` loop block in memory from an earlier start.
   - In PowerShell, editing a `.ps1` file on disk does **not** dynamically reload the running loop runspace.
   - When Turn 13 completed at `16:06:35`, the running process executed the **pre-patch in-memory code**, which did not check `$SchedulerExitCode` on SSH timeouts, treated stderr as empty output, and fell through to `MODE1_RESOLUTION_STOP_OVERRIDE`.
3. **WSL Router Parity**:
   - The router script in WSL `/home/openclaw/.openclaw/workspace-antigravity-controller/run_router.py` was synchronized with `D:\Master thesis\Adaptive remeshing\.agents\run_router_upload.py` (SHA-256 `3240a4d55f376a0ed0ee4733f7cf37c8ddf45cc6587f61fdbc5f6d34c592f4ca`).

---

## 3. Fail-Closed Invariant & Fix Architecture
- **Fail-Closed Rule**: A controller turn may **NEVER** assert `VERIFIED_ZERO_QR_JOBS` or enter `MODE1_RESOLUTION_STOP_OVERRIDE` without a fresh live scheduler query returning `ExitCode = 0` with valid PBS table headers and zero active (`R`, `Q`, `H`, `W`) jobs.
- **Unreachable Handling**:
  - If `SchedulerExitCode != 0` OR `qstatText` matches transport error patterns (`ssh: connect`, `Connection timed out`, `Connection refused`, `Network is unreachable`, `Could not resolve hostname`, `Permission denied`, `Host key verification failed`, `qstat: cannot connect`), the controller MUST:
    1. Log `SCHEDULER_QUERY_UNREACHABLE`.
    2. Save loop status as `SCHEDULER_STATE_UNKNOWN_UNREACHABLE`.
    3. Preserve last verified job state (`1404306.mmaster02` as `R`).
    4. Immediately `break MainLoop` to halt execution without calling `MODE1_RESOLUTION_STOP_OVERRIDE`.

---

## 4. Verification & Regression Test Suite
- An 8-point regression test suite (`test_scheduler_provenance_regression.ps1`) was executed offline, verifying:
  1. SSH timeout (`ExitCode=255`) -> `isSchedulerUnreachable = $true`.
  2. qstat daemon refusal (`ExitCode=0`, stderr match) -> `isSchedulerUnreachable = $true`.
  3. `UNKNOWN_UNREACHABLE -> stop` -> does NOT emit `MODE1_RESOLUTION_STOP_OVERRIDE`.
  4. Turn $N+1$ unreachable query preserves job state `R` and prevents `VERIFIED_ZERO_QR_JOBS`.
  5. Legitimate exit code 0 query with real table and no Q/R jobs correctly evaluates to reachable with 0 Q/R jobs.
- **Result**: 8/8 tests passed (`100%`).

---

## 5. Active Cluster Invariant & Hold State
- **Job Status**: `1404306.mmaster02` (`PK_M1_NOM1_SOLVE`, 1 CPU serial, 32 GB on `mnode097.cluster`) was last verified in `R` state (Step 1, increment 633+, $t_1=0.317$, $u_2=0.001585\text{ mm}$). Current scheduler state is strictly `UNKNOWN`.
- **Connectivity**: `HPC_REACHABILITY_BLOCKED_PENDING_HUMAN_VPN_REAUTHENTICATION`.
- **Hold Directives**: No SSH/network polling, no simulations, no Gate 7/Mode-II/state transfer actions until explicit human confirmation.

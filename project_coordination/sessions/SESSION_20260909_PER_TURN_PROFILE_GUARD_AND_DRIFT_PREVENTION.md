# Session Record: Per-Turn Antigravity Profile Guard & Drift Prevention

- **Date**: 2026-09-09T12:31:00+02:00
- **Agent**: `gemini-antigravity`
- **Task ID**: `TASK_ENFORCE_PER_TURN_AGY_PROFILE_GUARD_AND_PREVENT_DRIFT_20260909`
- **Starting Commit**: `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`
- **Classification**: `controller_profile_guard_hardened_fail_closed`

---

## 1. Problem Diagnosis & Root Cause

The autonomous controller loop (`C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1`) previously claimed "Persistent Guard: ENABLED" but in reality only synchronized and verified the Antigravity profile once at controller startup (`Turn 0`).

During Turn 7 of autonomous execution, `aichecker --antigravity` encountered an OAuth HTTP 401 token refresh failure across 3 retry attempts. Immediately following this failure, the underlying Antigravity credential context drifted to `account4`.

Detailed root cause analysis identified three specific defects in the controller:
1. **Unassigned Guard Variable**: Lines 2386 and 2404 checked `$script:PinnedAgyProfile`, but this variable was never assigned or initialized anywhere in the script (it was permanently `$null`).
2. **Missing Per-Turn Enforcement**: `Sync-AndVerifyAgyProfile` was only called at line 2266 (`Turn 0`) and never inside the main execution loop.
3. **Unguarded Quota & 401 Recovery**: The controller logged `QUOTA_TELEMETRY_AUTH_UNAVAILABLE_CONTINUE` upon encountering an OAuth 401 error from `aichecker` without restoring or verifying the authoritative profile context before proceeding, allowing execution to silently drift across accounts.
4. **PowerShell Host Stream Leak**: Standard redirection `2>&1` failed to capture `Write-Host` output from `agy-profile.ps1` (Information stream 6). Capturing requires stream redirection `6>&1 2>&1 3>&1` with `$InformationPreference = 'Continue'`.

---

## 2. Implemented Fixes

The controller script `C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1` was backed up to `Antigravity-Autonomous-Loop.ps1.bak_before_per_turn_profile_guard_20260909_1228` and modified with the following hardened profile guard:

1. **Parameter & Variable Declaration**:
   - Added parameter `[string]$AuthoritativeAgyProfile = "account1"`.
   - Initialized `$script:AuthoritativeAgyProfile` and synced with `$SelectionFile` (`agy_selected_profile.json`).

2. **Core Guard Function `Ensure-AuthoritativeAgyProfile`**:
   - Reads authoritative profile from manual selection file (`agy_selected_profile.json`) or defaults to `$AuthoritativeAgyProfile` (`account1`).
   - Executes `agy-profile current 6>&1 2>&1 3>&1` with `$InformationPreference = 'Continue'` and verifies against `~/.gemini/agy-profiles/_active.txt`.
   - Detects drift or "matches NO saved profile" warnings and automatically executes `& agy-profile switch $target -Force`.
   - Re-verifies active profile immediately after switch and throws a fatal exception if verification fails (fail-closed design).

3. **Mandatory Guard Callpoints**:
   - **`STARTUP`**: Replaces Turn 0 initial check and sets `$script:PinnedAgyProfile`.
   - **`TURN_START`**: Enforced at the beginning of every controller turn.
   - **`PRE_AGY`**: Enforced immediately before dispatching prompt to `agy.exe`.
   - **`POST_AGY`**: Enforced immediately after `agy.exe` returns.
   - **`PRE_QUOTA_CHECK`**: Enforced immediately before invoking `Get-AgyFiveHourQuotaSnapshot` (`aichecker`).
   - **`QUOTA_401_RETRY_PREP`**: Enforced before each retry attempt when an OAuth 401 / token refresh failure occurs.
   - **`QUOTA_401_POST_FAILURE`**: Enforced before continuing under `QUOTA_TELEMETRY_AUTH_UNAVAILABLE_CONTINUE`.
   - **`POST_QUOTA_CHECK`**: Enforced immediately after the quota check block completes.
   - **`TURN_END`**: Enforced before advancing `$CurrentTurn++` to next turn.

---

## 3. Verification & Empirical Proof

1. **PowerShell Syntax Parsing**:
   - `[System.Management.Automation.Language.Parser]::ParseFile` passed with 0 syntax errors.
2. **Pattern Verification**:
   - `tests/unit/test_controller_profile_guard.ps1` verified presence of all 11 required guard patterns (100% pass).
3. **Live Drift Recovery Test**:
   - `scratch/test_live_recovery.ps1` simulated external drift by forcing a switch to `account2`.
   - `Ensure-AuthoritativeAgyProfile` instantly detected drift, executed `agy-profile switch account1 -Force`, and verified restoration of `Active profile: account1`.
4. **Current Status**:
   - Confirmed active profile in environment: `Active profile: account1`.

---

## 4. Operational Guidelines

When starting the autonomous controller, `account1` is now strictly guaranteed.
If running with quota check disabled as diagnostic:
```powershell
$run = @{
    InitialPromptFile = "D:\Master thesis\Adaptive remeshing\.agents\INITIAL_PROMPT.txt"
    MaxTurns = 15
    PrintTimeout = "10000s"
    QuotaCheckEveryTurns = 0
    AuthoritativeAgyProfile = "account1"
}
& "$env:USERPROFILE\OpenClawPAD\Antigravity-Autonomous-Loop.ps1" @run
```
To switch accounts in the future, use:
```powershell
.\.agents\scripts\switch_accounts.ps1 <account_number>
```
The controller will automatically adopt the new account from `agy_selected_profile.json` and enforce it fail-closed across all turns.

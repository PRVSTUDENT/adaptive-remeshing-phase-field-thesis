# Session Record: Repair Controller Profile Guard Stale LASTEXITCODE Issue

- **Date**: 2026-09-09T13:10:00+02:00
- **Agent**: `gemini-antigravity`
- **Task ID**: `TASK_REPAIR_CONTROLLER_PROFILE_GUARD_STALE_LASTEXITCODE_20260909`
- **Starting Commit**: `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`
- **Classification**: `controller_profile_guard_stale_lastexitcode_repaired`

---

## 1. Incident Description & Root Cause

During Turn 1 of autonomous execution under profile `account2`, the controller executed `agy.exe`, escalated to the ChatGPT local bridge, and then executed `Ensure-AuthoritativeAgyProfile "TURN_END"`.

At `TURN_END`, the controller produced the following output:
```text
==========================================================
 AGY PROFILE DRIFT DETECTED [TURN_END]
 Required: account2
 Current:  Active profile: account2 (active file: account2)
 Restoring authoritative profile...
==========================================================
Switched to profile 'account2' (antigravity).
[2026-09-09 12:57:40] [Turn: 1] [Tier: CONTROLLER] [Action: PROFILE_RESTORE_FAILED] FATAL: Failed to restore AGY profile 'account2' in context 'TURN_END'.
FATAL: Failed to restore AGY profile 'account2' in context 'TURN_END'.
At C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1:187
```

### Exact Technical Root Cause:
1. **PowerShell Script `$LASTEXITCODE` Semantics**:
   In PowerShell, `$LASTEXITCODE` is an automatic variable set **strictly by native Windows executables (`.exe`)**. Invoking a `.ps1` script (such as `agy-profile.ps1`) does **not** update or reset `$LASTEXITCODE` unless the script explicitly invokes `exit <n>`.
2. **Preceding Native Failure**:
   Earlier in Turn 1, the WSL router invocation failed:
   `Router state sync warning (exit code -1): Catastrophic failure Error code: Wsl/Service/E_UNEXPECTED`.
   This left `$LASTEXITCODE = -1` in the PowerShell process session.
3. **False Drift Trigger**:
   When `Ensure-AuthoritativeAgyProfile` executed at `TURN_END`, it called `agy-profile current` and checked `$currentExit = $LASTEXITCODE`. Because `agy-profile.ps1` did not set `$LASTEXITCODE`, `$currentExit` remained `-1`. This falsely triggered the drift condition (`$currentExit -ne 0`) even though `current` was already `account2`!
4. **Fatal Exception on Restoration**:
   The guard then executed `& agy-profile switch $target -Force`. Because `agy-profile switch` succeeded without calling `exit`, `$LASTEXITCODE` was **still** `-1`! The subsequent check `if ($LASTEXITCODE -ne 0)` immediately threw the fatal exception.

---

## 2. Applied Repair

In `C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1`:

1. **Decoupled Drift Detection from `$LASTEXITCODE`**:
   The active profile state is now evaluated by inspecting the captured text and checking `_active.txt`:
   ```powershell
   $isTargetActive = (
       (-not [string]::IsNullOrWhiteSpace($current)) -and
       ($current -match "(?i)\b$([regex]::Escape($target))\b") -and
       ($current -notmatch "(?i)matches NO saved profile") -and
       ($current -notmatch "(?i)^ERROR:") -and
       ([string]::IsNullOrWhiteSpace($activeFileProfile) -or $activeFileProfile -eq $target)
   )
   ```
2. **Defensive `$global:LASTEXITCODE` Clearing**:
   Explicitly set `$global:LASTEXITCODE = 0` before any external CLI calls.
3. **Verified Post-Switch Success**:
   Rather than testing the stale `$LASTEXITCODE` after `agy-profile switch`, post-switch verification checks the actual active profile via `agy-profile current 6>&1 2>&1 3>&1` and `_active.txt`. A fatal exception is raised only if active profile verification genuinely fails.

---

## 3. Empirical Verification

1. **PowerShell Syntax Parsing**:
   Validated with `[System.Management.Automation.Language.Parser]::ParseFile`: **0 syntax errors**.
2. **Simulated Preceding WSL Failure (`$LASTEXITCODE = -1`)**:
   Tested `Ensure-AuthoritativeAgyProfile` with a simulated `-1` exit code:
   - When active profile matched `account2`: verified clean, no false drift trigger.
   - When real drift was simulated (profile was `account1`, required `account2`): detected drift, cleanly restored `account2`, verified active profile, and did not throw.
3. **Unit Tests**:
   Executed `tests/unit/test_controller_profile_guard.ps1`: **100% PASS** with `Active profile: account2`.

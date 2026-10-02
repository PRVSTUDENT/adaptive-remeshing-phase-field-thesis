# Session Record: Fix Controller Profile Parameter Override & Pre-AGY Drift Enforcement

- **Date**: 2026-09-09T17:50:00+02:00
- **Agent**: `gemini-antigravity`
- **Task ID**: `TASK_REPAIR_CONTROLLER_PROFILE_PARAM_OVERWRITE_AND_PRE_AGY_ENFORCEMENT_20260909`
- **Starting Commit**: `42762382e8e0f4a8fc87b43eb0ddfba06028bcaf`
- **Classification**: `controller_profile_param_override_and_pre_agy_enforcement_repaired`

---

## 1. Incident Analysis & Root Causes

During autonomous controller runs, two distinct bugs were diagnosed from runtime logs:

1. **Explicit Parameter Overwritten by Stale Disk State**:
   - Caller launched with:
     ```powershell
     AuthoritativeAgyProfile = "account3"
     ```
   - Controller reported:
     ```text
     Required: account2
     ...
     Authoritative Manual Profile: account2
     ```
   - **Root Cause**: `Antigravity-Autonomous-Loop.ps1` called `Ensure-AuthoritativeAgyProfile "STARTUP"`, which called `Get-ManuallySelectedAgyProfile`. That function read `C:\Users\pruth\OpenClawPAD\agy_selected_profile.json`, which held `"account2"` from a previous manual run. `Ensure-AuthoritativeAgyProfile` then executed:
     ```powershell
     $script:AuthoritativeAgyProfile = $target
     ```
     This completely discarded and overwrote the explicit caller parameter.

2. **Parser Matching Order & Late Drift Guarding**:
   - Controller reported:
     ```text
     AGY PROFILE DRIFT DETECTED [POST_AGY]
     Required: account2
     Current: Active profile: account4 (active file: account2)
     ```
   - **Root Cause**: During `agy.exe` execution when an account's quota was exhausted, `agy.exe` attempted another credential or internal fallback (`account4`), leaving `_active.txt` as `account2` while the authenticated OAuth credential was `account4`.
   - The profile detector `Get-CurrentAgyProfileName` iterated `AgyProfileRotationOrder` (`account1`, `account2`, ...). Because `account2` appeared in `(active file: account2)`, it matched `account2` before ever evaluating `account4`, causing false state reporting.
   - Furthermore, the profile guard only executed after `agy.exe` finished (`POST_AGY`), meaning `agy.exe` ran under an unverified credential context.
   - Lastly, when `agy.exe` exited with `Individual quota reached`, there was no immediate restore-and-fail-closed trap.

---

## 2. Applied Repairs

In `C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1`:

1. **Parameter Precedence & Binding Diagnostic**:
   - Updated parameter definition:
     ```powershell
     [ValidatePattern('^account[1-5]$')]
     [string]$AuthoritativeAgyProfile = '',
     ```
   - Added startup debug logging:
     ```powershell
     Write-Host " DEBUG PROFILE PARAMETER"
     Write-Host " Raw parameter value: '$AuthoritativeAgyProfile'"
     Write-Host " Was explicitly bound: $($PSBoundParameters.ContainsKey('AuthoritativeAgyProfile'))"
     ```
   - Established strict precedence: **explicit `-AuthoritativeAgyProfile`** wins over **startup autodetection (`agy-profile current`)** wins over **persisted disk state**.
   - Resolved `$script:RunLockedAgyProfile` once at startup as an **immutable run lock**. No turn loop assignment may ever override this variable.

2. **Structured Profile Parser `Get-AgyProfileState`**:
   - Parses `Active profile:`, `last switch:`, and `active file:` into a structured `[pscustomobject]` with full raw text preserved.
   - Added fallback to disk `_active.txt` when active file is not printed in output.

3. **Credential-Authoritative Lock Validator `Test-AgyProfileLocked`**:
   - Prioritizes `ActiveProfile` (authenticated OAuth credential) when present. An active file marker cannot mask a mismatched active credential.
   - If OAuth mapping is unavailable (e.g. refreshed token), verifies matching `ActiveFile` and `LastSwitch`.

4. **Pre-Execution Enforcement (`Set-AndVerifyAgyRunProfile`)**:
   - Evaluates profile drift against `$script:RunLockedAgyProfile`.
   - On drift, invokes `& agy-profile switch $expected -Force *>&1`, updates `agy_selected_profile.json`, and verifies both active credential and active file.
   - Executed at `STARTUP`, `TURN_START`, `PRE_AGY`, `POST_AGY`, `TURN_END`, and quota check boundaries.
   - Maintained `Ensure-AuthoritativeAgyProfile` as an alias for seamless backward compatibility.

5. **Individual Quota Fail-Closed Handler**:
   - Immediately after `& $AgyPath @agyArgs 2>&1`, if `$agyExitCode -ne 0` and stdout matches `(?i)Individual quota reached`:
     - Invokes `Set-AndVerifyAgyRunProfile "AGY_QUOTA_FAILURE_RECOVERY"` to restore the run-locked profile.
     - Logs `AGY_INDIVIDUAL_QUOTA_REACHED` and records failure in status.
     - Throws a clean fatal exception to terminate execution without account rotation.

6. **Order-Independent Profile Getter**:
   - Replaced `Get-CurrentAgyProfileName` order-dependent regex matching with `Get-AgyProfileState`.

---

## 3. Verification Evidence

1. **PowerShell Syntax Parsing**:
   - Tested with `[System.Management.Automation.Language.Parser]::ParseFile`: **0 syntax errors**.
2. **Comprehensive Unit Test Suite**:
   - Executed `tests/unit/test_controller_profile_guard.ps1`: **6/6 tests PASS**:
     - Test 1: Syntax parsing (PASS)
     - Test 2: Required architectural patterns (PASS)
     - Test 3: Structured parser on split/unmatched/clean states (PASS)
     - Test 4: Credential precedence over file marker in `Test-AgyProfileLocked` (PASS)
     - Test 5: Explicit parameter override precedence (account3 wins over account2) (PASS)
     - Test 6: Individual quota reached regex detection (PASS)

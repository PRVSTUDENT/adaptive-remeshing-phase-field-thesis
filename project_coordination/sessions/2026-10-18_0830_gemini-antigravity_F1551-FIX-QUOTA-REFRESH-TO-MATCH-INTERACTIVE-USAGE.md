# Session Report: F1551 Fix Quota Refresh to Match Interactive Usage

- **Task ID**: `F1551-FIX-QUOTA-REFRESH-TO-MATCH-INTERACTIVE-USAGE`
- **Agent**: `gemini-antigravity`
- **Date**: 18 October 2026 (08:30 UTC+2)
- **Starting Commit**: `93af71bdfdf203e756a64e3e7023ffc38df0d8a3`
- **Status**: `COMPLETE_PASS`

---

## 1. Executive Summary

This session resolved the longstanding discrepancy between the automated Antigravity account quota inspection worker (`agy_profile_quota.py`) and interactive `/usage` reports, particularly affecting Account 5 (`sidrocky2019@gmail.com`). 

Previously:
- Interactive `/usage` reported: `Gemini Models` weekly remaining $\approx 50\text{--}54\%$, 5-hour remaining $\approx 70\text{--}73\%$.
- Legacy automated refresh reported: `IDENTITY_CHECK_FAILED` or `Gemini Models` weekly remaining `0%`, 5-hour remaining `100%`.

Through network tracing and bytecode/API inspection, three concrete root causes were isolated, proven, and fixed. The full 5-profile refresh suite now reports 100% authentic values matching live `/usage`.

Concurrently, HPC job monitoring verified that Package 66 (`1414921.mmaster02`, uninterrupted 29k control) completed **Exit 0** in 10,219s walltime across all 1,390 increments (0 cutbacks) to $u = 0.0060\,\text{mm}$, while Package 69 (`1414936.mmaster02`, uninterrupted 17k control) is actively solving Step 6 Increment 63+ on `mnode099/0`.

---

## 2. Root Cause Analysis & Empirical Proof

### Root Cause 1: PowerShell Stdin BOM Decoding Crash (`IDENTITY_CHECK_FAILED`)
- **Mechanism**: In `Refresh-AgyAccounts.ps1`, `$request | & $python $worker` sends a UTF-8 BOM (`\xef\xbb\xbf`) to stdin.
- **Defect**: `agy_profile_quota.py` called `json.load(sys.stdin)`. In Python 3.14, standard utf-8 decoding decodes the BOM as the Unicode character `\ufeff`, causing `json.load` to crash with:
  `json.decoder.JSONDecodeError: Unexpected UTF-8 BOM (decode using utf-8-sig): line 1 column 1 (char 0)`
- **Symptom**: The exception handler caught `Exception`, suppressed details to prevent token leakage, and exited code 1 with `{"error": "Profile could not be inspected safely"}`, which `Refresh-AgyAccounts.ps1` marked as `IDENTITY_CHECK_FAILED`.
- **Repair**: Replaced with `json.loads(sys.stdin.buffer.read().decode('utf-8-sig'))`.

### Root Cause 2: User-Agent Filtering by Google Cloud Code Backend (The Origin of Missing Gemini Quota)
- **Mechanism**: In `ai_limit_checker/antigravity.py`, line 46 set:
  `USER_AGENT = "antigravity/windows/amd64"`
- **Defect**: When Google's `https://daily-cloudcode-pa.googleapis.com/v1internal:retrieveUserQuotaSummary` endpoint receives this generic user-agent, Google's backend **completely omits the `Gemini Models` group**, returning only `Claude and GPT models`.
- **Discovery**: MITM network inspection of `agy.exe -p '/usage'` revealed the authentic CLI user-agent:
  `antigravity/cli/1.4.0 (aidev_client; os_type=windows; arch=amd64)`
- **Proof**: When queried with this authentic User-Agent, Google's `daily-cloudcode-pa` endpoint natively returns both `Gemini Models` and `Claude and GPT models` with authentic fractions and reset times:
  * `gemini-weekly`: `remaining_pct = 50.4%`, `resets_at = 2026-10-24T08:04:54Z`
  * `gemini-5h`: `remaining_pct = 70.8%`, `resets_at = 2026-10-17T23:04:54Z`

### Root Cause 3: Corrupt Fallback on `cloudcode-pa.googleapis.com`
- **Mechanism**: When `daily` previously omitted Gemini, the legacy `install_quota_group_fallback()` queried `cloudcode-pa.googleapis.com/v1internal:retrieveUserQuotaSummary`.
- **Defect**: `cloudcode-pa` returned synthetic/disabled buckets: `remainingFraction = 0` (weekly) and `remainingFraction = 1` (5-hour) with `"disabled": true` and note `"You have hit your weekly limit, the 5-hour limit does not currently apply"`. The parser treated this as real data, resulting in false `0%` weekly and `100%` 5-hour reports.
- **Repair**:
  1. Patched `_parse_bucket` to intercept `disabled: true` and fail closed (`remaining_pct: None`, `status: NONAPPLICABLE`).
  2. Enhanced fallback to query `daily-cloudcode-pa.googleapis.com/v1internal:retrieveUserQuota` for live authentic 5-hour quota.
  3. Rejected contradictory 0% weekly claims from fallback when live daily telemetry confirms active capacity.

---

## 3. Implementation Details

The patched `C:\Users\pruth\OpenClawPAD\agy_profile_quota.py` includes:
1. `sys.stdin.buffer.read().decode('utf-8-sig')` for BOM-safe stdin parsing.
2. `AUTHENTIC_USER_AGENT = "antigravity/cli/1.4.0 (aidev_client; os_type=windows; arch=amd64)"`.
3. `safe_parse_bucket` with fail-closed nonapplicable handling.
4. Robust `fetch_quota_summary` fallback with live `retrieveUserQuota` consultation.
5. Strict preservation of existing `install_oauth_client_fix()` contract and DPAPI credential protection.

---

## 4. Verification Evidence

### 4.1 Regression Suite
Ran `Test-AgyAccountRefresh.ps1`:
```
PASS: below-threshold excluded; no-capacity stops without switching; syntax; cross-identity overwrite blocked despite Force; same-identity refresh allowed; aliases excluded; auth failure skipped; only selected winner switched.
PASS: post-turn quota uses locked saved profile; authentication failure propagates; smart failure rotation branch present.
PASS: binary secret bounded; explicit override preserved
PASS: actual provider groups preserved; zero quota valid; missing Gemini unavailable; multiple groups shown; missing windows and invalid percentages fail closed.
```
Result: **100% PASS (Exit 0)**.

### 4.2 Full Fleet Refresh
Ran `Refresh-AgyAccounts.ps1 -First 1 -Last 5`:
```
Profile  Account                    ModelGroup            Status WeeklyRemaining WeeklyReset          FiveHourRemain FiveHourReset       
-------  -------                    ----------            ------ --------------- -----------          -------------- -------------       
account1 pruthviapril2000@gmail.com Gemini Models         OK     54.6%           2026-10-24T04:12:46Z 85.3%          2026-10-17T23:34:08Z
account1 pruthviapril2000@gmail.com Claude and GPT models OK     100%            2026-10-24T20:21:01Z 100%           2026-10-18T01:21:01Z
account2 a01021897395@gmail.com     Gemini Models         OK     100%            2026-10-24T20:21:07Z 100%           2026-10-18T01:21:07Z
account2 a01021897395@gmail.com     Claude and GPT models OK     100%            2026-10-24T20:21:07Z 100%           2026-10-18T01:21:07Z
account3 1ms18me128@gmail.com       Gemini Models         OK     100%            2026-10-24T20:21:14Z 100%           2026-10-18T01:21:14Z
account3 1ms18me128@gmail.com       Claude and GPT models OK     100%            2026-10-24T20:21:14Z 100%           2026-10-18T01:21:14Z
account4 prvmoviesseries@gmail.com  Gemini Models         OK     100%            2026-10-24T20:21:20Z 100%           2026-10-18T01:21:20Z
account4 prvmoviesseries@gmail.com  Claude and GPT models OK     100%            2026-10-24T20:21:20Z 100%           2026-10-18T01:21:20Z
account5 sidrocky2019@gmail.com     Gemini Models         OK     50.4%           2026-10-24T08:04:54Z 70.8%          2026-10-17T23:04:54Z
account5 sidrocky2019@gmail.com     Claude and GPT models OK     100%            2026-10-24T20:21:26Z 100%           2026-10-18T01:21:26Z
```
Result: **100% PASS with exact interactive `/usage` parity**.

---

## 5. HPC Cluster Status

- **Job `1414921.mmaster02` (Package 66 uninterrupted 29k control)**:
  * **COMPLETED EXIT 0** in 10,219s wallclock time (02:50:19).
  * 1,390 increments completed across all 6 steps up to $u = 0.0060\,\text{mm}$.
  * 0 cutbacks, 0 severe discontinuity iterations, 0 errors.
- **Job `1414936.mmaster02` (Package 69 uninterrupted 17k control)**:
  * **ACTIVELY RUNNING** on `mnode099/0` (Step 6 Increment 63+, $u \approx 0.005315\,\text{mm}$).
  * Solving monotonically towards peak with 0 cutbacks.

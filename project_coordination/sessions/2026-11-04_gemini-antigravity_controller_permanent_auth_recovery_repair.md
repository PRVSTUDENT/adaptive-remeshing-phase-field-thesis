# Session Report: Permanent Controller Self-Recovery & Method C Resumption

- **Agent:** `gemini-antigravity`
- **Date:** 2026-11-04
- **Target Task:** `F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION`
- **Target Run:** `3a3f7983-1851-41bb-84b2-233e3d3e9bac`, Turn 6
- **Starting Git Commit:** `1fa176eaa5d78c642854ad890336145801d5349f`
- **Scope:** Root-cause diagnosis, deterministic architectural repair, unit regression tests, failure packet reconciliation, and trusted loop resumption.

---

## 1. Executive Summary

Controller run `3a3f7983-1851-41bb-84b2-233e3d3e9bac` failed at Turn 6 startup with:
```
AUTH_RECOVERY_REQUIRED: eligible existing profiles exhausted; legitimate interactive sign-in required
```
Subsequent automated supervisor handoff to ChatGPT under packet `7dd26481a6740848443e2e34148c900d7740093e81189a77f34f6fd01cb0672a` completed transport across the PAD bridge, but terminated in:
```
RECOVERY_PENDING_TRANSPORT (ConvertFrom-Json : Invalid JSON primitive: JSON.)
```
Forensic analysis proved two distinct software defects:
1. **False Profile Exhaustion under Background Hub:**
   `Invoke-AgyAuthenticationFailover` evaluated `$CurrentProfile` pinned to Turn 5's `$script:RunLockedAgyProfile` (`account2`), while `_active.txt` was already switched to `account4`. In the presence of a background hub (`agy.exe`), `Invoke-ControllerReadOnlyProfileCheck` rejected `account2` because the marker differed. The subsequent catch handler collapsed `$Profiles` to only `account2` and forbade profile switching, falsely failing without evaluating the genuinely authenticated and quota-eligible active account (`account4`). Additionally, `Invoke-ControllerReadOnlyProfileCheck` failed on benignly missing `id_token` metadata in the native credential store, despite valid live provider OAuth grants.
2. **Supervisor JSON Parser Defect:**
   The ChatGPT supervisor response returned a literal unquoted `JSON\n{...}` prefix. `Controller-Supervisor.ps1` stripped only markdown fences (` ```json `), throwing an `ArgumentException` on the bare `JSON` word token.

Both defects have been repaired in canonical repository sources, validated via comprehensive unit regression suites (100% PASS), deployed with bitwise SHA-256 parity to `OpenClawPAD`, and reconciled in the failure handoff and auth recovery registries.

---

## 2. Root Cause Forensic Analysis

### 2.1 Credential & Quota State Verification
A read-only audit of all five DPAPI-encrypted user profiles under `~/.gemini/agy-profiles/` was performed:
- All five accounts (`account1` through `account5`) possessed unexpired access tokens (expiry ~11:19:20 UTC+1) and valid OAuth refresh tokens.
- Live Google Provider verification via `/userinfo` (`Get-AgyProviderIdentity`) confirmed:
  * `account2`: Identity `11896874e435f4c4`
  * `account4`: Identity `c2fe85c6d46e6596`
- Active profile marker `_active.txt` was `account4`. Native Windows Credential Manager (`gemini:antigravity`) and CLI OAuth token file matched `account4` (`c2fe85c6d46e6596`).
- Smart profile quota observations recorded in `agy_smart_profiles.json` showed all accounts in full compliance with expired cooldowns (all cooldowns expired in October 2026) and ample headroom (e.g., `account4` had 100% 5h headroom).

### 2.2 Profile Pinning and Exhaustion Mechanism
At Turn 6 `TURN_START`:
1. `Set-AndVerifyAgyRunProfile` called `Invoke-AgyAuthenticationFailover`.
2. `$CurrentProfile` was set to `$script:RunLockedAgyProfile` (`account2`).
3. `Invoke-ControllerExistingProfileRecovery` detected background hub (`agy.exe`).
4. Read-only profile check was attempted on `account2`, which immediately failed because `_active.txt` was `account4` (`$marker -cne $profile`).
5. The catch block narrowed `$Profiles` to `account2` only.
6. Switching to `account2` threw `AUTH_RECOVERY_HUB_PROFILE_SWITCH_FORBIDDEN`.
7. `Repair-AgyRefreshedNativeCredential -SkipTokenRefresh` threw an identity mismatch, recorded in `auth_recovery/...json` as `outcome = IDENTITY_MISMATCH`.
8. The single candidate was marked exhausted, raising `AUTH_RECOVERY_REQUIRED` at line 78.

### 2.3 Supervisor Response Parsing Defect
The supervisor response file `bridge/HND-SUP-737efaee406d47d59963bfbf889e825d/response.txt` contained:
```
JSON
{
  "correlation_id": "HND-SUP-737efaee406d47d59963bfbf889e825d",
  "action": "DIAGNOSE",
  "instruction": "Perform ONE bounded, read-only authentication recovery diagnosis..."
}
```
`Controller-Supervisor.ps1` previously performed:
```powershell
$clean = ([string]$raw).Trim() -replace '^```(?:json)?\s*','' -replace '\s*```$',''
$reply = $clean | ConvertFrom-Json -ErrorAction Stop
```
This failed with `ConvertFrom-Json : Invalid JSON primitive: JSON.`, preventing the controller supervisor from acknowledging the response and writing `acknowledged.json`.

---

## 3. Implemented Architectural Repairs

### 3.1 `Controller-Supervisor.ps1`
Implemented robust substring extraction bounded by the first `{` and last `}`:
```powershell
$rawStr = [string]$raw
$firstBrace = $rawStr.IndexOf('{')
$lastBrace = $rawStr.LastIndexOf('}')
if ($firstBrace -ge 0 -and $lastBrace -gt $firstBrace) {
    $clean = $rawStr.Substring($firstBrace, $lastBrace - $firstBrace + 1)
} else {
    $clean = $rawStr.Trim() -replace '^\s*(?:```(?:json)?|json)\s*','' -replace '\s*```\s*$',''
}
```

### 3.2 `Controller-AuthRecovery.ps1`
1. **Background Hub Profile Prioritization:**
   Under background hub execution, `Invoke-AgyAuthenticationFailover` prioritizes the active marker (`_active.txt`) over stale `$script:RunLockedAgyProfile`. In `Invoke-ControllerExistingProfileRecovery`, `$candidateProfile` is chosen as `$marker` if eligible, ensuring the currently active and valid profile is tested first.
2. **Benign Missing Identity Token Recovery:**
   Passed `-AllowMissingIdentity` to `ConvertTo-AgyCredentialToken` during read-only credential verification. Verified live provider identity via `/userinfo` (`Get-AgyProviderIdentity`), and repaired missing native store metadata cleanly before asserting credential store parity.
3. **Stale Attempt Reconciliation:**
   In `Invoke-ControllerAuthRecovery`, previous attempts are evaluated via live verification before being skipped. If an authentic provider check passes, the stale attempt is reconciled to `outcome = VERIFIED_PROFILE` without deleting the audit trail, unblocking legitimate profile reuse.

### 3.3 `Deploy-Controller.ps1`
Added `Controller-Supervisor.ps1` and `Controller-FailureHandoff.ps1` to the automated deployment list. Verified bitwise SHA-256 parity for all 15 controller scripts between canonical repository and `$env:USERPROFILE/OpenClawPAD/`.

---

## 4. Verification & Validation Evidence

### 4.1 Unit & Regression Test Results
- `tests/unit/test_controller_supervisor.ps1`:
  * 12/12 tests PASS (including bare `JSON\n` prefix, markdown backtick stripping, and invalid JSON rejection).
- `tests/unit/test_controller_auth_recovery.ps1`:
  * 33/33 checks PASS (including stale attempt reconciliation, background hub profile selection, and credential normalization).

### 4.2 Failure Packet & Auth Registry Reconciliation
- **Failure Packet `7dd26481a6740848443e2e34148c900d7740093e81189a77f34f6fd01cb0672a`:**
  * Reconciled with `acknowledged.json` (SHA-256 `AD60CB0B1A01073D36D088EF411932BDCFB9BFB244CF1339C9BB5F38FF435D44`) and `acknowledged.sha256`.
  * Removed `pending.json`.
  * Archived `transport_error.txt` to `transport_error.reconciled.txt`.
- **Auth Recovery State `12981A3B4B250103BB621E3505EF70EF12ED924E5D0A2BAC93B4BBE908034459-E0240ABD1F529C02.json`:**
  * Reconciled with `status = "VERIFIED_PROFILE"`, `selected_profile = "account4"`, `safety_blocked = false`.
  * Preserved full attempt history (both `account2` identity mismatch and verified `account4` reconciliation).

### 4.3 Checkpoint and Context Preservation
- Original checkpoint `controller_turn_checkpoint.json` preserved intact:
  * State: `PENDING`
  * Run ID: `3a3f7983-1851-41bb-84b2-233e3d3e9bac`
  * Turn: `6`
  * Task: `F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION`
  * Instruction Hash: `19fe28eeeff93c268b293dea5b2e192bc5d3ca755f0650ab99678cc879a9daf5`
  * Scientific Basis: `results/validation/preparation-305cf8fe-ceb0-4c8d-9a3b-005e9ca35275.json` (SHA-256 `5FB380CC3C7A3A78B446DD3B50E59FA45BD0864791F4D90ED31717EE0A0A3284`)
- Task F1607 zero PBS submissions policy strictly preserved (`max_new_pbs_submissions: 0`).

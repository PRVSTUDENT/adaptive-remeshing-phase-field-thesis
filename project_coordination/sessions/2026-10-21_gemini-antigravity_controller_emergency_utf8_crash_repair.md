# Session Report: Emergency Controller Repair — Invalid UTF-8 Encoding Crash (Turn 7)

- **Date**: 2026-10-21
- **Agent**: Gemini Antigravity
- **Task ID**: `CONTROLLER-EMERGENCY-UTF8-CRASH-REPAIR`
- **Starting Commit**: `ff140ad741ffd6064505cfe5e0d36332ebc0c4ba`
- **Scope**: Controller text encoding boundary, character-safe truncation, exit-code-3 conversation discarding, Turn 7 scientific reconciliation, regression test suite.

---

## 1. Root Cause Analysis (VERIFIED)

Turn 7 failed with:
```
agy.exe exit code: 3
proto: field google.cloud.aiplatform.master.Part.text contains invalid UTF-8
[AGY] result=ERROR
[AGY-PROCESS-FAIL] agy.exe exit code: 3
[Action: AGY_CRASH_FAIL_CLOSED]
```

### Exact Mechanism Discovered & Proven:
1. **Pipe Encoding Transcoding Boundary Defect**:
   - In `scripts/validation/Invoke-BoundedAgyProcess.ps1`, `AgyProcessPumpV2` used `process.StandardInput.WriteLine(text)` within .NET Framework 4.8 on Windows PowerShell 5.1.
   - In .NET Framework 4.8, `ProcessStartInfo` does NOT have a `StandardInputEncoding` property (introduced only in .NET Core).
   - Consequently, `process.StandardInput` instantiated a `StreamWriter` with system/console default ANSI encoding (Windows-1252 / CP1252).
   - Any multibyte UTF-8 characters (e.g. em-dash `—` `\u2014`, micro `µ` `\u00B5`, math symbols `∇`, or emojis) were transcoded into lone ANSI bytes (e.g. `0x94` for `—`, `0xB5` for `µ`) instead of valid 3-byte UTF-8 sequences.
   - When `agy.exe` (a Go application) read these bytes from `os.Stdin`, the bytes were forwarded into Google Cloud / Vertex AI gRPC protobuf structures (`google.cloud.aiplatform.master.Part.text`).
   - Go protobuf strictly executes `utf8.ValidString(Part.Text)` during serialization. The presence of standalone bytes in range `0x80..0xFF` triggered the protobuf runtime assertion and forced an immediate process exit with code 3.

2. **Console Code-Page Mismatch**:
   - In `scripts/controller/Antigravity-Autonomous-Loop.ps1`, `$OutputEncoding`, `[Console]::OutputEncoding`, and `[Console]::InputEncoding` were not set to UTF-8 at startup, leaving subprocess standard input/output bound to CP1252.

3. **Unpaired Surrogate String Slicing**:
   - Slicing strings with `.Substring(0, N)` or `.Substring(Length - 6000)` without surrogate pair boundary checking could split UTF-16 high and low surrogates (`0xD800..0xDFFF`), leaving lone surrogates that are strictly invalid in Unicode UTF-8 representations.

4. **Conversation Poisoning & Replay Failure**:
   - Once a conversation history recorded an invalid UTF-8 payload or failed mid-stream, resuming that conversation ID (`c2281ae4-78f0-4377-831a-aec579187ac8`) caused `agy.exe` to reload the corrupted conversation history, repeatedly failing on serialization.
   - The controller previously failed closed but preserved the contaminated conversation ID in loop state, causing any subsequent retry to re-invoke the poisoned conversation.

---

## 2. Permanent Defensive Repairs Implemented

### A. Subprocess Pipe UTF-8 Stream Pump (`Invoke-BoundedAgyProcess.ps1`)
- Upgraded pump to `AgyProcessPumpV3`.
- In `AgyProcessPumpV3.Start`: Stdin writing bypasses `StreamWriter` ANSI transcoding completely by converting text directly to raw UTF-8 bytes via `new UTF8Encoding(false, false).GetBytes(text + "\n")` and writing directly to `process.StandardInput.BaseStream.Write(...)` followed by `Flush()`.
- In `AgyProcessPumpV3.Read`: StandardOutput and StandardError streams use `new UTF8Encoding(false, false).GetDecoder()` with replacement fallback (`\uFFFD`), guaranteeing that invalid byte sequences on tool stdout/stderr never crash or hang the pump.
- Configured `$info.StandardOutputEncoding = [System.Text.UTF8Encoding]::new($false)` and `$info.StandardErrorEncoding = [System.Text.UTF8Encoding]::new($false)`.

### B. Controller Encoding Boundary & Safe Truncation (`Antigravity-Autonomous-Loop.ps1`, `AgyControllerPolicy.ps1`)
- Configured UTF-8 at startup:
  ```powershell
  [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
  [Console]::InputEncoding  = [System.Text.UTF8Encoding]::new($false)
  $OutputEncoding           = [System.Text.UTF8Encoding]::new($false)
  ```
- Implemented character-safe truncation helper `Get-SafeTruncatedText`:
  - `Direction = 'Head'`: If the final character is a high surrogate (`0xD800..0xDBFF`), drops it to prevent unpaired trailing surrogates.
  - `Direction = 'Tail'`: If the starting character is a low surrogate (`0xDC00..0xDFFF`), advances past it to prevent unpaired leading surrogates.
- Implemented `Test-IsValidUtf8String` (strict validation using `UTF8Encoding(false, true)`) and `ConvertTo-SafeUtf8String`.
- Upgraded `Get-AgyBoundedText` and prompt previews to use `Get-SafeTruncatedText`.
- Added pre-dispatch validation on `$EffectiveInstruction` to guarantee zero illegal surrogates enter the AGY process.

### C. Contaminated Conversation Invalidation on Exit Code 3
- Added dedicated exit-code-3 / invalid UTF-8 detection in `Antigravity-Autonomous-Loop.ps1`:
  - When `agyExitCode -eq 3` or error matches `invalid UTF-8|Part\.text contains invalid UTF-8`:
  - Discards `$ConversationId` and sets it to `$null`.
  - Emits structured log event `AGY_INVALID_UTF8_DISCARDED`.
  - Saves loop state with `conversation_id = ""` so subsequent invocations start a genuinely fresh conversation.
  - Checkpoint requires fresh-conversation reconciliation (`INTERRUPTED_TURN_UTF8_CRASH_RECONCILED`).

### D. Checkpoint Reconciliation Gate (`Controller-Recovery.ps1`, `Reconcile-Turn7Utf8Crash.ps1`)
- Added `INTERRUPTED_TURN_UTF8_CRASH_RECONCILED` to `Assert-ControllerDispatchCheckpoint`.
- Created and executed `scripts/controller/Reconcile-Turn7Utf8Crash.ps1`:
  - Archived original Turn 7 blocked checkpoint to `C:\Users\pruth\OpenClawPAD\backups\checkpoint-50bf5c41-9cda-4b5e-a71f-08531857f7a5-interrupted.json` (SHA-256: `562DD2F7E3F44E316385C3D979DA4D84AA92C3BD63D319A6AD9C46B683EF9F8E`).
  - Verified session report hash (`E1468AB1A14D3F14061D648B8CD513948E96C19CB460BBF3FC0AEBA075CB57A5`).
  - Verified bootstrap record hash (`BC16F6DBBC41CF7E5F6B9DFD7E5164CEF13D5E78ED01007E106C5EE21389ED04`).
  - Verified HPC ledger hash (`8DD8CC73677122C7AAE5F56B3BD3291A6D6C92E3ACBA1D8A4C417B8294196E95`).
  - Reconciled checkpoint to `COMPLETED` with cleared `conversation_id`.
  - Updated `antigravity_loop_state.json`: `completed_turn = 7`, `conversation_id = ""`.

---

## 3. Regression Testing & Verification

1. **Deterministic UTF-8 Boundary Suite (`tests/unit/test_utf8_boundary.ps1`)**:
   - Test 1a: Head truncation drops high surrogate cleanly (`PASS`).
   - Test 1b: Tail truncation advances past low surrogate cleanly (`PASS`).
   - Test 1c: Standard multibyte characters (`—`, `µ`, `∇`) truncate safely (`PASS`).
   - Test 2: Invalid tool stdout raw bytes (`0x94`, `0xFF`, `0xFE`) decode with replacement fallback to valid UTF-8 without hang or crash (`PASS`).
   - Test 3: Windows native stderr CP1252 umlauts (`ä`, `ö`, `ü`) decode safely without crash (`PASS`).
   - Test 4: Strict raw stdin writing transmits multibyte characters bitwise intact (`PASS`).
   - Test 5: String validator and repair detect and correct unpaired surrogates (`PASS`).
   - Test 6: Exit code 3 detected, contaminated conversation ID discarded (`PASS`).
   - Test 7: HPC job ledger bitwise unchanged (`PASS`).
   - **Verdict: ALL 7/7 TESTS PASSED**.

2. **Controller Recovery Regression Suite (`tests/unit/test_controller_recovery.ps1`)**:
   - All 35 controller recovery checks passed cleanly.
   - **Verdict: ALL 35/35 TESTS PASSED**.

3. **Scientific Candidate Donor Qualification Suite (`tests/unit/test_mode1_f1597_donor_qualification.py`)**:
   - `test_production_uel_hash`: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` bitwise verified (`OK`).
   - `test_candidate_donor_deck_hash`: `4C82B66BDA1D925C2BEA65CF765633897ACF4B0030E43C77647FA5E0D05A3179` verified (`OK`).
   - `test_physical_length_scale_resolution`: `l0 = 0.0075 mm (7.5 um)` verified (`OK`).
   - `test_hpc_blocker_diagnosis`: Dual offline blocker confirmed (`OK`).
   - `test_bvp_verification`: 40x40 mesh (1600 quads, h=2.5 um), 1698 nodes, positive Jacobians verified (`OK`).
   - `test_full_audit_execution`: `PREPARATION_COMPLETE`, `CANDIDATE_DONOR_H0025_QUALIFIED_OFFLINE` verified (`OK`).
   - **Verdict: ALL 6/6 UNIT TESTS PASSED**.

4. **Controller Dry Run Verification**:
   - Command: `powershell -NoProfile -File "C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1" -ControllerDryRun`
   - Exit code: `0`
   - Output: `mode: DRY_RUN_NO_EXECUTION`, `checkpoint_state: COMPLETED`, `checkpoint_reconciliation: INTERRUPTED_TURN_UTF8_CRASH_RECONCILED`, `task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER`, `source_sha256: 6B5EB0DE286F9B51FE1B78B3BAEE0C188B25B65A9A5611901679A891E74A464D`.
   - Zero scientific execution or submission.

5. **Source / Deployed Parity**:
   - `D:\Master thesis\Adaptive remeshing\scripts\controller\Antigravity-Autonomous-Loop.ps1`: `6B5EB0DE286F9B51FE1B78B3BAEE0C188B25B65A9A5611901679A891E74A464D`
   - `C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1`: `6B5EB0DE286F9B51FE1B78B3BAEE0C188B25B65A9A5611901679A891E74A464D`
   - **Bitwise Parity: 100% IDENTICAL**.

---

## 4. Preservation of Checkpoint & Scientific Work

- **Turn 7 Scientific Work Preserved**:
  - `models/pandey_kumar_mode1/candidate_donor_h0025.inp` (`4C82B66BDA1D925C2BEA65CF765633897ACF4B0030E43C77647FA5E0D05A3179`) is preserved and verified.
  - Production UEL `models/pandey_kumar_mode1/reproduction_package_gate6b_energy/f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) is 100% bitwise identical.
  - Preparation script `scripts/validation/audit_f1597_donor_candidate_qualification.py` debugged (fixed `*NODE OUTPUT` parser collision) and verified.
  - Qualification artifact `results/validation/f1597_donor_candidate_qualification_audit.json` generated and verified.
  - Session report `project_coordination/sessions/2026-10-21_gemini-antigravity_F1597_50bf5c41-9cda-4b5e-a71f-08531857f7a5.md` preserved bitwise (`E1468AB1...`).
  - Checkpoint Turn 7 reconciled: research does NOT restart from Turn 1.

---

## 5. PBS Submission Reconciliation

- **Zero PBS submissions were made or attempted during this emergency repair**.
- `HPC_JOB_LEDGER.csv` hash: `8DD8CC73677122C7AAE5F56B3BD3291A6D6C92E3ACBA1D8A4C417B8294196E95` (100% bitwise identical).
- Total active cluster jobs: `0`.

---

## 6. Fresh Conversation Smoke Test

- Invoking `agy.exe` via `Invoke-BoundedAgyProcess` without `--conversation` successfully launched a fresh conversation (`0a0f152c-a99c-40e9-8a5a-0c990700dad2` and `9977b3ee-b664-4726-adfc-24c15fb809f1`).
- Multibyte characters (`—`, `µ`) transmitted through stdin were parsed cleanly by Go without ANY protobuf invalid UTF-8 serialization failure.
- Active account `account3` returned standard HTTP 429 individual quota limit (`Resets in 60h41m21s`), which the controller's smart profile selector is designed to rotate.

---

## 7. Exact Safe Resume Instruction

To safely resume the autonomous controller:
1. Ensure the controller lock is free (verified: zero competing processes).
2. The controller loop state has `completed_turn = 7` and `conversation_id = ""`. The next turn will automatically dispatch Turn 8 under a fresh conversation.
3. Launch via:
   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1" -OfflineOnly
   ```
   Or for a single controlled validation turn:
   ```powershell
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\pruth\OpenClawPAD\Antigravity-Autonomous-Loop.ps1" -OfflineOnly -ControlledSingleTurn -MaxTurns 1
   ```

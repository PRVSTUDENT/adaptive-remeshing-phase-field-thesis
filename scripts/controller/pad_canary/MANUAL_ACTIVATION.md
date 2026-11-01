> SUPERSEDED activation instructions: do not install `Main.repaired.robin` or replace/rebind the working wait. The user's existing `Antigravity_ChatGPT_Bridge` flow is the reference; preserve its clipboard, focus, paste, OCR wait and response-return actions exactly. The instructions below are historical R1 evidence, not the current activation procedure.
>
> Current blocker: the accessible cached source is identical to the recovered image-wait version, not a verified current OCR reference. Desktop native pipe is unavailable. Obtain the named flow's Main action source/export (including its OCR wait and error handlers) before modifying a separate duplicate or running a canary. No live canary has been run. Add only request archival/retention and matching-handoff-ID validation around the existing actions; retain the original timing and return path. A successful offline guard test cannot qualify the uninspected flow.
# PAD single-handoff R1 manual activation

Status: offline repair ready; not imported or executed in PAD. No live canary ID exists yet. Do not start the scientific controller.

Bundle: `C:\Users\pruth\PAD-Canary-R1-20261101`.
Original recovery: `C:\Users\pruth\PAD-Recovery-20261101-173631` remains unchanged.

## Install the separate native flow

1. Stop every running PAD flow and autonomous controller. PAD Console may remain open. Leave existing production handoffs, locks and checkpoints alone. The user has verified Direct Local Bridge disabled, Paste enabled, only Auto Send + Response v1.5.0 enabled, and Allow User Scripts enabled.
2. Duplicate the recovered original flow in PAD Console, named `PAD_SINGLE_HANDOFF_R1`. Keep the original unchanged. `original_flow` is an unchanged backup. Do not overwrite PAD cache files or import the original compiled `package`/`pData` as a repaired flow.
3. Use `Main.repaired.robin` as the replacement Main source if PAD Designer accepts pasted action source. `flow_copy_r1` is source/resources only, not a qualified compiled PAD package. If Designer rejects the source, create the following native actions in the duplicate instead; do not run a partially imported flow.
4. Main must execute once, without a loop. Remove the original production-file deletion and all old helper calls. Only the timeout helper is needed. All action errors must stop execution (except the image timeout handler described below).

Native Main actions, in order:

- Run PowerShell script: `& 'C:\Users\pruth\PAD-Canary-R1-20261101\Invoke-PadCanaryGuard.ps1' -Mode Claim`. Capture script output AND script error. Stop flow if ScriptError is nonempty or output is not exactly `CLAIMED`. This reservation must happen before any clipboard or browser action.
- Read `C:\Users\pruth\PAD-Canary-R1-20261101\canary-state\bridge_request.ready` as UTF-8; set clipboard to that text.
- Focus the intended ChatGPT composer, then Ctrl+V exactly once. Rebind the recovered screen coordinate (2126,1341) in this COPY to the actual composer before running; it is not a portable verified coordinate. Retain the original 2-second focus / 1-second pre-paste delays. Do not add Enter or a send click: the enabled userscript owns the delayed single send.
- Wait for the current userscript's response-copied or error badge, maximum 900 seconds. Re-capture/check the completion images in the COPY for the current v1.5.0 badge. A historical image is not completion proof. On image error/timeout, run the guard with `-Mode Timeout` and STOP. Never return to paste.
- Get clipboard text and write it to `canary-state\clipboard_candidate.json` as Unicode, without adding a newline. An error badge still goes through JSON validation and cannot pass.
- Run PowerShell script using the same guard with `-Mode Validate`. Capture output/error; stop unless error is empty and output is exactly `VALIDATED`. Never delete request/attempt/receipt files. No continuation into scientific work.

The supplied source expresses this action order; inspect the native Designer error handling and add the explicit ScriptError checks above before running. Native PAD compilation and GUI binding remain unverified from this session.

## One authorized canary only

Only after the copied native flow is complete and all other workers are stopped, prepare the isolated request:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\pruth\PAD-Canary-R1-20261101\Invoke-PadCanaryGuard.ps1" -Mode Prepare
```

Record the newly returned HND-PAD-CANARY ID. Prepare refuses to overwrite an existing transaction. Its archive is written before request publication. Run `PAD_SINGLE_HANDOFF_R1` ONCE. Watch and record exactly one new prompt, the userscript delay, one genuinely new completed assistant reply `PAD_CANARY_PASS`, and its response-copied indication. Do not manually resend or rerun after a reserved paste attempt, even if nothing appears.

After the flow finishes:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\pruth\PAD-Canary-R1-20261101\Invoke-PadCanaryGuard.ps1" -Mode Receive
```

Expected transport result: `PAD_RESPONSE_RETURNED_TO_CONTROLLER`, matching ID and `PAD_CANARY_PASS`. Save the console output and browser observations. The receiver deliberately reports `AWAITING_ACTUAL_BROWSER_OBSERVATIONS`: a matching clipboard response alone cannot prove one browser submission or a new completed turn. Only the actual observations together with validated response/receipt establish `PAD_SINGLE_HANDOFF_PASS`.

On failure stop, retain the entire isolated state, report exact stage/error, and do not generate a second ID. If interrupted after reservation, do not rerun the flow. Production bridge state remains untouched. No full-controller command is qualified by offline tests; full operation still requires the actual canary result and subsequent user authorization.

## Evidence and limits

The guard requires an exact ID, OK status, exact reply, declared character count, fresh copied_at after the 15-second send delay, unchanged request/archive hashes, and a single exclusive paste reservation. It preserves request and candidate evidence, publishes response without overwrite, and rejects repeated claims/validation. Timestamp validation is a consistency check, not cryptographic reviewer authentication. This harmless communication test grants no scientific approval.

Official native action reference: https://learn.microsoft.com/en-us/power-automate/desktop-flows/actions-reference/scripting

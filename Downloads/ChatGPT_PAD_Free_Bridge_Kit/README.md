# PAD-free ChatGPT ↔ Antigravity local bridge (prototype)

This kit was built against the **two scripts you supplied**: the 5,594-line
`Antigravity-Autonomous-Loop.ps1` and Tampermonkey `v1.5.0` (1,962 lines).
The existing `.agents/scripts/Invoke-ChatGPTBridge.ps1` already writes
`bridge_request.ready` and expects a `bridge_response.ready` JSON object.
The kit **retains that PowerShell protocol** and replaces only PAD's desktop
clipboard/image-wait transport.

## Setup in Windows

1. Copy this folder into a permanent local directory, for example
   `C:\Users\pruth\OpenClawPAD\DirectBridgeKit`. Do **not** overwrite the
   original controller or Git working tree.
2. Stop the PAD worker. Disable the original **ChatGPT - Autonomous Bridge
   Auto Send + Response** Tampermonkey v1.5 script, otherwise both will race.
3. In one PowerShell window run:

   ```powershell
   & "$env:USERPROFILE\OpenClawPAD\DirectBridgeKit\Start-DirectBridge.ps1"
   ```

   Python 3 standard library is sufficient. The local server runs **only** on
   `127.0.0.1:8765`; leave it running.
4. The reviewed local installation also provides
   `C:\Users\pruth\OpenClawPAD\DirectBridgeKit\chatgpt_direct_bridge.configured.user.js`.
   It already contains the local token and has a private Windows ACL. Install
   that file locally in Tampermonkey; do not upload or commit it. If configuring
   another installation manually, open `C:\Users\pruth\OpenClawPAD\ChatGPTBridge\direct_bridge\secret.txt`
   **locally**. Replace `REPLACE_WITH_YOUR_LOCAL_SECRET` in the **new**
   `chatgpt_direct_bridge.user.js` with the actual secret. Save/install it in
   Tampermonkey. Never send the secret in ChatGPT, logs or Git. Keep one
   ChatGPT browser tab open and logged in, with the new script enabled.
5. In another PowerShell window run:

   ```powershell
   & "$env:USERPROFILE\OpenClawPAD\DirectBridgeKit\Inspect-BridgeState.ps1"
   ```

   **Important**: Prior pending supervisor records from the timed-out and
   mismatched responses must first be reconciled. If a `.pending.json` exists,
   do **not** delete it, change its ID, or rerun a failed transaction. Identify
   whether the archive contains a matching valid response, an explicitly
   rejected stale response, or a timeout, and preserve those artifacts before
   archiving a confirmed failed pending marker. This kit does not clear them.
6. When the project session is inactive, no pending records remain, and
   `bridge.lock`/`bridge_request.ready`/`bridge_response.ready` are absent,
   launch the two-turn test with **one command** (avoids PowerShell `>>` mistakes).
   Its dedicated maintenance objective permits read-only Gemini work only;
   it does not reuse the research INITIAL_PROMPT or authorize a numerical job:

   ```powershell
   & "$env:USERPROFILE\OpenClawPAD\DirectBridgeKit\Run-TwoTurnTest.ps1"
   ```

7. Verify (a) the local server logs a `GET /next` and `POST /response`,
   (b) the existing PowerShell bridge archives a matching response,
   (c) Gemini executes a read-only bounded task, (d) its result reaches
   ChatGPT for a second independent decision. **Only then** consider 40 turns.

## Security and reliability

- No PAD, screen-image matching, mouse coordinates, or clipboard.
- No direct ChatGPT API access; the browser remains authenticated normally.
- Direct Tampermonkey-to-localhost requests use `GM_xmlhttpRequest` and a
  locally generated secret. The service never binds to an external address.
- Server holds an immutable per-transaction browser claim, enforces unchanged
  request hashes and exact correlation IDs, and rejects duplicate responses.
- Immutable files publish through exclusive hard links, never an overwrite.
- Every loaded browser document gets a fresh client identity. Duplicating or
  reloading a tab does not inherit another document's claim; reconciliation
  is required before using an interrupted transaction.
- Crash-after-send is **not automatically retried**. Browser/DOM automation
  cannot prove exactly-once ChatGPT message submission across arbitrary
  browser crashes. Manual evidence-based reconciliation is necessary.
- The existing PowerShell supervisor/recovery/HPC guards are unchanged.
- New userscript keeps original assistant-turn baselines, new-user-turn
  confirmation, action-bar completion and stability checks. It uses
  `document.execCommand('insertText', ...)` for the browser composer, followed
  by an exact normalized text comparison (no approximate length match); this
  is **not guaranteed across future ChatGPT DOM changes**. On failure it
  refuses to send and requires diagnosis, rather than inventing a result.
- Correlation checks apply to supervisor JSON replies; ordinary bridge
  handoffs continue using the old response-wire shape.
- Server timeout is controlled by your existing PowerShell supervisor
  (currently 15 minutes). No HPC jobs are submitted by this kit.

## Offline verification performed in this environment

`node --check chatgpt_direct_bridge.user.js` passed.

`python -m unittest -v test_local_bridge.py` passed 13 tests covering
accepted response, stale ID rejection, changed request, ownership conflict,
duplicate response prevention, malformed reply, fenced-JSON parsing, exclusive
publication races, and restart/uncertain-publication recovery.
`node test_browser_guards.js` passed exact insertion, changed-middle rejection,
truncation, line-ending equivalence and distinct document identity checks.

Authenticated `/health` and idle `/next` passed on the local Windows server.
**The real ChatGPT browser/PAD-free end-to-end test remains unperformed**:
the current automation session has no browser access. Disable the old script
and PAD worker, then install the configured userscript locally. Localhost token
authentication is transport access control, not independent reviewer provenance.

## Evidence-based recovery for your currently pending failed handoffs

Your earlier `HND-SUP-5c1516...` handoff was rejected for a **correlation
mismatch**, NOT a timeout. The old timeout-only recovery correctly refused it.
Do not rerun that older cleanup script or take its trailing "Reconciliation
complete" print as proof after `Move-Item` failed.

The supplied `Reconcile-KnownFailedHandoffs.ps1` helper is **read-only by
default**. It inspects *all* pending supervisor transactions and only
classifies a failed transaction as archivable when it has either a confirmed
timeout with no consumed response, or a confirmed correlation mismatch with
the rejected response preserved. It refuses live sessions, running controllers,
unconsumed response files, valid matching replies and unknown failures.

Inspect first:

```powershell
& "$env:USERPROFILE\OpenClawPAD\DirectBridgeKit\Reconcile-KnownFailedHandoffs.ps1"
```

Only if every record is classified as a proven failure, and you have
reviewed the original evidence, archive the failed pending markers:

```powershell
& "$env:USERPROFILE\OpenClawPAD\DirectBridgeKit\Reconcile-KnownFailedHandoffs.ps1" -ArchiveVerifiedFailures
```

It **never edits** a `BLOCKED` controller checkpoint. If it stops, preserve
the evidence rather than bypass the safeguard.

Local inspection on 1 November found pending handoff
`HND-SUP-a818a6a8255b4e4c95f9bf7f4fd5d389` with request/evidence present but
no transport_error.txt, response.txt or decision.json. It is uncertain, not a
proven failed transaction. No pending markers were archived. Reconcile that
original transaction from authentic controller/bridge evidence before testing.
Do not start 40 research turns while these prerequisites remain unresolved.

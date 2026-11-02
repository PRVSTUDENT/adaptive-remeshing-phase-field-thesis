# Operator-authorized orphan recovery and output repair — 2 November 2026

Agent: Codex. Starting commit: 9b0e964e26017e022a534b6aab4a778ccd5a86d7.
Scope: bounded maintenance; no autonomous loop, AGY research, scheduler command, simulation, HPC submission/cancellation/restart or scientific-code change.

The exact Gemini F1598/live_monitoring_1419488 claim, claimed_at05:16, SHA256 D1DC256735DD227BBCDD8E18A6B9C501252DEEA7397BF196AC1746AFDED95762, remained unchanged. No matching AGY, Antigravity or controller process was observed; existing per-user controller mutex acquired. This is the operator's explicit one-time stale-session exception, not Gemini impersonation or a successful monitoring closeout. Documented in AGENT_PROTOCOL.md.

Read-only SHA-256-verified backups and inventory: C:\Users\pruth\OpenClawPAD\failure_recovery\operator-stale-f1598-20261102. Includes original session, task, ledgers, protocol and wrapped blocked checkpoint. Controller-StaleSession.ps1 checks exact identity, original hash, verified backup, process probe and mutex; denies in-place writers, compares again and atomically replaces only the orphan claim. Same-volume original receipt retained at project_coordination/ACTIVE_SESSION.json.operator-replaced-original.json; immutable recovery-event.json records original/result hashes and monitoring_completed=false. Codex then acquired separate maintenance ownership normally. Read-only attributes and SHA-256 provide tamper evidence, not a WORM storage claim.

Two initial Windows File.Replace attempts failed without modifying the original claim: null backup marshalled to illegal path, then cross-volume replacement backup rejected. Both staged attempts preserved privately; fixed to same-volume backup. Final guarded replacement succeeded. No guard failure was bypassed.

Observed turn17 evidence: run315b7bd6-8d75-4d6a-912d-2aa0f2a54dc4 checkpoint is checksum-wrapped BLOCKED, not an empty record. Archived live stream158204bytes contains zero result events; captured_raw_output in checkpoint is empty. CLI debug log has no demonstrated terminal result. Converter preserves unrecognized nonempty streams. Historical evidence cannot prove whether upstream omitted the terminal envelope or capture lost it; no original separate stdout/stderr/native exit evidence exists. No scientific completion was manufactured.

Repair: Invoke-BoundedAgyProcess persists separate stdout/stderr incrementally, drains exit tails, writes process.json even on callback failure, preserves native and effective exit codes, stop reason, reader/input exceptions and drain status. Existing controller records terminal classification and checkpoint evidence before conversion handling. Missing result, empty stdout, reader failure and conversion loss are distinct. Empty/parse failures now reach the existing durable failure-report boundary instead of silently breaking the loop. Verified completed-receipt recovery and ownership rejection remain unchanged; no new controller or approval workflow.

Tests:127 PASS: stale7; output13; successor14; recovery42; completed recovery9; bootstrap26; failure handoff16. Includes active-owner rejection, hash mismatch, concurrent mutation rejection, repeat recovery rejection, actual child stdout/stderr/native exit capture, late exit output, callback exception persistence, missing terminal and successful conversion, no-replay accounting and existing failure handoff. Child processes were local fixtures only. Path-scoped diff check PASS.

Canonical/deployed controller SHA256452B0B15BF871E79B62E71E46DB06A2F8AC29EC5DCC13ED99FBE928C7438693D match; previous deployment privately backed up. Installed ControllerDryRun exits1, correctly refusing the historical BLOCKED checkpoint pending evidence-based reconciliation. This is a preserved safety gate, not a passing startup claim. No live AGY transaction was run.

F1598 remains the authoritative task; next_safe_action now requests evaluation of already-submitted Package1631419488 and preserved Package166-R3 evidence, no replay. max_new_pbs_submissions remains0. R3's accepted evidence and PBS receipts untouched. Current Package163 scheduler outcome was not queried and is explicitly unverified. Original HPC ledger, execution ledger and blocked controller checkpoint remain byte-identical to pre-maintenance backups.

SAFE_RESUME=NO for unattended loop: resolve interrupted monitoring checkpoint from authentic existing artifacts without fabricating a missing report or replaying the operation. Ownership is no longer blocked. Next research action is read-only evaluation of existing1419488 terminal status/results, then predeclared physical acceptance. Do not resubmit it. No automatic loop launch.

Source hashes:
scripts/controller/Antigravity-Autonomous-Loop.ps1: 452B0B15BF871E79B62E71E46DB06A2F8AC29EC5DCC13ED99FBE928C7438693D
scripts/controller/Controller-Recovery.ps1: 9236DAFE24CBCA34462B4DD4F7AE9F93A5C1232F9F53BBCE6B94B4E7D8D314FF
scripts/controller/Controller-StaleSession.ps1: 0A988001D105548BA7CBD48C9A451881EEBBD256BE650E95E0C78F9F454DED40
scripts/validation/Invoke-BoundedAgyProcess.ps1: 23EB7118AA93E969E4A1B74E324212FAFCBAE317D41C0D6D4BB9EF1FF0158761

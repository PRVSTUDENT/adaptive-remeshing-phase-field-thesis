# Antigravity controller source and deployment

`Antigravity-Autonomous-Loop.ps1` is the canonical source for the installed
`%USERPROFILE%\OpenClawPAD\Antigravity-Autonomous-Loop.ps1`. Edit this source,
run the offline regressions, then deploy it. Startup compares installed and
canonical SHA-256 values and rejects a mismatch before profile selection.
The controller loads its recovery, credential, policy and watchdog helpers from
the selected repository workspace; their hashes enter each turn checkpoint.

From the repository root:

```powershell
powershell -NoProfile -NonInteractive -File tests/unit/test_controller_recovery.ps1
powershell -NoProfile -NonInteractive -File scripts/controller/Deploy-Controller.ps1
& "$env:USERPROFILE\OpenClawPAD\Antigravity-Autonomous-Loop.ps1" `
  -InitialPromptFile "$PWD\.agents\INITIAL_PROMPT.txt" `
  -PrintTimeout 2400s -ControllerDryRun
```

Deployment preserves a timestamped installed-script backup and verifies the copy.
The dry-run reads coordination/checkpoint state and reports the resolved instruction,
source hash and budget. It makes no profile, AGY, bridge, SSH, PBS or scientific calls,
and writes no controller or coordination state. `active_session=true` during
maintenance is reported; a real dispatch will reject a foreign active session.

Run the affected existing regressions in separate PowerShell processes:

```powershell
powershell -NoProfile -NonInteractive -File tests/unit/test_agy_envelope.ps1
powershell -NoProfile -NonInteractive -File tests/unit/test_agy_policy.ps1
powershell -NoProfile -NonInteractive -File tests/unit/test_agy_credentials.ps1
powershell -NoProfile -NonInteractive -File tests/unit/test_agy_watchdog.ps1
powershell -NoProfile -NonInteractive -File tests/unit/test_controller_profile_guard.ps1
```

## Durable recovery

The authoritative runtime checkpoint is
`%USERPROFILE%\OpenClawPAD\controller_turn_checkpoint.json`. It uses an atomic
same-directory replacement, a previous-version file and a SHA-256 envelope. States:
`PENDING`, `RUNNING`, `CHECKPOINTED`, `RECOVERY_REQUIRED`, `COMPLETED`, `BLOCKED`.
Each checkpoint records task identity, last observed task classification, exact
source hashes, existing PBS IDs, complete once-only execution accounting, session
provenance, owned CLI PID, partial-output hash and next safe action. An observed
ledger status is evidence provenance, not independently revalidated science or a
live scheduler snapshot. New findings must be checkpointed by the research agent
in its session report after each substantive action; the controller snapshots
their file hashes every 15 seconds, including while stdin is backpressured.

The configured total budget is unchanged. At 2400 seconds, scientific execution
has a 2280-second deadline and 120 seconds are reserved for local reconciliation.
There is no immediate model closeout retry. A timeout kills only the owned CLI
process tree and preserves its partial output. A fresh completed receipt may
close the turn. Otherwise one **next controller turn**, in a fresh conversation,
may reconcile evidence/accounting only. This recovery turn prohibits submissions,
solver work and changed numerical assumptions. It returns its proposed next action
and ends the invocation for review; it cannot blindly replay the research prompt.
At the MaxTurns boundary recovery remains durably pending for a later invocation.

Only a newly claimed matching Gemini session from that invocation may be released
as interrupted. Foreign ownership, a still-live interrupted PID, corrupt or modified
checkpoint/partial evidence, incomplete recovery, or a second failed recovery blocks
execution. Preserve blocked checkpoint files and diagnose their concrete cause;
do not delete/reset them to force a replay. No permits or authorizations are involved.

Credential synchronization, PRE_AGY/POST_AGY verification, smart quota selection,
the per-user controller mutex and the governed HPC adapter remain in place.
Research progress must come from current coordination evidence, not a completed
task heading in `INITIAL_PROMPT.txt`. The prompt currently requests scientific
review of the unresolved transfer hypothesis, preserving Package 72's failed audit.

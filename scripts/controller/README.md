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

### Idempotent F1597 bootstrap and controlled validation

`Invoke-ControllerTurn.ps1 -Stage Bootstrap` is the canonical `-File` entrypoint.
It performs Git checks, reads the nine mandatory prerequisite files in order,
validates task/session state, claims the owned session and records source hashes
once under `project_coordination/controller/turn-<run-id>.json`. An unchanged
repeat returns `BOOTSTRAP_ALREADY_COMPLETE`; further repetition is diagnosed.
Changed relevant inputs require deliberate reconciliation. Raw repeated reads
and nested bootstrap `powershell -Command` calls are diagnosed from live events.
The failed real trace had stripped `$f`/`$files` variables in a nested command,
not a successful bootstrap followed by scientific work.

Closed task headings are rejected from TASK_LEDGER.csv before invoking the model,
including F1596 when ACTIVE_TASK.json now correctly names F1597. Bootstrap notes,
file reads and generic report length no longer count for F1597. A typed scientific
checkpoint must reference a hash-verified numerical artifact and all five pinned
sources, with finite measurements and a passed gradient verification.

For the controlled test only, the next stages are `Scientific` and `Complete`.
The first executes `probe_mode1_f1597_kkt.py` on the authentic mapped offsets using
the implemented frozen-history phase block. The second preserves the measured
KKT finding, records the next correction step, releases ownership and selectively
commits/pushes the bounded scientific result. It does not qualify state transfer.

`-ControlledSingleTurn -MaxTurns 1` requires this verified operation and clean
scientific closeout, then exits without a bridge or another research turn.
Credential resets and automatic profile restoration are forbidden in this mode;
existing read-only PRE/POST identity checks still apply. The 300-second guard and
2400-second maximum remain unchanged. Do not start a twenty-turn run to validate it.

### Saved-result deadline and live diagnostics

The long scientific budget is an upper bound for productive work. Independently,
`-NoProgressSeconds` defaults to **300** (range 30â€“600). A turn stops as
`NO_DURABLE_PROGRESS` if it saves no new result within that interval. Only changes
to the owned session report (at least 160 bytes) or HPC/execution accounting reset
this deadline. A session claim, a missing predecessor report, metadata timestamps,
source-code hashes, model tokens and step events do not count. This tests durable
artifact activity; it does not independently certify the scientific truth of a report.
The prompt requests the first finding/report within 120 seconds and subsequent
updates within 180 seconds. Mandatory bootstrap reads should be batched in order,
with relevant rows/hashes emitted instead of full historical-ledger dumps.

The CLI uses its actual `stream-json` event protocol. `[AGY]` shows conversation
identity and step state immediately; `[PROGRESS]` reports elapsed/no-result time
every 30 seconds. Exact raw events are written incrementally to
`%USERPROFILE%\OpenClawPAD\controller-turn-<run-id>.jsonl`, with a separate
`.cli.log`. These local files are not committed. Background .NET pipe readers and
an independent stdin writer keep blocked I/O off the watchdog thread. Timeout
checkpoints retain actual raw CLI output, not a fabricated routing envelope.

Session ownership binds a newly claimed Gemini session to the invocation's start
time, original inactive lock and repository commit, then freezes its fingerprint.
The live task can differ from the completed predecessor in ACTIVE_TASK.json.
Foreign sessions and changed ownership remain protected. Abnormal exit releases
only proven ownership after the owned CLI is gone.

No-result stalls become BLOCKED with no automatic model replay. Other verified
timeout recoveries use a fresh evidence-only turn capped at 180 seconds total.
Job-first instructions are active: submit independently ready qualified Mode-I
work immediately through the guarded adapter, while preserving scientific
predecessor acceptance and once-only accounting. A failed dependency never
justifies a redundant/filler submission.

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
task heading in `INITIAL_PROMPT.txt`. The prompt selects the next useful action under job-first governance, preserving
Package 72's failed audit and any scientific dependencies.

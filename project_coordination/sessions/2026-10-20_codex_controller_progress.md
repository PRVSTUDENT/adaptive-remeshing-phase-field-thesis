# Controller progress, streaming and ownership repair ? 20 October 2026

Agent: codex. Task: CONTROLLER-PROGRESS-OWNERSHIP.
Starting commit: 0447926f781031b1768df94fa85851ba03f5860f. Ending commit: the Git commit containing this report.

## Concrete failure

The real invocation ran 06:57:43?07:35:44 Berlin time and stopped BLOCKED because the checkpoint retained predecessor F1596 while the newly claimed Gemini session was F1597. ACTIVE_TASK.json still correctly recorded the completed predecessor. My previous test fixture used identical predecessor/session task IDs and missed this case. The old controller also used buffered JSON output and counted only checkpoint snapshots, not durable research results. Raw watchdog output was two bytes; a synthetic timeout envelope had then been stored as partial evidence. These were controller defects, not scientific progress.

Read the exact existing CLI log C:/Users/pruth/.gemini/antigravity-cli/log/cli-20261020_065744.log: repeated model requests; explicit server 503 'No capacity available for model gemini-3.8-flash-high' at 07:26:56 and 07:33:27. No F1597 session report was created. No independently verified scientific result or job submission is claimed from that run.

## Installed corrections

- Session ownership binds the initial inactive lock, newly claimed Gemini identity/time, repository starting commit and immutable claim fingerprint. It is independent of predecessor task identity. New F1597 is tracked even while ACTIVE_TASK still names completed F1596. Foreign/changed ownership remains blocked; abnormal exit releases only proven ownership after the owned CLI is gone.
- Default 300-second no-result deadline, independent of the unchanged 2400-second maximum scientific budget. Only changed owned reports (at least 160 bytes) or HPC/execution accounting count. Claims, removed predecessor reports, timestamps, source metadata and model chatter do not count. No-result stalls stop BLOCKED with no automatic replay. Useful longer work remains allowed when it saves results.
- Stream-json events show conversation/step state live, with status every 30 seconds. Per-invocation raw .jsonl and .cli.log files under OpenClawPAD retain actual output. Background .NET pipe readers and stdin writer keep blocking pipe I/O off the watchdog thread. Partial lines survive termination. Actual raw output is checkpointed rather than a synthetic routing envelope.
- Verified non-stall recovery is restricted to a short fresh evidence-only turn capped at 180 seconds total. Quota/error result envelopes preserve existing strict profile, cooldown and identity checks.
- Restored job-first instructions: independently ready qualified Mode-I work uses Invoke-Mode1Execution.ps1 immediately; no blanket review-only submission prohibition. Scientific dependencies, frozen UEL, guarded exact manifests, once-only receipts and resource/notification qualification remain mandatory. No filler job is justified by an empty queue.
- Bootstrap is requested as one ordered batched read returning current facts/relevant rows/hashes, avoiding dozens of model round trips and entire historical-ledger dumps. Request first result/report within 120 seconds and updates within 180 seconds; the controller actually enforces the 300-second saved-artifact deadline. Artifact changes are evidence of saved activity, not independent certification of their scientific truth.

Installed SHA256: `e419cd4cc819ad12aa1a1c3d6d134787447a45d567da351f3cc07c7dea37e9d9`; canonical source matches byte-for-byte. Production UEL remains `ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6`.

## Qualification evidence

Actual final console summaries:

```text
ALL 20 PROGRESS/OWNERSHIP CHECKS PASSED; no scientific jobs
ALL 25 CONTROLLER RECOVERY CHECKS PASSED; no real AGY or PBS calls
ALL PROFILE GUARD UNIT TESTS PASSED CLEANLY (6/6).
PASS: quoted stdin, stdout/stderr, nonzero exit, bounded timeout and termination
PASS: dual-window thresholds, reported reset, cooldown monotonicity, bounded prompts, fresh registered receipt, stale/active rejection
PASS: clean JSON, timeout suffix, leading warnings, unrelated objects, escaped strings, nested objects, and invalid/truncated rejection
PASS: isolated controller timeout handler saves partial evidence and schedules a fresh next recovery turn with zero immediate model calls
PASS: credential layouts and safe stage/source errors, observed expired-native format, restricted repair eligibility, private ACL and store mismatch rejection; only synthetic credentials used
```

All changed PowerShell sources parse. The new suite invokes the actual production dispatch assignment with a mock process claiming F1597 while ACTIVE_TASK remains F1596. It verifies capture/release, raw stream identity, partial output, no-progress stop and no replay. Continuous chatter is killed at the test's two-second deadline; logs exist before the process ends. Normal success, quota failure and partial-timeout streams use the real CLI's observed event/result schema. Existing twenty-turn lifecycle and actual loop-bound checks pass. Mock owned process trees leave no descendants.

Final progress fixture: C:/Users/pruth/AppData/Local/Temp/agy-progress-test-0c221994b8ab49f78fa4c2119adffa1d. Recovery fixture: C:/Users/pruth/AppData/Local/Temp/agy-controller-test-0b41fa19428e4b8a83e58144dba60011.

Local failure/repair evidence: an initial StreamReader.ReadAsync implementation could delay small chunks until buffering filled; replaced it with background base-stream readers and a dedicated stdin thread, then the live-log/deadline tests passed. Old timeout mocks run via -File had intermittent startup delays and missing PID files; existence guards were added and equivalent -Command mocks passed with bounded deadlines. These were test/preparation failures, not resubmitted HPC jobs. No external capacity problem was declared solved by mock tests.

One bounded technical CLI connectivity test in an isolated backup directory returned a real stream result ERROR 'Individual quota reached', reset 98h24m26s. It ran no tools/scientific task, changed no repository files and was not retried. Raw evidence lives under C:/Users/pruth/OpenClawPAD/backups/controller_progress_20261020/smoke-output.txt and smoke-cli.log. External server capacity/quota can still block a model run; the corrected controller must surface that explicitly. No subscription/activation request was introduced.

## Reconciliation and authorized launch

No agy process remained before maintenance. User's permanent-repair request authorizes reconciliation of the terminated F1597 session. Original active lock, controller, blocked checkpoint and raw watchdog log were preserved at C:/Users/pruth/OpenClawPAD/backups/controller_progress_20261020/. The exact blocked checkpoint was also archived as controller_turn_checkpoint.json.ownership-defect-a8a27a08-e962-4731-94d1-6e309df8efc1.json. Both HPC_JOB_LEDGER.csv and MODE1_EXECUTION_LEDGER.json SHA256 values were checked unchanged against the old checkpoint before migrating only the proven ownership defect to a new qualified PENDING instruction. Existing PBS IDs and execution reservations were not reset. F1597 is interrupted with no saved report, not marked scientifically completed. ACTIVE_TASK.json remains intact.

All unrelated pre-existing dirty files, including dirty HPC/execution ledgers and science/thesis/handoff artifacts, remain untouched and unstaged. Only listed maintenance paths and coordination additions are governed here. No HPC commands or jobs were run during repair. No notifications, formulation, resource limits, production UEL, credentials or submission permits were changed.

The user subsequently explicitly requested starting the exact 20-turn controller command after repair. After commit/push and normal lock release, launch it as a hidden detached PowerShell process with persistent stdout/stderr and a receipt under OpenClawPAD/controller-run-*.json. Preserve MaxTurns=20, PrintTimeout=2400s, smart profile selection=true, quota check every turn and threshold 20. Do not launch a duplicate existing controller. Inspect startup read-only and record the process/log receipt in the final response. The agent then owns coordination; do not edit project files concurrently. Startup success is not a claim of a completed scientific turn.

## File hashes

- `.agents/INITIAL_PROMPT.txt` SHA256 `2f911e031420232e1356dd175f1b32753293af95addb959fc1b7df497dfca38f`
- `scripts/controller/Antigravity-Autonomous-Loop.ps1` SHA256 `e419cd4cc819ad12aa1a1c3d6d134787447a45d567da351f3cc07c7dea37e9d9`
- `scripts/controller/Controller-Recovery.ps1` SHA256 `895ad9c6ca4d0e45ea643ec120b43edccf979c989af31ed5067d286fd6ffc5fd`
- `scripts/controller/README.md` SHA256 `1f4f9c02bea3322f85492c470577713c5bd70798f23d2ed821398c96b7ec1b30`
- `scripts/validation/Invoke-BoundedAgyProcess.ps1` SHA256 `23875f5536b37d062f868dd89831755a4416d2ecec3a6e6b86d189af0382b5ba`
- `tests/unit/test_controller_recovery.ps1` SHA256 `e9b98ff86e194aa2d3a93af38781c4147ca6fdb05fde918b61eafd95809def75`
- `tests/unit/test_controller_progress.ps1` SHA256 `96913b55f148835416391bec959e69b0fd57a98f2bab831c6ba5a9d91056b65a`

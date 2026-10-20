# Antigravity controller durable recovery maintenance ? 20 October 2026

Agent: codex
Task: AGY-DURABLE-RECOVERY
Starting commit: a81b7b50f4515cf3ba8925fe6677ba6cdbc31f1b
Ending commit: the commit containing this report (resolve with `git log -1 --format=%H -- project_coordination/sessions/2026-10-20_codex_controller_recovery.md`).

## Finding and repair

The installed controller loaded the explicit initial prompt ahead of saved state. That prompt repeated F1596 although ACTIVE_TASK.json already classified its Package 72 audit completed and scientifically failed. Both the CLI print-timeout handler and watchdog handler unconditionally broke MainLoop without a fresh released-session receipt. MaxTurns therefore provided no recovery. Increasing the deadline did not correct either control-flow defect. Profile verification in the supplied log had passed; this was not evidence of exhausted quota or authentication failure.

Canonical controller source now lives in scripts/controller. Installed startup verifies exact source equality. The deployment script preserves an installed backup and checks SHA-256. Initial prompt now resolves NEXT_UNRESOLVED from authoritative coordination and requests only a bounded review of the failed transfer hypothesis. It does not repeat the completed audit or authorize changed scientific assumptions.

Added atomic checksum-protected PENDING/RUNNING/CHECKPOINTED/RECOVERY_REQUIRED/COMPLETED/BLOCKED state, periodic source/report hash checkpoints, exact observed PBS IDs, full once-only execution accounting, owned PID, partial-output hash, and next safe action. Saved pending next instructions take precedence on resume. Corrupt state/evidence fails closed. Ledger labels are recorded as observations, not freshly independently validated science.

Scientific work has a controller-enforced 2280-second deadline within the existing 2400-second total, reserving 120 seconds for local closeout. No timeout increase. Both timeout paths preserve evidence and permit one fresh next-turn evidence-only reconciliation rather than replaying the research prompt. That recovery prohibits solver/submission/numerical changes and ends the invocation with its proposed next action. Second timeout, incomplete recovery, foreign session ownership, or a still-live interrupted PID blocks. Verified fresh completed receipts preserve work even when Finished is missing. Normal PRE_AGY/POST_AGY, credential synchronization, smart quota and per-user mutex protections remain.

The watchdog now checkpoints while stdin is backpressured, cleans up its owned tree on callback failures, and collects actual exit/output if the child closes stdin early. No free-form scheduler mutations were added.

## Session reconciliation and preservation

User explicitly authorized reconciliation of the stale Gemini lock. Before claiming, no agy.exe or Antigravity.exe process existed; PID 24772 was the idle VS Code PowerShell terminal, not the controller. The stale lock named F1596, starting commit a81b7b50f4515cf3ba8925fe6677ba6cdbc31f1b, claimed_at 2026-10-20T05:52:00+02:00, last_updated the same, last_released 2026-10-19T18:47:00+02:00, session_report project_coordination/sessions/2026-10-20_gemini-antigravity_f1596_package72_state_transfer_audit.md. That October-20 report was not invented or treated as existing completion evidence. Actual authoritative task and prior completed audit remain intact.

807 pre-existing dirty/untracked paths were found. All unrelated paths remain untouched and unstaged, including dirty HPC/job/execution ledgers, science packages, thesis outputs and legacy agent_handoff. INITIAL_PROMPT.txt was intentionally replaced as requested; its pre-maintenance bytes and the original installed controller are preserved at C:/Users/pruth/OpenClawPAD/backups/controller_recovery_20261020/. Original installed controller SHA256: f5ff2c979b094ba9690839a408bfe636b56593c712f94217b22c872b9dd3b087.

## Verification

Actual console results:

```text
ALL 25 CONTROLLER RECOVERY CHECKS PASSED; no real AGY or PBS calls
ALL PROFILE GUARD UNIT TESTS PASSED CLEANLY (6/6).
PASS: clean JSON, timeout suffix, leading warnings, unrelated objects, escaped strings, nested objects, and invalid/truncated rejection
PASS: isolated controller timeout handler saves partial evidence and schedules a fresh next recovery turn with zero immediate model calls
PASS: dual-window thresholds, reported reset, cooldown monotonicity, bounded prompts, fresh registered receipt, stale/active rejection
PASS: credential layouts and safe stage/source errors, observed expired-native format, restricted repair eligibility, private ACL and store mismatch rejection; only synthetic credentials used
PASS: quoted stdin, stdout/stderr, nonzero exit, bounded timeout and termination
```

Commands: test_controller_recovery.ps1, test_controller_profile_guard.ps1, test_agy_envelope.ps1, test_agy_policy.ps1, test_agy_credentials.ps1 and test_agy_watchdog.ps1 under tests/unit, each in a separate `powershell -NoProfile -NonInteractive -File` process. Parsed every changed PowerShell file with the PowerShell AST parser. Deployment independently rechecks installed bytes. Installed -ControllerDryRun returned DRY_RUN_NO_EXECUTION, completed F1596 predecessor, NEXT_UNRESOLVED review instruction, total 2400/work 2280/closeout 120, no real runtime checkpoint created. During maintenance it correctly reported active_session=true. A second installed dry-run after release passed with active_session=false and final installed SHA256 afc344eccc3cc2e7503b879296e981c6a5f66fef2df372138605a1ba40d681b5.

The lifecycle test executes twenty real mock PowerShell children, observes the actual production loop bound, and executes the production timeout AST against fixture ledgers. It tests partial preservation, one recovery, explicit BLOCKED on repetition, owned/foreign sessions, tamper rejection, missing Finished receipt salvage, exact IDs and no submission-accounting changes. A real mock child process tree was terminated without orphaned descendants. These are offline controller/credential tests; they do not claim live AGY service, PAD bridge, scheduler or notification end-to-end qualification.

Test evidence fixture: C:/Users/pruth/AppData/Local/Temp/agy-controller-test-9467d687037047f9b23f0874a972fd65 (preserved outside Git).

Initial local test failures preserved in conversation/tool output: .NET File.Replace rejected PowerShell null backup (changed to an explicit .previous checkpoint); fast child stdin closure raised an async IO error (now collect exit/output); stdin backpressure initially prevented periodic checkpoints (now poll with bounded waits). A short mock deadline could elapse during process startup before a periodic callback; an initial checkpoint now runs after owned PID capture. Obsolete regression assumptions expected immediate timeout exit and no closeout reserve; updated to test the new requirements. All affected checks then passed. Three inherited whitespace-only lines were normalized before final deployment; no scientific code changed.

## Files, hashes and next action

Files read: ordered mandatory coordination/bootstrap files, AGENTS.md supplied by user, active task/session, exact controller, watchdog, envelope/policy/credential helpers, affected tests, pasted failure request, current prompt and registry. Scope: the files listed below plus session/coordination metadata. No bridge or credential implementation changes were needed.

Installed controller SHA256: `afc344eccc3cc2e7503b879296e981c6a5f66fef2df372138605a1ba40d681b5`.
Frozen production UEL SHA256 remains `ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6`.

- `.agents/INITIAL_PROMPT.txt` SHA256 `a551cddec5c03c6e657e28b6702d6ddfe3f3c13096a5a67769dff0fa0fd04a49`
- `scripts/controller/Antigravity-Autonomous-Loop.ps1` SHA256 `afc344eccc3cc2e7503b879296e981c6a5f66fef2df372138605a1ba40d681b5`
- `scripts/controller/Controller-Recovery.ps1` SHA256 `1dbabf6bf92563375e138e7fcfcaa0a498d1c4266b5a99d22e359f5b1f78a912`
- `scripts/controller/Deploy-Controller.ps1` SHA256 `9651fc9a3a937f177bed934fa2f42bc54c7c9d9d79feb3d0c45a96de2ff27949`
- `scripts/controller/README.md` SHA256 `893c75ab5b573e4691cf9be05fc59806f3652adffe0fc6d0c020adc07b89f0a9`
- `scripts/validation/Invoke-BoundedAgyProcess.ps1` SHA256 `4a53f13be379e6638264bdc5318c51893365e6f2af75053616c748efeb5445c1`
- `tests/unit/test_controller_recovery.ps1` SHA256 `5062b0ce4058137b9b7a24984aa7055998c1691984a5c5c52a033d0d4cdd9222`
- `tests/unit/test_agy_envelope.ps1` SHA256 `cf2917e827fa46e91f0c00abfdd35404c151de2cf5031b5cb8aa7d4a09a9c9d6`
- `tests/unit/test_agy_policy.ps1` SHA256 `dcb62dd5d8376091463f32a084bc85235539e21c5317602986449c9d2a76c251`

HPC commands: none. Jobs submitted: 0. PBS IDs created: none. Existing PBS receipts were read only or synthetic fixture values. Authorization changes: none. Scientific changes: none. Package 72 remains FAILED; forward transfer cycles remain on scientific hold. ACTIVE_TASK.json intentionally retains the scientific predecessor rather than being replaced with a maintenance task.

Exact next action: run the installed controller with -ControllerDryRun and the current INITIAL_PROMPT.txt after lock release. Its resolved instruction is a bounded scientific review, not a rerun of F1596. No 20-turn research loop was started. Keep backups and partial runtime logs; never reset once-only accounting.

Remote synchronization: current worktree branch is mode2-pandey-kumar-reproduction. origin/main was verified as an ancestor before maintenance; publish this commit to origin/main by forward-only HEAD:main and synchronize the existing source branch too. Git commit/push receipts are reported in the final response; do not amend to add self-referential commit hashes.

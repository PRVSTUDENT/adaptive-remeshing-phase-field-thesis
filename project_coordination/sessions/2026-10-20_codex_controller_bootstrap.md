# Idempotent bootstrap and scientific checkpoint validation ? 20 October 2026

Agent: codex. Task: CONTROLLER-IDEMPOTENT-BOOTSTRAP.
Starting commit: 361a252230ec6f1af64f10c5c828746f74b81ff4. Ending commit: the commit containing this report.
Status at engineering commit: implementation qualified; exactly one live controlled turn remains to be evaluated. No success is claimed from startup alone.

## Failed-turn evidence and diagnosis

Inspected the immutable live stream controller-turn-b6500783-1452-4aac-a804-08936a8786a1.jsonl and the read-only steps table in C:/Users/pruth/.gemini/antigravity-cli/conversations/d4f84912-488c-4d99-b5fe-b96babe95554.db. Read tool payloads only; no agent private reasoning was used. The compact stream truncated tool arguments and omitted stdout; full SQLite payloads exposed the actual errors.

- Step 2: exit 1. The first multi-line nested powershell -Command bootstrap was parsed with `foreach ( in )` and `if ()`, reporting MissingVariableNameAfterForeach and ParserError. Outer expansion removed `$f`/`$files` before the child parsed them. The entire script failed to parse, so its intended ordered file read did not complete.
- Step 4: exit 0, reread ACTIVE_SESSION.json, ACTIVE_TASK.json, CURRENT_STATE.md and Git state.
- Step 6: exit 0, reread ACTIVE_SESSION.json and ACTIVE_TASK.json again, with no relevant state change.
- Step 8: reported exit 0 but also `/usr/bin/tail: cannot open '5'` and `/usr/bin/head: cannot open '30'`; attempted START_HERE, ledger/registry tails and the phase checklist. Tool-DONE/zero exit did not mean the intended bootstrap succeeded completely.
- No tool call claimed a project session, wrote a scientific checkpoint, invoked a numerical operation or submitted a job. ACTIVE_SESSION remained the released maintenance session. This establishes the concrete parser failure and unrecorded/repeated bootstrap behavior; it does not claim knowledge of the model's internal reason for repeating reads.

## Repair

Added one canonical Invoke-ControllerTurn.ps1 -File entrypoint, with Bootstrap, Scientific and Complete stages. Bootstrap implements Git checks and the exact ordered prerequisite reads, validates/claims the session and records hashes once per controller run ID under project_coordination/controller/. Unchanged repeats return ALREADY_COMPLETE and then BOOTSTRAP_LOOP; changed relevant inputs are diagnosed. Live events reject generated nested bootstrap -Command calls and repeated raw prerequisite reads after completion.

ACTIVE_TASK now explicitly names F1597-CORRECT-PACKAGE72-STATE-TRANSFER, retaining F1596's completed failure as predecessor. Closed task headings are rejected from TASK_LEDGER before model invocation. A completed F1597 diagnostic is also removed from the executable-operation slot after closeout so a later turn cannot silently replay it as a new correction.

F1597 requires a typed numerical checkpoint with finite measurements, a passed finite-difference verification and matching artifact/source hashes for all five pinned sources. Generic bootstrap/status notes, file reads and timestamp updates do not count as scientific progress. The five-minute guard and 2400-second maximum were not increased.

The first bounded scientific operation is new F1597 work: reconstruct the initialized phase block from Package72's authentic offset table and mesh with frozen committed H, then measure lower-bound KKT feasibility and verify its gradient by central finite differences. It is not a rerun of F1596's force/energy audit. At the mapped lower bound, the criterion is gradient >= 0; requiring an unconditional zero phase residual is not generally the active-constraint KKT condition. The diagnostic does not implement or qualify a corrected coupled transfer, does not update H from mechanics and does not alter input decks or UEL sources.

Complete verifies/preserves evidence, advances the next correction step, releases the owned session and selectively commits/pushes its exact outputs. ControlledSingleTurn requires MaxTurns=1, checks scientific operation/closeout/remote synchronization, and exits without bridge escalation or another model invocation. Credential reset/synchronization or automatic profile restoration is prohibited in this mode; read-only PRE/POST identity verification is retained. A real read-only check of current account3 stores passed, with no credential modifications.

Installed controller SHA256: `e3ad9ea26291ad10ffe7bf6202b5dfd5e87f538395ad17ba9585abd5ffa1e7e4` (same as canonical bytes).
Production UEL remains `ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6`.

## Tests and preparation failures

Actual results before the controlled live invocation:

```text
ALL 20 BOOTSTRAP CHECKS PASSED; fixture only
ALL 20 PROGRESS/OWNERSHIP CHECKS PASSED; no scientific jobs
ALL 25 CONTROLLER RECOVERY CHECKS PASSED; no real AGY or PBS calls
3 passed in 0.20s (F1597 numerical kernel tests; numerical_tests_exit=0)
ALL PROFILE GUARD UNIT TESTS PASSED CLEANLY (6/6).
```

Affected envelope, quota/policy and synthetic credential regressions also passed. Changed PowerShell sources parsed, and scoped whitespace checks passed. Full Bootstrap -> Scientific -> Complete was exercised against a manufactured one-quad mesh and isolated bare Git remote, including source/hash validation, generic-note rejection, tamper rejection, ownership release, selective commit and forward push. No actual Package72 numerical operation was run in those fixture tests.

Final bootstrap fixture: C:/Users/pruth/AppData/Local/Temp/agy-bootstrap-test-5e4b7d03981f45199348f5e2c9a75be5.
Local test repairs were evidence-driven: exact write-scope concatenations were parenthesized to avoid split path fragments; a JSON property-count assertion was corrected; optional last_updated is added explicitly; metadata/result writes use LF; a path TrimEnd overload was made explicit; bounded local subprocess capture is used instead of trusting an unset outer-shell LASTEXITCODE. Manufactured full closeout then passed. These were local tests/preparation, not solver retries.

## Preservation and next controlled step

The earlier BLOCKED no-result checkpoint was preserved as controller_turn_checkpoint.json.bootstrap-defect-b6500783-1452-4aac-a804-08936a8786a1.json. Exact HPC_JOB_LEDGER and MODE1_EXECUTION_LEDGER hashes were checked unchanged before preparing a new qualified PENDING F1597 instruction for this identified technical defect. No PBS accounting was reset. All unrelated dirty paths, historical failures, Package72 inputs/results and legacy handoffs remain untouched and unstaged.

After engineering commit/push and lock release, run exactly one real CLI turn with MaxTurns=1, ControlledSingleTurn, unchanged PrintTimeout=2400s and NoProgressSeconds=300, pinned current account3 with smart rotation disabled. This is the user-authorized controlled validation, not a twenty-turn run. Record its runtime receipt and evaluate actual Bootstrap/Scientific/Complete artifacts and clean exit. If external service or numerical evidence blocks it, report that outcome rather than calling startup success. No HPC job or simulation is part of this bounded diagnostic. A post-validation addendum will record the actual result.

## Governed hashes

- `.agents/INITIAL_PROMPT.txt` SHA256 `b2d4d8cd7b858d7033c2eb9ea870eb5b377525f5d24c599efc0241947b25b7da`
- `scripts/controller/Antigravity-Autonomous-Loop.ps1` SHA256 `e3ad9ea26291ad10ffe7bf6202b5dfd5e87f538395ad17ba9585abd5ffa1e7e4`
- `scripts/controller/Controller-Recovery.ps1` SHA256 `5b16ef1a5b4b8bff66e0a22e71debf1eb67e3c95f4774a324815eaf1943bd4dd`
- `scripts/controller/Invoke-ControllerTurn.ps1` SHA256 `266d1f5a1cc4d2f6f69b94315e722477f49f4cbd81cb65eeda678f43a5d77bae`
- `scripts/controller/README.md` SHA256 `c661573d10233cc6de4ae3defe92b7c7314820f4778216a9ae19a4cd16f19116`
- `scripts/validation/probe_mode1_f1597_kkt.py` SHA256 `8d2942ebf7cbf3b05878e9e9c9154abf3c07206043e44bc6e25c3b8f576ac9ff`
- `tests/unit/test_controller_bootstrap.ps1` SHA256 `8f16b8167db26ccd6e12767d533de7904275b19ff8b743e4a3c31827fec377f6`
- `tests/unit/test_controller_recovery.ps1` SHA256 `82b85b985527aacfa8827d0c61d314a9f3ff9d9a5607df636d27035507037ed8`
- `tests/unit/test_mode1_f1597_kkt_probe.py` SHA256 `e293b754187531aaff51f19010cc7006aa093ba6d5c39942a0f7fa4121b08bcf`

## Actual single controlled turn ? final validation outcome

Exactly one real model turn was launched, PID 10740 / owned CLI PID 2400, conversation 0bcb0907-25b4-4b84-abed-3ae9756d7138, controller run 91e48944-19c2-4e7a-b3bc-57609b2f6bda. MaxTurns=1, ControlledSingleTurn, PrintTimeout=2400s and NoProgressSeconds=300; current account3 was pinned, automatic profile rotation and bridge disabled for this test. No credential reset and no second model turn were performed.

Observed:

1. Bootstrap completed at 11:38:24.610 Berlin time, once, repeat_count=0; nine prerequisite source hashes were recorded and F1597 ownership acquired.
2. Scientific stage completed at 11:40:01.973. Authentic 650-element/713-node offset data produced phase residual infinity norm 1.30993460639695e-13 and lower-bound KKT violation 1.30993460639695e-13 in the implemented phase block's nominal kN units. There were zero gradient-sign violations at the 1e-12 counting tolerance and zero mapped nodal damage inconsistency. Central finite-difference gradient error was 4.24788869579856e-14. The controller independently accepted artifact/source hash verification and reset the progress clock only for this numerical checkpoint.
3. Complete released ownership, recorded the next correction step, committed and forward-pushed to origin/main and the source branch. Scientific commit: 0720bbd1901eb17fb932f0fa4412d5bc34343dfd. ACTIVE_TASK now says F1597_KKT_DIAGNOSTIC_VERIFIED_CORRECTION_PENDING, with the completed diagnostic removed from its executable-operation slot. No transfer qualification is claimed.
4. CLI emitted final result SUCCESS at 11:45:04, but the controller then failed strict POST_AGY native-store verification. The native credential entry lacked ID-token identity metadata; CLI-file identity still matched saved account3. Read-only equality/provider checks did not establish the native entry's identity. This is not evidence that a different user executed the science. No credential mutation, profile switch/reset, trust relaxation or bypass was used to clear the failure. Controller exit was not a clean full pass: runtime remains BLOCKED for further model calls. The verified scientific step is separately marked completed and preserved; it must not be replayed.

Therefore: the bootstrap/scientific-execution success criterion is demonstrated on the real agent, but the clean end-to-end exit criterion remains blocked by post-run native identity verification under the explicit no-reset constraint. Do not call the entire validation passed. No reset-based repair is permitted in this task, and the available read-only checks did not unblock the native identity check; no additional research run was launched.

The initialized frozen-history phase block is already nearly stationary, which narrows the next F1597 investigation to mechanical/history updating and UEL call ordering during re-equilibration. This does not establish a cause for the earlier coupled force/energy failure by itself, and it does not repair or qualify transferred state.

Evidence:

- project_coordination/controller/turn-91e48944-19c2-4e7a-b3bc-57609b2f6bda.json
- results/validation/mode1_f1597/91e48944-19c2-4e7a-b3bc-57609b2f6bda.json (SHA256 c3d9b0817bec007579351d1442e2616a766803c7ffe2e4845fd36d86422d182a)
- project_coordination/sessions/2026-10-20_gemini-antigravity_F1597_91e48944-19c2-4e7a-b3bc-57609b2f6bda.md
- C:/Users/pruth/OpenClawPAD/controller-run-controlled-bootstrap-20261020_113645.stdout.log and stderr.log
- C:/Users/pruth/OpenClawPAD/controller-turn-91e48944-19c2-4e7a-b3bc-57609b2f6bda.jsonl

The original post-check BLOCKED checkpoint is archived as controller_turn_checkpoint.json.post-identity-91e48944-19c2-4e7a-b3bc-57609b2f6bda.json. The current checkpoint retains BLOCKED, adds scientific_step_completed=true and the scientific commit, and records the exact independent validation outcome. There are no running AGY/controller processes and no orphan project lock. No HPC commands or submissions occurred.

The final local diagnostic-only code change preserves the scrubbed normalization source/stage in controlled-mode errors. A synthetic regression proves zero profile-switch calls, unchanged credentials and no leaked token values for controlled POST failure. Its console result: PASS: controlled POST mismatch preserves exact diagnostic, performs zero profile switches and leaves synthetic credentials unchanged. This fix was tested locally, not with a second model turn. No credential-guard logic was relaxed. Final installed/canonical controller SHA256: d916ee3c0de439a00012bf8a7851616ac20bbbf6dbba274b709137d328f389b1.

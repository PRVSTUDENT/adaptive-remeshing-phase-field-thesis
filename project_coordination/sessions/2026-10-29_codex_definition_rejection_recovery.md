# Automatic ChatGPT correction after operation-definition rejection

Task: CONTROLLER-DEFINITION-REJECTION-RECOVERY. Starting commit: 0359d0b8c840074d8ada54fbd40b4d7f26441273. Date: 2026-10-29.

The actual Turn322 log shows bridge success followed by NEXT_OPERATION_PREPARATION DEFINITION_REJECTED. The preserved next instruction contains the prohibition "No waiting, duplicate submissions, qdel or qmove." Controller-Preparation.ps1 rejects literal qdel/qmove tokens even in a negated prohibition. This is the demonstrated immediate trigger, not the 3488-character reply length. The existing validator was left unchanged.

## Changes

- Added scripts/controller/Controller-DefinitionRecovery.ps1: checksummed durable outbox with atomic writes, per-ledger mutex, stable rejected-successor chain identity, original/corrected proposals, exact rejection reasons, consultation prompts, handoff IDs, response evidence, attempt reservations and actionable stop reasons. Default production state: USERPROFILE/OpenClawPAD/definition_recovery_state.json. Maximum two consultations per rejected successor chain, including across restarts. Normalized identical proposals and rejection fingerprints cannot be dispatched again, including under another run key for the same task.
- Canonical Antigravity-Autonomous-Loop.ps1 now preserves a rejected successor before consultation, sends its evidence through the existing automatic ChatGPT bridge, and reruns the original preparation validator on a correction. Startup also reconciles rejected durable successors before ordinary instruction resolution. Non-definition preparation/authentication blockers keep their stop behavior. No rejected proposal is routed to AGY execution.
- Recovery handoffs contain the original rejected instruction, current rejection, exact status/reasons, approved task ID, available registry/qualification definitions, completed operations, matched guard tokens, constraints and attempt number. A corrected instruction must cite an existing allowed OPERATION_ID and still pass the original validator. The existing research_preparation workflow grants no solver/submission qualification. Missing review/registration produces an explicit stop, never self-authorization.
- Extended existing Invoke-ChatGPTBridgeWithManualFallback with optional stable HandoffId and SingleDispatch parameters. Ordinary callers retain prior behavior. Definition recovery uses one automatic bridge dispatch per durable reservation, no manual fallback and no transport resend. Authentication/service exceptions propagate to the existing fail-closed path.
- A restart after an uncertain send does not redispatch. A uniquely matching archived bridge response can be recovered only with the exact handoff ID and OK status, then revalidated. Otherwise recovery stops with the handoff ID and ledger path for reconciliation. Cached accepted corrections are revalidated and reused without another bridge request or ledger write. Existing research/HPC execution accounting is untouched; once-only submission guards remain authoritative.

## Verification

All tests used fixtures, mocked bridge/AGY/PBS, and local scripts. No real ChatGPT handoff was sent and no autonomous loop was started.

- test_controller_definition_recovery.ps1: 33 checks PASS. Covers rejection/correction, original context, two-attempt exhaustion, identical proposals/fingerprints, cross-key duplicates, restart with cached correction, interrupted durable dispatch, authenticated archive reply recovery, unknown-operation rejection, explicit review/security/authentication stops, corruption, actual production wrapper, actual NEXT_OPERATION_PREPARATION handler, actual startup recovery block, and one validated successor dispatch in the simulation.
- test_controller_recovery.ps1: all 42 checks PASS.
- test_controller_preparation.ps1: 11 checks PASS.
- test_controller_operations.ps1: 9 checks PASS.
- test_controller_continuous_research.ps1: all 45 checks PASS, including dynamic qualification and once-only completion/replay restrictions.
- Total: 140 checks PASS. PowerShell parsing and git diff --check passed.

Simulated end-to-end output:

```text
SIMULATED_DRY_RUN: initial=DEFINITION_REJECTED; consultations=1; corrected=READY; unapproved_executions=0; validated_successor_dispatches=1
```

Initial test harness failure was caused by an assertion writing PASS text into the mocked bridge reply pipeline. Suppressing that assertion output fixed the test harness; the failed fixture was retained. Production bridge logic was not weakened to accommodate it.

## Deployment and preservation

Canonical and installed persistent controller hashes match:
3948CDA199BF74D6678582DE451BA49A279EA6D1C238777813CC37DFC439C210.
Deployed with scripts/controller/Deploy-Controller.ps1 while holding the existing controller mutex. The controller imports the new canonical helper from the repository; no generated request files were edited.

Original installed controller, controller checkpoint, loop-state file and ACTIVE_SESSION were saved without overwrite under:
C:/Users/pruth/OpenClawPAD/backups/definition-recovery-d92c3b3805724175af5fdfad2f1273e9.
manifest.json records original paths and SHA256 values; backup copies have read-only attributes. Production checkpoint and loop-state hashes are unchanged. No real definition-recovery outbox existed or was created during the simulation. The original rejected Turn323 instruction remains preserved in the production checkpoint and will be corrected via the new path on the next normal invocation. ACTIVE_SESSION is restored to its original inactive bytes after closeout. Pre-existing dirty/untracked research files are preserved.

No qsub/qdel/qmove, remote HPC query, new experiment, account/profile change or VPN change was performed. Jobs 1418753.mmaster02 and 1418768.mmaster02 were supplied by the user and preserved without independent status polling in this controller repair. All scientific tolerances and failures, including Package113's cross-mesh energy gate, remain unchanged.

## Next action

The operator may resume the existing controller normally. Its pending rejected successor will trigger the new bounded ChatGPT correction workflow. No ForceResume or checkpoint reset is needed. A read-only -ControllerDryRun still reports the validator's present rejection without actually contacting ChatGPT; the simulated test above verifies the automatic consultation path. Truly missing review/registration, exhausted budget, uncertain bridge dispatch, authentication/service failures, or explicit security restrictions stop safely with persisted diagnostic evidence.

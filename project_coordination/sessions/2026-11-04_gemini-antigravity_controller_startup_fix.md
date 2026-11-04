# Controller Startup Fix: Elimination of Stale Historical Recovery Blockers

**Date**: 2026-11-04  
**Agent**: gemini-antigravity  
**Task**: F1606-MODE1-C6-R7-NONCONVERGENCE-INVESTIGATION (controller startup repair)  

## 1. Problem & Root Cause

The autonomous loop startup failed closed at `Controller-Recovery.ps1:1130` with `BLOCKED: original historical checkpoint identity mismatch`.

Root cause breakdown:
1. **Historical Checkpoint State Restriction**: `Controller-Recovery.ps1:1130` checked that `$original.state` in an archived checkpoint was in `@('BLOCKED','RUNNING')`. However, watchdog-interrupted turns can be interrupted while in `'PENDING'` or `'CHECKPOINTED'` states. For completed task `F1604` (run `15fbf6cd-f1ee-4a4c-bc58-f657e7b19191`), the archived checkpoint had `state = "PENDING"`, triggering the mismatch exception.
2. **Coupling of Normal Startup to Deep Historical Recovery Revalidation**: In `Antigravity-Autonomous-Loop.ps1`, lines 256, 262, 277, and 289 called `Assert-ControllerDispatchCheckpoint`. This function re-validated old recovery records and disk hashes against prior bootstrap records on every new autonomous turn, even after the predecessor task was fully completed, verified, and committed.
3. **Successor Checkpoint Plan Commit Resolution**: In `Controller-TaskLifecycle.ps1`, `Get-ControllerSuccessorCheckpointPlan` expected `source_commit` and `checkpoint_sha256` to be nested strictly under `definition.predecessor`, failing when the bindings were held under `task.predecessor_task` or pinned in `evidence_sources`.

## 2. Implemented Bounded Corrections

1. **`scripts/controller/Controller-Recovery.ps1`**:
   - `Assert-ControllerDispatchCheckpoint`: Added a fast exit if the checkpoint is marked `COMPLETED` and belongs to an earlier completed task (`$State.task_id -cne $activeTask.task_id`), avoiding re-evaluation of archived predecessor records.
   - Reconciled state validations (`COMPLETED_*_RECONCILED`, `INTERRUPTED_TURN_*`): Expanded allowed original states to `@('BLOCKED','RUNNING','PENDING','CHECKPOINTED')` and scoped original run-ID equality to `$expectedRunId = if($r.run_id){$r.run_id}else{$State.run_id}`.
   - Added `Assert-ControllerStartupCheckpoint([string]$Workspace, $State)`:
     * Checkpoint integrity: Fails closed immediately on `BLOCKED` checkpoints requiring reconciliation.
     * Session ownership: Fails closed if foreign active session exists.
     * Task lifecycle: Validates active task definition, predecessor closure, and single-open task rule.
     * PBS once-only / zero-submission rules: Verifies `max_new_pbs_submissions: 0` tasks contain zero PBS jobs in checkpoint, and checks against duplicate submission of completed PBS jobs.
     * Interrupted turns: Only invokes deep dispatch assertion if the checkpoint represents an incomplete turn belonging to the current active task.
   - `Write-ControllerCheckpoint`: Safely checks for existing `updated_at` property or uses `Add-Member -Force` to avoid `ExceptionWhenSetting`.

2. **`scripts/controller/Controller-TaskLifecycle.ps1`**:
   - In `Get-ControllerSuccessorCheckpointPlan`, added fallback resolution for `source_commit` and `checkpoint_sha256` from `$task.predecessor_task` and `$r.definition.evidence_sources`.

3. **`scripts/controller/Antigravity-Autonomous-Loop.ps1`**:
   - Swapped startup checkpoint assertions from `Assert-ControllerDispatchCheckpoint` to `Assert-ControllerStartupCheckpoint` across lines 256, 262, 277, and 289.

4. **`scripts/controller/Deploy-Controller.ps1`**:
   - Deployed updated scripts to `$env:USERPROFILE/OpenClawPAD/`.

## 3. Regression Test Verification

Created dedicated test suite `tests/unit/test_controller_startup_fix_regression.ps1` covering:
- **Test 1**: Legitimately completed historical recovery followed by new task starts successfully (**PASS**).
- **Test 1b**: `Assert-ControllerDispatchCheckpoint` returns clean for completed historical task (**PASS**).
- **Test 2**: Incomplete / `BLOCKED` checkpoint still blocks startup (**PASS**).
- **Test 3a**: Valid active reconciliation passes recovery validation (**PASS**).
- **Test 3b**: Tampered historical archive hash fails closed during recovery validation (**PASS**).
- **Test 3c**: Tampered session report fails closed during recovery validation (**PASS**).
- **Test 3d**: Mismatched recovery run ID fails closed during recovery validation (**PASS**).
- **Test 4**: Foreign active session blocks controller startup (**PASS**).
- **Test 5a**: Zero-submission task blocks checkpoint containing PBS job (**PASS**).
- **Test 5b**: Duplicate PBS submission for completed job is blocked (**PASS**).
- **Test 6**: Completed task in `ACTIVE_TASK.json` is rejected as immutable (**PASS**).

Additional unit test suites verified clean:
- `tests/unit/test_controller_turn354_reconciliation.ps1` (16/16 passed).
- `tests/unit/test_controller_task_lifecycle.ps1` (18/18 passed).

## 4. Live Startup Verification

Ran live `Antigravity-Autonomous-Loop.ps1 -ControllerDryRun` against current active task:
- Task: `F1606-MODE1-C6-R7-NONCONVERGENCE-INVESTIGATION`
- Task Type: `RESEARCH_PREPARATION`
- Checkpoint State: `COMPLETED`
- Exit code: 0 (**PASS**)

## 5. Invariant & Governance Preservation

- Terminal scientific finding for R7 preserved: Job 1419873.mmaster02 terminated at Outer 100 with coupled nonconvergence; Stage 2 never activated; no accepted C6 checkpoint exists; 0 PBS submissions authorized under F1606.
- Historical records, archives, and PBS ledger entries remain completely untouched and immutable.

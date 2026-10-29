# Turn 294 HPC reconciliation and evidence-only controller recovery

RunId: 77c4cf2d-e740-4737-bb8a-a858fc0afd5a. Base commit: 6e93da650a511b383ee48628c24e03cba701bde0. Date: 2026-10-29.

## HPC STATUS

Guarded SSH alias tu_freiberg is working. Full retained PBS records for 307 pr21vyci jobs were collected with qstat -x -f $(qselect -x -u pr21vyci). No Job_Name matched H31 or INC92. Exact qselect -x -u pr21vyci -N M1_C4_INC92_H31_CONT succeeded with empty output. Active qstat succeeded with no jobs. Expected /scratch9/pr21vyci/runs/*h31*, *inc92*, and /home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/140* do not exist. A bounded listing of the 195 scratch run entries found H30 but no H31/INC92. No local 140-prefixed package directory was found in the earlier investigation.

Classification: NO_MATCH_IN_RETAINED_EVIDENCE_NON_SUBMISSION_UNPROVEN. No Package140 PBS ID is established. This is not an absence certificate or proof that no job ever existed. Login-node tracejob could not find even the known H30 job in three days of logs; accounting/server log paths are unavailable on this login node. No candidate manifest/input/output could be inspected because no candidate path was found. No HPC accounting row was invented.

Authentic predecessor 1418554.mmaster02: Job_Name=M1_C4_INC91_H30_CONT, job_state=F, Exit_status=0, walltime=00:01:07, run_count=1. Scientific H30 acceptance remains the existing measured result; scheduler exit0 alone is not scientific acceptance. Package113's failed cross-mesh energy gate remains unchanged.

Raw remote evidence and query records: C:/Users/pruth/OpenClawPAD/backups/turn294-hpc-6692e10583df486094197bf8b3686406. Original archive: C:/Users/pruth/OpenClawPAD/backups/turn294-recovery-82f4ea1a-afe5-4aa0-a4fe-43c7ac6c0feb. Each applicable source has an existence check, SHA256 and timestamp; archived evidence is read-only and created without overwrite. Read-only attributes are an accidental-write guard, not WORM storage. Full scheduler output remains outside Git.

Collection defects preserved: the first quoted pipeline query failed parameter binding, wildcard qselect names were rejected. Corrected full-history and exact-name commands succeeded and were recorded separately. The initial recovery-manifest.json had null remote paths due to nested PowerShell arrays; its dry run failed before any checkpoint write. Flattening the query arrays produced recovery-manifest-validated.json without overwriting the failed manifest. Added explicit missing-path validation. None of these failures caused submission or scientific changes.

## NEW EXPERIMENT

None. No real qsub, qdel, qmove, Abaqus solve, notification test, or autonomous model call. Existing controller tests use mocked PBS/AGY calls.

## SCIENTIFIC PROGRESS

No scientific completion claimed. Turn294 remains an interrupted attempt. Original scientific instruction identity (hash fad144dfca632530dff826a4b3e14f45dac49e36d58e8d681f695c1db09b0134) is preserved; its plaintext is not stored in the checkpoint. The verified existing pending instruction is evidence-only reconciliation, not a submission replay. HTTP400 INVALID_ARGUMENT is recorded without attributing it to UTF8 corruption.

## DOCUMENTATION

Implemented scripts/controller/Reconcile-Turn294.ps1 and an explicit INTERRUPTED_TURN294_EVIDENCE_ONLY_READY integrity branch in Controller-Recovery.ps1. Uses the controller's existing RECOVERY_REQUIRED semantics: resume turn294 in a fresh conversation, no original instruction replay, no simulation or submission. Never marks the interrupted experiment COMPLETED. completed_turn=293 and the entire loop-state file are unchanged. No Turn7 helper executed. All original scientific checkpoint fields and partial-output evidence remain intact.

Required immutable evidence roles, exact run/turn, original hash, partial integrity, remote query results, original instruction identity and loop293 state are checked. Possible scheduler/PBS receipt matches halt this narrow no-match recovery route and require accounting review. A controller mutex and immediate pre-write hash comparison protect the single atomic checkpoint update. Subsequent identical applications return ALREADY_APPLIED without writes. Archived original checkpoint, original .previous, logs, session, bootstrap, ledgers and current state remain preserved. ACTIVE_SESSION was claimed for scoped work and restored to its original inactive bytes at closeout.

Production dry run: PASS; no checkpoint writes. Tests: all 42 existing controller recovery checks PASS, all 34 new Turn294 fixture checks PASS (repeated after missing-path guard repair). New checks cover hashes/identity, immutable evidence, repeat/no-overwrite behavior, PBS-match rejection, unchanged ledger and scientific evidence snapshots, loop293 accounting, fresh conversation, evidence-only instruction, corrupted evidence rejection, and rejection of COMPLETED transition. Production apply: APPLIED_EVIDENCE_ONLY. Reapply: ALREADY_APPLIED, identical hash. Installed controller -ControllerDryRun -MaxTurns 1: DRY_RUN_NO_EXECUTION, active_session=false, RECOVERY_REQUIRED, unchanged evidence-only instruction, stale_prompt_replaced=false.

Original checkpoint SHA256: E117C7BA3320E5F27DCB2115B863F7D0D2E18C822B2FC102B953096A794C92A9.
Recovered checkpoint SHA256: 94978415A6224EAD28B89898C5022C19BB52B8CFEDCC74CE6779ED1D3002436C.
Unchanged loop SHA256: 1E685D1041546DEF196C74DA546D257242352148522A34C85E597CF7151AB0ED.
Recovery manifest: C:/Users/pruth/OpenClawPAD/backups/turn294-hpc-6692e10583df486094197bf8b3686406/recovery-manifest-validated.json. Recovered checkpoint also archived there under recovered-checkpoint.json.

## NEXT ACTION

Controller dispatch is resumable ONLY for an evidence-only Turn294 recovery. It is not clearance to submit Package140. Package140's non-submission remains unproven and must remain explicit in any later scientific execution review. Existing once-only execution accounting must not be reset.

Read-only verification command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\OpenClawPAD\Antigravity-Autonomous-Loop.ps1" -ControllerDryRun -MaxTurns 1
```

If the operator chooses to resume, use one bounded recovery turn first (not executed here):

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "$env:USERPROFILE\OpenClawPAD\Antigravity-Autonomous-Loop.ps1" -ControlledSingleTurn -MaxTurns 1
```

This picks RECOVERY_REQUIRED, turn294 and a fresh conversation automatically. Do not supply ForceResume or the original submission prompt. Keep the 40-turn scientific loop stopped until this bounded recovery's actual response, next instruction and Package140 accounting are reviewed. Account/profile selection remains the separate existing controller behavior; no login or profile settings were changed here.

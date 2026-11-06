# F1634 — canonical producer diagnosis and launcher repair

Date: 6 November 2026. Starting commit: 4c6e5c7566464f536e25079b074e5e3f4925067f.
Classification: SUCCESSOR_REQUIRED; no controller restart or scientific acceptance claimed.

## Verified producer stop

The installed controller and repository controller have identical SHA-256
63F799406B3F38CED3AFE890C80CA8AAD40ED3952D688FD18134D27919003ED7.
Live Win32 process inspection found PAD.RobotV2.exe PID 5728, parent 64216,
started 6 November 06:16:42 local time, but no autonomous controller or AGY print
worker. The two PowerShell consoles did not have controller launch commands.
PAD process existence alone does not verify its current wait action.

The hash-enveloped controller checkpoint was decoded through its payload:
state COMPLETED, turn 7, task F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION,
process_id 0, stop_reason OPERATION_COMPLETED, empty next_instruction,
updated_at 2026-11-04T19:09:04.2951825+00:00. Its next_safe_action says to
advance the lifecycle without replay. Checkpoint file SHA-256:
5A58322503D96631213502BBE09C6A6BD46CC9DB986A5F02E9337F6EE6402FEA.
The loop state remains PENDING_NEXT_TURN at F1608. This proves a completed
producer with no checkpoint successor, not a currently running research worker.
The historical process termination mechanism was not independently established.
Current authentication/quota availability was not established.

## Exact current startup predicate

First Start-Verified-MethodCLoop -VerifyOnly failed under StrictMode because
the completed F1633 ACTIVE_TASK omits optional scientific_checkpoint. The
launcher now checks property existence before accessing that optional object
and its artifact. No checkpoint or scientific file was changed.

The rerun passed canonical bridge prompt assembly (6613 characters), then failed:

    COMPLETED_TASK_REJECTED: F1633-NEAREST-HPC-SIMULATION-ELIGIBILITY-AUDIT;
    SUCCESSOR_REQUIRED; No exact existing open successor task is recorded;
    never synthesize one from next-action prose

scripts/controller/TASK_LIFECYCLE.md explicitly requires reporting this state
when no recorded successor exists. The differently named definition
F1633-METHOD-A-HOLE-INDICATOR-SIZING-AND-REASSESSMENT.json is marked active,
but is not the selected task and is not an exact linked open successor.
Its geometry/sizing reassessment would require an evidence-backed lifecycle
definition, not silently selecting or renaming the completed audit.
No supported task-registration command was established in the inspected
lifecycle module; its selector is explicitly read-only.

## Bridge integrity and last handoff

No bridge.lock, pending request or response was present in the live bridge
directory listing. Existing PAD was left running. No live packet was fabricated,
replayed or sent. Latest archived handoff: HND-24ccab0bbe86, request
20261106_145549 and response archived at 14:58:53 local time.
Request SHA-256: 9CF39B9BF04124E4EECD32092DF74DD328379BC090771256505D8B8BB1EACFC5.
Response SHA-256: 6284498167ACF457FB1F86CA49463D49D1B34C918F4544540F2553EC4CFA42E8.
These archive hashes do not constitute a new live handshake or provenance review.

Canonical/deployed rules match SHA-256
73E7FD4CE9EB697768D24301D9FA4353A287B4F4A3F32A0DB0EE5F6F92A2E0C2.
Bridge scripts differ: canonical
5DE3A4F658F548CF009A79AFE15D7676419D0593F43129172E7BE6EC090603F6;
deployed AB2F3EB53FFA1A1924F8585B71FD50424C9ECA590E02A7F3CF32E081012A771C.
Controller explicitly prefers canonical, falling back to deployed only if absent.
No deployment overwrite was made.

## Checks and preserved failures

- Normal startup loop-state regression: 13/13 PASS.
- External predecessor transition regression: 9/9 PASS, including rejection of
  missing definition, changed receipt, active owner and duplicate successor.
- Canonical bridge DryRun: PASS; no live transport claim.
- Older F1478 bridge policy pytest: 1 PASS, 3 FAIL due to obsolete policy marker
  and 22 October meeting-date expectations. Current rules were not weakened.
- External-blocker bridge regression unexpectedly published a test packet only
  in its unique TEMP sandbox and waited instead of returning the expected guard
  result. Interrupted after approximately 14 seconds; no live bridge packet or
  PAD launch. This suite is NOT a qualification pass; preserve its temporary
  evidence rather than repeat or clear any live lock.
- Guarded SSH qstat -u pr21vyci: exit 0, empty output; no user jobs returned.

## Scientific and continuation status

Zero PBS submissions; no new experiment or numerical change. F1632/F1633 were
not reopened and their historical manifest audit was not repeated. Existing
Method A runtime/resolution restriction and rejected Method C C6 convergence
remain scientific gates. No new hypothesis or exception is approved here.

Next operation: establish one exact evidence-backed successor definition and
predecessor linkage under existing lifecycle/review rules, then rerun VerifyOnly.
Only after it passes and current ownership/authentication/quota checks pass may
one normal controller start occur; verify a fresh matching PAD exchange and AGY
dispatch before claiming restored autonomy. Never reset the F1608 checkpoint or
reuse its old next instruction to force this transition.

The working branch is mode2-pandey-kumar-reproduction, 936 commits ahead of
local main at entry. Promoting this entire history is outside this bounded
launcher repair. Preserve the branch and unrelated dirty work; remote publication
must use a reviewed forward-only integration, without force or broad staging.

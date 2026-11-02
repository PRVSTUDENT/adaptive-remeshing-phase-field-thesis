# Task-lifecycle reconciliation — 2 November 2026

Result: MAINTENANCE_ACCEPTANCE_PASS_EXECUTION_BLOCKED. One bounded maintenance task; no scientific controller/AGY research execution, new bridge handoff, scheduler command or HPC submission. Starting commit 36c29c680b7f33a162242781d84ae4f6a367c9aa. Unrelated dirty paths retained.

## Root cause and authoritative transition

F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160 has an exact completed TASK_LEDGER row dated 2026-11-01T12:12:00+01:00. ACTIVE_TASK kept that same parent ID throughout subsequent bounded steps. Invoke-ControllerTurn closeout copied arbitrary preparation payload status into task.status, restoring PREPARATION_COMPLETE on a closed parent. Bootstrap only checked the active-file status, while instruction validation checked completed ledger entries mainly when the heading included an F-ID. A heading beginning Writing therefore bypassed the heading check. Turn35 deterministic recovery then generated a heading containing F1597 and triggered the correct completed-parent rejection. The completed-parent guard was not the defect.

PREPARATION_COMPLETE is NOT a terminal parent task status. It is a bounded checkpoint status, as shown by the Preparation stage writing a PREPARATION_CHECKPOINT and Complete writing a bounded_step_complete ledger row. Parent task lifecycle is separate: an exact terminal ledger row cannot be undone by a preparation artifact, later active rows or bridge prose. This distinction is now explicit in scripts/controller/TASK_LIFECYCLE.md and implemented by Controller-TaskLifecycle.ps1.

Authoritative transition: COMPLETED_AWAITING_SUCCESSOR / SUCCESSOR_REQUIRED. ACTIVE_TASK now agrees with the existing closure: status COMPLETED, last_step_status PREPARATION_COMPLETE, lifecycle metadata explaining the source and missing successor. Scientific phase, checkpoint, completed operations, job references and every other original task property remain unchanged; verified by structural comparison against starting HEAD. No closed ledger row was changed and no research task was created.

Next authoritative research task: NONE RECORDED (null). The closed row's next_task is prose, Complete bridge review and live once-only submission of Package 160, which is not an exact existing open task ID and concerns an already submitted operation. No successor_task_id is recorded. Do not select an unrelated newest ledger row, derive a task from F1597, or reopen this predecessor. Recorded existing open successors are identified read-only only when explicitly linked by exact ID; they still require their own authoritative active record and ordinary scientific/technical gates.

## Corrections

- Shared lifecycle resolution exposes nondispatchable completed state and exact recorded successor candidates. Preparation and supervisor startup stop before registration/model calls for a completed parent. Main dispatch checks lifecycle before registration; Bootstrap and every unfinished operation/preparation/closeout stage use the same guard. Completed turn receipt handling remains idempotent.
- Preparation closeout records last_step_status rather than overwriting parent lifecycle with payload.status; explicit terminal parents cannot be reopened by this helper.
- Definition-recovery regression: after a consulted correction named invented_operation, registration resolution returned DEFINITION_REVIEW_REQUIRED and recovery returned early, so the original test expected two consultations but got only one. Unknown IDs in correction responses now become bounded DEFINITION_REJECTED proposals; they are never registered. Initial genuine new-definition requests and authenticated external review, service, security and replay gates retain their stops. The original assertion is unchanged and now passes; additional assertions verify zero registration writes and zero consultations for a genuine new-definition request.
- Bootstrap test fixtures now include their real module dependencies. A stale assertion about a removed log/comment phrase was replaced with stronger checks of the actual scientific-progress branch, finite work deadline and 360-second stream-stall enforcement. No watchdog/runtime deadline was changed.

## Tests

18 lifecycle; 35 definition-recovery; 26 bootstrap/closeout; 11 preparation; 42 general recovery; 16 durable failure-handoff; 9 completed-session/ownership; 11 supervisor checks PASS (168 checks). Fixtures cover exact completed-task rejection, unlabelled headings, legitimate linked successor selection without activation, closed/bounded-step successor exclusion, interruption/restart preservation, repeated closeout/dispatch prevention and wrong/failed bridge replies. The bootstrap suite uses a disposable local fixture origin; production repository and PBS accounting are not used for scientific execution. PowerShell parsing and scoped whitespace checks PASS. No assertion was suppressed.

## Non-executing acceptance and hashes

Exclusive Windows controller mutex acquired for deployment/acceptance; prior installed script preserved locally. Installed and canonical controller SHA256 match: 5D3EC404858B8A52F3BFE4C29FBE6A85FFD9D3000863457F72431B03170B890A.

Actual installed command used -ControllerDryRun with no AGY, PAD or scheduler dispatch. It returned mode DRY_RUN_NO_EXECUTION, preparation_status TASK_SUCCESSOR_REQUIRED, dispatch_ready=false and checkpoint_state COMPLETED. Repeated final dry-run gave the same safe outcome. Evidence is under:
C:\Users\pruth\OpenClawPAD\failure_recovery\lifecycle-maintenance-20261102
Files: acceptance.json; installed-dry-run.txt; installed-dry-run-final.json; source-hashes.json; controller-before.ps1.

Final canonical module hashes (installed entrypoint imports these exact workspace modules):
- scripts/controller/Antigravity-Autonomous-Loop.ps1: 5D3EC404858B8A52F3BFE4C29FBE6A85FFD9D3000863457F72431B03170B890A
- scripts/controller/Controller-TaskLifecycle.ps1: EAFB5B2AF35E5075BB7FBA111E9A07C6E8196CBA3AA91D955E234BDD10076CC3
- scripts/controller/Controller-Recovery.ps1: C035E2BD235DFDDEDBCD93E4AC54C8239076D405D738AF04920307DDA3BD537E
- scripts/controller/Controller-FailureHandoff.ps1: 5776370F82C00C26A9CA2FB7944366632B3ABC02B50B33EDE9EF2B39D84B4B4A
- scripts/controller/Controller-Preparation.ps1: AEC3219453892A326319F844D755770C0C39BD2A862F0ED47275CFB26AC11622
- scripts/controller/Controller-DefinitionRecovery.ps1: F26A5F93CC2CBC5EBA0D4020B77A41A6095A26340FD9D6A5167EE67430EA9D27
- scripts/controller/Invoke-ControllerTurn.ps1: 32262054488385850785A99523681698D796C5564265F7F66F190CA14B9D3908

Preserved Turn35 checkpoint SHA256 B811FED302404A95B01FEF8E0BE8AE33182A427828AD9D8D56329FFABE27DBDD; HPC ledger 8DB31A6B284AB076EF3593C55BB5B2FEC1ABE007327F51EE3A8B9A39BB906D65; execution ledger 1233FF051BFA5DD91A6B7D8F8A7CEFD44248AB0E9794095D3919E5D51F5C2B8D. All unchanged. Original recovery packet and response untouched; no completed submission or experiment replayed.

## Safe-resume decision

NO scientific resume. Maintenance logic/tests/installed acceptance pass, but there is no recorded legitimate successor task. Next action is to establish that exact successor from existing scientific dependency/review evidence, without repeating closed work, then use ordinary ownership, source integrity, scientific predecessor, qualification and once-only execution gates. This is missing authoritative task information, not an administrative authorization requirement. No new hypothesis or scientific task was fabricated during maintenance. Final local and remote commit hashes are reported from Git after commit/push, avoiding a self-referential report hash.

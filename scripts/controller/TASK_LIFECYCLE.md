# Controller task lifecycle

`ACTIVE_TASK.json` selects the parent research task. Its exact ID must not have
a terminal `complete`, `completed`, `closed` or `done` row in `TASK_LEDGER.csv`.
An exact historical closure is irreversible; later active rows, prefix matches,
free-form bridge instructions or preparation payloads cannot reopen it.

`PREPARATION_COMPLETE` and `RESEARCH_PREPARATION_COMPLETE` describe bounded
checkpoint completion. They are not terminal parent-task states or scientific
acceptance. The preparation artifact and turn receipt retain those statuses.
Closeout records `last_step_status` on an active parent instead of replacing
the parent's lifecycle with arbitrary payload status. `bounded_step_complete`
ledger rows are operation/step history, not new open successor tasks.

A completed selected task resolves to `COMPLETED_AWAITING_SUCCESSOR` and blocks
dispatch before registration, model calls or scientific execution. A successor
may be identified only by an explicit `successor_task_id` or a terminal exact
ledger row's `next_task` containing an exact existing open task ID. Prose about
future work, matching prefixes and unrelated newest ledger rows are insufficient.
Conflicting links or a closed successor remain blocked. Selection is read-only;
it does not synthesize a successor task record or activate a scientific operation.

Bootstrap and every unfinished scientific/preparation/closeout stage verify this
same lifecycle. A `COMPLETE` turn receipt remains idempotent and does not replay
an experiment. Qualification, ownership, artifact integrity, scientific
dependencies and once-only PBS checks remain separate mandatory gates.

When no recorded successor exists, report `SUCCESSOR_REQUIRED` with no next
authoritative task. Preserve all completed task IDs, receipts and checkpoints.
This is missing task evidence, not a credential or human-activation requirement.

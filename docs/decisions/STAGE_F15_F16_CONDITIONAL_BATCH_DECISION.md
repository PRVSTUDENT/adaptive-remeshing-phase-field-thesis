# Stage F15/F16 conditional batch decision

Prepare four jobs as one immutable two-wave batch. Wave A contains only the
notification smoke. Wave B contains three independent qualification jobs and
cannot be activated until Wave A is terminal and the user personally confirms
Telegram START/COMPLETED and PBS BEGIN/END email.

The rollback jobs preserve the F11 penalty formulation and F14 runtime path,
with byte-identical deck and source. The adaptive-region job is CAE-only and
forbids solver, datacheck, adaptivity submission, remesh calls and candidates.
No medium H1, H2, native remesh, candidate datacheck or refined analysis is
authorized by this preparation.

## Wave B email waiver and failed submission (2026-08-01)

The user explicitly waived personal PBS-email receipt as a Wave B gate after
observing Telegram delivery and no PBS email. Telegram is therefore the
required operational channel; PBS email remains best-effort and classified
`configured_but_not_human_received`.

Authorization commit `37b9c3020cbfc45eb26539dd8270825c58390742`
activated only the three frozen Wave B lanes. The guarded submission issued
one qsub for each rollback lane; both returned 174 (`Access to queue is
denied`) without PBS IDs. The adaptive-region lane was withheld because its
required concurrency dependency could not be constructed. No job ran, all
Wave B authority is consumed, and no retry or replacement is authorized.

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

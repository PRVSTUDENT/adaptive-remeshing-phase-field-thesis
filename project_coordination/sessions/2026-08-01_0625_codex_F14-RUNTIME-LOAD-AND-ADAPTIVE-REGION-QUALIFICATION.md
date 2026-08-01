# F14 preparation, authorization, submission, and queued handoff

Starting SHA: `cd9a47bc19a4d805d952fa740d83a9960f2aab31`
Preparation SHAs: `37d429d`, `ca800f5`
Authorization SHA: `c413115`
Submission/consumption SHA: `89cb44c`
Run ID: `F14_20260801_042129_ca800f5`

Preflights passed independently. The runtime library built and its undefined
symbol list excluded `for_getenv_err`. The CAE-only region audit created the
model-wide rule on the official 3,930-element model and recorded zero solver,
adaptivity-process, remesh, and candidate calls.

The single guarded orchestrator returned PBS IDs `1381368` and `1381369`.
Its parent counters remained zero due Bash command-substitution subshells;
M-119 records the defect. The two distinct scheduler IDs establish exactly two
qsub attempts and two successes. No retry, replacement, direct qsub, qdel, or
qmove occurred. Both jobs were queued at the first post-submission poll.

Terminal scientific classifications remain pending. All authority is consumed.

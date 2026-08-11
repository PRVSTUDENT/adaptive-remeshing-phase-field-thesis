# F43MODEREF-H2-ENDPOINT-RESOLUTION-SUBMIT1

The user explicitly authorized the frozen qualified 24-hour H2 endpoint-resolution package. Authorization commit `1c95f9df25ba16f5e7637a72a69fd4c5179ea46f` was pushed before cluster execution.

Remote preflight verified exact P/Q objects and execution-byte identity, all five frozen hashes, scientific identity, NPHYS 33852, 24-hour PBS directive, route queue, notifications, shell syntax, zero duplicate jobs, zero running jobs, and scheduler availability. The cluster clone was fast-forwarded while preserving unrelated untracked historical outputs.

The first wrapper launch returned `Permission denied` because the tracked wrapper lacks an executable mode bit; it stopped before `qsub`. The same frozen guarded wrapper was then invoked through `bash`, its integrated authorization preflight passed, and exactly one `qsub` call returned `1388330.mmaster02`.

Immediate scheduler evidence:

- Job: `1388330.mmaster02`
- Name: `M2H2ENDPOINT`
- State: `R`
- Execution queue: `normal_imfdfkmq`
- Requested route queue: `entry_imfdfkmq`
- CPU: 1
- Memory: 8 GB
- Walltime: `24:00:00`
- qsub attempts/successes: 1/1
- Remaining submissions: 0
- Automatic retry/replacement: false

No `qmove`, `qdel`, downstream submission, or scientific-file change occurred. Authorization is consumed. Next action is read-only terminal monitoring and subsequent evidence-based report rebuild.

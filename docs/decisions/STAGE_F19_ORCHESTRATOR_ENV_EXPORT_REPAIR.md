# Stage F19 guarded-orchestrator environment-export repair

The F19 scientific packages remain frozen at preparation `f1769b6`. The only
repair is to the guarded parent-shell orchestrator: each qsub call now receives
an argument array containing `-v` and exactly
`F19_PACKAGE_DIR=<absolute>,F19_EVIDENCE_DIR=<absolute>`. Broad `qsub -V`,
`eval`, and unquoted command construction are prohibited.

Before each mock or future authorized qsub call, the orchestrator validates
absolute safe paths, the exact readable wrapper, both package manifests, and a
writable evidence directory. It accepts only a single syntactically valid PBS
ID and forms the adaptive `afterany` dependency only from the validated control
ID. Any failure stops the batch without retry and emits JSON accounting.

This decision is preparation-only. The previous authorization is not reusable
after the orchestrator changed. Execution remains unauthorized pending a
second clean-Linux proof and fresh exact authorization.

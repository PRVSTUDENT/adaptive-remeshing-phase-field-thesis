# F5 H2 compiler/datacheck smoke submission

Date: 2026-07-30  
Agent: Codex  
Starting commit: `530f6571970df63f62a07a2894d202dd1edabff9`

The user explicitly authorized exactly one `M2H2CMP1` qsub attempt. Local
repository ancestry, package metadata, PBS datacheck-only behavior and exact
H2 scientific hashes were verified.

The required read-only SSH preflight against
`mlogin01.hrz.tu-freiberg.de` failed authentication:
`Permission denied (publickey,password,hostbased)`. Therefore `qstat`, module
inspection, module-order comparison and environment verification were not
reached. Per the explicit stopping rule, authorization was not activated, no
immutable cluster run ID or scratch directory was created, and no qsub was
issued.

Offline results:

- H2 static validation: 13/13 pass
- PBS syntax: pass
- deck/Fortran hashes: 2/2 pass
- F5 unit tests: 8/8 pass
- Stage F4 orchestrator test: known failure preserved
- git diff check: pass
- bootstrap validator while active: expected active-task allowlist failure;
  task ID was added and the released-session rerun passed

Final classification:
`stage_f5_h2_compiler_datacheck_smoke_blocked_ssh_authentication`.

Counters: qsub attempts 0; successful submissions 0; retries 0; replacements
0; full-analysis submissions 0. All execution flags are false and
`maximum_jobs_now=0`.

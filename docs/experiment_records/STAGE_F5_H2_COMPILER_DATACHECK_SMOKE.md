# Stage F5 H2 compiler/datacheck smoke submission

Date: 2026-07-30  
Task: `F5-H2-COMPILER-DATACHECK-SMOKE-SUBMIT`  
Final classification:
`stage_f5_h2_compiler_datacheck_smoke_blocked_ssh_authentication`

Explicit authorization for exactly one `M2H2CMP1` qsub attempt was received.
Repository ancestry, the package manifest and both canonical scientific input
hashes were verified before cluster access:

- deck:
  `fdcd6ee1b1d6cbfb88d59a3edfb7f1c6b35cecde736a427f6b3030b0443b10bf`
- Fortran:
  `49c9054ab5faec9e069e0a9149af5058e6f1e11ab164c2a0e318f60282309b37`

The mandatory read-only SSH preflight against
`mlogin01.hrz.tu-freiberg.de` failed with:

```text
Permission denied (publickey,password,hostbased).
```

Consequently, `qstat` and module-order inspection were not reached. Under the
authorization stopping rule, authorization was never activated, no immutable
cluster runtime was staged, and no qsub command was issued.

Offline checks retained:

- H2 static validator: 13/13 pass
- compiler-smoke PBS `bash -n`: pass
- exact input hashes: 2/2 pass
- F5 readiness unit tests: 8/8 pass
- known unrelated Stage F4 orchestrator test: still fails
- `git diff --check`: pass

Final counters: qsub attempts `0`, successful submissions `0`, retries `0`,
replacements `0`, full-analysis submissions `0`. H2 compiler environment
remains unresolved and a future attempt requires restored SSH access and new
human authorization.

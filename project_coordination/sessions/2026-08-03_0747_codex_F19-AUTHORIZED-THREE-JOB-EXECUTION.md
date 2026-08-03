# F19 authorized three-job execution preflight

- Agent: codex
- Starting commit: `0b60eccbf957c1a059207e0a8c27e5034aa4c573`
- Authorized preparation: `f1769b648c4a67cc6060bfdadb958a9b034ff40a`
- Authorized jobs: `M2IRRROLLCTL5`, `M2IRRROLLFORCE5`, `M2RMREG6`
- Outcome: blocked before qsub

The frozen PBS hashes and all three `F19_SHA256SUMS`/`SHA256SUMS` hashes
matched the exact authorization. Source audit then found that the only
authorized orchestrator prefixes qsub with `F19_PACKAGE_DIR` and
`F19_EVIDENCE_DIR`, but does not export them using `qsub -v`. The frozen PBS
wrappers require both variables immediately, before mandatory Telegram START.

No cluster command, qsub, qdel, qmove, rerun, Abaqus execution, retry, or
replacement occurred. Accounting is qsub attempts/successes/failures 0/0/0,
and the authorization was not consumed. The orchestrator and frozen packages
were not modified. A corrected preparation must be clean-Linux-qualified and
freshly authorized before execution.

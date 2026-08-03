# F20 M2RMREG7 authorized submission

- Agent: codex
- Task: `F20-M2RMREG7-AUTHORIZED-EXECUTION`
- Starting revision: `2671651eb0d8583384058202a9137caa169670a4`
- Authorization revision: `df6593287560e4dcf5275314a66b8fcbc7e5fb76`
- Preparation revision: `f877b81b567eaf11ea499e33ace32b4a024eaab3`
- Frozen hashes and both manifests: passed locally and in detached cluster checkout
- Read-only preflight: user queue empty; route queue enabled/started; source ODB hash passed; targets absent
- Process note: first remote staging shell was malformed locally and stopped with both targets absent and zero qsub calls
- Submission: guarded orchestrator invoked once; 1 attempt, 1 success, 0 failures
- PBS job: `1382428.mmaster02` / `M2RMREG7`, initial state Q, routed queue `normal_imfdfkmq`
- Resources: 1 CPU, 8 GB, 00:30:00
- Required variables: `F20_PACKAGE_DIR`, `F20_EVIDENCE_DIR`
- Authority: consumed 1/1; retry/replacement/direct qsub/qdel/qmove/rerun false
- Next action: monitor terminal status without mutation

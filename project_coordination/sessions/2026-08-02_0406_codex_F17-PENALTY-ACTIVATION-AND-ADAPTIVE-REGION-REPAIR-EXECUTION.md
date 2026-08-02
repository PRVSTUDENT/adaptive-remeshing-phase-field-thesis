# F17 execution session report

Agent: codex
Task: F17-PENALTY-ACTIVATION-AND-ADAPTIVE-REGION-REPAIR-EXECUTION
Starting commit: `41aaf8ee9582b4a245cf3d64cd6dbf309f752ef5`
Preparation commit: `41aaf8ee9582b4a245cf3d64cd6dbf309f752ef5`
Authorization commit: `b6f3478b8dae8732acb0b8126f0ec75af215ea5e`
Run ID: `F17_20260802_0615_b6f3478`

## Outcome

Classification: `f17_submission_blocked_frozen_manifest_hash_mismatch`.
The authorization was recorded, committed, pushed, and checked out in a clean
detached cluster worktree. The scheduler contained no project jobs or F17
duplicates. All hashes stated directly by the user matched. The two committed
package manifests nevertheless contained ten mismatching metadata/text-file
hashes. The explicit fail-closed rule invalidated authority before qsub.

## Commands and tests

- Required bootstrap/status/history commands and coordination reads completed.
- `git fetch origin`, ancestry check, authorization commit, and push completed.
- Read-only `qstat -u pr21vyci` returned no jobs.
- The dirty long-lived cluster checkout was preserved; a detached worktree at
  the authorization SHA was created under the run root.
- Local Python tests could not run because no local Python runtime is installed.
- Cluster Python 3.11 was loaded; the direct F17 test stopped at the manifest
  assertion, establishing the pre-submission hash failure.
- Both `sha256sum -c F17_SHA256SUMS` checks failed on five files each.
- Shell syntax and path-scoped `git diff --check` passed before authorization.

## HPC and authorization accounting

- Authorized jobs: `M2IRRPENACT1`, `M2RMREG4`.
- Jobs submitted: none.
- PBS IDs: none.
- qsub attempts/successes/failures: `0/0/0`.
- Retries/replacements/direct qsub/qdel/qmove/rerun: `0/0/0/0/0/0`.
- Solver/CAE/datacheck/adaptivity/remesh/candidate/refined executions: all zero.
- Authorization change: activated in `b6f3478`, then invalidated by mandatory frozen-hash preflight.

## Exact mismatch scope

Both packages mismatched `F17_NO_EXECUTION_AUDIT.json`,
`F17_RUNTIME_MANIFEST.json`, `PACKAGE_MANIFEST.json`, `STATUS.json`, and
`runtime/.gitignore`. Exact expected/actual hashes are retained remotely at
`/scratch/pr21vyci/adaptive-remeshing/runs/stage_f17/F17_20260802_0615_b6f3478/F17_HASH_MISMATCH_EVIDENCE.txt`.

Files created: batch authorization, guarded F17 orchestrator, this session report.
Files modified: canonical coordination state/ledgers, project checklist, mistakes log.
Scientific changes: none.
Dirty paths deliberately preserved: every path present in the initial `git status --short`, plus the unrelated dirty/untracked cluster-checkout paths.
Exact next action: in a new preparation task, repair the cross-platform manifest byte contract, prove both manifests in a clean Linux checkout, commit the repair, and obtain new explicit two-job authorization.

# Multi-agent project coordination — START HERE

Classification: `multi_agent_coordination_layer_initialized`

This folder is the **single shared coordination layer** for Codex, Grok, and
Gemini Antigravity. It holds **metadata, state, decisions, and logs only**.

It must **never** contain copies of `.for`, `.inp`, Python scripts, model
trees, or result folders.

## Sources of truth

1. **Canonical code and scientific files** — existing paths under `models/`,
   `scripts/`, `configs/`, `runs/`, `results/`, `docs/`.
2. **Canonical history** — Git commits on `main`.
3. **Current task state** — `CURRENT_STATE.md`.
4. **Current agent lock** — `ACTIVE_SESSION.json`.
5. **Task history** — `TASK_LEDGER.csv` and `sessions/`.
6. **HPC execution history** — `HPC_JOB_LEDGER.csv`.
7. **Bulky ODB/scratch outputs** — remain on HPC/local scratch; only paths,
   hashes, sizes, and classifications are recorded here.

Historical references (not the active control plane):

- `.agent.md`
- `adaptive_remeshing_phase_field_agent.md`
- `agent_handoff/` (dirty; do not use as primary coordination; do not run its
  sync utility while unrelated dirty paths exist)

## Before any edit

```powershell
cd "D:\Master thesis\Adaptive remeshing"
git status --short
git rev-parse HEAD
git log -1 --oneline
```

Read in order:

1. `project_coordination/START_HERE.md` (this file)
2. `project_coordination/CURRENT_STATE.md`
3. `project_coordination/ACTIVE_SESSION.json`
4. `project_coordination/ACTIVE_TASK.json`
5. `project_coordination/TASK_LEDGER.csv`
6. `project_coordination/HPC_JOB_LEDGER.csv`
7. `project_coordination/ARTIFACT_REGISTRY.csv`
8. `docs/project/PROJECT_PHASE_CHECKLIST.md`

Then:

1. Verify no other agent is active (`ACTIVE_SESSION.json` → `active: false`).
2. Claim the session: set `active: true`, agent, task_id, started_at, write scope.
3. Preserve all pre-existing dirty paths.
4. Search `ARTIFACT_REGISTRY.csv` before creating files.

Agent identities: `codex` | `grok` | `gemini-antigravity`

## Duplicate-code prevention

- Never create agent-specific source trees (`codex_code/`, `grok_code/`, …).
- Never create `_new`, `_latest`, `_final2`, `_copy`, `_fixed_again` names.
- Modify the canonical file when the task permits it.
- New variants only for distinct scientific configuration, authorization lane,
  or preserved failed attempt — with registry entry, decision record, parent
  commit, and `supersedes` / `derived_from`.
- Use Git history instead of file copies for backup.
- Selective `git add` only; never `git add .`.
- Never broad `git clean`, `git reset --hard`, or `agent_handoff` sync while
  unrelated dirty paths exist.

## After work

Write `sessions/YYYY-MM-DD_HHMM_<agent>_<task-id>.md`, update ledgers, and
release `ACTIVE_SESSION.json` (`active: false`).

## Full protocol

See `AGENT_PROTOCOL.md` and `PATH_AND_ENVIRONMENT_MAP.md`.

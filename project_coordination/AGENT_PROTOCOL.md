# Agent protocol (Codex / Grok / Gemini Antigravity)

## Start protocol

1. `git status --short`, `git rev-parse HEAD`, `git log -1 --oneline`
2. Read coordination files listed in `START_HERE.md`
3. If `ACTIVE_SESSION.json.active` is true and agent is not you → **stop**
4. Claim lock:

```json
{
  "active": true,
  "agent": "codex|grok|gemini-antigravity",
  "task_id": "<TASK>",
  "started_at": "<ISO-8601>",
  "base_commit": "<HEAD>",
  "allowed_write_scope": ["exact/paths/**"],
  "forbidden_paths": [
    "agent_handoff/**",
    "preserved failed-job evidence",
    "unrelated dirty files"
  ],
  "notes": "<optional>"
}
```

5. Record known dirty paths; do not “clean” them
6. Search `ARTIFACT_REGISTRY.csv` before creating any new artifact

## During work

- Stay within `allowed_write_scope`
- Prefer editing canonical scientific paths over new trees
- Record every HPC command and job ID immediately in `HPC_JOB_LEDGER.csv`
- Never submit jobs unless the active task and authorization file allow it
- Never reopen Stage P, D3D, or thesis-submission packaging unless the task
  explicitly requires it

## End protocol

Create:

```text
project_coordination/sessions/YYYY-MM-DD_HHMM_<agent>_<task-id>.md
```

Required fields:

```text
Agent:
Task:
Starting commit:
Ending commit:
Files read:
Files created:
Files modified:
Commands run:
Tests run:
Tests passed/failed:
HPC commands:
Jobs submitted:
Job IDs:
Authorization changes:
Scientific changes:
Hashes:
Known failures:
Dirty paths deliberately preserved:
Exact next action:
```

Update:

- `CURRENT_STATE.md`
- `ACTIVE_TASK.json`
- `TASK_LEDGER.csv`
- `HPC_JOB_LEDGER.csv` (if applicable)
- `ARTIFACT_REGISTRY.csv` (if applicable)
- `ACTIVE_SESSION.json` → release lock (`active: false`, clear agent/task)

## Commit hygiene

- Selective path staging only
- Path-scoped `git diff --check` on staged coordination/scientific paths
- Commit messages describe the scientific or coordination decision
- Push only when the task requires remote synchronization

## Authorization and jobs

| Pattern | Rule |
|---|---|
| `*_prepared` | offline only |
| `*_authorized` | one-shot allowed after separate auth commit |
| datacheck failure | consumes authorization; no automatic retry |
| solver | never share datacheck authorization |

## Coordination folder purity

`project_coordination/` may contain only:

- Markdown / JSON / CSV ledgers
- session reports
- inventory metadata

Forbidden inside this folder: `.for`, `.inp`, model copies, ODB, scratch dumps.

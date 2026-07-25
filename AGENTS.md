# Mandatory Multi-Agent Bootstrap

Protocol version: 1

This repository is operated sequentially by Codex, Grok, and Gemini Antigravity.
Only one agent may work at a time.

Before reading historical handoff files, editing anything, running commands,
authorizing execution, or submitting a job:

1. Run:
   - `git status --short`
   - `git rev-parse HEAD`
   - `git log -1 --oneline`

2. Read, in order:
   - `project_coordination/START_HERE.md`
   - `project_coordination/CURRENT_STATE.md`
   - `project_coordination/ACTIVE_SESSION.json`
   - `project_coordination/ACTIVE_TASK.json`
   - `project_coordination/TASK_LEDGER.csv`
   - `project_coordination/HPC_JOB_LEDGER.csv`
   - `project_coordination/ARTIFACT_REGISTRY.csv`
   - `docs/project/PROJECT_PHASE_CHECKLIST.md`

3. Verify `ACTIVE_SESSION.json` has `active=false`.

4. Claim the session before editing:
   - `active=true`
   - `agent=codex | grok | gemini-antigravity`
   - `task_id`
   - starting commit
   - exact allowed write scope

5. Preserve every pre-existing dirty path.

6. Search `ARTIFACT_REGISTRY.csv` before creating a file.

7. Do not create duplicate or agent-specific code trees.

8. Use selective `git add` only. Never use `git add .`, broad `git clean`,
   `git reset --hard`, or destructive handoff synchronization.

9. No Abaqus/PBS submission or authorization change without a separately
   recorded explicit authorization.

10. Before ending:
    - write the session report under `project_coordination/sessions/`;
    - update coordination ledgers;
    - record tests/jobs/hashes;
    - release `ACTIVE_SESSION.json`.

Dynamic project status is maintained only under `project_coordination/`.
Do not use historical status blocks in `.agent.md` or
`adaptive_remeshing_phase_field_agent.md` as current state.

The legacy `agent_handoff/` mirror is not the active coordination system.
Do not run `scripts/sync_agent_handoff.py` unless explicitly authorized and
all unrelated handoff changes are protected.

Canonical dynamic state:

- `project_coordination/CURRENT_STATE.md`
- `project_coordination/ACTIVE_TASK.json`
- `project_coordination/ACTIVE_SESSION.json`
- `project_coordination/PROTOCOL_VERSION.json`

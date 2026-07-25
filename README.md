# Adaptive Remeshing Phase-Field Thesis

> **AI agents:** Read `AGENTS.md` before inspecting, editing, running,
> committing, authorizing, or submitting anything.

Dynamic task, authorization, and job state is maintained only under
`project_coordination/`.

This repository supports a Master's thesis on adaptive remeshing and mesh
refinement for phase-field fracture simulations in Abaqus using user elements.

## For agents

1. Open `AGENTS.md` (mandatory multi-agent bootstrap, protocol version 1).
2. Follow `project_coordination/START_HERE.md` and the active ledgers.
3. Claim `project_coordination/ACTIVE_SESSION.json` before editing.
4. Do **not** use `agent_handoff/` or `scripts/sync_agent_handoff.py` as the
   active coordination system.

## Key paths

| Path | Role |
|---|---|
| `AGENTS.md` | Mandatory multi-agent bootstrap |
| `project_coordination/` | Active lock, task, ledgers, session reports |
| `.agent.md` | Compatibility entrypoint; stable scientific rules only |
| `docs/project/PROJECT_PHASE_CHECKLIST.md` | Living phase checklist |
| `models/`, `scripts/`, `configs/`, `runs/` | Canonical scientific code and evidence |
| `docs/thesis/` | Thesis sources |

## Humans

- Complete `docs/methods/ENVIRONMENT.md` before production HPC work.
- Prefer selective `git add <paths>`; never use broad workspace cleanup while
  unrelated dirty paths exist.
- Large Abaqus outputs (`.odb` and similar) stay local/scratch, not in Git.

Historical starter-pack and flat-handoff workflows are retired. See
`project_coordination/CURRENT_STATE.md` for the live project snapshot.

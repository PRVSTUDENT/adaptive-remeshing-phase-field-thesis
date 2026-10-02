# Adaptive Remeshing Phase-Field Thesis

> **Active AI agents:** Codex and Gemini Antigravity only. Read `AGENTS.md`
> before inspecting, editing, running, committing, authorizing, or submitting
> anything.

Dynamic task, authorization, job, and session state is maintained only under
`project_coordination/`.

This repository supports a Master's thesis on mesh refinement, state transfer,
and adaptive-remeshing methods for phase-field fracture simulations in Abaqus
using user elements.

## For agents

1. Open `AGENTS.md` first (mandatory bootstrap and university-writing rules,
   protocol version 2).
2. Follow `project_coordination/START_HERE.md` and the active ledgers.
3. Verify and claim `project_coordination/ACTIVE_SESSION.json` before editing.
4. Only one agent may work at a time.
5. Active agents are **Codex** and **Gemini Antigravity**. Grok is not part of
   the active workflow.
6. Do **not** use `agent_handoff/` or `scripts/sync_agent_handoff.py` as the
   active coordination system.

## University thesis/report format

The authoritative report build is the university LaTeX package:

`MA_AdaptiveRemeshing_Report_2026/`

Key rules are defined in `AGENTS.md`. In particular:

- preserve the university `preambel.tex` and `abbrvnat_custom.bst` unless the
  human user explicitly authorizes a change;
- preserve university logos/template assets;
- write thesis content in formal, evidence-based academic style;
- distinguish offline pre-refinement, nonmatching state transfer, automated
  external-driver remeshing, and true in-analysis remeshing;
- do not overstate censored-reference comparisons, energy accounting, SDV
  irreversibility evidence, or MISESERI interpretation;
- visually inspect every rendered page before freezing a review candidate;
- do not modify a frozen supervisor-review candidate unless explicitly
  instructed.

## Key paths

| Path | Role |
|---|---|
| `AGENTS.md` | Mandatory Codex/Gemini bootstrap, governance, and writing rules |
| `GEMINI.md` | Gemini Antigravity entrypoint |
| `project_coordination/` | Active lock, task, authorization, ledgers, session reports |
| `.agent.md` | Compatibility entrypoint; stable scientific rules only |
| `docs/project/PROJECT_PHASE_CHECKLIST.md` | Living phase checklist |
| `models/`, `scripts/`, `configs/`, `runs/` | Canonical scientific code and evidence |
| `docs/thesis/` | Historical/current thesis scientific sources and evidence |
| `MA_AdaptiveRemeshing_Report_2026/` | Official university-format LaTeX report build |

## Scientific scope terminology

Use precise terminology:

- **offline error-guided pre-refinement** for fixed meshes generated before the
  fracture analysis;
- **nonmatching state transfer/restart** for transfer of `u`, `d`, and `H`
  between discretizations;
- **automated external-driver adaptive remeshing** for chained solve/remesh/
  transfer/restart cycles controlled outside one continuously running Abaqus
  analysis;
- **online/in-analysis adaptive remeshing** only when genuinely demonstrated
  inside the running analysis.

## Humans

- Complete/update `docs/methods/ENVIRONMENT.md` before production HPC work when
  environment details change.
- Prefer selective `git add <paths>`; never use broad workspace cleanup while
  unrelated dirty paths exist.
- Large Abaqus outputs (`.odb` and similar) stay local/scratch, not in Git.
- Explicit human authorization remains required whenever the active governance
  state requires it for HPC submission or external actions.

Historical starter-pack and flat-handoff workflows are retired. See
`project_coordination/CURRENT_STATE.md` for the live project snapshot.

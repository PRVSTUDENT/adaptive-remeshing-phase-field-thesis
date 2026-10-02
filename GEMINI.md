# Gemini Antigravity Project Entry

Protocol version: 2

Gemini Antigravity is one of the two active project agents. The active agent
set is:

- Codex
- Gemini Antigravity

Grok and other autonomous agents are not part of the active workflow unless the
human user explicitly changes this rule.

Before any action, read and follow:

1. `AGENTS.md`
2. `project_coordination/START_HERE.md`
3. `project_coordination/CURRENT_STATE.md`
4. `project_coordination/ACTIVE_SESSION.json`
5. the remaining active coordination ledgers listed by `START_HERE.md` and
   `AGENTS.md`.

Do not begin work until `ACTIVE_SESSION.json` has been checked and claimed.
Only one agent may hold the active session at a time.

## University-Style Writing Requirement

For any thesis/report drafting or editing, follow the university-format and
scientific-writing rules in `AGENTS.md`.

In particular:

- treat `MA_AdaptiveRemeshing_Report_2026/` as the authoritative university
  LaTeX report build;
- preserve `preambel.tex`, `abbrvnat_custom.bst`, and university template
  assets unless explicitly authorized otherwise;
- do not modify a frozen supervisor-review candidate unless explicitly asked;
- keep scientific claims evidence-backed and scoped to the actual validation
  boundary;
- distinguish fixed offline pre-refinement from automated external-driver
  remeshing and from true online/in-analysis remeshing;
- inspect the rendered PDF page-by-page before declaring a build ready;
- keep internal agent/controller/quota language out of the scientific report.

## Coordination and Safety

Current task state, authorization, and HPC job state come only from
`project_coordination/`.

Do not use `agent_handoff/`, old chat text, or historical reports as authority
for the live task.

Routine progress commits and forward-only `git push origin main` of non-bulky, governed project state (excluding `.odb`, solver runtime logs, and credentials) are authorized and mandatory at session and milestone closeouts to keep GitHub continuously synchronized. Do not email, upload externally, submit/cancel/move HPC jobs, or perform destructive repository cleanup unless explicitly authorized.

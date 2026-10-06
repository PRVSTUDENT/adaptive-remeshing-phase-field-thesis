# Mandatory Codex + Gemini Antigravity Bootstrap Rules

Protocol version: 2

This repository is operated sequentially by **Codex** and **Gemini Antigravity**.
Only one agent may work at a time.

**Grok is not part of the active project workflow and must not be used as a
coordination or execution agent for this repository.**

## Mandatory Instruction for New Agents

Before performing any work in this repository, open the repository-root
`AGENTS.md` and follow this bootstrap procedure. Then read the
`project_coordination/` files in the stated order, verify that
`ACTIVE_SESSION.json` has `active=false`, and claim the session before making
changes.

Do not infer current task state, authorization, or job state from old chat
messages, historical handoff files, or stale reports. Live state and authority
are maintained under `project_coordination/`.

## Initial Environment Commands

Before starting, the agent must run:

```powershell
cd "D:\Master thesis\Adaptive remeshing"

git status --short
git rev-parse HEAD
git log -1 --oneline
```

The repository may contain unrelated dirty user work. Never clean, reset,
restore, checkout, or stash unrelated paths merely to obtain a clean tree.

## Mandatory File Reading Order

Before reading historical handoff files, editing anything, running commands,
authorizing execution, or submitting a job, the agent MUST read these files
**in this exact order**:

1. **`AGENTS.md`** — mandatory bootstrap and writing/governance rules.
2. `project_coordination/START_HERE.md`
3. `project_coordination/CURRENT_STATE.md`
4. `project_coordination/ACTIVE_SESSION.json`
5. `project_coordination/ACTIVE_TASK.json`
6. `project_coordination/TASK_LEDGER.csv`
7. `project_coordination/HPC_JOB_LEDGER.csv`
8. `project_coordination/ARTIFACT_REGISTRY.csv`
9. `docs/project/PROJECT_PHASE_CHECKLIST.md`

## State and Authority Rules

- `project_coordination/` is the only authoritative source for live task,
  authorization, job, and coordination state.
- `.agent.md`, `adaptive_remeshing_phase_field_agent.md`, previous chat text,
  and `agent_handoff/` may contain stable background or historical context but
  must not override the current coordination state.
- `agent_handoff/` and `scripts/sync_agent_handoff.py` are retired as active
  coordination mechanisms.
- Only one of Codex or Gemini Antigravity may hold the active session lock at a
  time.
- Routine progress commits and forward-only `git push origin main` of governed project state (model decks, Fortran source, scripts, tests, reports, and coordination ledgers, strictly excluding bulky solver binaries, runtime logs, and credentials) are authorized and mandatory as part of session and milestone closeouts to keep GitHub continuously synchronized.
- Do not email, upload to external non-GitHub endpoints, submit HPC jobs, cancel jobs, or move queued jobs unless explicitly authorized.
- Prefer selective edits and selective `git add <paths>`; never use broad workspace cleanup in a dirty repository.


## Scheduler Policy (Holiday-Window Concurrency: Demonstrated Minimum >= 10)

- **Empirical Demonstration**: 10 simultaneous running jobs using 97 CPUs (Jobs 1403368–1403377) actively demonstrated in `normal_imfdfkmq`.
- **Queue Limits Established**:
  - No explicit per-user `max_run` job-count limit on `normal_imfdfkmq`.
  - Per-user running CPU limit: **640 CPUs**.
  - Per-user running memory limit: **4 TB**.
  - Theoretical CPU headroom: ~543 additional CPUs with 97 CPUs currently allocated (node availability and placement permitting).
- **Policy Stance**: **10 is a demonstrated minimum capability floor, not a ceiling**.  - **Expansion Guideline**: During the September-9 window, Antigravity can cautiously expand to **15-20 useful Mode-I jobs** where scientifically justified:
    - 8-thread scaling/parity jobs on larger fixed/reference/adaptive meshes (or independent 16-thread qualification cases when explicitly authorized);
    - additional deterministic repeats where scientifically required;
    - post-processing/extraction jobs if those genuinely need PBS resources.
  - **Governing Constraint**: **Scientific usefulness**, not an arbitrary job-count cap. Strictly NO redundant or dummy jobs just to test capacity. Every job must be independently justified, qualified, and explicitly authorized within the active gate sequence.
  - **Execution Architecture**: Because `f42_mixed_uel.for` is not qualified for true multi-rank MPI, distributed multi-rank MPI is strictly disqualified. Individual Abaqus jobs must execute in single-rank shared-memory mode: 1-CPU serial serves as the authoritative scientific reference anchor; 8-thread shared-memory SMP is empirically qualified for the tested Mode-I formulation and controls; 16-thread shared-memory execution is UNQUALIFIED pending independent Stage-A/B verification; and 4-thread shared-memory execution is not part of the active approved execution path. High throughput is achieved primarily by running many independent scientific jobs concurrently.
- Baseline nominal active project jobs (reference): 4 (`MAX_TOTAL_ACTIVE_PROJECT_JOBS=4` baseline, superseded for the holiday window). Observed scheduler concurrency is recorded as >= 10.

# University-Style Thesis and Report Writing Rules

These rules apply to all thesis/report material generated or edited by Codex
or Gemini Antigravity.

## 1. Authoritative University Format

The official university LaTeX package is the formatting master:

`MA_AdaptiveRemeshing_Report_2026/`

The university infrastructure must be preserved unless the human user
explicitly authorizes a formatting change.

In particular:

- preserve `MA_AdaptiveRemeshing_Report_2026/preambel.tex` unchanged;
- preserve `MA_AdaptiveRemeshing_Report_2026/abbrvnat_custom.bst` unchanged;
- preserve university logos and supplied template assets unchanged;
- keep `main.tex` focused on document assembly and content inclusion;
- place thesis-specific content in modular chapter/front-matter files;
- do not copy formatting hacks from older donor thesis sources into the
  university template when the template already controls that formatting.

The official thesis title must not be changed without explicit human approval.

## 2. Frozen Supervisor-Review Candidate

When the coordination state marks a thesis PDF as frozen for supervisor review:

- do not modify the frozen PDF or its source tree unless explicitly instructed;
- new post-freeze research must be developed in separate experimental/code and
  evidence paths;
- integrate new results into the thesis only after explicit human instruction;
- preserve the frozen candidate hash and page count in the coordination record.

## 3. Scientific Writing Style

Write in concise, formal, evidence-based academic English suitable for a
Master's thesis at TU Bergakademie Freiberg.

Required style:

- state what was **implemented**, **validated**, **observed**, **inferred**, and
  **left as future work** separately;
- never present a hypothesis, correlation, or plausible mechanism as a proven
  cause without supporting evidence;
- avoid promotional or absolute wording such as “guarantees,” “proves,”
  “perfect,” “fully validated,” or “complete” unless the exact claim is
  supported by the stated validation boundary;
- prefer scoped wording such as “for the tested configuration,” “within the
  common validation window,” or “at the saved output states” where applicable;
- use consistent symbols, units, terminology, and model names throughout;
- distinguish exact scheduler measurements from rounded/derived values;
- distinguish diagnostic comparisons from strict like-for-like speedups;
- distinguish algorithmic enforcement from independently postprocessed
  observational evidence.

Do not place internal automation/controller language in the scientific body,
including quota status, bridge IDs, controller turns, agent names, or internal
workflow errors. Job IDs, hashes, and operational details belong in a concise
reproducibility appendix when scientifically useful.

## 4. Required Scope Terminology for This Project

Maintain these distinctions unless new evidence explicitly changes the project
scope:

- **Offline error-guided pre-refinement:** fixed non-uniform mesh generated
  before the fracture run using error-indicator information.
- **Nonmatching state transfer / restart:** transfer of displacement, phase, and
  history variables between different discretizations followed by the validated
  restart procedure.
- **Automated external-driver adaptive remeshing:** automatically chained solve
  → evaluate → remesh → transfer → restart → continue cycles driven outside a
  single continuously running Abaqus analysis.
- **Online/in-analysis adaptive remeshing:** reserve this term for a genuinely
  runtime in-analysis remeshing implementation if and when it is demonstrated.

Do not call fixed MM/PK5 pre-refined meshes “online adaptive remeshing.”

## 5. Phase-Field and Numerical Claim Discipline

Unless an active scientifically approved task changes them, preserve the
canonical formulation and conventions documented in the project evidence.

At minimum:

- `d = 0` means intact and `d = 1` means broken;
- phase bounds are `0 <= d <= 1`;
- damage irreversibility and history monotonicity must be stated only at the
  level actually verified;
- `H >= 0` and history monotonicity must not be conflated with an independent
  proof of every projected/visualized phase-field representation;
- MISESERI is a recovery-based stress-discretization indicator, not a
  phase-field error estimator;
- any Zienkiewicz–Zhu-style equation used to interpret MISESERI must be labeled
  as the thesis interpretation/adopted formulation unless Abaqus documentation
  explicitly defines that exact internal equation;
- state-transfer claims must preserve slit/flank topology and identify the
  transfer/sampling space used;
- standard Abaqus energy outputs must not be described as a complete UEL-aware
  thermodynamic energy balance when UEL fracture energy is not independently
  accounted for.

## 6. Censored References and Accuracy Claims

When a reference simulation terminates before the requested endpoint:

- explicitly call it censored/terminated at the recorded endpoint;
- define the common comparison domain before computing errors;
- keep post-censoring comparisons separate from reference-based validation;
- describe MM/PK5 comparisons beyond the uniform-reference endpoint as internal
  mutual diagnostics unless a new uncensored reference is available;
- do not silently convert provisional working criteria into universal physical
  acceptance thresholds.

## 7. Figures and Tables

Every figure and table included in the university-format report must be checked
against the underlying data before release.

Figures must:

- use publication-quality labels and readable fonts;
- show physical variables and units explicitly;
- avoid internal names such as “v3,” “unchanged,” “test,” or controller-stage
  labels unless scientifically meaningful;
- use terminology consistent with the text (for example, “locally refined”
  rather than “adaptive” for fixed pre-refined meshes);
- avoid clipped data, labels, legends, or annotations;
- state censoring/termination limits where they affect interpretation;
- have captions that agree with the plotted values.

Tables must:

- agree numerically with the main text and figures;
- identify whether time is CPU time or walltime;
- use one authoritative accounting convention consistently;
- include provenance identifiers only where useful for reproducibility.

## 8. Citations and Bibliography

- Use the university bibliography workflow and `abbrvnat_custom.bst`.
- Maintain the thesis bibliography in the template's `literature.bib` unless an
  active task explicitly specifies a different file.
- Do not fabricate authors, titles, journals, years, pages, issues, URLs, or
  DOIs.
- Foundational claims must cite the correct foundational source.
- Verify new references before adding them.
- Distinguish Abaqus documentation from independent scientific literature.

## 9. AI-Tool Disclosure

Repository execution agents are **Codex** and **Gemini Antigravity only**.
Do not introduce Grok or any other autonomous agent into the project workflow
without explicit human approval.

The thesis/report AI-use declaration must remain concise and must reflect the
actual tools the human user decides to disclose. Do not expand it into prompt
logs or detailed interaction histories unless the university explicitly
requires that level of disclosure.

This repository-agent rule does not by itself authorize changing an already
frozen thesis declaration.

## 10. University-Format Build and Visual QA

Before declaring a report/thesis build ready for review:

1. compile with all LaTeX/BibTeX passes needed to resolve references, contents,
   figures, tables, and bibliography;
2. confirm zero unresolved `??` references and zero undefined citations;
3. inspect every rendered page, not only the LaTeX source;
4. identify blank pages as intentional template behavior or unintended output;
5. remove only unintended blank pages without altering the university preamble;
6. verify title page, logos, margins, headers, page numbering, chapter headings,
   equations, tables, figures, bibliography, appendix, and PDF metadata;
7. compute and record the final PDF SHA-256 when a candidate is frozen.

## 11. Reproducibility and Evidence Placement

Keep the scientific narrative readable. Detailed implementation provenance may
be placed in appendices or project records, including:

- PBS job IDs;
- exact CPU/walltime accounting;
- SHA-256 hashes;
- package manifests;
- solver failure diagnostics;
- notification/monitoring details.

Do not let operational infrastructure dominate the main scientific argument.

## 12. Agent-Specific Responsibility

Both Codex and Gemini Antigravity must follow the same scientific, formatting,
coordination, and authorization rules.

If an agent discovers a conflict between:

1. explicit current human instruction;
2. current `project_coordination/` state;
3. these repository rules;
4. historical documents;

it must preserve evidence, avoid destructive action, and resolve the conflict
in that priority order, subject to any mandatory safety/governance constraints.

## 13. Runtime Artifact Existence Guard

Before using `view_file` or any equivalent file-reading tool on a generated or runtime artifact, first establish that the exact path exists.

This applies especially to:
- `pbs_execution.log`
- Abaqus `.log`, `.dat`, `.msg`, `.sta`, `.prt`, `.odb`
- scheduler-generated output
- generated evidence files
- files expected from an HPC transfer

Required procedure:
1. Use a shell existence check such as `Test-Path`, `Get-Item`, or `Get-ChildItem` first.
2. Only invoke `view_file` after the exact path has been confirmed to exist.
3. If the expected file does not yet exist, do not call `view_file` on it.
4. Determine whether:
   - the job has not been submitted,
   - the job is still running,
   - the file has not yet been transferred,
   - the filename differs,
   - or the producing step failed.
5. Missing runtime output is evidence about workflow state, not permission to invent its contents.
6. A missing `pbs_execution.log` must never by itself trigger resubmission.
7. Before retrying any HPC submission after a tool or agent crash, check `qstat` and `HPC_JOB_LEDGER.csv` for an already-created exact job ID.

## 14. Non-Interactive SSH Command Safety Policy

All noninteractive cluster SSH inspection and query commands MUST follow these rules:

1. **Mandatory `-n -T` and BatchMode Directives**:
   - Every read/query SSH invocation must pass `-n -T -o BatchMode=yes`.
   - The `-n` flag redirects standard input from null, guaranteeing that accidental syntax truncation or quoting errors cannot cause remote tools to hang indefinitely waiting on `stdin`.

2. **Prohibition of Nested `bash -c` Wrappers**:
   - Never wrap simple remote inspection commands in nested `bash -c`, `bash -lc`, or `sh -c`.
   - Pass the remote command directly to SSH (e.g. `ssh -n -T -F <config> <host> "tail -n 25 -- <file>"`).
   - For complex multi-command remote logic, create and upload a temporary `.sh` script rather than constructing nested quote strings.

3. **Explicit Target Arguments (No Bare Stdin Consumers)**:
   - Programs such as `tail`, `head`, `cat`, `grep`, `sed`, `awk`, `python`, and `bash` must always have explicit file/target arguments.
   - Bare invocations that wait on `stdin` are strictly prohibited.

4. **Bounded Execution Timeout & Mandatory Guarded Wrapper**:
   - Every controller-spawned SSH command must have an independent execution timeout (default 120 seconds).
   - If a timeout occurs, the controller terminates only that spawned SSH process tree, records the failure, and returns a non-zero exit code, allowing the agent to recover within the same turn without consuming the full turn timeout.
   - **MANDATORY**: All remote cluster operations MUST be invoked via the guarded wrapper:
     `powershell -NoProfile -ExecutionPolicy Bypass -File .\.agents\scripts\Invoke-GuardedSsh.ps1 -RemoteCommand "<cmd>"`
   - Raw, un-guarded `ssh` invocations in automated controller turns are strictly prohibited.

5. **Prohibition of Whole-Tree Searches and Heavy NFS File Scans**:
   - The remote cluster project directory contains over **1.3 TB of simulation outputs** (`.odb`, `.res`, `.sim`, `.pac`).
   - Whole-tree recursive commands such as `find /home/... -exec sha256sum`, un-excluded `grep -r`, or broad Python `os.walk` without directory pruning are **STRICTLY PROHIBITED** and fail closed.
   - Any remote file inspection or hash verification must explicitly target specific directories (e.g. `models/pandey_kumar_mode1/04_sharp_slit_test/`) and exclude binary simulation formats.


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

# Batch-Oriented HPC Execution

Batch execution is the default for this project unless the user explicitly
requests a one-job-at-a-time process.

Before proposing or submitting a batch:

1. Review the current scientific and coordination state.
2. Separate work into:
   - independent jobs that may be submitted together;
   - dependent jobs blocked on scientific review of a predecessor;
   - optional sensitivity jobs that run only when scientifically justified.
3. Prepare one batch plan that records:
   - exact job names and scientific purposes;
   - model, package, and revision;
   - input-deck and user-subroutine hashes;
   - CPUs, memory, walltime, queue, and execution mode;
   - expected outputs and acceptance criteria;
   - dependencies;
   - maximum permitted submissions;
   - `automatic_retry=false` unless separately authorized.

Authorization and submission rules:

- One explicit human approval may authorize the complete, specifically listed
  batch and must state the maximum number of jobs.
- Explicit approval remains mandatory before any Abaqus/PBS submission. This
  rule controls if another instruction appears to permit direct submission
  without approval.
- After approval, create one authorization update, make one normal commit,
  fast-forward the cluster clone, run common preflight checks once, and submit
  all approved independent jobs together.
- Use guarded submission wrappers. Never invoke direct `qsub` unless it is
  explicitly authorized.
- Never submit a job more than once and never retry a failed job automatically.
- A failed job must be scientifically and technically reviewed before any
  replacement submission.

Scheduler policy:

- At most two jobs may run simultaneously.
- Additional approved independent jobs may remain queued and start
  automatically as capacity becomes available.
- Do not use `qmove` or `qdel` unless explicitly authorized.
- Do not increase CPUs, memory, or walltime without scientific or measured
  technical justification.
- Do not submit speculative work merely to fill the queue.
- Do not queue dependent work before its predecessor has been scientifically
  reviewed.

Batch closeout:

- Collect lightweight scheduler, solver, validator, extracted-result, and
  Telegram evidence together after the batch finishes.
- Classify every job separately, compare the batch scientifically in one
  combined analysis, and use one combined GitHub closeout when practical.
- Preserve full Git SHAs and input/source/evidence hashes.
- Distinguish user-provided scheduler information from independently verified
  repository facts.
- Do not commit Abaqus binary outputs, including `.odb`, `.sim`, `.res`,
  `.pac`, `.abq`, `.sel`, or equivalent large solver artifacts.

Repository safety:

- No `git reset --hard`, `git clean`, casual stash, `git add .`,
  `git add -A`, `commit --amend`, force push, or broad destructive action.
- Stage files selectively, preserve unrelated dirty work, and release
  `ACTIVE_SESSION.json` normally.
- Prefer one meaningful commit and closeout over repeated metadata-only updates.

Scientific sequence for the current thesis phase:

1. Uniform reference verification.
2. H0/H1/H2 comparison as scientifically required.
3. Pandey-Kumar MISESERI coarse pre-analysis.
4. MISESERI-based refinement workflow.
5. Refined phase-field simulation.
6. Accuracy-versus-cost comparison.
7. Controlled evolving remeshing and state transfer.
8. Final thesis validation and documentation.

Batch only scientifically independent, sufficiently defined work. Reproducibility,
dependency control, validation, and formulation consistency take precedence over
reducing token usage or scheduler idle time.

# Immediate-Failure Recovery Policy

Do not return to the user for an immediately diagnosable implementation
failure if the repair is local/offline, deterministic, scientifically
equivalent, and within the authorization boundary.

If the first attempt fails:

1. Capture the exact error.
2. Identify the first concrete root cause.
3. Apply the smallest valid repair yourself.
4. Re-run the failed check.
5. Run affected regression tests.
6. Continue the remaining task if the repair passes.
7. Preserve both the original failure and repair evidence.

For known likely failure modes:

- Deterministic local/offline failures (wrong path, missing directory, syntax/API mismatch, environment variable, stale hash, missing generated metadata, CAE object name mismatch, SSH alias issue, etc.): diagnose, apply minimal repair, rerun validation, and continue.
- If Abaqus/Python API rejects a method for a specific version: inspect actual API/object state and use alternative supported API method.
- Do not perform repeated blind retries; base repair strictly on empirical error evidence.

HPC execution safety boundary:
- Automatic repair is permitted ONLY for local/offline preparation and pre-submission checks.
- Do NOT perform an unauthorized second `qsub`, replacement job, retry job, downstream job, `qdel`, or `qmove`.
- A consumed one-submission authorization remains strictly consumed.
- A modified executable package still requires a new P/Q qualification and fresh human authorization.

STOP and return to the user when:
- the failure changes scientific assumptions;
- multiple scientifically different choices exist;
- required source information is missing;
- the repair would alter an already qualified package;
- new HPC authorization is required;
- another qsub/retry/replacement would be required;
- destructive Git/HPC actions would be required;
- or the cause remains uncertain after reasonable diagnosis.


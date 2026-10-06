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
    - release `ACTIVE_SESSION.json`;
    - commit and push governed project progress to GitHub `origin/main` (see Regular Remote Git Synchronization Protocol).

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

- **Holiday-Window Concurrency Policy (Active until September 9, 2026)**:
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
- Standard baseline policy (historical reference):
  - Baseline nominal active project jobs (Q or R): 4 (`MAX_TOTAL_ACTIVE_PROJECT_JOBS=4` baseline, superseded for the holiday window).
  - Maximum ordinary scientific production jobs running concurrently: 3 (`MAX_ORDINARY_PRODUCTION_JOBS=3`).
  - Reserved MPI/parallelization qualification slot: 1 (`RESERVED_MPI_QUALIFICATION_SLOTS=1`).
  - The reserved slot is strictly for MPI/threading qualification, debugging, datacheck, or deliberately small parallel validation cases.
  - Observed scheduler concurrency is recorded as >= 10.
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

# Mandatory Dual-Channel Notification Policy

Every generated PBS execution script and submission wrapper MUST include dual-channel (email + Telegram) notification integration:

1. **PBS Mail Directives**:
   - `#PBS -m abe` (notify on abort, begin, end).
   - `#PBS -M pr21vyci@mailserver.tu-freiberg.de` (or configured notification recipient).

2. **Telegram & Email Shell Traps & Wrappers**:
   - Source `$HOME/projects/adaptive-remeshing/scripts/hpc/notifications/job_notifications.sh` or local package copy.
   - Load `NOTIFICATION_CONFIG` (default `~/.config/adaptive-remeshing/notifications.env` or `notifications.json`, permissions 600).
   - Wrappers must issue `notify_submitted` upon successful `qsub` submission.
   - PBS scripts must issue `notify_start` upon job environment initialization prior to solver execution.
   - PBS scripts must install `notification_install_terminal_trap` to automatically send `COMPLETED`, `FAILED`, or `TERMINATED` notifications with exit code, elapsed runtime, and termination reason upon exit, signal, or failure (firing exactly once).

3. **End-to-End Delivery Verification (Static Code Presence Is Not Sufficient)**:
   - Static code presence (directives, script sourcing, trap calls) is necessary but **NOT SUFFICIENT** to claim qualification pass.
   - A package may not claim `dual_channel_notification_contract = PASS` merely because `#PBS -m abe`, `job_notifications.sh`, `notify_start`, or terminal traps exist.
   - Qualification PASS strictly requires:
     1. Notification configuration resolved successfully (`~/.config/adaptive-remeshing/notifications.env` or `.json`, mode 600);
     2. Required Telegram token and chat ID variables verified non-empty without leaking secret values;
     3. Real Telegram API connectivity test (`api.telegram.org` acknowledgement `ok=true`, HTTP 200) verified for the applicable execution path;
     4. Guarded wrapper `SUBMITTED` code path tested;
     5. PBS `STARTED` code path tested;
     6. Terminal `COMPLETED` / `FAILED` / `TERMINATED` trap logic tested;
     7. Zero secrets exposed, logged, or committed;
     8. Configuration path and safe permissions recorded.
   - The qualification field `telegram_notification_contract = PASS | FAIL | UNRESOLVED` is mandatory for all future HPC qualification reports. If compute-node outbound connectivity remains unproven, compute-node start/terminal delivery must be classified as `UNRESOLVED` while login-node submission delivery is classified as `PASS`.



Repository safety and Remote Synchronization:

- No `git reset --hard`, `git clean`, casual stash, `git add .`,
  `git add -A`, `commit --amend`, force push, or broad destructive action.
- Stage files selectively, preserve unrelated dirty work, and release
  `ACTIVE_SESSION.json` normally.
- Prefer one meaningful, self-contained commit per task or substantive milestone.
- **Regular Remote Git Synchronization Protocol**:
  - Keep GitHub `origin/main` continuously synchronized with ongoing local and HPC progress.
  - At the completion of each substantive task, qualified scientific milestone, batch manifest generation, reproduction package freeze, or controller turn closeout, the agent must commit all governed changes (model input decks, user subroutines, scripts, tests, reports, and coordination ledgers) and push them via forward-only `git push origin main`.
  - Strictly exclude bulky solver artifacts (`.odb`, `.sim`, `.res`, `.pac`, `.abq`, `.sel`, `.dat`, `.msg`, `.sta`, `.prt`, `.log`), runtime traces (`*trace.csv`), local caches, credentials (`telegram.env`, `*.telegram-token`), and scratch outputs.
  - Forward-only `git push origin main` of qualified, non-bulky project state is authorized and mandatory standard operating procedure.

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

# Runtime Artifact Existence Guard

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

# Non-Interactive SSH Command Safety Policy

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




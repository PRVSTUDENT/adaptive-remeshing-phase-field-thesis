> [!IMPORTANT]
> MULTI-AGENT BOOTSTRAP — PROTOCOL VERSION 1
>
> Before doing any work, read AGENTS.md and then
> project_coordination/START_HERE.md.
>
> Current task, authorization, job, and workflow state are maintained only under
> project_coordination/.
>
> Any current-stage or immediate-next-task text later in this file is historical
> unless it matches project_coordination/CURRENT_STATE.md and
> project_coordination/ACTIVE_TASK.json.
>
> The flat agent_handoff/ mirror is not the active coordination system.
> Do not run its synchronization utility unless explicitly authorized.
>
> Dynamic state lives in:
> - project_coordination/CURRENT_STATE.md
> - project_coordination/ACTIVE_SESSION.json
> - project_coordination/ACTIVE_TASK.json

# Name: Adaptive Remeshing Phase-Field Thesis Codex Agent

## Summary

- Purpose: workspace-scoped engineering/research agent for the Master's thesis **"Application of Built-in Adaptive Remeshing and Mesh Refinement Features in Abaqus to Fracture Simulations Using Phase-field User Elements."**
- Main objective: reproduce a verified phase-field fracture baseline in Abaqus, implement the Pandey-Kumar MISESERI-driven pre-refinement workflow, preserve the scientific meaning of the UEL/UMAT fields, integrate IMFD/ABAQUSER post-processing, and quantify accuracy versus computational cost.
- Operating principle: **baseline first, one controlled change at a time, quantitative gates before claims.**
- Coordination principle: dynamic task/job/authorization state is maintained only under project_coordination/ (see AGENTS.md and START_HERE.md). The flat agent_handoff/ mirror is historical/optional and is **not** the active coordination system; do not run scripts/sync_agent_handoff.py unless explicitly authorized and unrelated dirty paths are protected.
- Report principle: keep living LaTeX reports for the active thesis stage updated after substantial validation, failure, repair, submission, or result. Read the active reporting requirements from `CURRENT_STATE.md`, `ACTIVE_TASK.json`, and `PROJECT_PHASE_CHECKLIST.md`. Do not create a new report for every run, and do not remove failed attempts from execution/failure logs. Generated PDFs remain local build artifacts and ignored.
- Checklist principle: `docs/project/PROJECT_PHASE_CHECKLIST.md` is the authoritative living task and phase checklist. Update it after every substantial operation and keep technical completion separate from scientific validation.
- Mistakes-ledger principle: `docs/project/MISTAKES_AND_FIXES_LOG.md` is mandatory project memory. Append every failed attempt, diagnosis, correction, rerun, and prevention rule; never overwrite or delete a predecessor failure when a later attempt passes.

## Current project state

Do not maintain dynamic project state in this file.

Read:

- project_coordination/CURRENT_STATE.md
- project_coordination/ACTIVE_TASK.json
- project_coordination/TASK_LEDGER.csv
- docs/project/PROJECT_PHASE_CHECKLIST.md

The current active operation is controlled by those files.

Historical narrative previously kept in this section is obsolete as a live ledger.
Stable scientific rules remain in the sections below.

## HPC access, queues, resources, and operating limits

Source and freshness:

- Evidence source: `HPC_Upgraded_Resources_and_Software.md` together with retained PBS job evidence and the workspace handoff.
- Snapshot date: 2026-07-20.
- This resource snapshot supersedes previous-project resource labels and policies, including “Stage 16N”. Do not copy a previous project's fixed CPU, memory, concurrency, or wall-time defaults into this thesis.
- Queue load, node state, free memory, and availability are dynamic. Never treat this snapshot as a reservation or guaranteed capacity.
- Queue ACLs and group membership show eligibility to submit; they do not guarantee immediate scheduling, software-license availability, or a particular node.
- The filesystem figures below are cluster-wide filesystem capacity/usage values, not personal storage quotas.

Account and access:

- HPC user: `pr21vyci` (`uid=50839`).
- Relevant access roles include general HPC user, teaching, Kiefer/AMS hardware, and Gaussian:
  - `t2-dl-rights-hpc_user`
  - `t2-dl-rights-hpc_teaching`
  - `t2-dl-rights-hpc_hw_kieferams`
  - `t2-dl-rights-hpc_gaussian`
- Windows SSH access is already configured through the user's explicit SSH profile:
  - config file: `$env:USERPROFILE\.ssh\codex_config`
  - host alias: `tu_freiberg`
  - canonical interactive login:
    ```powershell
    ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg
    ```
  - canonical one-command form:
    ```powershell
    ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg "<remote-command>"
    ```
  - current-job monitoring:
    ```powershell
    ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg "qstat -u pr21vyci"
    ```
- Treat this SSH profile and alias as the authoritative access method for this project. Do not create a competing host entry, replace the config file, or assume the default `$env:USERPROFILE\.ssh\config` is being used.
- Before any HPC submission or file transfer, verify the resolved account and cluster context:
  ```powershell
  ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg "hostname; whoami; pwd; id; groups"
  ```
- For a persistent interactive session, first establish the login with the canonical command above, then perform module inspection, file staging, and PBS work on the remote shell.
- For scripted checks, prefer the one-command form so the exact SSH profile and host alias remain explicit in logs.
- If the SSH connection fails from an external network, confirm the institutional VPN is active before changing SSH keys or configuration. The existing VPN-service commands remain in the protected user-notes section.

Storage:

- Home: `/home/pr21vyci`.
- Scratch: `/scratch/pr21vyci`.
- Snapshot filesystem status from the upgraded-resource note:
  - `/home`: 17 TB total, 12 TB used, 4.2 TB available, 74% used.
  - scratch backing filesystem shown as `/scratch9`: 28 TB total, 25 TB used, 3.2 TB available, 89% used.
- These values are point-in-time cluster-wide usage figures. Re-run `df -h /home /scratch` before every substantial campaign because scratch pressure is currently high in the recorded snapshot.
- Use home for source, scripts, small inputs, reports, and retained metadata.
- Use scratch for Abaqus work directories, `.odb`, `.sim`, restart, temporary, and other large solver files.
- Every PBS job must stage required inputs to its work directory and copy retained outputs back explicitly.
- Do not infer a personal quota from `df`; query the site quota command or support team before large campaigns.
- Never delete raw results without user approval and a verified retention/stage-out plan.

Submission routes and wall-time ceilings observed in the snapshot:

| Purpose             | Submit queue                           | Scheduler destination / limit                                                                                            | Access interpretation                                                                  |
| ------------------- | -------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| General CPU jobs    | `entryq`                             | routes to`shortq` (12 h), `mediumq` (36 h), `longq` (168 h), `gpuq` (24 h), and configured short fat-node queues | eligible through general HPC-user rights                                               |
| Kiefer/AMS CPU jobs | `entry_imfdfkmq`                     | routes to`short_imfdfkmq` (12 h) or `normal_imfdfkmq` (336 h)                                                        | eligible through`hpc_hw_kieferams` rights; preferred thesis route when appropriate   |
| Teaching jobs       | `entry_teachingq`                    | routes to`teachingq` (24 h)                                                                                            | eligible through teaching rights; use only when the work fits teaching-queue policy    |
| Short test jobs     | `testq`                              | maximum wall time 4 h; queue advertises up to one GPU                                                                    | eligible through general HPC-user rights; suitable for small environment/smoke checks  |
| GPU jobs            | `gpuq` or routing through `entryq` | maximum wall time 24 h                                                                                                   | eligibility exists, but Abaqus GPU benefit/license support must be verified before use |

Queue rules:

- Prefer route queues such as `entryq`, `entry_imfdfkmq`, and `entry_teachingq`.
- Do not submit directly to execution queues marked `from_route_only`.
- Use the Kiefer/AMS route for thesis Abaqus work only when its policy and requested resources match the job.
- Do not request a GPU merely because GPU nodes are visible. The current Molnar UEL/UMAT baseline is CPU-oriented, and GPU acceleration has not been validated.
- Do not request more CPUs, memory, or wall time than justified by a measured smaller run.
- Queue-level maxima are not automatically per-job or per-user entitlements. Confirm effective limits with `qstat -Qf`, the scheduler response, and site documentation.

### Stage C queue-selection policy (mandatory)

Choose the **shortest-wait eligible** queue from live status and resource limits.
**Do not hard-code `normal_imfdfkmq` for small smoke, pre-analysis, CAE, or integrity jobs.**

| Job | Resources | Preferred submit queue |
|---|---:|---|
| Job 1 smoke | 1 CPU, 8 GB, 1 h | `entry_imfdfkmq` |
| Job 2 H0 pre-analysis | 1 CPU, 16 GB, 2 h | `entry_imfdfkmq` when eligible |
| Job 3 CAE remesh | 1 CPU, 16 GB, 1 h | `entry_imfdfkmq` |
| Job 4 integrity | 1 CPU, 16 GB, 2 h | `entry_imfdfkmq` when eligible |
| Job 5 full fracture | 1 CPU, 32 GB, 6 h | `normal_imfdfkmq` unless another eligible queue is faster |

Before every submission:

```powershell
ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg "qstat -Qf entry_imfdfkmq | egrep -i 'enabled|started|resources_max|state_count'"
ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg "qstat -q"
```

Record `stime - qtime` wait for each job. `entry_imfdfkmq` is a route queue and may land on `short_imfdfkmq` or `normal_imfdfkmq` after routing.

Observed node classes:

| Node class                  | Typical advertised resources                                                                | Relevant queues / notes                                                           |
| --------------------------- | ------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Main CPU node               | 40 CPUs, about 190,016,512 KB memory (approximately 181 GiB), no GPU                        | general short/medium/long and related queues                                      |
| Kiefer/AMS extension-2 node | 16 CPUs, about 784,570,368 KB memory (approximately 748 GiB), about 1.48 TiB virtual memory | `normal_imfdfkmq`, `short_imfdfkmq`, `testq`; some nodes also list teaching |
| Fat-memory node             | 40 or 64 CPUs; approximately 748 GiB or approximately 3.0 TiB memory depending on node      | access is queue/scheduler dependent; not guaranteed by visibility                 |
| GPU node                    | 40 CPUs, approximately 181 GiB memory, one GPU                                              | `gpuq`, `testq`, and selected teaching/general routes                         |

### Adaptive-remeshing thesis resource policy

This policy is specific to the current phase-field/adaptive-remeshing thesis and supersedes previous-project “Stage 16N” guidance.

Resource classes:

| Work type                                             | Initial request                                                           | Scaling rule                                                                      |
| ----------------------------------------------------- | ------------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| Static validation, deck generation, manifest building | 1 CPU, 4-8 GB                                                             | Increase only when the script actually supports parallel work                     |
| Abaqus/CAE ODB extraction or consolidated replay      | 1 CPU, 16 GB                                                              | CAE postprocessing is not treated as a solver-scaling workload                    |
| One-element or environment smoke                      | 1 CPU, 8-16 GB                                                            | Keep serial                                                                       |
| UEL/UMAT scientific reference solve                   | 1 CPU, memory from measured predecessor                                   | Serial reference is mandatory for a new formulation/deck family                   |
| Threaded qualification solve                          | 4, 8, then 16 CPUs; one MPI rank                                          | Proceed only when the previous level is technically and scientifically equivalent |
| Validated production solve                            | Highest validated useful thread count, normally no more than 16 initially | Use the measured fastest scientifically equivalent configuration                  |

Memory and wall-time selection:

- Do not use `90 GB` or `24:00:00` as inherited defaults. Those values belonged to another project.
- Set memory from the largest measured peak of the nearest comparable run, normally with about 50-100% operational headroom and a documented minimum of 8-16 GB.
- Set wall time from measured serial/threaded runtime with sufficient queue headroom; do not request the queue maximum without evidence.
- Current Molnar H0 used far below its 16 GB request, so future memory requests for comparable 2D cases should be evidence-based rather than automatically increased.
- Keep all heavy Abaqus output and temporary files under `/scratch/pr21vyci`.

Threaded qualification evidence:

- identical input-deck, Fortran-source, configuration, and mesh hashes;
- Abaqus technical completion and readable ODB;
- RF2-U2 comparison on a common displacement grid;
- peak force and peak-displacement differences;
- SDV15/SDV16 bounds, crack path, and matched-state contours;
- increment/iteration history and warnings;
- elapsed time, CPU time, parallel efficiency, and peak memory;
- explicit check for COMMON-block races, call-order dependence, label/IP mapping errors, and nondeterministic state updates.

Do not promote a threaded configuration merely because it is faster. It must first be scientifically equivalent under predeclared provisional tolerances. During qualification, run one solver case at a time. Concurrent production jobs require a separate campaign authorization, license check, storage check, and scheduler-capacity check; there is no inherited fixed “two simultaneous jobs” rule for this thesis.

Project-specific threaded PBS pattern, after validation and explicit submission approval:

```bash
#PBS -q entry_imfdfkmq
#PBS -l select=1:ncpus=<validated_threads>:mpiprocs=1:ompthreads=<validated_threads>:mem=<measured_requirement>
#PBS -l walltime=<measured_requirement>
#PBS -j oe
#PBS -m abe

module --force purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

export OMP_NUM_THREADS=<validated_threads>
export TMPDIR="/scratch/pr21vyci/<run_id>/tmp"
mkdir -p "$TMPDIR"

abaqus job=<job_name> input=<deck.inp> user=<source.for> \
  cpus=<validated_threads> mp_mode=threads interactive
```

Node-selection rules:

- Do not hard-code a hostname from this snapshot; let PBS select a compatible vnode.
- Treat `free`, `offline`, `down`, and `<various>` states as point-in-time scheduler information only.
- Request one node for Abaqus UEL/UMAT work unless a separately validated distributed-memory design requires more.
- The Molnar implementation uses COMMON/shared-memory data transfer. The serial result remains the scientific reference until a threaded repeatability gate passes.
- Future parallel qualification must use one MPI rank with shared-memory threads: `mpiprocs=1`, `ompthreads=<n>`, and Abaqus `mp_mode=threads`. Test the same immutable deck/source at `1`, `4`, `8`, and `16` threads.
- Do not assume MPI processes share COMMON-block data. Distributed-memory or multi-node execution is prohibited until the source is shown process-safe and a separate MPI validation gate is approved.
- A visible 40-core node is not a default 40-core entitlement. First validate up to 16 threads, matching the Kiefer/AMS node class. Requests for 32 or 40 cores require measured 16-thread scaling, a compatible route, and explicit user authorization.

Available software relevant to the thesis:

- Abaqus modules:
  - `abaqus/2021-incomplete` — do not use for thesis runs.
  - `abaqus/2021`
  - `abaqus/2022`
  - `abaqus/2023` — reported as the default Abaqus module in the snapshot.
- Compiler/toolchain modules:
  - `intel/2024.2.0`
  - `gcc/11.4.0` — reported default GCC
  - `llvm/18.1.8`
- Python:
  - `python/gcc/11.4.0/3.11.7`
- Other available tools relevant to preprocessing/post-processing include ParaView, Gmsh, FEniCS/DOLFINx, MATLAB, PETSc, and OpenMPI.

Version boundary:

- The verified local Windows baseline uses Abaqus 2024.
- The HPC snapshot advertises Abaqus 2021, 2022, and 2023, but not Abaqus 2024.
- Therefore an HPC run is a controlled software-version change, not a transparent migration.
- Select one exact Abaqus module and one compiler environment, record both in the run manifest, and repeat the compile/link/solver and scientific regression gates before accepting HPC results.
- Do not claim equivalence between local Abaqus 2024 and an HPC Abaqus 2021/2022/2023 result without quantitative comparison.

Candidate HPC smoke-gate procedure:

1. Log in and capture:
   ```bash
   id
   groups
   qstat -Qf
   module avail abaqus
   module avail intel
   ```
2. Use explicit modules in the PBS script rather than relying on implicit defaults or `.bashrc`:
   ```bash
   module purge
   module load intel/2024.2.0
   module load abaqus/2023
   ```

   This is a candidate stack only; adjust after `module show` and a compile/link test.
3. Submit a serial, single-node, short-wall-time smoke job through `testq` or the approved route queue. After the serial scientific regression passes, use a separately authorized `1/4/8/16`-thread qualification series before any threaded production claim.
4. Preserve module output, environment, terminal log, `.dat`, `.msg`, `.sta`, and ODB-readability evidence.
5. Classify separately:
   - environment/compiler/linker result;
   - technical solver result;
   - scientific regression result.
6. Only after the unchanged one-element result matches the local source-defined checks should the unchanged single-notch benchmark be considered for HPC reproduction.
7. Production jobs still require explicit user approval.

Conservative PBS templates:

General/Kiefer serial smoke test:

```bash
#!/bin/bash
#PBS -N abaqus_uel_smoke
#PBS -q testq
#PBS -l select=1:ncpus=1:mem=8gb
#PBS -l walltime=00:30:00
#PBS -j oe
#PBS -m abe

set -euo pipefail
cd "$PBS_O_WORKDIR"

module purge
module load intel/2024.2.0
module load abaqus/2023

mkdir -p "/scratch/pr21vyci/$PBS_JOBID"
workdir="/scratch/pr21vyci/$PBS_JOBID"
cp OneElement.inp OneElement.for "$workdir/"
cd "$workdir"

abaqus job=OneElement input=OneElement.inp user=OneElement.for cpus=1 interactive
```

Kiefer/AMS routed threaded production candidate, to be used only after serial/threaded equivalence, measured scaling, and explicit approval:

```bash
#PBS -q entry_imfdfkmq
#PBS -l select=1:ncpus=<validated_threads>:mpiprocs=1:ompthreads=<validated_threads>:mem=<measured_requirement>
#PBS -l walltime=<measured_walltime_not_exceeding_queue_limit>
#PBS -m abe
```

The placeholders must be replaced from current-project measurements; they are not defaults. Do not reuse `16 CPUs`, `90 GB`, `24 hours`, or a two-job concurrency rule merely because they appeared in another project's resource note. The private email recipient must be supplied with `qsub -M` and verified after submission.

HPC monitoring and evidence commands:

```bash
qstat -u pr21vyci
qstat -f <job_id>
tracejob <job_id>
pbsnodes -av
module list
```

Record the exact timestamp whenever queue or node state is reported.

## Scientific source hierarchy

Use sources in this order when they disagree:

1. The signed thesis proposal and explicit supervisor instructions.
2. Original supplied source code and its associated paper/tutorial.
3. The original papers listed above.
4. Abaqus documentation for the installed release.
5. The rapid study guide as a synthesis and checklist, not as a substitute for the papers.
6. Secondary literature only when explicitly added to the project bibliography.

Never silently combine equations, phase-field conventions, degradation functions, energy splits, element interpolation, state-variable layouts, or staggered/monolithic algorithms from different sources.

## Non-negotiable scientific boundaries

- The phase-field convention must be recorded for every implementation. In the Molnar convention, `d=0` is intact and `d=1` is fully broken. Do not reverse it in code, plots, or transfer logic.
- `MISESERI` is an Abaqus stress-discretization error indicator based on recovered von Mises stress. It is **not** a mathematical phase-field error estimator.
- The Pandey-Kumar workflow is primarily a coarse pre-analysis followed by targeted mesh refinement and a final phase-field run. Do not describe it as fully online crack-following adaptivity unless the implementation actually remeshes during fracture evolution and transfers all required state.
- A fine mesh should initially target a defensible `h/l` ratio. `h/l <= 0.5` is a starting point from the supplied literature, not a universal convergence proof.
- Phase-field results may be sensitive to mesh size, length scale, load increment, energy split, and solver coupling. Change and study these separately.
- Irreversibility must be verified. A damaged point must not heal during unloading unless the selected formulation explicitly permits it.
- UEL/UMAT/overlay-element labels and integration-point indexing are part of the scientific implementation, not bookkeeping details.
- COMMON-block or other shared-memory transfer is considered fragile until serial/parallel repeatability and element-number mapping are tested.
- Do not claim validation because a job completed. Validation requires comparison against predeclared quantitative and qualitative gates.
- Do not claim computational savings without reporting model size, active degrees of freedom where available, CPU/wall time, memory, increments/iterations, hardware, and solver settings.
- Do not compare crack contours at unmatched load/displacement states.

## Role and privileges

The agent may, when instructed:

- Read project files and the supplied papers.
- Create and edit source code, Abaqus input files, Python scripts, Fortran UEL/UMAT code, documentation, plotting scripts, and tests.
- Run local terminal commands, formatters, parsers, unit tests, small preprocessing jobs, and post-processing scripts.
- Record touched files in the project_coordination/sessions/ report; optional handoff mirror only if authorized.

The agent must not without explicit user approval:

- Submit Abaqus or HPC production jobs.
- Delete raw solver results, source code, reference decks, or experimental data.
- Overwrite a known-good baseline.
- Change the governing formulation while presenting the result as a numerical-only change.
- Queue large parameter sweeps.
- Commit, push, rewrite Git history, or remove branches.

## General behavior

- Before editing, state the planned files and the scientific purpose of the change.
- Prefer small, reversible changes and new versioned files over destructive overwrites.
- Preserve the original reference implementation in a read-only or clearly named `baseline_original/` area.
- For every numerical change, identify the expected effect and the test that can falsify it.
- Log assumptions explicitly. Never hide missing information behind a plausible default.
- Use exact paths, job names, parameter values, timestamps, and software versions in reports.
- When a run fails, preserve the failure evidence and classify it as environment, preprocessing, compilation, solver convergence, post-processing, or scientific mismatch.
- Keep raw data separate from derived plots and tables.
- Prefer configuration-driven scripts over hard-coded benchmark values.
- Make scripts rerunnable and idempotent where practical.

## Recommended workspace structure

```text
.
|-- .agent.md
|-- README.md
|-- THESIS_PLAN.md
|-- WORKSPACE_STRUCTURE.md
|-- references/
|   |-- papers/
|   `-- notes/
|-- src/
|   |-- uel/
|   |-- umat/
|   |-- abaquser/
|   `-- shared/
|-- models/
|   |-- baseline_original/
|   |-- one_element/
|   |-- mode_I/
|   |-- mode_II/
|   |-- hole_plate/
|   |-- l_panel/
|   `-- multi_hole/
|-- scripts/
|   |-- preprocessing/
|   |-- remeshing/
|   |-- postprocessing/
|   |-- validation/
|   `-- sync_agent_handoff.py
|-- configs/
|-- tests/
|   |-- unit/
|   |-- deck_checks/
|   `-- regression/
|-- runs/
|   |-- local/
|   `-- hpc/
|-- results/
|   |-- raw_index/
|   |-- processed/
|   |-- figures/
|   `-- tables/
|-- docs/
|   |-- experiment_records/
|   |-- decisions/
|   |-- methods/
|   `-- handoffs/
`-- agent_handoff/
```

Do not reorganize an existing workspace merely to match this tree. Map existing folders to these roles and document the mapping.

## Thesis execution stages and gates

### Stage A - Freeze and verify the original baseline

Required work:

- Compile and run the original Molnar example unchanged.
- Record environment and solver metadata.
- Reproduce the one-element check.
- Reproduce at least one single-edge-notched benchmark.
- Implement automated extraction of reaction force/displacement, phase field, selected SDVs, energies, element count, timing, and solver status.

Gate A1 - environment:

- Reference source compiles without undocumented source edits.
- Job starts with the intended user subroutine.
- Compiler and linker commands are archived.

Gate A2 - one-element verification:

- Status: passed locally for the unchanged Molnar one-element run using provisional numerical tolerances.
- Elastic response, degradation behavior, phase-field evolution, and history/irreversibility behavior agree with the source-defined analytical relations.
- Residual/tangent sign and DOF ordering are documented in the source notes and validator report.

Gate A3 - benchmark reproduction:

- Force-displacement curve and crack contour are compared at matched displacement states.
- Differences are quantified, not described only visually.
- Any mismatch is classified before proceeding.

Do not modify remeshing logic before Gate A3 is passed or explicitly waived by the user/supervisor.

### Stage B - Build the uniform fine-mesh reference

Required work:

- Choose a benchmark and create a uniformly fine reference mesh.
- Study mesh size, length scale, and load increment independently.
- Establish the reference curve, crack path, fracture energy, and runtime/resource baseline.
- Define the crack-identification threshold and curve-interpolation method.

Gate B1:

- A convergence trend is demonstrated for the selected outputs.
- The chosen reference mesh is justified, not merely the finest affordable case.
- Acceptance metrics are written before adaptive/refined results are evaluated.

### Stage C - Reproduce the Pandey-Kumar pre-refinement pipeline

Required workflow:

1. Generate a coarse model from the same geometry/material/loading source as the final model.
2. Create the layered UEL/UMAT/facsimile arrangement required to expose stress to Abaqus.
3. Ensure `umatelem` and `All_elem` mappings are valid and have matching connectivity where the method requires it.
4. Request at minimum `MISESERI`, `MISESAVG`, `S`, `EVOL`, `U`, `RF`, and required `SDV` outputs.
5. Create and log the remeshing rule, including `errorTarget`, `refinementFactor`, `minElementSize`, `maxElementSize`, coarsening policy, output frequency, and remeshing pass count.
6. Run the coarse pre-analysis.
7. Apply Abaqus native adaptive remeshing using the resulting ODB.
8. Export/regenerate the refined input deck.
9. Rebuild the UEL/UMAT layers on the refined connectivity.
10. Validate sets, sections, properties, element types, node/element labels, boundary conditions, amplitudes, output requests, and UEL DOF ordering.
11. Run an elastic dry test before the full fracture analysis.
12. Run the refined phase-field model and compare with the uniform reference.

Gate C1 - refined deck integrity:

- Automated deck checks pass.
- Refined mesh satisfies the selected local `h/l` requirement.
- No required set or property is lost.

Gate C2 - scientific comparison:

- Peak-force error, curve error, fracture-energy error, crack-path difference, and computational cost are reported.
- The MISESERI-marked zone is shown separately from the final phase-field crack.
- Results are not accepted solely because the crack looks plausible.

### Stage D - State transfer and IMFD/ABAQUSER integration

State-transfer inventory:

- Nodal phase field.
- History field enforcing irreversibility.
- Integration-point state variables.
- Degradation-related variables.
- Stress/strain fields needed for restart or visualization.
- Any coupling or bookkeeping arrays used by UEL, UMAT, or ABAQUSER.

Required tests:

- Transfer a known analytical spatial field between two meshes and measure L2 and maximum error.
- Check physical bounds after mapping.
- Check no-healing/monotonic-history conditions.
- Compare total energies immediately before and after transfer.
- Check element/integration-point ordering.
- Repeat serially and, if parallel execution is intended, compare parallel results.

ABAQUSER/IMFD work:

- Document variable names, dimensions, ordering, units, and intact/broken convention.
- Keep solver fields separate from visualization-only fields.
- Verify 2D/3D/axisymmetric assumptions before reusing generalized routines.
- Produce a minimal visualization test before integrating the complete fracture model.

Gate D1:

- State transfer is demonstrated on a controlled field before a fracture case.
- ABAQUSER output matches independent extraction for selected points/elements.
- Any unsupported state variable is explicitly listed.

### Stage E - Sensitivity, efficiency, and thesis recommendations

Minimum sensitivity axes:

- `h/l`.
- Length scale `l` with `h/l` controlled.
- Load increment strategy.
- Coarse pre-analysis mesh size.
- `errorTarget`.
- `refinementFactor`.
- Minimum and maximum element sizes.
- One versus multiple remeshing passes.
- Serial versus parallel execution if shared data are used.

Minimum outputs per case:

- Force-displacement curve.
- Phase-field contours at matched states.
- Crack path using a declared threshold.
- Peak force and initiation displacement.
- Fracture/dissipated energy as defined by the implementation.
- Element/node count and active DOFs if available.
- Wall time, CPU time, peak memory, increments, and iterations.
- Mesh map and local `h/l` distribution.
- Exact configuration and source-code revision.

Recommended metrics:

```text
e_peak  = abs(Fmax_candidate - Fmax_reference) / abs(Fmax_reference) * 100%
e_curve = ||F_candidate(U) - F_reference(U)||_2 / ||F_reference(U)||_2 * 100%
saving  = (cost_reference - cost_candidate) / cost_reference * 100%
```

Crack-path comparison must state:

- phase-field threshold;
- geometry scaling;
- load/displacement state;
- distance measure, such as sampled centerline distance or Hausdorff distance.

## Provisional validation policy

Until the supervisor approves final tolerances, use the following only as internal working gates:

- Primary scalar outputs: target <= 5% relative error.
- Force-displacement curve: target <= 5% normalized L2 error.
- Crack path: must remain inside a benchmark-specific geometric tolerance defined before viewing the candidate result.
- No unexplained discontinuity in energy or history variables after remeshing/transfer.

Label these as `provisional_working_gate`, not as a thesis-standard acceptance criterion.

Validation classifications:

- `not_run`
- `technical_fail`
- `technical_pass_scientific_unchecked`
- `scientific_fail`
- `provisional_pass`
- `validated_against_declared_gate`
- `feasibility_only`

Never promote `feasibility_only` to validation.

## Abaqus UEL/UMAT implementation rules

- Document UEL type, nodal DOFs, element dimension, interpolation order, integration rule, property-array layout, and state-variable layout.
- Keep a machine-readable or tabular map of every `PROPS`, `JPROPS`, and `SVARS/STATEV` index.
- Add bounds checks and clear diagnostic messages where the Abaqus interface permits them.
- Avoid hidden dependence on element call order.
- Treat overlay/facsimile element numbering as an explicit mapping with validation checks.
- Verify `AMATRX` and `RHS` conventions with the smallest possible test.
- Where practical, compare the analytical tangent with a finite-difference directional derivative.
- Preserve double precision consistently across source files and compiler flags.
- Do not alter fixed/free-form Fortran formatting accidentally.
- Keep physics calculations separate from Abaqus interface plumbing where feasible.
- Any stabilization, residual stiffness, clipping, or numerical tolerance must be named, configurable, and reported.
- For staggered schemes, record whether there is one pass per increment or an inner coupling iteration and its stopping criterion.
- For monolithic schemes, document symmetry/unsymmetry and consistent tangent assumptions.

## Remeshing-specific rules

- Log every remeshing-rule argument in a run manifest.
- Disable coarsening for the first irreversible-fracture baseline unless there is a specific, verified reason to allow it.
- Keep the coarse pre-analysis loading and boundary conditions consistent with the final fracture problem.
- Do not treat a coarse pre-analysis as physically converged unless independently shown.
- Save images/data for the coarse stress field, MISESERI field, refined mesh, and final phase-field crack as separate artifacts.
- After remeshing, run automated comparisons of model keywords and entity counts.
- Verify that the intended local minimum size was actually reached.
- Check mesh-quality and size-transition metrics, not only element count.
- Distinguish mesh regeneration from physical-state transfer in code and documentation.

## Python scripting rules

- Detect and document the Python version embedded in the installed Abaqus release.
- Avoid language/library features unsupported by that interpreter.
- Use a CLI or configuration file for benchmark parameters; do not bury them inside CAE commands.
- Provide `--dry-run` for scripts that rewrite input decks, remesh models, submit jobs, or delete files.
- Validate required files, model names, steps, instances, sets, and output variables before running expensive work.
- Make generated filenames deterministic and include a run identifier.
- Write a manifest containing input paths, parameters, timestamp, software version, and output paths.
- Fail loudly on duplicate element labels, missing sets, inconsistent connectivity, or unknown element types.
- Keep ODB extraction scripts read-only.
- Use interpolation onto a common displacement grid before computing curve error.
- Unit-test pure parsing/transformation functions outside Abaqus where possible.

## Fortran source rules

- Preserve the compiler-compatible source form and line-length rules.
- Use explicit kinds/precision consistently.
- Centralize constants and array-index definitions.
- Comment every shared-data interface and its ownership/lifetime.
- Avoid implicit assumptions about thread/process memory.
- Add a serial reference path before parallel execution.
- Never rename or reorder state variables without updating the mapping documentation, post-processing code, and regression tests.

## Experiment and run management

Each run directory should contain or reference:

- `run_manifest.json` or equivalent configuration.
- Input deck and user-subroutine revision/hash.
- Software/compiler/hardware metadata.
- Submission command and solver command.
- Abaqus status and relevant log excerpts.
- Extracted raw curves/fields.
- Validation metrics.
- `RUN_SUMMARY.md` with classification and next action.

Naming convention example:

```text
<benchmark>__<method>__hOverL-<value>__errTarget-<value>__<YYYYMMDD-HHMM>
```

Do not overwrite a completed run directory. Create a new run identifier.

## Job submission and resource reporting

Before any Abaqus/HPC submission:

- Obtain explicit user approval unless a standing instruction exists in the repository.
- Identify the work class: CAE-only, serial scientific reference, threaded qualification, or validated threaded production.
- Never infer a CPU count from node capacity alone. For UEL/UMAT jobs, use `cpus=1` unless a project-specific threaded qualification has passed for the same formulation/deck family.
- For a validated threaded job, use one MPI rank and the recorded OpenMP thread count; record `ncpus`, `mpiprocs`, `ompthreads`, `OMP_NUM_THREADS`, and Abaqus `mp_mode` in the manifest.
- Choose memory and wall time from measured current-project evidence, not from previous-project defaults.
- Read the current HPC handoff/configuration file if one exists.
- Confirm license availability, queue, CPUs, MPI/OpenMP layout, memory, wall time, scratch path, and stage-out policy.
- Confirm the job uses the intended input deck and subroutine revision.
- Confirm the tracked PBS script has `#PBS -m abe`.
- Pass the private recipient at submission time with `qsub -M "pr21vyci@mailserver.tu-freiberg.de" -m abe`.
- Verify the recipient address before the first submission with `scripts/hpc/validate_pbs_email_notifications.py`; do not assume the cluster account's default email address.
- Immediately after submission, run `qstat -f "$JOB_ID"` and verify `Mail_Users = pr21vyci@mailserver.tu-freiberg.de` and `Mail_Points = abe`.

Future submission pattern:

```bash
REVISION=$(git rev-parse HEAD)

JOB_ID=$(qsub \
  -M "pr21vyci@mailserver.tu-freiberg.de" \
  -m abe \
  -v PROJECT_REVISION="${REVISION}" \
  scripts/hpc/<job-script>.pbs)

echo "${JOB_ID}"
qstat -f "${JOB_ID}" | grep -E 'Mail_Users|Mail_Points|job_state|queue'
```

For a running job, report:

- job ID, state, queue, host/vnode;
- requested CPUs, MPI ranks/threads, memory, wall time;
- used wall time, CPU time/utilization, memory/VMEM when available;
- current increment/step and latest meaningful log lines;
- exact timestamp.

For a finished job, report:

- exit status and whether Abaqus completed normally;
- final resources used;
- start/finish timestamps;
- scientific classification, which is separate from technical completion.

Never delete large results merely to save storage without user approval and a verified retention plan.

## Git and large-file hygiene

- Keep raw `.odb`, restart, scratch, and other large generated Abaqus files out of Git unless explicitly required.
- Prefer targeted Git commands such as `git status --short --untracked-files=no`, `git diff -- <paths>`, and explicit `git add <paths>`.
- Avoid broad hashing, full-tree scans, `git gc`, or recursive diffs in a workspace containing large solver outputs unless the user approves.
- Do not commit the flat `agent_handoff/` mirror by default.
- Preserve reference source archives and record checksums.

## File tracking and handoff mirror - legacy optional behavior

The active multi-agent control plane is project_coordination/, not agent_handoff/.

1. Record the workspace-relative paths of all touched files in the session report under
   project_coordination/sessions/.
2. Do **not** run scripts/sync_agent_handoff.py by default. That utility can clear and
   overwrite the flat agent_handoff/ tree and must not run while unrelated dirty handoff
   changes exist unless explicitly authorized.
3. If an authorized handoff mirror is requested, use selective paths only and never treat
   the mirror as version history or mandatory coordination.
4. Do not mirror large solver outputs or binary files unless the user explicitly asks.

Default excluded extensions for any optional mirror include:

```text
.odb .sim .stt .res .mdl .prt .dat .msg .lck .023 .cax .abq .pac .sel
```

## Documentation rules

Maintain:

- `docs/decisions/` for formulation and workflow decisions.
- `docs/experiment_records/` for one record per meaningful run or comparison.
- `docs/methods/` for stable procedures.
- `docs/handoffs/` for current-status summaries.
- `docs/project/PROJECT_PHASE_CHECKLIST.md` as the single authoritative living task and phase checklist.

Checklist rules:

- Update `docs/project/PROJECT_PHASE_CHECKLIST.md` after every substantial operation.
- Every completed item must link to evidence or identify its commit/run.
- Failed attempts remain recorded.
- Technical completion and scientific validation must remain separate.
- A phase may be marked complete only after its stated gate passes.
- Blocked downstream tasks must remain visibly blocked.
- When a phase closes, record closure date, final commit, passed gate, frozen reports, and remaining limitations.
- Do not create duplicate phase checklists.
- Generated PDFs are not checklist evidence unless their source and generation command are recorded.

Every decision record should state:

- question;
- alternatives;
- evidence;
- decision;
- consequences;
- date and owner.

Every figure intended for the thesis should have:

- source run IDs;
- variable and threshold definitions;
- units;
- matched load/displacement state;
- generation script path;
- no manual edits that change scientific content.

## Common failure triage

Crack path changes after remeshing:

- Check state/history transfer, mesh bias, sets, element orientation, and phase-field convention.

MISESERI marks irrelevant regions:

- Check coarse-mesh adequacy, load stage, boundary conditions, stress exposure through UMAT/facsimile elements, and output frequency.

Peak load is too high:

- Reduce `h/l` and load increment separately; verify energy split and material units.

Healing appears:

- Check history max-update, state storage, transfer interpolation, and initialization.

No phase-field contour in ODB/ABAQUSER:

- Check overlay/visualization layer, SDV mapping, element labels, and output requests.

Parallel and serial results differ:

- Check COMMON/shared data, call-order assumptions, race conditions, and element indexing.

Refined input deck fails:

- Diff keyword blocks; check UEL definitions, sections, property blocks, connectivity, sets, amplitudes, and DOF ordering.

Job finishes but result is wrong:

- Classify as `technical_pass_scientific_unchecked` or `scientific_fail`, never `validated`.

## Agent session closing checklist

At the end of each substantial session:

1. Summarize files changed and commands run.
2. Report tests and their outcomes.
3. State the current scientific classification.
4. List unresolved issues and the next smallest falsifiable task.
5. Update project_coordination/ ledgers and session report; do not duplicate dynamic state in this file.
6. Do not run the legacy agent_handoff synchronization utility unless the
current task explicitly authorizes it.
7. Do not edit the user-notes block below.

## User notes - do not edit below this line

- Add supervisor-specific constraints, deadlines, institutional templates, and personal preferences here.

User Notes (don't touch this section):
ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg "qstat -u pr21vyci"

VPN service start (first run as administrator)

powershell -Command "Start-Process PowerShell -Verb RunAs"

Start-Service -Name 'eduWGManager$eduVPN'
Start-Service -Name 'OpenVPNServiceInteractive$eduVPN'

ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg 'cd ~/software/src && rm -rf install-tl-* && wget -O install-tl-unx.tar.gz https://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz && tar -xzf install-tl-unx.tar.gz && cd "$(find . -maxdepth 1 -type d -name '"'"'install-tl-*'"'"' | sort | tail -n 1)" && perl ./install-tl --no-interaction --scheme=small --no-doc-install --no-src-install --texdir=$HOME/texlive/2026 && echo '"'"'export PATH=$HOME/texlive/2026/bin/x86_64-linux:$PATH'"'"' >> ~/.bashrc && source ~/.bashrc && which pdflatex && pdflatex --version | head -n 2'

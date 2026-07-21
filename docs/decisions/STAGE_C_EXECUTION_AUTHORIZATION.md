# Stage C Execution Authorization

Status: `authorized_staged_execution`  
Recorded: 2026-07-21  
Source: user execution authorization (routine engineering + staged HPC)

## Decision policy

**Proceed without supervisor approval for:**

- preprocessing and automation;
- implementation fixes;
- initial numerical parameters within the accepted workflow;
- smoke and integrity tests;
- the planned MISESERI campaign;
- normal HPC resource choices;
- postprocessing and documentation.

**Ask the supervisor only for:**

- changing the phase-field formulation or material model;
- replacing H1 as the thesis production reference;
- introducing a new validation benchmark or major study axis;
- accepting a scientifically unresolved result;
- changing the thesis scope or final conclusions.

## Fixed technical decisions

```text
Testing/development mesh: H0
Final/report comparison mesh: H1
Fine RF–U validation reference: H2-PUB

errorTarget       = 0.05
refinementFactor  = 2.0
minElementSize    = 0.0025 mm
maxElementSize    = 0.025 mm
remeshing passes  = 1
coarsening        = disabled

pre-analysis: elastic pre-crack
U_pre = 0.8 * U_peak_H1 = 0.8 * 0.0058 = 0.00464 mm
```

## Authorization boundary

```text
Authorized:
- implement Job 3
- finalize Jobs 1–5 infrastructure
- submit Jobs 1–5 once each through staged gates
- local preprocessing, validation and postprocessing
- commit and push resulting evidence

Not authorized:
- automatic retries
- repeated parameter tuning
- additional remeshing passes
- a second mesh family
- length-scale or load-increment sweeps
- formulation/material changes
- multicore qualification
- GPU execution
- state transfer or online remeshing
```

## Stage gates

```text
Job 1 pass
  → Job 2 pass and field suitable
    → Job 3 remesh/export pass
      → layered refined deck validation pass
        → Job 4 integrity pass
          → Job 5 final refined simulation
```

## Queue-selection policy (mandatory)

Do **not** hard-code `normal_imfdfkmq` for small jobs. No queue guarantees an
immediate start; select the **fastest eligible** queue for the requested
resources from live `qstat -q` / `qstat -Qf` status.

| Job | Resources | Preferred submit queue |
|---|---:|---|
| Job 1 — smoke | 1 CPU, 8 GB, 1 h | `entry_imfdfkmq` |
| Job 2 — H0 pre-analysis | 1 CPU, 16 GB, 2 h | `entry_imfdfkmq` when limits allow |
| Job 3 — CAE extract/remesh | 1 CPU, 16 GB, 1 h | `entry_imfdfkmq` |
| Job 4 — integrity | 1 CPU, 16 GB, 2 h | `entry_imfdfkmq` when eligible |
| Job 5 — full fracture | 1 CPU, 32 GB, 6 h | `normal_imfdfkmq`, unless another eligible queue is demonstrably faster |

Notes:

- `entry_imfdfkmq` is a **route** queue (enabled/started). It may land on
  `short_imfdfkmq` or `normal_imfdfkmq` after routing; that is expected.
- Before every submission, verify preferred queue `enabled=True`, `started=True`,
  and that walltime/memory fit `resources_max`.
- Record queue wait time (`stime - qtime`) for each job to compare routes.

Pre-submit checks:

```powershell
ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg `
  "qstat -Qf entry_imfdfkmq | egrep -i 'enabled|started|resources_max|resources_min|resources_default|max_run|state_count'"
ssh -F $env:USERPROFILE\.ssh\codex_config tu_freiberg "qstat -q"
```

Submission mail pattern:

```bash
qsub -q entry_imfdfkmq \
  -M pr21vyci@mailserver.tu-freiberg.de \
  -m abe \
  -v PROJECT_REVISION=...,PRESTAGED_ROOT=... \
  scripts/hpc/<job>.pbs
```

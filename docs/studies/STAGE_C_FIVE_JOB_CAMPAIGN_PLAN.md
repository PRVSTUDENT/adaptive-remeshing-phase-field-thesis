# Stage C — Five-Job MISESERI Campaign (Plan Only)

Status: `prepared_plan_only`  
Recorded: 2026-07-21  
Submission authorization: **none** — do not `qsub`

This document freezes the proposed first HPC campaign after preprocessing automation is ready. It is not a submission record.

---

## Job 1 — MISESERI output smoke test

| Field | Proposal |
|---|---|
| Job name | `molnar_h0_miseseri_smoke` |
| Model | H0-based reduced/test configuration |
| Purpose | Verify stress exposure and `MISESERI` availability |
| CPUs | 1 |
| Memory | 8–16 GB |
| Walltime | 01:00:00 |
| Solver | Abaqus/Standard |
| Scientific result | Not used as final evidence |

Acceptance:

```text
solver completes
MISESERI exists in ODB
MISESAVG and S exist
facsimile mapping is correct
no missing element/set/output errors
```

---

## Job 2 — H0 coarse pre-analysis

| Field | Proposal |
|---|---|
| Job name | `molnar_h0_miseseri_preanalysis` |
| Model | Full H0 testing model |
| Purpose | Produce the stress-error field used for remeshing |
| CPUs | 1 |
| Memory | 16 GB |
| Walltime | 02:00:00 |
| Outputs | MISESERI, MISESAVG, S, EVOL, U, RF |

Acceptance:

- stable completion;
- physically reasonable stress field;
- MISESERI concentrated in defensible regions;
- no irrelevant boundary-driven refinement dominating the crack region;
- required ODB fields present.

This is **not** the final fracture result.

---

## Job 3 — CAE-only remeshing and refined-deck generation

| Field | Proposal |
|---|---|
| Job name | `molnar_h0_miseseri_remesh` |
| Solver runs | 0 (CAE remesh/export only) |
| Purpose | Apply remeshing rule and export refined mesh/deck |
| CPUs | 1 |
| Memory | 16 GB |
| Walltime | 01:00:00 |

Outputs:

```text
refined mesh
mesh-size map
MISESERI-marked region
remeshing-rule manifest
exported physical input deck
```

After this job, **local** scripts rebuild UEL/phase/visualization layers and run deck validators. No fracture conclusion.

---

## Job 4 — Refined-deck integrity test

| Field | Proposal |
|---|---|
| Job name | `molnar_h0_refined_integrity` |
| Model | Rebuilt layered refined model |
| Loading | Short elastic or reduced-load test |
| CPUs | 1 |
| Memory | 16 GB |
| Walltime | 02:00:00 |

Acceptance:

- compile/link pass;
- no duplicate or missing element labels;
- all sets and properties retained;
- UEL/UMAT mappings correct;
- RF and displacement outputs correct;
- no fracture conclusion drawn.

---

## Job 5 — Final refined phase-field simulation

| Field | Proposal |
|---|---|
| Job name | `molnar_miseseri_refined_final` |
| Target resolution | H1-equivalent local resolution |
| Reference | Existing uniform H1 simulation |
| CPUs | 1 initially |
| Memory | 32 GB |
| Walltime | 06:00:00 |

Compare against frozen uniform H1:

- peak force and peak displacement;
- pre-peak and full-curve NRMSE;
- post-peak response;
- element count, walltime, memory;
- local \(h/l_c\);
- MISESERI refinement zone.

Crack-path comparison: preliminary only; not the acceptance gate (Decision 2B).

---

## Campaign boundary

```text
max_jobs_this_campaign: 5
serial_only: true
multi_cpu: false
gpu: false
automatic_retry: false
submission: requires explicit new authorization
```

Do not mix multicore qualification into this campaign.

## Dependency chain (when authorized)

```text
Job1 smoke
  → Job2 pre-analysis
    → Job3 remesh (CAE)
      → local layer rebuild + validators
        → Job4 integrity
          → Job5 refined fracture
```

Prefer `afterok` dependencies only after each predecessor’s acceptance criteria are verified; do not auto-chain Job5 on Job4 until integrity evidence is reviewed.

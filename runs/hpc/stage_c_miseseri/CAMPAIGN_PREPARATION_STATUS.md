# Stage C five-job campaign

Status: `execution_authorized_job1_ready`  
Updated: 2026-07-21  
Submission: staged, once each

## Fixed decisions

```text
H0 test | H1 production | H2-PUB fine validation
elastic pre-crack U_pre = 0.00464 mm
errorTarget=0.05 refinementFactor=2.0 min h=0.0025 max h=0.025
passes=1 coarsening=disabled
```

## Job status

| Job | Purpose | Infrastructure | Execution |
|---|---|---|---|
| 1 | MISESERI smoke | ready | pending submit |
| 2 | H0 pre-analysis | ready | gated on Job 1 |
| 3 | CAE remesh export | ready (extract+remesh scripts) | gated on Job 2 |
| 4 | refined integrity | ready | gated on Job 3 + layer rebuild |
| 5 | refined fracture | ready | gated on Job 4 |

## Local validation snapshot

| Check | Result |
|---|---|
| Smoke deck static | pass |
| Preanalysis deck static (Upre=0.00464, MISESERI) | pass |
| PBS email directives | pass |
| Job 3 extract/remesh scripts | present |

## Authorization

`docs/decisions/STAGE_C_EXECUTION_AUTHORIZATION.md`

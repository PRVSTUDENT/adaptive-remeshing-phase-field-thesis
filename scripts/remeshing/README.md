# Remeshing Scripts

Store Abaqus Python remeshing automation here. Every script that can rewrite decks or run remeshing must support dry-run behavior where practical.

## Stage C MISESERI pre-refinement (preparation only)

Authority:

- `docs/decisions/MOLNAR_GATE_A3_SUPERVISOR_DECISION_1A_2B.md`
- `docs/studies/STAGE_C_MISESERI_PREPARATION_PLAN.md`
- `docs/studies/STAGE_C_FIVE_JOB_CAMPAIGN_PLAN.md`

Initial implementation rules (record before tuning):

```text
coarsening: disabled
remeshing passes: 1
target local final size: approximately H1, h = 0.0025 mm
comparison reference: existing uniform H1
solver mode: serial initially
development mesh for first trials: H0
```

Do **not** retune `errorTarget` after viewing the final crack result.

### Planned modules (not yet implemented)

| Module | Purpose |
|---|---|
| stress-exposure layer builder | Ensure MISESERI-capable UMAT/facsimile outputs on H0 |
| remesh rule applicator | CAE-only adaptive remesh export (Job 3) |
| refined layer rebuild | Rebuild UEL/UMAT layers after physical remesh |
| remesh manifest writer | Record errorTarget, factors, size bounds, pass count |

### Authorization

```text
Scripts may be developed now.
CAE remesh jobs and qsub: not authorized without explicit submission approval.
```

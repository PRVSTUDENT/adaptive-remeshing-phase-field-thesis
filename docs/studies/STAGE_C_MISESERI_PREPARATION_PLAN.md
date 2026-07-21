# Stage C — MISESERI Preparation Plan

Status: `stage_c_miseseri_preparation_authorized`  
Recorded: 2026-07-21  
Authority: supervisor decisions **1A** and **2B**  
Gate tag: `gate_a3_conditionally_accepted_rf_u`

```text
Preparation: AUTHORIZED
HPC submission: NOT AUTHORIZED without explicit new approval
```

## Objective

Implement and validate a Pandey–Kumar-style **MISESERI-driven pre-refinement** workflow on the Molnar single-notch model, using:

- **H0** for first implementation and debugging;
- remeshing toward approximately **H1** local resolution (\(h = 0.0025\) mm);
- **uniform H1** as the primary scientific comparison reference;
- **H2-PUB** only as an optional secondary fine RF–U check.

Claim boundary: **pre-refinement only**, not online evolving adaptivity with state transfer.

## Prerequisites (Phase 1 — complete when freeze docs exist)

- [x] Record decisions 1A and 2B
- [x] Freeze mesh roles and H0/H1/H2 results
- [x] Mark Stage C preparation authorized
- [ ] Fully automated H0/H1 preprocessing (Phase 2)
- [ ] Gate P1 determinism check
- [ ] Five-job campaign scripts prepared (not submitted)

## Phase 2 — Automated preprocessing

Single configuration controls geometry, notch, materials, \(l_c\), mesh role (H0/H1), sizes, loading, UEL properties, numbering, outputs, and MISESERI remeshing parameters.

Pipeline:

```text
configuration
  → geometry generation
  → physical mesh generation
  → UEL displacement layer
  → UEL phase-field layer
  → UMAT/facsimile visualization layer
  → sets, sections, loads, BCs
  → output requests
  → validated Abaqus input deck
```

Mandatory automated checks: duplicate nodes/elements; UEL/UMAT/facsimile correspondence; label offsets; required sets; UEL properties; DOF order; material/\(l_c\); corridor mesh size and \(h/l_c\); RP/RF outputs; `MISESERI`, `MISESAVG`, `S`, `EVOL`, `U`, `RF`, SDVs; deterministic regeneration.

### Gate P1

```text
same config → same geometry, mesh, labels, sets and input keywords
```

Generate the same H0 model twice; require byte-identical or semantically identical decks.

## Phase 3 — MISESERI pre-refinement (implementation sequence)

```text
H0 coarse/test model
  → stress-exposure UMAT/facsimile layer
  → coarse pre-analysis
  → MISESERI field
  → Abaqus adaptive remeshing
  → refined physical mesh
  → rebuild UEL/UMAT layers
  → elastic integrity test
  → phase-field fracture test
```

Initial rules (record before tuning):

```text
coarsening: disabled
remeshing passes: 1
target local final size: approximately H1, h = 0.0025 mm
comparison reference: existing uniform H1
solver mode: serial initially
```

Do **not** retune `errorTarget` after viewing the final crack result. Define initial value, record it, assess consequences.

Parameters requiring explicit approval before first remesh job:

- `errorTarget`
- `refinementFactor`
- `minElementSize`
- `maxElementSize`
- one remeshing pass
- coarsening disabled

Open technical choice for the short supervisor meeting: whether the MISESERI pre-analysis is elastic-only or uses partial fracture loading.

## Scientific comparison (Stage C)

Primary: **uniform H1** vs **MISESERI-refined targeting H1 local resolution**.

\[
e_{\mathrm{peak}}
=
\frac{|F_{\max}^{\mathrm{refined}}-F_{\max}^{H1}|}
{|F_{\max}^{H1}|}
\]

\[
e_{\mathrm{curve}}
=
\frac{\|F_{\mathrm{refined}}(U)-F_{H1}(U)\|_2}
{\|F_{H1}(U)\|_2}
\]

Also report: physical/layered element counts; reduction vs uniform H1; walltime; CPU time; memory; refinement distribution; min/median \(h/l_c\).

Crack-path comparison may be recorded as preliminary but is **not** the acceptance gate (Decision 2B).

## Parallel lower-priority tasks (do not block Stage C prep)

### V1 — Secondary literature matrix

Applicability matrix fields: reference, geometry, material, length scale, formulation, energy split, loading, mesh size, RF–U data, crack path, compatibility with current Molnar model.

### V2 — Analytical benchmark assessment

Defensible analytical checks only: initial stiffness; uncracked stress field; energy release before propagation; critical-load estimate; homogeneous one-element phase-field response. Full nonlinear post-peak analytical solution is not the target.

## Deferred crack-path reproducibility

Prepare postprocessor metrics now; execute study later:

- initiation point, centerline, SDV15 threshold, extension
- path deviation, Hausdorff/mean centerline distance
- matched displacement state

Later matrix: repeated same input; H0 vs H1; small mesh perturbations; selected parameter variations; MISESERI-refined vs uniform H1.

## Multicore qualification (separate, later)

After serial workflow is stable, qualify H1 only:

| Run | MPI ranks | OpenMP threads |
|---|---:|---:|
| Reference | 1 | 1 |
| P4 | 1 | 4 |
| P8 | 1 | 8 |
| P16 | 1 | 16 |

Accept parallel only when RF–U, SDVs, crack initiation, and increments match serial within declared tolerances.

## Immediate next actions

```text
Record supervisor decisions 1A and 2B          [done in decision docs]
→ freeze mesh roles                              [done]
→ build automated H0/H1 preprocessing pipeline
→ prepare five-job MISESERI campaign (no qsub)
→ request explicit submission authorization
```

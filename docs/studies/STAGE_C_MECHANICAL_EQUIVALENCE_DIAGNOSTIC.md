# Stage C — Mechanical equivalence diagnostic

Status: **open** (pipeline executable; scientific validation open)  
Failed iteration: C2F-v2 job `1376444.mmaster02`  
Production / report reference: **uniform H1** (unchanged)

## Executive status

```text
pipeline execution: pass
refined-mesh construction (element economy): pass
four-thread qualification: pass
refined-model scientific equivalence: fail
Stage C validation: open
H1 remains the production/report reference
```

Do **not** present C2F-v2 as a successful adaptive-remeshing scientific result.

Do **not** retune `relative_MISESERI_threshold` or enlarge the refined zone until the refined deck reproduces H1 elastic stiffness.

## Decisive observation

Initial stiffness mismatch (appears **before** meaningful fracture):

| Model | K (kN/mm) |
| --- | ---: |
| H1 | 134.3 |
| C2F-v2 | 230.5 |

Peak RF 1.430 vs 0.700, monotone RF, SDV15≈0.059 are treated as **downstream** of this model mismatch.

## Terminology

```text
relative_MISESERI_threshold = 0.05
MISESERI / max(MISESERI) > relative_MISESERI_threshold
```

Not an absolute Abaqus `errorTarget` claim without literature for that normalization.

## Hypotheses

### H1 — CPS4 double stiffness (priority check)

| Field | Content |
| --- | --- |
| Hypothesis | Auxiliary-continuum / full-E CPS4 accidentally retained, double-counting stiffness |
| Evidence for | High K and RF |
| Evidence against | C2F-v2 deck `*User Material` = `1e-11, 0.3` identical policy to H1; U2 UEL `E=210, k=1e-7` matches H1 |
| Test | Property parse audit |
| Result | **REJECTED** |
| Decision | Do not change residual UMAT policy |

### H2 — Missing notch split (confirmed)

| Field | Content |
| --- | --- |
| Hypothesis | Offline remesh never placed an exact `y=0` grid line, so MeshBuilder notch free-face doubling never fired → **continuous plate** |
| Evidence for | C2F-v2: `has_exact_y0=false`, nearest y≈−3.5e−4, **0** notch-line nodes; H1: exact y=0, 32 doubled x-stations; elevated K; no localization |
| Evidence against | — |
| Test | Geometry audit of part nodes |
| Result | **CONFIRMED** |
| Decision | Force-include `y=0` (and `x=0`) in remesh axis builder; rebuild C2C-v3 offline; run D1 elastic probe before any full C2F-v3 |

## Corrections applied (geometry only)

| File | Change |
| --- | --- |
| `scripts/remeshing/build_refined_mesh_from_miseseri.py` | `_force_include_coordinate` so y=0 exists exactly |
| `scripts/preprocessing/build_molnar_unified_deck.py` | Reconstruct notch face nsets from doubled y=0 nodes when present |

**Not changed:** E, ν, Gc, lc, geometry envelope, H1 reference, relative MISESERI threshold, refined-zone bounds, size limits, phase-field formulation.

## Release gate for full C2F-v3

```text
[x] deck audit complete
[x] no unintended full-E CPS4 layer (property match H1)
[x] BC keyword equivalence verified (structure)
[x] UEL properties match H1
[x] Fortran N_ELEM matches physical count (builder)
[ ] tiny elastic stiffness |K−K_H1|/K_H1 ≤ 1%
[ ] phase-field patch / SDV15 spatial meaning
[ ] static validators pass on corrected deck
```

One full fracture run only after D1 passes. Parallel: `cpus=4`, `mp_mode=threads`, no MPI.

## Artifact index

```text
runs/hpc/stage_c2/diagnostics/
  C2F_V2_FAILED_ITERATION_FREEZE.json
  C2F_V2_FAILED_ITERATION_REVIEW.md
  H1_VS_C2F_V2_DECK_AUDIT.json/.md
  H1_VS_C2F_V2_PROPERTY_DIFF.csv
  H1_VS_C2F_V2_KEYWORD_DIFF.txt
  H1_VS_C2F_V2_BC_AUDIT.json
  C2F_V2_LOAD_CARRYING_LAYER_AUDIT.json
  DIAGNOSTIC_STATUS.json
  v3_notchfix/...
```

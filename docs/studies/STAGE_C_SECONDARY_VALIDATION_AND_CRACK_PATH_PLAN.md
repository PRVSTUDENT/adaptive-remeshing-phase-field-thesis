# Stage C Parallel Tasks — Secondary Validation and Deferred Crack Path

Status: `parallel_lower_priority`  
Recorded: 2026-07-21  
Does not block Stage C preprocessing or five-job campaign preparation.

## Task V1 — Secondary literature search

Create an applicability matrix:

| Field | Description |
|---|---|
| reference | citation |
| geometry | single-notch / other |
| material | E, ν, Gc, etc. |
| length scale | \(l_c\) |
| phase-field formulation | AT1/AT2/other |
| energy split | spectral / volumetric-deviatoric / none |
| loading | tension / shear / mixed |
| mesh size | local \(h\), \(h/l_c\) |
| reported RF–U data | yes/no + digitizable |
| reported crack path | yes/no |
| compatibility with current Molnar model | high/medium/low + notes |

Priority order:

1. Same single-notch geometry and material  
2. Same \(l_c\) and degradation law  
3. Same staggered formulation  
4. Published force–displacement data  
5. Published crack path or contour data  

Working location (to be populated): `references/derived/secondary_validation/APPLICABILITY_MATRIX.md`

## Task V2 — Analytical benchmark assessment

Assess whether analytical comparison is defensible for:

| Quantity | Likely defensible? | Notes |
|---|---|---|
| Initial elastic stiffness | yes | one-element and plate stiffness checks |
| Uncracked stress field | partially | simple geometries only |
| Energy release rate before propagation | partially | LEFM-type estimates only |
| Critical-load estimate | partially | order-of-magnitude / asymptotic |
| Homogeneous one-element phase-field response | yes | already used in WP1 |
| Full nonlinear post-peak crack evolution | no | not an appropriate closed-form target |

## Deferred crack-path reproducibility plan

Prepare tools now; execute later after preprocessing automation.

Postprocessor should compute:

- crack initiation point  
- crack centerline  
- SDV15 threshold used  
- crack extension  
- path deviation from expected ligament  
- Hausdorff or mean centerline distance  
- matched displacement state  

Later study matrix:

```text
same input repeated
H0 versus H1
small mesh perturbations
selected material/input variations
MISESERI-refined versus uniform H1
```

Purpose: test whether the path is **reproducible**, not merely whether each contour looks plausible.  
Not an acceptance gate for Stage C preparation (Decision 2B).

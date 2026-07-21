# Stage C — Terminology and live status note

Recorded: 2026-07-21  
Commit series: through `2d85bdc` (C2E/F-v2 submission)

## Terminology correction (retain)

The implemented offline marking rule is a **relative field threshold**, not a claim of native Abaqus absolute `errorTarget` semantics unless a cited source uses the same normalization:

```text
relative_MISESERI_threshold = 0.05
```

Implemented formula:

```text
MISESERI / max(MISESERI) > relative_MISESERI_threshold
```

with `relative_MISESERI_threshold = 0.05`.

Frozen numeric value `0.05` is unchanged. Documentation and manifests should prefer the name **`relative_MISESERI_threshold`** when describing the v2 algorithm. Do not present this as an absolute Abaqus `errorTarget` without literature support for that normalized interpretation.

Legacy incorrect (v1 over-refined) rule:

```text
raw MISESERI > 0.05   # absolute; invalid for field max ~1390
```

## Interpretation of completed gates

| Gate | Meaning |
| --- | --- |
| C2D | Frozen H0 is reproducible with four OpenMP threads for this workflow |
| C2C-v2 | Physical mesh 10 088 vs H1 12 064 (~16.4% fewer); localized refine, coarse far field |
| C2E-v2 | Refined deck integrity (reduced load) technically passed |
| C2F-v2 | Decisive Stage C full refined fracture solve |

## Live status at note write

| Job | ID | State | Exit | Marker |
| --- | --- | --- | --- | --- |
| C2E-v2 | 1376443.mmaster02 | F | 0 | **C2E_V2.ok** |
| C2F-v2 | 1376444.mmaster02 | **R** (running) | — | pending |

Because `C2E_V2.ok` exists, C2F is expected to perform the **full scientific solve** (not `skipped_upstream_failure`).  
`afterany` only released the PBS job; the internal marker gates the solve.

## Submission freeze

Do **not** submit additional jobs while `1376444.mmaster02` is running.  
Preserve all PBS logs, scratch run directories, chain_state markers, and status JSON.

## Final classification (after C2F completes)

Use exactly one of:

```text
stage_c_refined_response_supported
stage_c_technically_valid_response_deviation
stage_c_refined_solver_failed
```

### Technical requirements for pass path

- PBS Exit_status = 0  
- Abaqus completed successfully  
- `C2F_V2.ok`  
- ODB readable; RF2/U2 and required SDVs present and finite  
- Physical/layered mappings valid  

### Scientific vs H1 (provisional)

| Metric | Criterion |
| --- | --- |
| Peak-force difference | ≤ 2% |
| Initial stiffness difference | ≤ 1% |
| Pre-peak RF–U NRMSE | ≤ 2% |
| Peak displacement | within one output interval |
| Full/post-peak | report separately |

### Performance caution

H1 reference was **serial**; C2F uses **four threads**. Element-count reduction is attributable to the mesh. Walltime may be reported, but speedup must **not** be attributed solely to remeshing.

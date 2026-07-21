# Stage C2 — Auxiliary continuum MISESERI chain

Status: `authorized_unattended_afterok_chain`  
Date: 2026-07-21

## Why

Job 2 on the layered UEL/UMAT facsimile produced:

```text
max(MISESERI) ~ 1e-13
```

because continuum stress is recovered from residual-stiffness CPS4 UMAT, not
load-bearing U2 UEL. That ODB must **not** drive remeshing.

## Replacement route

```text
C2A aux continuum H0 (real E, CPE4, MPI=4)
  → C2B scientific gate + offline remesh (1 CPU)
    → C2C rebuild UEL layered refined deck + validators
      → C2D H0 4-thread qualification vs serial H0
        → C2E refined integrity (threads)
          → C2F refined final fracture (threads)
```

## Parallel policy

| Model class | Parallel mode |
|---|---|
| Auxiliary continuum pre-analysis | MPI (`mp_mode=mpi`, 4 ranks) |
| UEL/UMAT jobs | **No MPI**; after C2D pass use `mp_mode=threads`, 4 OpenMP threads |

## Gate (C2B)

```text
max(von Mises) > 1 MPa
max(MISESERI) > 1e-6
top5 corridor fraction >= 0.25
top5 corridor fraction >= top5 outer-boundary fraction
```

## Frozen remesh params (unchanged)

```text
errorTarget=0.05
refinementFactor=2.0
minElementSize=0.0025 mm
maxElementSize=0.025 mm
passes=1
coarsening=disabled
```

## Boundary

```text
One chain submission only
No automatic retries
No parameter retuning in-chain
Inactive Job 2 ODB: forbidden for remeshing
```

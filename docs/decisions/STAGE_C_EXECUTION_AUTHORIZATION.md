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

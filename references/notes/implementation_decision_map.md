# Implementation Decision Map

| Decision | Default | Evidence Needed To Change |
|---|---|---|
| First reproduction target | Molnar one-element and Mode I benchmark | Supervisor requires another benchmark first |
| First remeshing milestone | Pandey-Kumar-style MISESERI pre-refinement | Installed Abaqus remeshing API cannot support it |
| Evolving remesh | Mandatory thesis branch after state-transfer proof | Supervisor explicitly removes it from scope |
| Tolerances | Provisional only until approved | Supervisor-approved numeric gates |
| Runtime | HPC after maintenance, local/static validation now | Local Abaqus availability and license confirmation |
| Coarsening | Disabled for first irreversible-fracture baseline | Specific verified reason to allow coarsening |
| Validation claim | Requires predeclared quantitative and qualitative gates | No exception |
| Git initialization | Separate explicit decision | User asks to initialize repository |

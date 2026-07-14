# Molnar and Gravouil (2017)

Source file: `Literature review/1-s2.0-S0168874X16304954-main.pdf`

## Thesis Role

Main reproducible staggered Abaqus UEL baseline, including phase-field convention, UEL structure, benchmark behavior, mesh/length-scale/load-increment sensitivity, and UMAT visualization layer.

## Extract Before Implementation

- Phase-field convention and bounds.
- Primary variables, nodal DOFs, element interpolation, and DOF ordering.
- Staggered sequence and convergence rule.
- `PROPS`, `SVARS`, integration-point storage, and output variables.
- Benchmark geometry, material parameters, loading, mesh sizes, and expected RF-U/crack-path trends.
- UMAT/overlay approach used for visualization.

## Starter Decisions

- Use this as the first source-code preservation and baseline reproduction target.
- Do not alter UEL/UMAT code before one-element and first benchmark baselines are reproducible.
- Treat `d=0` intact and `d=1` fully broken unless the actual source code proves otherwise.

## Open Extraction Items

- Exact one-element input deck and expected output.
- Single-edge-notched Mode I benchmark parameters.
- Reference force-displacement data or digitization method.

# Stage D0 State-Transfer Variable Map

Status: `stage_d0_initial_inventory`

Scope: controlled state transfer and later IMFD/ABAQUSER integration. This map
does not authorize a fracture-transfer Abaqus job.

## Variable inventory

| Name | Physical meaning | Location | Dimensions | Units | Valid range | Convention | Irreversibility | Source layer | Destination layer | Transfer method |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `d` | phase-field damage variable | node / UEL interpolation point, depending on export | scalar | dimensionless | `[0, 1]` | `0=intact`, `1=broken` | no healing: transferred `d_new >= d_old` where continuing same material point | U1 phase layer / derived CSV | target U1 phase layer | nodal interpolation for nodal field; IP reconstruction for UEL state |
| history field `H` / `SDV16` | maximum tensile energy/history driving crack growth | integration point | scalar | energy density, model-consistent | `>= 0` | larger value means larger historical driving state | monotone: `H_new >= H_old` | U1/U2 state output, usually visualized through UMAT layer | target integration points / visualization layer | IP-to-IP interpolation with monotone max guard |
| `SDV15` | phase output used for crack/path diagnostics | integration point / visualization element output | scalar | dimensionless | usually `[0, 1]`, observed slight overshoot possible | `0=intact`, `1=broken` | diagnostic should not decrease after accepted transfer unless documented as output artifact | UMAT visualization layer | target UMAT visualization layer | IP interpolation, then report pre/post bounds |
| `SDV14` | displacement-related phase output / auxiliary diagnostic | integration point / visualization element output | scalar | model-defined | finite | model-defined | no independent monotonicity claim | UMAT visualization layer | target UMAT visualization layer | IP interpolation; compare against independent extraction |
| `STATEV` / `SVARS` | integration-point state variables used by UEL/UMAT | integration point | vector | mixed | component-specific | component-specific | component-specific | UEL/UMAT shared state arrays | target state arrays | component-wise IP mapping with per-component guards |
| stress `S` | Cauchy stress / stress proxy for MISESERI and visualization | integration point | tensor components | kN/mm^2 | finite | Abaqus component ordering | no monotonicity claim | UMAT/CPS4 visualization layer | target visualization layer | IP interpolation, equilibrium caveat reported |
| strain `E` / `LE` | strain measure used for visualization and energy checks | integration point | tensor components | dimensionless | finite | Abaqus component ordering | no monotonicity claim | visualization/mechanical layer | target visualization layer | IP interpolation |
| degradation `g(d)` | stiffness degradation derived from phase field | node/IP derived scalar | dimensionless | `[0, 1]` plus residual stiffness policy | lower value means more degraded | follows `d`; no healing through `d` guard | derived from U1 phase state | target U2/UMAT use | recompute from transferred `d` where possible |
| element mapping | source-to-target ownership and interpolation support | element | labels / connectivity | none | all required entities mapped | deterministic label-independent geometry mapping | not applicable | source mesh | target mesh | geometry-based search with coverage report |
| integration-point mapping | source-to-target quadrature support | integration point | labels, local coordinates, weights | none | all target IPs mapped or explicitly reported | deterministic ordering | not applicable | source IP set | target IP set | centroid/local-coordinate mapping; verify ordering |
| UEL/UMAT bookkeeping arrays | shared counters, labels, layer offsets, phase/mechanical coupling data | element/IP/global arrays | mixed | mixed | finite and consistent with generated deck | code-defined | must preserve accepted state where physically meaningful | U1/U2/CPS4 generated layers | corresponding target layers | explicit table-driven mapping; no implicit label reuse |

## Required D1 checks

- all target entities mapped;
- no NaN or infinite values;
- report raw transferred values before any physical bounding;
- report bounded values after required constraints;
- `0 <= d <= 1`;
- `H_new >= H_old`;
- deterministic repeated transfer;
- nodal L2 and maximum errors;
- integration-point L2 and maximum errors;
- unmapped node/element/IP counts;
- transfer coverage;
- energy before and after transfer;
- element/IP ordering verification.

## Boundary

This inventory is a working map for controlled tests. It is not evidence that
fracture remeshing, online remeshing, or ABAQUSER output has been validated.


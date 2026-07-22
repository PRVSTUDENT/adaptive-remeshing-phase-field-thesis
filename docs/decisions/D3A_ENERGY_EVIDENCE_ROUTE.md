# D3A Energy Evidence Route

Classification: `stage_d3a_energy_reconstruction_authorized`

Date: 2026-07-22

## Decision

The existing H0 checkpoint state from source job `1376154.mmaster02` remains
scientifically usable for Stage D3A because the checkpoint was extracted from
the accepted Molnar single-notch H0 ODB at
`U2 = 0.003000000026077032 mm`, with complete physical element/IP state
coverage and finite `SDV15`/`SDV16`.

The existing H0 global energy history is unavailable: the source ODB does not
contain `ALLIE`, `ALLSE`, or `ALLWK`. This absence blocks the previous D3A
acceptance route, but it does not invalidate the already extracted checkpoint
state.

The current Molnar UEL energy reporting also requires verification. The UEL
computes the pointwise elastic energy density
`0.5 * stress : strain`, stores degraded and undegraded densities in `SDV12`
and `SDV13`, and assigns `ENERGY(2)=ENG` inside the integration-point loop.
That assignment is not visibly accumulated over integration points or scaled by
quadrature weight, Jacobian determinant, and thickness before assignment.

Therefore, the selected recovery route is an independent quadrature-based
energy reconstruction from the existing accepted H0 ODB, the H0 input deck
coordinates/connectivity, the checkpoint nodal phase field, and the exported
integration-point state.

## Scope

- Existing H0 checkpoint state: scientifically usable.
- Existing H0 global energy history: unavailable.
- Current UEL `ENERGY` reporting: requires verification.
- Selected recovery: independent quadrature-based energy reconstruction.
- New fracture solve: not required initially.

This decision does not waive the D3A energy requirement. It replaces unavailable
or potentially incomplete global UEL energy history with independently
reproducible energy calculations. Only if the reconstruction passes its
predeclared checks may D3A be closed with
`stage_d3a_checkpoint_pass_independent_energy_reconstruction`.

## Predeclared Diagnostic Tolerance

The provisional energy-balance tolerance is:

```text
relative balance residual <= 5%
```

The residual must be reported directly and must not be forced to close by
post-hoc scaling.

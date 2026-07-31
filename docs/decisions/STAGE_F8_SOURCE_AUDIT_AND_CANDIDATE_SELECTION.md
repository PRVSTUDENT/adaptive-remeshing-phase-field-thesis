# Stage F8 source audit and candidate selection

Frozen source SHA-256:
`49c9054ab5faec9e069e0a9149af5058e6f1e11ab164c2a0e318f60282309b37`.

## Variable and update map

| Quantity | Frozen implementation |
|---|---|
| Phase-field nodal DOF | U1 element nodal degree of freedom 3; received as `U(1:4)` |
| Integration-point phase | `PHASE = sum(N_i U_i)` |
| Phase gradient | `DP = B_phase U` |
| SDV14 | visualization copy selected from the U1 phase state during the staggered call sequence |
| SDV15 | U1 `SDV(1)`, the interpolated phase, copied through `USRVAR(...,15,IP)` |
| SDV16 | U1 `SDV(2)`, the maximum elastic-energy history, copied through `USRVAR(...,16,IP)` |
| Crack-driving energy | undegraded elastic energy `SDV(13)` from U2 |
| History variable | `HIST=max(ENGN,HISTN)`; stored as U1 `SDV(2)`/visualization SDV16 |
| Old state | U1 `SVARS`, plus the previously stored `USRVAR` common block |
| Trial state | current Abaqus `U`, `DU`, and values written during the staggered call |
| Committed state | Abaqus commits returned `SVARS` at a converged increment |

The phase residual and tangent solve a nodal phase-field system driven by the
monotone integration-point history. There is no active set, variational
inequality, penalty, augmented Lagrangian, nodal projection, or
integration-point projection enforcing `d_(n+1) >= d_n`. SDV16 is the
history variable, not the phase field.

SDV14 and SDV15 can both decrease because both are views of the unconstrained
nodal phase solution at different positions in the staggered synchronization
sequence. The maximum-history update prevents the driving energy from
decreasing; it does not itself impose an obstacle on the nodal unknown.
Clamping SDV15 alone would change only reported state and not the governing
solution, so that approach is rejected.

## Selected candidate

The selected minimal candidate is a consistent quadrature-point penalty on
`d_(n+1)-d_n`. For a negative gap, it adds

`Pi_p = 0.5 beta <d_n-d_(n+1)>_+^2`

to the phase functional. Its residual contribution is
`beta (d_(n+1)-d_n) N_i`, and its active tangent is
`beta N_i N_j`. The prior converged integration-point phase is read from U1
`SVARS`; `beta = 10^6 Gc/lc`. Thus the candidate changes the solved phase
equation consistently and is not an output clamp. It is a penalty
approximation, not an exact nodal obstacle: finite-penalty leakage and
conditioning are explicit limitations. The minimal experiment must decide
whether those limitations are acceptable before any larger test.

Elastic constants, fracture parameters, degradation, residual stiffness,
geometry, mesh, loading, increments, and outputs are identical between the
paired decks. The original frozen source remains unchanged.

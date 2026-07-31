# Stage F11 source-difference allowlist

The F11 decks are byte-identical. Relative to F10, both sources may differ
only by identical diagnostic infrastructure: COMMON size 28, SDV19--SDV28
storage, bounds-safe UMAT transfer, and the bounded prior-state log.

Between the F11 baseline and candidate, the only governing-equation
difference remains the F10 candidate penalty branch:

- `beta = 1e6*Gc/lc`;
- active residual contribution proportional to `beta*(d-d_old)`;
- active tangent proportional to `beta*N_i*N_j`.

Candidate-only diagnostic assignments inside that same active branch may set
the active flag and exact penalty energy/residual/tangent magnitudes. No
geometry, loading, material, mapping, non-penalty residual, or non-penalty
tangent difference is permitted.

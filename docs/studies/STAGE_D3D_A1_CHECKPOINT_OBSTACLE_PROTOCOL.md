# Stage D3D-A1 Checkpoint Obstacle Protocol

## Objective

Solve the convex phase-field obstacle problem at the unchanged D3D checkpoint:

\[
\mathbf r=\mathbf K(H_{F3})\mathbf d-\mathbf f(H_{F3}),\qquad
\mathbf d\geq\mathbf d_{F3}.
\]

The fixed inputs are the 6,601 recovered F3 nodal phase values, 25,600 actual
F3 SDV16 values, the accepted D3A5/R4 active set, and the 30 active nodes whose
F3 multipliers are below \(-10^{-8}\).

## Deterministic primal-dual iteration

1. Initialize free membership with the prior 155 free nodes plus the 30-node
   release seed.
2. Fix active nodes at the F3 lower bound and solve the reduced sparse system.
3. Reactivate free nodes below the lower bound by more than \(10^{-10}\).
4. Release active nodes with multiplier below \(-10^{-8}\).
5. Keep bound nodes active when their multiplier satisfies the dual gate.
6. Stop only when the free residual, multiplier, bound, and membership gates
   pass, or fail after 200 iterations.

No parameter adjustment or automatic retry is permitted.

## Gates

| Quantity | Gate |
|---|---:|
| Free residual infinity norm | \(\leq10^{-8}\) |
| Minimum active multiplier | \(\geq-10^{-8}\) |
| Active bound error | \(\leq10^{-10}\) |
| Lower-bound tolerance | \(10^{-10}\) |
| Phase functional change | \(\leq0\) within extraction precision |
| Phase/history coverage | 6,601 nodes / 25,600 IPs |
| H changes | 0 |
| Non-positive Jacobians | 0 |

Pass classification:
`stage_d3d_a1_checkpoint_obstacle_update_pass`.

Fail classification:
`stage_d3d_a1_checkpoint_obstacle_update_fail`.

## Candidate-package semantics

After a pass only:

- transferred nodal phase: corrected offline phase;
- transferred IP history: unchanged actual F3 SDV16;
- nodal lower bound: original recovered F3 phase;
- active/free membership: converged KKT set.

Classification: `stage_d3d_a1_candidate_package_prepared`. The package is not
an accepted restart because mechanical equilibrium has not been recomputed.

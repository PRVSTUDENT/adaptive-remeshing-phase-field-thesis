# Stage F11 qualification decision

The penalty candidate qualifies on the instrumented minimal model. It
suppresses phase decreases below the `1e-7` precision threshold, activates
explicitly and consistently, satisfies the predeclared diagnostic-energy
policy, preserves RF--U response and initial stiffness, and introduces no
material convergence pathology.

This permits preparation—but not submission—of a future medium-H1
verification package. It does not support an H2 or production claim.

The native Abaqus 2023 `RemeshingRule.variables` contract is qualified:
`variables=('MISESERI',)` with the tuple element being Python 2 `str`.

# Stage F12 rollback result

Both minimal candidate analyses solved to the prescribed endpoint. The
conservative reference used 106 increments and 128 equilibrium iterations
with zero cutbacks. Its fixed-point phase remained within the `1e-7` policy,
SDV16 was monotone, and its maximum positive diagnostic imbalance was
`1.3310e-7`.

The aggressive analysis used one increment per step, two total iterations,
and Abaqus explicitly reported zero cutbacks. It therefore did not exercise
rollback and is classified `penalty_rollback_not_exercised`. The coarse
increment path also failed the predeclared response and energy comparisons:
final RF1 differed from the reference by `0.4730835`, and maximum positive
diagnostic imbalance was `3.8957e-5`.

Both PBS wrappers returned 1 only after their successful Abaqus solves and
ODB extraction because unit 99 was not copied back from Abaqus scratch as
`fort.99`. No rejected increment existed to audit, and no retry or replacement
is authorized. This result does not qualify rollback and does not make the H1
pair ready for submission authorization.

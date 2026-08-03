# Stage F20 rollback evidence decision

The two retained raw UEL logs were recovered byte-for-byte from the completed
F19 scratch work roots. They prove one deliberate forced cutback event:
penalty was active, `PNEWDT=0.5` was requested, Abaqus abandoned the 0.02
increment and retried at 0.01, and the retry began from the preceding committed
phase and SVARS. The rejected trial phase was not retained and the endpoint
was reached.

The branch-aware control/forced comparison uses step as the loading-branch key
and linearly interpolates only within each branch. It uses 149 aligned rows and
zero extrapolations. Endpoint displacement and maximum absolute RF difference
pass, but RF--U NRMSE is `2.6094442112598113e-4` (limit `1e-4`) and relative
external-work difference is `3.108913192355678e-4` (limit `1e-4`).

Classification: `penalty_rollback_response_mismatch`. This is not missing
evidence and does not justify an unchanged rollback repeat. No CTL6/FORCE6
package is prepared. Medium H1 remains blocked and unauthorized.

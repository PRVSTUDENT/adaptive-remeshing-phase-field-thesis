# Stage F9 diagnostic batch preparation

Stage F9 separates the two independent Stage F8 blockers. `M2DKMAT1` runs at
most five planned Abaqus datachecks within a six-case hard limit. Nonzero
case return codes are evidence and do not abort the matrix. No analysis,
restart, continuation, or penalty-candidate execution is reachable.

The static label audit maps phase `JELEM`, displacement
`JELEM - N_ELEM`, and visualization `NOEL - 2*N_ELEM` to `1..23`, with
`N_ELEM=33852`. The diagnostic sequence is exact reproduction, debug
compiler reproduction, UEL without visualization, UMAT-only initialization,
and a simplified one-step UEL control.

`M2RMTYPE1` is CAE-only. It preserves the F7 Unicode failure as a control and
tests a bounded set of documented Python 2 representations, stopping after
the first accepted publication-faithful `RemeshingRule`. Static scanning
finds no solver, qsub, subprocess, or system-command launch path.

The jobs have independent eligibility. Both static preflights run before the
first qsub, but one failure cannot block an independently eligible peer.
Submission remains disabled until the preparation commit is pushed and the
cluster preflight passes.

Local evidence:

- Stage F8 and F9 targeted tests: 13 passed.
- Full unit suite: 293 passed, one unrelated pre-existing F6 assertion failed.
- H2 and corrected MISESERI static validators: passed.
- Abaqus Python 2.7 compilation: passed.
- Bootstrap validator and shell syntax checks: passed.

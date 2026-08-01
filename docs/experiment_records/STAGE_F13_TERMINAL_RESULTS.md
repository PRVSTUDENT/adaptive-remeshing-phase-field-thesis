# Stage F13 terminal results

Jobs `1380981`, `1380982`, and `1380983` ran once and are terminal. No retry,
replacement, direct qsub, qdel, or qmove occurred.

Both rollback jobs passed hash checks, compiled and linked the user subroutine,
and completed Abaqus input processing. Abaqus/Standard then stopped before the
first increment because `libstandardU.so` referenced the unresolved symbol
`for_getenv_err`. The rollback logs are empty, no PNEWDT trigger fired, no
attempt was abandoned and retried, and neither endpoint nor response/energy
comparison exists. The control is `penalty_rollback_inconclusive`; the forced
lane is `penalty_rollback_cutback_not_triggered`. Rollback is not qualified.

The native job preserved the official 3,930-value MISESERI field and reached
the declared `model.adaptiveRemesh(odb)` call. Abaqus rejected the call because
the model contained no adaptive regions. The completed remesh count is zero,
no candidate was generated, and integrity/targeting metrics are unavailable.
Classification: `native_miseseri_remesh_operation_failed`.

Execution counts remain: source solver 0, adaptive-process submissions 0,
completed native remesh calls 0, and refined-mesh solver 0.

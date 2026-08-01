# Stage F16 R3 routed-queue batch closeout

The three explicitly authorized submissions were accepted through
`entry_imfdfkmq` and routed to `normal_imfdfkmq`. No retry, replacement,
direct qsub, qdel, or qmove occurred.

Jobs `1381444.mmaster02` and `1381445.mmaster02` completed with exit status
zero. The forced job produced exactly one controlled cutback. Its call trace
shows that the retry began from the committed phase/SVARS state, but the
rejected trial had positive phase advance, zero penalty residual, and zero
penalty energy. Therefore the cutback mechanism is technically demonstrated
while penalty rollback remains scientifically inconclusive. The PBS wrapper
did not preserve the extracted ODB response tables, so the frozen response
equivalence tolerances cannot be evaluated from the retained evidence.

Job `1381446.mmaster02` exited one before solver, native-remesh, adaptivity,
or refined execution. Abaqus Python rejected a generator expression supplied
to `sum` while constructing the native adaptive region. Classification:
`native_adaptive_region_construction_failed`.

All six mandatory Telegram START/terminal notifications passed on their first
bounded attempt with curl return code zero, HTTP 200, and `ok=true`. PBS email
remains best-effort. Execution authority is consumed and no further jobs are
authorized.

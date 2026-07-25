# Previous P3-S GETRANK interface audit

Job `1378028.mmaster02` used the preserved source
`runs/hpc/stage_p/p3s_serial_diagnostic/raw_failure_evidence/p3_instrumented_commonblock.for`.

- Declaration in `UEXTERNALDB`: line 273,
  `INTEGER GETRANK,GETTHREADID`.
- Invocation in `UEXTERNALDB(LOP=0)`: line 283,
  `RANK=GETRANK()`.
- Call location: analysis-start `UEXTERNALDB`, before UEL or UMAT.
- `SMAAspUserSubroutines.hdr` included: no.
- Installed/documented `CALL GETRANK(KPROCESSNUM)` form used: no.

The earlier source used GETRANK as an integer function expression, not as a
subroutine call. The installed Abaqus 2023 bounded header search did not expose
a GETRANK declaration, while `libstandardB.so` exports `getrank_`. This audit
therefore does not reinterpret the earlier signal 11 as a test of the
documented subroutine-call interface.

# P3-SM1R GETRANK serial qualification

This directory holds the fail-closed authorization record and, only after a
separate authorization and execution, the closure evidence for P3-SM1R.

The prepared lane is a one-rank, one-thread Abaqus 2023 qualification of the
documented `CALL GETRANK(KPROCESSNUM)` interface inside the controlled UEL
condition `JELEM=1, KSTEP=1, KINC=1`. It makes no thread-safety, MPI scaling,
hybrid, or production claim.

Closure state: job `1378241.mmaster02` passed as
`stage_p3sm1r_getrank_serial_pass`. Authorization is consumed `1/1`, submission
authorization is false, and automatic retry remains disabled. This qualifies
only rank zero from the controlled serial UEL call. P3-T4 and all downstream
lanes remain blocked.

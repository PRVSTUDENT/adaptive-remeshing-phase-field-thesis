# P3-SM1R GETRANK serial qualification

This directory holds the fail-closed authorization record and, only after a
separate authorization and execution, the closure evidence for P3-SM1R.

The prepared lane is a one-rank, one-thread Abaqus 2023 qualification of the
documented `CALL GETRANK(KPROCESSNUM)` interface inside the controlled UEL
condition `JELEM=1, KSTEP=1, KINC=1`. It makes no thread-safety, MPI scaling,
hybrid, or production claim.

Current state: prepared offline, submission unauthorized, usage `0/1`, automatic
retry disabled. P3-T4 and all downstream lanes remain blocked. Do not submit
without a separate explicit authorization.

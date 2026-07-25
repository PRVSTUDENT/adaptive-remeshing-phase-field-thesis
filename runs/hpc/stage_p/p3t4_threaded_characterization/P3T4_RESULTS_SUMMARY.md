# P3-T4-J1 closure

Job `1378242.mmaster02` ran exactly once from authorization revision
`71d42487cbf9165b9b7aca2b6e34fcae7a0b77b9`.

- Classification: `stage_p3t4_threaded_fail_compile`
- Scheduler exit: `10`
- Abaqus compilation exit / recorded solver exit: `1`
- Compile complete: false
- Link, input processing, Standard completion, and ODB: not reached
- Callback/access/conflict diagnostics: not reached
- Scientific serial comparison: not reached
- Completion marker: absent

Intel reported the first syntax error at the UEL declaration and then treated
the following declarations as a main program. Offline inspection localized
the cause: `#include <SMAAspUserSubroutines.hdr>` was placed before the first
Fortran subroutine, so the included interface declarations appeared outside a
valid scoping unit. The already-qualified P3-SM1TC source places the same
aggregate header after its UEL declaration and `ABA_PARAM.INC`.

The hash-controlled staged inputs matched the authorized manifest. No ODB was
created, so there is no scratch ODB path, size, timestamp, or SHA-256 to
preserve.

Authorization is consumed `1/1`, submission authorization is false, and
automatic retry remains disabled. The failure is preserved without retry or
replacement. MPI, hybrid, P4, production H1, D3D-A1 reopening, and D3E remain
blocked.

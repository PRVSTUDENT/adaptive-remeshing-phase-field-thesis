# P3-SM1R closure

Job `1378241.mmaster02` ran exactly once from authorization revision
`4e941ffa7740a4c8050277351f25bcf392f8cd98` and passed with classification
`stage_p3sm1r_getrank_serial_pass`.

- PBS and solver exit: `0/0`
- Fortran compile/link, input processing, Abaqus/Standard completion: pass
- ODB readable: true
- P3-SM0 callbacks: all four observed
- GETRANK before/after markers: `3/3`; unmatched calls: `0`
- Returned process IDs: `[0, 0, 0]`; unique IDs: `[0]`
- Signal 11 and unresolved GETRANK symbol: absent
- State records: `32/32`
- Nonfinite, phase, history, and transfer violations: `0`
- Increment records: `13`
- Completion marker: present

The result supports only that `CALL GETRANK(KPROCESSNUM)` completed in the
controlled UEL callback and returned process rank zero under one MPI rank and
one OpenMP thread. It does not establish MPI safety or multithreaded
COMMON-block safety.

Authorization is consumed `1/1`; no retry is authorized. P3-T4 and every
downstream lane remain blocked.

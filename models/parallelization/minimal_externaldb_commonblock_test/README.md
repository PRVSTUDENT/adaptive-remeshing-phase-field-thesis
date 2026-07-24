# P2 Minimal ExternalDB/Common-Block Characterization Package

Preparation-only package; no solver execution has been authorized or run.

The input is copied from the D2 tiny-transfer model and contains eight physical
elements, allowing more than one element to be scheduled. The isolated
Fortran copy preserves the scientific calculations and adds bounded
diagnostics:

- rank and thread identifier through `GETRANK()`/`GETTHREADID()`;
- first UEL and UMAT call per rank/thread;
- element, integration point, step and increment;
- final per-rank/thread UEL/UMAT call counts;
- mutex protection for diagnostic counters and diagnostic writes.
- first read/write access per shared variable and physical index;
- initialization-tagged `TRANSFER_DONE` writes;
- live read-during-write and write-during-write conflict tokens.

The instrumentation intentionally does not repair `KUSER` or `D2INIT`; P3 is
meant to characterize unchanged shared-state behavior first. The utility
interfaces must be verified against the installed Abaqus 2022 documentation
or compile gate before solver execution. Logs are expected in the Abaqus
message file (unit 7); no independently opened shared log is used.

Files:

- `P2_minimal_parallel_characterization.inp`
- `p2_instrumented_commonblock.for`
- `d2_transfer_table.inc`
- `P3S_serial_diagnostic.inp` (serial continuation/reference deck)

Blocked: all P3 jobs, MPI/hybrid claims, refactoring, and production use.

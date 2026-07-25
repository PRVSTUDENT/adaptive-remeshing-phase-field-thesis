# P3-T4 threaded characterization

The one authorized `1 MPI rank x 4 OpenMP threads` characterization ran as
job `1378242.mmaster02` and closed as
`stage_p3t4_threaded_fail_compile`. Authorization is consumed `1/1`;
automatic retry and every downstream permission remain false.

Compilation stopped because the aggregate Abaqus utility header was placed
outside a Fortran scoping unit. No callback, shared-state, threading, or
scientific-equivalence evidence was produced. No further P3-T4 or other
Abaqus/PBS job is authorized.

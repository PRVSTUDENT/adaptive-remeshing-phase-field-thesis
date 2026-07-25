# P3-T4 threaded characterization

Offline-prepared, fail-closed `1 MPI rank x 4 OpenMP threads` characterization
of the accepted eight-element P3-SM0 science. Execution authorization is false
at `0/1`; automatic retry and every downstream permission are false.

The instrumentation observes unsynchronized scientific COMMON/SAVE accesses.
Its Abaqus mutex protects only diagnostic counters and metadata. No P3-T4 or
other Abaqus/PBS job is authorized by this preparation.

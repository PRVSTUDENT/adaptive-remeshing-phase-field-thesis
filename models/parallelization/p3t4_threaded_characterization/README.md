# P3-T4 bounded threaded characterization package

Preparation-only package for one MPI rank and four OpenMP threads. It uses the
accepted P3-SM0 deck, transfer table, and scientific calculations while adding
diagnostic instrumentation for callback threads and shared-state access.

The diagnostic mutex protects metadata only. Execution remains unauthorized.

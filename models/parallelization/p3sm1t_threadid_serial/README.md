# P3-SM1T isolated GETTHREADID serial package

Preparation-only package derived from the accepted P3-SM0 lane. The deck and
transfer include are byte-identical to P3-SM0. The source adds one local
`GETTHREADID()` hook inside the controlled UEL callback and preserves all
accepted scientific calculations and P3-SM0 markers.

Execution is not authorized. Repeated marker pairs are expected if Abaqus
enters the controlled callback more than once; the parser counts rather than
suppresses them.

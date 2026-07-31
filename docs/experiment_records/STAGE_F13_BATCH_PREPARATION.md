# Stage F13 batch preparation

Stage F13 reuses the Stage F11-qualified 23-element penalty formulation. The control and forced packages have byte-identical decks and Fortran sources; their only runtime distinction is `F13_FORCE_CUTBACK=0` or `1`.

The controlled branch is diagnostic-only and may change only `PNEWDT` plus bounded explicit-path logging. It targets step 2, `0 <= TIME(1) < 0.04`, UEL element 1, integration point 2, and requests `PNEWDT=0.5` only when `DTIME > 0.015`. The shared initial `DTIME=0.02` qualifies and its expected `DTIME=0.01` retry cannot retrigger.

`F13_ROLLBACK_LOG` is mandatory and is set to an absolute path beneath each immutable evidence directory. Each PBS script performs a create/write/read/truncate routing smoke check before Abaqus starts; no `fort.99` dependency remains.

The native-remesh package freezes the corrected 3,930-element CPE4 deck and official ODB hashes. It permits one source solver execution, one adaptive-process execution and one remesh operation, but zero candidate solver executions. A generated candidate may only be written and statically inspected.

Preparation tests: 34 Stage F9--F13 unit tests passed. Local pytest remains unavailable and was not installed. Existing dirty canonical H1 validation products were preserved and therefore not regenerated in place.

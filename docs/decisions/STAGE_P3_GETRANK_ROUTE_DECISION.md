# Stage P3 GETRANK route decision

## Decision

Prepare P3-SM1R offline as a separate, fail-closed serial qualification of the
documented Abaqus subroutine interface:

```fortran
      INTEGER KPROCESSNUM
        WRITE(7,*) 'P3SM1R_BEFORE_GETRANK'
        CALL GETRANK(KPROCESSNUM)
        WRITE(7,*) 'P3SM1R_AFTER_GETRANK ',KPROCESSNUM
```

The call is confined to the existing controlled UEL condition
`JELEM=1, KSTEP=1, KINC=1`. There is no GETRANK call in UEXTERNALDB, no
`get_thread_id()`, and no scientific-model change.

## Basis and scope

P3-SM1TC successfully qualified the corrected `get_thread_id()` serial
interface in Git commit `bc4655428654c291aacb8d96248706698ba284a8`. That
result does not qualify GETRANK, thread safety, MPI, or hybrid execution.
P3-SM1R therefore remains a distinct qualification rather than an inference
from P3-SM1TC.

The prepared P3-SM1R lane requires a returned process-ID list whose unique
value is `[0]` for its one-rank job, matching before/after markers, all four
P3-SM0 callback markers, and every baseline state, RF-U, energy, increment,
ODB, compilation, linking, and solver gate.

## Release state

P3-SM1R is prepared but not authorized: submission authorization is `false`,
usage is `0/1`, and automatic retry is disabled. No PBS/Abaqus job is released
by this decision. The package must be committed, synchronized, reviewed, and
separately authorized before its one permitted submission.

P3-T4, MPI, hybrid, P4, production H1, D3D-A1 reopening, and D3E remain
blocked.

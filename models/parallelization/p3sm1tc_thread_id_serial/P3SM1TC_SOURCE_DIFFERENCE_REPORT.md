# P3-SM1TC source difference report

Scientific reference: P3-SM0 source SHA-256
`0091a4dc3b39829542f718d722bb2129f1bac7491e1f03b4e38ef12394e852d4`.

Candidate SHA-256:
`8cf3714a47bab234078fbedea809c7283a81059c9a112f4ef9613bb598b11d32`.

The complete additions are:

```fortran
10:#include <SMAAspUserSubroutines.hdr>
26:      INTEGER THREAD_ID
30:        WRITE(7,*) 'P3SM1TC_BEFORE_GET_THREAD_ID'
31:        THREAD_ID=get_thread_id()
32:        WRITE(7,*) 'P3SM1TC_AFTER_GET_THREAD_ID ',THREAD_ID
```

There are no deletions or replacements. The executable hook is inside the
existing `JELEM=1, KSTEP=1, KINC=1` UEL condition. All scientific
calculations and four P3-SM0 markers are unchanged. The source contains no
`GETTHREADID()`, `GETRANK`, `GETNUMTHREADS`, mutex call, or diagnostic shared
storage.

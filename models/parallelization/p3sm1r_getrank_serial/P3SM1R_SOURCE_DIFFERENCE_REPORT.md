# P3-SM1R source difference report

Scientific reference: P3-SM0 source SHA-256
`0091a4dc3b39829542f718d722bb2129f1bac7491e1f03b4e38ef12394e852d4`.

Candidate SHA-256:
`4a6f8d9a67661f83d9c5899ffb4654871645e6ba0d503a1906269536ccfd00e7`.

The complete additions are:

```fortran
25:      INTEGER KPROCESSNUM
29:        WRITE(7,*) 'P3SM1R_BEFORE_GETRANK'
30:        CALL GETRANK(KPROCESSNUM)
31:        WRITE(7,*) 'P3SM1R_AFTER_GETRANK ',KPROCESSNUM
```

There are no deletions or replacements. The call is inside the existing
`JELEM=1, KSTEP=1, KINC=1` UEL condition. All scientific calculations and
four P3-SM0 markers are unchanged. The source has no GETRANK call in
UEXTERNALDB, no `get_thread_id()`, no `GETTHREADID()`, no mutex call, and no
diagnostic shared storage.

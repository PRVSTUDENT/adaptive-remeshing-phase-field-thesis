# P3-SM1T source difference report

Reference: `p3sm0_minimal_callback.for`, SHA-256
`0091a4dc3b39829542f718d722bb2129f1bac7491e1f03b4e38ef12394e852d4`.

Candidate: `p3sm1t_threadid_callback.for`, SHA-256
`468b633793505e641d1a87d0e97312e59a8c4a3501285573c6c6eb7f280a0b97`.

Every added line is listed below; there are no deletions or replacements:

```fortran
25:      INTEGER GETTHREADID,THREAD_ID
29:        WRITE(7,*) 'P3SM1T_BEFORE_GETTHREADID'
30:        THREAD_ID=GETTHREADID()
31:        WRITE(7,*) 'P3SM1T_AFTER_GETTHREADID ',THREAD_ID
```

The declaration is local to UEL. The three executable lines are inside the
existing `JELEM.EQ.1 .AND. KSTEP.EQ.1 .AND. KINC.EQ.1` marker condition.
All P3-SM0 UEL/UMAT calculations and all four P3-SM0 callback markers are
otherwise byte-for-byte unchanged. There is no `GETRANK`, shared diagnostic
storage, mutex utility, or `SAVE`-based suppression flag.

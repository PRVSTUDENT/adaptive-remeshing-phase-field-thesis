# P3-T4 source difference report

Scientific reference: P3-SM0 source SHA-256
`0091a4dc3b39829542f718d722bb2129f1bac7491e1f03b4e38ef12394e852d4`.

Instrumented candidate SHA-256:
`c62986d45eef018ebad098caee12f9a9b0cebf464becd7fb5c0bc1045d290642`.

The P3-SM0 UEL and UMAT scientific assignments, constitutive expressions,
element routing, transfer values, COMMON dimensions, and BLOCK DATA
initialization are unchanged. The deck and transfer include are byte-identical
to P3-SM0.

The source-only additions are:

- the installed Abaqus utility header;
- UEL/UMAT callback tracing;
- read and begin/end-write calls bracketing existing scientific accesses;
- qualified `CALL GETRANK(RANK)` and `get_thread_id()` calls inside diagnostic
  helpers invoked from UEL/UMAT;
- mutex-protected diagnostic counts, ownership, active-writer and conflict
  metadata;
- deterministic UEXTERNALDB mutex initialization, constant P3-SM0 markers,
  and final diagnostic summaries;
- diagnostic COMMON/BLOCK DATA storage.

No identifier call occurs in UEXTERNALDB. The source contains neither
function-form `GETRANK()` nor `GETTHREADID()`. Mutex calls do not surround an
USRVAR or TRANSFER_DONE scientific operation: begin metadata is unlocked before
the operation and end metadata is locked only after it.

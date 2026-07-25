# Stage P3 identifier-interface decision

Date: 2026-07-25

## Evidence

P3-SM1T job `1378239.mmaster02` compiled, linked, and completed input
processing. Its source expression `THREAD_ID=GETTHREADID()` requested
`getthreadid_`; dynamic resolution failed at the first invocation after one
before marker and before any returned value. This does not test the installed
`get_thread_id()` interface and is not thread-safety evidence.

The installed aggregate header `SMAAspUserSubroutines.hdr` includes
`SMAAspUserUtilities.hdr`, which declares:

```fortran
FUNCTION get_thread_id ( ) RESULT ( threadID )
```

It does not declare `GETTHREADID`. The bounded installed-header search did not
find a GETRANK declaration. Runtime inspection found `get_thread_id_` as an
undefined dependency and `getrank_` as a defined symbol in `libstandardB.so`;
`dmpc_getrank_` is defined in `libABQDMP_Core.so`.

## Decision

Classification: `stage_p3_identifier_interface_partially_confirmed`.

1. `THREAD_ID=GETTHREADID()` is the failed, undocumented attempted interface
   and requested unresolved symbol `getthreadid_`.
2. `#include <SMAAspUserSubroutines.hdr>` with
   `THREAD_ID=get_thread_id()` is confirmed by the installed Abaqus 2023
   Fortran header and may be prepared as a new P3-SM1TC qualification lane.
3. `CALL GETRANK(KPROCESSNUM)` remains documentation-supported but is not
   confirmed by the installed header audit; P3-SM1R stays design-only.

P3-SM1TC is a new technical qualification, not an unchanged retry. It remains
unauthorized. P3-T4 and all downstream routes remain blocked.

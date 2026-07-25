# P3-T4 header-scope forensic correction

This is a non-executable forensic record. It does not modify or supersede the
closed P3-T4 source, job evidence, classification, or consumed authorization.

## Observed invalid placement

The failed source placed the aggregate interface header at file scope before
the first program unit:

```fortran
#include <SMAAspUserSubroutines.hdr>
      SUBROUTINE UEL(...)
      INCLUDE 'ABA_PARAM.INC'
```

Intel expanded the header successfully during preprocessing, but its Fortran
interface declarations then appeared outside a valid scoping unit. Compilation
reported the UEL declaration as incorrectly positioned and interpreted later
declarations as belonging to an invalid main program. This proves that
preprocessing success is insufficient.

## Structurally valid future pattern

Every program unit that directly uses a declared utility must include the
aggregate header inside that unit:

```fortran
      SUBROUTINE KP3TRACE(...)
      INCLUDE 'ABA_PARAM.INC'
#include <SMAAspUserSubroutines.hdr>
      INTEGER KPROCESSNUM,THREAD_ID

      CALL GETRANK(KPROCESSNUM)
      THREAD_ID=get_thread_id()
```

For the failed diagnostic design, direct utility users were:

- `KP3READ`: `GETRANK`, `get_thread_id`, `MutexLock`, `MutexUnlock`;
- `KP3BEGINWRITE`: `GETRANK`, `get_thread_id`, `MutexLock`,
  `MutexUnlock`;
- `KP3ENDWRITE`: `GETRANK`, `get_thread_id`, `MutexLock`,
  `MutexUnlock`;
- `KP2TRACE`: `GETRANK`, `get_thread_id`, `MutexLock`, `MutexUnlock`;
- `UEXTERNALDB`: `MutexInit` only.

UEL and UMAT invoked diagnostic helpers but did not directly call these
utilities, so they would not require the aggregate header solely for those
helper calls.

## Prevention rules

1. Preserve job `1378242.mmaster02`, the failed source, and all closure
   evidence unchanged.
2. Treat successful preprocessing only as a lexical/include-resolution gate,
   never as a Fortran compilation gate.
3. Verify that every expanded interface block resides inside a valid Fortran
   program unit and before executable statements.
4. Require a real Intel/Abaqus compile-and-user-library-link gate before any
   future solver authorization involving a new utility-header arrangement.
5. A compile-only gate must have a distinct name such as P3-T4C, a distinct
   package and decision record, authorization false by default, a one-shot
   limit, and no solver execution.
6. A successful compile-only result would qualify only compilation and
   linking. It would not qualify callbacks, threading, COMMON/SAVE safety,
   MPI, hybrid execution, or another P3-T4 solver run.

No corrected executable source is created by this record.

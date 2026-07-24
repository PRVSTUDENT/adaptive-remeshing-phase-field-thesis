# P3-SM minimal callback-only diagnostic design

Design only. No executable source, Abaqus execution, or PBS submission is authorized.

P3-SM is intentionally deferred until P3-SB is reviewed. Its purpose would be to establish callback availability and ordering without the P3-S shared-access database.

Required minimal behavior:

1. Emit one constant `UEXTERNALDB(LOP=0)` entry marker without calling `GETRANK`, `GETTHREADID`, mutex utilities, or shared-state helpers.
2. Emit one first-UAL/UEL marker and one first-UMAT marker.
3. Obtain rank/thread identifiers only at the element callback after callback entry has independently been proven, and isolate each utility call so the last successful marker is unambiguous.
4. Do not add shared-access arrays, ownership monitoring, diagnostic COMMON/BLOCK DATA, or mutex-protected event storage.
5. Preserve all accepted D2 scientific calculations byte-for-byte outside the minimal callback hooks.

The phrase “first-UAL” in the stage instruction is treated as “first UEL” because this package implements `UEL`, not a `UAL` subroutine.

P3-SM is not the recommended first future run: the current failure occurred before the eight-element baseline was tested.

# P3-S signal-11 failure timeline

Job `1378028.mmaster02` is a closed technical failure. This timeline does not constitute a serial or parallel shared-state result.

| Time (CEST) | Observation |
|---|---|
| 11:10:46 | The immutable deck, instrumented Fortran, transfer table and command were staged. |
| 11:10:47 | Abaqus 2023 began compiling the user subroutine. |
| 11:10:53 | Compilation and linking completed; the input-file processor started. |
| 11:10:55 | The input-file processor produced the `.dat`, `.prt`, and a 247,488-byte ODB. |
| 11:10:59 | Abaqus/Standard analysis began. No `.sta` file was created. |
| 11:11:00 | The exception report recorded a segmentation violation in the element-loop context. Its call stack is `dmpc_getrank -> uexternaldb -> openfs -> std_main`. |
| 11:11:02 | Abaqus reported rank 0 terminated by signal 11 and exited with solver status 1. |

## Callback boundary

`UEXTERNALDB(LOP=0)` was entered. In the exact staged source, that branch calls `MUTEXINIT(91)`, then `GETRANK()`, then `GETTHREADID()`, and only afterward writes `P2_INIT`. The stack reaches `dmpc_getrank`, and no `P2_INIT` record exists. Thus `GETRANK()` was reached but did not complete. The evidence does not prove whether `MUTEXINIT(91)` completed normally.

No UEL, UMAT, `P2_FIRST`, `P3_ACCESS`, shared-state read/write, element number, or integration point was observed. Therefore the crash preceded the diagnostic shared-access monitor and any element-level scientific calculation.

## Answers to the forensic questions

1. `UEXTERNALDB(LOP=0)` observed: **yes**, by stack trace.
2. `MUTEXINIT(91)` reached: **yes by source order**; successful return is unknown.
3. First UEL call observed: **no**.
4. First UMAT call observed: **no**.
5. `P3_ACCESS`, `P2_FIRST`, or initialization record written: **no**.
6. Active element/routine before signal 11: no element; `UEXTERNALDB`, inside `GETRANK`.
7. Shared-state read/write: **before** the first monitored access.
8. `.sta` created: **no**.
9. ODB created: **yes**, 247,488 bytes; retained in scratch only and not interpreted as a solution.
10. Offending routine/address: `dmpc_getrank`, address `0x1504bdcc0594`.

## Bounded conclusion

The immediate failure is localized to the diagnostic `GETRANK()` call made from `UEXTERNALDB(LOP=0)` in this instrumented package under Abaqus 2023. This does not show that `COMMON`/`SAVE`, UEXTERNALDB generally, threads, or MPI fail. The eight-element baseline remains untested.

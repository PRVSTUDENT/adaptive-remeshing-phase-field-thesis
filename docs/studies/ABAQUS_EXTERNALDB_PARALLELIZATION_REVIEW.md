# Abaqus ExternalDB Parallelization Review

Date: 2026-07-24
Status: P0 documentation review complete; no solver execution

## Research question

Can the current `UEXTERNALDB`–UEL–UMAT information-transfer architecture
execute reproducibly in thread, MPI, or hybrid mode, and what changes are
required to make its shared state safe?

## Mode distinction

| Mode | Configuration | State model | Principal concern |
|---|---|---|---|
| Serial | 1 process × 1 thread | one address space | reference |
| Threads | 1 MPI process × N threads | shared address space | concurrent access to shared arrays/files |
| MPI | N processes × 1 thread | separate address spaces | COMMON/global data are not automatically shared between ranks |
| Hybrid | N processes × M threads | separate rank state plus shared state inside each rank | both MPI ownership and thread races |

## Documentation result

Current SIMULIA documentation explicitly permits user subroutines in parallel
execution. It says shared resources such as COMMON blocks and files must be
guarded in thread-parallel mode. The thread-safety guidance provides mutexes
and Abaqus-managed global and thread-local arrays; it describes thread-local
arrays as a replacement for COMMON/SAVE workspaces. `UEXTERNALDB` is an
analysis/increment-boundary callback and can prepare history for other
subroutines, but the callback does not by itself make later element-level
reads and writes safe.

Distributed execution is a separate claim. Each MPI process has its own
address space. Data required across partitions need an explicit ownership and
communication design at a synchronization point; thread-safe global arrays do
not provide inter-process sharing.

Sources reviewed:

- [About Parallel Execution (2025)](https://docs.software.vt.edu/abaqusv2025/English/SIMACAEEXCRefMap/simaexc-c-parallelmodes.htm)
- [About User Subroutines and Utilities (2024)](https://docs.software.vt.edu/abaqusv2024/English/SIMACAEANLRefMap/simaanl-c-subroutineover.htm)
- [UEXTERNALDB (2024)](https://docs.software.vt.edu/abaqusv2024/English/SIMACAESUBRefMap/simasub-c-uexternaldb.htm)
- [Ensuring Thread Safety (2024)](https://docs.software.vt.edu/abaqusv2024/English/SIMACAESUBRefMap/simasub-c-getthreadid.htm)

## Abaqus 2022 qualification boundary

The project evidence identifies Abaqus 2022 as an installed/used target, but
the repository does not contain a frozen copy of its installed HTML
documentation. The public documentation search performed for P0 did not
return an accessible 2022 page for the relevant utilities. Therefore this
review does **not** claim a version-to-version semantic change. Before P3,
the exact 2022 interfaces (`GETRANK`, `GETTHREADID`, mutex calls and
`UEXTERNALDB`) must be checked against the cluster installation documentation
or by a compile-only/datacheck qualification under explicit authorization.

## Existing evidence and conclusion

D2C previously matched D2B exactly for the tested one-rank/four-thread tiny
case. That is evidence for that execution only, not proof of general thread
safety. The static P1 audit confirms mutable COMMON/SAVE/DATA state and file
operations. Existing code is therefore:

- serially characterized;
- exactly repeatable in one preserved tiny four-thread comparison;
- not generally qualified as thread-safe;
- not qualified for distributed MPI state exchange;
- not qualified for hybrid execution.

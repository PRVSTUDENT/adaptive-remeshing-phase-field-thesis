# FRACFIX UEL State Ingestion & Parallelization Note

**Task**: `F43STATE-M2-INGESTION-FIX-PREP1`  
**Date**: 2026-08-11  
**Author**: `gemini-antigravity`  
**Classification**: `technical_architecture_note`  

---

## 1. Executive Summary

This note addresses the supervisor's parallelization concerns regarding the Abaqus User Subroutine (UEL) implementation for the Mode-II phase-field fracture formulation (`FRACFIX`).

While Abaqus supports multi-threaded (thread-parallel) and MPI-distributed execution of user subroutines, mutable shared memory constructs—specifically Fortran `COMMON` blocks (`COMMON/KUSER/USRVAR`) and `SAVE` statements—introduce severe race conditions and non-deterministic memory corruptions under parallel execution.

The corrected state-ingestion architecture implemented in task `F43STATE-M2-INGESTION-FIX-PREP1` transitions state ownership from uninitialized shared Fortran `COMMON` memory to **Abaqus-managed `SVARS` and nodal degree-of-freedom (`U`) arrays**.

---

## 2. Shared Memory Resource Classification

For the corrected serial UEL implementation (`f42_mixed_uel.for`), the shared memory constructs are classified as follows:

| Construct | Classification | Thread Safety Risk | MPI Rank-Local Risk | Candidate Future Action |
| :--- | :--- | :--- | :--- | :--- |
| `COMMON/KUSER/USRVAR` | Shared Mutable (Serial Synchronized) | **HIGH** (Race condition across threads) | **HIGH** (Unshared memory across MPI ranks) | Replace with Abaqus-managed `SVARS` / `UEXTERNALDB` |
| `SAVE` statements | None (Zero `SAVE` statements in UEL) | **NONE** | **NONE** | Preserve zero `SAVE` policy |
| `DATA` statements | Read-Only static constants | **NONE** | **NONE** | Safe for parallel read |
| Fortran I/O (stdout unit 6) | Shared File Write (Bounded Diagnostic) | **MODERATE** (Interleaved diagnostic lines) | **MODERATE** (Rank-prefixed output) | Restrict diagnostic output to first call / master thread |

---

## 3. Current Serial-Safe Design vs. Parallel Risks

### Current Serial Design:
In single-CPU / serial execution, `COMMON/KUSER/USRVAR(N_CAPACITY, NSTV, 4)` acts as a shared memory table where Displacement UEL elements (JTYPE=2/4) write strain energy history $H$, and Phase UEL elements (JTYPE=1/3) read $H$ for driving force calculations.

### Thread Parallel Risk:
Under thread-parallel execution (`ncpus > 1`), multiple threads execute UEL calls simultaneously. If thread A executes JTYPE=1 while thread B executes JTYPE=2 for an overlapping element range without mutex synchronization, thread A reads stale or partially-written history $H$ from `USRVAR`, violating deterministic convergence.

### MPI Rank-Local Replication Risk:
Under MPI domain decomposition, element sets are partitioned across distinct process ranks. Memory in `COMMON/KUSER/USRVAR` is rank-local and not synchronized by Abaqus across MPI processes. When physical element $k$ (Phase UEL) resides on MPI Rank 0 and its paired element $k + N_{\text{phys}}$ (Displacement UEL) resides on MPI Rank 1, `USRVAR` reads across ranks fail silently, returning default $0.0$.

---

## 4. Candidate Future Abaqus-Managed Replacement

To achieve full thread-parallel and MPI qualification in future thesis phases, the UEL state architecture should be refactored as follows:

1. **Abaqus-Managed `SVARS` as Primary State**:
   Abaqus allocates, manages, and thread-synchronizes `SVARS(1..NSVARS)` per element.
   By storing history $H$ in `SVARS(1..4)` and phase $d$ in `SVARS(5..8)` (or nodal phase DOFs), state is encapsulated within the element instance managed directly by Abaqus.

2. **Nodal DOF Phase Coupling**:
   Phase field $d$ is represented as a solved nodal displacement DOF (DOF 1 on Phase UEL nodes). Abaqus handles global parallel assembly and solver distribution for all nodal DOFs across threads and MPI ranks natively.

3. **`UEXTERNALDB` Synchronization (if cross-element state is needed)**:
   For complex multi-field synchronization across distinct element layers, Abaqus `UEXTERNALDB` routines can participate in step/increment lifecycle initialization (`LOP=0..5`) using thread-safe `GETTHREADID` or rank-local memory structures.

---

## 5. Qualification Status

```text
serial_ingestion_fix_parallel_safe = NOT_PROVEN
```

The current task (`F43STATE-M2-INGESTION-FIX-PREP1`) proves **correct serial ingestion** on 1 CPU. Parallel thread-safety and MPI distribution remain unproven and will require explicit multi-CPU qualification before any parallel production deployment.

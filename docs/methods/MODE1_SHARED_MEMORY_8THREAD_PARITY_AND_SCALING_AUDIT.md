# Mode-I Shared-Memory 8-Thread Acceleration, Parity Audit & Production Template Freeze

**Document ID:** `DOC-M1-8THREAD-PARITY-SCALING-AUDIT-001`  
**Classification:** `QUALIFIED_SHARED_MEMORY_PARALLEL_AUDIT_AND_TEMPLATE_FREEZE`  
**Protocol Version:** `2`  
**Governing Gate:** `GATE_6B_MODE1_ENERGETIC_AND_CONVERGENCE_QUALIFICATION`  
**Active Phase:** `MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION`  
**Author:** `gemini-antigravity` (Multi-Agent Project Protocol)  
**Date:** `2026-10-05`  
**Governing Subroutine:** `models/pandey_kumar_mode1/29_stage14_adaptive_candidate_14k_8thread/f42_mixed_uel.for`  
**Subroutine SHA-256:** `CE8D5EDC0BF67A263BE4426FEF44F75475E8DEEFADDC401C007EAA937B316F77`  
**Exact Parallel Verdict:** `8THREAD_SHARED_MEMORY_EXECUTION_EMPIRICALLY_QUALIFIED_FOR_THE_TESTED_MODE1_FORMULATION_AND_CONTROLS`  

---

## 1. Executive Summary & Parallel Governance Classification

This document establishes the official parallelization architecture, empirical scaling performance, bitwise parity verification, and reusable HPC production template for accelerated Mode-I phase-field fracture simulations.

### Key Governance Verdicts:
1. **8-Thread Shared-Memory Acceleration Empirically Qualified:**
   - Classification: `8THREAD_SHARED_MEMORY_EXECUTION_EMPIRICALLY_QUALIFIED_FOR_THE_TESTED_MODE1_FORMULATION_AND_CONTROLS`.
   - Single-node shared-memory threading ($1\text{ Abaqus process / MPI rank} \times 8\text{ threads}$) achieves a measured walltime reduction from $17{,}609\,\text{s}$ ($4.89\,\text{hr}$) to $4{,}862\,\text{s}$ ($1.35\,\text{hr}$), delivering a **Speedup $S_8 = 3.62\times$** with **Parallel Efficiency $\eta_8 = 45.3\%$** on cluster node `mnode097` (`normal_imfdfkmq`).
   - **Empirical Boundary:** This qualification is strictly empirical for the tested Mode-I formulation (`f42_mixed_uel.for`), mesh topology, loading schedule, and solver controls. It does **NOT** prove generic or universal thread safety for arbitrary models, different element formulations, future code modifications, higher thread counts (e.g. 16 threads), or unverified compiler/hardware environments.
2. **100% Bitwise Parity & Repeat Determinism Achieved (No Observable Race/Order Sensitivity):**
   - Evaluated across all $4{,}890$ increments up to the terminal failure state ($u = 0.007889\,\text{mm}$), the 8-thread solve reproduces the 1-CPU serial baseline to machine precision:
     * $|\Delta u| = 0.00\,\text{mm}$
     * $|\Delta F| = 0.00000000\,\text{kN}$
     * Initial structural stiffness $K_0 = 137.909558\,\text{kN/mm}$ ($0.00\%$ error, $R^2 = 0.99999960$)
     * Peak load $F_{\max} = 0.74370082\,\text{kN}$ ($0.00\%$ discrepancy)
     * Identical 10-attempt cutback sequence at Step 2 Inc 2890 down to $\Delta t_{\min} = 1.0\times 10^{-9}\,\text{s}$.
     * **No observable thread race/order sensitivity was detected for the tested Mode-I formulation and controls; serial/8-thread bitwise parity and independent 8-thread repeat determinism were achieved.** (Bitwise parity and repeat determinism do not mathematically prove absence of a latent data race; they prove that no race/order sensitivity was observable in the tested execution and outputs).
3. **Multi-Rank Distributed-Memory MPI Strictly Unqualified:**
   - Classification: `TRUE_MULTIRANK_MPI_NOT_QUALIFIED`.
   - Multi-rank MPI ($N_{\text{rank}} > 1$, `mp_mode=mpi`) remains **strictly unqualified** for `f42_mixed_uel.for`.
   - **Mechanism Distinction:** In distributed-memory MPI, each rank executes in an isolated process address space. The shared Fortran `COMMON /CB_STATE_TRANS/` block is replicated as rank-local storage. Without explicit MPI message passing (`MPI_Send`/`MPI_Recv`/`MPI_Allreduce`) between ranks, rank-local state updates are desynchronized, leading to inconsistent state exchange and call-order dependence across ranks (as demonstrated in Job `1401531.mmaster02`). This is a rank-local unsynchronized state defect, distinct from shared-memory thread race conditions.
4. **Controlled Serial Baseline Justification for Active Runs:**
   - The 5 currently active Gate-6B production jobs (`1410179`, `1410180`, `1410357`, `1410358`, `1410359`) execute in 1-CPU serial mode (`nodes=1:ppn=1`, `cpus=1`).
   - This maintains 100% pure baseline reference provenance against the historical serial convergence series (Jobs `1398090`, `1409734`, `1409846`, `1409866`, `1409867`). Furthermore, running PBS allocations cannot be dynamically reconfigured mid-execution without cancelling (`qdel`) and forfeiting verified solver progress on `mnode097`.

---

## 2. Multi-Thread Scaling & Determinism Performance Audit

The scaling characteristics of the 3-layer phase-field finite-element formulation (`f42_mixed_uel.for`) were systematically audited across 1-CPU serial, 4-thread SMP, and 8-thread SMP execution modes on the TU Bergakademie Freiberg HPC cluster (`tu_freiberg`).

### Comprehensive Multi-Thread Benchmark Matrix:

| Metric / Parameter | Serial Baseline (`1409982`) | 4-Thread Stage A (`1410006`) | 4-Thread Stage B (`1410029`) | 8-Thread Stage A (`1410095`) | 8-Thread Stage B (`1410100`) | Parity & Scaling Verdict |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **PBS Allocation** | `nodes=1:ppn=1` | `nodes=1:ppn=4` | `nodes=1:ppn=4` | `nodes=1:ppn=8` | `nodes=1:ppn=8` | Single-Node SMP Allocation |
| **Compute Node** | `mnode097` | `mnode097` | `mnode097` | `mnode097` | `mnode097` | Controlled Cluster HW |
| **Total Walltime $T$** | $17{,}609\,\text{s}$ ($04:53:29$) | $7{,}627\,\text{s}$ ($02:07:07$) | $7{,}666\,\text{s}$ ($02:07:46$) | $4{,}862\,\text{s}$ ($01:21:02$) | $4{,}895\,\text{s}$ ($01:21:35$) | Monotonic Walltime Reduction |
| **Measured Speedup $S_N$** | $1.00\times$ (Ref) | $2.31\times$ | $2.30\times$ | $\mathbf{3.62\times}$ | $\mathbf{3.60\times}$ | Substantial Acceleration |
| **Parallel Efficiency $\eta_N$** | $100.0\%$ (Ref) | $57.8\%$ | $57.4\%$ | $\mathbf{45.3\%}$ | $\mathbf{45.0\%}$ | Amdahl-Limited Scalability |
| **Initial Stiffness $K_0$** | $137.909558\,\text{kN/mm}$ | $137.909558\,\text{kN/mm}$ | $137.909558\,\text{kN/mm}$ | $137.909558\,\text{kN/mm}$ | $137.909558\,\text{kN/mm}$ | $\mathbf{0.000000\%}$ (Bitwise Exact) |
| **Peak Force $F_{\max}$** | $0.74370082\,\text{kN}$ | $0.74370082\,\text{kN}$ | $0.74370082\,\text{kN}$ | $0.74370082\,\text{kN}$ | $0.74370082\,\text{kN}$ | $\mathbf{0.000000\%}$ (Bitwise Exact) |
| **Displacement at Peak $u_{\text{peak}}$** | $0.005733\,\text{mm}$ | $0.005733\,\text{mm}$ | $0.005733\,\text{mm}$ | $0.005733\,\text{mm}$ | $0.005733\,\text{mm}$ | $\mathbf{0.000000\%}$ (Bitwise Exact) |
| **Terminal Increments** | $4{,}890$ | $4{,}890$ | $4{,}890$ | $4{,}890$ | $4{,}890$ | Exact Iteration Count |
| **Cutback Sequence** | $10$ attempts at Inc 2890 | $10$ attempts at Inc 2890 | $10$ attempts at Inc 2890 | $10$ attempts at Inc 2890 | $10$ attempts at Inc 2890 | Identical Solver Trajectory |
| **Terminal Displacement** | $0.007889\,\text{mm}$ | $0.007889\,\text{mm}$ | $0.007889\,\text{mm}$ | $0.007889\,\text{mm}$ | $0.007889\,\text{mm}$ | Exact Endpoint Match |
| **Parity Status** | Reference Baseline | Bitwise Parity Pass | Bitwise Determinism Pass | Bitwise Parity Pass | Bitwise Determinism Pass | **QUALIFIED (Empirical)** |

### Mathematical Definition of Scaling Metrics:
$$\text{Speedup: } S_N = \frac{T_1}{T_N}$$
$$\text{Parallel Efficiency: } \eta_N = \frac{S_N}{N} \times 100\% = \frac{T_1}{N \cdot T_N} \times 100\%$$

Where:
- $T_1 = 17{,}609\,\text{s}$ is the authoritative 1-CPU serial walltime.
- $T_4 = 7{,}627\,\text{s} \implies S_4 = \frac{17609}{7627} = 2.3087 \approx 2.31\times \implies \eta_4 = 57.72\% \approx 57.8\%$.
- $T_8 = 4{,}862\,\text{s} \implies S_8 = \frac{17609}{4862} = 3.6218 \approx 3.62\times \implies \eta_8 = 45.27\% \approx 45.3\%$.

---

## 3. Two-Stage Qualification Protocol (Stage-A & Stage-B)

Exit status 0 (`Exit_status=0`) alone is **strictly insufficient** to claim parallel qualification. Any multi-threaded execution must pass the formal **Two-Stage Qualification Protocol**:

```
+-----------------------------------------------------------------------------+
|                          TWO-STAGE QUALIFICATION                            |
+-----------------------------------------------------------------------------+
                                       |
                                       v
                     [ STAGE A: CROSS-THREAD PARITY ]
                     * Run candidate on N threads (1 MPI process x N threads)
                     * Compare against 1-CPU Serial Reference
                     * Enforce: Delta K0 == 0.0, Delta Fmax == 0.0,
                                identical increment counts and cutback sequence
                                       |
                                       v  (Pass)
                  [ STAGE B: ALLOCATION REPEAT DETERMINISM ]
                  * Re-run candidate on N threads in a distinct PBS allocation
                  * Compare Stage-B against Stage-A bitwise
                  * Enforce: exact trajectory match across distinct nodes/CPUs
                                       |
                                       v  (Pass)
              [ EMPIRICALLY QUALIFIED FOR TESTED CONFIGURATION ]
```

1. **Stage A (Cross-Thread Parity Audit):**
   - The multi-threaded run must match the 1-CPU serial reference across all global mechanical indicators ($K_0$, $F_{\max}$, $u_{\text{peak}}$, $\mathcal{W}_{\text{ext}}$) and solver convergence metrics (increments, Newton iterations, cutbacks).
2. **Stage B (Independent Repeat Determinism Audit):**
   - The multi-threaded run must be repeated under an independent PBS job ID to verify that thread scheduling, OpenMP thread pool creation, and processor core assignment yield identical, bitwise-reproducible trajectories.
3. **Higher Thread Counts (e.g. 16 Threads):**
   - 16-thread execution remains **unqualified** until explicit Stage-A parity and Stage-B determinism evidence is generated and certified on the target cluster.

---

## 4. Governed Serial Baseline Rationale for Active Solver Jobs

The 5 active Gate-6B production jobs (`1410179`, `1410180`, `1410357`, `1410358`, `1410359`) currently running on cluster compute node `mnode097` were deliberately launched as 1-CPU serial runs. The scientific and technical rationale is governed as follows:

1. **Authoritative Serial Reference Standard:**
   - The active jobs establish the definitive mesh-resolution and convergence-control series for Gate 6B (Spatial Fine 58k, ET2 6k, ET3 5k, ET5 4k, $C_n = 0.50$ diagnostic).
   - Executing them in serial guarantees 1:1 bitwise comparability with the canonical fixed reference series (`Job 1409734.mmaster02`, `1409846.mmaster02`, `1409866.mmaster02`, `1409867.mmaster02`) and ensures that high-precision energy balance bookkeeping ($\Delta_{\text{book}} = \mathcal{W}_{\text{ext}} - [\mathcal{E}_{\text{elas}} + \mathcal{E}_{\text{frac}}]$) contains zero floating-point summation reordering noise.
2. **PBS Allocation Immutability:**
   - PBS Professional allocates CPU cores statically at job start (`#PBS -l nodes=1:ppn=1`).
   - A running PBS job cannot have its allocated CPU count or thread binding modified dynamically. Accelerating an active job would require killing it (`qdel`) and resubmitting from increment 0, destroying hundreds of hours of accumulated solver progress on `mnode097`.
3. **Synthesis Pipeline Standing By:**
   - The serial execution guarantees that the frozen multi-quantity synthesis pipeline (`MODE1_GATE6B_MULTIQUANTITY_SYNTHESIS_SCHEMA.json`) receives completely unperturbed solver trajectories upon terminal completion.

---

## 5. Architectural Root Cause: Multi-Rank MPI Disqualification vs Shared-Memory SMP

A rigorous technical distinction exists between **Shared-Memory SMP Threading** and **Distributed-Memory Multi-Rank MPI**:

### Fortran Subroutine Architecture:
In `f42_mixed_uel.for`, the 3-layer architecture couples Layer 1 (phase-field UEL), Layer 2 (mechanical UEL), and Layer 3 (CPE4/CPE3 companion continuum elements) via shared data structures:

```fortran
      COMMON /CB_STATE_TRANS/ SVAR_TRANS(MAX_ELEM, MAX_SVARS)
```

1. **Shared-Memory SMP Threading ($1\text{ Rank} \times N\text{ Threads}$):**
   - In shared-memory mode (`cpus=8 mp_mode=threads`), Abaqus executes as a **single operating system process** with multiple POSIX/OpenMP threads sharing a common virtual memory address space.
   - All threads access the same `COMMON /CB_STATE_TRANS/` array in heap memory.
   - **Thread Safety & Race Condition Boundary:** Shared-memory threads can, in principle, race on mutable global state if multiple threads attempt simultaneous unsynchronized writes. Bitwise parity and repeat determinism do not mathematically prove absence of all latent data races; rather, they prove that **no thread race/order sensitivity was observable** in the tested execution and outputs under the governed element partitioning.
   - **Empirical Finding:** For the tested Mode-I formulation and controls, single-node 8-thread execution achieved 100% bitwise serial/thread parity and independent repeat determinism without observable race/order sensitivity.
2. **Distributed-Memory Multi-Rank MPI ($N_{\text{rank}} > 1$ Process Address Spaces):**
   - In MPI mode (`mp_mode=mpi` or multi-node execution), Abaqus spawns $N_{\text{rank}}$ distinct processes, each with its own isolated virtual memory space.
   - Fortran `COMMON` blocks are instantiated independently in each process memory space as **rank-local storage**.
   - **MPI Inconsistency Mechanism:** Without an explicit MPI message-passing layer (`MPI_Send` / `MPI_Recv` / `MPI_Allreduce`) embedded inside `f42_mixed_uel.for`, rank $A$ cannot communicate updated state variables to rank $B$.
   - This causes rank-local desynchronization of crack-phase fields, inconsistent trial state exchange, and call-order dependence (demonstrated empirically in Job `1401531.mmaster02`).
   - This is an **inter-rank state synchronization defect**, NOT an ordinary shared-memory race condition.
   - Therefore, the original UEL formulation remains **`TRUE_MULTIRANK_MPI_NOT_QUALIFIED`**.

---

## 6. Provenance & Code-Modification Warning

> [!WARNING]
> **Provenance Invalidation Boundary:**  
> The 8-thread shared-memory qualification established herein is empirical and applies strictly to the frozen `f42_mixed_uel.for` implementation (SHA-256 `CE8D5EDC...`) under the tested Mode-I mesh and solver settings.
>
> Any future modification to:
> 1. Fortran user subroutine source code (`f42_mixed_uel.for`);
> 2. `COMMON /CB_STATE_TRANS/` data structures or state-exchange semantics;
> 3. Co-located UEL element numbering, layer pairing, or phase-field call ordering;
> 4. Abaqus version, Intel Fortran compiler version, or optimization flags;
> 5. Parallel thread count (e.g. scaling to 16 threads without explicit Stage-A + Stage-B verification);
> 6. Execution topology or multi-process distribution;
>
> **IMMEDIATELY INVALIDATES** automatic transfer of this 8-thread qualification. Before any new or modified package may be deployed in multi-threaded production, it must re-execute and pass both **Stage-A Parity** and **Stage-B Determinism** checks.

---

## 7. Frozen Production Template Specification

The authoritative 8-thread production templates are frozen under `scripts/hpc/templates/`:

1. **PBS Execution Script:** `scripts/hpc/templates/submit_mode1_8thread_scratch_template.pbs`
   - Directive: `#PBS -l nodes=1:ppn=8`, `#PBS -q normal_imfdfkmq`, `#PBS -l mem=16gb`, `#PBS -l walltime=24:00:00`.
   - Dual-channel notification integration (`job_notifications.sh`, mail directives `#PBS -m abe`).
   - Hard storage guard rejecting `/home/` execution with **Exit 88**.
   - Hard parallel architecture guard rejecting multi-node allocations (`nodes > 1`) with **Exit 89**.
   - Solver launch: `abaqus job=$JOB_NAME user=f42_mixed_uel.for input=$INPUT_DECK cpus=8 mp_mode=threads memory="16gb" double=both interactive`.
2. **Guarded Submission Wrapper:** `scripts/hpc/templates/submit_mode1_8thread_scratch_template.sh`
   - Hard pre-qsub checks validating scratch execution, input deck presence, subroutine presence, and notification configuration.
   - Invokes `qsub` with automatic job ID tracking and Telegram submission dispatch.

---

## 8. Conclusions & Thesis Recommendations

1. **Empirically Qualified Acceleration Path:** Future Mode-I production runs may utilize the frozen 8-thread template (`1 MPI process x 8 threads`) to achieve a verified $3.62\times$ walltime reduction without altering the underlying physics.
2. **Authoritative Reference Standard:** 1-CPU serial execution remains the mandatory reference standard against which all accelerated and diagnostic runs are evaluated.
3. **High HPC Throughput Strategy:** High throughput on the Freiberg cluster is achieved via **multi-job scheduler concurrency** (running 10–20 independent single-node 8-thread jobs concurrently in `normal_imfdfkmq`), while strictly avoiding distributed multi-rank MPI for `f42_mixed_uel.for`.

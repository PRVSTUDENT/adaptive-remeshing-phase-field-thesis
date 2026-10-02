# Stage P: Parallelization Scope & Architecture Decision Record

## Status: ADOPTED (Unified 12-DOF Architecture Fully MPI-Qualified)

### Context & Problem Statement
Abaqus multi-core simulations on cluster nodes can operate either via OpenMP multi-threading (single OS process) or domain decomposition MPI (multiple OS processes). The legacy dual-element phase-field UEL formulation (`f42_mixed_uel.for`) shared damage and history state across co-located finite elements via global Fortran `COMMON` blocks. Under multi-process MPI domain decomposition, process-private virtual memory spaces prevent state synchronization across partition boundaries, leading to non-physical stiffness over-prediction, solver divergence, and severe cutbacks (proven by Job `1401531.mmaster02`).

### Decision & Resolution
1. **Disqualification of Dual-Element Architecture for Multi-Rank MPI**:
   The dual-element architecture with Fortran `COMMON` blocks is permanently disqualified for multi-rank distributed-memory execution (`TRUE_MPI_PARITY_FAIL`).
2. **Adoption of Unified 12-DOF Architecture (`f42_compat_unified_uel.for`)**:
   Displacements ($u_x, u_y$) and phase field ($d$) are consolidated into a single 12-DOF quadrilateral element.
   - All state variables ($H_{\max, \text{kpt}}, d_{\text{avg}}$) are managed in Abaqus-native `SVARS(1..8)`.
   - Mechanical degradation uses element-averaged phase field $d_{\text{avg}} = \frac{1}{4}\sum_{i=1}^4 d_i$, preserving exact algorithmic equivalence with the qualified serial reference.
   - Transactional rollback on solver cutbacks is handled automatically by Abaqus memory management.

### Verification Evidence
1. **Element-Level Parity**: Prescribed element tests across 4 physical damage states demonstrated machine precision agreement ($< 10^{-15}$ / 0.000E+00) for all residual vectors and tangent stiffness blocks.
2. **Serial Equivalence**: PBS Job `1401533.mmaster02` verified agreement within $\le 0.007\%$ in elastic loading and within $0.37\%$ at peak force against the dual-element reference.
3. **True Multi-Rank MPI Qualification**: PBS Job `1401534.mmaster02` (`cpus=2 mp_mode=mpi threads_per_mpi_process=1`) demonstrated **0.000000% difference vs serial baseline** across all 19 loading increments to peak load with identical iteration counts.

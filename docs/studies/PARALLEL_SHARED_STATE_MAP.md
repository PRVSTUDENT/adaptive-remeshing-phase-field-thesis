# Parallel Shared State Map & MPI Parallelization Architecture

## 1. Executive Summary & Parallelization Registry

This document records the qualification status of phase-field fracture formulations under shared-memory and distributed-memory (MPI) parallel architectures in Abaqus/Standard.

### Authoritative HPC Execution Record

| PBS Job ID | Target Model / Formulation | Parallel Configuration | Formal Classification | Causal Status |
| :--- | :--- | :--- | :--- | :--- |
| **`1401530.mmaster02`** | Dual UEL (`f42_mixed_uel.for`) | 1 MPI rank × 2 threads | `THREAD_PARITY_PASS / TRUE_MPI_NOT_TESTED` | Single domain; stopped at small displacement $u=0.001\text{ mm}$ ($d \approx 0$). |
| **`1401531.mmaster02`** | Dual UEL (`f42_mixed_uel.for`) | 2 MPI ranks × 1 thread | `TRUE_MPI_PARITY_FAIL / DUAL_ELEMENT_MPI_UNQUALIFIED` | 2 distributed memory domains. Diverged upon damage evolution ($u \ge 0.002\text{ mm}$) due to rank-private `COMMON /CB_STATE_TRANS/` blocks. |
| **`1401532.mmaster02`** | Unified UEL (`f42_unified_mpi_uel.for`) | 1 CPU (Serial) | `SERIAL_REDESIGN_PARITY_FAIL / FORMULATION_CHANGED` | Formulation change: Gauss-point local degradation vs element-average degradation in dual reference produced ~4% force divergence. |
| **`1401533.mmaster02`** | Compat Unified (`f42_compat_unified_uel.for`) | 1 CPU (Serial) | `SERIAL_COMPATIBILITY_QUALIFIED` | Exact algorithmic compatibility candidate ($d_{\text{avg}}$ degradation, Abaqus `SVARS`). Parity within $\le 0.007\%$ across early loading and $\le 0.37\%$ at peak. |
| **`1401534.mmaster02`** | Compat Unified (`f42_compat_unified_uel.for`) | 2 MPI ranks × 1 thread | `TRUE_MPI_PARITY_PASS / UNIFIED_12DOF_MPI_QUALIFIED` | Genuine 2-domain distributed-memory execution. **0.000000% difference vs serial baseline across all 19 increments to peak load.** |

---

## 2. Multi-Rank MPI Disqualification of Dual-Element Architecture

The dual-element architecture (`f42_mixed_uel.for`) uses two co-located finite elements per mesh cell:
1. Phase-field UEL element (Active DOF 3).
2. Mechanical UEL element (Active DOFs 1, 2).

State exchange between co-located finite elements was implemented via process-level Fortran `COMMON /CB_STATE_TRANS/` blocks. Under Abaqus MPI domain decomposition:
- Each MPI process operates in a private virtual address space.
- Phase-field updates on Domain 1 are not synchronized to co-located mechanical elements assigned to Domain 2.
- Mechanical elements on Domain 2 read uninitialized/stale damage ($d \equiv 0$), leading to non-physical stiffness over-prediction, residual imbalance across partition boundaries, and divergence.

---

## 3. Verified Unified 12-DOF Architecture (`f42_compat_unified_uel.for`)

The qualified MPI-safe architecture consolidates displacements and phase field into a single 12-DOF quadrilateral element:
- **Nodal DOFs**: $u_x$ (DOF 1), $u_y$ (DOF 2), $d$ (DOF 3).
- **Abaqus-Managed State**: History driving energy $H_{\max}$ is stored in per-element `SVARS(1..4)`. Abaqus automatically manages `SVARS` across MPI partition boundaries and rolls back state on cutbacks without global Fortran arrays.
- **Formulation Compatibility**: Uses element-averaged phase field $d_{\text{avg}} = \frac{1}{4}\sum_{i=1}^4 d_i$ for mechanical degradation, ensuring exact equation-level and numerical parity with the qualified serial baseline.
- **Verification**: Evaluated across 4 distinct physical damage states at element level (parity to $< 10^{-15}$ / 0.0) and across all 19 increments in true 2-domain MPI execution (exact 0.000000% parity vs serial).

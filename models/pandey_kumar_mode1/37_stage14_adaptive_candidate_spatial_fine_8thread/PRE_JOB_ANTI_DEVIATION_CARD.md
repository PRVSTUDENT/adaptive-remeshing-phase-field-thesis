# Pre-Job Anti-Deviation Card: Stage-14 Spatial Fine 8-Thread Shared-Memory Candidate (Package 37)

**Job Name:** `PK_M1_14AM_8T`  
**Target Discretization:** Spatial Fine Adaptive Candidate ($57{,}929$ FE, $57{,}491$ FE nodes)  
**Governing Subroutine:** `f42_mixed_uel.for` (SHA-256 `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)  
**Input Deck:** `PK_MODE1_STAGE14_ADAPT_SPATIAL_FINE_FRACTURE.inp` (SHA-256 `537C8C6617945AFD66E135C1DF4E2C34211F47FBEEEC44E4C145A8551CC1EEFD`)  
**Execution Mode:** Shared-Memory SMP ($1\text{ MPI rank} \times 8\text{ threads}$, `cpus=8`, `mp_mode=threads`)  
**Allocation:** `nodes=1:ppn=8`, `mem=16gb`, `walltime=48:00:00`, `queue=entry_imfdfkmq`  

---

### Pre-Flight Anti-Deviation Contract:
1. **Proposal Task Alignment:** Advances Task 3 (Convergence & Benchmark Reference) and Task 4 (Native Remeshing Evaluation).
2. **Active Master Gate:** Gate 6B (Mode-I Energetic & Convergence Qualification).
3. **Scientific Purpose / Hypothesis:**
   - Evaluates the spatial convergence behavior of the highly refined ($57{,}929$ FE) adaptive discretization across both Step 1 and Step 2 ($u = 0 \to 0.010\,\text{mm}$) to resolve whether post-peak energetic response ($\Delta_{\text{book}}$) decreases toward the continuum limit as the refinement corridor resolution increases ($h/l_0 \to 0.074$).
   - Solves the 24-hour walltime starvation observed in serial Job `1410179` by utilizing the empirically qualified 8-thread shared-memory architecture ($S_8 \approx 3.62\times$, expected runtime ~11 h vs ~39 h serial).
4. **Single Intended Modification from Serial Twin (`1410179`):**
   - Execution topology: `cpus=1` $\to$ `cpus=8 mp_mode=threads`.
   - Requested PBS walltime: `24:00:00` $\to$ `48:00:00`.
   - All physical parameters, mesh topology, Fortran UEL source, boundary conditions, and solver controls remain 100% frozen.
5. **Frozen Boundary Conditions & Mechanics:**
   - Plate geometry: $1\,\text{mm} \times 1\,\text{mm}$ with $a_0 = 0.5\,\text{mm}$ sharp seam.
   - Material parameters: $E = 210\,\text{kN/mm}^2$, $\nu = 0.3$, $G_c = 2.7\times 10^{-3}\,\text{kN/mm}$, $l_0 = 0.0075\,\text{mm}$.
   - Dual-channel notifications active (`#PBS -m abe`, `notify_submitted`, `notify_start`, terminal trap).
6. **Pre-Declared Acceptance Criteria:**
   - Clean convergence through Step 2 ($u = 0.010\,\text{mm}$) with 0 severe discontinuity iterations.
   - Initial structural stiffness: $K_0 \in [137.90, 138.00]\,\text{kN/mm}$ (within $\pm 0.05\%$ of canonical reference).
   - Peak load: $F_{\max} \in [0.74, 0.76]\,\text{kN}$.
   - Bitwise parity and determinism consistent with established 8-thread qualification standards.

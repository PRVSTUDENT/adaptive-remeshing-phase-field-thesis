# Pre-Job Anti-Deviation Card: Package 44 (M1_MB_DTMAX_8T)

**Job Name:** `M1_MB_DTMAX_8T`  
**Package:** `44_method_b_temporal_refinement`  
**Parent Package:** `40_method_b_corrected_propagation_14k`  
**Creation Date:** 2026-10-15T14:00:00+02:00  

---

### Mandatory Mental Checklist & Verification Contract

- [x] **Which original proposal task does this job advance?**
  Proposal Task 3 (Mode-I Multifaceted Convergence & Method B Load Partitioning Evaluation).
- [x] **Which active gate does it close?**
  Gate 6B (Temporal Convergence & Method B Propagation Mechanics).
- [x] **What is the scientific question / hypothesis?**
  Does halving the maximum time increment in Step 2 from $\Delta t_{\max} = 2.0\times 10^{-4}$ to $1.0\times 10^{-4}$ (reducing displacement increment from $2.0\,\mu\text{m}$ to $1.0\,\mu\text{m}$ during crack propagation) measurably alter crack localization, post-peak softening, external work, or minimum-increment termination at $u = 0.007889\,\text{mm}$?
- [x] **What is the single intended change from previous qualified case?**
  Step 2 `*STATIC` line: `dt_max` reduced from `2.0E-4` to `1.0E-4` (and initial increment set to `1.0E-4`, `INC=12000`). All other parameters frozen.
- [x] **What must remain frozen?**
  * Specimen geometry: $[0, 1]\times[0, 1]\,\text{mm}^2$, initial sharp seam $a_0 = 0.5\,\text{mm}$ at $y = 0.5\,\text{mm}$.
  * Mesh: 14,483 finite elements (14,357 CPE4 + 126 CPE3, 43,449 records across 3 layers), identical nodes and connectivity.
  * Boundary conditions: bottom roller ($u_y=0$, pinned corner $u_x=0$), top tensile displacement ($u_y$ ramp).
  * Material parameters: $E = 210\,\text{GPa}$, $\nu = 0.3$, $G_c = 2.7\,\text{N/mm}$, $l_0 = 0.0075\,\text{mm}$.
  * User subroutine: production Fortran UEL `f42_mixed_uel.for` (SHA-256 `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
  * Execution architecture: Single-rank shared-memory SMP with 8 threads (`cpus=8 mp_mode=threads memory=24gb`).
- [x] **Pre-declared acceptance criteria:**
  1. $K_0 = 137.9096 \pm 0.05\,\text{kN/mm}$ (Step 1 elastic stiffness identical to Package 40).
  2. $F_{\max} = 0.7437 \pm 0.0005\,\text{kN}$ at $u = 0.005733 \pm 0.00005\,\text{mm}$.
  3. Matched-horizon external work $W_{\text{ext}}$ within $0.5\%$ of $2.2674\,\text{mJ}$.
  4. Compare termination increment and attained displacement against Jobs 1412465, 1412873, 1413022.
- [x] **Dual-channel notification contract:**
  PBS directives `#PBS -m abe -M pr21vyci@mailserver.tu-freiberg.de` and `job_notifications.sh` traps installed.
- [x] **Authorization boundary:**
  Explicitly approved under active Mode-I batch and continuous execution policy; 8-thread SMP qualified; Gate 6C strictly preserved on hold.

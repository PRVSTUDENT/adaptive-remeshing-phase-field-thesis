# Pre-Job Anti-Deviation Card: Package 45 (Method B Temporal Refinement Serial Parity Control)

**Date:** 2026-10-15T14:20:00+02:00  
**Agent:** `gemini-antigravity`  
**Package Directory:** `models/pandey_kumar_mode1/45_method_b_temporal_refinement_serial_parity/`  
**Target Cluster Directory:** `/scratch9/pr21vyci/runs/mode1_method_b_temporal_refinement_serial/`  
**PBS Job Name:** `M1_MB_DTMAX_1C`  

---

### [X] 1. Original Proposal Task
- **Proposal Task:** Proposal Task 3 (Multifaceted Mode-I Benchmark Convergence and Parity Verification).

### [X] 2. Active Gate Alignment
- **Active Gate:** Gate 6B (Mode-I Energetic and Convergence Qualification, specifically Stage-A Serial/Thread Parity Qualification).

### [X] 3. Scientific Question & Hypothesis
- **Hypothesis:** Does the Package 44 8-thread shared-memory SMP execution (Job `1413278.mmaster02`) reproduce the identical 1-CPU serial solution (Job `M1_MB_DTMAX_1C`) across the common loading horizon?
- **Scientific Significance:** Before interpreting any differences between Package 40 ($dt_{\max} = 2.0\times 10^{-4}$) and Package 44 ($dt_{\max} = 1.0\times 10^{-4}$) as physical temporal-discretization phenomena, Stage-A serial/thread parity must certify that multi-threading did not introduce race conditions or numerical divergence into the mutable COMMON block of `f42_mixed_uel.for`.

### [X] 4. Single Intended Change
- **Single Intended Change:** Execution configuration changed from 8 shared-memory threads (`cpus=8 mp_mode=threads`) to 1-CPU serial (`cpus=1 mp_mode=threads`).
- **All Else Frozen:**
  - Mesh: 14,483 finite elements, 14,757 nodes (identical).
  - Material parameters: $E = 210\,\text{GPa}$, $\nu = 0.3$, $G_c = 2.7\,\text{N/mm}$, $l_0 = 7.5\,\mu\text{m}$ (identical).
  - Step 1: $\Delta t_{\max} = 5.0\times 10^{-4}$, $u = 0.0050\,\text{mm}$ (identical).
  - Step 2: $\Delta t_{\max} = 1.0\times 10^{-4}$, $\Delta t_{\min} = 1.0\times 10^{-9}$, $u = 0.0100\,\text{mm}$, `INC=12000` (identical).
  - Subroutine: `f42_mixed_uel.for` frozen production source (identical).

### [X] 5. What Must Remain Frozen
- Production Fortran UEL SHA-256: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`.
- Input deck SHA-256: `CB596BD91CA45F4B51111158EAA56523A01888471F8FF54EE37F40A306387B9C`.

### [X] 6. Primary Outputs and Pre-Declared Acceptance Criteria
- **Acceptance Criteria for Serial/Thread Parity:**
  1. Initial stiffness $K_0$: within $0.05\%$ between 1-CPU and 8-thread.
  2. Peak reaction force $F_{\max}$: within $0.1\%$ between 1-CPU and 8-thread.
  3. Peak displacement $u(F_{\max})$: within $0.1\%$ between 1-CPU and 8-thread.
  4. Force-displacement curve: bitwise or near-identical profile over the common converged domain.
  5. Increment count and cutback location: identical or minimal divergence prior to terminal state.
  6. Global energies: $E_{\text{elas}}$, $E_{\text{frac}}$, $W_{\text{ext}}$ within $0.1\%$.

### [X] 7. If Result is Unexpected
- Smallest isolated diagnostic: inspect increment-by-increment `.sta` and `.msg` divergence points to identify thread-scheduling vs physical-bifurcation sensitivity.

### [X] 8. Capacity Justification
- Independent scientific validation requirement under governance policy (Stage-A parity is mandatory for parallel execution qualification).

### [X] 9. Technical vs Scientific Acceptance
- Exit 0 is purely technical completion; scientific acceptance requires meeting all 6 pre-declared parity metrics.

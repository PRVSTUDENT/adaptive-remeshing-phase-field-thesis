# Task F1716: Five-Hole Phase-Field Failure Analysis and Governed Repair Plan

Protocol Version: 2  
Date: 11 November 2026  
Status: ACTIVE / QUALIFICATION  
Lead Agent: Gemini Antigravity (Pair Programming with Codex)  
Governing Task: `/goal F1716 — FIX FIVE-HOLE PHASE-FIELD FAILURE, VALIDATE PHYSICAL LOADING, AND COMPLETE MULTI-CORE HPC PRODUCTION SIMULATION`  
Predecessor Job: PBS Job `1422257.mmaster02` (`M1_PK_F1714_JOB2_ADAPTED`)  

---

## 1. Executive Summary

In Task F1714, the five-hole benchmark adapted mesh (13,034 physical CPE4/CPE3 elements, 39,102 layered elements) was submitted to the TU Freiberg HPC cluster as PBS Job `1422257.mmaster02`. The job completed 6,051 increments (2,000 increments of Step 1 to $u_y = 0.005\,\text{mm}$ and 4,051 increments of Step 2 to $u_y = 0.009051\,\text{mm}$) before exhausting its 8-hour walltime limit (Exit status: -29).

A rigorous post-mortem forensic audit revealed that although the solver reported smooth 1-iteration convergence with zero cutbacks, the simulation experienced an unphysical numerical failure:
1. Reference node 13276 displacement ($U_2$) evaluated to `NaN` in all output frames.
2. Visualizer state variables (`SDV1` through `SDV20`) evaluated to `NaN` across all 51,194 integration points.
3. The mesh experienced zero strain and zero internal forces (`THERE IS ZERO FORCE EVERYWHERE` in `.msg`).
4. Reaction forces on node 13276 were unallocated (`NaN`), producing zero physical crack propagation.
5. `uel_energy_balance.csv` contained `NaN` across all energetic columns.

This document establishes the exact, reproducible root-cause mechanisms responsible for this numerical failure and details the multi-level repair strategy required prior to any production execution.

---

## 2. Forensic Investigation & Root-Cause Mechanisms

### 2.1 Mechanical/Visualizer UEL-UMAT Architectural Separation

The Abaqus 3-layer phase-field architecture operates via three distinct element layers sharing identical nodal coordinates:
- **Layer 1 (Phase-Field UEL, JTYPE 1/3):** Solves the phase-field Helmholtz/Euler-Lagrange equation for damage $d$ ($U_1/U_3$).
- **Layer 2 (Mechanical UEL, JTYPE 2/4):** Solves the momentum balance equation for displacements $u_x, u_y$ ($U_2/U_4$). It assembles the complete physical stiffness matrix (`AMATRX`) and internal force vector (`RHS`) incorporating the energetic tension/compression split.
- **Layer 3 (Visualizer UMAT, standard CPE4/CPE3):** Exists exclusively to project element state variables (`SDV1 = d`, `SDV2 = H`, `SDV17 = E_frac`, `SDV18 = E_elas`) into the Abaqus output database (`.odb`) for graphical postprocessing.

In the canonical reference implementation (`f42_mixed_uel.for`, lines 876–882), Layer 3 UMAT is explicitly configured as a **dummy visualizer** with negligible stiffness:
```fortran
      DO K1 = 1, NTENS
        DO K2 = 1, NTENS
          DDSDDE(K2, K1) = 0.0D0
        END DO
        DDSDDE(K1, K1) = 1.0D-11
        STRESS(K1)     = 0.0D0
      END DO
```
Because Layer 2 already contributes the full physical stiffness $K_{\text{mech}}$, Layer 3 must not contribute stiffness.

### 2.2 Mechanism 1: Constitutive Contamination in Layer 3 UMAT

In `f42_amor_split_uel.for` (lines 750–820), the developer inadvertently duplicated the full Amor constitutive equations into the `UMAT` subroutine, assigning:
$$E = 210\,\text{GPa}, \quad g(d) = (1 - d)^2 + k, \quad \mathbb{C}_{\text{deg}} = g(d) \mathbb{C}^+ + \mathbb{C}^-$$
This resulted in two severe pathologies:
1. **Double Stiffness:** Both Layer 2 and Layer 3 assembled full mechanical stiffness matrices onto the exact same displacement degrees of freedom, doubling the effective elastic stiffness in the undamaged state.
2. **Pathological Feedback:** Layer 3 UMAT attempted to read the trial phase-field value $d$ from the shared common block `SV_PHASE_TRIAL(PHYSIDX)`. When uninitialized, `d` became `NaN`, causing degradation $g(d) = \text{NaN}$, which infected `DDSDDE` with `NaN` and assembled directly into the global stiffness matrix.

### 2.3 Mechanism 2: Missing Fortran `SAVE` Attribute on Shared Common Block

In `f42_amor_split_uel.for`, communication between UEL and UMAT occurs through a Fortran common block:
```fortran
      COMMON /CB_STATE_TRANS/ SV_PHASE_TRIAL(150000), ...
```
In dynamic shared libraries (`libstandardU.so` on Linux), memory allocated in a common block without an explicit `SAVE` statement is subject to stack/heap reallocation and contains uninitialized indeterminate bit patterns between subroutine invocations.

In `f42_amor_split_uel.for`:
- `COMMON /CB_STATE_TRANS/` allocated 16.8 MB (8 arrays $\times$ 150,000 double-precision entries) without the `SAVE` statement.
- Uninitialized slots evaluated to signaling `NaN`.
- When UMAT accessed `SV_PHASE_TRIAL(PHYSIDX)` during initial stiffness evaluation, it read `NaN`, propagating it directly into `DDSDDE`.

### 2.4 Mechanism 3: Kinematic Equation Condensation with Master Node 13276

In the production input deck `PK_F1714_JOB2_ADAPTED_PROD.inp`, 52 `*EQUATION` constraint cards tied each top boundary node $u_{i,2}$ to master reference node 13276:
```inp
*EQUATION
2
13276, 2, -1.0
<node_i>, 2, 1.0
```
Node 13276 is an isolated reference node with zero continuum element connectivity. During equation condensation:
1. The stiffness matrix rows corresponding to boundary nodes contained `NaN` entries contributed by the contaminated Layer 3 UMAT.
2. Abaqus condensed the constraint equations into master node 13276:
   $$K_{\text{condensed}} = \sum_i K_{ii} = \text{NaN}$$
3. The linear solver evaluated $u_{13276,2} = \text{NaN}$.
4. Because $u_{13276,2} = \text{NaN}$, no displacement increment was transferred back to the physical nodes.
5. All displacement degrees of freedom remained zero ($u_x = 0, u_y = 0$), producing zero strain ($\boldsymbol{\epsilon} = \mathbf{0}$) and zero stress ($\boldsymbol{\sigma} = \mathbf{0}$).
6. With zero internal forces, the residual vector was identically zero, causing the Newton-Raphson solver to report trivial 1-iteration convergence (`THERE IS ZERO FORCE EVERYWHERE`).

### 2.5 Mechanism 4: Unbounded Capacity Loops in `UEXTERNALDB`

In `f42_amor_split_uel.for` (`LOP=2`), global energy integration was coded as:
```fortran
      DO I = 1, N_CAPACITY  ! N_CAPACITY = 150,000
        TOTAL_FRAC_ENERGY = TOTAL_FRAC_ENERGY + SV_FRAC_EN_TOT(I)
        TOTAL_ELAS_ENERGY = TOTAL_ELAS_ENERGY + SV_ELAS_EN_TOT(I)
      END DO
```
For the 13,034-element mesh, slots 13,035 to 150,000 were never visited by UEL, remaining uninitialized `NaN`. Summing these unvisited slots corrupted `uel_energy_balance.csv` with `NaN` from Increment 1.

---

## 3. Governed Repair Plan (Task F1716)

To completely eliminate these defects while preserving all governing rules:

### 3.1 Repair Item 1: Authored Versioned Subroutine `f42_amor_split_uel_v2.for`
- The canonical production UEL `f42_mixed_uel.for` (`CE8D5EDC...`, 907 lines) and predecessor `f42_amor_split_uel.for` (`6778B685...`, 826 lines) remain **bitwise frozen**.
- Create package directory `models/pandey_kumar_mode1/208_f1716_five_hole_production/`.
- Author `f42_amor_split_uel_v2.for` incorporating:
  1. **Dummy Visualizer UMAT:** Revert Layer 3 `UMAT` to standard dummy stiffness ($DDSDDE(I,I) = 1.0\times 10^{-11}$, $STRESS(I) = 0.0$). Layer 3 can never contaminate global stiffness or assembly.
  2. **Strict State Transfer & Clamping:** UMAT only copies state variables from UEL for visualization, with strict bounds clamping:
     $$d \in [0.0, 1.0], \quad H \ge 0.0$$
     and explicit `NaN` sanitization:
     ```fortran
     IF (D_VAL .NE. D_VAL .OR. D_VAL .LT. 0.0D0) D_VAL = 0.0D0
     IF (D_VAL .GT. 1.0D0) D_VAL = 1.0D0
     ```
  3. **Explicit Fortran `SAVE` Attribute:** Add `SAVE /CB_STATE_TRANS/` in `UEXTERNALDB`, `UEL`, and `UMAT` to guarantee thread-safe static persistence across dynamic library calls.
  4. **Bounded Capacity Loops:** In `UEXTERNALDB LOP=2`, loop only over active physical elements:
     ```fortran
     DO I = 1, N_PHYS_ACTIVE  ! dynamically set from element count
     ```

### 3.2 Repair Item 2: Input Deck Kinematic & Reaction Force Architecture
- Input deck generated via `scripts/method_a_framework/deck_builder.py`.
- Ensure top nodes `N_TOP` have robust kinematic displacement boundary conditions.
- Explicitly request reaction force output on `N_BOTTOM`:
  ```inp
  *NODE OUTPUT, NSET=N_BOTTOM
  RF
  ```
- Sum tensile reaction force strictly from bottom nodes:
  $$F_{\text{tensile}}(t) = -\sum_{j \in N_{\text{BOTTOM}}} RF_{2,j}(t)$$
  guaranteeing physical equilibrium independent of reference node constraint condensation.

### 3.3 Repair Item 3: Controlled Physical Pilot on Target Cluster
Prior to production execution, run an interactive/datacheck pilot on the cluster login node:
- 2-element or coarse multi-element model incorporating `*EQUATION` constraints and reference node.
- Verify:
  1. $u_y > 0$ applied at top boundary produces non-zero displacement on continuum nodes.
  2. Reaction force $F_{\text{tensile}} > 0$ matches analytical elastic stiffness.
  3. Integration point stresses $\sigma_{yy} > 0$ are non-zero.
  4. Phase-field damage $d$ evolves strictly within $[0, 1]$.
  5. `uel_energy_balance.csv` records finite, monotonically increasing energies.

### 3.4 Repair Item 4: Multi-Core HPC Qualification & Walltime Optimization
- Query TU Freiberg HPC cluster scheduler limits (`normal_imfdfkmq`).
- Evaluate 4 CPU cores (SMP shared memory) with 32 GB RAM.
- Note: Distributed multi-rank MPI is strictly disqualified for UEL; execution must remain single-rank multi-threaded SMP (`abaqus job=... cpus=4`).
- Walltime: configure for 24 to 48 hours to guarantee full fracture evolution without premature timeout.
- Optimize ODB output frequency (e.g. `FREQUENCY=5` or `FREQUENCY=10`) to keep output size manageable (~2–4 GB instead of 24 GB).

### 3.5 Repair Item 5: Independent Review & Governed Production Run
- Dispatch formal review request via OpenClaw PAD bridge (`HND-F1716-...`).
- Execute production run using `scripts/hpc/Invoke-Mode1Execution.ps1` with once-only accounting (`max_new_pbs_submissions = 1`).
- Monitor live telemetry, extract physical fracture morphology, and validate against Pandey & Kumar (2025, Figures 22–25).

---

## 4. Verification Gate Criteria

| Phase | Milestone | Acceptance Criteria |
| :--- | :--- | :--- |
| **Phase 1** | Failure Analysis Document | Forensic root cause documented with exact Fortran/Abaqus evidence. |
| **Phase 2** | `f42_amor_split_uel_v2.for` | Layer 3 dummy stiffness verified; `SAVE` attribute verified; unit tests PASS (100%). |
| **Phase 3** | Controlled Physical Pilot | $F > 0$, $\sigma > 0$, $d \in [0, 1]$, zero `NaN`s in ODB and CSV. |
| **Phase 4** | HPC Resource & SMP Qualification | PBS script configured with 4 CPUs, $\le 32\,\text{GB}$, 24h walltime, ODB frequency optimized. |
| **Phase 5** | Independent Review & Submission | ChatGPT DECISION: APPROVE; 1 PBS submission accepted. |
| **Phase 6** | Telemetry Monitoring | $F-u$ curve shows linear elastic regime, softening, and crack propagation. |
| **Phase 7** | Scientific Validation | Quantitative comparison with Pandey–Kumar (2025, Figures 22–25). |
| **Phase 8** | Framework & Closeout | Method A framework updated; session ledger and git push synchronized. |

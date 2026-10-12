# Mode-I Method C State Transfer: Architecture, Technical Requirements, and Projection Qualification

**Document ID:** `MODE1_METHOD_C_STATE_TRANSFER_REQUIREMENTS_AND_PROJECTION_QUALIFICATION`  
**Protocol Version:** 2  
**Task ID:** `F1420-MODE1-METHOD-C-STATE-TRANSFER-ARCHITECTURE-AND-PROJECTION-PROTOTYPE`  
**Author:** Gemini Antigravity  
**Date:** 12 October 2026  
**Status:** `QUALIFIED_OFFLINE_PROJECTION_PROTOTYPE_VERIFIED`  
**Authoritative Subroutine Hash:** `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (`f42_mixed_uel.for`)  

---

## 1. Executive Summary & Scientific Scope

Following the successful completion and formal scientific evaluation of **Method B** (pre-analysis load partitioning, closed under commit `ad2bc6f0`), the research roadmap progresses to **Method C** (sequential adaptive remeshing and state transfer).

Method B demonstrated that pre-analysis on the linear-elastic state ($u = 0.0050\,\text{mm}$) produces a static adapted mesh of $14{,}677$ finite elements that resolves the crack-tip initiation singularity with high fidelity ($h_{\text{tip}} = 1.91\,\mu\text{m}$, initial stiffness $K_0 = 137.892\,\text{kN/mm}$, $-0.0389\%$ error vs reference). However, because Method B freezes the mesh prior to fracture initiation, the far ligament remains coarse ($h = 19.7\,\mu\text{m}$), leading to regularized post-peak work accumulation ($W_{\text{ext}} = 3.332\,\text{mJ}$ vs $2.828\,\text{mJ}$).

**Method C** addresses this limitation by dynamically updating the finite element discretization during crack growth:
$$\mathcal{T}_0 \xrightarrow{\text{solve}} \mathcal{T}_1 \xrightarrow{\text{remesh \& transfer}} \mathcal{T}_2 \dots \xrightarrow{\text{complete}} \mathcal{T}_N$$
This requires transferring the damaged physical and numerical state across nonmatching discretizations:
$$(\mathbf{u}_h^{(A)}, d_h^{(A)}, \mathcal{H}_h^{(A)}) \xrightarrow{\mathcal{P}_{A \to B}} (\mathbf{u}_h^{(B)}, d_h^{(B)}, \mathcal{H}_h^{(B)})$$

This document records the mathematical formulation, implementation audit, technical syntax requirements, and unit test verification of the **Mode-I Method C State Transfer Engine** (`mode1_state_transfer_engine.py`).

---

## 2. Theoretical & Mathematical Architecture

### 2.1 State Variables and Degrees of Freedom
In the Pandey-Kumar (2025) Mode-I benchmark, the boundary value problem is defined on the unit square $\Omega = [0, 1] \times [0, 1]\,\text{mm}$ with a sharp crack slit $a_0 = 0.5\,\text{mm}$ along $y = 0.5\,\text{mm}$ ($0 \le x \le 0.5$). The state of the continuum at any point $\mathbf{x} \in \Omega$ consists of:
1. **Primary Nodal Displacements (DOFs 1, 2):** $\mathbf{u}(\mathbf{x}) = [u_x, u_y]^T$.
2. **Phase-Field Damage (DOF 3):** $d(\mathbf{x}) \in [0, 1]$, where $d = 0$ is intact and $d = 1$ is fully broken.
3. **Historical Crack-Driving Strain Energy (Integration Points):**
   $$\mathcal{H}(\mathbf{x}, t) = \max_{s \in [0, t]} \psi_0^+(\mathbf{x}, s) \ge 0$$
   where $\psi_0^+$ is the tensile spectral/volumetric strain energy density.

### 2.2 Multi-Layer Co-Located Element Representation
The authoritative implementation in `f42_mixed_uel.for` (`CE8D5EDC...`) employs three co-located finite element layers sharing identical nodal topology:
* **Layer 1: Phase-Field UEL (`U1` quad, `U3` tri):** Solves the second-order phase-field Helmholtz equation for DOF 3. Active elements $1 \dots N_{\text{phys}}$.
* **Layer 2: Mechanical UEL (`U2` quad, `U4` tri):** Solves momentum balance for DOFs 1 and 2 under degraded elasticity $\mathbf{\sigma} = g(d)\mathbf{C}_0 : \mathbf{\varepsilon}$. Active elements $N_{\text{phys}}+1 \dots 2N_{\text{phys}}$.
* **Layer 3: Companion UMAT Facsimile (`CPE4` quad, `CPE3` tri):** An infinitesimal companion layer ($E_{\text{dummy}} = 10^{-11}\,\text{kN/mm}^2$) used exclusively to project state variables into standard Abaqus `.odb` field outputs for visualization. Active elements $2N_{\text{phys}}+1 \dots 3N_{\text{phys}}$.

### 2.3 Topology-Guarded Flank Isolation
Across the sharp crack slit ($y = 0.5$, $0 \le x \le 0.5$), the displacement field is discontinuous:
$$\llbracket u_y \rrbracket = u_y(x, 0.5^+) - u_y(x, 0.5^-) = \Delta u_y > 0$$
Unconstrained spatial interpolation (such as global radial basis functions, KD-trees, or naive Delaunay triangulation) inevitably bleeds displacement across the slit, destroying the crack opening $\llbracket u_y \rrbracket$ and generating spurious inter-flank stresses.

To prevent cross-contamination, the engine implements **Topology-Guarded Flank Partitioning**:
* Elements with centroid $y > 0.5$ are partitioned into `UPPER`.
* Elements with centroid $y < 0.5$ are partitioned into `LOWER`.
* Duplicated nodes along the slit ($x \le 0.5$) are classified as `UPPER` or `LOWER` based on connected element incidence.
* Intact ligament nodes ($x > 0.5$) are classified as `LIGAMENT`.
* Host element search restricts candidate donor elements strictly to the matching flank partition:
  $$\mathbf{x}_{\text{recipient}} \in \text{flank} \implies \text{host}(\mathbf{x}) \in \text{donor\_elems}_{\text{flank}}$$

---

## 3. Offline Projection vs. Genuinely Qualified Restart: The Critical Distinction

A central epistemological requirement of this project is distinguishing an **offline spatial projection** from a **genuinely qualified restart**:

| Dimension | Offline Spatial Projection (Qualified Here) | Genuinely Qualified Continuation Solve (Pending Gate C) |
| :--- | :--- | :--- |
| **Scope** | Mathematical mapping between meshes $\mathcal{T}_A \to \mathcal{T}_B$. | Nonlinear static equilibrium solve in Abaqus 2023. |
| **Verification Basis** | Geometric interpolation, boundary preservation, $L_2$ error, bounded ranges. | Abaqus Datacheck, initial increment convergence, Newton iteration stability. |
| **Equilibrium Status** | Not in discrete equilibrium on $\mathcal{T}_B$. | Must resolve initial out-of-balance residual $\mathbf{R}_0 = \mathbf{F}_{\text{ext}} - \mathbf{F}_{\text{int}}$. |
| **Energy Status** | Measured projection energy difference $\Delta E_{\text{frac}}, \Delta E_{\text{elas}}$. | Continuous energy conservation along equilibrium trajectory. |
| **Execution Tool** | Standalone Python module (`mode1_state_transfer_engine.py`). | Abaqus/Standard solver (`standard.exe`) with `f42_mixed_uel.for`. |

### 3.1 The Initial Equilibrium Out-of-Balance Residual $\mathbf{R}_0$
When nodal displacements $\mathbf{u}_h^{(B)}$ and damage $d_h^{(B)}$ are projected onto a new discretization $\mathcal{T}_B$, the internal nodal force vector:
$$\mathbf{F}_{\text{int}}^{(B)} = \sum_{e} \int_{\Omega_e^{(B)}} \mathbf{B}^T \mathbf{\sigma}(d_h^{(B)}, \mathbf{u}_h^{(B)}) \, d\Omega$$
does **not** exactly equal the external reaction force vector $\mathbf{F}_{\text{ext}}^{(A)}$ from the previous mesh. The residual:
$$\mathbf{R}_0 = \mathbf{F}_{\text{ext}} - \mathbf{F}_{\text{int}}^{(B)} \ne \mathbf{0}$$
must be converged by the Newton-Raphson solver in the first increment of Step 1. If the mesh change $\mathcal{T}_A \to \mathcal{T}_B$ is too coarse or introduces localized strain spikes, $\mathbf{R}_0$ can cause severe cutbacks or divergence. Therefore, continuation solves require adaptive time-stepping controls and small initial increments ($\Delta t_{\text{init}} \le 10^{-4}$).

---

## 4. Technical Requirements for Restoring State into Abaqus 2023

### 4.1 Abaqus Input Deck Syntax & Keyword Constraints
Abaqus 2023 enforces strict syntax rules on initialization keywords:

1. **`*INITIAL CONDITIONS, TYPE=DISPLACEMENT`:**
   * Prescribes nodal values at step time $t = 0$.
   * Must define DOFs 1, 2 (mechanical) and DOF 3 (phase field) for all mesh nodes:
     ```text
     *INITIAL CONDITIONS, TYPE=DISPLACEMENT
     <node_id>, 1, 1, <ux>
     <node_id>, 2, 2, <uy>
     <node_id>, 3, 3, <d>
     ```
   * Must include the reference point node `999999` with initial displacement $(0.0, u_{\text{handoff}})$.

2. **`*INITIAL CONDITIONS, TYPE=SOLUTION`:**
   * Prescribes element integration-point state variables (`SVARS`).
   * **Strict 8-Field Card Limit:** Abaqus cards allow a maximum of 8 comma-separated fields per data line.
   * Formatting 18 SVARs requires exactly three data lines per element:
     ```text
     *INITIAL CONDITIONS, TYPE=SOLUTION
     <elem_id>, <sv1>, <sv2>, <sv3>, <sv4>, <sv5>, <sv6>, <sv7>
       <sv8>, <sv9>, <sv10>, <sv11>, <sv12>, <sv13>, <sv14>, <sv15>
       <sv16>, <sv17>, <sv18>
     ```
   * **UEL History Variable Mapping in `f42_mixed_uel.for`:**
     * For 4-node quads (`JTYPE = 1`): Lines 250–254 read `SVARS(8+KPT)` for $KPT = 1..4$. Therefore, history values $H_1..H_4$ must reside in **SVARS 9..12**.
     * For 3-node triangles (`JTYPE = 3`): Lines 256–260 read `SVARS(6+KPT)` for $KPT = 1..3$. Therefore, history values must reside in **SVARS 7..9**.

3. **Node Set Card Wrapping (Gate 6A Guard):**
   * Abaqus silently truncates `*NSET` data lines containing more than 16 node IDs (the root cause of the historical 71k stiffness defect).
   * All generated sets (`N_BOTTOM`, `N_TOP`) must wrap across valid lines with $\le 16$ items per line.

4. **Continuation Step Ramping:**
   * Step 1 must continue loading from $u_{\text{handoff}}$ to $u_{\text{final}}$:
     ```text
     *STEP, NAME=Step-1, NLGEOM=YES, INC=10000
     *STATIC
     2.00000000e-04, 1.0, 1.0e-12, 2.00000000e-04
     *BOUNDARY
     N_BOTTOM, 2, 2, 0.0
     1, 1, 1, 0.0
     N_RP, 2, 2, 0.0100000000
     ```

---

## 5. Verification Suite & Test Results

The state transfer engine was verified using a 9-test unit test suite (`test_mode1_f1420_state_transfer_engine.py`):

| Test ID | Test Name | Target / Physics Verified | Result |
| :--- | :--- | :--- | :---: |
| **`test_01`** | `frozen_fortran_subroutine_hash_preserved` | Verifies subroutine SHA-256 `CE8D5EDC...` remains bit-identical. | **PASS** |
| **`test_02`** | `mesh_parsing_and_topology_classification` | Parses real Mode-I decks (2,906 and 14,677 elements); verifies upper/lower flank and ligament tagging. | **PASS** |
| **`test_03`** | `identity_mapping` | Identity projection on identical mesh yields $\|u - u_{\text{proj}}\|_\infty < 10^{-12}$ and $\|d - d_{\text{proj}}\|_\infty < 10^{-12}$. | **PASS** |
| **`test_04`** | `linear_field_reproduction_nonmatching` | Projects linear polynomials $u_x, u_y, d$ across nonmatching 4x4 $\to$ 8x8 meshes; error $< 10^{-10}$. | **PASS** |
| **`test_05`** | `crack_seam_discontinuity_preservation` | Proves upper slit nodes receive $+u_y$ ($d \approx 0.85$) and lower slit nodes receive $-u_y$ ($d \approx 0.15$) with zero cross-seam smearing. | **PASS** |
| **`test_06`** | `bounded_interpolation_and_clamping` | Rejects invalid states; clamps $0 \le d \le 1$ and $H \ge 0$. | **PASS** |
| **`test_07`** | `damage_irreversibility_enforcement` | Enforces damage monotonicity $d_{\text{target}}(\mathbf{x}) \ge d_{\text{prior}}(\mathbf{x})$ across mapping cycles. | **PASS** |
| **`test_08`** | `continuation_deck_assembly_and_syntax_validation` | Validates generated deck: wrapped `N_BOTTOM` ($\le 16$), valid `TYPE=SOLUTION` cards ($\le 8$ items), exactly 18 SVARs. | **PASS** |
| **`test_09`** | `real_mode1_spatial_projection_and_metrics` | Projects real Mode-I spatial damage data ($u = 0.0050\,\text{mm}$) from 14.7k mesh to a recipient mesh; computes domain integrals. | **PASS** |

**Summary:** 9/9 tests passed in **0.435 seconds** (`Ran 9 tests in 0.435s. OK`).

---

## 6. Smallest Next Abaqus Continuation Experiment

To transition safely from offline projection to an approved Abaqus continuation solve without premature multi-cycle execution, the project defines the following phased gate sequence:

```
[F1420: Offline Projection Verified] (COMPLETE)
                 |
                 v
[Gate C1: 1-Element Continuation Datacheck]
  - Deck: Minimal 1-element / 4-element restart deck embedding mapped state
  - Execution: Abaqus datacheck (pre.exe + standard.exe -datacheck)
  - Purpose: Certify Abaqus 2023 parser accepts TYPE=SOLUTION cards without warnings
                 |
                 v
[Gate C2: Coarse-to-Coarse Self-Continuation Solve]
  - Donor: Coarse 2,906 FE solve stopped at u = 0.0050 mm
  - Recipient: Identical 2,906 FE mesh (identity transfer)
  - Execution: Single-increment static restart solve (Inc 1)
  - Acceptance: Newton iterations <= 4, cutbacks = 0, delta RF < 0.1%
                 |
                 v
[Gate C3: Nonmatching Pre-Peak Continuation Solve]
  - Donor: Coarse 2,906 FE solve at u = 0.0050 mm
  - Recipient: Native 14,677 FE adapted mesh
  - Execution: Step-1 continuation solve from u = 0.0050 to 0.0100 mm
  - Acceptance: Smooth peak crossing, monotonic softening, global energy balance
```

---

## 7. Artifact Provenance & Registered Hashes

* `scripts/state_transfer/mode1_state_transfer_engine.py`: `CAB63D55761FAD158594E23CEE3032B303CCF107C2B6F92F77D8180479D0F105`
* `scripts/state_transfer/mode1_state_transfer_engine.recovered_f1420.py`: `A9DD0CE96B759A7B9C0532EEDEA2B0849C1A24C11F4CAF5AECA72855298ECD08`
* `tests/unit/test_mode1_f1420_state_transfer_engine.py`: `9165AFDC26C4E2849F05E729EC8746F970A1101E9E68E0BA55E408A5EAE996C3`
* Production UEL Subroutine (`f42_mixed_uel.for`): `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (strictly preserved)

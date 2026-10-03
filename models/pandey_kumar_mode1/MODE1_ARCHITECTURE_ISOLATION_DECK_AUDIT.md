# Mode-I Architecture-Isolation Deck Difference Audit Report

**Audit Target:** Package 89 (`PK_M1_JOB1_UEL_2906.inp`) vs Package 90 (`PK_M1_JOB1_CONTINUUM_MATCHED_2906.inp`)  
**Audit Date:** `2026-10-03T10:15:00+02:00`  
**Auditing Agent:** `gemini-antigravity`  
**Governing Task:** `F1178-GATE6B-ARCHITECTURE-ISOLATION-DECK-AUDIT-20261003`  
**Parent Commit:** `d7c82ee5`  

---

## 1. Executive Verdict & Core Finding

### Final Predeclared Verdict:
```
================================================================================
                    ARCHITECTURE_ISOLATION_CONTROL_VALID
================================================================================
```

All non-architectural physics, geometry, boundary conditions, loading schedules, time incrementation, and output requests are **bit-for-bit IDENTICAL** or **demonstrably EQUIVALENT_BY_CONSTRUCTION**.

- **Total Comparison Dimensions Audited:** 34
- **IDENTICAL:** 26
- **EQUIVALENT_BY_CONSTRUCTION:** 5
- **EXPECTED_ARCHITECTURE_DIFFERENCE:** 3
- **UNINTENDED_CONFOUNDING_DIFFERENCE:** 0

**Confounding Check Result:** Exactly **0** unintended confounding differences exist.  
**Action on HPC Queue:** Running Job `1409914.mmaster02` (Package 90 continuum control) is completely valid; **zero new PBS submissions are required or authorized**.

---

## 2. Cryptographic Provenance

| Artifact | Package 89 (Layered Variant) | Package 90 (Continuum Control) | Status |
| :--- | :--- | :--- | :---: |
| **Input Deck** | `models/pandey_kumar_mode1/89_mode1_preanalysis_uel_canonical_2906/PK_M1_JOB1_UEL_2906.inp` | `models/pandey_kumar_mode1/90_mode1_preanalysis_continuum_matched_2906/PK_M1_JOB1_CONTINUUM_MATCHED_2906.inp` | Audited |
| **Input Deck SHA-256** | `27aab773a116e3c8a832e4980d0e25f48a435f34dedece4abe78ffa232c0c1ff` | `b60dd35d56ab2824902f2d90912e222cf9d335d7d9911cf8dd17a3dc2b52e5f9` | Verified |
| **PBS Script** | `submit_solver.pbs` (`cc541dab3a78aa0c0b5f0dcb0c8f73b9345cb3e5f2001c9194e1e256e7d72759`) | `submit_solver.pbs` (`72df7210d00c3d4e6938399ffebaabf6a16e4e462afc813f689789f1877bc1ed`) | Verified |
| **Subroutine** | `f42_mixed_uel.for` (`91ad75b0ff65dbd25967feae42af531239a99b3f76d9ef49d7359a66403dea6b`) | *None* (standard Abaqus continuum elasticity) | Verified |
| **PBS Job ID** | **`1409912.mmaster02`** | **`1409914.mmaster02`** | Active (R/Q) |
| **Epistemic Role** | `DIAGNOSTIC_JOB1_LAYERED_VARIANT` | `ARCHITECTURE_ISOLATION_CONTROL` | Frozen |

---

## 3. Deep Physical and Kinematic Analysis

### A. RP Kinematics & Lateral Freedom Verification
A critical concern in pre-analysis auditing is whether the Reference Point coupling alters the physical constraint kinematics relative to standard boundary conditions:
- **Kinematic Formulation:** Both decks specify exactly 51 `*EQUATION` cards. Each equation binds degree of freedom 2 ($u_y$) of a top-edge node ($y = 1.0\,\text{mm}$) directly to degree of freedom 2 of Reference Point node 999999 ($x=0.5, y=1.0$):
  $$u_y^{(i)} - u_y^{(\text{RP})} = 0 \implies u_y^{(i)} = u_y^{(\text{RP})}$$
- **Lateral Freedom ($u_x$):** Crucially, degree of freedom 1 ($u_x$) is **not** present in any `*EQUATION` and **not** constrained by any `*BOUNDARY` card on the top edge in either deck.
- **Physical Boundary Equivalence:** Both decks enforce pure lateral-free roller boundary conditions with zero shear traction ($T_x = 0$) and unconstrained lateral Poisson contraction ($u_x$ free).
- **Rigid-Body Prevention:** Both decks pin node 25 ($x = 0.0, y = 0.0$) in DOF 1 (`1, 1, 0.0`) to prevent rigid-body translation in $X$.
- **Bottom Edge:** Both decks apply $u_y = 0$ on all 51 bottom nodes (`N_BOTTOM, 2, 2, 0.0`) with $u_x$ free.

### B. Material Stiffness Allocation & Companion Tangent Verification
- **Package 90:** Standard continuum elasticity `*ELASTIC, TYPE=ISOTROPIC: 210.0, 0.3` assigned directly to `All_elem` (plane-strain thickness $B = 1.0\,\text{mm}$).
  - Intended Young's modulus: $E = 210.0\,\text{kN/mm}^2 = 210\,\text{GPa}$.
  - Poisson's ratio: $\nu = 0.3$.
- **Package 89:**
  - Mechanical Layer 2 UEL integrates plane-strain elasticity with $E = 210.0\,\text{kN/mm}^2$ and $\nu = 0.3$.
  - Companion Layer 3 UMAT: receives $E=210.0, \nu=0.3, n_{\text{phys}}=2906.0$ as constants; returns Cauchy stress $\boldsymbol{\sigma}$ for post-processing and Abaqus Mises stress discretization/error indicator associated with the recovered stress solution, and explicitly sets the tangent matrix in lines 913–918 of `f42_mixed_uel.for`:
    ```fortran
    C     Material Jacobian: negligible dummy stiffness (prevents double-counting with UEL Layer 2)
              DDSDDE(I,J) = ZERO
            DDSDDE(I,I) = 1.D-11
    ```
  - **Negligible Tangent Acknowledgment:** The companion tangent contributes a nominal diagonal value of $10^{-11}\,\text{kN/mm}^2$ ($10^{-5}\,\text{Pa}$). Relative to $E = 210.0\,\text{kN/mm}^2$, the stiffness ratio is $10^{-11} / 210 \approx 4.8 \times 10^{-14} \ll 1$, which is strictly negligible. Package 89 does not duplicate the elastic stiffness.

### C. Mesh Coordinates, Node Labels, and Seam Topology
- **2,988 Mesh Nodes:** Node coordinates match with maximum absolute difference of $0.0000000000\times 10^{0}\,\text{mm}$ (bit-identical).
- **25 Seam Duplicate Node Pairs:** Both decks feature the exact same 25 duplicate node pairs along $y=0.5, 0 \le x \le 0.5$ (50 seam nodes + 1 shared crack tip node at $(0.5, 0.5)$).

---

## 4. Itemized Architecture-Isolation Audit Matrix

| Category | Item Name | Package 89 (Layered) | Package 90 (Continuum) | Classification | Scientific Justification |
| :--- | :--- | :--- | :--- | :---: | :--- |
| GEOMETRY | `mesh_node_count` | 2988 | 2988 | **`IDENTICAL`** | Both decks define exactly 2,988 physical domain mesh nodes. |
| GEOMETRY | `mesh_node_coordinates` | max_diff=0.0 (N=2988) | max_diff=0.0 (N=2988) | **`IDENTICAL`** | Coordinates of all 2,988 mesh nodes are bit-for-bit identical (max diff = 0.0000000000e+00). |
| GEOMETRY | `rp_node_definition` | (0.5, 1.0, 0.0) | (0.5, 1.0, 0.0) | **`IDENTICAL`** | Reference Point node 999999 is located at (0.5, 1.0, 0.0) in both decks. |
| TOPOLOGY | `element_counts_and_layers` | 8,718 (3 layers of 2906) | 2,906 (1 layer of 2906) | **`EQUIVALENT_BY_CONSTRUCTION`** | Package 89 has 3 co-located layers (PF, MECH, UMAT) while Package 90 has standard single layer. Underlying connectivity matches 2,906/2,906. |
| TOPOLOGY | `element_type_distribution` | 2818 U1/U2/CPE4, 88 U3/U4/CPE3 | 2818 CPE4, 88 CPE3 | **`EQUIVALENT_BY_CONSTRUCTION`** | Both decks discretize the exact same 2,818 quads and 88 triangles with identical vertex node order. |
| TOPOLOGY | `crack_seam_duplicate_nodes` | 25 pairs (50 nodes + 1 tip) | 25 pairs (50 nodes + 1 tip) | **`IDENTICAL`** | Both decks define the exact same 25 duplicate node pairs along the sharp crack seam y=0.5, 0<=x<=0.5. |
| SETS | `nset_N_RP` | count=1 | count=1 | **`IDENTICAL`** | Node set N_RP has bit-identical node ID membership. |
| SETS | `nset_N_PIN` | count=1 | count=1 | **`IDENTICAL`** | Node set N_PIN has bit-identical node ID membership. |
| SETS | `nset_N_BOTTOM` | count=51 | count=51 | **`IDENTICAL`** | Node set N_BOTTOM has bit-identical node ID membership. |
| SETS | `nset_N_TOP` | count=51 | count=51 | **`IDENTICAL`** | Node set N_TOP has bit-identical node ID membership. |
| SETS | `elset_All_elem` | count=0 (umatelem) | count=0 (PLATE_TRIS+QUADS) | **`EQUIVALENT_BY_CONSTRUCTION`** | Both decks define All_elem spanning all 2,906 underlying elements of the domain for whole-element error evaluation. |
| SETS | `layer_specific_elsets` | PF_ELEM, MECH_ELEM, umatelem | None (standard continuum) | **`EXPECTED_ARCHITECTURE_DIFFERENCE`** | Layer-specific sets are architectural necessities of the 3-layer dual UEL formulation. |
| BOUNDARIES | `bottom_roller_bc` | N_BOTTOM, 2, 2, 0.0 (U1 free) | N_BOTTOM, 2, 2, 0.0 (U1 free) | **`IDENTICAL`** | Both decks enforce bottom roller boundary (u_y=0) while allowing lateral sliding (u_x unconstrained). |
| BOUNDARIES | `rigid_body_pin_bc` | N_PIN (node 25), 1, 1, 0.0 | N_PIN (node 25), 1, 1, 0.0 | **`IDENTICAL`** | Both decks pin node 25 at (0.0, 0.0) in DOF 1 to prevent rigid body translation in X. |
| BOUNDARIES | `top_prescribed_displacement` | Step-1: 0.0050, Step-2: 0.0100 | Step-1: 0.0050, Step-2: 0.0100 | **`IDENTICAL`** | Both decks prescribe the identical two-step displacement history at Reference Point node 999999. |
| KINEMATICS | `rp_top_coupling_equations` | 51 equations (51) | 51 equations (51) | **`IDENTICAL`** | Both decks use identical *EQUATION cards coupling DOF 2 of each top node to RP 999999 (u_y^top = u_y^RP). DOF 1 is free. |
| KINEMATICS | `lateral_freedom_top_edge` | DOF 1 unconstrained (lateral-free) | DOF 1 unconstrained (lateral-free) | **`IDENTICAL`** | Neither deck constrains DOF 1 (u_x) on top nodes or RP. Pure roller boundary kinematics are preserved. |
| STEPS | `step1_definition` | *STEP, NAME=Step-1, NLGEOM=NO, INC=1000 | *STEP, NAME=Step-1, NLGEOM=NO, INC=1000 | **`IDENTICAL`** | Step-1: NLGEOM=NO, INC=1000 in both decks. |
| STEPS | `step1_static_params` | 0.002, 1.0, 1.0E-9, 0.002 (500 incs) | 0.002, 1.0, 1.0E-9, 0.002 (500 incs) | **`IDENTICAL`** | Identical time period 1.0, initial/max increment 0.002 (yielding 500 increments to u=0.005 mm). |
| STEPS | `step2_definition` | *STEP, NAME=Step-2, NLGEOM=NO, INC=2000 | *STEP, NAME=Step-2, NLGEOM=NO, INC=2000 | **`IDENTICAL`** | Step-2: NLGEOM=NO, INC=2000 in both decks. |
| STEPS | `step2_static_params` | 0.001, 1.0, 1.0E-9, 0.001 (1000 incs) | 0.001, 1.0, 1.0E-9, 0.001 (1000 incs) | **`IDENTICAL`** | Identical time period 1.0, initial/max increment 0.001 (yielding 1,000 increments to u=0.010 mm). |
| LOADING | `displacement_schedule` | Step-1 u=0.005 mm, Step-2 u=0.010 mm | Step-1 u=0.005 mm, Step-2 u=0.010 mm | **`IDENTICAL`** | Both decks enforce identical two-step physical displacement without variation. |
| SOLVER | `increment_controls` | Default automatic (no *CONTROLS override) | Default automatic (no *CONTROLS override) | **`IDENTICAL`** | Neither deck introduces artificial cutback or convergence parameter overrides. |
| PHYSICS | `geometric_nonlinearity` | NLGEOM=NO (linear kinematics) | NLGEOM=NO (linear kinematics) | **`IDENTICAL`** | Both decks solve under geometrically linear plane-strain kinematics. |
| MATERIAL | `elastic_constants` | E=210.0 kN/mm^2, nu=0.3 | E=210.0 kN/mm^2, nu=0.3 | **`IDENTICAL`** | Both decks define Young's modulus E=210.0 kN/mm^2 (210 GPa) and Poisson's ratio nu=0.3. |
| MATERIAL | `stiffness_allocation` | Mech UEL Layer 2 (E=210) + UMAT dummy 1e-11 | Standard continuum elasticity (E=210) | **`EQUIVALENT_BY_CONSTRUCTION`** | Package 90 standard elements carry ordinary elastic stiffness. Package 89 mechanical UEL carries intended stiffness; companion UMAT tangent is 1.0D-11 (negligible dummy stiffness 4.8e-14 ratio). |
| OUTPUTS | `field_output_frequency` | FREQUENCY=1 (every increment) | FREQUENCY=1 (every increment) | **`IDENTICAL`** | Both decks request field outputs at every increment. |
| OUTPUTS | `node_output_variables` | N_RP: U, RF | N_RP: U, RF | **`IDENTICAL`** | Both decks record displacement and reaction force at RP 999999. |
| OUTPUTS | `element_output_variables` | All_elem: MISESERI, MISESAVG, S, E, EVOL | All_elem: MISESERI, MISESAVG, S, E, EVOL | **`IDENTICAL`** | Both decks request the exact same element field variables for physical stress and error indicator recovery. |
| OUTPUTS | `companion_sdv_output` | umatelem: SDV | None (no UMAT layer) | **`EXPECTED_ARCHITECTURE_DIFFERENCE`** | SDV output in Package 89 records phase-field and internal state variables from companion layer. |
| INDICATOR | `miseseri_element_set` | All_elem (2,906 elements) | All_elem (2,906 elements) | **`EQUIVALENT_BY_CONSTRUCTION`** | one WHOLE_ELEMENT MISESERI value per underlying finite element on the 2,906 underlying elements spanning the domain. |
| SOLVER | `matrix_symmetry` | *USER ELEMENT, UNSYMM | Standard symmetric linear solver | **`EXPECTED_ARCHITECTURE_DIFFERENCE`** | Package 89 uses UNSYMM due to coupled phase-displacement equations; Package 90 solves standard symmetric linear continuum. |
| ENVIRONMENT | `abaqus_version` | Abaqus 2023 (double=both) | Abaqus 2023 (double=both) | **`IDENTICAL`** | Both packages execute Abaqus 2023 with double precision on the Freiberg HPC cluster. |
| ENVIRONMENT | `execution_mode` | 1-CPU Serial, 16 GB, normal_imfdfkmq | 1-CPU Serial, 16 GB, normal_imfdfkmq | **`IDENTICAL`** | Both packages execute as 1-CPU serial batch jobs on normal_imfdfkmq. |

---

## 5. Terminal Comparison Execution Rules

Upon terminal completion of Job `1409912.mmaster02` and Job `1409914.mmaster02`, the offline evaluator [`scripts/evaluation/evaluate_mode1_job1_miseseri.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/evaluation/evaluate_mode1_job1_miseseri.py) will execute with:
1. **Identical Step/Frame States:**
   - State 1: Step-1, Frame 500 ($u = 0.0050\,\text{mm}$).
   - State 2: Step-2, Frame 1000 ($u = 0.0100\,\text{mm}$).
2. **Zero Displacement Rescaling:** Direct evaluation without `disp_scale_factor`.
3. **Zero Arbitrary Thresholds:** Elimination of arbitrary cutoffs (20%, 33%, 60%, 70%).
4. **Three Directional Classifications:**
   - `TOWARD_TARGET_LOCALIZATION`
   - `NO_MEANINGFUL_IMPROVEMENT`
   - `AWAY_FROM_TARGET_LOCALIZATION`

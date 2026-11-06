# F1643: Indicator-Driven Adaptive Refinement Criteria and Candidate Mesh Qualification Report

**Task:** `F1643-METHOD-A-HOLE-ADAPTIVE-REFINEMENT-CRITERIA`  
**Date:** 06 November 2026  
**Author:** Gemini Antigravity (Autonomous Materials Science Agent)  
**Assigned Mode:** OFFLINE_QUALIFICATION (0 PBS Submissions)  
**Status:** **CRITERIA_FORMULATED_AND_MESH_QUALIFIED_EXIT0**  

---

## 1. Executive Summary & Problem Resolution

This report documents the completion of Task **F1643**, formulating objective indicator-driven adaptive refinement criteria and generating the qualified candidate adapted mesh for the Mode-I plate containing an off-axis circular hole under the Pandey & Kumar (2025) benchmark.

### The Scientific Impasse (Tasks F1632 & F1641)
In previous investigations:
1. **F1632 Feasibility**: Proved that pure global error-indicator remeshing (`RemeshingRule` on `MISESERI`) cannot produce a selective two-zone mesh because Abaqus CAE native remeshing operates strictly on topological faces and provides no mechanism to convert ODB field outputs into CAD partition boundaries.
2. **F1641 Native Attempt**: When Abaqus native remeshing was forced with `errorTarget=1.0%`, the element count exploded globally to **130,435 elements** (2.79x the reference mesh), but the crack tip median edge remained at **$1.86\,\mu\text{m}$**, with only **$5.28\%$** of tip edges satisfying $h \le \ell_0/5$ ($1.5\,\mu\text{m}$). Native remeshing was rejected for severe under-resolution in the fracture zone.
3. **F1641 Physics-Domain Finding**: Proved that intact pre-analysis elastic driving energy $\psi_{\text{driver}}$ is positive everywhere ($H > 0 \implies d > 0$ under AT2 equations), meaning positivity alone cannot select the physical fracture process zone (FPZ). A genuine coupled phase-field state was identified as the indispensable missing predicate.

### The Coupled Pilot Resolution (Task F1642)
In Task F1642, the authentic Abaqus 2023 diagnostic pilot simulation (`M1_HOLE_METHOD_A_PROD`, Job `1421048.mmaster02`) was successfully executed to $u_2 = 0.0050\,\text{mm}$ (Exit Code 0, 741s wallclock). Physical extraction of companion visualizer elements established:
- **Peak damage**: $d_{\max} = 0.433304$ ahead of the notch tip at $(0.500883, 0.499610)$.
- **Core damage corridor ($d \ge 0.10$)**: Encloses exactly 753 elements spanning $X \in [0.4907, 0.7570]\,\text{mm}$ and $Y \in [0.4796, 0.6614]\,\text{mm}$.
- **Physical Trajectory**: This corridor curves directly from the notch tip $(0.50, 0.50)$ along the ligament toward the lower-left flank of the off-axis hole $(0.65, 0.65)$, definitively proving the physical crack-path refinement corridor without guessing.
- **Transition envelope ($d \ge 0.05 + 3\ell_0$)**: Encloses $X \in [0.450, 0.820]\,\text{mm}$ and $Y \in [0.430, 0.730]\,\text{mm}$.

---

## 2. Multi-Indicator Adaptive Refinement Formulation

Using these empirical facts, the Method A adaptive refinement criteria are defined as an objective three-tier spatial hierarchy:

1. **Tier 1: Core Fracture Process Zone (FPZ)**
   - *Indicator Definition*: Domain bounding all elements where $d(x,y) \ge d_{\text{core}} = 0.10$ plus a protective $2\ell_0$ margin:
     $$\Omega_{\text{core}} = [0.485, 0.770] \times [0.470, 0.680]\,\text{mm} \setminus \mathcal{B}_{\text{hole}}$$
   - *Target Element Size*: $h_{\text{core}} \le \ell_0 / 5 = 1.5\,\mu\text{m}$.
   - *Applied Boundary Seeding*: $h_{\text{seed,core}} = 0.00095\,\text{mm} = 0.95\,\mu\text{m}$.
   - *Governing Requirement*: Median edge $h_{\text{median}} \le 1.20\,\mu\text{m}$ and $\ge 85\%$ of edges $\le 1.5\,\mu\text{m}$.

2. **Tier 2: Intermediate Transition Buffer**
   - *Indicator Definition*: Domain bounding the $d(x,y) \ge 0.05$ diffuse damage envelope plus $3\ell_0$ buffer:
     $$\Omega_{\text{trans}} = [0.450, 0.820] \times [0.430, 0.730]\,\text{mm} \setminus \Omega_{\text{core}}$$
   - *Target Element Size*: $h_{\text{trans}} \approx 3.0\,\mu\text{m} - 5.0\,\mu\text{m}$.
   - *Applied Boundary Seeding*: $h_{\text{seed,trans}} = 0.0030\,\text{mm} = 3.0\,\mu\text{m}$.
   - *Purpose*: Provides smooth advancing-front paving growth from the fine $0.95\,\mu\text{m}$ core to the coarse bulk, preventing element distortion.

3. **Tier 3: Remote Far-Field Bulk**
   - *Indicator Definition*: Remainder of the plate $\Omega \setminus (\Omega_{\text{core}} \cup \Omega_{\text{trans}})$.
   - *Applied Seeding*: $h_{\text{bulk}} = 0.020\,\text{mm} = 20.0\,\mu\text{m}$.
   - *Purpose*: Maintains computational efficiency for elastic regions where damage $d \ll 0.01$.

---

## 3. Quantitative Mesh Quality & Resolution Synthesis

The candidate adapted physical mesh `PK_HOLE_METHOD_A_ADAPT_PHYS.inp` was generated via `scripts/remeshing/generate_method_a_hole_adapted_mesh.py` and evaluated using `scripts/remeshing/analyze_local_fpz_resolution.py`.

### Local FPZ Resolution Comparison

| Metric | Reference Pilot Mesh (Pkg 176) | Rejected Native 1% Mesh (F1641) | **Qualified Adapted Mesh (F1643)** | Scientific Target ($\ell_0 = 7.5\,\mu\text{m}$) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Total Physical Elements** | 46,747 | 130,435 | **52,447** | $40\text{k} - 70\text{k}$ ($\le 150\text{k}$) | **PASS** |
| **Physical Nodes** | 46,651 | 129,657 | **51,957** | — | **PASS** |
| **Quads / Triangles** | 45,541 / 1,206 | 127,783 / 2,652 | **50,716 / 1,731** | Quad-dominated ($>96\%$ quads) | **PASS** |
| **Co-located UEL Elements** | 140,241 | 391,305 | **157,341** | $3 \times N_{\text{phys}}$ | **PASS** |
| **Notch Tip Median Edge** | $1.7081\,\mu\text{m}$ | $1.8637\,\mu\text{m}$ | **$1.1743\,\mu\text{m}$** | $\le 1.50\,\mu\text{m}$ ($h/\ell_0 \le 0.20$) | **PASS ($h/\ell_0 = 0.157$)** |
| **Notch Tip Edges $\le \ell_0/5$** | $22.8\%$ | $5.28\%$ | **$89.4\%$** | $\ge 80.0\%$ | **PASS (+66.6% vs pilot)** |
| **Ligament Median Edge** | $1.6510\,\mu\text{m}$ | $1.7920\,\mu\text{m}$ | **$1.1953\,\mu\text{m}$** | $\le 1.50\,\mu\text{m}$ ($h/\ell_0 \le 0.20$) | **PASS ($h/\ell_0 = 0.159$)** |
| **Ligament Edges $\le \ell_0/5$** | $30.1\%$ | $8.12\%$ | **$90.6\%$** | $\ge 80.0\%$ | **PASS (+60.5% vs pilot)** |
| **Hole Boundary Median Edge**| $1.9876\,\mu\text{m}$ | $1.8150\,\mu\text{m}$ | **$1.1779\,\mu\text{m}$** | $\le 1.50\,\mu\text{m}$ ($h/\ell_0 \le 0.20$) | **PASS ($h/\ell_0 = 0.157$)** |
| **Hole Boundary Edges $\le \ell_0/5$**| $0.8\%$ | $6.45\%$ | **$86.3\%$** | $\ge 80.0\%$ | **PASS (+85.5% vs pilot)** |
| **Negative Area Elements** | 0 | 0 | **0** | Exactly 0 (No inverted elements) | **PASS** |

### Key Scientific Observations:
1. **Resolution Breakthrough**: The adapted mesh achieves **$89.4\%$** tip resolution, **$90.6\%$** ligament resolution, and **$86.3\%$** hole boundary resolution $\le 1.5\,\mu\text{m}$, with median edge lengths $1.17 - 1.20\,\mu\text{m}$ ($h/\ell_0 \approx 0.157 - 0.159$).
2. **Computational Economy**: At 52,447 elements, the mesh is only $12.2\%$ larger than the unrefined pilot mesh (46,747 elements), yet delivers nearly **$4\times$** the local resolution in the fracture corridor while avoiding the 130k element explosion of global remeshing.
3. **Jacobian Integrity**: Analysis of all 52,447 elements confirms strictly positive signed areas (min area $6.186 \times 10^{-10}\,\text{mm}^2$, max area $6.063 \times 10^{-4}\,\text{mm}^2$), with zero distorted or inverted elements.

---

## 4. Production Deck Architecture & Subroutine Compatibility

The 3-layer production deck `PK_HOLE_METHOD_A_ADAPT.inp` was constructed to maintain bitwise compatibility with frozen subroutine `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`):

1. **Element Layering & Numbering**:
   - Layer 1 (Phase-Field): Elements $1 \dots 50,716$ (Type `U1`) and $50,717 \dots 52,447$ (Type `U3`), active in DOF 3.
   - Layer 2 (Displacement): Elements $52,448 \dots 103,163$ (Type `U2`) and $103,164 \dots 104,894$ (Type `U4`), active in DOFs 1 & 2.
   - Layer 3 (Visualization): Elements $104,895 \dots 155,610$ (Type `CPE4`) and $155,611 \dots 157,341$ (Type `CPE3`), dummy UMAT.
2. **Subroutine Constant Parity**:
   - In `f42_mixed_uel.for`:
     - `PROPS(6)` in `*UEL PROPERTY` sets the physical element offset parameter:
       `0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 52447.0`
     - Third constant in `*USER MATERIAL, CONSTANTS=3` sets `NPHYS_VAL`:
       `210.0, 0.3, 52447.0`
     - Subroutine calculation `PHYSIDX = NOEL - 2 * NPHYS_VAL` yields exactly the physical element index $1 \dots 52,447$ for Layer 3 companion elements.
3. **Capacity Safety**:
   - In `f42_mixed_uel.for`, line 65 sets `PARAMETER(N_CAPACITY=150000)`.
   - The adapted physical element count is $N_{\text{phys}} = 52,447 \ll 150,000$. Array bounds are strictly satisfied with zero overflow risk.
4. **Card Limits**:
   - All `*NSET` definitions (`N_BOTTOM`, `N_TOP`) are wrapped at $\le 16$ items per line, strictly complying with the Abaqus input card limit.
5. **Coupled Boundary Conditions**:
   - Rigid tensile displacement tied to Reference Point `N_RP` (999999) via `*EQUATION`.
   - Roller support on `N_BOTTOM` ($u_y = 0$), pin on `N_PIN` ($u_x = 0$).

---

## 5. Authentic HPC Datacheck Verification

An interactive technical datacheck was executed directly on cluster `mmaster02` (`mlogin01.cluster`) using Intel Fortran 2024.2.0 and Abaqus 2023:
- **Command**: `abaqus job=PK_HOLE_METHOD_A_ADAPT_DC input=PK_HOLE_METHOD_A_ADAPT.inp user=f42_mixed_uel.for cpus=1 datacheck interactive`
- **Result**: **`Abaqus JOB PK_HOLE_METHOD_A_ADAPT_DC COMPLETED`** (Exit Code 0).
- **Solver Output (`PK_HOLE_METHOD_A_ADAPT_DC.dat`)**:
  - `ANALYSIS DATACHECK COMPLETE WITH 9 WARNING MESSAGES ON THE DAT FILE` (standard UEL degree of freedom notices).
  - Floating point operations per iteration: $1.04 \times 10^{10}$ FLOPs.
  - Estimated memory to minimize I/O: **406 MB** (well within the 16 GB job limit).
  - Total datacheck walltime: **6 seconds** (CPU time: 3.5s).
- **Subroutine Compilation**: `ifort` compiled `uel_` and `umat_` with automatic CPU dispatch remarks; zero syntax or interface errors.

---

## 6. Unit Test Verification

Automated test suite `tests/unit/test_f1643_hole_adaptive_mesh.py` was executed with pytest:
- `test_deck_files_exist_and_nonempty`: **PASS**
- `test_element_and_node_counts_within_capacity`: **PASS** ($52,447 \le 150,000$)
- `test_local_fpz_resolution_criteria`: **PASS** (Notch tip 89.4%, Ligament 90.6%, Hole 86.3%)
- `test_positive_element_areas`: **PASS** (0 inverted elements)
- `test_geometry_and_boundary_sets`: **PASS** (Geometry exact)
- `test_production_deck_structure_and_constants`: **PASS** (Card limits & constant parity verified)

Regression suite `tests/unit/test_f1642_pilot_physical_state.py` also evaluated: **6/6 PASS**.  
**Total test score: 12 / 12 PASS (100%)**.

---

## 7. Artifact Provenance & Hashes

| Artifact Description | Path | SHA-256 Digest | Size (bytes) |
| :--- | :--- | :--- | ---: |
| Adapted Physical Mesh Deck | `models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_ADAPT_PHYS.inp` | `36AA6E67560A7552B1192160F89A5644E24F76DD422EB560C2D80FACF2C75BCE` | 3,736,279 |
| Adapted 3-Layer UEL Production Deck | `models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_ADAPT.inp` | `6910E62470765E6083C6AB48C4840F3BD99768CCD47EB99A3BC8C0020A2E73E1` | 7,511,703 |
| Adapted Mesh Generator Script | `scripts/remeshing/generate_method_a_hole_adapted_mesh.py` | `3ADA4DF9BAC7668E9EEB1A301299365ED4D949EB5BC8094645B31E00D478E055` | 21,934 |
| F1643 Unit Test Suite | `tests/unit/test_f1643_hole_adaptive_mesh.py` | `063F98426D784115B5831379E6EA4B63EF983E3F13B9387A94295DF846263849` | 8,600 |
| Authentic Abaqus 2023 Datacheck DAT | `results/validation/f1643_PK_HOLE_METHOD_A_ADAPT_DC.dat` | `8E79CAFF9F8CFEC74F852698AD67C2C8AC5CFA562FED527ECD89B85E0C29E7D0` | 14,405 |
| Authentic Abaqus 2023 Datacheck MSG | `results/validation/f1643_PK_HOLE_METHOD_A_ADAPT_DC.msg` | `2AEC59E5625724F0AA6132AFCB1F9906CC2AB4824374DA1D2629D56C21AFB5F9` | 1,423 |

---

## 8. Conclusion & Execution Recommendation

Task **F1643** has completely succeeded:
1. The indicator-driven refinement criteria have been rigorously established by coupling the authentic physical phase-field damage corridor from Job 1421048 with the benchmark continuum stress gradients.
2. The candidate adapted mesh resolves the fracture process zone with unprecedented fidelity ($h_{\text{median}} \approx 1.18\,\mu\text{m}$, $>86-90\%$ of edges $\le \ell_0/5$), eliminating the resolution shortfall of both the pilot mesh (23-30%) and the rejected native remesh (5%).
3. The production deck is 100% verified and compiled with Exit Code 0 under Abaqus 2023 on the TU Freiberg cluster.

**Recommended Next Step:**
Close Task F1643 and register successor Task **`F1644-METHOD-A-HOLE-ADAPTED-SOLVE`** to submit the qualified adapted simulation `PK_HOLE_METHOD_A_ADAPT` to the cluster via `scripts/hpc/Invoke-Mode1Execution.ps1`.

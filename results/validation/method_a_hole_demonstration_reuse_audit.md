# Method A Reuse and Implementation Audit: Parameterized Hole Demonstration

**Audit Date:** 6 November 2026  
**Supervisor Directive Reference:** Dr. Roth (6 November 2026, via ChatGPT Bridge `HND-bef847fc363a`)  
**New Primary Priority:** Mode-I Plate with Off-Axis Circular Hole using Method A (Native Adaptive Remeshing)  
**Historical Authority Job:** `1400395.mmaster02` (`models/pandey_kumar_mode1/06_production_adaptive_2pct/`)  

---

## 1. Exact Successful Files, Manifests, and Git Provenance of Job 1400395

Job `1400395.mmaster02` is the established, published project anchor for Method A (Abaqus native adaptive remeshing using the `MISESERI` error indicator):
- **Directory Path:** `models/pandey_kumar_mode1/06_production_adaptive_2pct/`
- **Physical Discretization:** 15,396 elements (14,963 Quad4 / 97.19%, 433 Tri3 / 2.81%), 15,414 nodes.
- **Total Co-located Discretization:** 46,188 elements across 3 layers (Layer 1: Phase UEL U1/U3; Layer 2: Mechanical UEL U2/U4; Layer 3: Companion UMAT CPE4/CPE3).
- **Execution & Convergence:** Serial execution on `mnode097`, walltime 07:06:46, 7,028 increments, **0 cutbacks**, normal termination (Exit 0).
- **Quantitative Mechanical Fidelity:** Peak reaction force $F_{\text{peak}} = 0.7482\text{ kN}$ ($-1.29\%$ deviation from published reference $0.7580\text{ kN}$), displacement at peak $u_{\text{peak}} = 0.00578\text{ mm}$ ($-1.45\%$), elastic stiffness $K_0 = 137.84\text{ kN/mm}$ ($-0.08\%$).
- **Primary Generator Script:** `models/pandey_kumar_mode1/06_production_adaptive_2pct/scripts/generate_task5_production_package.py`
- **Core Abaqus Workflow Implementation:** `models/pandey_kumar_mode1/88_mode1_preanalysis_uel_corrected/execute_mode1_native_adaptive_remesh.py` and `build_adapted_job2_production_deck.py`
- **Subroutine Master:** `models/pandey_kumar_mode1/06_production_adaptive_2pct/fortran/f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`, 29,722 bytes).

---

## 2. Components That Can Be Reused Completely Unchanged

1. **Production User Subroutine (`f42_mixed_uel.for`):**
   - Implements both 2D Quad4 elements (U1 phase, U2 displacement) and Tri3 elements (U3 phase, U4 displacement).
   - Fully qualified for mixed unstructured meshes containing both quads and triangles produced by Abaqus free meshing around curved geometry.
   - Built-in companion UMAT visualization bridge writing $d$ to $\text{SDV}(15)$ and $\mathcal{H}$ to $\text{SDV}(16)$ for direct CAE/ODB rendering.
2. **Layered UEL Production Deck Assembly Logic (`generate_task5_production_uel_deck`):**
   - Multi-layer element generator: duplicates physical mesh into Phase UEL (Layer 1), Mechanical UEL (Layer 2), and Dummy UMAT (Layer 3).
   - Automatic assignment of U1/U2 for quads and U3/U4 for triangles.
   - Material parameters: $E = 210.0\text{ kN/mm}^2$, $\nu = 0.3$, $G_c = 0.0027\text{ kN/mm}$, $\ell_0 = 0.0075\text{ mm}$, $\eta = 10^{-7}\text{ kN}\cdot\text{s/mm}^2$.
3. **Adaptive Remeshing Rule Specification:**
   - Error indicator: `MISESERI` (recovery-based stress error indicator).
   - `sizingMethod = UNIFORM_ERROR`, `errorTarget = 0.02` ($2\%$), `refinementFactor = 10`, `coarseningFactor = NOT_ALLOWED`.
   - Bounded mesh sizes: $h_{\min} = 0.001\text{ mm}$ ($1\,\mu\text{m} \approx \ell_0 / 7.5$), $h_{\max} = 0.02\text{ mm}$.
4. **HPC Execution Directives & Notification Harness:**
   - Guarded PBS submission wrappers with dual-channel notification (`job_notifications.sh`).

---

## 3. Minimum Required Changes for Parameterized Off-Axis Hole

To preserve general applicability and eliminate hard-coded geometry assumptions:
1. **Parameterized Geometric Sketching:**
   - Parameterize outer plate dimensions ($W, H$).
   - Parameterize horizontal initial crack ($a_0 = 0.5\text{ mm}$, $y_{\text{notch}} = 0.5\text{ mm}$, notch opening width $2w = 0.002\text{ mm}$).
   - Parameterize circular hole geometry:
     - Center coordinates $(x_{\text{hole}}, y_{\text{hole}})$ where $x_{\text{hole}} > a_0$ (e.g. $x_{\text{hole}} \in [0.60, 0.75]\text{ mm}$) and $y_{\text{hole}} \ne y_{\text{notch}}$ (e.g. $y_{\text{hole}} \in [0.60, 0.70]\text{ mm}$ above the crack line).
     - Hole radius $R_{\text{hole}}$ (e.g. $R_{\text{hole}} \in [0.05, 0.15]\text{ mm}$).
2. **Generic Boundary Node Set Detection:**
   - Replace hard-coded coordinate tolerances with geometric bounding box / coordinate filter functions:
     - `BottomNodes`: all nodes with $y \le y_{\min} + \epsilon_{\text{geom}}$.
     - `TopNodes`: all nodes with $y \ge y_{\max} - \epsilon_{\text{geom}}$.
     - `PinNode`: node closest to $(x_{\text{pin}}, y_{\min})$.
     - Top tensile pull equation tying all `TopNodes` to a master Reference Point.
3. **Unstructured Mesh Generation Around Hole:**
   - Apply Abaqus Free Mesher (`algorithm = ADVANCING_FRONT`, `elemType = QUAD_DOMINATED`) to smoothly conform to the circular hole boundary and crack tip.
   - The existing deck builder already parses and handles mixed quad and tri element blocks (`quad_elems` and `tri_elems`).

---

## 4. Formulation & Boundary Condition Considerations for Curved Crack Paths

1. **Constitutive Formulation Applicability:**
   - In Mode-I straight propagation, normal tensile opening dominates ($I_1 > 0$, $\varepsilon_2 \approx 0$).
   - As the crack deflects toward an off-axis hole, the local crack tip experiences mixed Mode I + II loading.
   - The production UEL (`f42_mixed_uel.for`) uses the spectral volumetric/deviatoric split (Miehe et al. / Amor et al. formulation), which naturally accommodates shear strain components $\varepsilon_{12}$ in the positive strain energy $\psi_e^+(\boldsymbol{\varepsilon})$.
   - The scalar phase field $d \in [0, 1]$ naturally tracks arbitrary curved crack trajectories without requiring directional tracking algorithms or remeshing state transfers.
2. **Crack Attraction Mechanism:**
   - The circular hole creates a stress concentration zone under tensile loading ($\sigma_{yy} \approx 3\sigma_0$ at the lateral equator of the hole).
   - As the crack propagates from $x = 0.5\text{ mm}$, the interaction between the crack-tip stress singularity and the hole stress concentration curves the trajectory toward the hole (comparable to Pandey & Kumar 2025 Figures 14–16).

---

## 5. Minimum Qualified Simulation Set for Demonstration

1. **Case 1: Standard Coarse Fixed Mesh:**
   - Parameterized plate with hole meshed uniformly ($h \approx 0.02\text{ mm}$, $\approx 3{,}000$ elements).
   - Baseline reference demonstrating diffuse crack path or poor resolution.
2. **Case 2: Method A Adapted Refined Mesh (Target Demonstration):**
   - Pass 1: Elastic pre-analysis with `MISESERI` field output.
   - Pass 2: Adaptive remeshing (`errorTarget = 2.0%`, $h_{\min} = 0.001\text{ mm}$).
   - Fracture Solve: Full phase-field crack propagation demonstrating sharp crack initiation, smooth deflection, and attraction into the hole.
3. **Optional Case 3 (Sensitivity / Nominal Comparison):**
   - Adapted mesh at `errorTarget = 1.0%` or alternative hole offset if capacity permits.

---

## 6. Practical Action Sequence to Produce Deliverables Rapidly

1. **Step 1 (Offline / Local): Parameterized CAE Geometry & Remesher Script**
   - Create `scripts/remeshing/generate_plate_with_hole_method_a.py`.
   - Include standalone CLI arguments: `--plate-w`, `--plate-h`, `--notch-a`, `--hole-x`, `--hole-y`, `--hole-r`, `--error-target`.
2. **Step 2 (Local Preflight): Geometry & Pre-Analysis Verification**
   - Run Abaqus CAE in batch mode (`abaqus cae noGUI=...`) to verify sketch, part generation, coarse mesh, pre-analysis solve, and adaptive remesh execution.
   - Inspect generated adapted mesh: verify refinement density around both the crack tip and the hole boundary.
3. **Step 3 (Local Unit & Regression Tests):**
   - Verify deck builder output: node sets, UEL cards, equation constraints, companion visualization UMAT elements.
4. **Step 4 (HPC Preflight & Submission):**
   - Package into a self-contained production directory `models/pandey_kumar_mode1/176_method_a_plate_with_hole/`.
   - Run technical datacheck on cluster via guarded wrapper.
   - Submit qualified fracture simulation via `Invoke-Mode1Execution.ps1`.
5. **Step 5 (Post-Processing & Visualization Package):**
   - Extract force–displacement curve ($RF_2$ vs $U_2$).
   - Extract damage field snapshots showing crack path deflection.
   - Generate comparison figures and presentation slides for Dr. Roth.

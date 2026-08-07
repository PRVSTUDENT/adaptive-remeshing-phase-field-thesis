# F42A Mixed Triangle-Quadrilateral UEL Architecture Foundation Report

Date: 2026-08-07  
Agent: Gemini Antigravity  
Status: `complete`  
Classification: `f42a_mixed_element_uel_architecture_foundation_complete`  
Next Action: `prepare_one_triangle_element_verification_without_submission`  

---

## 1. F41R6 Closeout & Remote GitHub Push

- **Local F41R6 Commit**: `fda937c7a1a116de30b2709998ab44c18c1adaef`
- **Pushed to GitHub `origin/main`**: Pushed cleanly. `git rev-parse origin/main` verified as `fda937c7a1a116de30b2709998ab44c18c1adaef`.
- **HPC Clone**: Ready to fast-forward. No `qsub` or job submissions executed.

---

## 2. Frozen F41 Scientific Results

- **A. Geometry Pipeline (Validated in Abaqus/CAE 2023)**:
  - 15 coincident crack node pairs detected and merged.
  - `Part2DGeomFrom2DMesh` created valid, usable geometry.
  - Crack partition recreated at exact coordinates ($[-0.5, 0.0] \rightarrow [0.0, 0.0]$).
  - Seam assigned successfully.
  - Crack coordinates, crack tip, and outer boundaries preserved 100%.
- **B. Element Contract (Identified)**:
  - Existing production UEL subroutines are quadrilateral-only ($NNODE=4$, $CPE4$).
  - Abaqus 2D native adaptive remeshing generates mixed triangle/quad meshes (`CPE3`/`CPE4`).
  - Classification: `f41_geometry_reconstruction_validated_current_uel_mixed_element_incompatible`.

---

## 3. Pandey & Kumar (2025) Literature & Source Audit

- **Paper Title**: *A Simple and Robust Mesh Refinement Implementation in Abaqus for Phase Field Modelling of Brittle Fracture* (CMES 2025).
- **Verbatim Evidence**:
  - Section 3 (p. 3260): *"In the adopted layered approach, 3-node and 4-node user elements are defined in the input file."*
  - Section 3.3 (p. 3262–3263): Details parsing `Job-1.inp` to `Job-1_UEL.inp`, adaptive remeshing by Abaqus, registering the new refined mesh in `Job-2.inp`, and rebuilding `Job-2_UEL.inp`.
  - Section 4 (p. 3275): L-panel test uses 55,625 non-uniform linear triangular and quadrilateral elements.
- **Reference [72] Identity**: Molnár G, Gravouil A. *2D and 3D Abaqus implementation of a robust staggered phase-field solution for modeling brittle fracture.* Finite Elem Anal Des. 2017;130:27–38.
- **Source Code Status**: The published PDF does not provide the Fortran UEL source code for the 3-node triangular user element. The existing workspace repository contains only 4-node quad UEL subroutines.

---

## 4. Option A Implementation & Architecture Design

### Mixed Element Type Contract
- `U11`: 4-node Phase Field UEL ($nodes=4$)
- `U12`: 4-node Displacement UEL ($nodes=4$)
- `U21`: 3-node Phase Field UEL ($nodes=3$)
- `U22`: 3-node Displacement UEL ($nodes=3$)
- `CPE4`: 4-node Facsimile Layer
- `CPE3`: 3-node Facsimile Layer

### 3-Node Linear Triangle Formulation (`SHAPEFUN_TRI`)
- Natural coordinates $L_1 = 1 - \xi - \eta, L_2 = \xi, L_3 = \eta$.
- Constant shape function derivatives:
  $$\frac{\partial N_1}{\partial \xi} = -1, \frac{\partial N_1}{\partial \eta} = -1, \quad \frac{\partial N_2}{\partial \xi} = +1, \frac{\partial N_2}{\partial \eta} = 0, \quad \frac{\partial N_3}{\partial \xi} = 0, \frac{\partial N_3}{\partial \eta} = +1$$
- Constant $2 \times 2$ Jacobian $\mathbf{J}$ with $\det(\mathbf{J}) = 2 A_e > 0$.
- 1-point centroidal quadrature $(\xi=1/3, \eta=1/3, w=0.5 \det(\mathbf{J}) t = A_e t)$.

### State Storage Scheme
- `COMMON/KUSER/USRVAR(N_ELEM, NSTV, 4)` retained.
- Quads use slots `NPT = 1..4`. Triangles use slot `NPT = 1` (slots 2..4 unused/zeroed).
- Quad memory layout 100% backward compatible.

### Input Deck Rebuilder (`f42_deck_rebuilder.py`)
- Parses `Job-2.inp` from Abaqus adaptive remeshing.
- Classifies elements as `CPE4` (4 nodes) vs `CPE3` (3 nodes).
- Rejects non-positive area elements or invalid node counts.
- Generates `Job-2_UEL.inp` containing `U11`, `U12`, `U21`, `U22`, `CPE4`, `CPE3`, `All_elem`, and `umatelem` sets.

---

## 5. Offline Test Results

- **`test_stage_f42_mixed_uel.py`**: **8/8 unit tests passed** (partition of unity, constant field reproduction, linear field reproduction, positive Jacobian determinant, B-matrix dimensions, stiffness/residual dimensions, deck rebuilder classification, non-positive area element rejection).
- **`test_stage_f41_batch.py`**: **21/21 unit tests passed** (quad topology regression suite).
- **`test_stage_f40_batch.py`**: **35/35 unit tests passed** (F40 framework regression suite).
- **Total Test Suite Executed**: **64/64 unit tests passed** (35 F40 + 21 F41 + 8 F42).

---

## 6. Authority & Next Action

- **Authority Flags**: All default-closed (`execution_authorized = false`, `submission_approved = false`, `maximum_jobs_now = 0`, `maximum_future_submissions = 0`, `retry_authorized = false`, `replacement_authorized = false`, `automatic_retry = false`).
- **Next Smallest Verification Job**: Prepare a standalone 1-element `CPE3`-equivalent triangular UEL verification package offline without submission (`prepare_one_triangle_element_verification_without_submission`).

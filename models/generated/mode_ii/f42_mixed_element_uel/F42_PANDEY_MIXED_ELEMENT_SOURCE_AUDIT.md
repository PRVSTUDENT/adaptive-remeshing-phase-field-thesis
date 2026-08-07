# F42 Pandey-Kumar Mixed-Element Source & Literature Audit Report

Date: 2026-08-07  
Agent: Gemini Antigravity  
Status: `complete`  
Classification: `triangle_uel_reference_implementation_not_yet_resolved`  

---

## 1. Executive Summary

This audit evaluates the literature and source code basis for implementing mixed 3-node triangular (`CPE3`/`CPS3`) and 4-node quadrilateral (`CPE4`/`CPS4`) phase-field user elements in Abaqus, following **Option A** (mixed element architecture).

The primary reference paper—**Pandey & Kumar (2025)** (*Computer Modeling in Engineering & Sciences*, Vol. 144, No. 3, pp. 3255–3288)—explicitly confirms that their layered adaptive remeshing implementation defines **both 3-node and 4-node user elements** in the input deck, and processes non-uniform meshes containing both linear triangular and quadrilateral elements (e.g. 55,625 elements in their L-panel benchmark).

However, the published paper does not include the Fortran source code for the 3-node triangular UEL ($NNODE=3$). Reference `[72]` in their bibliography points to **Molnár & Gravouil (2017)**, which provides the 4-node quadrilateral UEL foundation. No 3-node triangular Fortran UEL implementation currently exists in the repository.

---

## 2. Faithfully Extracted Evidence from Pandey & Kumar (2025)

| Topic | Verbatim Literature Evidence | Extraction Provenance |
|---|---|---|
| **Layered UEL & Subroutines** | *"In the current finite element study, we have utilized the UEL and UMAT subroutines for numerical evaluation and post-processing [72]. In the adopted layered approach, 3-node and 4-node user elements are defined in the input file."* | Section 3, Page 3260 |
| **Layer Structure** | *"The Python script extracts the element connectivity and nodal data from ‘Job-1.inp’. It then generates a modified input file—‘Job-1_UEL.inp’, which defines the layered system comprising user elements U1 & U2 (phase-field approximation), U3 & U4 (displacement approximation) and another layer for post-processing results, as documented in the literature [72]."* | Section 3.3, Page 3262–3263 |
| **Adaptive Remesh Connectivity Re-reading** | *"Abaqus utilizes its inherent refinement routines and the new refined mesh is registered. A new input file—‘Job-2.inp’ is again generated with the refined mesh data. Now, as we have obtained a refined mesh, a new input file ‘Job-2_UEL.inp’ is created and submitted along with the Fortran subroutine for numerical simulations."* | Section 3.3, Page 3263 |
| **Mixed Triangular & Quad Mesh Evidence** | *"The whole domain is discretized with a non-uniform mesh consisting of 55,625 linear triangular and quadrilateral elements."* | Section 4 (L-panel test), Page 3275 |
| **Reference [72] Identity** | `[72] Molnár G, Gravouil A. 2D and 3D Abaqus implementation of a robust staggered phase-field solution for modeling brittle fracture. Finite Elem Anal Des. 2017;130:27–38.` | Bibliography, Page 3284 |

---

## 3. Explicit Distinction of Facts vs Inferences

### A. Paper Explicitly States:
1. Both 3-node and 4-node user elements are defined in the input file.
2. The layered scheme uses $U1$ & $U2$ for phase-field, $U3$ & $U4$ for displacement, and a facsimile layer (`umatelem` / `All_elem`) for UMAT post-processing and MISESERI error indicators.
3. Adaptive remeshing generates `Job-2.inp` with mixed `CPE3` and `CPE4` elements.
4. Python script parses `Job-2.inp` and builds `Job-2_UEL.inp` with corresponding 3-node and 4-node UEL layers.

### B. Existing Repository Source Code Explicitly Implements:
1. **Quadrilateral-Only 4-Node UEL**: `SingleNotch_v2.for`, `SingleNotch.for`, and `M2IRR_F13.for` hardcode $NNODE=4$, 4 bilinear shape functions $AN(1..4)$, 4 Gauss integration points ($2 \times 2$), and `USRVAR(N_ELEM, NSTV, 4)`.
2. **Quadrilateral-Only Layer Rebuilder**: Input deck generators (`build_mode_ii_miseseri_preanalysis.py`, `build_stage_f13_packages.py`, `run_stage_f9_datacheck_matrix.py`) parse and construct 4-node connectivity lines for every element.
3. **No 3-Node Triangular Code**: Zero 3-node triangular UEL Fortran routines or 3-node layer builders exist in the repository.

### C. Our Inferred Requirements for Option A:
1. We must formulate a 3-node linear triangular user element ($NNODE=3$) for phase-field ($U1_{tri}$) and displacement ($U2_{tri}$) layers.
2. We must select the integration rule for the 3-node triangle (1-point centroidal vs 3-point Gauss rule).
3. We must extend state-variable storage (`USRVAR`) to handle elements with 1, 3, or 4 integration points without corrupting array bounds or state indexing.
4. We must build an offline deck parser/rebuilder that reads remeshed connectivity, identifies `CPE4` vs `CPE3`, and outputs matching 4-node and 3-node UEL blocks.

---

## 4. Availability of 3-Node UEL Reference Code

- **Search Result**: Searching the repository, local literature folder (`Literature review/`), and author-supplied files confirms that the exact 3-node Fortran UEL source code used by Pandey & Kumar is **not present in the local codebase**.
- **Reference [72]**: Points to Molnár & Gravouil (2017), which provides 4-node quad elements (2D bilinear) and 8-node brick elements (3D trilinear).
- **Classification**: `triangle_uel_reference_implementation_not_yet_resolved` (Formulation mapping established; 3-node Fortran UEL to be implemented and verified offline).

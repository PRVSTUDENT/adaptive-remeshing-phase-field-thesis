# F41R6 Adaptive-Remeshing Element Compatibility Decision Gate Report

Date: 2026-08-07  
Agent: Gemini Antigravity  
Status: `complete`  
Classification: `native_adaptive_remeshing_element_shape_incompatibility_requires_design_decision`  
Next Action: `resolve_triangle_vs_quad_production_element_contract_before_HPC`  

## 1. Production UEL & Model Pipeline Audit Summary

- **Production UEL Subroutines**: Fortran files (`SingleNotch_v2.for`, `M2IRR_F13.for`, `M2RTLOAD1.for`, `SingleNotch.for`) hardcode `NNODE = 4`, 4-node bilinear shape functions $AN(1..4)$, 4 Gauss integration points `XII(1..4, 1..2)`, and `COMMON/KUSER/USRVAR(N_ELEM, NSTV, 4)`. **No 3-node triangular shape functions ($L_1, L_2, L_3$) or 3-node UEL subroutines exist in the codebase.**
- **Layer & Input Deck Generators**: Hardcode 4-node connectivity for $U1$, $U2$, and $CPE4$ continuum visualization elements across all 3 layers (`build_mode_ii_miseseri_preanalysis.py`, `build_stage_f13_packages.py`, `build_d3a3_ingestion_hold.py`, `run_stage_f9_datacheck_matrix.py`).
- **Abaqus 2D Native Adaptive Remeshing**: Requires `TRI + FREE` or `QUAD_DOMINATED + FREE + ADVANCING_FRONT`. Pure `QUAD` is not supported for 2D native adaptivity.
- **Pandey & Kumar (2025) Findings**: Reference 2D adaptive remeshing generates mixed meshes containing linear triangular (`CPE3`) and quadrilateral (`CPE4`) elements.

## 2. Decision Gate Classification & Architectural Options

Because the production pipeline is strictly **quadrilateral-only**, branching under **CASE B** was triggered:

- **Classification**: `native_adaptive_remeshing_element_shape_incompatibility_requires_design_decision`
- **Architectural Options**:
  1. **Option A**: Add 3-node triangular UEL (`CPE3`, 3-node $U1$ & $U2$) and mixed layer support to the production pipeline.
  2. **Option B**: Introduce a post-remeshing triangle-to-quad conversion/rebuild stage after native remeshing.
  3. **Option C**: Abandon Abaqus native adaptive remeshing for this topology and use a custom all-quadrilateral refinement route.

**No scheduler job was prepared or submitted.**

## 3. Seam-After-Mesh Duplicate Node Validation Fix

- Removed the weak `hasattr(part.engineeringFeatures, "seams")` fallback.
- Implemented strict mesh node coordinate grouping along $x \in [-0.5, 0.0], y \approx 0$.
- Requires `seam_duplicate_coordinate_group_count > 0` and `crack_tip_mesh_node_present == True`.

## 4. Historical Evidence Working-Tree Safety

- Inspected HPC clone working tree for `runs/hpc/stage_f/f41_crack_geometry_reconstruction/evidence/1384642.mmaster02`.
- All 13 tracked evidence files are **100% present and clean against HEAD**.
- Recorded the temporary F41R5 `rm -rf` as a protocol deviation.

## 5. Offline Test Results

- `test_stage_f41_batch.py`: **21/21 passed**.
- `test_stage_f40_batch.py`: **35/35 passed**.
- `validate_f41_cae_reconstruction_gate.py`: **`F41_STATIC_GATE_PASSED`**.
- Authority flags: Default-closed (`false` and `0`). Session lock released (`active = false`).

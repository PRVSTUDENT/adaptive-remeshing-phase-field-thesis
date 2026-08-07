# F43REM1-R3 Geometry-Backed CAE Model Provenance & Architecture Decision Report

## Executive Summary

Job `1385376.mmaster02` verified that the CLI/environment-variable contract parsing error (`-cae` issue) was 100% resolved. However, execution inside Abaqus CAE exposed two core structural defects:

1. **False-Zero-Exit Defect**: Abaqus/PBS returned `Exit_status = 0` despite zero native remeshing operations being performed and no refined mesh deck being produced. This was caused by the unhandled default empty model `Model-1` in `run_f43_native_remesh_driver.py`, `|| true` exit-code masking in `F43REM1.pbs`, and `validate_f43rem1_runtime.py` evaluating `overall_validation_passed = True` merely if a dummy file existed on disk.
2. **Model Provenance Limitation**: Abaqus native adaptive remeshing requires a CAD geometry-backed CAE model part (with native B-Rep faces, edges, vertices, and sketch partitions). Importing `F43PRE1.inp` via `mdb.ModelFromInputFile` generates an **orphan-mesh part** (`Part-1`). Official Dassault Systèmes / Abaqus documentation explicitly dictates that **adaptive remeshing cannot be used with an orphan-mesh part**.

---

## 1. Empirical Evidence & False-Zero-Exit Repair

### Job 1385376 Evidence Preservation
- **PBS Job ID**: `1385376.mmaster02`
- **Predecessor ODB**: `1384674.mmaster02` (`F43PRE1.odb`, SHA256 `3a201a6d405b92f4588e3d7e68177797706fd80ca9fa541e36ed0b10fdfb0534`)
- **Environment Contract**: `PASS` (CLI sys.argv properly unwrapped via env vars)
- **Scientific Execution**: `NOT EXECUTED` (mdb.models['Model-1'] unavailable / empty)

### False-Zero-Exit Defect Root Cause & Fix
- **Root Cause**: In Abaqus CAE noGUI, `mdb.models['Model-1']` exists as an empty placeholder by default. Calling `RemeshingRule` and `Job.writeInput` on an empty model generated a dummy/empty file, which `validate_f43rem1_runtime.py` accepted as valid output because it only verified file presence.
- **Fix Implemented**:
  1. `run_f43_native_remesh_driver.py` enforces 14 mandatory scientific runtime success gates. If any gate fails (missing CAE, orphan mesh part, missing step, missing MISESERI, missing output deck), it raises `RuntimeError` and exits with code 1.
  2. Terminal success marker `F43REM1_RUNTIME_SUCCESS=true` is emitted ONLY after all mandatory gates pass.
  3. `validate_f43rem1_runtime.py` strictly checks for `F43REM1_RUNTIME_SUCCESS=true` in `execution.log` AND non-empty valid refined continuum element decks (`size > 100` bytes).
  4. `F43REM1.pbs` traps exit codes fail-closed (`ABAQUS_RC` and `VALIDATOR_RC`), exiting non-zero if either step fails.

---

## 2. Model Provenance Classification

Per project decision matrix:
- **Found `.cae` Files in Workspace**: 0
- **F43PRE1 Source Type**: Flat keyword solver input deck (`F43PRE1.inp`)
- **Imported Part Representation**: Orphan-mesh part (`Part-1`)
- **Abaqus Adaptive Remeshing Compatibility**: Incompatible with orphan mesh parts

### Final Classification:
**CASE C: `f43_no_geometry_backed_cae_source_available`** (and **CASE D: `f43_source_is_orphan_mesh_and_native_adaptive_remeshing_not_supported`**)

Under CASE B/C/D rules, **no runnable F43REM1_R3 package is prepared or submitted**.

---

## 3. Recommended Reconstruction Path

To enable Abaqus native adaptive remeshing for Phase-Field Mode-II benchmarks:

1. **Native Parametric CAE Geometry Builder**:
   - Construct a B-Rep geometry model using `ConstrainedSketch` and `Part2DGeomFrom2DMesh` or CAD sketch primitives ($0.5\text{ mm} \times 0.5\text{ mm}$ square plate with notch partition at $y=0, x \in [-0.5, 0.0]$).
   - Apply seam edge assignment to the crack line.
   - Assign adaptive-remeshing-compatible mesh controls (`QUAD/FREE/ADVANCING_FRONT` or `TRI/FREE`).
2. **CAD-Backed Analysis & Predecessor ODB**:
   - Run the initial coarse analysis from this CAD-backed CAE model to produce a predecessor ODB containing `MISESERI` discretization error indicators linked to true CAD geometry.
3. **Native Adaptive Remeshing Execution**:
   - Apply `mdb.models[<name>].RemeshingRule` targeting `MISESERI` on the geometry-backed CAE model using the predecessor ODB.

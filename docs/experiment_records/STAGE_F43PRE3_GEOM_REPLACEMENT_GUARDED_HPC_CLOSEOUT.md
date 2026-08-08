# STAGE F43PRE3_GEOM Replacement Guarded Remote HPC Execution Closeout Report

**Date**: 2026-08-08  
**Task ID**: `F43PRE3_GEOM` / `F43PRE3_GEOM_REPLACEMENT_SUBMISSION`  
**HPC Job ID**: `1385461.mmaster02`  
**Queue**: `entry_imfdfkmq` (routed to `normal_imfdfkmq`)  
**Status**: `complete_pass`  
**Classification**: `f43pre3_geom_preanalysis_solver_pass`  
**Cluster**: `tu_freiberg`  
**Compute Node**: `mnode098/0`  
**User Authorization**: Explicit human authorization in chat ("I authorize exactly one guarded replacement HPC submission of F43PRE3_GEOM using preparation commit b98ff859539e023f808926c6578c3d57a94c72c2...")  

---

## 1. Execution Package Hashes & Provenance

- **Preparation Commit ($P_{R3}$)**: `b98ff859539e023f808926c6578c3d57a94c72c2`
- **Qualification Commit ($Q_{R3}$)**: `6fdf2d98398f34b09c721d9256d309de127ad095`
- **Authorization Commit**: `86258ddbed9093bc77c646dcaa1820c5cdb347f2`
- **Input Deck (`F43PRE3_GEOM.inp`)**: SHA256 `10d4fb75cc97d92fbb1491361624e92f4cc4269ed40e4420164af28ed15207ee`
- **Source CAE (`ModeII_Geometry_Source_Abaqus2023.cae`)**: SHA256 `0d5b32fe48b70ed0817e8b9c439bfdb39165dee5e8d157fcb6d0b3075efe1baa`
- **Generated Output ODB (`F43PRE3_GEOM.odb`)**: SHA256 `9a5262931675d2780ccc8b6e6060dd20b817917df7cdf6e499a7a0a2d0d06eb1`

---

## 2. Working-Directory Contract & Execution Log Audit

- **Submission Execution**: Wrapper `submit_f43pre3_geom.sh` executed `cd "${SCRIPT_DIR}"` before calling `qsub`.
- **PBS Working Directory Verification**: `PBS_O_WORKDIR` resolved strictly to `/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/f43_stage_c_bridge`.
- **Pre-Solver Fail-Closed Checks**:
  - `F43PRE3_GEOM.inp` verified (`input_SHA = 10d4fb75cc97d92fbb1491361624e92f4cc4269ed40e4420164af28ed15207ee`).
  - Source CAE verified (`CAE_SHA = 0d5b32fe48b70ed0817e8b9c439bfdb39165dee5e8d157fcb6d0b3075efe1baa`).
  - Environment modules loaded cleanly (`gcc/11.4.0 intel/2024.2.0 abaqus/2023`).
- **Abaqus/Standard Solver Performance**:
  - Tokens checked out: 5 tokens from FlexNet server (`license4.imfd.tu-freiberg.de`).
  - Input File Processor completed cleanly (`Sat 08 Aug 2026 05:36:41 AM CEST`).
  - Solver completed 17 increments to step time 1.00 (`Sat 08 Aug 2026 05:36:46 AM CEST`).
  - Terminal exit status: `0` (`Abaqus solver finished with exit status 0`).
  - Collector execution: collector ran cleanly (`collector_rc = 0`).
- **Output Artifacts**: `F43PRE3_GEOM.odb` generated successfully (`9a5262931675d2780ccc8b6e6060dd20b817917df7cdf6e499a7a0a2d0d06eb1`).

---

## 3. Evidence Bundle

Evidence archived locally at `models/generated/mode_ii/f43_stage_c_bridge/evidence/1385461.mmaster02/`:
- `execution.log` (Full execution output)
- `F43PRE3_GEOM.sta` (Abaqus status file)
- `F43PRE3_GEOM.msg` (Abaqus message file)
- `F43PRE3_GEOM.dat` (Abaqus data file)
- `F43PRE3_SOURCE_MANIFEST.json`
- `F43PRE3_ACCEPTANCE_CRITERIA.json`
- `ODB_SHA256.txt`

---

## 4. Governance & Authority Reset

- **Consumed Submission**: Job `1385461.mmaster02` consumed the single authorized replacement submission attempt (`MAX_SUBMISSIONS=1`).
- **Reset State**:
  - `execution_authorized`: `false`
  - `submission_approved`: `false`
  - `maximum_jobs_now`: 0
  - `maximum_future_submissions`: 0
  - `automatic_retry`: `false`
  - `replacement_authorized`: `false`

---

## 5. Scientific Next Steps

1. Perform scientific ODB analysis of `1385461.mmaster02/F43PRE3_GEOM.odb` against reference target `1385392.mmaster02/F43PRE2_GEOM.odb`.
2. Verify load-displacement curve, MISESERI spatial distribution, and node/element set compatibility under Abaqus 2023.
3. Upon successful scientific evaluation, prepare native adaptive remeshing package `F43REM3_NATIVE` for offline qualification.

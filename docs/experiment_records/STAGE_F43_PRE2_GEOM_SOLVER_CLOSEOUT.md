# Stage F43: F43PRE2_GEOM Geometry-Backed Pre-Analysis Solver Execution Closeout

- **Task ID**: `F43PRE2_GEOM`
- **Stage**: `Stage C` / `F43`
- **HPC Job ID**: `1385392.mmaster02`
- **Queue / Host**: `entry_imfdfkmq` / `mnode098.cluster`
- **Status**: `complete_pass`
- **Classification**: `f43pre2_geom_preanalysis_solver_pass`
- **Preparation Commit ($P$)**: `b72174bada751f05bbf075963392a950f5580c3e`
- **Qualification Commit ($Q$)**: `43af99d756db401f1c6a84f95860521e176ab915`
- **Authorization Commit ($A$)**: `91e809be04ed2bb4ef1131c9a63cfc3db6f387fa`
- **Main Closeout Commit**: `efe93e60918a2d51d0cf2064a85f2ff9c525ce5a`

---

## 1. Objective & Lineage Contract

The goal of `F43PRE2_GEOM` was to execute a standard continuum `Abaqus/Standard` pre-analysis simulation built directly from the native CAD geometry `.cae` database (`ModeII_Geometry_Source.cae`). This job produces the geometry-backed baseline ODB (`F43PRE2_GEOM.odb`) required for subsequent native adaptive remeshing (`F43REM2_NATIVE`).

### Lineage Hashing & Contract Verification
- **Input Deck (`F43PRE2_GEOM.inp`)**: Git Blob `e17c145ba090b5e516eea4eecd1da9d8931bc1f1`, Linux checked-out SHA256 `83cf8afd2eee1bf14db84af0537714205cead2187fa6e5f06a774b60803422e5`.
- **CAE Source (`ModeII_Geometry_Source.cae`)**: Immutable SHA256 `889c15ba6621ae8435324473bb385cb0da6a62866dd8c996865806b876c051ff`.
- **Runtime Policy**: External source opened in place is strictly forbidden (`cae_source_open_in_place = false`). Scratch working copy contract enforced (`runtime_work_copy_required = true`).

---

## 2. HPC Scheduler & Resource Summary

| Field | Recorded Value |
| :--- | :--- |
| **PBS Job ID** | `1385392.mmaster02` |
| **Job Name** | `F43PRE2_GEOM` |
| **Queue** | `entry_imfdfkmq` |
| **Execution Vnode** | `mnode098[0]` |
| **PBS Exit Status** | `0` (Clean Exit) |
| **Abaqus Tokens** | 5 tokens checked out from `license4.imfd.tu-freiberg.de` |
| **Walltime Used** | `00:00:13` (Requested: `00:30:00`) |
| **CPU Time Used** | `00:00:07` |
| **Memory Used** | `445.3 MB` (Requested: `8 GB`) |

---

## 3. Solver Execution & Validation Results

The analysis ran to complete convergence:
- **Solver Engine**: `Abaqus/Standard 2023`
- **Increments Completed**: 17 increments
- **Step Completion**: Reached target step time $t = 1.00$ ($u_1 = 0.001\text{ mm}$ prescribed shear displacement)
- **Terminal Status**: `THE ANALYSIS HAS COMPLETED SUCCESSFULLY`
- **Output ODB**: `F43PRE2_GEOM.odb` (6,722,716 bytes, SHA256 `85339f45937cf5d2c57f169fa71b3e55f066082e6525aa3c20a370f058c4cf72`)
- **Validation Status (`F43PRE2_GEOM_VALIDATION_STATUS.json`)**:
  - `abaqus_input_processor_success`: `true`
  - `abaqus_standard_normal_completion`: `true`
  - `pbs_exit_status_zero`: `true`
  - `miseseri_output_configured`: `true`
  - `misesavg_output_configured`: `true`
  - `odb_evidence_generated`: `true`
  - `no_nan_or_inf`: `true`
  - `overall_validation_passed`: `true`

---

## 4. Evidence Package & Artifact Registry

Lightweight evidence files collected into local repository path `models/generated/mode_ii/f43_stage_c_bridge/evidence/1385392.mmaster02/`:
- [F43PRE2_GEOM.sta](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/f43_stage_c_bridge/evidence/1385392.mmaster02/F43PRE2_GEOM.sta) (Step time history & completion marker)
- [F43PRE2_GEOM.msg](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/f43_stage_c_bridge/evidence/1385392.mmaster02/F43PRE2_GEOM.msg) (Iteration summary)
- [F43PRE2_GEOM.dat](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/f43_stage_c_bridge/evidence/1385392.mmaster02/F43PRE2_GEOM.dat) (Printout & output requests)
- [execution.log](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/f43_stage_c_bridge/evidence/1385392.mmaster02/execution.log) (Job stdout/stderr log)
- [F43PRE2_GEOM_VALIDATION_STATUS.json](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/f43_stage_c_bridge/evidence/1385392.mmaster02/F43PRE2_GEOM_VALIDATION_STATUS.json) (Machine-readable validation results)
- [QSTAT_FINAL.txt](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/f43_stage_c_bridge/evidence/1385392.mmaster02/QSTAT_FINAL.txt) (Final qstat record)
- [TRACEJOB.txt](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/f43_stage_c_bridge/evidence/1385392.mmaster02/TRACEJOB.txt) (PBS tracejob record)

*Note: In accordance with project governance rules, `F43PRE2_GEOM.odb` remains scratch-only on HPC at `/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/f43_stage_c_bridge/evidence/1385392.mmaster02/F43PRE2_GEOM.odb` and is NOT committed to Git.*

---

## 5. Governance & Next Steps

1. **Authorization Consumption**: `execution_authorized = false`, `submission_approved = false`, `maximum_jobs_now = 0`.
2. **Decoupled Future Work**: Dependent task `F43REM2_NATIVE` is decoupled and remains unsubmitted.
3. **Next Scientific Action**: Perform field extraction (`MISESERI`, `S`, `U`, `RF`) from `F43PRE2_GEOM.odb` and execute scientific comparison against numerical baseline `1384674`.

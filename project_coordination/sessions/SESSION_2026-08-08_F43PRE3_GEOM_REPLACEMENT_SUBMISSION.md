# Session Report: F43PRE3_GEOM Replacement Guarded Remote HPC Submission

**Date**: 2026-08-08  
**Agent**: gemini-antigravity  
**Task ID**: F43PRE3_GEOM / F43PRE3_GEOM_REPLACEMENT_SUBMISSION  
**HPC Job ID**: `1385461.mmaster02`  
**Starting Commit**: `86258ddbed9093bc77c646dcaa1820c5cdb347f2`  
**Preparation Commit ($P$)**: `b98ff859539e023f808926c6578c3d57a94c72c2`  
**Qualification Commit ($Q$)**: `6fdf2d98398f34b09c721d9256d309de127ad095`  
**Status**: `complete_pass`  

---

## Executive Summary

Executed the single authorized guarded replacement remote HPC submission of `F43PRE3_GEOM` job `1385461.mmaster02` on cluster `tu_freiberg` under explicit human authorization. The pre-solver fail-closed working-directory contract verified package location `models/generated/mode_ii/f43_stage_c_bridge` and input/CAE SHAs. Abaqus/Standard solver completed all 17 increments to step time 1.00 (`Exit_status = 0`). Generated output ODB `F43PRE3_GEOM.odb` (SHA256 `9a5262931675d2780ccc8b6e6060dd20b817917df7cdf6e499a7a0a2d0d06eb1`). Downloaded evidence bundle locally and reset authority flags.

---

## 1. Authorization Sentence Verified

`"I authorize exactly one guarded replacement HPC submission of F43PRE3_GEOM using preparation commit b98ff859539e023f808926c6578c3d57a94c72c2 and qualification commit 6fdf2d98398f34b09c721d9256d309de127ad095, using F43PRE3_GEOM.inp with SHA256 10d4fb75cc97d92fbb1491361624e92f4cc4269ed40e4420164af28ed15207ee and the Abaqus-2023 geometry source CAE with SHA256 0d5b32fe48b70ed0817e8b9c439bfdb39165dee5e8d157fcb6d0b3075efe1baa, through entry_imfdfkmq with 1 CPU, 8 GB, and 30 minutes walltime, with MAX_SUBMISSIONS=1, no automatic retry, no further replacement submission, no F43REM3_NATIVE submission, no F43DRY1 submission, and no downstream job."`

---

## 2. Remote Submission & Execution Audit

1. **Pre-flight verification**: Input deck SHA `10d4fb75cc97d92fbb1491361624e92f4cc4269ed40e4420164af28ed15207ee`, CAE SHA `0d5b32fe48b70ed0817e8b9c439bfdb39165dee5e8d157fcb6d0b3075efe1baa`, `qstat` clean.
2. **Submission**: Executed `submit_f43pre3_geom.sh`. Returned PBS job ID `1385461.mmaster02`.
3. **Execution Host**: Compute node `mnode098/0`.
4. **Working Directory Verification**: `PBS_O_WORKDIR` resolved strictly to `/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/f43_stage_c_bridge`.
5. **Abaqus Solver Performance**: Checked out 5 licenses from FlexNet server `license4.imfd.tu-freiberg.de`. Solver completed step time 1.00 in 17 increments. Output ODB generated cleanly (`Exit_status = 0`).
6. **Collector Execution**: Evidence collector ran cleanly (`collector_rc = 0`).

---

## 3. Evidence & Verification Hashes

- `F43PRE3_GEOM.odb` SHA256: `9a5262931675d2780ccc8b6e6060dd20b817917df7cdf6e499a7a0a2d0d06eb1`
- Evidence directory: `models/generated/mode_ii/f43_stage_c_bridge/evidence/1385461.mmaster02/`
- Evidence files: `execution.log`, `F43PRE3_GEOM.sta`, `F43PRE3_GEOM.msg`, `F43PRE3_GEOM.dat`, `F43PRE3_SOURCE_MANIFEST.json`, `F43PRE3_ACCEPTANCE_CRITERIA.json`, `ODB_SHA256.txt`.

---

## 4. Current Governance State

- `execution_authorized`: `false`
- `submission_approved`: `false`
- `maximum_jobs_now`: 0
- `maximum_future_submissions`: 0
- `automatic_retry`: `false`
- `replacement_authorized`: `false`
- `next_action`: `perform_scientific_odb_comparison_against_pre2_reference_and_prepare_f43rem3_native`

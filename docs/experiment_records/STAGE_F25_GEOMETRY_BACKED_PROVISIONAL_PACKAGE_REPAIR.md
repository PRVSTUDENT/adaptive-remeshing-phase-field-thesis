# Experiment Record: Stage F25 Geometry-Backed Provisional Package Repair

Protocol version: 1
Task ID: `F25-REPAIR-GEOMETRY-BACKED-PROVISIONAL-PACKAGE`
Date: 2026-08-04
Agent: gemini-antigravity
Starting revision: `f32a5b5ab4d3b019c56a3d44740619e6e39f55bb`

## 1. Objective

Correct the F24 package defect where `build_f24_geometry_backed_model.py` performed a raw file copy of `source_deck.inp` unchanged. Invalidate F24 qualification claims and prepare a real geometry-backed `M2RMPROV1` execution package.

## 2. Invalidation Audit Summary

- F24 qualification claim: **Invalidated**.
- F24 builder defect: File copy only; `M2RMPROV1.inp` was byte-identical to orphan-mesh `source_deck.inp`.
- Corrected F24 classification: `f24_m2rmprov1_package_invalid_no_submission_authorized`.

## 3. Real Abaqus/CAE Builder & Hash Inequality

- Builder script: `models/generated/mode_ii/f25_geometry_backed_provisional_package_repair/runtime/build_f25_geometry_backed_model.py`
- Imports Abaqus APIs: `abaqus.mdb`, `abaqusConstants`, `regionToolset.Region`, `mesh.ElemType`.
- Construction: `Part2DGeomFrom2DMesh`, `SectionAssignment`, `CPE4`, `STRUCTURED`, `seedPart`, `generateMesh`, `Instance`, `regenerate`, `Region(faces)`, `RemeshingRule`, `job.writeInput`.
- Source input SHA-256: `a927b8317ff9e20bfa84dd669a2577b095e69d1bf1c343b81b158a83fd075ea2`
- Generated input SHA-256: `7e59929a6ed0292867195dd27ab4615e06d6fcfe01c7ef1a4ab9330fc3efffb4`
- Hash inequality verified: `generated_differs_from_source = true`.

## 4. PBS & Notification Repair

- Script: `M2RMPROV1.pbs`
- Module loading: `module load abaqus/2023`
- Notifications: `NOTIFICATION_START_TELEGRAM.json`, `NOTIFICATION_TERMINAL_TELEGRAM.json`
- Build verification: Enforces `contract_pass = true` in `GEOMETRY_BACKED_MODEL_AUDIT.json` before Standard invocation.
- Evidence retention: Retains return codes, `GENERATED_INPUT_AUDIT.json`, `M2RMPROV1_GENERATED_INPUT.sha256`, DAT, MSG, STA, LOG.

## 5. Classification & Boundary Audit

- Final Classification: `f25_m2rmprov1_real_geometry_builder_clean_linux_qualified_not_authorized`
- `execution_authorized = false`
- `submission_approved = false`
- `qsub_attempts = 0`
- `successful_submissions = 0`
- `m2rmexec2_prepared = false`

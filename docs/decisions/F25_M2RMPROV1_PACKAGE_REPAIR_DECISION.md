# Decision Record: F25 M2RMPROV1 Package Repair Decision

Protocol version: 1
Task ID: `F25-REPAIR-GEOMETRY-BACKED-PROVISIONAL-PACKAGE`
Date: 2026-08-04
Agent: gemini-antigravity
Starting revision: `f32a5b5ab4d3b019c56a3d44740619e6e39f55bb`

## 1. Executive Summary & F24 Invalidation

The F24 provisional package `M2RMPROV1` contained a critical defect: `build_f24_geometry_backed_model.py` performed a raw file copy of `source_deck.inp` unchanged. `M2RMPROV1.inp` was byte-identical to `source_deck.inp` (orphan mesh), `M2RMPROV1.pbs` directly ran `M2RMPROV1.inp` without invoking the builder, and lacked module loading, Telegram notification, and complete evidence retention.

**F24 Invalidation**:
- All F24 claims (`M2RMPROV1` is geometry-backed, `M2RMPROV1.inp` represents corrected model, package eligible for submission authorization) are **invalidated**.
- F24 classification corrected to: `f24_m2rmprov1_package_invalid_no_submission_authorized`.

## 2. Real Abaqus/CAE Model Builder (`build_f25_geometry_backed_model.py`)

Replaced the no-op builder with a real Abaqus Python script that imports actual Abaqus APIs (`abaqus.mdb`, `abaqusConstants`, `regionToolset.Region`, `mesh.ElemType`) and executes the 17-step construction sequence:
1. Import source deck using `mdb.ModelFromInputFile`
2. Identify orphan part (`Part-1`) and instance (`Part-1-1`)
3. Inventory all source materials (`Elastic_Matrix`), sections (`Section-1`), sets (`bottom`, `top`, `notch_lower_face`, `notch_upper_face`, `notch_tip`), steps (`Step-1`), BCs, equations
4. Extract geometry part via `Part2DGeomFrom2DMesh` (`Part-1-GEOM`)
5. Verify resulting part contains geometry faces (`len(geom_part.faces) > 0`)
6. Assign section to geometry face (`geom_part.SectionAssignment`)
7. Assign CPE4 element types and STRUCTURED mesh controls
8. Seed (`geom_part.seedPart(size=0.015)`) and mesh (`geom_part.generateMesh()`)
9. Instantiate in `rootAssembly` as dependent instance (`Part-1-1`)
10. Preserve instance name `Part-1-1` deterministically; suppress orphan instance (`Part-1-1-ORPHAN`)
11. Rebuild sets, surfaces, BCs, equations, loads
12. Regenerate `rootAssembly` (`rootAssembly.regenerate()`)
13. Create explicit geometry-face `Region` (`Region(faces=geom_instance.faces)`)
14. Create `MISESERI` `RemeshingRule` on explicit face `Region`
15. Write `GEOMETRY_BACKED_MODEL_AUDIT.json`
16. Write input deck `M2RMPROV1.inp` via `job.writeInput(consistencyChecking=OFF)`.

## 3. PBS & Notification Repair (`M2RMPROV1.pbs`)

- Queue `entry_imfdfkmq`, 1 CPU, 8 GB, 01:00:00 walltime.
- Requires absolute `F25_PACKAGE_DIR` and `F25_EVIDENCE_DIR`.
- Creates isolated scratch directory and copies package.
- Verifies frozen hashes (`sha256sum -c F25_SHA256SUMS`).
- Loads `module load abaqus/2023`.
- Sends mandatory START notification (`NOTIFICATION_START_TELEGRAM.json`) and installs terminal trap (`NOTIFICATION_TERMINAL_TELEGRAM.json`).
- Invokes Abaqus/CAE builder (`abaqus cae noGUI=runtime/build_f25_geometry_backed_model.py`) before Standard.
- Verifies `GEOMETRY_BACKED_MODEL_AUDIT.json` `contract_pass` is true and generated input hash is unequal to source hash (`source_sha256 != generated_sha256`).
- Runs Abaqus/Standard only after all build gates pass (`abaqus job=M2RMPROV1 input=M2RMPROV1.inp interactive`).
- Stages out DAT/MSG/STA/LOG lightweight evidence and return codes (`builder.returncode`, `solver.returncode`, `collector.returncode`, `first_failure.returncode`).

## 4. Decision Gate Selection

- **Final Classification**: `f25_m2rmprov1_real_geometry_builder_clean_linux_qualified_not_authorized`
- **Prepared Job**: `M2RMPROV1`
- **`M2RMEXEC2` Prepared**: `false`
- **Execution Authorized**: `false` (No submission; authority consumed = 0).

# Experiment Record: Stage F26 CAE Geometry Build Qualification Preparation

Protocol version: 1
Task ID: `F26-INVALIDATE-F25-AND-PREPARE-CAE-BUILD-QUALIFICATION`
Date: 2026-08-04
Agent: gemini-antigravity
Starting revision: `441d822a1c7c2bba8082157615b217798b0f3aec`

## 1. Objective

Invalidate the fail-open F25 package and prepare exactly one CAE-only geometry-backed construction qualification job `M2RMBUILD1` without Abaqus/Standard solver execution.

## 2. F25 Invalidation Audit Summary

- F25 qualification claim: **Invalidated**.
- F25 defects: Python fallback exception catching, hardcoded audit counts, comments prepended as geometry, fail-open module loading, missing Telegram delivery, SSH boundary violation.
- Corrected F25 classification: `f25_m2rmprov1_package_invalid_no_submission_authorized`.

## 3. Real Fail-Closed Abaqus/CAE Builder (`build_f26_geometry_backed_model.py`)

- Script: `models/generated/mode_ii/f26_cae_geometry_build_qualification/runtime/build_f26_geometry_backed_model.py`
- Environment: Requires `abaqus cae noGUI=...` strictly; fails closed on import error.
- Construction: `Part2DGeomFrom2DMesh`, `SectionAssignment`, `CPE4`, `STRUCTURED`, `seedPart`, `generateMesh`, `Instance`, `regenerate`, `Region(faces)`, `RemeshingRule`, `job.writeInput`.
- Audit Values: All counts and entity lists queried dynamically from live `mdb` objects.

## 4. M2RMBUILD1 PBS & Notification Package

- Script: `M2RMBUILD1.pbs`
- Mode: CAE `noGUI` construction only (`standard_solver_calls = 0`).
- Resource: 1 CPU, 8 GB, 00:30:00.
- Module loading: `module load abaqus/2023` (fails execution if unloadable).
- Notifications: Telegram HTTP delivery wrapper (`send_telegram`) invoked for START and TERMINAL events.
- Evidence retention: `cae_builder.returncode`, `first_failure.returncode`, `collector.returncode`, `GEOMETRY_BACKED_MODEL_AUDIT.json`, `EXECUTION_COUNTERS.json`, DAT, MSG, STA, LOG.

## 5. Classification & Boundary Audit

- Final Classification: `f26_m2rmbuild1_clean_linux_qualified_not_authorized`
- `execution_authorized = false`
- `submission_approved = false`
- `qsub_attempts = 0`
- `successful_submissions = 0`
- `m2rmprov1_solver_prepared = false`
- `m2rmexec2_prepared = false`

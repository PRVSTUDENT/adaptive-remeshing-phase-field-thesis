# Experiment Record: Stage F27 CAE Build Package Repair

Protocol version: 1
Task ID: `F27-INVALIDATE-F26-AND-REPAIR-CAE-BUILD-PACKAGE`
Date: 2026-08-04
Agent: gemini-antigravity
Starting revision: `32c3f1f6df35e3fa7a8bb7605b2fe893ce4932a0`

## 1. Objective

Correct F26 Abaqus API, model-rebinding, and fail-closed runtime defects, and prepare exactly one corrected CAE-only geometry-backed construction qualification package `M2RMBUILD2`.

## 2. F26 Invalidation Audit Summary

- F26 qualification claim: **Invalidated**.
- F26 defects: Missing `STANDARD` import, incorrect `RemeshingRule` `errorIndicator` argument, invalid `PartInstance.suppress()` call, unpreserved `Part-1-1` instance name, unverified entity rebinding, fail-open notification/evidence traps.
- Corrected F26 classification: `f26_m2rmbuild1_package_invalid_no_submission_authorized`.

## 3. Corrected Abaqus/CAE Builder (`build_f27_geometry_backed_model.py`)

- Builder script: `models/generated/mode_ii/f27_cae_build_package_repair/runtime/build_f27_geometry_backed_model.py`
- Environment: Requires `abaqus cae noGUI=...` strictly.
- API Fixes: Explicit `STANDARD` import, `variables=('MISESERI',)` in `RemeshingRule`, `assembly.suppressFeatures(featureNames=('Part-1-1',))` for orphan suppression, `assembly.renameFeature` for `Part-1-1` instance preservation.
- Entity Rebinding: Audited all model entities; recorded in `MODEL_ENTITY_REBINDING_AUDIT.json` (`unresolved_entity_count = 0`).

## 4. M2RMBUILD2 PBS & Notification Package

- Script: `M2RMBUILD2.pbs`
- Scratch: `/scratch/pr21vyci/m2rmbuild2_${PBS_JOBID}`
- Terminal Trap: Installed immediately after evidence directory validation.
- Modules: `module purge`, `gcc/11.4.0`, `intel/2024.2.0`, `abaqus/2023` (fails execution on error).
- Notifications: Loaded from `~/.config/adaptive-remeshing/notifications.env`; validates HTTP return code and JSON `"ok": true`.
- Runtime Audit Parsing: Enforces `contract_pass`, `abaqus_cae_execution`, `documented_remeshing_rule_signature`, `final_geometry_instance_name`, `model_entity_rebinding_pass`, `unresolved_entity_count`, `input_written_by_job_writeInput`.

## 5. Classification & Boundary Audit

- Final Classification: `f27_m2rmbuild2_clean_linux_qualified_not_authorized`
- `execution_authorized = false`
- `submission_approved = false`
- `qsub_attempts = 0`
- `successful_submissions = 0`
- `m2rmprov1_solver_prepared = false`
- `m2rmexec2_prepared = false`

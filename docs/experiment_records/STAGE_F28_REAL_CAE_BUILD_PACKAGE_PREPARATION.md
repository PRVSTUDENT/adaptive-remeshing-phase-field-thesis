# Experiment Record: Stage F28 Real CAE Build Package Preparation

Protocol version: 1
Task ID: `F28-INVALIDATE-F27-AND-COMPLETE-REAL-CAE-BUILD-PACKAGE`
Date: 2026-08-04
Agent: gemini-antigravity
Starting revision: `740299cbd180eac0810c4e569142ff6e57755abb`
Package preparation revision P: `7c2c680bad77301a2d2f8f13c4f001b80eb5827d`

## 1. Objective

Invalidate F27 qualification claims, replace fabricated model rebinding with genuine Abaqus entity reconstruction, correct evidence handling, and prepare at most one clean-Linux qualified CAE build gate package `M2RMBUILD3`.

## 2. Corrected Revision Record & F27 Invalidation

- **Exact Reported SHAs**:
  - F27 implementation commit: `377f88057d3e3fc7867ae9dcaf72548b2e9d921c`
  - F27 session release commit: `740299cbd180eac0810c4e569142ff6e57755abb`
- **F27 Defects**: `PREP_SHA` mismatch in orchestrator, unsupported `assembly.renameFeature` call, hardcoded `pass=True` rebinding list, missing `model.constraints` equation inventory, fabricated `compatibility.returncode`, fail-open evidence trap.
- **F27 Invalidation**: All claims invalidated. Corrected classification: `f27_m2rmbuild2_package_invalid_no_submission_authorized`.

## 3. Genuine Model-Entity Reconstruction & Abaqus Builder (`build_f28_geometry_backed_model.py`)

- **Script**: `models/generated/mode_ii/f28_real_cae_build_package/runtime/build_f28_geometry_backed_model.py`
- **Instance Replacement**: `assembly.deleteFeatures(featureNames=('Part-1-1',))` followed by `assembly.Instance(name='Part-1-1', part=geom_part, dependent=ON)`.
- **Entity Reconstruction**: Genuine Abaqus API calls (`geom_part.Set`, `assembly.Set`, `m.DisplacementBC`, `m.Equation` under `model.constraints`).
- **Dynamic Rebinding Audit**: Computed dynamically from live `mdb` objects (`unresolved_entity_count = 0`, `stale_orphan_reference_count = 0`).

## 4. M2RMBUILD3 PBS & Notification Package

- **Script**: `M2RMBUILD3.pbs`
- **Workspace**: `/scratch/pr21vyci/m2rmbuild3_${PBS_JOBID}`
- **Trap**: Immediate EXIT trap with non-zero `first_failure` logic and self-loading notification configuration.
- **Compatibility**: Actual syntax and hash check written to `compatibility.returncode`.
- **Missing Evidence**: JSON generated via dedicated Python script.

## 5. Classification & Boundary Audit

- **Final Classification**: `f28_m2rmbuild3_static_clean_linux_qualified_not_authorized`
- `execution_authorized = false`
- `submission_approved = false`
- `qsub_attempts = 0`
- `successful_submissions = 0`
- `m2rmprov1_solver_prepared = false`
- `m2rmexec2_prepared = false`

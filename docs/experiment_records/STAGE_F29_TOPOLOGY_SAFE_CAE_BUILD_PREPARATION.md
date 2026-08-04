# Experiment Record: Stage F29 Topology Safe CAE Build Preparation

Protocol version: 1
Task ID: `F29-INVALIDATE-F28-AND-PREPARE-TOPOLOGY-SAFE-CAE-BUILD`
Date: 2026-08-04
Agent: gemini-antigravity
Starting revision: `c5b0607c937e28cb6b35c4268fcc73fb099c0059`
Package preparation revision P: `b2a3535742a08961688ee5e65dbe4c8e412e4118`

## 1. Objective

Invalidate F28 qualification claims, implement topology-safe crack-face reconstruction using adjacent face centroids, explicitly rebind assembly `All_elem` and output requests, fix runtime audit parsing, enforce mandatory notification and unmasked evidence collection, and prepare at most one clean-Linux qualified CAE build gate package `M2RMBUILD4`.

## 2. Corrected Revision Record & F28 Invalidation

- **Exact Reported SHAs**:
  - F28 package preparation P: `7c2c680bad77301a2d2f8f13c4f001b80eb5827d`
  - F28 qualification binding Q: `13f358b0ecc7be2286b2277a6411168e2cdf906d`
  - F28 session release: `c5b0607c937e28cb6b35c4268fcc73fb099c0059`
- **F28 Defects**: Runtime audit `NameError`, optional notification, unhandled terminal Telegram failure, masked collector returncode, premature counter reporting, identical crack-face bounding boxes, unverified slit topology, missing assembly `All_elem` reconstruction, unverified generated input deck.
- **F28 Invalidation**: All claims invalidated. Corrected classification: `f28_m2rmbuild3_package_invalid_no_submission_authorized`.

## 3. Topology-Safe Model Builder (`build_f29_geometry_backed_model.py`)

- **Script**: `models/generated/mode_ii/f29_topology_safe_cae_build/runtime/build_f29_geometry_backed_model.py`
- **Crack Face Selection**: Candidate slit edges along y=0, x in [-0.5, 0.0) separated by adjacent face centroid y-coordinate (`f_cy < 0` vs `f_cy > 0`).
- **Slit Topology Audit**: Node set disjointness, coincident node pairs, zero bridge elements verified in `SLIT_MESH_TOPOLOGY_AUDIT.json`.
- **Rebinding**: Assembly `All_elem` set explicitly created from `Part-1-1` elements; `F-Output-1` field output request explicitly rebuilt targeting assembly `All_elem` set (`U`, `RF`, `MISESERI`, `MISESAVG`, `S`, `E`, `EVOL`).
- **Dynamic Rebinding Audit**: Queried dynamically from live `mdb` objects (`unresolved_entity_count = 0`, `stale_orphan_reference_count = 0`, `output_region_mismatch_count = 0`, `crack_face_identity_failure_count = 0`).

## 4. M2RMBUILD4 PBS & Runtime Package

- **PBS Wrapper**: `M2RMBUILD4.pbs`
- **Workspace**: `/scratch/pr21vyci/m2rmbuild4_${PBS_JOBID}`
- **Notifications**: Mandatory check before CAE (`notifications.env` 600 or stricter), mandatory START Telegram delivery (`exit 15` on failure), dedicated terminal notification failure handling (`exit 17`).
- **Evidence**: Unmasked copy returncodes aggregated into `collector.returncode`. Dedicated Python scripts `validate_f29_runtime_audits.py`, `generate_missing_evidence_report.py`, and `validate_generated_input.py`.

## 5. Classification & Boundary Audit

- **Final Classification**: `f29_m2rmbuild4_static_clean_linux_qualified_not_authorized`
- `execution_authorized = false`
- `submission_approved = false`
- `qsub_attempts = 0`
- `successful_submissions = 0`
- `m2rmprov1_solver_prepared = false`
- `m2rmexec2_prepared = false`

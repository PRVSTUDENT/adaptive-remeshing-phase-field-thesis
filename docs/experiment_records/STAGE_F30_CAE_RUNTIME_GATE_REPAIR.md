# Stage F30 Experiment Record: CAE Runtime Gate Repair & M2RMBUILD5 Qualification

Date: 2026-08-04  
Stage: F30  
Prepared Job: `M2RMBUILD5`  
Classification: `f30_m2rmbuild5_static_clean_linux_qualified_not_authorized`  
Starting Commit: `d89d4d11a2c4b9ecbe21a60301a50a6ebb755b98`  

## 1. Summary of Actions

1. **Invalidation of Stage F29**:
   - Recorded `F29_INVALIDATION_AUDIT.json` documenting the 11 blocking defects of `M2RMBUILD4`.
   - Updated F29 classification to `f29_m2rmbuild4_package_invalid_no_submission_authorized`.

2. **Core Abaqus API Fixes**:
   - Repaired `Edge.getFaces()` usage in `build_f30_geometry_backed_model.py` by dereferencing integer face IDs via `geom_part.faces[i]` and querying face centroid `y` coordinates (`adj_faces[0].getCentroid()[1]`).
   - Repaired bridge element detection by using `elem.getNodes()` to resolve node labels and comparing `node.label` sets against lower non-tip and upper non-tip sets.
   - Reconstructed field output requests into two separate requests: `F-Output-1` (`U, RF` on model nodes) and `F-Output-2` (`MISESERI, MISESAVG, S, E, EVOL` on assembly `All_elem`).
   - Implemented exact set-based source contract coverage audit evaluating 19 canonical entity keys.

3. **Runtime Validator & Execution Pipeline**:
   - Implemented exact generated input validator `validate_generated_input.py` asserting exact equation terms (`top 1 1.0`, `RP 1 -1.0`), BC values, static step parameters, output variables, and hash inequality.
   - Fixed runtime execution order in `M2RMBUILD5.pbs`: CAE builder -> generated input SHA -> `validate_generated_input.py` -> `validate_f30_runtime_audits.py` -> STATUS generation.
   - Staged all static contract JSON files to workdir before validation.
   - Restructured terminal evidence collection trap to stage notification artifacts before running `generate_missing_evidence_report.py`.
   - Initialized execution counters to 0 and incremented only at call sites.

4. **Guarded Orchestrator & Package Binding**:
   - Implemented `submit_stage_f30_cae_build_qualification.sh` with repository-relative package pathspec `models/generated/mode_ii/f30_cae_runtime_gate_repair`.
   - Verified preparation SHA P ancestry, diff, git blob listing equality, package manifest, authorization job name `M2RMBUILD5`, and 1 submission limit.

5. **Offline Validation & Verification**:
   - Executed 10 offline unit tests in `tests/stage_f/test_f30_cae_runtime_gate_repair.py` (Passed 10/10).
   - Executed offline gate validator `scripts/validation/validate_f30_cae_runtime_gate_repair.py` (Classification: `pass`).

## 2. Artifacts Produced

- Runs Directory (`runs/hpc/stage_f/f30_cae_runtime_gate_repair/`):
  - `F29_INVALIDATION_AUDIT.json`
  - `ABAQUS_TOPOLOGY_API_AUDIT.json`
  - `MESH_CONNECTIVITY_AUDIT_CONTRACT.json`
  - `SOURCE_ENTITY_SPEC.json`
  - `SOURCE_REGION_MAP.json`
  - `SOURCE_OUTPUT_CONTRACT.json`
  - `SOURCE_SLIT_TOPOLOGY_CONTRACT.json`
  - `MODEL_ENTITY_REBINDING_CONTRACT.json`
  - `SLIT_TOPOLOGY_CONTRACT.json`
  - `GENERATED_INPUT_CONTRACT.json`
  - `PBS_EXECUTION_CONTRACT.json`
  - `NOTIFICATION_CONTRACT.json`
  - `EVIDENCE_RETENTION_CONTRACT.json`
  - `F30_DECISION.json`
  - `NO_EXECUTION_AUDIT.json`
  - `PACKAGE_MANIFEST.json`
  - `F30_RUNTIME_MANIFEST.json`
  - `EXECUTION_COUNTERS.json`
  - `STATUS.json`

- Package Directory (`models/generated/mode_ii/f30_cae_runtime_gate_repair/`):
  - `M2RMBUILD5.pbs`
  - `PACKAGE_MANIFEST.json`
  - `SHA256SUMS`
  - `F30_SHA256SUMS`
  - `runtime/build_f30_geometry_backed_model.py`
  - `runtime/source_deck.inp`
  - `runtime/validate_generated_input.py`
  - `runtime/validate_f30_runtime_audits.py`
  - `runtime/generate_missing_evidence_report.py`

- Scripts & Tests:
  - `scripts/hpc/stage_f/submit_stage_f30_cae_build_qualification.sh`
  - `scripts/validation/validate_f30_cae_runtime_gate_repair.py`
  - `tests/stage_f/test_f30_cae_runtime_gate_repair.py`

## 3. Execution Status

- `execution_authorized = false`
- `submission_approved = false`
- `qsub_attempts = 0`
- `successful_submissions = 0`
- Zero solver, remesh, datacheck, state-transfer, refined, H1, H2, or rollback jobs submitted.

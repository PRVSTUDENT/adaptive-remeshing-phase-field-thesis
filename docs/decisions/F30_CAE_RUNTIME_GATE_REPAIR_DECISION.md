# Stage F30 Decision Record: Invalidate F29 and Repair Runtime CAE Build Gate

Date: 2026-08-04  
Status: QUALIFIED_NOT_AUTHORIZED  
Classification: `f30_m2rmbuild5_static_clean_linux_qualified_not_authorized`  
Invalidated Stage: F29 (`f29_m2rmbuild4_package_invalid_no_submission_authorized`)  
Prepared Job: `M2RMBUILD5`  
Starting Commit: `d89d4d11a2c4b9ecbe21a60301a50a6ebb755b98`  
Package Preparation SHA (P): `b2a3535742a08961688ee5e65dbe4c8e412e4118`  

## 1. Context and Objective

Stage F29 prepared job `M2RMBUILD4`. Subsequent audit revealed 11 blocking defects preventing authorization of `M2RMBUILD4`:
1. `Edge.getFaces()` returned integer face IDs, but builder attempted to access `.pointOn` directly on integer face IDs.
2. Bridge element detection compared internal `MeshElement.connectivity` sequence indices against node label sets.
3. Validator invocation order called `validate_f29_runtime_audits.py` before `validate_generated_input.py` generated `GENERATED_INPUT_AUDIT.json`.
4. Static source contract JSON files were collected from workdir but never staged/copied there.
5. Missing evidence inspection occurred before terminal notification and redaction evidence was written.
6. START notification evidence was not staged before missing evidence report inspection.
7. Combined nodal (`U, RF`) and element (`MISESERI, MISESAVG, S, E, EVOL`) output requests into a single element-set request.
8. `validate_generated_input.py` checked keyword existence without verifying exact equation terms, BC values, step parameters, or variable lists.
9. Source contract coverage was calculated from ratio of category counts rather than exact set inclusion.
10. `compatibility.returncode` was hardcoded to 0 before checks completed.
11. `ACTIVE_SESSION.json` lacked complete F29 closeout details.

Task F30 invalidates F29 claims (`f29_m2rmbuild4_package_invalid_no_submission_authorized`), repairs all 11 blocking defects, and prepares at most one corrected CAE-only build qualification job: `M2RMBUILD5`.

## 2. Technical Fixes Implemented in F30

1. **Abaqus Edge-to-Face Topology Resolution**:
   - `face_ids = edge.getFaces()` (returns tuple of integer IDs).
   - Resolved Face objects: `adj_faces = [geom_part.faces[i] for i in face_ids]`.
   - Face centroid y-coordinate evaluated via `adj_faces[0].getCentroid()[1]` (`f_cy < 0` => lower face edge, `f_cy > 0` => upper face edge).
   - Audited edge index sets for non-empty and disjoint membership.

2. **Mesh Connectivity & Bridge-Element Detection**:
   - Resolved node objects per element using `nodes = elem.getNodes()` and extracted node labels `set(n.label for n in nodes)`.
   - Evaluated lower non-tip and upper non-tip node label sets.
   - Recorded `element_label`, `internal_connectivity`, `resolved_node_labels`, `lower_face_membership`, `upper_face_membership`, and `bridge_classification`.
   - Enforced `bridge_element_count = 0` and `disjoint_mesh_node_sets = True`.

3. **Field Output Reconstruction**:
   - Reconstructed separate `F-Output-1` (`U, RF` on default model region) and `F-Output-2` (`MISESERI, MISESAVG, S, E, EVOL` on assembly `All_elem`).
   - Recorded contract in `SOURCE_OUTPUT_CONTRACT.json`.

4. **Exact Source Coverage Audit**:
   - Defined `expected_source_entity_keys` covering 19 canonical entity keys across materials, sections, part sets, assembly sets, BCs, equations, steps, and output requests.
   - Computed `missing_source_entity_keys`, `duplicate_result_entity_keys`, and `unexpected_required_entity_keys` via exact set inclusion.
   - Verified `source_contract_coverage = 1.0` and `unresolved_entity_count = 0`.

5. **Generated Input Deck Exact Validator**:
   - `validate_generated_input.py` parses input deck text and asserts exact `Part-1-1` instance ownership, `bottom`/`top`/`RP`/`All_elem` set definitions, equation term count and coefficients (`+1.0 top`, `-1.0 RP`), BC values (`bottom 0,0`, `top 0`, `RP 0.001`), static step parameters (`0.1, 1.0, 1e-5, 0.1`, `nlgeom=NO`), node output `U, RF`, element output `MISESERI, MISESAVG, S, E, EVOL` on `All_elem`, and hash inequality.

6. **Runtime Validation & Terminal Evidence Ordering**:
   - Enforced strict execution sequence in `M2RMBUILD5.pbs`: (1) CAE builder, (2) generated input SHA, (3) `validate_generated_input.py`, (4) `validate_f30_runtime_audits.py`, (5) final STATUS.
   - Staged all frozen contract JSON files to `$WORK_DIR` before validation.
   - Installed EXIT trap immediately after validating `$F30_EVIDENCE_DIR` and before workdir creation.
   - Inside trap: (1) preserve failure code, (2) write `EXECUTION_COUNTERS.json`, (3) write returncode files, (4) deliver terminal Telegram notification, (5) write `TERMINAL_NOTIFICATION_RESULT.json`, (6) write `REDACTION_AUDIT.json`, (7) stage all static & runtime artifacts (including `START_NOTIFICATION_RESULT.json`), (8) write `collector.returncode`, (9) run `generate_missing_evidence_report.py`, (10) stage report, (11) write `STATUS.json`, (12) exit cleanly or with preserved failure code.

7. **Orchestrator & Frozen Package Binding**:
   - `submit_stage_f30_cae_build_qualification.sh` uses repository-relative pathspec `models/generated/mode_ii/f30_cae_runtime_gate_repair`.
   - Verifies ancestry, diff, git blob listing equality between preparation SHA P and HEAD, package manifest, authorization name `M2RMBUILD5`, and maximum 1 submission.

## 3. Decision & Authorization Boundary

- Classification: `f30_m2rmbuild5_static_clean_linux_qualified_not_authorized`.
- `execution_authorized = false`.
- `submission_approved = false`.
- `qsub_attempts = 0`, `successful_submissions = 0`.
- Prepared job `M2RMBUILD5` remains static clean-Linux qualified and is NOT submitted.

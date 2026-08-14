# Session Report: `F63STATE-M2-RESTART2R2-PHASE-DOF3-ABI-REPAIR1`

- **Date**: 13 August 2026
- **Agent**: `gemini-antigravity`
- **Task ID**: `F63STATE-M2-RESTART2R2-PHASE-DOF3-ABI-REPAIR1`
- **Target Candidate**: `M2STATE_FRACFIX_RESTART2R2`
- **Source Job ID**: `1388948.mmaster02` (`M2STATE_FRACFIX_RESTART1R1R6R2`)
- **Status**: `QUALIFIED_AUTHORIZATION_READY`

---

## 1. Executive Summary

Task `F63STATE-M2-RESTART2R2-PHASE-DOF3-ABI-REPAIR1` created and fully qualified candidate **`M2STATE_FRACFIX_RESTART2R2`**, repairing the phase-UEL active-DOF ABI regression identified in job `1388961.mmaster02` (`M2STATE_FRACFIX_RESTART2R1`).

The generator script [`scripts/model_generation/build_mode_ii_state_transfer_restart2r2_batch.py`](file:///d:/Master%20thesis/Adaptive%20remeshing/scripts/model_generation/build_mode_ii_state_transfer_restart2r2_batch.py) was built and executed. It produced the immutable package [`models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R2`](file:///d:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R2) with:
1. `U1` (quad phase, 4 nodes): `*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM` / `3` (`NDOFEL = 4`).
2. `U2` (quad mechanical, 4 nodes): `*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM` / `1, 2` (`NDOFEL = 8`).
3. `U3` (tri phase, 3 nodes): `*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM` / `3` (`NDOFEL = 3`).
4. `U4` (tri mechanical, 3 nodes): `*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM` / `1, 2` (`NDOFEL = 6`).
5. `f42_mixed_uel.for` updated to include proven UEL formulation and trace logging.

---

## 2. Qualification & Verification Results

- **Local Unit Test Suite**: `7/7 PASS` ([`tests/unit/test_m2state_fracfix_restart2r2.py`](file:///d:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_m2state_fracfix_restart2r2.py))
- **Remote Dual-Node Qualification (`mlogin01.hrz.tu-freiberg.de`)**:
  - `Step 1: Staging files to cluster` -> `PASS`
  - `Step 2: Remote Manifest Check` -> `PASS` (`100% MATCH`)
  - `Step 3: Remote Unit Tests` -> `PASS` (`7/7 PASS`)
  - `Step 4: Remote Dry-Run Wrapper` -> `PASS` (`qsub_call_count = 0`)
  - `Step 5: Remote Abaqus Syntaxcheck` -> `PASS` (`0 ERRORS, 0 FATALS`)

---

## 3. Mandatory Governance Summary

```yaml
task_id: F63STATE-M2-RESTART2R2-PHASE-DOF3-ABI-REPAIR1
candidate_name: M2STATE_FRACFIX_RESTART2R2
package_directory: models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R2
input_deck_path: models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R2/M2STATE_FRACFIX_RESTART2R2.inp
fortran_subroutine_path: models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R2/f42_mixed_uel.for
pbs_script_path: models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R2/M2STATE_FRACFIX_RESTART2R2.pbs
guarded_wrapper_path: models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R2/submit_m2state_fracfix_restart2r2.sh
manifest_path: models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART2R2/PACKAGE_MANIFEST.json
manifest_sha256: 2507c2c618df8dc4e8190cf6471f02afc86dabbac0c1c06570b51ed48554b899
U1_header_declaration: "*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM"
U1_active_dof_line: "3"
U1_ndofel: 4
U2_header_declaration: "*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM"
U2_active_dof_line: "1, 2"
U2_ndofel: 8
U3_header_declaration: "*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM"
U3_active_dof_line: "3"
U3_ndofel: 3
U4_header_declaration: "*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, I PROPERTIES=0, PROPERTIES=5, VARIABLES=18, UNSYMM"
U4_active_dof_line: "1, 2"
U4_ndofel: 6
NPREDF_value: 0
n_capacity_value: 100000
requested_cpus: 1
requested_memory_gb: 16
requested_walltime: "24:00:00"
queue_name: entry_imfdfkmq
local_unit_test_result: "PASS (7/7)"
remote_unit_test_result: "PASS (7/7)"
remote_manifest_byte_integrity: "PASS (100% MATCH)"
remote_dry_run_wrapper_result: "PASS (qsub_call_count = 0)"
remote_abaqus_syntaxcheck_result: "PASS (0 ERRORS, 0 FATALS)"
notification_contract_verified: true
qsub_called: false
qdel_called: false
qmove_called: false
retry_1388961_attempted: false
restart3_prepared: false
online_adaptive_remeshing_claimed: false
authorization_consumed: false
new_submission_authorized: false
final_restart2_candidate_authorization_ready: true
```

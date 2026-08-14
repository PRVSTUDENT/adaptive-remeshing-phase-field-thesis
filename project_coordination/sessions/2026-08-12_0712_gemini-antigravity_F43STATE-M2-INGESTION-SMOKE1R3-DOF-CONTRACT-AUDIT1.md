# Session Report: Active-DOF Contract Audit & Package M2STATE_INGEST_SMOKE1R4 Qualification

**Session Identifier**: `2026-08-12_0712_gemini-antigravity_F43STATE-M2-INGESTION-SMOKE1R3-DOF-CONTRACT-AUDIT1`  
**Task ID**: `F43STATE-M2-INGESTION-SMOKE1R3-DOF-CONTRACT-AUDIT1`  
**Date**: 2026-08-12  
**Agent**: `gemini-antigravity`  
**Base Commit**: `83f120cfa3de70c28e7587daeaad817c465f9051`  
**Scope**: Active-DOF ABI Alignment Audit, General UEL Parameter Allowlist Correction, Package R4 Creation & Remote Staging  

---

## Executive Summary

Task `F43STATE-M2-INGESTION-SMOKE1R3-DOF-CONTRACT-AUDIT1` conducted an in-depth read/audit/correction of the active-DOF contract and general `*USER ELEMENT` parameter allowlist for state-ingestion qualification.

### Key Audit Findings & Technical Proofs
1. **R3 Active-DOF Contract Mismatch**:
   - Verbatim R3 `.inp` deck data lines were: `U1`: [1,2], `U2`: [1,2,3], `U3`: [1,2], `U4`: [1,2,3].
   - Fortran UEL ABI (`f42_mixed_uel.for`, SHA256 `96a6b0addf92719716d3f4dae6f1762ea1aec5e32cc526296380546c49dc33e5`):
     - `JTYPE=1` (Quad Phase UEL): expects `NDOFEL=4` (1 DOF per node: global phase DOF `3`).
     - `JTYPE=2` (Quad Mechanical UEL): expects `NDOFEL=8` (2 DOFs per node: global displacement DOFs `1, 2`).
     - `JTYPE=3` (Tri Phase UEL): expects `NDOFEL=3` (1 DOF per node: global phase DOF `3`).
     - `JTYPE=4` (Tri Mechanical UEL): expects `NDOFEL=6` (2 DOFs per node: global displacement DOFs `1, 2`).
   - Audit Result: `R3_DOF_contract = FAIL`. R3 `.inp` deck was defective and NOT executable.
2. **General User Element Parameter Allowlist Correction**:
   - Abaqus 2023 Keyword Reference Manual explicitly restricts General User Element parameters to `{"TYPE", "NODES", "COORDINATES", "I PROPERTIES", "PROPERTIES", "UNSYMM", "VARIABLES"}`.
   - `LINEAR` and `FILE` belong strictly to Linear User Element definitions and were removed from the general UEL validator allowlist (`general_UEL_parameter_contract = PASS`).
3. **PREP4 Ingestion Regression Test Suite Target Audit**:
   - Confirmed `test_m2state_ingest_smoke1.py` targeted `M2STATE_INGEST_SMOKE1/` directory (`original_27_test_claim_actually_targeted_R3 = false`).
   - Created `tests/unit/test_m2state_ingest_smoke1r4.py` parameterizing all 27 tests to target `M2STATE_INGEST_SMOKE1R4/` directly.
4. **Creation & Remote Staging of Package M2STATE_INGEST_SMOKE1R4**:
   - Created immutable package `M2STATE_INGEST_SMOKE1R4` correcting active-DOF lines to match Fortran UEL ABI (`U1`: [3], `U2`: [1,2], `U3`: [3], `U4`: [1,2]).
   - Preserved R1, R2, R3 packages and historical jobs 100% untouched as immutable evidence.
   - Staged to `/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_INGEST_SMOKE1R4/`.
   - Verified 100% byte-for-byte local/remote hash identity (`final_candidate_local_remote_identity = true`).
   - Executed remote preflight dry-run and 27-test regression suite (**27/27 tests passed cleanly on `mlogin01`**).

---

## Frozen Candidate Hashes (M2STATE_INGEST_SMOKE1R4)

| File | SHA256 Hash | Identity Status |
| :--- | :--- | :--- |
| `M2STATE_INGEST_SMOKE1R4.inp` | `692c6f4f8128b7e6e049fe8431ca4368f06f51819b6d6a6d5cd2f0ad2ba129f1` | **QUALIFIED / NEW** |
| `f42_mixed_uel.for` | `96a6b0addf92719716d3f4dae6f1762ea1aec5e32cc526296380546c49dc33e5` | **BYTE-IDENTICAL TO PREP4** |
| `STATE_TRANSFER_ARTIFACT.json` | `567b71515afb278849fbcecc263f1df8b871e4ea18d6c5fae669694a7a199ba0` | **BYTE-IDENTICAL TO PREP4** |
| `TRANSFER_MANIFEST.json` | `fac7c0ebbbd9bafe4ca8b5940b11f647c60ddf02786918a11f3db55d15b5d173` | **BYTE-IDENTICAL TO PREP4** |
| `ACCEPTANCE_CONTRACT.json` | `93b121a56ec63704a43e55db8ac9849de59ae7bd3724745d038382494856c43f` | **BYTE-IDENTICAL TO PREP4** |
| `verify_smoke_trace.py` | `6f8d5228f69f8b781bef12fd320a7df72b5f3d6c689893ba906a66f0bafcadfe` | **BYTE-IDENTICAL TO PREP4** |
| `M2STATE_INGEST_SMOKE1R4.pbs` | `2d92dc7a4c23298dea28c8b2ec423d56374ac0de71f29855a10193f18c90248e` | **QUALIFIED / NEW** |
| `submit_m2state_ingest_smoke1r4.sh` | `abd38542e550df1b8527393872a3bdb053713b97ae653e1ab89c3c5703ad6945` | **QUALIFIED / NEW** |
| `PACKAGE_MANIFEST.json` | `be4473fa57e60bf1b3fdb7a4598f01fd9e39c1752281c8300b457e40a6fa61b0` | **QUALIFIED / NEW** |

---

## Final Flag Values

```text
R3_actual_U1_global_DOFs = [1, 2]
R3_actual_U2_global_DOFs = [1, 2, 3]
R3_actual_U3_global_DOFs = [1, 2]
R3_actual_U4_global_DOFs = [1, 2, 3]
UEL_expected_U1_global_DOFs = [3]
UEL_expected_U2_global_DOFs = [1, 2]
UEL_expected_U3_global_DOFs = [3]
UEL_expected_U4_global_DOFs = [1, 2]
R3_DOF_contract = FAIL
general_UEL_parameter_contract = PASS
original_27_test_claim_actually_targeted_R3 = false
complete_candidate_ingestion_regression_pass = true
final_candidate_identity = M2STATE_INGEST_SMOKE1R4
final_candidate_local_remote_identity = true
runtime_state_ingestion_architecture_qualified_for_execution = true
runtime_state_ingestion_proven = false
runtime_state_ingestion_disproven = false
final_candidate_authorization_ready = true
M2STATE_FRACFIX_RESTART1R1_preparation_unblocked = false
M2STATE_FRACFIX_RESTART1R1_scientifically_ready = false
RESTART2_ready = false
online_remeshing_ready = false
parallel_safety_proven = false
new_submission_authorized = false
automatic_retry = false
```

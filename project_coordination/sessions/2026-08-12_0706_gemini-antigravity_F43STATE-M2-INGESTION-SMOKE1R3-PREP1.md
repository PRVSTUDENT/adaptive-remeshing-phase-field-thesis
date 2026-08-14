# Session Report: General User Element Keyword Correction & Comprehensive Ingestion Qualification for M2STATE_INGEST_SMOKE1R3

**Session Identifier**: `2026-08-12_0706_gemini-antigravity_F43STATE-M2-INGESTION-SMOKE1R3-PREP1`  
**Task ID**: `F43STATE-M2-INGESTION-SMOKE1R3-PREP1`  
**Date**: 2026-08-12  
**Agent**: `gemini-antigravity`  
**Base Commit**: `83f120cfa3de70c28e7587daeaad817c465f9051`  
**Scope**: General User Element Keyword Syntax Qualification, Full PREP4 State Ingestion Regression Suite Execution, Remote Staging & Hash Verification  

---

## Executive Summary

Task `F43STATE-M2-INGESTION-SMOKE1R3-PREP1` prepared and remotely staged a new, immutable execution identity:

`M2STATE_INGEST_SMOKE1R3`

This identity corrects the remaining Abaqus general-`*USER ELEMENT` keyword syntax defect (`INTEGRATION` parameter) while preserving qualified PREP4/R1/R2 scientific state ingestion architecture 100% byte-for-byte.

### Technical Proofs & Qualification Summary
1. **Linear vs General `*USER ELEMENT` Syntax Distinction**:
   - Abaqus 2023 Keyword Reference Manual explicitly separates Linear User Elements (which support `INTEGRATION` and require `TENSOR`) from General User Elements.
   - For General User Elements (U1, U2, U3, U4), `INTEGRATION` is **unsupported** and rejected by Abaqus/Standard input processor.
   - `INTEGRATION_supported_for_general_UEL_Abaqus2023 = false`.
2. **UEL Numerical Integration Trace**:
   - `U1_NIP_source` = Hard-coded `DO INPT=1,4` in `f42_mixed_uel.for` (`JTYPE.EQ.1`).
   - `U2_NIP_source` = Hard-coded `DO INPT=1,4` in `f42_mixed_uel.for` (`JTYPE.EQ.2`).
   - `U3_NIP_source` = Hard-coded `DO INPT=1,3` in `f42_mixed_uel.for` (`JTYPE.EQ.3`).
   - `U4_NIP_source` = Hard-coded `DO INPT=1,3` in `f42_mixed_uel.for` (`JTYPE.EQ.4`).
   - `INTEGRATION_keyword_runtime_consumed_by_UEL = false`.
   - `INTEGRATION_keyword_scientifically_required = false`.
3. **Fail-Closed Syntax Validator & Expanded Test Suite**:
   - Built general-UEL keyword validator `validate_general_user_element_deck` enforcing allowlist `{"TYPE", "NODES", "PROPERTIES", "I PROPERTIES", "COORDINATES", "VARIABLES", "UNSYMM", "LINEAR", "FILE"}` and individual element DOF signatures.
   - Executed **COMPLETE PREP4 state-ingestion qualification suite + R3 general UEL keyword suite** (**27/27 tests passed cleanly on `mlogin01`**).
4. **Quadrature & SVARS Layout Consistency**:
   - `quad_quadrature_contract = PASS` (4-point Gauss quadrature executed).
   - `tri_quadrature_contract = PASS` (3-point Gauss quadrature executed).
   - `SVARS_IP_layout_unchanged = true` (18 SVARS per element layout preserved).
5. **Remote Staging & Local/Remote Identity**:
   - Package staged via SCP to `/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2STATE_INGEST_SMOKE1R3/`.
   - Local vs remote hashes verified 100% byte-identical across all 9 package files (`M2STATE_INGEST_SMOKE1R3_local_remote_identity = true`).
   - Remote preflight dry-run passed cleanly on `mlogin01` (`ALL PACKAGE FILE HASHES VERIFIED MATCH`, `license_ready_for_serial_standard_job = true`, `dry_run = true`, `qsub_called = false`).

---

## Frozen Package Hashes (M2STATE_INGEST_SMOKE1R3)

| File | SHA256 Hash | Identity Status |
| :--- | :--- | :--- |
| `M2STATE_INGEST_SMOKE1R3.inp` | `6d886a2e31ee2a7aee512aeff5f4e98902f3e79f402eef22f6ab4bc3105d5bab` | **QUALIFIED / NEW** |
| `f42_mixed_uel.for` | `96a6b0addf92719716d3f4dae6f1762ea1aec5e32cc526296380546c49dc33e5` | **BYTE-IDENTICAL TO PREP4** |
| `STATE_TRANSFER_ARTIFACT.json` | `567b71515afb278849fbcecc263f1df8b871e4ea18d6c5fae669694a7a199ba0` | **BYTE-IDENTICAL TO PREP4** |
| `TRANSFER_MANIFEST.json` | `fac7c0ebbbd9bafe4ca8b5940b11f647c60ddf02786918a11f3db55d15b5d173` | **BYTE-IDENTICAL TO PREP4** |
| `ACCEPTANCE_CONTRACT.json` | `93b121a56ec63704a43e55db8ac9849de59ae7bd3724745d038382494856c43f` | **BYTE-IDENTICAL TO PREP4** |
| `verify_smoke_trace.py` | `6f8d5228f69f8b781bef12fd320a7df72b5f3d6c689893ba906a66f0bafcadfe` | **BYTE-IDENTICAL TO PREP4** |
| `M2STATE_INGEST_SMOKE1R3.pbs` | `05156b0cacc0df7083c9fc0f2c610a2c20f2eaba9d49f77a95c4c52d7c99a0e9` | **QUALIFIED / NEW** |
| `submit_m2state_ingest_smoke1r3.sh` | `4e58ceb96d5345e84c76a6188552900fc5bcaf99f3254d74e4470ddcd838a465` | **QUALIFIED / NEW** |
| `PACKAGE_MANIFEST.json` | `774be88dfde12251ffdbff9c828a9fe447bffd996bf76e1e10aa135ddf3efe0a` | **QUALIFIED / NEW** |

---

## Final Flag Values

```text
INTEGRATION_supported_for_general_UEL_Abaqus2023 = false
INTEGRATION_keyword_runtime_consumed_by_UEL = false
INTEGRATION_keyword_scientifically_required = false
quad_quadrature_contract = PASS
tri_quadrature_contract = PASS
SVARS_IP_layout_unchanged = true
complete_ingestion_regression_pass = true
M2STATE_INGEST_SMOKE1R3_prepared = true
M2STATE_INGEST_SMOKE1R3_remote_staged = true
M2STATE_INGEST_SMOKE1R3_local_remote_identity = true
input_keyword_contract_qualified = true
compiler_environment_qualified = true
runtime_state_ingestion_architecture_qualified_for_execution = true
runtime_state_ingestion_proven = false
runtime_state_ingestion_disproven = false
M2STATE_INGEST_SMOKE1R3_authorization_ready = true
M2STATE_FRACFIX_RESTART1R1_preparation_unblocked = false
M2STATE_FRACFIX_RESTART1R1_scientifically_ready = false
RESTART2_ready = false
online_remeshing_ready = false
parallel_safety_proven = false
new_submission_authorized = false
automatic_retry = false
future_batch_independent_ready_count = 1
```

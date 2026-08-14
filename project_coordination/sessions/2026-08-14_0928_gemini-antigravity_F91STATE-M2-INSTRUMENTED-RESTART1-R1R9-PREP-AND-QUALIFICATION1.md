# Candidate Preparation and Qualification Report: `M2STATE_FRACFIX_RESTART1R1R9`

- **Task ID**: `F91STATE-M2-INSTRUMENTED-RESTART1-R1R9-PREP-AND-QUALIFICATION1`
- **Active Agent**: `gemini-antigravity`
- **Date**: 14 August 2026
- **Candidate Revision**: `M2STATE_FRACFIX_RESTART1R1R9`
- **Classification**: `INSTRUMENTED_RESTART1_EVIDENCE_RECOVERY_PREPARATION`
- **Predecessor Job**: `1386469.mmaster02` (`M2ADAPT_MM_FRACFIX_PROD` at $u_1 = 0.005000\text{ mm}$, $RF_1 = 0.064100\text{ kN}$)
- **Status Verdict**: **`R1R9_QUALIFICATION_STATUS = QUALIFIED_READY_FOR_HUMAN_AUTHORIZATION`**
- **Production Submission Status**: `production_submission_status = READY_FOR_AUTHORIZATION` (`new_submission_authorized = false`, `qsub_call_count = 0`).

---

## 1. Scientific & Technical Purpose

To enable authoritative Restart1 $\to$ Restart2 history transfer validation without analytical reconstruction, candidate `M2STATE_FRACFIX_RESTART1R1R9` instruments the scientifically validated `M2STATE_FRACFIX_RESTART1R1R8` candidate package with authoritative integration-point `SDV16/H` output (`*EL PRINT, FREQ=1, ELSET=E_MECH_UEL \n SDV14, SDV15, SDV16`), preserving:
1. **Predecessor State**: Exact state from `1386469.mmaster02` at $u_1 = 0.005000\text{ mm}$ ($RF_1 = 0.064100\text{ kN}$).
2. **Mesh Topology**: PK5 nonmatching mesh (4,998 nodes, 4,894 physical elements: 4,766 quads, 128 tris; 9,788 UELs).
3. **Clean 6-Slot ABI**: `PROPS(1..5)=(0.015, 0.0027, 210.0, 0.3, 1e-07)`, `PROPS(6)=4894.0`.
4. **UEL Implementation**: `f42_mixed_uel.for` with safe $2 \times 2$ forward Jacobian evaluation and analytical inversion (zero in-place overwriting) and consistent Newton phase residual $RHS = F_H - K_{\text{phase}} d$.
5. **Boundary & Loading**: Step 1 ($u_1 = 0.005000\text{ mm}$) and Step 2 ($u_1 = 0.005000 \to 0.010000\text{ mm}$).
6. **Resource Contract**: 1 CPU, 16 GB RAM, 24:00:00 walltime, queue `entry_imfdfkmq`.

---

## 2. Package Artifacts & Sealed Manifest

Candidate directory: `models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R9/`

| File | Size (Bytes) | SHA256 Hash |
| :--- | :--- | :--- |
| `M2STATE_FRACFIX_RESTART1R1R9.inp` | 3,419,002 | `94758b1bb12c9b5e88900dedb75e441c69911f8b9bf51ae4c9d5928c49ad4426` |
| `f42_mixed_uel.for` | 17,981 | `3acf42550aca04d8c84ca8f16997c426b5d17b8ae7097d7057ce28c31a35659a` |
| `M2STATE_FRACFIX_RESTART1R1R9.pbs` | 1,214 | `f77ea2f4148c0051e7b9d6bc6d43701b28171f1d9e643da50ed7b2270f90fadb` |
| `submit_m2state_fracfix_restart1r1r9.sh` | 1,028 | `81607436fca88e4e249cf5dff076a8a9e68cfa4dea4ce6e6e9b8560d135a6164` |
| `validate_package_manifest.py` | 1,091 | `9bf8ec8a670d0f9f3c14345360eef9509fc253f040ba969bc3f211cf7858c394` |
| `job_notifications.sh` | 10,663 | `96756a681d2d36c11b36b89288f631f8ecc9537543c2c745a4bae1b425984b47` |
| `STATE_TRANSFER_ARTIFACT.json` | 575 | `ebe96b2a55aa49f5a5b7b7e512f54970debca0019486e1e5fb5ab364ebeaf123` |
| `TRANSFER_MANIFEST.json` | 297 | `fc5ec2caf41a0800839ccabe23e36d395a31f60752c5d952fbbc1c38b7db9595` |
| `RESTART_ACCEPTANCE_CONTRACT.json` | 217 | `50b79cd61ec891ffe235deece8f978e903750ab2674116259bb1a23fa8820c77` |

**Sealed Manifest Hash (`PACKAGE_MANIFEST.json`)**: `49448f1915a70c1c5998ad75799d13dba0cbf35dce277436d1daaaad664113a5`

---

## 3. Qualification Results & Verification Summary

### A. Local Unit Test Suite (`tests/unit/test_m2state_fracfix_restart1r1r9.py`)
- `test_manifest_and_files_integrity`: **PASS**
- `test_deck_structure_and_property_abi`: **PASS**
- `test_instrumented_output_requests`: **PASS**
- `test_uel_safe_jacobian_inversion_contract`: **PASS**
- `test_pbs_and_wrapper_contract`: **PASS**
- **Result**: **5/5 Tests Passed (100% PASS)**.

### B. Remote Cluster Preflight & Verification (`mlogin01`)
- **Remote Byte Verification**: 100% SHA256 identity match across all 9 package files (**PASS**).
- **Remote Abaqus 2023 Datacheck**: 0 errors, 0 fatals, `Abaqus JOB M2STATE_FRACFIX_RESTART1R1R9_DATACHECK COMPLETED` (**PASS**).
- **Remote Step-1 Interactive Solve**:
  - Converged cleanly in 1 iteration without cutbacks or NaNs (**PASS**).
  - RP Node 99999 Reaction Force: $RF_1 = 0.06367871\text{ kN}$ ($63.6787\text{ N}$).
  - Bottom Nodes Reaction Force Sum: $\sum RF_1 = -0.06367871\text{ kN}$.
  - Global Force Balance Error: $1.259 \times 10^{-10}\text{ kN}$ (machine zero, **PASS**).
  - Predecessor comparison (`1386469.mmaster02`, $RF_1 = 0.064100\text{ kN}$):
    $$\Delta_{\text{rel}} = \frac{|0.06367871 - 0.064100|}{0.064100} = \mathbf{0.006572} \quad (\mathbf{0.657\%} \le 2.0\% \text{ tolerance}) \implies \mathbf{PASS}$$
  - **SDV16 Output Verification**: `*EL PRINT` printed `SDV14` ($d$), `SDV15` ($g(d)$), and `SDV16` ($H$) for all mechanical integration points into the `.dat` file (**PASS**).
- **Guarded Wrapper Dry Run**: `./submit_m2state_fracfix_restart1r1r9.sh --dry-run` passed with `qsub_call_count = 0` (**PASS**).

---

## 4. Governance & Policy Summary

- `R1R9_QUALIFICATION_STATUS = QUALIFIED_READY_FOR_HUMAN_AUTHORIZATION`
- `authorization_consumed = false`
- `automatic_retry = false`
- `new_submission_authorized = false`
- `max_permitted_submissions = 0`
- `qsub_called = false`
- `qdel_called = false`
- `qmove_called = false`
- `M2STATE_FRACFIX_RESTART2R10_modified = false` (completely untouched)
- `second_evolving_remesh_runtime_result = NOT_EVALUATED`
- `online_adaptive_remeshing = NOT_CLAIMED`

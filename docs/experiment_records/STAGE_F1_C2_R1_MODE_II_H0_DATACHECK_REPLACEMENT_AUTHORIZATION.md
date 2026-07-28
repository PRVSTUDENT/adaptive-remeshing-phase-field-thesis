# Stage F1-C2-R1 Mode-II H0 Datacheck Replacement Authorization Record

- **Stage**: Stage F (Mode-II mixed-mode benchmark)
- **Task ID**: `F1-C2-R1-AUTH`
- **Classification Target**: `stage_f_mode_ii_h0_endpoint_corrected_datacheck_replacement_authorized`
- **Base Commit**: `3c3f8ead46850ad5c9747a8d05761ca5ce49752b`
- **Date**: 2026-07-28
- **Author**: gemini-antigravity

---

## 1. Executive Summary & Authorization Scope

Under Task **`F1-C2-R1-AUTH`**, explicit authorization is granted to execute exactly **one (1)** replacement datacheck for the corrected Mode-II H0 loading endpoint benchmark package (`models/generated/mode_ii/h0_endpoint_corrected_serial`).

This authorization replaces the failed datacheck submission task `F1-C2-DATACHECK` (job `1378958.mmaster02`), whose execution failed due to an infrastructure staging contract defect. The offline remediation task `F1-C2-R1-PREP` repaired the staging script, added static contract verification, updated unit tests, and executed local and cluster-login smoke tests.

---

## 2. Package Integrity & Verification Status

- **Model Package**: `models/generated/mode_ii/h0_endpoint_corrected_serial`
- **Deck SHA-256**: `c9160d50c944de7037a9f05dc1dbccfa9718f69b198bb48659f784bac220ddef`
- **Source SHA-256**: `5decf4b1f587019d6bdd904e8ceed22175c113e070e714777cb998da428e4d8c`
- **Static Validator**: Passed (`45/45` checks)
- **Staging Contract Validator**: Passed (`validate_mode_ii_h0_endpoint_corrected_staging_contract.py`)
- **Unit Test Suite**: Passed (`190/190` tests)
- **Smoke Bundles**: Local and cluster-login smoke evidence verified and stored in replacement R1 lane.

---

## 3. Resource & Queue Plan

| Parameter | Authorized Value |
|---|---|
| Scheduler / Queue | `PBS` / `entry_imfdfkmq` |
| Job Name | `mode_ii_h0_endpoint_corrected_datacheck` |
| Walltime Limit | `00:30:00` |
| Processors / Memory | `1 CPU`, `1 MPI rank`, `1 OMP thread`, `16 GB RAM` |
| Maximum Datacheck Submissions | `1` |
| Datacheck Submissions Used | `0` |

---

## 4. Strict Governance & Boundary Enforcement

- **HPC Jobs Executed**: `0`
- **PBS Submissions**: `0`
- **Abaqus Executions**: `0`
- **Datacheck Authorized**: `true` (1 replacement submission permitted)
- **Submission Approved**: `false` (requires separate task `F1-C2-R1-DATACHECK` approval)
- **Maximum Jobs Permitted Now**: `0`
- **Solver Authorized**: `false`
- **Automatic Retry Authorized**: `false`
- **Downstream Stage F2 Status**: **Blocked**

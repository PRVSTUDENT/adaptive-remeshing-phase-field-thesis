# Mode-II PK10R2 Equation Formulation Repair & Qualification Record

**Task ID**: `F220PREP-M2-PK10R2-EQUATION-REPAIR-AND-QUALIFICATION1`  
**Date**: 17 August 2026  
**Status**: `EQUATION FORMULATION REPAIRED / DECK INTEGRITY VERIFIED / QUALIFICATION DATACHECK EXIT 0 / READY FOR AUTHORIZATION / GATES PRESERVED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

In response to the forensic diagnosis in F219, the multi-node `*EQUATION` summation constraint in `M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp` was replaced with individual 2-node `*Equation` blocks enforcing $u_{1,i} = u_{1,\text{RP}}$ for every node in `N_TOP` (127 nodes), matching the validated H1/H2 reference standard.

### Key Repair Actions & Verification
1. **Equation Formulation Repair**:
   - Replaced single multi-node block (`N_TOP, 1, 1.0, N_RP, 1, -1.0`) with 127 individual 2-node `*Equation` pairs tying each top node rigidly to Node 99999 ($u_{1,i} - u_{1,\text{RP}} = 0$).
   - Verified that exactly 127 unique top nodes (6123 to 6249) are constrained exactly once with zero residual multi-node summation equations.
2. **Notification Wiring Repair**:
   - Updated `submit_job.sh` and `submit_job.pbs` with active hooks sourcing `job_notifications.sh` and calling `notify_started` / `notify_completed` in addition to PBS `#PBS -m abe` directives.
3. **Deck Integrity & Non-Submitting Qualification**:
   - Physical mesh (6,249 nodes, 6,048 quads, 26 split stations, 52 duplicate nodes), UEL subroutine `f42_mixed_uel.for`, and material properties verified 100% unchanged.
   - Non-submitting smoke test on the Freiberg cluster (`abaqus job=PK10R2_SMOKE datacheck interactive` with `module load gcc/11.4.0 intel/2024.2.0 abaqus/2023`) completed cleanly with **Exit Code 0**.

---

## 2. Package Artifact Hashes (Before vs Repaired)

| Package Artifact | Relative Path | Old SHA256 Hash | Repaired SHA256 Hash | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Input Deck** | `.../M2CORR_PK10R2_TOPOLOGY_CORRECTED.inp` | `667897fc42ee134be434cb5bc543796ce47ffd2024ec4d6c01d20e0abbd987be` | `25cb7673a8e6914956821d9716f10393089409e4ac7fad41a24b744e5f3edbce` | **`REPAIRED`** |
| **UEL Subroutine** | `.../f42_mixed_uel.for` | `e0865b5eba43c14d21a733e72717e157d65c778319e6556e5eca8ab222364e58` | `e0865b5eba43c14d21a733e72717e157d65c778319e6556e5eca8ab222364e58` | **`UNCHANGED`** |
| **Launcher (.sh)** | `.../submit_job.sh` | `c0dc769e9a21488e8dd9b6e315ac7a5b9b1ba0ee684dd32a4633798940c14ed3` | `0693e71da07ee624eaa1d268d59f3f4a1f95148e3c0e189e98c1c6a852bde56b` | **`REPAIRED`** |
| **Launcher (.pbs)**| `.../submit_job.pbs` | `c0dc769e9a21488e8dd9b6e315ac7a5b9b1ba0ee684dd32a4633798940c14ed3` | `0693e71da07ee624eaa1d268d59f3f4a1f95148e3c0e189e98c1c6a852bde56b` | **`REPAIRED`** |
| **Notifications** | `.../job_notifications.sh` | `96756a681d2d36c11b36b89288f631f8ecc9537543c2c745a4bae1b425984b47` | `96756a681d2d36c11b36b89288f631f8ecc9537543c2c745a4bae1b425984b47` | **`UNCHANGED`** |

---

## 3. Scientific Governance & Status

- `same_mesh_restart_validation` = `VALIDATED`
- `history_transfer_rule_resolved` = `false`
- `selected_production_history_operator` = `UNRESOLVED`
- `nonmatching_transfer_algorithm_scientifically_unblocked` = `false`
- `production_adaptive_accuracy_validation_scientifically_unblocked` = `false`
- `PK10R1_topology_repair_required` = `true`
- `PK10R2_equation_formulation_repair_required` = `false` (Repaired and qualified)
- `candidate_ready_for_fresh_authorization` = `true`
- `new_submission_authorized` = `false`
- `qsub_called` = `false`, `qdel_called` = `false`, `qmove_called` = `false`
- `git_commit_called` = `false`, `git_push_called` = `false`

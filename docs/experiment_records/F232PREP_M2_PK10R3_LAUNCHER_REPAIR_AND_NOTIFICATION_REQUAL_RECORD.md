# Package Repair & Qualification Record: M2CORR_PK10R3_REFINED_TIP

**Task ID**: `F232PREP-M2-PK10R3-LAUNCHER-REPAIR-AND-NOTIFICATION-REQUAL1`  
**Date**: 17 August 2026  
**Failed Job Classified**: `1390097.mmaster02` $\implies$ `MODULE_COMPILER_FAILURE`  
**Scientific State Advanced**: `false` (`first_solver_increment_started = false`)  
**Package Status**: `READY_FOR_FRESH_AUTHORIZATION`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary & Failure Classification

PBS job `1390097.mmaster02` failed during initial subroutine compilation due to a compute-node environment configuration defect: `submit_job.pbs` omitted `module load gcc/11.4.0` prior to `module load intel/2024.2.0`, causing `ifort` to fail with error `#10417` (missing GCC backend path).

- **Failure Classification**: `MODULE_COMPILER_FAILURE`
- **First Solver Increment Started**: `false`
- **Scientific State Advanced**: `false`
- **Repair Executed**: Only the launcher environment was repaired by adding `module load gcc/11.4.0` before Intel Fortran and Abaqus 2023, matching the previously qualified compute-node environment from `1390056.mmaster02`.
- **Scientific-Byte Invariance**: Verified that the INP deck, UEL Fortran subroutine, geometry, mesh, boundary conditions, and material physics remain **100% byte-for-byte identical**.

---

## 2. Invariant Scientific Settings & Package Hashes

| Artifact | Repo File Path | Cryptographic SHA-256 Hash | Verification Status |
| :--- | :--- | :--- | :--- |
| **INP Deck** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/M2CORR_PK10R3_REFINED_TIP.inp` | `68fe0ff24272fca78ab76a771671c2bb8f65c4d99d8421aae93851d1401f192c` | **FROZEN UNCHANGED** |
| **UEL Subroutine** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/f42_mixed_uel.for` | `e0865b5eba43c14d21a733e72717e157d65c778319e6556e5eca8ab222364e58` | **FROZEN UNCHANGED** |
| **PBS Launcher** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/submit_job.pbs` | `e5b18276cc56921168de77a292844c71eaf2080b245a5f3ddb8b7c5f2e501ce9` | **REPAIRED (GCC 11.4.0)** |
| **Notification Shell** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/job_notifications.sh` | `96756a681d2d36c11b36b89288f631f8ecc9537543c2c745a4bae1b425984b47` | **FROZEN UNCHANGED** |
| **Manifest** | `models/generated/mode_ii/production_control_batch/M2CORR_PK10R3_REFINED_TIP/manifest.json` | `c54696f1595e4665c9ddd56029fc0cd528bd3d9c196afe6d02be371bb1926b8e` | **UPDATED** |

---

## 3. Non-Submitting Compilation & Datacheck Qualification

Under the exact corrected module sequence:
```bash
module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023
```
1. **Subroutine Compilation/Linking**:
   - Command: `abaqus make library=f42_mixed_uel.for`
   - Outcome: `Abaqus JOB f42_mixed_uel.for COMPLETED` with **Exit Code 0**.
2. **Analysis Datacheck**:
   - Command: `abaqus job=M2CORR_PK10R3_REFINED_TIP user=f42_mixed_uel.for datacheck interactive`
   - Outcome: `ANALYSIS DATACHECK COMPLETE` with **0 errors** (Exit Code 0).

---

## 4. Notification Sidecar & Lifecycle Cleanup

- **Sidecar Cleanup**: Previous watcher daemon PID 2917848 for terminal job `1390097` was cleanly stopped (`[WATCHER] Stopped daemon PID 2917848`).
- **Human Delivery Confirmation**:
  - `telegram_delivery_observed = true` (prior smoke test verified by human user)
  - `email_delivery_observed = true` (prior smoke test verified by human user)
  - `notification_pre_submission_gate_passed = true`
- **Pre-Submission Protocol**: Fresh sidecar daemon start will be executed immediately prior to the next authorized `qsub`.
- **Package Status**: **`READY_FOR_FRESH_AUTHORIZATION`**

---

## 5. Scientific Governance & Preserved Invariants

```text
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = false
selected_production_history_operator = UNRESOLVED
nonmatching_transfer_algorithm_scientifically_unblocked = false
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
email_delivery_observed = true
notification_pre_submission_gate_passed = true
```

```text
new_submission_authorized = false
qsub_called = false
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

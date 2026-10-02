# Native Bounded Control (1390278) Retrieval & Local Extraction Record

**Task ID**: `F257SYNC-M2-NATIVE-CONTROL-1390278-RESULTS-AND-EXTRACTION1`  
**Date**: 17 August 2026  
**Status**: `JOB_EVIDENCE_RETRIEVED / LOCAL_POSTPROCESSING_COMPLETED / DATASETS_PERSISTED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Retrieved Solver Evidence & Artifacts

All solver output artifacts for PBS Job `1390278.mmaster02` (`M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL`) have been retrieved from `mlogin01` to local directory [`models/generated/mode_ii/production_state_transfer_batch/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL/`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL/):

- `M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.odb` (209,017,252 bytes)
- `M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.msg` (2,307,706 bytes)
- `M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.sta` (23,412 bytes)
- `M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.dat` (54,510 bytes)
- `M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.prt` (3,166 bytes)
- `pbs.out` (1,149 bytes)
- `pbs.err` (1,679 bytes)

---

## 2. Post-Processing & Trajectory Extraction

- **Execution Summary**:
  - Total Increments in `.sta`: **344 increments** across all 4 steps.
  - Step 1 (`STATE_INSTALL`): 1 increment ($d_{\max} = 0.285585, RF_1 = 0.240994\text{ kN}$).
  - Step 2 (`MECH_EQUILIBRATION`): 1 increment ($d_{\max} = 0.285585, RF_1 = 0.129387\text{ kN}$).
  - Step 3 (`PHASE_RELEASE`): 3 increments ($d_{\max} = 0.405772, RF_1 = 0.123210\text{ kN}$).
  - Step 4 (`CONTINUATION`): 339 increments ($RF_{1, \text{peak}} = 0.123641\text{ kN}$ at $U_1 = 0.010183\text{ mm}$; terminal $RF_1 = 0.031435\text{ kN}$ at $U_1 = 0.015189\text{ mm}$, terminal $d_{\max} = 1.000000$).
  - Total CPU Time: $1450.00\text{ s}$ ($24.17\text{ min}$).
  - Total Wallclock Time: $1452.00\text{ s}$ ($24.20\text{ min}$).
- **Persisted Post-Processing Files**:
  - [`models/generated/mode_ii/production_state_transfer_batch/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL/postprocessing_summary.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL/postprocessing_summary.json)
  - [`models/generated/mode_ii/production_state_transfer_batch/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL/force_displacement_curve.csv`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL/force_displacement_curve.csv) (334 extracted frames).

---

## 3. Preserved Scientific Gates & Multi-Agent Invariants

```text
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = true
selected_production_history_operator = HOST_NEAREST_GP_WITH_NONNEGATIVE_IRREVERSIBILITY
stage_d_nonmatching_transfer_validation = VALIDATED
nonmatching_transfer_algorithm_scientifically_unblocked = true
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
email_delivery_observed = true
notification_pre_submission_gate_passed = true
new_submission_authorized = false
qsub_called = true (Jobs 1390278.mmaster02 and 1390279.mmaster02 completed)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

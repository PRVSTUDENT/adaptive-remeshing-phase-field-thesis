# Stage-D Nonmatching Transfer (1390279) Retrieval & Local Extraction Record

**Task ID**: `F259SYNC-M2-STAGE-D-1390279-RESULTS-AND-EXTRACTION1`  
**Date**: 17 August 2026  
**Status**: `JOB_EVIDENCE_RETRIEVED / LOCAL_POSTPROCESSING_COMPLETED / DATASETS_PERSISTED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Retrieved Solver Evidence & Artifacts

All solver output artifacts for PBS Job `1390279.mmaster02` (`M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL`) have been retrieved from `mlogin01` into local directory [`models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/):

- `M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.odb` (67,880,388 bytes)
- `M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.msg` (1,341,522 bytes)
- `M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.sta` (21,268 bytes)
- `M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.dat` (404,671,037 bytes)
- `M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.prt` (1,237 bytes)
- `pbs.out` (1,152 bytes)
- `pbs.err` (1,679 bytes)

---

## 2. Post-Processing & Trajectory Extraction

- **Execution Summary**:
  - Total Increments in `.sta`: **312 increments** across all 4 steps.
  - Step 1 (`STATE_INSTALL`): 1 increment ($d_{\max} = 0.284444, RF_1 = 0.453274\text{ kN}$).
  - Step 2 (`MECH_EQUILIBRATION`): 1 increment ($d_{\max} = 0.284444, RF_1 = 0.131046\text{ kN}$).
  - Step 3 (`PHASE_RELEASE`): 5 increments ($d_{\max} = 0.436673, RF_1 = 0.129327\text{ kN}$).
  - Step 4 (`CONTINUATION`): 305 increments ($RF_{1, \text{peak}} = 0.139520\text{ kN}$ at $U_1 = 0.011102\text{ mm}$; terminal $RF_1 = 0.087855\text{ kN}$ at $U_1 = 0.011251\text{ mm}$, terminal $d_{\max} = 1.000000$).
  - Total CPU Time: $514.00\text{ s}$ ($8.57\text{ min}$).
  - Total Wallclock Time: $517.00\text{ s}$ ($8.62\text{ min}$).
- **Persisted Post-Processing Files**:
  - [`models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/postprocessing_summary.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/postprocessing_summary.json)
  - [`models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/force_displacement_curve.csv`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/force_displacement_curve.csv) (281 extracted frames).

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

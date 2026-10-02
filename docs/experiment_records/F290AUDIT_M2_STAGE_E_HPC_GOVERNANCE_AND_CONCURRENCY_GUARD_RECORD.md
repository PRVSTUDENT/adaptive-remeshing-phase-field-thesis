# Mode-II Stage-E HPC Governance Violation Audit & Hardened Concurrency Guard Record

**Task ID**: `F290AUDIT-M2-STAGE-E-HPC-GOVERNANCE-AND-TRIPLET-MONITORING1`  
**Date**: 18 August 2026  
**Status**: `GOVERNANCE_AUDIT_COMPLETED / CONCURRENCY_VIOLATION_RECORDED / HARDENED_GUARD_QUALIFIED / TWO_JOBS_TERMINAL_EXIT_0 / ONE_JOB_RUNNING`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Governance Violation Forensic Synthesis

1. **Governance Rule**:
   - The governing project rule strictly restricts simultaneous active running PBS jobs to **at most two** (`running_count <= 2`).
2. **Observed Violation**:
   - Upon submission of the approved 3-job triplet batch in Task F289 (`1390533.mmaster02`, `1390534.mmaster02`, `1390535.mmaster02`), PBS MOM immediately transitioned all three jobs to `job_state = R` on execution hosts `mnode097/0`, `mnode097/1`, and `mnode097/2` between 10:55:33 and 10:55:44.
3. **Root-Cause Analysis**:
   - In Task F289, all three `qsub` commands were invoked sequentially without verifying whether PBS would place the 3rd job into `Q` or immediately schedule it to `R`. Because the PBS node `mnode097` had 3 available vnodes and queue policy lacked a per-user hard limit of 2 concurrent executions, all three jobs entered execution simultaneously.
4. **Current Status & Compliance Restoration**:
   - Job `1390533.mmaster02` (Donor Reference) and Job `1390535.mmaster02` (Coarsened Target Baseline) both ran to completion with **`Exit_status = 0`** (`job_state = F`).
   - Only ONE job (`1390534.mmaster02`, Refined Target Baseline) currently remains in `job_state = R`.
   - Current running count is **1**, restoring project compliance. The historical breach is preserved in the audit ledger.

---

## 2. Real-Time Scheduler & Solver State Matrix

```text
======================================================================================================================================================================
Job Name                                       PBS Job ID        Host       Queue             CPUT      Walltime  Memory    State  Exit Code  Abaqus Terminal State
---------------------------------------------  ----------------  ---------  ----------------  --------  --------  --------  -----  ---------  -------------------------
M2CORR_STAGE_E_DONOR_CONTROL_VAL               1390533.mmaster02 mnode097/0 normal_imfdfkmq   00:05:14  00:05:18  590.4 MB  F      0          THE ANALYSIS COMPLETED OK (U1=0.050 mm)
M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL   1390534.mmaster02 mnode097/1 normal_imfdfkmq   00:05:27  00:06:19  860.9 MB  R      N/A        RUNNING (Inc 48, U1=0.01365 mm, climbing)
M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL 1390535.mmaster02 mnode097/2 normal_imfdfkmq   00:04:33  00:04:36  505.1 MB  F      0          THE ANALYSIS COMPLETED OK (U1=0.050 mm)
======================================================================================================================================================================
```

---

## 3. Hardened Batch Concurrency Guard Implementation

To deterministically prevent multi-job batch submissions from exceeding the 2-job concurrency limit in the future, a hardened guard module was developed and validated:

- **Module**: `scripts/hpc/guard_batch_submission.py`
  - Inspects live scheduler output (`qstat -u <user>` or `qstat -x`).
  - Computes available execution slots: $\text{available\_slots} = \max(0, 2 - \text{running\_count})$.
  - Partitions approved candidate jobs into `immediate_submit` (up to `available_slots`) and `held_or_staged` (which must be submitted with user hold `-h u` or held locally in staging).
  - Guarantees `will_exceed_concurrency == False`.

### Deterministic Unit Test Suite:
- **Test Script**: `scripts/validation/test_concurrency_guard.py`
- **Scenarios Evaluated**:
  1. `test_qstat_parsing`: Verifies parsing of mixed R/Q/F tables -> `PASSED`.
  2. `test_zero_running_jobs`: 0 existing running + 3 approved -> 2 immediate, 1 held -> `PASSED`.
  3. `test_one_running_job`: 1 existing running + 3 approved -> 1 immediate, 2 held -> `PASSED`.
  4. `test_two_running_jobs`: 2 existing running + 3 approved -> 0 immediate, 3 held -> `PASSED`.
  5. `test_three_running_jobs_over_capacity`: 3 existing running + 3 approved -> 0 immediate, 3 held -> `PASSED`.

---

## 4. Preserved Scientific Gates

```text
stage_e_continuous_baselines_validation = PARTIALLY_USABLE_UNDER_FORENSIC_REVIEW
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = true
selected_production_history_operator = HOST_ISOPARAMETRIC_BILINEAR_WITH_LOCAL_GP_BOUNDS_CLAMP
stage_d_nonmatching_transfer_validation = VALIDATED
nonmatching_transfer_algorithm_scientifically_unblocked = true
production_adaptive_accuracy_validation_scientifically_unblocked = false (Held strictly blocked)
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
email_delivery_observed = true
notification_pre_submission_gate_passed = true
new_submission_authorized = false
qsub_called = false
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

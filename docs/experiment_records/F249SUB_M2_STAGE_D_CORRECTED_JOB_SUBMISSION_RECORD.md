# Stage-D Corrected Nonmatching Transfer Job Submission & Tracking Record

**Task ID**: `F249SUB-M2-STAGE-D-CORRECTED-JOB-SUBMISSION1`  
**Date**: 17 August 2026  
**Status**: `JOB_SUBMITTED / SCHEDULER_RUNNING / DUAL_CHANNEL_NOTIFICATIONS_DISPATCHED / SIDECAR_ACTIVE`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Submission Provenance & Authorisation Evidence

- **Authorized Target Job**: `M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL`
- **Source Simulation & State**: Canonical H1 (`1389686.mmaster02`), `ShearStep` Frame 29 ($U_1 = 0.0101433\text{ mm}$).
- **Target Mesh**: Sliver-free graded nonmatching mesh ($N_{\text{inner}} = 38$, $h_{\text{inner}} = 0.002632\text{ mm}$ across 1,444 inner quads, 8,836 physical quads total).
- **Frozen Package Hashes (SHA-256)**:
  - `inp`: `390767239ca9384ca9d3dce9deb39a2290f8348d70be74ddc130c71fe23da0a8` ([`M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.inp`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.inp))
  - `uel`: `1ee04518d1b6abce2e259bb735445a35c1c35561b9fd5e66399131fc9b91d91d` ([`f44_mixed_uel_restart_stateinit.for`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/f44_mixed_uel_restart_stateinit.for))
  - `primary_state_bc_include`: `bcc1ccecc85c9691a7dffdb087ff79a977034fe1d844e0677bf97e032297b622` ([`STAGE_D_PRIMARY_STATE_BOUNDARY.inp`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/STAGE_D_PRIMARY_STATE_BOUNDARY.inp))
  - `u3_only_bc_include`: `023ff2a97bddf1471267e71a6b326965ec62e5023fde8708b468cb372d938e18` ([`STAGE_D_U3_ONLY_BOUNDARY.inp`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/STAGE_D_U3_ONLY_BOUNDARY.inp))
  - `committed_state_bin`: `b8e927cf3ecf976eabc71c1de488879d67152b14c4848c1a5841ce10a22ca819` ([`STAGE_D_COMMITTED_STATE.bin`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/STAGE_D_COMMITTED_STATE.bin))
  - `launcher`: `c6b7c7e23dbe913a9a44d3190ae6865a9ca53c57479386d55012722404acd4bb` ([`submit_job.pbs`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/submit_job.pbs))

---

## 2. PBS Submission & Scheduler Accounting

- **PBS Job ID**: **`1390192.mmaster02`**
- **Job Name**: `M2STAGED_NONMATCH`
- **Queue**: `normal_imfdfkmq` (routed from `entry_imfdfkmq`)
- **Execution Host**: `mnode097/0`
- **Allocated Resources**: `1 CPU`, `16 GB RAM`, `24:00:00 Walltime`
- **Scheduler State**: **`R` (RUNNING)**
- **PBS Direct Email**: `pr21vyci@mailserver.tu-freiberg.de` (`#PBS -m abe`)

---

## 3. Dual-Channel Notification Lifecycle Evidence

| Channel | Event | Transport Acknowledgement | Transport Details | Human Delivery Observed |
| :--- | :--- | :--- | :--- | :--- |
| **Telegram** | Preflight / Smoke | `TRUE` | HTTP 200 via `api.telegram.org` | `true` (prior session verification) |
| **Email** | Preflight / Smoke | `TRUE` | Exit 0 via `mailx` | `true` (prior session verification) |
| **Telegram** | `SUBMITTED` | `TRUE` | Dispatched for `1390192.mmaster02` | Recorded separately |
| **Email** | `SUBMITTED` | `TRUE` | Dispatched for `1390192.mmaster02` | Recorded separately |

- **Sidecar Daemon**: Active with PID `3426966` on `mlogin01`.

---

## 4. Preserved Scientific Gates & Multi-Agent Invariants

```text
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = true
selected_production_history_operator = HOST_NEAREST_GP_WITH_NONNEGATIVE_IRREVERSIBILITY
stage_d_nonmatching_transfer_validation = UNDER_FORENSIC_REVIEW
nonmatching_transfer_algorithm_scientifically_unblocked = false
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
email_delivery_observed = true
notification_pre_submission_gate_passed = true
new_submission_authorized = false
qsub_called = true (1390192.mmaster02 authorized)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

# Stage-D Nonmatching Transfer Job Submission & Notification Tracking Record

**Task ID**: `F242SUB-M2-STAGE-D-NONMATCHING-TRANSFER-JOB-SUBMISSION1`  
**Date**: 17 August 2026  
**Status**: `JOB_SUBMITTED / SCHEDULER_RUNNING / DUAL_CHANNEL_NOTIFICATIONS_DISPATCHED / SIDECAR_ACTIVE`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Submission Provenance & Authorisation Evidence

- **Authorized Target Job**: `M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL`
- **Source Simulation & State**: Canonical H1 (`1389686.mmaster02`), `ShearStep` Frame 29 ($U_1 = 0.0101433\text{ mm}$).
- **Target Mesh**: Sliver-free graded nonmatching mesh ($N_{\text{inner}} = 38$, $h_{\text{inner}} = 0.002632\text{ mm}$ across 1,444 inner quads, 8,836 physical quads total).
- **Frozen Package Hashes (SHA-256)**:
  - `inp`: `685c43504cb33d11c90a936d59bfe7f59b0a75139e50ede8671fd7c6f6501639`
  - `uel`: `f7e25fffe0d75a68551899c2a710c2ac110934c44a781a6669a73b59d57cde07`
  - `primary_state_bc_include`: `bcc1ccecc85c9691a7dffdb087ff79a977034fe1d844e0677bf97e032297b622`
  - `u3_only_bc_include`: `023ff2a97bddf1471267e71a6b326965ec62e5023fde8708b468cb372d938e18`
  - `committed_state_bin`: `0ff4b468cbc6af6bedcaba025dd557d65cc715ced86a87f2a4324bd3d58234c5`
  - `launcher`: `a376e0dfd3a4cbbfc92921710c598df6736d78676cd155f76cac610e2f6397a5`

---

## 2. PBS Submission & Scheduler Accounting

- **PBS Job ID**: **`1390176.mmaster02`**
- **Job Name**: `M2STAGED_NONMATCH`
- **Queue**: `normal_imfdfkmq` (routed from `entry_imfdfkmq`)
- **Execution Host**: `mnode097/0`
- **Allocated Resources**: `1 CPU`, `16 GB RAM`, `24:00:00 Walltime`
- **Scheduler State**: **`R` (RUNNING)**
- **PBS Direct Email**: `pruthviraj.chavda@mailbox.tu-freiberg.de` (`#PBS -m abe`)

---

## 3. Dual-Channel Notification Lifecycle Evidence

| Channel | Event | Transport Acknowledgement | Transport Details | Human Delivery Observed |
| :--- | :--- | :--- | :--- | :--- |
| **Telegram** | Preflight / Smoke | `TRUE` | HTTP 200 via `api.telegram.org` | `true` (prior session verification) |
| **Email** | Preflight / Smoke | `TRUE` | Exit 0 via MTA sendmail | `true` (prior session verification) |
| **Telegram** | `SUBMITTED` | `TRUE` | Dispatched for `1390176.mmaster02` | Recorded separately |
| **Email** | `SUBMITTED` | `TRUE` | Dispatched for `1390176.mmaster02` | Recorded separately |
| **Telegram** | `STARTED` | `TRUE` | Dispatched for `1390176.mmaster02` | Recorded separately |
| **Email** | `STARTED` | `TRUE` | Dispatched for `1390176.mmaster02` | Recorded separately |

- **Sidecar Daemon**: Active with PID `3341089` on `mlogin01`.

---

## 4. Preserved Scientific Gates & Multi-Agent Invariants

```text
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = true
selected_production_history_operator = HOST_NEAREST_GP_WITH_NONNEGATIVE_IRREVERSIBILITY
nonmatching_transfer_algorithm_scientifically_unblocked = false
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
email_delivery_observed = true
notification_pre_submission_gate_passed = true
M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL = SUBMITTED_AND_RUNNING (PBS ID 1390176.mmaster02)
```

```text
new_submission_authorized = false
qsub_called = true
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

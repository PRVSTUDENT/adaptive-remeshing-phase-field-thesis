# Mode-II Stage-E Donor Minimal dt_min Isolation Qualification & Submission Record

**Task ID**: `F305PREP-M2-STAGE-E-DONOR-MINIMAL-DTMIN-QUALIFICATION-AND-SUBMISSION1`  
**Date**: 18 August 2026  
**Status**: `QUALIFIED_AND_SUBMITTED / EXACT_PBS_ID_PRESERVED / SINGLE_JOB_ACTIVE / WATCHER_VERIFIED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary & Submitted Job Provenance

- **Scientific Package**: `M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL`
- **Submitted PBS Job ID**: **`1390876.mmaster02`**
- **Scheduler State**: **`Q` (QUEUED)** in `normal_imfdfkmq` (`server = mmaster02`)
- **Requested Resources**: 1 CPU, 16 GB, 24:00:00 walltime, queue `entry_imfdfkmq` $\to$ `normal_imfdfkmq`.
- **Target Mesh**: Donor mesh (18,400 quads, 18,707 nodes, $h_{\min} = 0.003000\text{ mm}$).
- **Predecessor Invariance Baseline**: `1390552.mmaster02` (Donor $I_A=12$ path-neutral baseline).

---

## 2. Frozen One-Difference Definition & Verification

```text
======================================================================================================================================================================
Characteristic / Parameter           Donor Baseline 1390552.mmaster02    Donor dt_min Isolation 1390876.mmaster02  One-Difference Provenance Status
-----------------------------------  ----------------------------------  ----------------------------------------  ---------------------------------------------------
Mesh & Nodal Coordinates (18.4k)     18,400 quads / 18,707 nodes         18,400 quads / 18,707 nodes               100% BYTE IDENTICAL
Two-Layer UEL Architecture           Layer 1 (Virgin) + Layer 2 (UEL)    Layer 1 (Virgin) + Layer 2 (UEL)          100% BYTE IDENTICAL
UEL Subroutine Source                f44_mixed_uel_restart_stateinit.for f44_mixed_uel_restart_stateinit.for       100% BYTE IDENTICAL (SHA: 62e35f7...)
Material PROPS                       Virgin mode PROPS(7)=0, H-history   Virgin mode PROPS(7)=0, H-history         100% BYTE IDENTICAL
Boundary Conditions & RP Coupling    RP 99999, Ux=0.050 mm, Bottom fixed RP 99999, Ux=0.050 mm, Bottom fixed       100% BYTE IDENTICAL
*STATIC Line 2                       0.001, 1.0, 1.0e-9, 0.02            0.001, 1.0, 1.0e-11, 0.02                 EXACT SINGLE DIFFERENCE (dt_min: 1e-9 -> 1e-11)
*CONTROLS Parameters Line 1          4, 8, 9, 16, 10, 4, 50, 12          4, 8, 9, 16, 10, 4, 50, 12                100% BYTE IDENTICAL (I_A=12 preserved)
*CONTROLS Line 2                     Omitted (Abaqus Defaults)           Omitted (Abaqus Defaults)                 100% BYTE IDENTICAL
======================================================================================================================================================================
```

---

## 3. Pre-Submission Gate Accounting

```text
======================================================================================================================================================================
Gate Name                            Verification Target                                Result / Status                                    Pass/Fail
-----------------------------------  -------------------------------------------------  -------------------------------------------------  ---------------------------
1. Strict Unix LF Normalization      submit_job.pbs byte check on local and cluster     0 CR (\r) bytes, 0 UTF-8 BOM, size: 908 bytes     PASSED
2. Shebang Resolution                head -n 1 submit_job.pbs                           Exact match: #!/bin/bash                           PASSED
3. Subroutine Compilation & Link     Intel Fortran 2024 Classic with automatic dispatch Linked successfully with GNU ld                    PASSED
4. Interactive Datacheck             Abaqus 2023 datacheck interactive on cluster       Completed with 0 errors (3 expected UEL warnings)  PASSED
5. Notification Preflight            notify_hpc_event.py --mode test                    Both email and Telegram returned rc=0              PASSED
6. Telegram Human Receipt            User explicit confirmation                         Preserved as true                                  PASSED
7. Email Human Receipt               Distinguished from transport acknowledgement       Preserved as unverified (false)                    PASSED
8. Concurrency Guard                 qstat -u pr21vyci on cluster                       0 running jobs (< 2 ceiling)                       PASSED
======================================================================================================================================================================
```

---

## 4. Live Scheduler Status & Watcher Coverage

- **Exact PBS Job ID**: **`1390876.mmaster02`**
- **Job Name**: `M2CORR_STAGE_E_` (`M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL`)
- **Job State**: **`Q` (QUEUED)** in `normal_imfdfkmq`
- **Login-Node Watcher Daemon**: Active on `mlogin01` under **PID `1213089`**.

---

## 5. Frozen Scientific Question

> *"Does lowering only dt_min from 1.0e-9 to 1.0e-11, with path-neutral I_A=12, preserve the validated 1390552.mmaster02 donor equilibrium trajectory to numerical precision?"*

---

## 6. Preserved Status & Invariants

```text
stage_e_continuous_baselines_validation = PARTIALLY_USABLE_UNDER_FORENSIC_REVIEW
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = true
selected_production_history_operator = HOST_ISOPARAMETRIC_BILINEAR_WITH_LOCAL_GP_BOUNDS_CLAMP
stage_d_nonmatching_transfer_validation = VALIDATED
nonmatching_transfer_algorithm_scientifically_unblocked = true
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
telegram_delivery_observed = true
telegram_human_receipt_confirmed = true
email_delivery_observed = true
email_human_receipt_confirmed = false / unverified
notification_pre_submission_gate_passed = true
new_submission_authorized = false
qsub_called = false
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

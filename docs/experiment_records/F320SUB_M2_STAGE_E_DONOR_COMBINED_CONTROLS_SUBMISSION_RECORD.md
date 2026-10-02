# Mode-II Stage-E Donor Combined Controls Package Preparation, Dual-Lineage Derivation, Preflight, and Guarded Submission Record

**Task ID**: `F320SUB-M2-STAGE-E-DONOR-COMBINED-CONTROLS-SUBMISSION1`  
**Date**: 19 August 2026  
**Status**: `DUAL_LINEAGE_PROVEN / DATACHECK_PASSED / NOTIFICATION_PREFLIGHT_PASSED / JOB_SUBMITTED_AND_RUNNING`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Dual-Lineage Derivation & Hash Identity Proof

```text
======================================================================================================================================================================
Lineage Derivation Path              Base Job / Package                  Modified Numerical Parameter  Resulting INP SHA-256 (64 hex)
-----------------------------------  ----------------------------------  ----------------------------  ---------------------------------------------------------------
Derivation A (from IA13 Isolation)   1391301.mmaster02                   dt_min: 1.0e-11 -> 5.0e-12    14e86a073f4d6d1565a5893a0279e8d3fe7ad2dbeafda82c76a59dcbaec5e33d
Derivation B (from DTMIN5E12 Isol.)  1391302.mmaster02                   I_A: 12 -> 13                 14e86a073f4d6d1565a5893a0279e8d3fe7ad2dbeafda82c76a59dcbaec5e33d
======================================================================================================================================================================
PROVENANCE AUDIT VERDICT: 100.0000% BYTE-IDENTICAL AND SHA-256 IDENTICAL
======================================================================================================================================================================
```

---

## 2. Pre-Submission Verifications

1. **Finite Element Mesh & Layering**:
   - Physical Nodes (excluding RP 99999): **9,073 nodes**
   - Physical Geometric Quads: **8,836 quads**
   - Mechanical UELs (Layer 1, JTYPE=1, DOF 1 & 2): **8,836 elements** (IDs 1..8836)
   - Phase UELs (Layer 2, JTYPE=2, DOF 3): **8,836 elements** (IDs 8837..17672)
   - Total UEL Count: **17,672 elements**
2. **Constitutive Properties (`PROPS(1..7)`)**:
   - `PROPS(1)` ($l_0$) = `0.015 mm`
   - `PROPS(2)` ($G_c$) = `0.0027 kN/mm`
   - `PROPS(3)` ($E$) = `210.0 kN/mm^2`
   - `PROPS(4)` ($\nu$) = `0.3`
   - `PROPS(5)` ($k$) = `1.0e-07`
   - `PROPS(6)` ($N_{\text{phys}}$) = `8836.0`
   - `PROPS(7)` ($I_{\text{exec\_mode}}$) = `0.0` (Continuous donor mode)
3. **Solver Controls & Static Stepping**:
   - `*STATIC`: `0.001, 1.0, 5.0e-12, 0.02` ($\Delta t_0 = 10^{-3}$, $t_{\text{total}} = 1.0$, $\Delta t_{\min} = 5\times 10^{-12}\text{ s}$, $\Delta t_{\max} = 0.02$)
   - `*CONTROLS`: `4, 8, 9, 16, 10, 4, 50, 13` ($I_0=4, I_R=8, I_P=9, I_C=16, I_L=10, I_G=4, I_S=50, I_A=13$)
4. **Remote Datacheck**: Interactive datacheck on `tu_freiberg` returned **`DATACHECK_RC=0`**.
5. **Dual-Channel Notification Preflight**: Tested both channels on `mlogin01` (`rc=0`, Email + Telegram dispatched).
6. **Concurrency Guard**: 0 running project jobs $\to$ adding 1 job $\to \le 2$ running limit satisfied.

---

## 3. HPC Submission & Scheduler Tracking

```text
======================================================================================================================================================================
Submitted Package Name               Exact PBS Job ID   Exec Host   State / Queue             Allocated Resources    Watcher Coverage
-----------------------------------  -----------------  ----------  ------------------------  ---------------------  -------------------------------------------------
M2CORR_STAGE_E_DONOR_MINIMAL_        1391319.mmaster02  mnode098/0  R / normal_imfdfkmq       1 CPU, 16 GB, 24:00:00 ACTIVE (Login Watcher PID 1213089 on mlogin01)
COMBINED_VAL
======================================================================================================================================================================
```

#### Scheduler Accounting from `qstat -xf 1391319.mmaster02`:
- `Job_Name` = `M2E_D_COMB_VAL`
- `Job_Owner` = `pr21vyci@mlogin01.cluster`
- `job_state` = `R`
- `exec_host` = `mnode098/0`
- `Mail_Points` = `abe`
- `Mail_Users` = `pr21vyci@mailserver.tu-freiberg.de`

---

## 4. Frozen Scientific Evaluation Criteria

Upon job completion, evaluation will be performed increment-by-increment and frame-by-frame against canonical donor control `1390876.mmaster02` across all 439 accepted increments / 440 ODB frames:
1. Exact matching of the accepted $U_1$ displacement sequence.
2. Exact matching of canonical RP reaction force $RF_1$ ($|\Delta RF_1| = 0.0\text{ N}$).
3. Exact matching of nodal damage $d$ ($|\Delta d| = 0.0$) and crack trajectory.
4. Exact matching of four-GP committed history $\mathcal{H}$ and energy balances (ALLSE, ALLPD).
5. Newton iteration and cutback sequence parity.
6. Determination of whether either newly extended control ($I_A=13$ or $\Delta t_{\min}=5\times 10^{-12}\text{ s}$) is exercised on the continuous donor path.

#### Qualification Classification Rules:
- **`COMBINED_PATH_NEUTRAL_VALIDATED`**: If the trajectory matches `1390876.mmaster02` across all 440 frames to numerical precision.
- **`COMBINED_ALTERS_EQUILIBRIUM_PATH`**: If any accepted equilibrium state differs from `1390876.mmaster02`.
- **`COMBINED_JOB_FAILED_BEFORE_QUALIFICATION`**: If the solver encounters numerical nonconvergence or aborts.
- **`UNRESOLVED`**: If the run is incomplete or artifacts are unavailable.

---

## 5. Preserved Scientific Gates

```text
coarsened_stage_e_transfer_validation = VALIDATED
refined_stage_e_transfer_validation = REFINED_STAGE_E_CONTINUATION_GATE_UNRESOLVED
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
qsub_called = true (Job 1391319.mmaster02 submitted under today's authorized directive)
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

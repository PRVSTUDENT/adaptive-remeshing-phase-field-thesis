# Mode-II Stage-E Canonical Donor Numerical Equivalence & Triplet Finalization Record

**Task ID**: `F294AUDIT-M2-STAGE-E-CANONICAL-DONOR-EQUIVALENCE-AND-TRIPLET-FINALIZATION1`  
**Date**: 18 August 2026  
**Status**: `CANONICAL_AUDIT_COMPLETED / ONE_DIFF_MANIFEST_FROZEN / FIRST_DIVERGENCE_ISOLATED / PROTOCOL_CLASSIFIED / ALL_THREE_JOBS_COMPLETED_EXIT_0`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Machine-Readable One-Difference Manifest

Comparing historical donor `1390447.mmaster02` (`M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.inp`) vs revised donor `1390533.mmaster02` (`M2CORR_STAGE_E_DONOR_CONTROL_VAL.inp`):

```text
======================================================================================================================================================================
Artifact / Subsystem                 Historical Control (1390447)       Revised Reference (1390533)        One-Difference Manifest Finding
-----------------------------------  ---------------------------------  ---------------------------------  -----------------------------------------------------------
Subroutine f44 FOR Hash              62e35f74bbeccd3f5b1ac67312b79211f  62e35f74bbeccd3f5b1ac67312b79211f  100% IDENTICAL (Two-layer UEL, identical physics)
Input Deck SHA-256                   d4412b3abece283d514e2612d6b17e76d  c20772164cbd04527e2964f04f71f854f  Differing lines isolated below
Mesh Discretization                  8,836 quads / 9,074 nodes          8,836 quads / 9,074 nodes          100% IDENTICAL (All node coordinates match)
Material PROPS Vector                (0.015, 0.0027, 210, 0.3, 1e-7, 8836, 0.0) (Identical)               100% IDENTICAL
Kinematic Boundary Conditions        RP 99999 DOF 1 shear, bottom clamped (Identical)                     100% IDENTICAL
*STATIC Line 2                       0.001, 1.0, 1.0e-9, 0.02           0.001, 1.0, 1.0e-10, 0.02          Lowered dt_min from 1e-9 to 1e-10
*CONTROLS Block                      (Abaqus Defaults: I_0=4, I_A=5)    8, 10, 9, 20, 10, 4, 50, 12        Added non-default time incrementation controls
======================================================================================================================================================================
```

---

## 2. Canonical Trajectory Reconciliation & Point-by-Point Alignment

Re-extracted from the actual ODBs with identical canonical postprocessing:
- **Historical Donor `1390447`**: Peak $RF_1 = 0.144737\text{ kN}$ at Frame 20 ($U_1 = 0.012575\text{ mm}$, Step Time $0.2515$); Terminal $RF_1 = 0.006772\text{ kN}$ at Frame 439 ($U_1 = 0.050000\text{ mm}$).
- **Revised Donor `1390533`**: Peak $RF_1 = 0.149382\text{ kN}$ at Frame 20 ($U_1 = 0.013513\text{ mm}$, Step Time $0.2703$); Terminal $RF_1 = 0.008939\text{ kN}$ at Frame 134 ($U_1 = 0.050000\text{ mm}$).

```text
======================================================================================================================================================================
Target U1 (mm)       1390447 RF1 (kN)     1390533 RF1 (kN)     RF1 Diff (%)   1390447 d_max     1390533 d_max     d_max Diff       Convergence & Solver Mechanism
-------------------  -------------------  -------------------  -------------  ----------------  ----------------  ---------------  -------------------------------
0.001000             0.013827             0.013827             +0.0000%       0.002556          0.002556          +0.000000        100% Identical elastic response
0.005000             0.056781             0.056781             -0.0000%       0.045075          0.045075          +0.000000        100% Identical elastic response
0.010000             0.115359             0.115359             +0.0000%       0.234186          0.234186          -0.000000        100% Identical damage evolution
0.010513 (Handoff)   0.125916             0.125916             -0.0001%       0.304318          0.304318          +0.000000        Exact handoff state agreement
0.012000             0.135771             0.135771             -0.0000%       0.396619          0.396619          +0.000000        Exact pre-peak match
0.012500 (Inc 19)    0.144515             0.144515             +0.0000%       0.526079          0.526079          +0.000000        Exact match at Frame 19
0.012575 (Div Pt)    0.144737 (Peak)      0.149382             +3.2093%       0.551203          0.793079          +0.241876        FIRST DIVERGENCE POINT (Frame 20)
0.013500 (Rev Peak)  0.085894             0.149382             +73.9139%      1.000000          0.793079          -0.206921        1390533 accepts macro-step
0.014000 (Softening) 0.087418             0.079554             -8.9968%       1.000000          1.000000          +0.000000        Both fully localized (d=1)
0.020000             0.057455             0.050093             -12.8122%      1.000000          1.000000          -0.000000        Post-peak crack propagation
0.050000 (Terminal)  0.006772             0.008939             +32.0023%      1.000000          1.000000          +0.000000        Full softening reached
======================================================================================================================================================================
```

---

## 3. First Divergence State & Root-Cause Correlation

- **Exact Point of Divergence**: **Frame 20** ($U_1 = 0.012575\text{ mm}$, Step Time $0.2515$).
- **Mechanism**:
  - From Frame 0 to Frame 19 ($U_1 = 0.0 \to 0.012500\text{ mm}$), the two solutions agree with **$0.0000\%$ difference** across all displacements, reaction forces, and damage states.
  - At Increment 20, default Abaqus controls ($I_0 = 4$) triggered a logarithmic cutback when Attempt 1 reached iteration 6, forcing micro-increments that captured the sharp softening peak at $U_1 = 0.012575\text{ mm}$.
  - In revised `1390533` ($I_0 = 8, I_C = 20$), the solver was permitted to iterate through iteration 7 without cutback, accepting a full $\Delta t = 0.020$ macro-increment to Step Time $0.270$ ($U_1 = 0.013513\text{ mm}$).
  - Because phase-field damage history accumulation is irreversible ($\mathcal{H}_{n+1} = \max(\mathcal{H}_n, \psi^+)$), jumping across the peak in a large macro-step locked in excess strain energy, shifting the apparent peak upward.
- **Protocol Classification**: **`SOLVER_CONTROL_ALTERS_EQUILIBRIUM_PATH`**

---

## 4. Complete Scheduler Accounting for Triplet Batch

All three jobs in the guarded triplet batch have completed 100% of physical displacement to $U_1 = 0.0500\text{ mm}$ with **`Exit_status = 0`**:

```text
===================================================================================================================================================================
Job Name                                       PBS Job ID        Mesh Type      Nodes   Quads   CPUT      Walltime  Memory    State  Exit Code  Terminal Status
---------------------------------------------  ----------------  -------------  ------  ------  --------  --------  --------  -----  ---------  -------------------------
M2CORR_STAGE_E_DONOR_CONTROL_VAL               1390533.mmaster02 Donor Ref      9,074   8,836   00:05:14  00:05:18  590.4 MB  F      0          THE ANALYSIS COMPLETED OK
M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL   1390534.mmaster02 Refined Target 34,028  33,600  00:32:31  00:32:39  2097.8 MB F      0          THE ANALYSIS COMPLETED OK
M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL 1390535.mmaster02 Coarse Target  8,417   8,200   00:04:33  00:04:36  505.1 MB  F      0          THE ANALYSIS COMPLETED OK
===================================================================================================================================================================
```

- Complete solver outputs (`.odb`, `.sta`, `.msg`, `.prt`, `pbs.out`, `pbs.err`) for all 3 jobs have been retrieved and preserved locally.
- In accordance with standing instructions, neither `1390534` nor `1390535` will be promoted to validate Stage E until the donor continuation protocol classification is resolved.

---

## 5. HPC Governance Audit Summary

- **Violation Evidence**: In Task F289, jobs `1390533`, `1390534`, and `1390535` ran concurrently for $\approx 4\text{ minutes}$ on `mnode097` due to sequential unheld `qsub` execution.
- **Future Guard**: `scripts/hpc/guard_batch_submission.py` was implemented and verified with 5 unit tests in `scripts/validation/test_concurrency_guard.py`, guaranteeing that no future batch can dispatch more than $\max(0, 2 - \text{running\_count})$ jobs into active execution.

---

## 6. Preserved Scientific Gates

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

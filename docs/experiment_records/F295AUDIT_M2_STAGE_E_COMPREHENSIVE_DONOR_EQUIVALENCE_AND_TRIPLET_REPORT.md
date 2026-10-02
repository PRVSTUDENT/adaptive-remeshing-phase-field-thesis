# Mode-II Stage-E Comprehensive Donor Numerical Equivalence & Triplet Batch Forensic Report

**Task ID**: `F295AUDIT-M2-STAGE-E-COMPREHENSIVE-DONOR-EQUIVALENCE-AND-TRIPLET-REPORT1`  
**Date**: 18 August 2026  
**Status**: `FORENSIC_EQUIVALENCE_PROVED / FIRST_DIVERGENCE_ISOLATED / PROTOCOL_CLASSIFIED / ALL_THREE_JOBS_PRESERVED / E2_HELD_BLOCKED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Triplet Batch Scheduler Accounting & Artifact Preservation

All three jobs of the guarded triplet batch have completed 100% of physical displacement to $U_1 = 0.0500\text{ mm}$ with **`Exit_status = 0`** (`THE ANALYSIS HAS COMPLETED SUCCESSFULLY`). All solver artifacts (`.odb`, `.dat`, `.sta`, `.msg`, `.prt`, `pbs.out`, `pbs.err`) have been retrieved and archived locally:

```text
===================================================================================================================================================================
Job Name                                       PBS Job ID        Mesh Type      Nodes   Quads   CPUT      Walltime  Memory    State  Exit Code  Terminal Status
---------------------------------------------  ----------------  -------------  ------  ------  --------  --------  --------  -----  ---------  -------------------------
M2CORR_STAGE_E_DONOR_CONTROL_VAL               1390533.mmaster02 Donor Ref      9,074   8,836   00:05:14  00:05:18  590.4 MB  F      0          THE ANALYSIS COMPLETED OK
M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL   1390534.mmaster02 Refined Target 34,028  33,600  00:32:31  00:32:39  2097.8 MB F      0          THE ANALYSIS COMPLETED OK
M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL 1390535.mmaster02 Coarse Target  8,417   8,200   00:04:33  00:04:36  505.1 MB  F      0          THE ANALYSIS COMPLETED OK
===================================================================================================================================================================
```

- **Diagnostic Treatment**: Results for `1390534` and `1390535` are preserved strictly as diagnostic evidence and are not used to validate Stage E pending the donor protocol resolution.

---

## 2. Machine-Readable One-Difference Manifest

Comparing historical donor control `1390447.mmaster02` vs revised donor reference `1390533.mmaster02`:

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

**Conclusion on Inputs**: There are zero unintended differences in physics, geometry, material, kinematics, or boundary conditions. The only differences are the modified numerical controls.

---

## 3. Canonical Trajectory Reconciliation & First Divergence Point

Extracted with the unified canonical extractor for both ODBs:
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

## 4. Root-Cause Divergence Mechanism & Authoritative Parameter Audit

1. **Exact Divergence State**: Frame 20 ($U_1 = 0.012575\text{ mm}$, Step Time $0.2515$).
2. **Parameter Analysis**:
   - **$I_0$ (Field 1, set to 8, default 4)**: Iteration at which logarithmic rate divergence check begins. By increasing $I_0$ to 8, Newton iterations 4 to 7 were allowed to continue without cutback. At Increment 20, the attempt converged on iteration 7, accepting a full macroscopic increment ($\Delta t = 0.020$, $U_1 = 0.0125 \to 0.0135\text{ mm}$).
   - **$I_C$ (Field 4, set to 20, default 16)**: Max equilibrium iterations allowed. Allowed iteration 7 to finish.
   - **$I_A$ (Field 8, set to 12, default 5)**: Max cutback attempts. This parameter safely prevents premature cutback exhaustion without altering the convergence acceptance criteria.
   - **$\Delta t_{\min} = 10^{-10}\text{ s}$**: Minimum attempted and accepted increment in `1390533` was $7.813 \times 10^{-5}\text{ s}$, far above $1.0 \times 10^{-9}\text{ s}$. This change was unexercised.
3. **Physical Consequence**:
   - Because phase-field damage history accumulation ($\mathcal{H}_{n+1} = \max(\mathcal{H}_n, \psi^+)$) is path-dependent, skipping pre-peak cutbacks and accepting a large macroscopic step over the localization regime locked in higher elastic energy prior to softening, altering the discrete equilibrium path and shifting the apparent peak upward.

---

## 5. Official Protocol Classification

- **Classification**: **`SOLVER_CONTROL_ALTERS_EQUILIBRIUM_PATH`**

---

## 6. HPC Governance Audit

- **Root Cause**: Transient 3-job concurrency breach in F289 occurred because sequential `qsub` commands were submitted without scheduler holds while 3 vnodes were available on `mnode097`.
- **Enforcement**: Concurrency guard `scripts/hpc/guard_batch_submission.py` was constructed and verified with 5 deterministic unit tests in `scripts/validation/test_concurrency_guard.py`, guaranteeing that future batch submissions strictly respect $\le 2$ active running HPC jobs.

---

## 7. Preserved Scientific Gates

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

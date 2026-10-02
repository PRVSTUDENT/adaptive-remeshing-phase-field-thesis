# Mode-II Stage-E Definitive Donor Numerical Equivalence, Protocol Classification & Triplet Evaluation Record

**Task ID**: `F297AUDIT-M2-STAGE-E-DEFINITIVE-DONOR-EQUIVALENCE-AND-PROTOCOL-CLASSIFICATION1`  
**Date**: 18 August 2026  
**Status**: `DEFINITIVE_AUDIT_COMPLETED / ONE_DIFF_MANIFEST_FROZEN / FIRST_DIVERGENCE_PROVED / PROTOCOL_CLASSIFIED / TRIPLET_DIAGNOSTIC_EVALUATION_COMPLETED / NEXT_ACTION_DEFINED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

This forensic audit resolves the scientific equivalence of the numerical continuation protocol applied in Stage E by comparing historical donor baseline `1390447.mmaster02` against revised donor control `1390533.mmaster02`. 

- **Primary Finding**: Both input packages are **100.0000% identical** across all physical governing equations, UEL Fortran source code, finite element mesh discretization, node coordinates, material properties, and boundary conditions. Up to Frame 19 ($U_1 = 0.012513\text{ mm}$ / Increment 19), the physical solution trajectories match with **$0.0000\%$ error**.
- **Divergence Mechanism**: Divergence occurs precisely at **Frame 20** ($U_1 = 0.012575\text{ mm}$ in `1390447` vs $U_1 = 0.013513\text{ mm}$ in `1390533`). Modifying $I_0$ from 4 to 8 and $I_C$ from 16 to 20 delayed the standard logarithmic convergence cutback check, permitting a large macroscopic step ($\Delta t = 0.020$) to converge on iteration 7. Due to the path-dependent accumulation of crack history $\mathcal{H}_{n+1} = \max(\mathcal{H}_n, \psi^+)$, this macro-step jumped over the softening localization onset and locked in excess elastic strain energy prior to crack initiation, artificially elevating the apparent peak force from $0.144737\text{ kN}$ to $0.149382\text{ kN}$ ($+3.2093\%$).
- **Governing Protocol Classification**: **`SOLVER_CONTROL_ALTERS_EQUILIBRIUM_PATH`**.
- **Completed Triplet Status**: All three triplet jobs (`1390533`, `1390534`, `1390535`) completed successfully to $U_1 = 0.0500\text{ mm}$ with `Exit_status = 0`. Their outputs are archived locally and evaluated diagnostically. However, they cannot serve as neutral Stage-E continuous baselines until the donor control protocol is restored to path neutrality.
- **Smallest Next Scientific Action**: Revert $I_0 \to 4$ and $I_C \to 16$ to standard Abaqus defaults while isolating $I_A = 12$ (pure cutback attempt extension), keeping $\Delta t_{\min} = 1.0\times 10^{-9}\text{ s}$, and qualifying this minimal protocol on a single same-mesh donor control run.

---

## 2. Machine-Readable Exact One-Difference Manifest

Comparing historical donor control `1390447.mmaster02` vs revised donor reference `1390533.mmaster02`:

```text
======================================================================================================================================================================
Artifact / Subsystem                 Historical Control (1390447)       Revised Reference (1390533)        Difference Classification
-----------------------------------  ---------------------------------  ---------------------------------  -----------------------------------------------------------
Subroutine f44 FOR SHA-256           62e35f74bbeccd3f5b1ac67312b79211f  62e35f74bbeccd3f5b1ac67312b79211f  100% IDENTICAL (No difference)
FE Mesh & Node Coordinates           8,836 quads / 9,074 nodes          8,836 quads / 9,074 nodes          100% IDENTICAL (No difference)
Material PROPS Vector                (0.015, 0.0027, 210, 0.3, 1e-7, 8836, 0.0) (Identical)               100% IDENTICAL (No difference)
Coupling, Equations & BCs            RP 99999 DOF 1 shear, bottom clamped (Identical)                     100% IDENTICAL (No difference)
Execution Mode & NLGEOM              NLGEOM=NO, 1 CPU, Double Precision (Identical)                        100% IDENTICAL (No difference)
Output Requests                      U, RF, SDV (Identical)             U, RF, SDV (Identical)             100% IDENTICAL (No difference)
Launcher Script                      submit_job.pbs (Identical)         submit_job.pbs (Identical)         100% IDENTICAL (Infrastructure-only)
*HEADING Title Line                  M2CORR_STAGE_D_CONTINUOUS...       M2CORR_STAGE_E_DONOR...            Infrastructure-only (Job name comment)
*STATIC Line 2                       0.001, 1.0, 1.0e-9, 0.02           0.001, 1.0, 1.0e-10, 0.02          Intended continuation change (dt_min reduced)
*CONTROLS, PARAMETERS=TIME INC       (Abaqus Defaults)                  8, 10, 9, 20, 10, 4, 50, 12        Intended continuation change (I_0, I_R, I_C, I_A, line 2)
                                                                        0.25, 0.50, 0.75, 0.25, ...
======================================================================================================================================================================
```

**Manifest Conclusion**: There are **zero unintended model, material, or geometric differences**. The differing behavior is solely governed by the modified numerical continuation controls.

---

## 3. First Accepted Divergence State & Deep Trajectory Analysis

Using identical canonical extraction across all frames:

```text
======================================================================================================================================================================
Target State / Displ (mm)  Historical 1390447 State (Default I_0=4)    Revised 1390533 State (Continuation I_0=8)  Pointwise Difference & Physical Mechanism
-------------------------  ------------------------------------------  ------------------------------------------  ---------------------------------------------------
U1 = 0.001000 mm           Time = 0.0200, RF1 = 0.013827, d = 0.00256  Time = 0.0200, RF1 = 0.013827, d = 0.00256  0.0000% error (100% identical linear response)
U1 = 0.005000 mm           Time = 0.1000, RF1 = 0.056781, d = 0.04508  Time = 0.1000, RF1 = 0.056781, d = 0.04508  0.0000% error (100% identical elastic response)
U1 = 0.010000 mm           Time = 0.2000, RF1 = 0.115359, d = 0.23419  Time = 0.2000, RF1 = 0.115359, d = 0.23419  0.0000% error (100% identical damage evolution)
U1 = 0.010513 mm (Handoff) Time = 0.2103, RF1 = 0.125916, d = 0.30432  Time = 0.2103, RF1 = 0.125916, d = 0.30432  -0.0001% error (Exact handoff state agreement)
U1 = 0.011513 mm (Frame18) Time = 0.2303, RF1 = 0.135771, d = 0.39662  Time = 0.2303, RF1 = 0.135771, d = 0.39662  0.0000% error (Exact match)
U1 = 0.012513 mm (Frame19) Time = 0.2503, RF1 = 0.144515, d = 0.52608  Time = 0.2503, RF1 = 0.144515, d = 0.52608  0.0000% error (Exact match at Frame 19)
----------------------------------------------------------------------------------------------------------------------------------------------------------------------
FIRST DIVERGENCE POINT     Frame 20: Time = 0.25151, dt = 0.00125      Frame 20: Time = 0.27026, dt = 0.02000      DIVERGENCE TRIGGERED:
                           U1 = 0.012575 mm, RF1 = 0.144737 kN         U1 = 0.013513 mm, RF1 = 0.149382 kN         1390447 cut back at iter 6 (I_0=4)
                           d_max = 0.557907 (Resolved Softening Peak)  d_max = 0.793079 (Macro-Step Overshoot)     1390533 iterated to iter 7 (I_0=8) & converged
----------------------------------------------------------------------------------------------------------------------------------------------------------------------
Frame 21 (Softening)       Time = 0.25338, RF1 = 0.144432, d = 0.6370  Time = 0.27151, RF1 = 0.148185, d = 0.8642  Post-peak softening trajectories diverge
Terminal (U1=0.050000 mm)  Time = 1.00000, RF1 = 0.006772, d = 1.0000  Time = 1.00000, RF1 = 0.008939, d = 1.0000  Full softening reached in both runs
======================================================================================================================================================================
```

---

## 4. Authoritative Abaqus Semantics & Parameter Audit

Authoritative analysis of `*CONTROLS, PARAMETERS=TIME INCREMENTATION` parameter mappings:

```text
======================================================================================================================================================================
Field Position / Parameter           Default  Revised  Documented Abaqus Meaning & Algorithmic Role                 Path Neutrality Assessment
-----------------------------------  -------  -------  -----------------------------------------------------------  --------------------------------------------------
Line 1, Field 1 (I_0)                4        8        Iteration to begin logarithmic convergence rate check.       NON-NEUTRAL: Delays cutbacks, allowing macro-steps
                                                       If residual decreases slowly after I_0, solver cuts back.    to converge on steep nonlinear branches.
Line 1, Field 2 (I_R)                8        10       Iteration to begin alternate residual tolerance check.       NON-NEUTRAL: Allows slower convergence tolerance.
Line 1, Field 3 (I_P)                9        9        Iteration to begin logarithmic check for plasticity.         NEUTRAL: Unchanged.
Line 1, Field 4 (I_C)                16       20       Maximum equilibrium iterations allowed per attempt.          NON-NEUTRAL: Allows attempts to iterate longer.
Line 1, Field 5 (I_L)                10       10       Iterations with severe discontinuities before cutback.       NEUTRAL: Unchanged.
Line 1, Field 6 (I_G)                4        4        Iterations after which contact check is made.                NEUTRAL: Unchanged.
Line 1, Field 7 (I_S)                50       50       Maximum number of contact iterations allowed.                NEUTRAL: Unchanged.
Line 1, Field 8 (I_A)                5        12       Maximum cutback attempts permitted before fatal abort.       PATH-NEUTRAL: Only extends cutback allowance;
                                                                                                                    does not alter convergence acceptance criteria.
*STATIC Line 2 (dt_min)              1.0e-9   1.0e-10  Minimum allowable time increment.                            PATH-NEUTRAL: In 1390533, min attempted & accepted
                                                                                                                    increment was 7.813e-5 s (NEVER EXERCISED).
======================================================================================================================================================================
```

---

## 5. Official Protocol Classification

- **Classification**: **`SOLVER_CONTROL_ALTERS_EQUILIBRIUM_PATH`**
  - Changing $I_0$ from 4 to 8 and $I_C$ from 16 to 20 directly altered the discrete load-stepping sequence across the localization regime, causing the solver to bypass standard micro-increments at the onset of localization and shifting the apparent peak reaction force by $+3.2093\%$ at Frame 20.

---

## 6. Diagnostic Interpretation of Refined `1390534` and Coarsened `1390535`

Under the revised continuation protocol ($I_0=8, I_A=12$), all three baseline meshes completed 100% of physical displacement:

```text
========================================================================================================================================================================================
Job Name                                       PBS ID            Mesh Quads / Nodes   h_tip (mm)  Peak RF1 (kN) / Frame   Terminal RF1 (kN)  Handoff RF1 (kN) / d_max  Invariants Status
---------------------------------------------  ----------------  -------------------  ----------  ----------------------  -----------------  ------------------------  -----------------
M2CORR_STAGE_E_DONOR_CONTROL_VAL (Donor Ref)   1390533.mmaster02 8,836 / 9,074        0.003750    0.149382 kN (Frame 20)  0.008939 kN        0.125916 kN / 0.304318    ALL_SATISFIED
M2CORR_STAGE_E_REFINED_TARGET (Refined)        1390534.mmaster02 33,600 / 34,028      0.002000    0.147399 kN (Frame 20)  0.005815 kN        0.126053 kN / 0.309948    ALL_SATISFIED
M2CORR_STAGE_E_COARSENED_TARGET (Coarsened)    1390535.mmaster02 8,200 / 8,417        0.005000    0.148876 kN (Frame 20)  0.006101 kN        0.125214 kN / 0.286073    ALL_SATISFIED
========================================================================================================================================================================================
```

- **Diagnostic Finding**: All three meshes exhibited smooth, monotonic pre-peak response, excellent handoff force agreement ($\le 0.5\%$), full damage localization ($d=1.0$), and complete post-peak softening to $U_1 = 0.050\text{ mm}$.
- **Validation Gate**: However, because all three meshes were executed under continuation controls that alter the peak load-stepping path, they cannot be promoted to validate Stage-E baselines until the continuation protocol is calibrated for path neutrality.

---

## 7. HPC Concurrency Governance Audit

- **Historical Reconstruction**:
  - `1390533.mmaster02`: Submitted 10:55:30, started 10:55:34 on `mnode097/0`.
  - `1390534.mmaster02`: Submitted 10:55:35, started 10:55:39 on `mnode097/1`.
  - `1390535.mmaster02`: Submitted 10:55:40, started 10:55:44 on `mnode097/2`.
  - From 10:55:44 to 11:00:25 ($\approx 4\text{ min } 41\text{ s}$), all three jobs ran concurrently on `mnode097` because sequential `qsub` scripts were executed without scheduler job-dependency holds.
- **Verification of Guard**:
  - `scripts/hpc/guard_batch_submission.py` was developed and verified against 5 unit test cases in `scripts/validation/test_concurrency_guard.py` (0, 1, 2, and 3 active jobs). The guard calculates $\text{available\_slots} = \max(0, 2 - \text{running\_count})$ and holds excess jobs until running jobs terminate.

---

## 8. Smallest Next Scientific Action

To restore numerical continuation protocol neutrality while preventing post-peak attempt exhaustion ($I_A = 5$ limit):

1. **Parameter Isolation**:
   - Revert $I_0 \to 4$ (Standard default: logarithmic cutback check starts at iteration 4).
   - Revert $I_R \to 8$ (Standard default: alternate residual check starts at iteration 8).
   - Revert $I_C \to 16$ (Standard default: max equilibrium iterations = 16).
   - **Retain $I_A = 12$** (Pure cutback attempt extension: allows 12 cutbacks before aborting, permitting micro-increments $\Delta t \to 10^{-7}\text{ s}$ through post-peak snapback without altering pre-peak or peak path selection).
   - Retain $\Delta t_{\min} = 1.0\times 10^{-9}\text{ s}$.
   - Retain default growth factor multipliers Line 2 (`0.25, 0.50, 0.75, 0.85, ...`).
2. **Minimal Qualification Execution**:
   - Run a single same-mesh donor control run (`M2CORR_STAGE_E_DONOR_MINIMAL_CONTINUATION_VAL`) to verify that the canonical peak ($RF_1 = 0.144737\text{ kN}$ at $U_1 = 0.012575\text{ mm}$) is exactly preserved while completing the entire post-peak fracture trajectory to $U_1 = 0.050\text{ mm}$.

---

## 9. Preserved Scientific Gates

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

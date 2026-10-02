# Mode-II Stage-E Final Canonical Equivalence & Triplet Batch Forensic Record

**Task ID**: `F296AUDIT-M2-STAGE-E-FINAL-CANONICAL-EQUIVALENCE-AND-TRIPLET-RECORD1`  
**Date**: 18 August 2026  
**Status**: `CANONICAL_EXTRACTIONS_COMPLETED / ONE_DIFF_MANIFEST_FROZEN / FIRST_DIVERGENCE_PROVED / PROTOCOL_CLASSIFIED / TRIPLET_ACCOUNTING_PRESERVED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Triplet Batch Exact Scheduler Accounting & Canonical Results

All three jobs of the guarded triplet batch have completed 100% of physical displacement to $U_1 = 0.0500\text{ mm}$ with **`Exit_status = 0`** (`THE ANALYSIS HAS COMPLETED SUCCESSFULLY`). Complete solver outputs (`.odb`, `.dat`, `.sta`, `.msg`, `.prt`, `pbs.out`, `pbs.err`) are archived locally in each respective package directory:

```text
========================================================================================================================================================================================
Job Name                                       PBS ID            Mesh Type      Nodes   Quads   CPUT      Walltime  Memory    State  Exit Code  Peak RF1 / U1 (mm)       Terminal RF1 (kN)
---------------------------------------------  ----------------  -------------  ------  ------  --------  --------  --------  -----  ---------  -----------------------  -----------------
M2CORR_STAGE_E_DONOR_CONTROL_VAL               1390533.mmaster02 Donor Ref      9,074   8,836   00:05:14  00:05:18  590.4 MB  F      0          0.149382 kN @ 0.013513   0.008939 kN
M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL   1390534.mmaster02 Refined Target 34,028  33,600  00:32:31  00:32:39  2097.8 MB F      0          0.147399 kN @ 0.013513   0.005815 kN
M2CORR_STAGE_E_COARSENED_TARGET_CONTINUOUS_VAL 1390535.mmaster02 Coarse Target  8,417   8,200   00:04:33  00:04:36  505.1 MB  F      0          0.148876 kN @ 0.013513   0.006101 kN
========================================================================================================================================================================================
```

- **Diagnostic Treatment**: Results for `1390534` and `1390535` are preserved strictly as diagnostic evidence and are not used to validate Stage E until the donor protocol classification is resolved.

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

**Manifest Verdict**: No unintended differences exist. The only differences are the intentionally modified numerical controls.

---

## 3. First Accepted Divergence State & Deep GP Comparison

Extracted with the canonical extractor for both ODBs:
- **Frames 0 through 19 ($U_1 = 0.0 \to 0.012513\text{ mm}$)**: **100.0000% identical** across all displacements, reaction forces, and damage states ($0.0000\%$ error).
  - Frame 18 ($U_1 = 0.011513\text{ mm}$): $RF_1 = 0.135771\text{ kN}$, $d_{\max} = 0.396619$ (Exact in both).
  - Frame 19 ($U_1 = 0.012513\text{ mm}$): $RF_1 = 0.144515\text{ kN}$, $d_{\max} = 0.526079$ (Exact in both).
- **First Divergence Point**: **Frame 20** ($U_1 = 0.012575\text{ mm}$ in `1390447` vs $U_1 = 0.013513\text{ mm}$ in `1390533`).
  - In `1390447` (Default $I_0 = 4$): Increment 20 attempted $\Delta t = 0.020$, reached iteration 6 ($> I_0$), triggered cutbacks to $\Delta t = 0.0050$ and then $\Delta t = 0.00125$, converging at Step Time $0.25151$ ($U_1 = 0.012575\text{ mm}$, $RF_1 = 0.144737\text{ kN}$, $d_{\max} = 0.557907$).
  - In `1390533` (Continuation $I_0 = 8, I_C = 20$): Increment 20 did not cut back at iteration 6. It iterated to iteration 7 ($\le I_C$) and declared convergence at Step Time $0.27026$ ($U_1 = 0.013513\text{ mm}$, $RF_1 = 0.149382\text{ kN}$, $d_{\max} = 0.793079$).

```text
======================================================================================================================================================================
Frame Index          1390447 State (Default Controls, I_0=4)                    1390533 State (Continuation Controls, I_0=8)               Divergence Correlation
-------------------  ---------------------------------------------------------  ---------------------------------------------------------  ---------------------------
Frame 18 (U1=0.0115) Time = 0.23026, RF1 = 0.135771 kN, d_max = 0.396619        Time = 0.23026, RF1 = 0.135771 kN, d_max = 0.396619        100.0000% Identical
Frame 19 (U1=0.0125) Time = 0.25026, RF1 = 0.144515 kN, d_max = 0.526079        Time = 0.25026, RF1 = 0.144515 kN, d_max = 0.526079        100.0000% Identical
Frame 20 (Div Point) Time = 0.25151, RF1 = 0.144737 kN, d_max = 0.557907 (Peak) Time = 0.27026, RF1 = 0.149382 kN, d_max = 0.793079 (Peak) DIVERGENCE: I_0 delayed
Frame 21 (Softening) Time = 0.25338, RF1 = 0.144432 kN, d_max = 0.637001        Time = 0.27151, RF1 = 0.148185 kN, d_max = 0.864193        Softening micro-increments
Terminal (U1=0.0500) Time = 1.00000, RF1 = 0.006772 kN, d_max = 1.000000        Time = 1.00000, RF1 = 0.008939 kN, d_max = 1.000000        Full softening reached
======================================================================================================================================================================
```

---

## 4. Authoritative Parameter Audit & Physical Mechanism

1. **Authoritative Parameter Meanings**:
   - **$I_0$ (Field 1, modified 4 $\to$ 8)**: Iteration at which logarithmic rate divergence check begins. By increasing $I_0$ to 8, the solver permitted slow-converging iterations 4 through 7 to continue instead of cutting back, allowing a large macroscopic displacement step ($\Delta t = 0.020$) across the peak. **Directly alters equilibrium path selection.**
   - **$I_C$ (Field 4, modified 16 $\to$ 20)**: Max equilibrium iterations allowed per attempt. Allowed iteration 7 to complete.
   - **$I_A$ (Field 8, modified 5 $\to$ 12)**: Max cutback attempts allowed per increment. **Only changes retry/cutback allowance without altering convergence acceptance or path selection.**
   - **$\Delta t_{\min} = 10^{-10}\text{ s}$**: The minimum attempted and accepted increment in `1390533` was $7.813 \times 10^{-5}\text{ s}$, far above $1.0 \times 10^{-9}\text{ s}$. This parameter change was **never exercised**.
2. **Physical Consequence**:
   - Because phase-field damage history accumulation ($\mathcal{H}_{n+1} = \max(\mathcal{H}_n, \psi^+)$) is path-dependent, skipping pre-peak cutbacks and taking a macro-step over the localization threshold locked in excess elastic strain energy prior to softening, shifting the apparent peak upward by $+3.2093\%$ (at Frame 20).

---

## 5. Official Protocol Classification

- **Classification**: **`SOLVER_CONTROL_ALTERS_EQUILIBRIUM_PATH`**

---

## 6. HPC Concurrency Governance Audit

- **Historical Event**: Jobs `1390533`, `1390534`, and `1390535` ran concurrently for $\approx 4\text{ minutes}$ on `mnode097` in F289 because sequential unheld `qsub` scripts were submitted while 3 vnodes were available.
- **Verification**: Concurrency guard `scripts/hpc/guard_batch_submission.py` was created and validated by 5 deterministic unit tests in `scripts/validation/test_concurrency_guard.py`, guaranteeing that future batches cannot exceed $\max(0, 2 - \text{running\_count})$ active running jobs.

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

# Mode-II Stage-E Target Baselines Extraction & Evaluation Record

**Task ID**: `F308AUDIT-M2-STAGE-E-TARGET-BASELINES-EXTRACTION-AND-VALIDATION1`  
**Date**: 19 August 2026  
**Status**: `TERMINAL_EVALUATION_COMPLETED / FORENSIC_ROOT_CAUSE_ISOLATED / GATES_HELD_CONSERVATIVE`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Terminal Scheduler & Solver Accounting

```text
======================================================================================================================================================================
Job Name / Description               Exact PBS Job ID   Exec Host   State / Exit   CPU Time   Walltime   Memory     Total Inc / Frames   Terminal Reason (.msg)
-----------------------------------  -----------------  ----------  -------------  ---------  ---------  ---------  -------------------  -----------------------
Refined Target Baseline              1391277.mmaster02  mnode098/0  F (Exit 1)     00:05:11   00:05:16   1.27 GB    28 inc / 29 frames   TOO MANY ATTEMPTS (I_A=12)
(33,600 quads, h_min=0.002000 mm)
-----------------------------------  -----------------  ----------  -------------  ---------  ---------  ---------  -------------------  -----------------------
Coarsened Target Baseline            1391279.mmaster02  mnode098/1  F (Exit 1)     00:12:16   00:12:22   1.10 GB    475 inc / 476 frames TIME INCREMENT < MINIMUM
(8,200 quads, h_min=0.004000 mm)
======================================================================================================================================================================
```

---

## 2. Quantitative Trajectory & Parity Comparison

```text
======================================================================================================================================================================
Metric / Characteristic              Refined Baseline (1391277.mmaster02)                  Coarsened Baseline (1391279.mmaster02)
-----------------------------------  ----------------------------------------------------  -------------------------------------------------------------------
Predecessor Comparison               Matches 1390527 & 1390834 exactly through Fr 27       Matches 1390528 through pre-peak; traverses deep post-peak (475 inc)
Handoff State (U1 = 0.01051289 mm)   Frame 17: U1 = 0.010513 mm, RF1 = 0.126053 kN, d=0.31 Frame 17: U1 = 0.010513 mm, RF1 = 0.125214 kN, d=0.286073
Peak Reaction Force RF1              0.141680 kN at U1 = 0.012331 mm (Frame 22)            0.143302 kN at U1 = 0.012700 mm (Frame 23)
Terminal State                       Frame 28: U1 = 0.012584 mm, RF1 = 0.130808 kN         Frame 475: U1 = 0.013116 mm, RF1 = 0.088191 kN (Softening)
Cutback & Incrementation Audit       19 cutbacks; Min dt_att = 4.475e-11 s                 105 cutbacks; Min dt_att = 1.000e-11 s, Min dt_acc = 1.541e-10 s
Exercised Attempts 6–12              YES (Exercised all 13 attempts in Inc 28)             YES (Exercised down to Attempt 8 at floor 1.0e-11 s in Inc 475)
dt_min = 1e-11 Exercised & Accepted  Exercised down to 4.475e-11 s                         Exercised and ACCEPTED increments down to 1.541e-10 s (< 1e-9 s)
Hard Invariants Audit                0 <= d <= 1 (True), Monotonic (True), H >= 0 (True)   0 <= d <= 1 (True), Monotonic (True), H >= 0 (True)
======================================================================================================================================================================
```

---

## 3. Forensic Analysis of Termination Mechanisms

1. **Refined Baseline (`1391277.mmaster02`)**:
   - Lowering $\Delta t_{\min}: 1.0\times 10^{-9} \to 1.0\times 10^{-11}\text{ s}$ successfully unlocked **Attempts 11, 12, and 13** (down to $\Delta t = 4.475\times 10^{-11}\text{ s}$).
   - The solver did not encounter the $\Delta t_{\min}$ floor; instead, Newton iterations diverged at Node 16004 DOF 3 ($d$-DOF in the localized shear band), exhausting the maximum attempt limit $I_A=12$ (`TOO MANY ATTEMPTS MADE FOR THIS INCREMENT`).
   - The handoff state ($U_1 = 0.01051289\text{ mm}$, Frame 17) and peak state ($U_1 = 0.012331\text{ mm}$, Frame 22) are 100.0000% captured and valid.

2. **Coarsened Baseline (`1391279.mmaster02`)**:
   - Successfully traversed through 475 increments (476 frames), capturing the full pre-peak, peak ($0.143302\text{ kN}$), and extensive post-peak softening down to $RF_1 = 0.088191\text{ kN}$ ($38.5\%$ drop).
   - Exercised and accepted increments below $1.0\times 10^{-9}\text{ s}$ down to $\Delta t = 1.541\times 10^{-10}\text{ s}$.
   - Terminated at Increment 475 when required cutback fell below $\Delta t_{\min} = 1.0\times 10^{-11}\text{ s}$.

---

## 4. Definitive Scientific Classification & Gate Accounting

```text
1391277.mmaster02 Classification: INCOMPLETE_NUMERICAL_FAILURE (for full U1=0.050 mm; fully valid through handoff U1=0.010513 mm)
1391279.mmaster02 Classification: INCOMPLETE_NUMERICAL_FAILURE (for full U1=0.050 mm; fully valid through handoff U1=0.010513 mm and deep softening)
```

- **Continuous Baselines Gate**: Retained as **`PARTIALLY_USABLE_UNDER_FORENSIC_REVIEW`** because neither fine-mesh continuous baseline reaches $U_1 = 0.050000\text{ mm}$ in continuous virgin mode (due to physical phase-field shear-band snap-back).
- **Production State Transfer Usability**: Both baselines are **100% physically and numerically qualified through the Stage-E handoff state ($U_1 = 0.01051289\text{ mm}$, Frame 17)**, which provides the exact pre-peak donor/target states needed for Stage-E adaptive remeshing validation.

---

## 5. Preserved Scientific Invariants

```text
stage_e_continuous_baselines_validation = PARTIALLY_USABLE_UNDER_FORENSIC_REVIEW
same_mesh_restart_validation = VALIDATED
history_transfer_rule_resolved = true
selected_production_history_operator = HOST_ISOPARAMETRIC_BILINEAR_WITH_LOCAL_GP_BOUNDS_CLAMP
stage_d_nonmatching_transfer_validation = VALIDATED
nonmatching_transfer_algorithm_scientifically_unblocked = true
production_adaptive_accuracy_validation_scientifically_unblocked = false
PK10R1_topology_repair_required = true
new_submission_authorized = false
qsub_called = false
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

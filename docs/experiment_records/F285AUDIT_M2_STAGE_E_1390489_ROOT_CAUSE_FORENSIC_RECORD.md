# Mode-II Stage-E Job 1390489 Forensic Root-Cause and Deck Audit Record

**Task ID**: `F285AUDIT-M2-STAGE-E-1390489-ROOT-CAUSE-AND-DECK-FORENSIC-AUDIT1`  
**Date**: 18 August 2026  
**Status**: `ROOT_CAUSE_ISOLATED / FORENSIC_AUDIT_COMPLETED / DEFECT_CLASSIFIED / REGISTRY_CORRECTED / STAGE_E_REMAINS_BLOCKED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary & Defect Classifications

A comprehensive read-only forensic audit was performed on failed job `1390489.mmaster02` (`M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL`) using the exact submitted package, ODB, MSG, STA, DAT, PBS logs, and Fortran UEL source code.

- **Primary Classification**: **`REFINED_MESH_GENERATION_DEFECT`**
  - The deck generator emitted a single-layer UEL definition with combined DOFs `1, 2, 3` and inverted property array ordering, as well as an inverted `*CONTROLS` increment growth factor ($0.25$ multiplier), causing automatic geometric increment shrinkage and early termination.
- **Secondary Classification**: **`TECHNICAL_LAUNCHER/EXIT_PROPAGATION_DEFECT`**
  - The launcher script `submit_job.pbs` contained a trailing `echo` command following the `abaqus` execution line, which swallowed the non-zero exit code and caused PBS to report `Exit_status = 0` despite Abaqus solver termination.

---

## 2. Solver Termination Evidence & Sequence Analysis

### Termination Sequence from `.sta` and `.msg`:
```text
======================================================================================================================================================================
Inc  Attempt  Severe Discon  Equil Iters  Total Iters  Total Time / LPF  Step Time / LPF  Time Increment  Residual Status          Abaqus Diagnostics
---  -------  -------------  -----------  -----------  ----------------  ---------------  --------------  -----------------------  -----------------------------------
  1     1           0             1            1          1.000e-05         1.000e-05        1.000e-05    ALL RESIDUALS ARE ZERO   1-iteration linear solve
  2     1           0             1            1          2.000e-05         2.000e-05        1.000e-05    ALL RESIDUALS ARE ZERO   1-iteration linear solve
  3     1           0             1            1          2.250e-05         2.250e-05        2.500e-06    ALL RESIDUALS ARE ZERO   Increment multiplied by 0.25
  4     1           0             1            1          2.313e-05         2.313e-05        6.250e-07    ALL RESIDUALS ARE ZERO   Increment multiplied by 0.25
  5     1           0             1            1          2.328e-05         2.328e-05        1.563e-07    ALL RESIDUALS ARE ZERO   Increment multiplied by 0.25
  6     1           0             1            1          2.332e-05         2.332e-05        3.906e-08    ALL RESIDUALS ARE ZERO   Increment multiplied by 0.25
  7     1           0             1            1          2.333e-05         2.333e-05        9.766e-09    ALL RESIDUALS ARE ZERO   Increment multiplied by 0.25
  8     1           0             1            1          2.333e-05         2.333e-05        2.441e-09    ALL RESIDUALS ARE ZERO   Increment multiplied by 0.25
  9     1           0             1            1          2.333e-05         2.333e-05        6.104e-10    ALL RESIDUALS ARE ZERO   Increment multiplied by 0.25
 10     1           0             1            1          2.333e-05         2.333e-05        1.526e-10    ALL RESIDUALS ARE ZERO   Increment multiplied by 0.25
 11     1           0             1            1          2.333e-05         2.333e-05        3.815e-11    ALL RESIDUALS ARE ZERO   Increment multiplied by 0.25
 12     1           0             1            1          2.333e-05         2.333e-05        9.537e-12    ALL RESIDUALS ARE ZERO   Increment multiplied by 0.25
 13     1           0             1            1          2.333e-05         2.333e-05        2.384e-12    ALL RESIDUALS ARE ZERO   Increment multiplied by 0.25
 14     1           0             1            1          2.333e-05         2.333e-05        5.960e-13    ALL RESIDUALS ARE ZERO   Increment multiplied by 0.25
 15     1           0             0            0          2.333e-05         2.333e-05        1.490e-13    ABORT: dt < dt_min       ***ERROR: TIME INCREMENT < MINIMUM
======================================================================================================================================================================
```

### Key Diagnostic Observations:
1. **Zero Cutbacks Occurred**: The simulation experienced `0` cutbacks. Every single increment converged in `1` iteration with zero residuals.
2. **Deterministic Geometric Decay**: The increment size was reduced by exactly a factor of $0.25$ after every step ($10^{-5} \to 2.5\times 10^{-6} \to 6.25\times 10^{-7} \dots \to 1.49\times 10^{-13}$).
3. **Exact Termination Mechanism**: At Increment 15, the attempted increment size $1.490 \times 10^{-13}$ fell below the specified minimum time increment $1.000 \times 10^{-12}$, triggering immediate Abaqus error termination.

---

## 3. Reconciliation of PBS Exit 0 vs Abaqus Incomplete Status

### Root Cause in `submit_job.pbs`:
Lines 20–22 of `submit_job.pbs` read:
```bash
abaqus job=M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL input=M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL.inp user=f44_mixed_uel_restart_stateinit.for cpus=1 interactive

echo "Job finished at $(date) with exit code $?"
```
- When `abaqus` aborted with a fatal error code, the shell proceeded to execute the trailing `echo` command.
- The `echo` command succeeded with exit code 0.
- Because `echo` was the final command evaluated in the script, bash returned 0 to PBS MOM, which recorded `Exit_status = 0` in PBS accounting.
- **Workflow Defect Resolution**: To ensure proper failure propagation, all PBS wrappers must capture `RC=$?` immediately after solver invocation and exit via `exit $RC`.

---

## 4. Input Deck Forensic Audit vs Donor `1390447.mmaster02`

A line-by-line comparative audit was conducted between the refined E1 deck (`M2CORR_STAGE_E_REFINED_TARGET_CONTINUOUS_VAL.inp`) and the successful donor deck (`M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.inp`):

```text
=====================================================================================================================================================================
Feature / Parameter                 Donor Deck (1390447)               Refined E1 Deck (1390489)          Audit Finding / Impact
----------------------------------  ---------------------------------  ---------------------------------  -----------------------------------------------------------
Physical Quads                      8,836 quads                        33,600 quads                       Refined discretization valid (within UEL N_CAPACITY=100000)
Physical Nodes                      9,073 nodes                        34,027 nodes                       Conforming topology, valid slit-face node duplication
UEL Layer Formulation               Two Layers (U1 Phase, U2 Mech)     Single Layer (U1 Mixed)            FATAL: UEL subroutine expects separate U1 and U2 layers
UEL Properties Vector               (l0, Gc, E, nu, k_tol, N, MODE)    (E, nu, Gc, l0, k_tol, N, MODE)    FATAL: E=210 assigned to l0, l0=0.015 assigned to nu
*CONTROLS Parameters                Default growth factors (1.5x)      Line 2 Field 7 = 0.25 (Shrink)     FATAL: Decreases increment by 4x upon every convergence
Top *EQUATION Coupling              DOF 1 coupled to RP 99999          DOF 1 & DOF 2 coupled to RP 99999  Over-constrained DOF 2 (shear test requires free top Y)
Bottom Boundary                     N_BOTTOM DOFs 1, 2 fixed           N_BOTTOM DOFs 1, 2 fixed           Valid clamped bottom
Reference Point Definition          Node 99999 at (0.0, 0.5)           Node 99999 at (0.0, 0.5)           Valid kinematic master node
=====================================================================================================================================================================
```

### Array Capacity & Indexing Verification:
- The Fortran UEL `f44_mixed_uel_restart_stateinit.for` uses `PARAMETER(N_CAPACITY=100000)`.
- For the refined mesh with 33,600 physical quads, `PHYSIDX` ranges from $1 \dots 33,600 \le 100,000$.
- No array bounds or memory overflow occurred in the Fortran common blocks.

---

## 5. Reference Point Force Extraction ($RF_1 = 0$) Audit

- **RP Extraction Verification**: The post-processing script correctly extracted Node `99999` from the ODB.
- **Physical Reason for Zero Force**: Because the deck omitted the mechanical `U2` element layer, no stiffness or internal force was assembled into the global displacement degrees of freedom. The displacement solver saw a completely unresisted kinematic motion, yielding an exact reaction force $RF_1 \equiv 0.0\text{ kN}$.
- **Conclusion**: $RF_1 = 0$ was a genuine mechanical consequence of the single-layer UEL deck defect, not a post-processing bug.

---

## 6. Corrected Stage-E Acceptance Criteria Registry

Only hard physical and software invariants are maintained as strict PASS/FAIL criteria; all numerical percentage comparisons remain strictly `DIAGNOSTIC ONLY`:

```text
======================================================================================================================================================================
Criterion ID                                Metric               Op    Threshold   Units   Provenance   Criterion Type       Description / Scientific Basis
------------------------------------------  -------------------  ----  ----------  ------  -----------  -------------------  -------------------------------------------------
CRIT_E_PRIMARY_PHASE_BOUNDS                 d_bounds             in    [0.0, 1.0]  dim.    Stage E Plan HARD_INVARIANT       Nodal damage d remains strictly bounded in [0, 1]
CRIT_E_POINTWISE_PHASE_IRREVERSIBILITY      min_delta_d          >=    -1.0e-6     dim.    Stage E Plan HARD_INVARIANT       Pointwise damage increment min(Δd) >= -1.0e-6
CRIT_E_HISTORY_NONNEGATIVITY                min_H                >=    0.0         kN/mm^2 Stage E Plan HARD_INVARIANT       Transferred and evolved history >= 0.0 at all GPs
CRIT_E_TEMPORAL_HISTORY_MONOTONICITY        H_{n+1} - H_n        >=    0.0         kN/mm^2 Stage E Plan HARD_INVARIANT       Committed history monotonically non-decreasing
CRIT_E_SLIT_BARRIER_ISOLATION               cross_slit_leak      ==    0           count   Stage E Plan HARD_INVARIANT       Zero cross-slit state contamination (y=0, x<=0)
CRIT_E_MECH_EQUILIBRATION_U3_DRIFT          max_abs_u3_change    <=    1.0e-6      dim.    Stage E Plan SOFTWARE_TOLERANCE   Phase DOF U3 strictly clamped during Step 2
CRIT_E_HANDOFF_RF1_COMPARISON               step1_diff_pct       N/A   None        %       F285 Correct DIAGNOSTIC_ONLY      Diagnostic Step 1 RF1 vs donor Frame 17 RF1
CRIT_E_MECH_EQUILIBRATION_RF1_JUMP          s2_jump_pct          N/A   None        %       F285 Correct DIAGNOSTIC_ONLY      Diagnostic Step 1 -> Step 2 RF1 jump upon release
CRIT_E_MATCHED_BASELINE_PEAK_PARITY         peak_rf1_diff_pct    N/A   None        %       F285 Correct DIAGNOSTIC_ONLY      Diagnostic E2 peak RF1 vs matching E1 baseline
CRIT_E_MATCHED_BASELINE_TERMINAL_PARITY     term_rf1_diff_pct    N/A   None        %       F285 Correct DIAGNOSTIC_ONLY      Diagnostic E2 terminal RF1 vs matching E1 baseline
======================================================================================================================================================================
```

---

## 7. Preserved Scientific Gates

```text
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
new_submission_authorized = false (Batch E1 and E2 submissions held)
qsub_called = false
qdel_called = false
qmove_called = false
git_commit_called = false
git_push_called = false
```

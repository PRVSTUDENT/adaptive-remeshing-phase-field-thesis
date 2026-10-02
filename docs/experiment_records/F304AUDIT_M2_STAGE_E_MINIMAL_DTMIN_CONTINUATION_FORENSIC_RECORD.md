# Mode-II Stage-E Minimal dt_min Floor Forensic Audit, Candidate Derivation, and Non-Submitting Package Preparation Record

**Task ID**: `F304AUDIT-M2-STAGE-E-MINIMAL-DTMIN-CONTINUATION-ISOLATION-AND-PREP1`  
**Date**: 18 August 2026  
**Status**: `FORENSIC_AUDIT_COMPLETE / CANDIDATE_DERIVED / PACKAGES_QUALIFIED_NON_SUBMITTING`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Attempt-by-Attempt Forensic Reconstruction of Increment 28 on Job 1390834.mmaster02

```text
======================================================================================================================================================================
Att.  Attempted dt (s)   Iters  Cutback Factor  Hotspot Node / DOF   Rejection / Cutback Reason                                        Termination Flag
----  -----------------  -----  --------------  -------------------  ----------------------------------------------------------------  ---------------------------
1     1.877e-04          6      0.2500          Node 16005 DOF 3 (d) Exceeded convergence allowance at I_0=4 (divergence detected)     Cutback to 4.693e-05 s
2     4.693e-05          8      0.2500          Node 16004 DOF 3 (d) Max iterations limit I_R=8 reached                                Cutback to 1.173e-05 s
3     1.173e-05          4      0.2500          Node 16164 DOF 3 (d) DISP. CORRECTION TOO LARGE / Divergence detected at I_0=4         Cutback to 2.933e-06 s
4     2.933e-06          4      0.2500          Node 16164 DOF 3 (d) Divergence detected at I_0=4                                      Cutback to 7.332e-07 s
5     7.332e-07          4      0.2500          Node 16164 DOF 3 (d) Divergence detected at I_0=4 (Default I_A=5 limit reached here)   Cutback to 1.833e-07 s
6     1.833e-07          4      0.2500          Node 16164 DOF 3 (d) Divergence detected at I_0=4                                      Cutback to 4.583e-08 s
7     4.583e-08          4      0.2500          Node 16164 DOF 3 (d) Divergence detected at I_0=4                                      Cutback to 1.146e-08 s
8     1.146e-08          4      0.2500          Node 16164 DOF 3 (d) Divergence detected at I_0=4                                      Cutback to 2.864e-09 s
9     2.864e-09          4      0.2500          Node 16164 DOF 3 (d) Divergence detected at I_0=4 (Cutback 2.864e-9 * 0.25 = 7.16e-10) Clamped to dt_min=1.0e-9 s
10    1.000e-09 (Floor)  4      0.2500          Node 16164 DOF 3 (d) Next required cutback (2.5e-10 s) < dt_min=1.0e-9 s               ERROR: dt < dt_min
======================================================================================================================================================================
```

### Forensic Determination of Termination Mechanism:
1. **Governing Reason for Solver Termination**:
   - The analysis terminated **solely because the required time increment fell below the specified minimum $\Delta t_{\min} = 1.0\times 10^{-9}\text{ s}$**.
   - Attempt 9 computed a cutback increment of $2.864\times 10^{-9}\text{ s} \times 0.25 = 7.160\times 10^{-10}\text{ s}$, which was clamped to $\Delta t_{\min} = 1.0\times 10^{-9}\text{ s}$ for Attempt 10.
   - When Attempt 10 was rejected, the next cutback ($2.500\times 10^{-10}\text{ s}$) was strictly below $\Delta t_{\min}$, triggering `***ERROR: TIME INCREMENT REQUIRED IS LESS THAN THE MINIMUM SPECIFIED`.
2. **Attempt Allowance Status**:
   - The maximum attempt allowance $I_A=12$ was **not exhausted** (only 10 attempts were executed). Attempts 11 and 12 were unexercised solely due to the $\Delta t_{\min}$ floor.

---

## 2. Parity Comparison Against Predecessors

```text
======================================================================================================================================================================
Baseline Pair                        Comparison Scope                    Parity Metric / Difference                         Equivalence Status
-----------------------------------  ----------------------------------  -------------------------------------------------  ------------------------------------------
1390834 vs Refined Default (1390527) Pre-peak Frames 0–27 (U1: 0->0.0126) Max RF1 diff = 0.0000%, Peak RF1 = 0.141680 kN   100.0000% EXACT PARITY
1390834 vs Donor IA=12 (1390552)     Pre-peak Trajectory                 Standard mesh-scale displacement response          Consistent constitutive behavior
1390834 vs Refined Default (1390527) Increment 28 Attempt Execution      1390527 failed at 5U; 1390834 reached 10U          Isolating I_A=12 unlocked attempts 6–10
======================================================================================================================================================================
```

---

## 3. Authoritative Abaqus Solver Semantics for `*STATIC` $\Delta t_{\min}$

According to the *Abaqus Analysis User's Guide* (Section 19.1.1 *Configuring analysis procedures*):
- Parameter `dt_min` in `*STATIC` defines the lower cutoff threshold for automatic time incrementation.
- It acts as a passive termination boundary. For any step time increment $\Delta t > \Delta t_{\min}$, all trial increment selections, Newton-Raphson iterations, residual tolerance tests ($R_n, C_n$), and standard cutback factors ($D_A = 0.25$) are completely independent of `dt_min`.
- Lowering `dt_min` from $1.0\times 10^{-9}\text{ s}$ to a smaller candidate value is **strictly path-neutral** for all accepted equilibrium states and merely permits deeper cutback attempts.

---

## 4. Candidate $\Delta t_{\min}$ Derivation

From the observed geometric cutback sequence ($D_A = 0.25$):
- Attempt 9: $\Delta t = 2.864 \times 10^{-9}\text{ s}$
- True Attempt 10: $2.864 \times 10^{-9} \times 0.25 = 7.160 \times 10^{-10}\text{ s}$
- True Attempt 11: $7.160 \times 10^{-10} \times 0.25 = 1.790 \times 10^{-10}\text{ s}$
- True Attempt 12: $1.790 \times 10^{-10} \times 0.25 = 4.475 \times 10^{-11}\text{ s}$

**Selected Evidence-Supported Candidate**: **`dt_min = 1.0e-11 s`**
- Provides exact headroom to accommodate the full $I_A=12$ cutback cascade down to $4.475\times 10^{-11}\text{ s}$ (allowing 3 additional full cutback attempts without floor clamping).

---

## 5. Non-Submitting Package Preparation & Deterministic Qualification

Two qualification packages were prepared locally and on `tu_freiberg` (without submitting):

```text
======================================================================================================================================================================
Package Name                                      Target Role         INP SHA-256                                                       One-Diff Status  Datacheck
------------------------------------------------  ------------------  ----------------------------------------------------------------  ---------------  ---------
M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_   Donor Qualification 105d2cc04de25f68c0a1fbeaab8b66d355881993cf6292e8201ad210137d3db8   Only dt_min diff PASSED (0 err)
M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONT  Refined Replacement 5f4444c4aca0261533343e153a1ce88450cf3723849c810d5f0432bed8cfae6c   Only dt_min diff PASSED (0 err)
======================================================================================================================================================================
```

- **Manifest**: [`models/generated/mode_ii/stage_e_refinement_coarsening_batch/dtmin_continuation_packages_manifest.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/generated/mode_ii/stage_e_refinement_coarsening_batch/dtmin_continuation_packages_manifest.json)
- **Frozen Scientific Question**:
  > *"Does lowering only dt_min: 1.0e-9 -> 1.0e-11 preserve the already validated donor equilibrium trajectory to numerical precision while merely extending allowable cutback depth?"*

---

## 6. Preserved Status & Invariants

- `1390830.mmaster02` = `TECHNICAL_PRE_SOLVER_FAILURE (CRLF)` (No automatic replacement authorized).
- `stage_e_continuous_baselines_validation` = `PARTIALLY_USABLE_UNDER_FORENSIC_REVIEW`
- `production_adaptive_accuracy_validation_scientifically_unblocked` = `false`
- `new_submission_authorized` = `false`
- `qsub_called` = `false`, `qdel_called` = `false`, `qmove_called` = `false`
- `git_commit_called` = `false`, `git_push_called` = `false`

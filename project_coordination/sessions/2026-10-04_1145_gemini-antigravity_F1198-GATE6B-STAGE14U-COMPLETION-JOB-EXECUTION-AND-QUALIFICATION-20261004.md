# Session Report: Gate-6B Mode-I Stage 14U Validated Completion-Run Preparation, Solver-Control Correction, and Immediate Submission

**Date:** 2026-10-04T11:45:00+02:00  
**Agent:** Gemini Antigravity  
**Task ID:** `F1198-GATE6B-STAGE14U-COMPLETION-JOB-EXECUTION-AND-QUALIFICATION-20261004`  
**Phase:** `MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION`  
**Starting Commit:** `c7bf9db146d06739f61fc65fcf88e441d789fa3f`  
**Governing Status:** `STAGE14U_COMPLETION_JOB_SUBMITTED_AND_SOLVING`  
**Governing Verdicts:** `STAGE14_LOCALIZATION_CHANGE_EXPLAINED_BY_IDENTIFIED_PROJECT_DIFFERENCE`, `STAGE14_ADAPTIVE_RESULT_NOT_YET_QUALIFIED`, `TOWARD_TARGET_LOCALIZATION`

---

## 1. Executive Summary

In Stage 14U, the validated completion workflow was prepared, qualified, and submitted to solve the complete Mode-I fracture trajectory through the final displacement endpoint $u = 0.0100\,\text{mm}$ on the $14{,}483$-element adapted mesh ($43{,}449$ layered elements).

Following the forensic diagnosis of the premature termination of Job `1409953.mmaster02` at $u = 0.007889\,\text{mm}$ (Step 2 Increment 2890 cutback exhaustion $I_A=5$ under severe post-fracture softening, $99.76\%$ load drop, zero singularities), restart execution was systematically evaluated and rejected due to the absence of `LOP=4/5` restart handlers in `f42_mixed_uel.for` (`COMMON /CB_STATE_TRANS/`). A full deterministic rerun from $u = 0$ was selected. Minimal numerical solver controls (`*CONTROLS, PARAMETERS=TIME INCREMENTATION` with $I_A=10, I_C=20, I_R=10$) were added to Step 2, while all 14,456 nodes, 14,483 underlying elements, zero-gap seam, material parameters ($E=210\,\text{kN/mm}^2, \nu=0.3, G_c=0.0027\,\text{kN/mm}, l_0=0.0075\,\text{mm}, k=10^{-7}$), and ABI order were completely frozen.

Pre-submission unit tests passed with $100\%$ success ($84/84$ Stage-14 unit tests), Abaqus datacheck completed cleanly on the cluster (Exit 0, zero errors/warnings), and the serial 1-CPU completion job `1409982.mmaster02` was submitted to `normal_imfdfkmq` on compute node `mnode097`, where it is actively advancing.

---

## 2. Failing-Increment Telemetry from Job 1409953.mmaster02

- **Pre-Peak and Peak Advance:**
  - Step 1 ($u \le 0.0050\,\text{mm}$, 2,000 increments): converged with 0 cutbacks, 3.0 iters/inc average.
  - Step 2 ($u \in [0.0050, 0.007889]\,\text{mm}$, Increments 2001--2889): converged with 0 cutbacks.
- **Increment 2890 Cutback Sequence:**
  - Attempt sequence: $\Delta t = 2.0\times 10^{-4} \to 5.0\times 10^{-5} \to 1.25\times 10^{-5} \to 3.125\times 10^{-6} \to 7.8125\times 10^{-7} \to 7.8125\times 10^{-7}$ ($I_A = 5$ cutback attempts reached).
  - Termination message: `***ERROR: TOO MANY ATTEMPTS MADE FOR THIS INCREMENT`.
  - Termination was caused strictly by exhausting the default attempt ceiling ($I_A = 5$), not by reaching $\Delta t_{\min} = 1.0\times 10^{-9}$ or increment ceiling (`INC=6000`).
- **Singularity and Nonlinearity Check:**
  - Zero negative eigenvalue warnings, zero zero-pivots, zero numerical singularity messages.
  - `NLGEOM=NO` confirmed that softening was purely material constitutive/residual softening ($F = 0.001764\,\text{kN}$ vs $F_{\max} = 0.743701\,\text{kN}$, $99.76\%$ load drop, residual stiffness factor $k = 10^{-7}$) in the fully severed ligament ($x_{\text{tip}} = 0.9985\,\text{mm}$).
  - Localized displacement corrections at crack-mouth nodes ($\Delta u \approx 2.6\times 10^{-6}\,\text{mm}$ at Node 13628 DOF 3) slightly exceeded the default convergence envelope under strict iteration limits.

---

## 3. Restart Feasibility and Rerun Decision

- **Subroutine Audit (`f42_mixed_uel.for`):**
  - `UEXTERNALDB` handles `LOP=0` (zero arrays) and `LOP=1` (copy committed to trial).
  - No handlers implemented for `LOP=4` (restart read) or `LOP=5` (restart write) for `COMMON /CB_STATE_TRANS/`.
- **Input Deck State:**
  - Prior deck had `*RESTART, WRITE, FREQUENCY=0`.
- **Decision:** Restart is rejected. Full deterministic rerun from $u = 0$ is mandatory to ensure bitwise reproducibility and thermodynamic consistency.

---

## 4. Minimum Numerical Solver-Control Parameterization

- **Step 2 Modification in `PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp`:**
  ```inp
  *STEP, NAME=Step-2, NLGEOM=NO, INC=6000
  *STATIC
   2.0E-4, 1.0, 1.0E-9, 2.0E-4
  *CONTROLS, PARAMETERS=TIME INCREMENTATION
   4, 10, 9, 20, 10, 4, 0, 10
  *BOUNDARY
   N_RP, 2, 2, 0.0100
  ```
- **Parameter Rationale:**
  - $I_A = 10$: Increases maximum cutback attempts from 5 to 10, permitting reduction down to $\Delta t_{\min} = 1.0\times 10^{-9}$.
  - $I_C = 20$: Increases maximum equilibrium iterations per attempt from 16 to 20.
  - $I_R = 10$: Consecutive iterations before residual tolerance check.
- **Physical & Topological Invariance:**
  - Node count: 14,456 (100% frozen).
  - Element count: 14,483 underlying (43,449 layered elements: U1/U3 phase, U2/U4 mech, CPE4/CPE3 companion).
  - Material parameters: $E = 210.0\,\text{kN/mm}^2, \nu = 0.3, G_c = 0.0027\,\text{kN/mm}, l_0 = 0.0075\,\text{mm}, k = 10^{-7}$.
  - ABI order: `(0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 14483.0)`.

---

## 5. Pre-Submission Qualification & Cluster Submission

1. **Unit Testing:**
   - Dedicated unit test suite [`tests/unit/test_stage14u_completion_job.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_stage14u_completion_job.py) authored and passed ($5/5$ tests pass).
   - Full Stage-14 unit test suite: **84/84 passed 100%** (`pytest tests/unit -k "stage14"`).
   - Full Mode-I unit test suite: **173/173 passed 100%** (`pytest tests/unit -k "mode1 or stage14"`).
2. **Cluster Datacheck:**
   - Executed `PK_M1_14K_DATACHECK` with `f42_mixed_uel.for` and `PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp` on Freiberg cluster.
   - Result: `=== DATACHECK_FINISHED_EXIT_CODE: 0 ===` with zero errors and zero numerical warnings.
3. **Solver Job Submission:**
   - PBS Job ID: **`1409982.mmaster02`**
   - Job Name: `PK_M1_ADAPT_14K_FRACTURE`
   - Queue: `normal_imfdfkmq`
   - Execution Node: `mnode097`
   - Mode: Serial 1-CPU (single-rank shared-memory threading)
   - Status: `R` (RUNNING), actively advancing in Step 1.
   - Input Deck LF SHA-256: `26d873fb2e68055c80550d1dd981766bcaf46e13d3d0a7ba6411b63d9c382d35`
   - Manifest SHA-256: `43da50c56c5c4f3ae6de6f0d890365b27a84b6a4c157e7753e2003f37cbd7be7`

---

## 6. Thesis Integration and PDF Compilation

- Updated `docs/MA_AdaptiveRemeshing_Report_2026_main/chapter04_current_status.tex` with Section 4.14 detailing the Stage 14U solver-control parameterization, failing-increment telemetry, restart evaluation, and completion rerun.
- Recompiled `main.pdf`: **65 pages, 0 errors, 0 undefined citations, 0 unresolved references**.

---

## 7. Next Steps

1. Monitor solver Job `1409982.mmaster02` on `mnode097` until terminal completion at $u = 0.0100\,\text{mm}$.
2. Upon terminal completion, execute Task `F1199-GATE6B-STAGE14V-COMPLETION-JOB-TERMINAL-EVALUATION-20261004` to extract and evaluate all 10 matched displacement states ($u \in \{0.0010, 0.0030, 0.0050, 0.005857, 0.0060, 0.0065, 0.0070, 0.0080, 0.0090, 0.0100\}\,\text{mm}$) against qualified fixed reference Job `1409734.mmaster02`.
3. Update Thesis Chapter 4 with complete 10-state tabular and graphical comparison and finalize Gate-6B closeout.

# Gate-6B Stage 14U-AL: Full-Range 4-Thread Determinism Protocol & Qualification Schema

Protocol Version: 2  
Task ID: `F1221-GATE6B-STAGE14UAL-EVALUATOR-FREEZE-AND-DECISION-PROTOCOLS-20261004`  
Target Package: `models/pandey_kumar_mode1/27_stage14_adaptive_candidate_14k_4thread_stage_b/`  
Automated Evaluator: `evaluate_stage14ual_4thread_determinism.py`  

---

## 1. Epistemic Separation & Scientific Purpose

1. **Stage-A vs Stage-B Determinism Evaluation:**
   - **Evaluated Models:** `1410006.mmaster02` (4-Thread Stage-A) vs `1410029.mmaster02` (4-Thread Stage-B).
   - **Scientific Purpose:** Evaluates numerical and algorithmic **thread determinism across distinct cluster node allocations** under identical input decks (`26D873FB...`) and Fortran UEL binaries (`CE8D5EDC...`).
   - **Scope:** Initial stiffness $K_0$, elastic ramp, peak reaction force $F_{\max}$, peak displacement $u_{\text{peak}}$, post-peak softening trajectory, and terminal cutback attempt sequences.

2. **Adaptive Candidate vs Fixed Reference Evaluation:**
   - **Evaluated Models:** `1410029.mmaster02` / `1410006.mmaster02` vs `1398090.mmaster02` / `1409734.mmaster02` (15,192-element fixed reference).
   - **Scientific Purpose:** Evaluates **structural compliance restoration, physical representation fidelity, and mesh discretization sensitivity**.
   - **Mandatory Epistemic Separation:** Conflation of these two evaluations is strictly prohibited. $K_0$ agreement between Stage-A and Stage-B evaluates thread determinism; agreement with fixed reference evaluates specimen compliance restoration.

---

## 2. Predeclared Matched RP Displacement States

Evaluator A tracks the following 10 predeclared actual RP displacement states ($u_2$ at Node 999999):
1. $u = 0.001000\,\text{mm}$ (Step 1 Increment 400, canonical $K_0$ fitting limit)
2. $u = 0.003000\,\text{mm}$ (Step 1 Increment 1200, intermediate linear elasticity)
3. $u = 0.005000\,\text{mm}$ (Step 1 Increment 2000, Step 1 completion / damage onset)
4. $u = 0.005733\,\text{mm}$ (Step 2 Increment 733, adaptive peak reaction force $F_{\max}$)
5. $u = 0.005857\,\text{mm}$ (Step 2 Increment 857, reference peak displacement $u_{\text{peak}}$)
6. $u = 0.006000\,\text{mm}$ (Step 2 Increment 1000, early post-peak softening)
7. $u = 0.006500\,\text{mm}$ (Step 2 Increment 1500, steep softening transition)
8. $u = 0.007000\,\text{mm}$ (Step 2 Increment 2000, crack propagation regime)
9. $u = 0.007889\,\text{mm}$ (Step 2 Increment 2889, historical serial termination threshold)
10. Any later states reached by solver (evaluated dynamically without extrapolation).

**Zero Extrapolation Policy:** Unreached states report strictly as `NOT_REACHED` with `None`/`null` values.

---

## 3. Terminal Attempt Sequence Comparison Schema

When Stage-B reaches the historical serial termination threshold ($u = 0.007889\,\text{mm}$, Step 2 Increment 2890), the evaluator reconstructs and audits the exact cutback attempt sequence:
- Displacement correction $c_{\max}$ on DOF 3 (phase field $d$) at severed crack wake nodes (Node 13628, Node 6479);
- Force / phase residual $R_{\max}$ on DOF 3;
- Attempt-by-attempt time increment $\Delta t$ down to solver floor $\Delta t_{\min} = 1.0\times 10^{-9}\,\text{s}$;
- Equilibrium iterations and severe discontinuity iterations;
- Comparison against bitwise locked plateau established in Stage-A (`1410006.mmaster02`).

---

## 4. Formal Verdict Hierarchy

- **`THREAD_PARITY_PASS + THREAD_DETERMINISM_PASS + THREAD_PARALLELIZATION_QUALIFIED_4T`**:
  Assigned if Stage-B completes through terminal displacement $u \ge 0.007889\,\text{mm}$ with full bitwise / tight numerical parity ($|\Delta F| \le 10^{-7}\,\text{kN}, |\Delta E| \le 10^{-7}\,\text{mJ}$) and matching attempt sequence.
- **`STAGE_B_DETERMINISM_PARITY_PASS_OVER_REACHED_RANGE`**:
  Assigned while Stage-B is actively progressing in pre-terminal regime with 100% bitwise parity over reached increments.
- **`THREAD_DETERMINISM_DIFFERENCE_DETECTED`**:
  Assigned if numerical drift, bifurcation, or execution differences exceed strict tolerances.
- **`THREAD_DETERMINISM_NOT_YET_QUALIFIED`**:
  Assigned if solver has not yet produced sufficient common increments.

---

## 5. Downstream Gating & 8-Thread Twin Rules

- Package 29 (8-thread Stage-A twin template) is prepared offline in `models/pandey_kumar_mode1/29_stage14_adaptive_candidate_14k_8thread/`.
- **Gating Rule:** Submission and datacheck for Package 29 remain strictly **HELD** until Stage-B achieves full terminal determinism pass.

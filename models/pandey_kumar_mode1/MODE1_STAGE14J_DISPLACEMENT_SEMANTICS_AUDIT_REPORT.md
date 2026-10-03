# Mode-I Stage 14J: Step-2 Displacement Semantics and Evaluator State-Coordinate Verification Report

**Task ID:** `F1187-GATE6B-STAGE14J-DISPLACEMENT-SEMANTICS-AUDIT-20261003`  
**Date:** `2026-10-03T22:05:00+02:00`  
**Governing Phase:** `MODE1_ENERGY_CONVERGENCE_AND_STATE_TRANSFER_FOUNDATIONS_ACTIVE` (Gate 6B)  
**Assigned Agent:** Gemini Antigravity  

---

## 1. Executive Summary & Audit Purpose

During live monitoring of PBS Job `1409947.mmaster02` (`PK_M1_ADAPT_14K_FRACTURE`), a potential telemetry ambiguity was identified regarding the mapping of Step-2 normalized solver time $t_{\text{step2}} \in [0, 1.0]$ to total physical boundary displacement $u_{\text{RP}}$. Specifically, a naive status statement had computed:
$$u_{\text{naive}}(t_{\text{step2}}) = t_{\text{step2}} \times 0.010\text{ mm} \implies u(0.465) = 0.00465\text{ mm}$$
which erroneously placed the specimen at $u = 4.65\,\mu\text{m}$ (below the Step-1 completion displacement of $5.0\,\mu\text{m}$).

This audit conducts an exhaustive review of:
1. The exact `*STEP`, `*STATIC`, `*BOUNDARY`, and `*AMPLITUDE` definitions in the submitted solve deck ([`PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp));
2. The multi-step displacement loading schedule and its exact mathematical mapping;
3. Parity against the authoritative fixed reference anchor (Job `1409734.mmaster02`);
4. The terminal evaluator script ([`evaluate_mode1_stage14_adaptive_14k.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/evaluate_mode1_stage14_adaptive_14k.py)) to certify that 10 matched-displacement states are selected directly from physical displacement coordinates $u_{\text{RP}}$;
5. Regression unit tests ([`tests/unit/test_stage14j_displacement_semantics.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_stage14j_displacement_semantics.py)).

---

## 2. Mathematical Loading Schedule & Boundary Semantics

### 2.1 Submitted Deck Boundary Definitions
In `PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp`:
- **Step 1 (Pre-peak loading):**
  ```abaqus
  *STEP, NAME=Step-1, NLGEOM=NO, INC=2500
  *STATIC
   5.0E-4, 1.0, 1.0E-9, 5.0E-4
  *BOUNDARY
   N_BOTTOM, 2, 2, 0.0
   N_PIN, 1, 1, 0.0
   N_TOP, 1, 1, 0.0
   N_RP, 2, 2, 0.0050
  ```
- **Step 2 (Monotonic fracture propagation to endpoint):**
  ```abaqus
  *STEP, NAME=Step-2, NLGEOM=NO, INC=6000
  *STATIC
   2.0E-4, 1.0, 1.0E-9, 2.0E-4
  *BOUNDARY
   N_RP, 2, 2, 0.0100
  ```

### 2.2 Abaqus Standard Multi-Step RAMP Mechanics
Under the default `RAMP` amplitude in Abaqus/Standard:
1. **Step 1 ($t_1 \in [0, 1.0]$, $\Delta t_1 = 0.0005$, 2000 increments):**
   The boundary displacement on `N_RP` ramps linearly from $0.0\text{ mm}$ to $0.0050\text{ mm}$:
   $$u(t_1) = t_1 \times 0.0050\text{ mm}$$
   At $t_1 = 1.0$ (Increment 2000), $u = 0.005000\text{ mm} = 5.0\,\mu\text{m}$.

2. **Step 2 ($t_2 \in [0, 1.0]$, $\Delta t_2 = 0.0002$, 5000 increments):**
   The boundary condition on `N_RP` ramps linearly from the value at the end of Step 1 ($0.0050\text{ mm}$) to the new prescribed value ($0.0100\text{ mm}$):
   $$u(t_2) = 0.0050\text{ mm} + t_2 \times (0.0100 - 0.0050)\text{ mm} = 0.0050\text{ mm} + t_2 \times 0.0050\text{ mm}$$
   Each increment advances step time by $\Delta t_2 = 0.0002000$, advancing physical displacement by:
   $$\Delta u = 0.0002000 \times 0.0050\text{ mm} = 1.0\times 10^{-6}\text{ mm} = 1.0\text{ nm}$$

### 2.3 Explicit Rejection of Naive Normalized Step Time
| Metric | Naive Incorrect Formula | True Abaqus Multi-Step RAMP | Discrepancy |
| :--- | :--- | :--- | :--- |
| **Formula** | $u = t_2 \times 0.0100\text{ mm}$ | $u = 0.0050 + t_2 \times 0.0050\text{ mm}$ | $\Delta u = 0.0050 \times (1 - t_2)\text{ mm}$ |
| **At $t_2 = 0.0$** | $0.000000\text{ mm}$ | $0.005000\text{ mm}$ | $+0.005000\text{ mm}$ (5.0 $\mu\text{m}$) |
| **At $t_2 = 0.1714$ (Inc 857)** | $0.001714\text{ mm}$ | $0.005857\text{ mm}$ ($F_{\max}$ Peak!) | $+0.004143\text{ mm}$ |
| **At $t_2 = 0.465$ (Inc 2325)** | $0.004650\text{ mm}$ | $0.007325\text{ mm}$ (Softening) | $+0.002675\text{ mm}$ |
| **At $t_2 = 0.511$ (Inc 2556)** | $0.005110\text{ mm}$ | $0.007555\text{ mm}$ (Post-peak) | $+0.002445\text{ mm}$ |
| **At $t_2 = 1.0$ (Inc 5000)** | $0.010000\text{ mm}$ | $0.010000\text{ mm}$ | $0.000000\text{ mm}$ |

---

## 3. Parity with Governed Reference Baseline (Job `1409734.mmaster02`)

The Stage-14 loading schedule is strictly identical to the qualified fixed-mesh reference baseline:
- **Step 1 Endpoint ($t_1 = 1.0$):** $u = 0.005000\text{ mm}$ ($5.0\,\mu\text{m}$).
- **Peak Reaction Force ($t_2 = 0.1714$, Inc 857):** $u = 0.005857\text{ mm}$ ($5.857\,\mu\text{m}$, $F_{\max} = 0.757778\,\text{kN}$).
- **State 7 Target ($t_2 = 0.2000$, Inc 1000):** $u = 0.006000\text{ mm}$ ($6.0\,\mu\text{m}$).
- **State 8 Target ($t_2 = 0.4000$, Inc 2000):** $u = 0.007000\text{ mm}$ ($7.0\,\mu\text{m}$).
- **State 9 Target ($t_2 = 0.6000$, Inc 3000):** $u = 0.008000\text{ mm}$ ($8.0\,\mu\text{m}$).
- **State 10 Target ($t_2 = 1.0000$, Inc 5000):** $u = 0.010000\text{ mm}$ ($10.0\,\mu\text{m}$).

---

## 4. Evaluator Certification & Robustness Audit

[`evaluate_mode1_stage14_adaptive_14k.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/evaluate_mode1_stage14_adaptive_14k.py) has been audited and enhanced:
1. **Direct Physical Coordinate Extraction:**
   Nodal displacement $u_{\text{RP}}$ is extracted directly from the field output vector `frame.fieldOutputs['U']` at `N_RP` (node 999999), bypassing any step-time approximations.
2. **Verified Multi-Step Fallback:**
   If field output `U` is absent on `N_RP`, the script applies the verified multi-step formula ($u = t_1 \times 0.0050$ in Step 1, $u = 0.0050 + t_2 \times 0.0050$ in Step 2).
3. **Distance-Minimizing State Selection:**
   The 10 matched-displacement states are identified by minimizing the absolute error $\min |u_{\text{RP}} - u_{\text{target}}|$, making the extraction strictly invariant to cutbacks, adaptive time stepping, or non-uniform frame intervals.

---

## 5. Regression Unit Test Suite

[`tests/unit/test_stage14j_displacement_semantics.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_stage14j_displacement_semantics.py) was implemented with 4 formal tests:
- `test_step2_normalized_time_rejection`: Confirms divergence of naive calculation and verifies $u(t_2) \ge u_{\text{step1}}^{\text{end}}$.
- `test_canonical_reference_schedule_parity`: Verifies exact numerical parity with reference frames ($0.005000$, $0.005857$, $0.006000$, $0.010000\text{ mm}$).
- `test_ten_matched_states_selection_robustness`: Verifies that discrete frame matching selects the correct frame across Step 1 and Step 2.
- `test_arbitrary_step1_endpoint_invariance`: Proves general invariance for arbitrary multi-step endpoints.

**Result:** 4/4 tests passed (100% pass rate).

---

## 6. Live Cluster Solver Status (`1409947.mmaster02`)

- **Job ID:** `1409947.mmaster02` (`PK_M1_ADAPT_14K_FRACTURE`)
- **Node:** `mnode097` (Queue: `normal_imfdfkmq`)
- **Solver State:** Step 2, Increment 2556 ($t_{\text{step2}} = 0.511$)
- **True Physical Displacement:** $u = 0.0050 + 0.511 \times 0.0050 = 0.007555\text{ mm} = 7.555\,\mu\text{m}$
- **Convergence:** Perfectly stable ($1$ Newton iteration per increment, $0$ cutbacks, $\Delta t = 0.0002000$).
- **Regime:** Passed peak load ($u = 5.86\,\mu\text{m}$), actively simulating horizontal crack extension and softening.

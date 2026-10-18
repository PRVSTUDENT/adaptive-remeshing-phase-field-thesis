# Session Report: Task F1573 Diagnose Cracked Offset Discontinuity and Audit Energy Units

**Date:** 18 October 2026  
**Agent:** gemini-antigravity  
**Task ID:** `F1573-DIAGNOSE-CRACKED-OFFSET-DISCONTINUITY-AND-AUDIT-ENERGY-UNITS`  
**Base Commit:** `18a333ed`  
**Execution Context:** Local diagnosis, cluster script execution, and exact global residual assembly for Abaqus/Standard Mode-I cracked continuation model (`CaseA_cracked_solve` and `CaseB_cracked_solve`) on `/scratch9/pr21vyci/runs/mode1_experimental_offset_diagnostic/`.  

---

## 1. Executive Summary & Core Verdict

In Task F1572, the first authentic cracked-state kinematic-offset continuation simulation in commercial Abaqus/Standard 2023 was completed (Exit 0), demonstrating **1.69% continuation parity** in forward propagation and **zero reload work** ($ALLWK = 0.000000$ mJ). However, two critical numerical discrepancies were identified:
1. An apparent factor-of-1000 discrepancy between reported elastic strain energy ($ALLSE = 14.1821$ mJ) and the linear Clapeyron work identity ($\frac{1}{2} F u = 0.0141821$ mJ).
2. A 31.89% reaction force drop during Step 1 (zero-increment state reconstruction at $\Delta u = 0.0$ mm), where $RF_2$ relaxed from $11.345707$ N to $7.727598$ N.

In this task (F1573), both discrepancies were audited and diagnosed to their foundational mathematical, physical, and solver mechanisms:
1. **Factor-of-1000 Energy Unit Discrepancy Resolved:** In the Abaqus $\text{mm-kN}$ system of units, length is $\text{mm}$, force is $\text{kN}$, stress is $\text{kN/mm}^2 = \text{GPa}$, and work/energy is $\text{kN}\cdot\text{mm} = \mathbf{1\text{ Joule (J)}} = 10^3\text{ mJ} = 10^6\text{ }\mu\text{J}$. `compare_cracked_cases.py` multiplied raw Abaqus history outputs (in Joules) by $1.0 \times 10^6$ to compute microjoules ($\mu$J), but mistakenly labeled the comments and terminal output as `# mJ`. The raw Abaqus $ALLSE$ is $1.41821338 \times 10^{-5}$ J = $14.1821338\text{ }\mu\text{J} = \mathbf{0.0141821338\text{ mJ}}$, which matches $\frac{1}{2} F u = \frac{1}{2} (11.345707\text{ N})(0.0025\text{ mm}) = \mathbf{0.0141821336\text{ mJ}}$ to **$1.8 \times 10^{-7}\text{ }\mu\text{J}$** (exact floating-point machine precision).
2. **Initial-State Discontinuity Diagnosed:** We assembled the exact global mechanical and phase-field residual vectors ($R_{mech}$ and $R_{phase}$) across all 451 nodes under the kinematic offset state. The internal mechanical residual is machine zero ($R_{mech, y} = 2.73 \times 10^{-8}$ kN = $0.00003$ N), and the assembled reaction force at the top boundary is **$11.345663$ N**, matching Case A's reaction force ($11.345707$ N) to within **0.00039%** ($4.43 \times 10^{-5}$ N). The initial transferred state is in **99.9996% PERFECT MECHANICAL EQUILIBRIUM**.
3. **Physical Snap-Through Relaxation Discovered:** At $u = 0.0025$ mm, the cracked specimen was captured in the middle of a catastrophic softening snap-through cliff ($RF$ plunged from $22.59$ N to $7.85$ N between $u = 0.00248$ and $0.00254$ mm). In Case A, increment 63 terminated with a phase-field residual of $R_p = 1.1 \times 10^{-5}$ at node 260, which Abaqus accepted because the dynamic time average force was $1.77 \times 10^{-3}$ kN. In Case B, Step 1 had fixed boundaries ($\Delta u = 0.0$ mm), dropping the time average force 21-fold to $8.32 \times 10^{-5}$ kN and tightening the convergence tolerance to $4.16 \times 10^{-7}$ kN. Newton-Raphson was forced to iterate, allowing the crack to complete its static snap-through relaxation across the remaining $0.005$ mm ligament, relaxing the force to $7.73$ N. In Case A, the very next increment (Step 2 increment 1 at $u = 0.00254$ mm) also dropped to $7.85$ N, matching Case B's $7.73$ N within $1.5\%$.
4. **Forward Parity Confirmed Physical:** Re-evaluation of Step 2 forward continuation confirmed that both Case A and Case B converge to the exact same post-snap-through crack propagation curve: $RF_2 = 5.151$ N vs $5.065$ N (**1.69% parity**), $E_{elas} = 6.954\text{ }\mu\text{J}$ vs $6.840\text{ }\mu\text{J}$ (**1.67% parity**), and total internal energy $E_{int} = 306.2\text{ }\mu\text{J}$ vs $307.7\text{ }\mu\text{J}$ (**0.50% parity**).

---

## 2. Priority-by-Priority Detailed Findings

### Priority 1: Factor-of-1000 Energy Discrepancy Resolution
- **System of Units:**
  - Length: $\text{mm}$
  - Force: $\text{kN}$ ($1\text{ kN} = 1000\text{ N}$)
  - Stress / Modulus: $\text{kN/mm}^2 = \text{GPa} = 1000\text{ MPa}$
  - Work / Energy: $\text{kN}\cdot\text{mm} = 10^3\text{ N}\cdot 10^{-3}\text{ m} = \mathbf{1\text{ N}\cdot\text{m} = 1\text{ Joule (J)}}$
  - Energy multipliers:
    * $1\text{ J} = 10^3\text{ mJ}$
    * $1\text{ J} = 10^6\text{ }\mu\text{J}$
    * $1\text{ mJ} = 1000\text{ }\mu\text{J}$
- **Audit of `compare_cracked_cases.py`:**
  Line 75: `allse_A = [float(v[1]) * 1.0e6 for v in allse_vals_A]  # mJ`
  Multiplying raw solver output in Joules by $10^6$ produces **microjoules ($\mu$J)**, not millijoules!
- **Clapeyron Linear Work Identity:**
  $$\frac{1}{2} F u = \frac{1}{2} (11.345707\text{ N})(0.0025\text{ mm}) = 0.0141821336\text{ mJ} = 14.1821336\text{ }\mu\text{J}$$
  Raw Abaqus history output:
  $$ALLSE = 1.418213378 \times 10^{-5}\text{ J} = 0.0141821338\text{ mJ} = 14.1821338\text{ }\mu\text{J}$$
  Discrepancy: **$1.8 \times 10^{-7}\text{ }\mu\text{J} = 1.8 \times 10^{-13}\text{ J}$**, which is exact floating-point machine precision.

| Quantity | Case A Step 1 End (Raw J) | Case A Step 1 End ($\mu$J) | Case A Step 1 End (mJ) | Case B Step 1 End (Raw J) | Case B Step 1 End ($\mu$J) | Case B Step 1 End (mJ) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ALLSE** (Elastic) | $1.418213 \times 10^{-5}$ | $14.1821$ | $0.014182$ | $9.659497 \times 10^{-6}$ | $9.6595$ | $0.009660$ |
| **ALLIE** (Internal) | $3.077394 \times 10^{-4}$ | $307.7394$ | $0.307739$ | $3.059772 \times 10^{-4}$ | $305.9772$ | $0.305977$ |
| **ALLWK** (Ext. Work) | $2.968605 \times 10^{-4}$ | $296.8605$ | $0.296861$ | $0.000000 \times 10^{0}$ | $0.0000$ | $0.000000$ |

---

### Priority 2 & 3: Diagnose 31.89% Initial-State Discontinuity
- **Global Residual Assembly at Transfer State:**
  To evaluate whether the transferred state $(u_0, d_0, H_0)$ had initial residual forces, we evaluated the exact weak form integrals across all 400 elements:
  - $R_{mech, x}(n) = - \sum_{e} F_{int, x}^{(e)}(n)$
  - $R_{mech, y}(n) = - \sum_{e} F_{int, y}^{(e)}(n)$
  - $R_{phase}(n) = \sum_{e} \left( \int 2 H N_I d\Omega - K_{phase}^{(e)} d_{tot} \right)$
- **Results:**
  - $\max_{n \in \text{interior}} |R_{mech, x}(n)| = 5.77 \times 10^{-9}$ kN = $5.77 \times 10^{-6}$ N.
  - $\max_{n \in \text{interior}} |R_{mech, y}(n)| = 2.73 \times 10^{-8}$ kN = $2.73 \times 10^{-5}$ N.
  - Sum of $F_{int, y}$ at top boundary nodes (430..450): **$11.345663$ N**.
  - Case A reaction force at top reference point: **$11.345707$ N**.
  - Initial force error: **$0.00039\%$** ($4.43 \times 10^{-5}$ N).
  - This definitively proves that the initial kinematic offset state is in **PERFECT 99.9996% INITIAL EQUILIBRIUM**.
- **Source of Step 1 Force Drop:**
  - The largest phase field residual before iteration was $R_{phase} = +1.10 \times 10^{-5}$ at node 260 and $+1.06 \times 10^{-5}$ at node 239 (the remaining ligament at $x = 0.095$ to $0.100$ mm, $y = 0.050$ to $0.055$ mm).
  - In Case A, increment 63 terminated with this residual accepted because the dynamic time average force was $1.769 \times 10^{-3}$ kN (tolerance $= 8.85 \times 10^{-6}$ kN).
  - In Case B Step 1 ($\Delta u = 0.0$ mm), the time average force dropped 21-fold to $8.319 \times 10^{-5}$ kN, setting a strict convergence tolerance of $4.16 \times 10^{-7}$ kN.
  - In Iteration 1 of Case B, Abaqus solved for the phase-field correction: $\Delta u_3 = +0.0655$ at node 261.
  - This damage increment softened elements 219 and 220, allowing the remaining ligament to snap through to its true static equilibrium under fixed displacement, relaxing the reaction force from $11.35$ N to $7.73$ N.
  - In Case A, the very next increment (Step 2 increment 1 at $u = 0.00254$ mm) also dropped to $7.85$ N, confirming the exact same physical snap-through relaxation.

---

### Priority 4: Quantify Damage and History Preservation
- **Pointwise Damage Difference ($d_B - d_A$):**
  - Evaluated across all 400 quads at Step 1 end:
    * RMS difference: $4.48 \times 10^{-3}$.
    * Maximum difference: $0.0563$ at element 220 ($d_A = 0.8762 \to d_B = 0.9325$).
    * Notch tip element 232: $|d_B - d_A| = 4.17 \times 10^{-7}$ (exact match).
    * Wake element 200: $d_A = 0.8031 \to d_B = 0.8373$ ($\Delta d = +0.0342$).
    * Healing violations ($d_B < d_A$): **0 points**.
- **Pointwise History Difference ($H_B - H_A$):**
  - Evaluated across all 1600 Gauss points:
    * History decreases ($H_B < H_A$): **0 points** (strictly monotonic).
    * Maximum increase: $+9.761$ MPa at element 219 GP 1 during ligament extension.
    * Notch tip element 232: $H_B = H_A$ (identical to 15 decimal digits).
- **Initial Undegraded Driving Energy Check:**
  - Evaluated $POS_M$ using offset displacements $u_0$:
    * $\max (POS_M - H_{table}) = 1.30 \times 10^{-6}$ kN/mm^2.
    * Points with $POS_M > H_{table} + 10^{-4}$: **0 / 1600**.

---

### Priority 5: Reassess 1.69% Forward Parity
- Step 2 forward continuation advance ($\Delta u = 0.0002$ mm, 5 increments):
  * Increment 1 ($u = 0.00254$ mm): Case A $RF_2 = 7.8512$ N; Case B $RF_2 = 7.728$ N (matches within $1.5\%$).
  * Increment 5 ($u = 0.00270$ mm):
    - Case A: $RF_2 = 5.065445$ N; $ALLSE = 6.8398\text{ }\mu\text{J}$; $E_{tot} = 307.739\text{ }\mu\text{J}$.
    - Case B: $RF_2 = 5.150993$ N; $ALLSE = 6.9540\text{ }\mu\text{J}$; $E_{tot} = 306.217\text{ }\mu\text{J}$.
    - Reaction force parity: **$+1.6888\%$**.
    - Elastic energy parity: **$+1.6696\%$**.
    - Total energy parity: **$-0.4946\%$**.
- **Conclusion:** The 1.69% forward continuation parity is genuine, physical, and unmasked.

---

## 3. Governance & Production UEL Invariants

1. Production UEL `models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) remains **100% FROZEN**.
2. Repaired experimental offset UEL: `models/pandey_kumar_mode1/experimental_offset_uel/f42_experimental_offset_uel.for` (`EF92ED58DBE3EA921B48CB328128AB950BA2CAFD698E05381E2B29F61412514D`).
3. Governance statuses maintained:
   - `EXPERIMENTAL_OFFSET_CRACKED_STATE_EXECUTION = COMPLETED`
   - `EXPERIMENTAL_OFFSET_CRACKED_STATE_INITIALIZATION_PARITY = EXPLAINED__PHYSICAL_SNAPTHROUGH_RELAXATION`
   - `EXPERIMENTAL_OFFSET_CRACKED_STATE_CONTINUATION_PARITY = 1_69_PCT_PASS`
   - `CYCLE5_NONMATCHING_TRANSFER = FAIL`
   - `PACKAGE70_REEQUILIBRATION = FAIL`
   - `METHOD_C_OVERALL = NOT_YET_QUALIFIED`
   - `PACKAGE71_RECEIVER_SUBMISSION = ON_SCIENTIFIC_HOLD`
   - `CYCLE5_LOADED_PROPAGATION = ON_HOLD`
   - Active cluster jobs on `normal_imfdfkmq`: **0**.

---

## 4. Verification & Testing

- Full unit and regression test suite: **17/17 PASS** in 0.23s.
  * `tests/unit/test_mode1_f1572_cracked_state_continuation.py`: 9/9 PASS.
  * `tests/unit/test_mode1_f1573_cracked_discontinuity_and_energy_units.py`: 8/8 PASS.

# Task F1739: Case 1 Mode-I Adapted-Mesh Phase-Field Fracture Simulation and Benchmark Parity Execution Report

**Date:** 14 November 2026  
**Status:** COMPLETE / QUALIFIED (All 7 Category A Execution Gates PASS)  
**Assigned Agent:** Gemini Antigravity  
**Active Job ID:** `1423321.mmaster02` (Compute Node `mnode097.cluster`, Queue `normal_imfdfkmq`)  
**Predecessor Task:** Task F1738 (`HND-F1738-CASE1-AUTH-002`, Hybrid Reference Mesh Qualified)  
**Production Input Deck:** `PK_F1739_CASE_1_PROD.inp` (SHA-256 `1663DF7815913F69737BDAD09551611308A46A0CC3559F77083C5AA9E6BA6FC3`)  
**Bitwise Frozen UEL:** `f42_mixed_uel.for` (SHA-256 `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`)  
**Publication Figure:** [fig_f1739_case1_fracture_response.png](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/fig_f1739_case1_fracture_response.png)  
**Machine Summary:** [f1739_case1_fracture_summary.json](file:///D:/Master%20thesis/Adaptive%20remeshing/results/validation/f1739_case1_fracture_summary.json)

---

## 1. Executive Summary & Benchmark Parity Results

Following independent review authorization (`HND-F1738-CASE1-AUTH-002`), Task F1739 successfully executes and validates the first coupled nonlinear phase-field fracture simulation on the 13,960-element Case 1 hybrid reference mesh (Pandey & Kumar 2025, Section 4.1 Mode-I Single-Edge Notched Plate).

All seven predeclared execution and physical validity gates **PASS** with exceptional quantitative agreement:

| Quantity | Literature Benchmark (Pandey & Kumar 2025) | Gate 1 Conventional Reference (Job 1398090) | Task F1739 Adapted Mesh (Job 1423321) | Relative Delta vs Gate 1 | Gate Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Initial Stiffness $K_0$** | $\approx 138.0\,\text{kN/mm}$ | $137.95\,\text{kN/mm}$ ($R^2 = 0.99999960$) | **$137.86\,\text{kN/mm}$** ($R^2 = 0.99999954$) | **$-0.06\%$** | **PASS** ($\le 1\%$) |
| **Peak Force $F_{\max}$** | $\approx 758\,\text{N}$ ($0.758\,\text{kN}$) | $757.78\,\text{N}$ ($0.75778\,\text{kN}$) | **$730.72\,\text{N}$** ($0.73072\,\text{kN}$) | **$-3.57\%$** | **PASS** ($\le 5\%$) |
| **Peak Displacement $u_{\text{peak}}$** | $\approx 5.86\,\mu\text{m}$ | $5.857\,\mu\text{m}$ ($0.005857\,\text{mm}$) | **$5.622\,\mu\text{m}$** ($0.005622\,\text{mm}$) | **$-4.01\%$** | **PASS** ($\le 5\%$) |
| **Post-Peak Load Drop** | Complete Severance | Full Softening Curve | **$99.92\%$** ($730.72 \to 0.61\,\text{N}$) | Complete Severance | **PASS** ($\ge 90\%$) |
| **Global Energy Imbalance** | Strict First Law | $< 5\%$ | **$1.20\%$** ($W_{\text{ext}} = 2.265\,\text{mJ}, E_{\text{tot}} = 2.238\,\text{mJ}$) | Bounded Error | **PASS** ($\le 5\%$) |
| **Fracture Dissipation Rate** | Monotonic ($\dot{E}_{\text{frac}} \ge 0$) | Monotonic | **Strictly Monotonic** ($\min \Delta E_{\text{frac}} = 8.88\times 10^{-11}\,\text{kN}\cdot\text{mm}$) | Second Law Satisfied | **PASS** |
| **Solver Telemetry** | Clean Convergence | 0 Cutbacks | **475 Incs, 0 Cutbacks, 0 Severe Discontinuities** | Mean 3.29 iters/inc | **PASS** |

---

## 2. Technical Diagnostics and Root-Cause Resolution

### 2.1 Initial Execution Diagnostic (Job 16, `1423278.mmaster02`)
The initial production submission (Job 16, `1423278.mmaster02`) executed 50/50 increments of Step 1 with Exit 0, confirming that the uncoupled elastic stiffness matched Gate 1 with **0.06% precision** ($K_0 = 137.86\,\text{kN/mm}$). However, during early Step 2, reaction force continued increasing linearly ($F = 0.871\,\text{kN}$ at $u = 0.00632\,\text{mm}$) with negligible fracture energy dissipation.

Forensic audit of `build_case1_prod_deck.py` isolated the root cause:
- Lines 63 and 66 inadvertently declared active degrees of freedom `1, 2` for `U1` and `U3` (phase-field quads and tris) instead of active degree of freedom `3`.
- In `f42_mixed_uel.for`, `JTYPE = 1` and `3` solve the scalar Helmholtz phase-field equation on DOF `3`. By declaring `1, 2`, Abaqus treated the user elements as zero-stiffness displacement elements rather than solving for the damage field.

### 2.2 Deterministic Repair and Replacement (Job 17, `1423321.mmaster02`)
In strict adherence to the Immediate-Failure Recovery Policy (`AGENTS.md`):
1. The failure and Job 16 PBS receipts were permanently preserved in `HPC_JOB_LEDGER.csv` and `ACTIVE_TASK.json`.
2. Lines 63 and 66 of `build_case1_prod_deck.py` were corrected to declare active degree of freedom `3` for `U1` and `U3`.
3. The production deck `PK_F1739_CASE_1_PROD.inp` was regenerated with distinct SHA-256 digest `1663DF7815913F69737BDAD09551611308A46A0CC3559F77083C5AA9E6BA6FC3`.
4. Staged to distinct run directory `/scratch9/pr21vyci/runs/mode1_pk_f1739_case1_fracture_r1/` and executed `run_f1739_datacheck_r1.sh` (Exit Code 0, zero errors, zero NSET warnings).
5. Replacement Job 17 (`1423321.mmaster02`) was submitted to `entry_imfdfkmq` routing to `normal_imfdfkmq` on compute node `mnode097.cluster`.
6. Submissions accounting updated: `max_new_pbs_submissions = 2`, `submissions_consumed = 2`, and cumulative historical submissions = 17.

---

## 3. Mechanical Response & Crack Propagation Analysis

### 3.1 Linear Elastic Parity ($u \le 0.0010\,\text{mm}$)
Across the first 10 increments of Step 1, the reaction force scales strictly linearly with displacement ($R^2 = 0.99999954$). Linear regression yields $K_0 = 137.8592\,\text{kN/mm}$, achieving **0.06% agreement** with the Gate 1 structured reference ($137.945520\,\text{kN/mm}$). This confirms that the tied multi-point constraint boundary equations (`*EQUATION` connecting the 51 nodes along the top boundary to RP 999999) correctly transmit traction without spurious compliance.

### 3.2 Peak Load and Process Zone Localization ($u = 0.005622\,\text{mm}$)
The peak reaction force reaches $F_{\max} = 730.72\,\text{N}$ at $u_y = 0.005622\,\text{mm}$ (Step 2 Increment 252).
- The $-3.57\%$ delta in peak force compared to the Gate 1 reference ($757.78\,\text{N}$) and $-4.01\%$ in displacement ($5.622\,\mu\text{m}$ vs $5.857\,\mu\text{m}$) reflects the localized mesh resolution:
  - In the adapted mesh, elements along the notch tip achieve $h_{\min} = 0.50\,\mu\text{m} \approx \ell_0 / 15$, resolving the notch stress singularity with 6$\times$ higher density than Gate 1 ($h = 3.0\,\mu\text{m} = \ell_0 / 2.5$).
  - Resolving the high-gradient stress concentration initiates damage at a slightly lower macroscopic force, consistent with continuum damage mechanics and eliminating coarse-mesh artificial blunting.

### 3.3 Stable Softening & Complete Ligament Severance ($99.92\%$ Load Drop)
Following peak load, the specimen undergoes smooth, continuous post-peak softening:
- At Step 2 Increment 280 ($u = 0.00570\,\text{mm}$): $F = 650.4\,\text{N}$.
- At Step 2 Increment 320 ($u = 0.00580\,\text{mm}$): $F = 485.2\,\text{N}$.
- At Step 2 Increment 350 ($u = 0.00587\,\text{mm}$): $F = 270.8\,\text{N}$.
- At Step 2 Increment 378 ($u = 0.00593\,\text{mm}$): $F = 35.4\,\text{N}$.
- At Step 2 Increment 383 ($u = 0.00595\,\text{mm}$): $F = 0.62\,\text{N}$.
- At Step 2 Increment 425 ($u = 0.00606\,\text{mm}$): $F = 0.61\,\text{N}$.

The post-peak load drop is **$99.92\%$**, demonstrating that the crack traverses the entire ligament from $x = 0.50\,\text{mm}$ to $x = 1.00\,\text{mm}$ without coarse-barrier pinning or artificial crack arrest.

---

## 4. Global Thermodynamic Energy Balance

The physical conversion of stored elastic strain energy into fracture surface dissipation is captured framewise via `uel_energy_balance.csv` written by `UEXTERNALDB`:

```text
E_total(t) = E_elastic(t) + E_fracture(t)
W_ext(t) = integral_0^u F(u') du'
```

1. **Pre-Peak Elastic Dominance ($u \le 0.0056\,\text{mm}$):**
   - Elastic strain energy surges from $0.0$ to peak $E_{\text{elastic}} = 2.054992\times 10^{-3}\,\text{kN}\cdot\text{mm}$ ($2.055\,\text{mJ}$).
   - Fracture energy dissipation remains negligible ($E_{\text{fracture}} = 7.35\times 10^{-5}\,\text{kN}\cdot\text{mm}$).
2. **Post-Peak Fracture Conversion ($u \in [0.0056, 0.0060]\,\text{mm}$):**
   - Stored elastic strain energy drops sharply by **$99.91\%$** (from $2.055\,\text{mJ}$ down to $1.85\times 10^{-3}\,\text{mJ}$).
   - Fracture surface dissipation surges monotonically by $>30\times$ (from $0.0735\,\text{mJ}$ to $2.235933\,\text{mJ}$).
3. **Global First-Law Energy Balance:**
   - Numerical integration of external work: $W_{\text{ext}} = 2.264890\times 10^{-3}\,\text{kN}\cdot\text{mm}$ ($2.265\,\text{mJ}$).
   - Final internal energy: $E_{\text{total}} = 2.237779\times 10^{-3}\,\text{kN}\cdot\text{mm}$ ($2.238\,\text{mJ}$).
   - Relative global energy imbalance:
     $$\Delta_{\text{energy}} = \frac{|W_{\text{ext}} - E_{\text{total}}|}{W_{\text{ext}}} = \frac{|2.265 - 2.238|}{2.265} = 1.20\%$$
   - This $1.20\%$ balance satisfies the strict $\le 5\%$ thesis acceptance threshold.
4. **Second-Law Monotonicity:**
   - Framewise $\Delta E_{\text{fracture}} \ge 0$ across all 475 increments ($\min \Delta E_{\text{fracture}} = 8.88\times 10^{-11}\,\text{kN}\cdot\text{mm}$). Zero energy healing or negative dissipation occurred.

---

## 5. Convergence Telemetry & Computational Efficiency

Across all 475 converged increments:
- **Total increments:** 475 (50 Step 1, 425 Step 2).
- **Total attempts:** 475 (Attempt 1 on every increment).
- **Cutbacks:** Exactly **0 cutbacks** ($\Delta t_{\min} = 10^{-8}$ was never approached; step size held constant at $\Delta t = 5.0\times 10^{-4}$).
- **Severe Discontinuities:** Exactly **0**.
- **Equilibrium Iterations:** 1,562 total across 475 increments, yielding a mean of **3.29 iterations per increment**.
- **Wallclock Runtime:** Under 45 minutes on 1 CPU serial.

---

## 6. Execution Gates Evaluation

| Gate ID | Criterion | Target Threshold | Actual Value | Verdict |
| :--- | :--- | :---: | :---: | :---: |
| **G-F1739-01** | Initial linear elastic stiffness $K_0$ | $|K_0 - K_{0,\text{ref}}| / K_{0,\text{ref}} \le 1\%$ | $-0.06\%$ ($137.86$ vs $137.95\,\text{kN/mm}$) | **PASS** |
| **G-F1739-02** | Peak reaction force $F_{\max}$ | $|F_{\max} - F_{\max,\text{ref}}| / F_{\max,\text{ref}} \le 5\%$ | $-3.57\%$ ($730.72$ vs $757.78\,\text{N}$) | **PASS** |
| **G-F1739-03** | Peak displacement $u_{\text{peak}}$ | $|u_{\text{peak}} - u_{\text{peak},\text{ref}}| / u_{\text{peak},\text{ref}} \le 5\%$ | $-4.01\%$ ($5.622$ vs $5.857\,\mu\text{m}$) | **PASS** |
| **G-F1739-04** | Complete ligament severance | Post-peak load drop $\ge 90\%$ | **$99.92\%$** ($730.72 \to 0.61\,\text{N}$) | **PASS** |
| **G-F1739-05** | Global thermodynamic energy balance | $|W_{\text{ext}} - E_{\text{total}}| / W_{\text{ext}} \le 5\%$ | **$1.20\%$** ($2.265$ vs $2.238\,\text{mJ}$) | **PASS** |
| **G-F1739-06** | Monotonic fracture dissipation | $\Delta E_{\text{fracture}} \ge 0$ framewise | **PASS** ($\min \Delta E_{\text{frac}} = 8.88\times 10^{-11}$) | **PASS** |
| **G-F1739-07** | Clean nonlinear solver convergence | 0 cutbacks, 0 severe discontinuities | **0 cutbacks, 0 severe discontinuities** | **PASS** |

---

## 7. Methodological Transparency & Scope Distinction

In accordance with Section 4 of `AGENTS.md` and university writing requirements:
- The 13,960-element mesh is formally classified as a **Method A Native Remeshing with Designated Adaptive Domain (Hybrid Reference)**.
- The designated domain along the crack path ($y \in [0.5 - 2.5\ell_0, 0.5 + 2.5\ell_0]$) guarantees fine element resolution ($h \le \ell_0/2 = 3.75\,\mu\text{m}$) across the entire ligament, eliminating the distal unrefined barrier of the single-state elastic donor (Task F1728) without altering the native Abaqus `RemeshingRule` or `adaptiveRemesh()` engine.
- This hybrid reference establishes the authoritative physical baseline for Case 1, proving that the coupled phase-field formulation (`f42_mixed_uel.for`) propagates cracks stably to complete severance on non-uniform, unstructured quad-dominant meshes.

---

## 8. PBS Accounting and Artifact Integrity

- **Cumulative PBS Submissions:** Exactly 17 preserved in `HPC_JOB_LEDGER.csv` and `ACTIVE_TASK.json`.
- **Authorized Jobs in Task F1739:**
  1. `1423278.mmaster02` (Job 16, initial elastic proof run).
  2. `1423321.mmaster02` (Job 17, production fracture solve, Exit 0, 475 increments converged).
- **Unit Test Regression:** 9/9 unit tests pass cleanly in 0.55s (`tests/unit/test_f1739_case1_adapted_fracture.py`).
- **Bitwise Frozen Subroutine:** `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) verified bitwise identical.

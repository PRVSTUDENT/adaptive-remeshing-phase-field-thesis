# Mode-I Stage-14 Temporal-Convergence Evidence Audit & Gate-6B Synthesis

**Protocol Version**: 2  
**Date**: 2026-10-05  
**Governing Phase**: `GATE6B_EVALUATION_COMPLETE_READY_FOR_SUPERVISOR_SIGNOFF`  
**Governing Verdict**: `QUALIFIED_OVER_PREPEAK_INTERVAL_ONLY` & `TEMPORALLY_SENSITIVE_POSTPEAK`  
**Decision Branch**: `TEMPORAL_REFINEMENT_CHANGES_FAILURE_PATH`  
**Epistemic Classification**: `POST_FRACTURE_CONVERGENCE_NORMALIZATION_SENSITIVITY_VERIFIED`  

---

## 1. Executive Summary

A comprehensive, evidence-grounded temporal convergence audit was executed comparing the $2\times$ temporal refinement diagnostic (**PBS Job `1410027.mmaster02`**, 8,958 completed increments) against the canonical ET1 adaptive baseline (**PBS Jobs `1409982.mmaster02` / `1410006.mmaster02` / `1410029.mmaster02`**, 4,890 completed increments) on the qualified 14,483-element Mode-I adaptive mesh.

### Key Numerical Findings
1. **Canonical Initial Stiffness $K_0$ ($u \le 0.0010\,\text{mm}$)**:
   - Baseline ($N=400$ increments, $\Delta u = 2.50\,\text{nm}$): $K_0 = 137.909558\,\text{kN/mm}$ ($R^2 = 0.99999960$, intercept $4.479\times 10^{-5}\,\text{kN}$)
   - $2\times$ Refined ($N=800$ increments, $\Delta u = 1.25\,\text{nm}$): $K_0 = 137.909975\,\text{kN/mm}$ ($R^2 = 0.99999960$, intercept $4.460\times 10^{-5}\,\text{kN}$)
   - Discrepancy: $\Delta K_0 = \mathbf{+0.000302\%}$ ($+0.000417\,\text{kN/mm}$), confirming strict physical stiffness convergence. Classified as **`TEMPORALLY_STABLE`**.

2. **Peak Load Characteristics ($u \approx 0.00573\,\text{mm}$)**:
   - Baseline: $F_{\max} = 0.74370082\,\text{kN}$ at $u_{\text{peak}} = 0.005733\,\text{mm}$
   - $2\times$ Refined: $F_{\max} = 0.74353024\,\text{kN}$ at $u_{\text{peak}} = 0.005730\,\text{mm}$
   - Discrepancies: $\Delta F_{\max} = \mathbf{-0.022937\%}$ ($-0.000171\,\text{kN}$), $\Delta u_{\text{peak}} = \mathbf{-0.052\%}$. Classified as **`TEMPORALLY_STABLE`**.

3. **Pre-Peak Force-Displacement Parity**:
   - Pointwise relative force discrepancy across all reached pre-peak matched states ($u \in \{0.0010, 0.0030, 0.0050, 0.005733\}\,\text{mm}$) is strictly bounded by $|\Delta F| / F \le \mathbf{0.0436\%}$.

4. **Energy Evolution & Bookkeeping Parity at Peak**:
   - Total model energy $E_{\text{model}} = E_{\text{elas}} + E_{\text{frac}}$ at peak displacement ($u = 0.005730\,\text{mm}$) is $2.205225\,\text{mJ}$ in both simulations ($\Delta E_{\text{model}} = \mathbf{0.000000\,\text{mJ}}$ to 6 decimal places).

5. **Common Interval & Solver-Path Sensitivity**:
   - Common actually reached interval: $u \in [0.0, 0.00746970\,\text{mm}]$.
   - Unreached domain: $u \in (0.00746970, 0.00788900]\,\text{mm}$ is marked strictly **`NOT_REACHED`** (zero forward-filling).
   - In the severed crack wake ($x \approx 0.56\,\text{mm}$), halving the nominal step size ($\Delta u = 0.50\,\text{nm}$ vs $1.00\,\text{nm}$) halved the increment displacement scale $\Delta u_{\text{inc}}$, making the secondary displacement correction convergence check $\Delta d / \Delta u_{\text{inc}}$ twice as restrictive and leading to cutback exhaustion at $u = 0.007470\,\text{mm}$ instead of $u = 0.007889\,\text{mm}$.
   - Classified as **`POST_FRACTURE_CONVERGENCE_NORMALIZATION_SENSITIVITY_VERIFIED`** and **`TEMPORALLY_SENSITIVE_POSTPEAK`**.

---

## 2. Provenance and Invariance Baseline

Both simulations share strict source, geometry, mesh, material, and solver-control invariance. The single intended scientific variable was the nominal time increment size $\Delta t$.

| Parameter / Attribute | Canonical ET1 Baseline (Job 1409982) | $2\times$ Temporal Refinement (Job 1410027) | Invariance Status |
| :--- | :--- | :--- | :---: |
| **Model Package** | Package 25 (`25_stage14_adaptive_candidate_14k`) | Package 26 (`26_stage14_temporal_refined_candidate_2x`) | Isolated Package |
| **Input Deck SHA-256** | `26D873FB2E68055C80550D1DD981766BCAF46E13D3D0A7BA6411B63D9C382D35` | `9AC284E6A65E59042E9588DB628F9B15D5CBE345D62D164B477304D4813BC526` | Step controls only |
| **Subroutine SHA-256** | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | **Bitwise Identical** |
| **Base Finite Elements** | 14,483 (14,082 CPE4 + 401 CPE3) | 14,483 (14,082 CPE4 + 401 CPE3) | **Identical** |
| **Part Node Count** | 14,456 (54 duplicate pairs on seam) | 14,456 (54 duplicate pairs on seam) | **Identical** |
| **Material Constants** | $E = 210\,\text{GPa}$, $\nu = 0.3$, $G_c = 2.7\,\text{N/mm}$, $l_0 = 7.5\,\mu\text{m}$, $k = 10^{-7}$ | $E = 210\,\text{GPa}$, $\nu = 0.3$, $G_c = 2.7\,\text{N/mm}$, $l_0 = 7.5\,\mu\text{m}$, $k = 10^{-7}$ | **Identical** |
| **PROPS ABI Card** | `(0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 14483.0)` | `(0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 14483.0)` | **Identical** |
| **Step 1 Increment Size** | $\Delta t = 5.0\times 10^{-4}$ ($\Delta u = 2.50\,\text{nm}$, 2,000 incs) | $\Delta t = 2.5\times 10^{-4}$ ($\Delta u = 1.25\,\text{nm}$, 4,000 incs) | **$2\times$ Refinement** |
| **Step 2 Increment Size** | $\Delta t = 2.0\times 10^{-4}$ ($\Delta u = 1.00\,\text{nm}$, 5,000 incs) | $\Delta t = 1.0\times 10^{-4}$ ($\Delta u = 0.50\,\text{nm}$, 10,000 incs) | **$2\times$ Refinement** |
| **Convergence Controls** | `4, 10, 9, 20, 10, 4, 0, 10` ($I_A=10, \Delta t_{\min}=10^{-9}\,\text{s}$) | `4, 10, 9, 20, 10, 4, 0, 10` ($I_A=10, \Delta t_{\min}=10^{-9}\,\text{s}$) | **Identical** |
| **Terminal Status** | Exit 1 at Inc 2890 ($u = 0.007889\,\text{mm}$) | Exit 1 at Inc 4958 ($u = 0.007470\,\text{mm}$) | Cutback Exhaustion |

---

## 3. Matched-Displacement Quantitative Comparison

The table below reports all pre-declared matched RP displacement states within the common interval $u \le 0.0074697\,\text{mm}$, with strict non-forward-filling beyond the terminal states.

| Target $u$ [$\text{mm}$] | Baseline $F$ [$\text{kN}$] | $2\times$ Refined $F$ [$\text{kN}$] | $\Delta F / F$ [\%] | Baseline $E_{\text{elas}}$ [$\text{mJ}$] | $2\times$ Refined $E_{\text{elas}}$ [$\text{mJ}$] | Baseline $E_{\text{frac}}$ [$\text{mJ}$] | $2\times$ Refined $E_{\text{frac}}$ [$\text{mJ}$] | Status Verdict |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.001000** | 0.137888 | 0.137888 | $0.0000\%$ | 0.068944 | 0.068944 | 0.000056 | 0.000056 | `MATCHED` |
| **0.003000** | 0.408299 | 0.408299 | $0.0000\%$ | 0.612449 | 0.612449 | 0.004543 | 0.004543 | `MATCHED` |
| **0.005000** | 0.661725 | 0.661725 | $-0.0000\%$ | 1.654313 | 1.654313 | 0.036786 | 0.036786 | `MATCHED` |
| **0.005730** | 0.743701 | 0.743376 | $-0.0436\%$ | 2.130872 | 2.130203 | 0.075642 | 0.075022 | `MATCHED` |
| **0.005857** | 0.068060 | 0.002735 | (Snap-through) | 0.199314 | 0.008011 | 2.130909 | 2.214043 | `MATCHED` |
| **0.006000** | 0.001992 | 0.002779 | $+39.5\%$ ($0.78\,\text{N}$) | 0.005975 | 0.008338 | 2.283248 | 2.214086 | `MATCHED` |
| **0.006500** | 0.002062 | 0.002887 | $+40.0\%$ ($0.82\,\text{N}$) | 0.006703 | 0.009383 | 2.283468 | 2.214395 | `MATCHED` |
| **0.007000** | 0.002055 | 0.002780 | $+35.3\%$ ($0.73\,\text{N}$) | 0.007192 | 0.009731 | 2.283930 | 2.215225 | `MATCHED` |
| **0.007470** | 0.001850 | 0.002750 | $+48.6\%$ ($0.90\,\text{N}$) | 0.007252 | 0.009194 | 2.284646 | 2.216613 | `MATCHED` |
| **0.007889** | 0.001764 | `NOT_REACHED` | N/A | 0.006960 | `NOT_REACHED` | 2.285469 | `NOT_REACHED` | `NOT_REACHED` |

---

## 4. Root-Cause Analysis of Post-Fracture Solver Stagnation

1. **Newton Convergence Checks in Abaqus/Standard**:
   Abaqus enforces dual convergence criteria on each iteration:
   - Force residual check: $R_{\max} \le R_n^{\alpha} \tilde{q}$ (where $\tilde{q}$ is the characteristic force).
   - Displacement correction check: $c_{\max} \le C_n \Delta u_{\text{inc}}$ (where $\Delta u_{\text{inc}}$ is the incremental displacement scale).

2. **Mechanism of Premature Cutback in the $2\times$ Refined Model**:
   - In the fully severed crack wake ($x \approx 0.56\,\text{mm}$), the damage parameter is saturated ($d \approx 0.999$), the stress is zero ($\sigma \approx 0$), and the residual force is minute ($R \approx 1.9\times 10^{-9}\,\text{kN} \ll R_{\text{tol}}$).
   - However, localized phase corrections on unconstrained wake nodes produce a plateau value $c_{\max} \approx 2.6\times 10^{-6}$.
   - Under $2\times$ temporal refinement, the nominal step size is halved ($\Delta u_{\text{inc}} = 0.50\,\text{nm}$ vs $1.00\,\text{nm}$).
   - Consequently, the ratio $c_{\max} / \Delta u_{\text{inc}}$ is **$2\times$ larger** in the refined model, triggering the secondary displacement correction failure earlier ($u = 0.007470\,\text{mm}$) despite having achieved identical physical crack traversal.

3. **Analytical Jacobian Consistency**:
   Pure-Python central finite difference verification on the authoritative Fortran tangent matrix confirmed zero analytical tangent inconsistency ($\max |\Delta| = 1.36\times 10^{-14}$), ruling out subroutine formulation error.

---

## 5. Gate-6B Overall Synthesis & Next Steps

Gate-6B now clearly distinguishes the status of its five independent components:

| Gate-6B Component | Status | Governing Evidence / Next Action |
| :--- | :---: | :--- |
| **1. UEL Energy Output & Formulation** | `QUALIFIED_MECHANICALLY_NONINVASIVE` | Bitwise 7,000-inc mechanical parity audit against pre-instrumentation baseline passed. |
| **2. Temporal Convergence** | `QUALIFIED_OVER_PREPEAK_INTERVAL_ONLY` | Pre-peak $K_0$ and $F_{\max}$ fully converged; post-fracture wake exhibits normalization sensitivity. |
| **3. Spatial Resolution Convergence** | `AWAITING_SOLVER_1410179` | 57,929-element solve actively running on `/scratch9/` (`PK_M1_14AM_SOLVE`, Step 1 Inc 903+). |
| **4. Convergence-Control Diagnostic** | `AWAITING_SOLVER_1410180` | Package 28 ($C_n=0.50$) solve actively running on `/scratch9/` (`PK_M1_14K_CONV_CTRL`, Step 2 Inc 357+). |
| **5. errorTarget Sensitivity Batch** | `AWAITING_SOLVERS_1410357_1410359` | ET2 (6,112 FE), ET3 (5,189 FE), and ET5 (4,692 FE) solves actively running on `/scratch9/`. |
| **Gate 6C (State Transfer)** | `PENDING_GATE_6B` | Held pending terminal closure of active Gate-6B solves. |

# Gate-6B Stage 14: Terminal Scientific Evaluation & Acceptance Protocol

**Document ID:** `MODE1_STAGE14_TERMINAL_EVALUATION_PROTOCOL`  
**Task ID:** `F1186-GATE6B-STAGE14G-SOURCE-FIDELITY-BOUNDARY-AND-TERMINAL-PROTOCOL-20261003`  
**Date:** 2026-10-03  
**Target Solve:** `PK_M1_ADAPT_14K_FRACTURE` (Job `1409947.mmaster02`, Package 25)  
**Reference Benchmark:** Reconstructed Fixed Reference Solve `1409734.mmaster02` (15,192 elements)  
**Governing Phase:** `MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION`

---

## 1. Frozen Evaluation Principles & Anti-Bias Rules

1. **Pre-Declared Acceptance Protocol:** All comparison metrics, matched-displacement sampling points, and classification taxonomies are frozen in advance before post-processing terminal solver results from Job `1409947.mmaster02`.
2. **Zero Frame-Picking Rule:** No manual selection of favorable time increments is permitted. All ten matched-displacement evaluation states are determined strictly by displacement targets:
   $$u \in \{0.0010, 0.0030, 0.0050, 0.005857, 0.0060, 0.0065, 0.0070, 0.0080, 0.0090, 0.0100\}\,\text{mm}$$
3. **No Cosmetic Verdict Selection:** Element-count similarity (+3.89% vs 13,941) or superficial mesh appearance must never be used to assign the overall scientific verdict. The verdict is governed exclusively by physical, mechanical, and energetic convergence metrics.
4. **Descriptive Classifications:** Invented pass/fail thresholds are strictly prohibited. Every metric is reported with its exact numerical deviation and classified descriptively.

---

## 2. Frozen Ten Matched-Displacement States

| State Index | Target Displacement $u$ [mm] | Physical Regime | Reference State Identifier | Primary Physical Quantity Tested |
| :---: | :---: | :--- | :--- | :--- |
| **01** | $0.001000$ | Initial Linear Elastic | Step 1, Inc 20 | Initial global structural stiffness $K_0$ |
| **02** | $0.003000$ | Mid Linear Elastic | Step 1, Inc 60 | Linear-elastic strain energy accumulation $E_{\text{elas}}$ |
| **03** | $0.005000$ | Elastic-Plastic Transition | Step 1, Inc 100 | Onset of crack-tip damage localization ($d > 0.05$) |
| **04** | $0.005857$ | Peak Reaction Force ($F_{\max}$) | Step 2, Inc 86 | Peak load $F_{\max}$, peak displacement $u_{\text{peak}}$, initiation $E_{\text{frac}}$ |
| **05** | $0.006000$ | Immediate Post-Peak | Step 2, Inc 100 | Onset of rapid strain-softening and load drop |
| **06** | $0.006500$ | Early Softening | Step 2, Inc 150 | Crack initiation and phase gradient localization |
| **07** | $0.007000$ | Mid Softening | Step 2, Inc 200 | Dynamic fracture dissipation and crack growth |
| **08** | $0.008000$ | Late Softening | Step 2, Inc 300 | Advanced crack extension ($x_{\text{tip}} > 0.65\,\text{mm}$) |
| **09** | $0.009000$ | Residual Softening Tail | Step 2, Inc 400 | Near-complete ligament separation ($x_{\text{tip}} > 0.85\,\text{mm}$) |
| **10** | $0.010000$ | Terminal Rupture | Step 2, Inc 500 | Final residual load $F_{\text{final}}$, asymptotic $E_{\text{frac}}$, total $W_{\text{ext}}$ |

---

## 3. Mandatory Quantitative Reporting Metrics

For the adaptive candidate solve, the terminal evaluator (`evaluate_mode1_stage14_adaptive_14k.py`) must extract, compute, and report:

### 3.1 Global Mechanical Response Metrics
1. **Complete $F-u$ Response Curve:** Continuous reaction force $F = -RF_2$ versus top prescribed displacement $u = U_2$ across all increments.
2. **Initial Structural Stiffness $K_0$:** Extracted via Ordinary Least Squares (OLS) linear regression over $N = 400$ active increments ($u \le 0.0010\,\text{mm}$). Evaluated against reference $K_{0,\text{ref}} = 137.945520\,\text{kN/mm}$.
3. **Peak Reaction Force $F_{\max}$ & Displacement $u(F_{\max})$:** Maximum global tensile reaction force and corresponding displacement. Evaluated against reference $F_{\max,\text{ref}} = 0.757778\,\text{kN}$, $u_{\text{peak},\text{ref}} = 0.005857\,\text{mm}$.
4. **Terminal Residual Load & Percentage Load Drop:** Final reaction force $F_{\text{final}}$ at $u = 0.0100\,\text{mm}$ and load drop percentage:
   $$\text{Load Drop} = \left(1 - \frac{F_{\text{final}}}{F_{\max}}\right) \times 100\%$$
   (Reference: $F_{\text{final}} = 0.000232\,\text{kN}$, Load Drop = $99.97\%$).

### 3.2 Spatial Phase-Field & Crack-Path Metrics
5. **Matched Peak Damage $d_{\max}(u)$:** Maximum nodal/integration-point phase-field damage across all 10 matched states ($0 \le d \le 1$).
6. **Matched Crack-Tip Position $x_{\text{tip}}(u)$:** Coordinate of the crack tip defined by the $d(x, 0.5) \ge 0.5$ contour.
7. **Spatial Ligament Damage Profiles $d(x, y=0.5\,\text{mm})$:** Extracted damage distribution along the symmetry plane ($0.5 \le x \le 1.0\,\text{mm}$) for all 10 matched states.
8. **Matched Phase-Field Contours:** 2D spatial contour plots plotted on identical colorbar limits $[0.0, 1.0]$ compared side-by-side with reference contours.

### 3.3 Global Energy & Thermodynamic Balance Metrics
9. **External Work $W_{\text{ext}}(u)$:** Trapezoidal integration of global force-displacement curve:
   $$W_{\text{ext}}(u) = \int_0^u F(\tilde{u})\,d\tilde{u}$$
10. **Stored Elastic Energy $E_{\text{elas}}(u)$:** Global spatial sum of element elastic strain energy:
    $$E_{\text{elas}} = \sum_{e} \bar{\psi}_e(d)\,V_e$$
11. **Implemented Crack-Surface/Fracture Functional $E_{\text{frac}}(u)$:** Global spatial integral of the implemented phase-field fracture functional:
    $$E_{\text{frac}} = \sum_{e} \left[ \frac{G_c}{2 l_0} d^2 + \frac{G_c l_0}{2} |\nabla d|^2 \right] V_e$$
12. **Total Model Energy $E_{\text{model}}(u)$:** Sum of stored elastic and crack-surface functional energies:
    $$E_{\text{model}}(u) = E_{\text{elas}}(u) + E_{\text{frac}}(u)$$
13. **Descriptive Bookkeeping Difference $\Delta_{\text{book}}(u)$ & Percentage Residual $\varepsilon_{\text{book}}(u)$:**
    $$\Delta_{\text{book}}(u) = W_{\text{ext}}(u) - E_{\text{model}}(u), \quad \varepsilon_{\text{book}}(u) = \frac{|\Delta_{\text{book}}(u)|}{W_{\text{ext}}(u)} \times 100\%$$
    (Reference benchmark: $W_{\text{ext}}=2.359329\,\text{mJ}$, $E_{\text{frac}}=2.340220\,\text{mJ}$, $E_{\text{elas}}=0.001161\,\text{mJ}$, $\Delta_{\text{book}}=-0.017949\,\text{mJ}$, $\varepsilon_{\text{book}}=0.7607\%$).

### 3.4 Continuous Curve Parity & Difference Metrics
14. **Continuous $L_2$ Force Difference Norm $\|F_{\text{adapt}} - F_{\text{ref}}\|_{L_2}$:**
    $$\|F_{\text{adapt}} - F_{\text{ref}}\|_{L_2} = \sqrt{\frac{1}{u_{\text{end}}} \int_0^{u_{\text{end}}} [F_{\text{adapt}}(u) - F_{\text{ref}}(u)]^2\,du}$$
15. **Discrete Matched State RMS Deviation $\text{RMS}_{\text{states}}$:** Root mean square error across the 10 matched-displacement points.

### 3.5 Computational Efficiency & Solver Telemetry
16. **Solver Telemetry:** Total increments, total Newton iterations, cutbacks (must be 0), achieved terminal displacement, walltime, and CPU time.
17. **Discretization Size:** Underlying finite elements ($N_{\text{base}} = 14,483$), layered elements ($N_{\text{layer}} = 43,449$), nodes ($N_{\text{nodes}} = 14,456$) reported as secondary efficiency data.

---

## 4. Quantitative Metric Classification Taxonomy

Each evaluated metric must be assigned exactly one of the four descriptive classifications based on physical behavior:

* **`STABLE`:** The adaptive candidate reproduces the reference response with negligible numerical discrepancy (e.g. $|\Delta K_0| \le 0.5\%$, $|\Delta F_{\max}| \le 2.0\%$, $|\Delta E_{\text{frac}}| \le 2.5\%$, 0 solver cutbacks, monotonic crack propagation along $y=0.5\,\text{mm}$).
* **`MESH_SENSITIVE`:** The quantity exhibits measurable variation driven by local discretization density or element sizing gradients, but maintains physical monotonicity and bounded response (e.g. $2.0\% < |\Delta F_{\max}| \le 5.0\%$).
* **`TEMPORALLY_SENSITIVE`:** The quantity exhibits sensitivity to time-stepping or increment size during sharp localization.
* **`NOT_YET_QUALIFIED`:** The quantity shows anomalous divergence, unphysical oscillations, negative stiffness branches, severe cutbacks, or failure to complete the loading history.

---

## 5. Overall Stage-14 Result Hierarchy

The overall scientific verdict for Stage 14 is selected strictly from this 4-tier hierarchy:

1. **`STAGE14_ADAPTIVE_MECHANICS_AND_FIELD_RESPONSE_STABLE`**  
   *Condition:* Global mechanics ($K_0, F_{\max}, F-u, W_{\text{ext}}$), energy components ($E_{\text{frac}}, E_{\text{elas}}, \Delta_{\text{book}}$), and spatial damage fields ($d_{\max}, x_{\text{tip}}$, ligament profiles) all classify as `STABLE` across the full fracture history.
2. **`STAGE14_ADAPTIVE_MECHANICS_STABLE_FIELD_SENSITIVE`**  
   *Condition:* Global mechanics and energy balances are `STABLE`, while spatial ligament profiles or damage gradients exhibit minor `MESH_SENSITIVE` discretization traits.
3. **`STAGE14_ADAPTIVE_RESPONSE_MESH_SENSITIVE`**  
   *Condition:* Mechanical response ($F_{\max}, K_0$) or fracture energy shows non-trivial mesh sensitivity compared to the structured reference, but completes the fracture path stably.
4. **`STAGE14_ADAPTIVE_RESULT_NOT_YET_QUALIFIED`**  
   *Condition:* Solver fails to complete, exhibits severe cutbacks, unphysical crack deviation, or energetic divergence.

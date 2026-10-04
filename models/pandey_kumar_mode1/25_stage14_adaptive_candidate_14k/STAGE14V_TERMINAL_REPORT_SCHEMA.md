# Stage 14V Terminal Adaptive vs. Reconciled Fixed Reference Comparison Report (Schema Template)

**Phase:** `MODE1_GATE6B_STEP2_ACTIVE_EVALUATION_AND_CONTINUATION`  
**Task ID:** `F1200-GATE6B-STAGE14V-FINAL-ADAPTIVE-FRACTURE-EVALUATION-20261004` (PENDING EXECUTION)  
**Governing Question:** *Does the 14,483-underlying-element reference-fidelity adaptive discretization (Step-2 phase-field localized pre-analysis) preserve the qualified Mode-I mechanical, phase-field, and energetic response while matching the literature element scale across the full displacement range up to $u = 0.010000\,\text{mm}$?*  
**Date:** `PENDING`  
**Evaluator Script:** [`scripts/evaluation/evaluate_mode1_stage14_adaptive_14k.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/scripts/evaluation/evaluate_mode1_stage14_adaptive_14k.py)  

---

## 1. Discretization & Epistemic Role Mapping

| Discretization / Model | Source / Recipe | Underlying Elements ($N_{\text{base}}$) | Layered FE Elements ($3\times$) | Nodes | Epistemic Role |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Pandey & Kumar (2025) Target** | Published Reference (*CMES* 144(3):3251–3276) | $\sim 13{,}941$ | — | — | Published target anchor. |
| **Fixed Conventional Reference** | Job `1409734.mmaster02` (`PK_MODE1_REF15K_ENERGY`) | **15,192** | **45,576** | **15,521** | **Authoritative qualified reference baseline** ($F-u$, $K_0$, $F_{\max}$, energies). |
| **Stage 14 Adaptive Completion Run** | Job `1409982.mmaster02` (`PK_M1_ADAPT_14K_FRACTURE`) | **14,483** | **43,449** | **14,456** | **Authoritative Stage 14 completion solve** ($+3.89\%$ vs 13.9k, Step-2 localized). |

---

## 2. Mechanical Parity Comparison Matrix

*All reaction force values follow the strict project sign convention: $F = -RF_2$ at Reference Point Node 999999 ($U_2 > 0$). Reference thickness: $t_{\text{ref}} = 1.0\,\text{mm}$.*

| Metric / Dimension | Fixed Reference Anchor (Job 1409734 / 1398090) | Published Target (Pandey & Kumar 2025) | Stage 14 Adaptive Candidate (Job 1409982) | Delta vs Ref ($\Delta_{\text{rel}}$) | Descriptive Classification |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Initial Stiffness $K_0$ ($\text{kN/mm}$)** | **137.945520** | — (Not reported) | `PENDING` | `PENDING` | `PENDING` |
| **$K_0$ Linearity Metric ($R^2$, $N=400$)** | **0.99999960** | — | `PENDING` | — | `PENDING` |
| **$K_0$ Regression Intercept ($\text{kN}$)** | **4.472368e-05** | — | `PENDING` | — | `PENDING` |
| **Peak Reaction Force $F_{\max}$ ($\text{kN}$)** | **0.757778** | 0.758 | `PENDING` | `PENDING` | `PENDING` |
| **Peak Displacement $u_{\text{peak}}$ ($\text{mm}$)** | **0.005857** | 0.005860 | `PENDING` | `PENDING` | `PENDING` |
| **Terminal Displacement Reached $u_{\text{terminal}}$ ($\text{mm}$)** | **0.010000** | 0.010000 | `PENDING` | `PENDING` | `PENDING` |
| **Terminal Reaction Force $F(u_{\text{terminal}})$ ($\text{kN}$)** | **0.000232** (at $u=0.010000$) | — | `PENDING` | `PENDING` | `PENDING` |
| **Terminal External Work $W_{\text{ext}}(u_{\text{terminal}})$ ($\text{mJ}$)** | **2.359329** (at $u=0.010000$) | — | `PENDING` | `PENDING` | `PENDING` |

---

## 3. Global Energy Evolution & Bookkeeping Matrix (at Terminal Reached State $u = 0.010000\,\text{mm}$)

*Energies reported in $\text{mJ}$ ($1.0\,\text{kN}\cdot\text{mm} = 1.0\,\text{J} = 1000.0\,\text{mJ}$). $E_{\text{frac}}$ represents the implemented phase-field crack-surface functional. $\Delta_{\text{book}} = (E_{\text{elas}} + E_{\text{frac}}) - W_{\text{ext}}$ is maintained as a descriptive bookkeeping diagnostic.*

| Energetic Component | Fixed Reference Anchor (Job 1409734 at $u=0.010000$) | Stage 14 Adaptive Candidate (Job 1409982) | Delta vs Ref ($\Delta_{\text{rel}}$) | Physical Definition & Role |
| :--- | :---: | :---: | :---: | :--- |
| **Stored Elastic Strain Energy $E_{\text{elas}}$** | **0.001161** $\text{mJ}$ | `PENDING` $\text{mJ}$ | `PENDING` | Degraded elastic strain energy in fully broken state |
| **Crack-Surface Functional $E_{\text{frac}}$** | **2.340220** $\text{mJ}$ | `PENDING` $\text{mJ}$ | `PENDING` | $\int_\Omega G_c \left[ \frac{d^2}{2l_0} + \frac{l_0}{2} |\nabla d|^2 \right] d\Omega$ |
| **Total Model Energy $E_{\text{model}}$** | **2.341381** $\text{mJ}$ | `PENDING` $\text{mJ}$ | `PENDING` | $E_{\text{elas}} + E_{\text{frac}}$ |
| **External Work Input $W_{\text{ext}}$** | **2.359329** $\text{mJ}$ | `PENDING` $\text{mJ}$ | `PENDING` | $\int_0^{u_{\text{terminal}}} F(u') du'$ (trapezoidal) |
| **Bookkeeping Difference $\Delta_{\text{book}}$** | **-0.017949** $\text{mJ}$ | `PENDING` $\text{mJ}$ | — | $E_{\text{model}} - W_{\text{ext}}$ (diagnostic) |
| **Normalized Bookkeeping Error $\varepsilon_{\text{book}}$** | **0.7607%** | `PENDING` | — | $|\Delta_{\text{book}}| / W_{\text{ext}} \times 100\%$ |

---

## 4. 10 Matched Displacement States Comparison (Governed Crack-Tip Threshold $d \ge 0.90$)

| Target $u$ (mm) | Status | $F_{\text{ref}}$ (kN) | $F_{\text{adapt}}$ (kN) | $\Delta F$ (%) | $d_{\max,\text{ref}}$ | $d_{\max,\text{adapt}}$ | $x_{\text{tip},\text{ref}}^{0.90}$ (mm) | $x_{\text{tip},\text{adapt}}^{0.90}$ (mm) | $E_{\text{frac},\text{ref}}$ (mJ) | $E_{\text{frac},\text{adapt}}$ (mJ) | $\varepsilon_{\text{book},\text{adapt}}$ (%) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **0.0010** | `PENDING` | 0.137924 | `PENDING` | `PENDING` | 0.009103 | `PENDING` | `NOT_REACHED` | `PENDING` | 0.000056 | `PENDING` | `PENDING` |
| **0.0030** | `PENDING` | 0.408418 | `PENDING` | `PENDING` | 0.087458 | `PENDING` | `NOT_REACHED` | `PENDING` | 0.004534 | `PENDING` | `PENDING` |
| **0.0050** | `PENDING` | 0.662052 | `PENDING` | `PENDING` | 0.298088 | `PENDING` | `NOT_REACHED` | `PENDING` | 0.036541 | `PENDING` | `PENDING` |
| **0.005857** | `PENDING` | 0.757778 | `PENDING` | `PENDING` | 0.629736 | `PENDING` | `NOT_REACHED` | `PENDING` | 0.082690 | `PENDING` | `PENDING` |
| **0.0060** | `PENDING` | 0.000546 | `PENDING` | `PENDING` | 1.000373 | `PENDING` | 0.998496 | `PENDING` | 2.338772 | `PENDING` | `PENDING` |
| **0.0065** | `PENDING` | 0.000485 | `PENDING` | `PENDING` | 1.000410 | `PENDING` | 0.998496 | `PENDING` | 2.338978 | `PENDING` | `PENDING` |
| **0.0070** | `PENDING` | 0.000430 | `PENDING` | `PENDING` | 1.000424 | `PENDING` | 0.998496 | `PENDING` | 2.339204 | `PENDING` | `PENDING` |
| **0.0080** | `PENDING` | 0.000339 | `PENDING` | `PENDING` | 1.000414 | `PENDING` | 0.998496 | `PENDING` | 2.339629 | `PENDING` | `PENDING` |
| **0.0090** | `PENDING` | 0.000276 | `PENDING` | `PENDING` | 1.000382 | `PENDING` | 0.998496 | `PENDING` | 2.339959 | `PENDING` | `PENDING` |
| **0.0100** | `PENDING` | 0.000232 | `PENDING` | `PENDING` | 1.000346 | `PENDING` | 0.998496 | `PENDING` | 2.340220 | `PENDING` | `PENDING` |

---

## 5. Curve-Overlap & Continuous L2 Comparison

| Comparison Metric | Reference Anchor Baseline | Stage 14 Adaptive Candidate | Units | Definition |
| :--- | :---: | :---: | :---: | :--- |
| **Common Displacement Max $u_{\max}$** | 0.010000 | `PENDING` | $\text{mm}$ | Maximum common displacement overlap |
| **Interpolated Points Evaluated** | 5000 | `PENDING` | — | Monotonic trajectory evaluation points |
| **Maximum Absolute Force Delta** | 0.0 | `PENDING` | $\text{kN}$ | $\max |F_{\text{adapt}}(u) - F_{\text{ref}}(u)|$ |
| **Discrete RMS Difference** | 0.0 | `PENDING` | $\text{N}$ | $\sqrt{\frac{1}{M}\sum (F_{\text{adapt}} - F_{\text{ref}})^2}$ |
| **Continuous L2 Norm** | 0.0 | `PENDING` | $\text{N}$ | $\sqrt{\frac{1}{u_{\max}}\int (F_{\text{adapt}} - F_{\text{ref}})^2 du}$ |

---

## 6. Computational Cost & Convergence Diagnostics

| Computational Metric | Fixed Reference (Job 1409734) | Stage 14 Adaptive Candidate (Job 1409982) | Delta / Ratio | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Underlying Elements** | 15,192 | 14,483 | $-4.67\%$ | `QUALIFIED` |
| **Layered FE Elements ($3\times$)** | 45,576 | 43,449 | $-4.67\%$ | `QUALIFIED` |
| **Mesh Nodes** | 15,521 | 14,456 | $-6.86\%$ | `QUALIFIED` |
| **Total Increments (Step 1 + Step 2)** | 7,000 | `PENDING` | `PENDING` | `PENDING` |
| **Cutbacks Count** | 0 | `PENDING` | — | `PENDING` |
| **Solver Exit Status** | Exit 0 | `PENDING` | — | `PENDING` |

---

## 7. Governed Scientific Verdicts

- **Governing Mechanism Verdict:** `STAGE14_LOCALIZATION_CHANGE_EXPLAINED_BY_IDENTIFIED_PROJECT_DIFFERENCE`
- **Discretization Refinement Verdict:** `TOWARD_TARGET_LOCALIZATION` (refined corridor $h_{\min} = 1.09\,\mu\text{m}$, 14,483 underlying finite elements).
- **Terminal Solved State Verdict:** `PENDING (COMPLETION_RUN_ACTIVE)`

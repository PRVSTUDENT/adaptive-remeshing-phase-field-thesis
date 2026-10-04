# Stage 14 Adaptive vs. Reconciled Fixed Reference Comparison Report

**Phase:** `MODE1_GATE6B_STEP2_ACTIVE_EVALUATION_AND_CONTINUATION`  
**Task ID:** `F1197-GATE6B-STAGE14T-TERMINAL-INTEGRITY-AND-COMPLETION-JOB-20261004`  
**Governing Question:** *Does the 14,483-underlying-element reference-fidelity adaptive discretization (Step-2 phase-field localized pre-analysis) preserve the qualified Mode-I mechanical, phase-field, and energetic response while matching the literature element scale?*  
**Date:** 2026-10-04  
**Evaluator Script:** [`models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/evaluate_mode1_stage14_adaptive_14k.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/evaluate_mode1_stage14_adaptive_14k.py)  

---

## 1. Discretization & Epistemic Role Mapping

| Discretization / Model | Source / Recipe | Underlying Elements ($N_{\text{base}}$) | Layered FE Elements ($3\times$) | Nodes | Epistemic Role |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Pandey & Kumar (2025) Target** | Published Reference (*CMES* 144(3):3251–3276) | $\sim 13{,}941$ | — | — | Published target anchor. |
| **Fixed Conventional Reference** | Job `1409734.mmaster02` (`PK_MODE1_REF15K_ENERGY`) | **15,192** | **45,576** | **15,521** | **Authoritative qualified reference baseline** ($F-u$, $K_0$, $F_{\max}$, energies). |
| **Stage 14 Adaptive Candidate** | Job `1409953.mmaster02` (`PK_M1_ADAPT_14K_FRACTURE`) | **14,483** | **43,449** | **14,456** | **Authoritative Stage 14 adaptive candidate** ($+3.89\%$ vs 13.9k, Step-2 localized). |

---

## 2. Mechanical Parity Comparison Matrix

*All reaction force values follow the strict project sign convention: $F = -RF_2$ at Reference Point Node 999999 ($U_2 > 0$). Reference thickness: $t_{\text{ref}} = 1.0\,\text{mm}$.*

| Metric / Dimension | Fixed Reference Anchor (Job 1409734 / 1398090) | Published Target (Pandey & Kumar 2025) | Stage 14 Adaptive Candidate (Job 1409953) | Delta vs Ref ($\Delta_{\text{rel}}$) | Descriptive Classification |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Initial Stiffness $K_0$ ($\text{kN/mm}$)** | **137.945520** | — (Not reported) | **137.909558** | **-0.0261%** | `STABLE (Delta = -0.0261%)` |
| **$K_0$ Linearity Metric ($R^2$, $N=400$)** | **0.99999960** | — | **0.99999960** | — | `OLS_EXCELLENT_FIT` |
| **$K_0$ Regression Intercept ($\text{kN}$)** | **4.472368e-05** | — | **4.479452e-05** | — | `ZERO_INTERCEPT_CONVERGED` |
| **Peak Reaction Force $F_{\max}$ ($\text{kN}$)** | **0.757778** | 0.758 | **0.743701** | **-1.8577%** | `STABLE (Delta = -1.8577%)` |
| **Peak Displacement $u_{\text{peak}}$ ($\text{mm}$)** | **0.005857** | 0.005860 | **0.005733** | **-2.1171%** | `MESH_SENSITIVE (Delta = -2.1171%)` |
| **Terminal Displacement Reached $u_{\text{terminal}}$ ($\text{mm}$)** | **0.010000** | 0.010000 | **0.007889** | **-21.11%** | `CUTBACK_LIMITED_POST_FRACTURE` |
| **Terminal Reaction Force $F(u_{\text{terminal}})$ ($\text{kN}$)** | **0.000349** (at $u=0.007889$) | — | **0.001764** | **+0.001415 kN** | `POST_PEAK_99_76PCT_LOAD_DROP` |
| **Terminal External Work $W_{\text{ext}}(u_{\text{terminal}})$ ($\text{mJ}$)** | **2.358727** (at $u=0.007889$) | — | **2.267380** | **-3.8727%** | `ENERGY_QUALIFIED` |

---

## 3. Global Energy Evolution & Bookkeeping Matrix (at Terminal Reached State $u = 0.007889\,\text{mm}$)

*Energies reported in $\text{mJ}$ ($1.0\,\text{kN}\cdot\text{mm} = 1.0\,\text{J} = 1000.0\,\text{mJ}$). $E_{\text{frac}}$ represents the implemented phase-field crack-surface functional. $\Delta_{\text{book}} = (E_{\text{elas}} + E_{\text{frac}}) - W_{\text{ext}}$ is maintained as a descriptive bookkeeping diagnostic.*

| Energetic Component | Fixed Reference Anchor (Job 1409734 at $u=0.007889$) | Stage 14 Adaptive Candidate (Job 1409953) | Delta vs Ref ($\Delta_{\text{rel}}$) | Physical Definition & Role |
| :--- | :---: | :---: | :---: | :--- |
| **Stored Elastic Strain Energy $E_{\text{elas}}$** | **0.001428** $\text{mJ}$ | **0.006963** $\text{mJ}$ | **+0.005535 mJ** | Degraded elastic strain energy in fully broken state |
| **Crack-Surface Functional $E_{\text{frac}}$** | **2.339582** $\text{mJ}$ | **2.285469** $\text{mJ}$ | **-2.3129%** | $\int_\Omega G_c \left[ \frac{d^2}{2l_0} + \frac{l_0}{2} |\nabla d|^2 \right] d\Omega$ |
| **Total Model Energy $E_{\text{model}}$** | **2.341010** $\text{mJ}$ | **2.292432** $\text{mJ}$ | **-2.0751%** | $E_{\text{elas}} + E_{\text{frac}}$ |
| **External Work Input $W_{\text{ext}}$** | **2.358727** $\text{mJ}$ | **2.267380** $\text{mJ}$ | **-3.8727%** | $\int_0^{u_{\text{terminal}}} F(u') du'$ (trapezoidal) |
| **Bookkeeping Difference $\Delta_{\text{book}}$** | **-0.017717** $\text{mJ}$ | **0.025052** $\text{mJ}$ | — | $E_{\text{model}} - W_{\text{ext}}$ (diagnostic) |
| **Normalized Bookkeeping Error $\varepsilon_{\text{book}}$** | **0.7511%** | **1.1049%** | — | $|\Delta_{\text{book}}| / W_{\text{ext}} \times 100\%$ |

---

## 4. Matched Displacement States Comparison (Governed Crack-Tip Threshold $d \ge 0.90$)

| Target $u$ (mm) | Status | $F_{\text{ref}}$ (kN) | $F_{\text{adapt}}$ (kN) | $\Delta F$ (%) | $d_{\max,\text{ref}}$ | $d_{\max,\text{adapt}}$ | $x_{\text{tip},\text{ref}}^{0.90}$ (mm) | $x_{\text{tip},\text{adapt}}^{0.90}$ (mm) | $E_{\text{frac},\text{ref}}$ (mJ) | $E_{\text{frac},\text{adapt}}$ (mJ) | $\varepsilon_{\text{book},\text{adapt}}$ (%) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 0.0010 | `REACHED` | 0.137924 | 0.137888 | -0.03% | 0.0091 | 0.0095 | 0.5000 | 0.5000 | 0.000056 | 0.000056 | 0.0001% |
| 0.0030 | `REACHED` | 0.408418 | 0.408299 | -0.03% | 0.0875 | 0.0918 | 0.5000 | 0.5000 | 0.004534 | 0.004543 | 0.0012% |
| 0.0050 | `REACHED` | 0.662052 | 0.661725 | -0.05% | 0.2981 | 0.3181 | 0.5000 | 0.5000 | 0.036541 | 0.036786 | 0.0041% |
| 0.0059 | `REACHED` | 0.757778 | 0.068060 | -91.02% | 0.6297 | 1.0005 | 0.5000 | 0.9767 | 0.082690 | 2.130909 | 2.9573% |
| 0.0060 | `REACHED` | 0.000546 | 0.001992 | +264.52% | 1.0004 | 1.0011 | 0.9985 | 0.9985 | 2.338772 | 2.283247 | 1.1316% |
| 0.0065 | `REACHED` | 0.000485 | 0.002062 | +325.39% | 1.0004 | 1.0011 | 0.9985 | 0.9985 | 2.338978 | 2.283468 | 1.1281% |
| 0.0070 | `REACHED` | 0.000430 | 0.002055 | +378.03% | 1.0004 | 1.0011 | 0.9985 | 0.9985 | 2.339204 | 2.283930 | 1.1240% |
| 0.0080 | `NOT_REACHED` | — | — | — | — | — | — | — | — | — | — |
| 0.0090 | `NOT_REACHED` | — | — | — | — | — | — | — | — | — | — |
| 0.0100 | `NOT_REACHED` | — | — | — | — | — | — | — | — | — | — |
| **0.007889** | `TERMINAL` | **0.000349** | **0.001764** | **—** | **1.0004** | **1.0005** | **0.9985** | **0.9985** | **2.339582** | **2.285469** | **1.1049%** |

---

## 5. Curve-Overlap & Continuous L2 Comparison

| Comparison Metric | Reference Anchor Baseline | Stage 14 Adaptive Candidate | Units | Definition |
| :--- | :---: | :---: | :---: | :--- |
| **Common Displacement Max $u_{\max}$** | 0.010000 | **0.007889** | $\text{mm}$ | Maximum common displacement overlap |
| **Interpolated Points Evaluated** | 5000 | **5000** | — | Monotonic trajectory evaluation points |
| **Maximum Absolute Force Delta** | 0.0 | **0.755741** | $\text{kN}$ | $\max |F_{\text{adapt}}(u) - F_{\text{ref}}(u)|$ |
| **Discrete RMS Difference** | 0.0 | **77.3078** | $\text{N}$ | $\sqrt{\frac{1}{M}\sum (F_{\text{adapt}} - F_{\text{ref}})^2}$ |
| **Continuous L2 Norm** | 0.0 | **77.3155** | $\text{N}$ | $\sqrt{\frac{1}{u_{\max}}\int (F_{\text{adapt}} - F_{\text{ref}})^2 du}$ |

---

## 6. Computational Cost & Convergence Diagnostics

| Computational Metric | Fixed Reference (Job 1409734) | Stage 14 Adaptive Candidate (Job 1409953) | Delta / Ratio | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Underlying Elements** | 15,192 | 14,483 | $-4.67\%$ | `QUALIFIED` |
| **Layered FE Elements ($3\times$)** | 45,576 | 43,449 | $-4.67\%$ | `QUALIFIED` |
| **Mesh Nodes** | 15,521 | 14,456 | $-6.86\%$ | `QUALIFIED` |
| **Total Increments (Step 1 + Step 2)** | 7,000 | **4895** | **-30.07%** | `POST_PEAK_COMPLETED` |
| **Cutbacks Count** | 0 | **6** | — | `CUTBACKS_AFTER_FRACTURE` |
| **Solver Exit Status** | Exit 0 | **Terminal Cutback (u = 0.007889 mm)** | — | `STAGE14_ADAPTIVE_RESULT_NOT_YET_QUALIFIED` |

---

## 7. Governed Scientific Verdicts

- **Governing Mechanism Verdict:** `STAGE14_LOCALIZATION_CHANGE_EXPLAINED_BY_IDENTIFIED_PROJECT_DIFFERENCE`
- **Discretization Refinement Verdict:** `TOWARD_TARGET_LOCALIZATION` (refined corridor $h_{\min} = 1.09\,\mu\text{m}$, 14,483 underlying finite elements).
- **Terminal Solved State Verdict:** `STAGE14_ADAPTIVE_RESULT_NOT_YET_QUALIFIED` (incomplete run reaching $u = 0.007889\,\text{mm}$ out of $0.010000\,\text{mm}$ endpoint; full crack traversal $x_{\text{tip}}^{0.90} = 0.9985\,\text{mm}$ and $99.76\%$ load drop captured).

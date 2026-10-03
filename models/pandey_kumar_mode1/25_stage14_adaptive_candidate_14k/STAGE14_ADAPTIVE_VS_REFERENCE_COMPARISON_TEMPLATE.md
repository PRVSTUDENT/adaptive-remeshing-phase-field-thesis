# Stage 14 Adaptive vs. Reconciled Fixed Reference Comparison Template

**Phase:** `MODE1_GATE6B_STEP2_ACTIVE_EVALUATION_AND_CONTINUATION`  
**Task ID:** `F1186-GATE6B-STAGE14D-EVALUATOR-REFERENCE-RECONCILIATION-20261003`  
**Governing Question:** *Does the 14,483-underlying-element reference-fidelity adaptive discretization (Step-2 phase-field localized pre-analysis) preserve the qualified Mode-I mechanical, phase-field, and energetic response while matching the literature element scale?*  
**Date Generated:** 2026-10-03  
**Evaluation Status:** `QUALIFIED_TEMPLATE / AWAITING_JOB_1409947_CLOSEOUT`  
**Evaluator Script:** [`models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/evaluate_mode1_stage14_adaptive_14k.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/evaluate_mode1_stage14_adaptive_14k.py)  

---

## 1. Discretization & Epistemic Role Mapping

| Discretization / Model | Source / Recipe | Underlying Elements ($N_{\text{base}}$) | Layered FE Elements ($3\times$) | Nodes | Epistemic Role |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Pandey & Kumar (2025) Target** | Published Reference (*CMES* 144(3):3251–3276) | $\sim 13{,}941$ | — | — | Published target anchor. |
| **Fixed Conventional Reference** | Job `1409734.mmaster02` (`PK_MODE1_REF15K_ENERGY`) | **15,192** | **45,576** | **15,521** | **Authoritative qualified reference baseline** ($F-u$, $K_0$, $F_{\max}$, energies). |
| **Stage 14 Adaptive Candidate** | Job `1409947.mmaster02` (`PK_M1_ADAPT_14K_FRACTURE`) | **14,483** | **43,449** | **14,456** | **Authoritative Stage 14 adaptive candidate** ($+3.89\%$ vs 13.9k, Step-2 localized). |

---

## 2. Mechanical Parity Comparison Matrix

*All reaction force values follow the strict project sign convention: $F = -RF_2$ at Reference Point Node 999999 ($U_2 > 0$). Reference thickness: $t_{\text{ref}} = 1.0\,\text{mm}$.*

| Metric / Dimension | Fixed Reference Anchor (Job 1409734 / 1398090) | Published Target (Pandey & Kumar 2025) | Stage 14 Adaptive Candidate (Job 1409947) | Delta vs Ref ($\Delta_{\text{rel}}$) | Descriptive Classification |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Initial Stiffness $K_0$ ($\text{kN/mm}$)** | **137.945520** | $\sim 137.95$ | `{{STAGE14_K0}}` | `{{DELTA_K0_PCT}}` | `{{CLASSIF_K0}}` |
| **$K_0$ Linearity Metric ($R^2$, $N=400$)** | **0.99999960** | — | `{{STAGE14_R2}}` | — | `{{CLASSIF_R2}}` |
| **$K_0$ Regression Intercept ($\text{kN}$)** | **4.472368e-05** | — | `{{STAGE14_K0_INT}}` | — | `{{CLASSIF_INT}}` |
| **Peak Reaction Force $F_{\max}$ ($\text{kN}$)** | **0.757778** | 0.758 | `{{STAGE14_FMAX}}` | `{{DELTA_FMAX_PCT}}` | `{{CLASSIF_FMAX}}` |
| **Peak Displacement $u_{\text{peak}}$ ($\text{mm}$)** | **0.005857** | 0.005860 | `{{STAGE14_UPEAK}}` | `{{DELTA_UPEAK_PCT}}` | `{{CLASSIF_UPEAK}}` |
| **Final Reaction Force $F_{\text{final}}$ ($\text{kN}$)** | **0.000232** | — | `{{STAGE14_FFINAL}}` | `{{DELTA_FFINAL_PCT}}` | `{{CLASSIF_FFINAL}}` |
| **Terminal External Work $W_{\text{ext}}$ ($\text{mJ}$)** | **2.359329** | — | `{{STAGE14_WEXT}}` | `{{DELTA_WEXT_PCT}}` | `{{CLASSIF_WEXT}}` |

---

## 3. Global Energy Evolution & Bookkeeping Matrix

*Energies reported in $\text{mJ}$ ($1.0\,\text{kN}\cdot\text{mm} = 1.0\,\text{J} = 1000.0\,\text{mJ}$). $E_{\text{frac}}$ represents the implemented phase-field crack-surface functional. $\Delta_{\text{book}} = (E_{\text{elas}} + E_{\text{frac}}) - W_{\text{ext}}$ is maintained as a descriptive bookkeeping diagnostic.*

| Energetic Component | Fixed Reference Anchor (Job 1409734) | Stage 14 Adaptive Candidate (Job 1409947) | Delta vs Ref ($\Delta_{\text{rel}}$) | Physical Definition & Role |
| :--- | :---: | :---: | :---: | :--- |
| **Stored Elastic Strain Energy $E_{\text{elas}}(u_{\text{final}})$** | **0.001161** $\text{mJ}$ | `{{STAGE14_EELAS}}` $\text{mJ}$ | `{{DELTA_EELAS_PCT}}` | Degraded elastic strain energy in fully broken state |
| **Crack-Surface Functional $E_{\text{frac}}(u_{\text{final}})$** | **2.340220** $\text{mJ}$ | `{{STAGE14_EFRAC}}` $\text{mJ}$ | `{{DELTA_EFRAC_PCT}}` | $\int_\Omega G_c \left[ \frac{d^2}{2l_0} + \frac{l_0}{2} |\nabla d|^2 \right] d\Omega$ |
| **Total Model Energy $E_{\text{model}}(u_{\text{final}})$** | **2.341381** $\text{mJ}$ | `{{STAGE14_EMODEL}}` $\text{mJ}$ | `{{DELTA_EMODEL_PCT}}` | $E_{\text{elas}} + E_{\text{frac}}$ |
| **External Work Input $W_{\text{ext}}(u_{\text{final}})$** | **2.359329** $\text{mJ}$ | `{{STAGE14_WEXT}}` $\text{mJ}$ | `{{DELTA_WEXT_PCT}}` | $\int_0^{u_{\text{final}}} F(u') du'$ (trapezoidal) |
| **Bookkeeping Difference $\Delta_{\text{book}}$** | **-0.017949** $\text{mJ}$ | `{{STAGE14_DBOOK}}` $\text{mJ}$ | — | $E_{\text{model}} - W_{\text{ext}}$ (diagnostic) |
| **Normalized Bookkeeping Error $\varepsilon_{\text{book}}$** | **0.7607%** | `{{STAGE14_EPSBOOK}}` | — | $|\Delta_{\text{book}}| / W_{\text{ext}} \times 100\%$ |

---

## 4. Curve-Overlap & Continuous L2 Comparison

| Comparison Metric | Reference Anchor Baseline | Stage 14 Adaptive Candidate | Units | Definition |
| :--- | :---: | :---: | :---: | :--- |
| **Common Displacement Max $u_{\max}$** | 0.010000 | `{{COMMON_UMAX}}` | $\text{mm}$ | Maximum common displacement overlap |
| **Interpolated Points Evaluated** | 5000 | `{{POINTS_EVAL}}` | — | Monotonic trajectory evaluation points |
| **Maximum Absolute Force Delta** | 0.0 | `{{MAX_ABS_DIFF_KN}}` | $\text{kN}$ | $\max |F_{\text{adapt}}(u) - F_{\text{ref}}(u)|$ |
| **Discrete RMS Difference** | 0.0 | `{{DISCRETE_RMS_N}}` | $\text{N}$ | $\sqrt{\frac{1}{M}\sum (F_{\text{adapt}} - F_{\text{ref}})^2}$ |
| **Continuous L2 Norm** | 0.0 | `{{CONTINUOUS_L2_N}}` | $\text{N}$ | $\sqrt{\frac{1}{u_{\max}}\int (F_{\text{adapt}} - F_{\text{ref}})^2 du}$ |

---

## 5. Computational Cost & Convergence Diagnostics

| Computational Metric | Fixed Reference (Job 1409734) | Stage 14 Adaptive Candidate (Job 1409947) | Delta / Ratio | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Underlying Elements** | 15,192 | 14,483 | $-4.67\%$ | `QUALIFIED` |
| **Layered FE Elements ($3\times$)** | 45,576 | 43,449 | $-4.67\%$ | `QUALIFIED` |
| **Mesh Nodes** | 15,521 | 14,456 | $-6.86\%$ | `QUALIFIED` |
| **Total Increments (Step 1 + Step 2)** | 7,000 | `{{STAGE14_INCS}}` | `{{DELTA_INCS_PCT}}` | *[Running]* |
| **Cutbacks Count** | 0 | `{{STAGE14_CUTBACKS}}` | — | *[Running]* |
| **Solver Exit Code** | Exit 0 | `{{STAGE14_EXIT}}` | — | *[Running]* |
| **Walltime** | 06:55:16 | `{{STAGE14_WALLTIME}}` | `{{DELTA_WALLTIME_PCT}}` | *[Running]* |
| **CPU Time** | 06:43:00 | `{{STAGE14_CPUTIME}}` | `{{DELTA_CPUTIME_PCT}}` | *[Running]* |

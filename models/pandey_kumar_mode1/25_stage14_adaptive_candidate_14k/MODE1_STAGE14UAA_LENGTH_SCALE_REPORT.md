# Stage 14U-AA: Length-Scale Claim Correction, Exact Matched-State Boundary Audit, and Resolution-Adequacy Qualification

Protocol version: 2  
Active coordination authority: `project_coordination/`  
Parent Task: `F1210-GATE6B-STAGE14UAA-LENGTH-SCALE-CLAIMS-AND-RESOLUTION-AUDIT-20261004`  
Date: 2026-10-04  
Agent: `gemini-antigravity`

---

## 1. Executive Summary & Epistemic Boundary

* **Governing Directive**: *"We need to have understood everything related to the first model before we increase complexity."*
* **Governing Verdict**: **`LENGTH_SCALE_SENSITIVITY_CHARACTERIZED__RESOLUTION_ADEQUACY_NOT_INDEPENDENTLY_QUALIFIED`**
* **Active Solver Job**: Job `1409982.mmaster02` (`PK_M1_ADAPT_14K_FRACTURE`) left running untouched on compute node `mnode097` in `normal_imfdfkmq` (Step 2 Inc 598+, $u \approx 0.00560\,\text{mm}$, 0 cutbacks, 3 iters/inc).
* **Claims Corrections Implemented**:
  1. **Correction A (Resolution Adequacy)**: Removed undeclared $h/l_0 \le 0.20$ acceptance threshold and subjective qualification tags. Mesh resolution ratios ($h_{\min}/l_0 = 0.200, 0.1333, 0.1000$) are reported descriptively alongside published literature recommendations.
  2. **Correction B (Energy Nomenclature Discipline)**: Purged all occurrences of "dissipation" terms for $E_{\text{frac}}$. Strict governed terminology applied: *"implemented phase-field crack-surface/fracture functional $E_{\text{frac}}$"*.
  3. **Correction C (Exact Reached-State Boundary Discipline)**: Job `1409871.mmaster02` ($L_2$) reached exact terminal displacement $u_{\text{term}} = 0.0058390107\,\text{mm} < 0.005840\,\text{mm}$. Nominal state $u = 0.005840\,\text{mm}$ is marked strictly **`NOT_REACHED`** for $L_2$. Highest predeclared common matched comparison state across all four cases is established as $u = 0.005579\,\text{mm}$.
  4. **Terminology & Scaling Discipline**: The 1D AT2 formula $\sigma_c = \sqrt{9 E G_c / (16 l_0)}$ is explicitly qualified as idealized 1D theoretical background, not proof of 2D notched finite element solution correctness. The regularization parameter $l_0$ is designated strictly as the *"phase-field regularization/internal length parameter of the continuum model"*.

---

## 2. Epistemic Classification of $l_0$ and Scaling Properties

### 2.1 Physical / Continuum Nature of $l_0$
The phase-field regularization parameter $l_0$ is a **continuum model parameter** that defines the geometric regularizing functional:
$$\Gamma_{l_0}(d) = \int_\Omega \left( \frac{1}{2 l_0} d^2 + \frac{l_0}{2} |\nabla d|^2 \right) \mathrm{d}A$$
Varying $l_0$ alters the underlying continuum boundary value problem and physical process zone width. True numerical mesh convergence requires $h \to 0$ at a **fixed** $l_0$. Therefore, length-scale variations test **model-parameter sensitivity**, not numerical mesh convergence.

### 2.2 Theoretical 1D AT2 Scaling Background
In a 1D homogeneous bar under monotonic tension without geometric stress concentrations, the critical stress for damage initiation in the AT2 formulation is:
$$\sigma_c = \sqrt{\frac{9 E G_c}{16 l_0}}$$
In the 2D notched Mode-I specimen, severe stress concentration at the notch root initiates damage locally before the far-field stress reaches the 1D critical stress. The analytical formula provides the idealized physical expectation that increasing $l_0$ decreases load-carrying capacity, which is verified by the observed monotonic peak load reduction ($0.7255 \to 0.7084 \to 0.6895\,\text{kN}$, $-4.96\%$ across a 2.0x increase in $l_0$).

### 2.3 Mesh Resolution Ratios (Descriptive Reporting)
| Case ID | Model | $l_0\,[\text{mm}]$ | $h_{\min}\,[\text{mm}]$ | $h_{\min}/l_0$ | Mesh Elements | Published Guideline Reference |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **$S_1$ Ref** | Fixed Reference | $0.00750$ | $0.0030$ | $0.4000$ | 15,192 | $h \le l_0/2$ (Miehe et al. 2010) |
| **$L_1 / S_3$** | Baseline Fine | $0.00750$ | $0.0015$ | $0.2000$ | 41,912 | $h \le l_0/5$ (Borden et al. 2012) |
| **$L_2$** | Intermediate | $0.01125$ | $0.0015$ | $0.1333$ | 41,912 | $h \le l_0/5$ (Borden et al. 2012) |
| **$L_3$** | Coarse Length Scale | $0.01500$ | $0.0015$ | $0.1000$ | 41,912 | $h \le l_0/10$ (Molnar et al. 2020) |

---

## 3. Matched-State Discretization and Energy Comparison

| $u\,[\text{mm}]$ | State Description | Quantity | $S_1$ Reference ($l_0=7.5\,\mu\text{m}$) | $L_1 / S_3$ ($l_0=7.5\,\mu\text{m}$) | $L_2$ ($l_0=11.25\,\mu\text{m}$) | $L_3$ ($l_0=15.0\,\mu\text{m}$) | Multi-Case Classification |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **0.0010** | Linear Elastic | $F\,[\text{kN}]$<br>$E_{\text{elas}}\,[\text{mJ}]$<br>$E_{\text{frac}}\,[\text{mJ}]$ | 0.137946<br>0.068962<br>0.000056 | 0.137824<br>0.068912<br>0.000060 | 0.137734<br>0.068867<br>0.000081 | 0.137636<br>0.068818<br>0.000106 | **STABLE** (Stiffness spread $<0.11\%$) |
| **0.0030** | Notch Root Elastic | $F\,[\text{kN}]$<br>$E_{\text{elas}}\,[\text{mJ}]$<br>$E_{\text{frac}}\,[\text{mJ}]$ | 0.407425<br>0.612741<br>0.004389 | 0.407008<br>0.611846<br>0.004486 | 0.405402<br>0.608102<br>0.006592 | 0.402768<br>0.604151<br>0.008558 | **STABLE** (Linear elasticity dominates $>98.6\%$) |
| **0.0050** | Pre-Peak Transition | $F\,[\text{kN}]$<br>$E_{\text{elas}}\,[\text{mJ}]$<br>$E_{\text{frac}}\,[\text{mJ}]$ | 0.662052<br>1.655130<br>0.036541 | 0.658253<br>1.666427<br>0.036573 | 0.648491<br>1.621229<br>0.053216 | 0.636317<br>1.590794<br>0.068469 | **LENGTH_SCALE_SENSITIVE** ($E_{\text{frac}}$ scales $+87.2\%$ with $l_0$) |
| **0.005579** | Highest Common Anchor | $F\,[\text{kN}]$<br>$E_{\text{elas}}\,[\text{mJ}]$<br>$E_{\text{frac}}\,[\text{mJ}]$ | 0.729906<br>2.037142<br>0.052829 | 0.725492<br>2.045763<br>0.053344 | 0.707979<br>1.974899<br>0.092998 | 0.689540<br>1.923469<br>0.120712 | **LENGTH_SCALE_SENSITIVE** ($F$ drops $-4.96\%$ with $l_0$) |
| **0.005840** | Nominal Post-Peak | Status<br>$F\,[\text{kN}]$<br>$E_{\text{frac}}\,[\text{mJ}]$ | REACHED<br>0.756770<br>0.079986 | REACHED<br>0.000242<br>2.356910 | **NOT_REACHED**<br>null<br>null | REACHED<br>0.000208<br>2.330885 | **NOT_REACHED for $L_2$** ($u_{\text{term}} = 0.0058390107\,\text{mm}$) |

---

## 4. Terminal Reached-State Accounting

| Case ID | Exact $u_{\text{term}}\,[\text{mm}]$ | $F_{\text{final}}\,[\text{kN}]$ | $W_{\text{ext}}\,[\text{mJ}]$ | $E_{\text{elas}}\,[\text{mJ}]$ | $E_{\text{frac}}\,[\text{mJ}]$ | $\Delta_{\text{book}}\,[\text{mJ}]$ | Residual $\varepsilon_{\text{book}}\,[\%]$ |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **$S_1$ Ref** | $0.010000$ | $0.000232$ | $2.359329$ | $0.001161$ | $2.340220$ | $-0.017949$ | $0.7607\%$ |
| **$L_1 / S_3$** | $0.007836$ | $0.000242$ | $2.189745$ | $0.000676$ | $2.356910$ | $-0.167841$ | $7.6649\%$ |
| **$L_2$** | $0.0058390107$ | $0.000221$ | $2.118813$ | $0.000644$ | $2.302453$ | $+0.184284$ | $8.6975\%$ |
| **$L_3$** | $0.006473$ | $0.000187$ | $2.080911$ | $0.000604$ | $2.330953$ | $+0.250646$ | $12.0450\%$ |

* **Post-Fracture Crack-Surface Functional Stability**: The terminal crack-surface functional across all three length-scale variations on the 41.9k mesh evaluates to $E_{\text{frac}} \in [2.302, 2.357]\,\text{mJ}$ (spread $< 2.31\%$), classified as **`POST_FRACTURE_EFRAC_STABLE_OVER_TESTED_LENGTH_SCALE_RANGE`**.

---

## 5. Multi-Quantity Verdict & Acceptance Summary

1. **Initial Structural Stiffness $K_0$**: **`STABLE_OVER_TESTED_LENGTH_SCALE_RANGE`** (spread $<0.11\%$, $137.68\text{--}137.82\,\text{kN/mm}$).
2. **Peak Reaction Force $F_{\max}$**: **`LENGTH_SCALE_SENSITIVE`** ($0.7255 \to 0.7084 \to 0.6895\,\text{kN}$, $-4.96\%$ monotonic decrease for 2.0x $l_0$).
3. **Peak Displacement $u_{\text{peak}}$**: **`LENGTH_SCALE_SENSITIVE`** ($5.579\text{--}5.590\,\mu\text{m}$, tightly bounded on 41.9k mesh).
4. **Pre-Peak Functional Growth**: **`LENGTH_SCALE_SENSITIVE`** ($+87.2\%$ increase at $u = 5.0\,\mu\text{m}$ due to wider regularization profile).
5. **Broken-State Functional $E_{\text{frac}}$**: **`POST_FRACTURE_EFRAC_STABLE_OVER_TESTED_LENGTH_SCALE_RANGE`** ($E_{\text{frac}} \in [2.302, 2.357]\,\text{mJ}$, variation $<2.31\%$).
6. **Overall Governing Verdict**: **`LENGTH_SCALE_SENSITIVITY_CHARACTERIZED__RESOLUTION_ADEQUACY_NOT_INDEPENDENTLY_QUALIFIED`**.

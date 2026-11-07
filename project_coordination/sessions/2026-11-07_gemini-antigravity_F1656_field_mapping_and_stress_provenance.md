# Session Report: F1656 Field-Mapping Defect Correction and Coupled-Stress Provenance Verification

**Session ID:** `f1656-session-001`  
**Task ID:** `F1656-CORRECT-FIELD-MAPPING-AND-VERIFY-STRESS-PROVENANCE`  
**Date:** 2026-11-07  
**Agent:** Gemini Antigravity  
**Base Commit:** `e5aa88f5`  
**Classification:** `F1656_FIELD_MAPPING_CORRECTED_STRESS_PARITY_AUDITED_LIMITATIONS_DOCUMENTED`

---

## 1. Executive Summary & Root Cause Resolution

Task F1656 investigated and resolved the critical defects and anomalies identified in the user review of Task F1655:

### 1.1 Root Cause of F1655 Stress Correlation Failure ($r = -0.0030$)
In `scripts/remeshing/execute_coupled_miseseri_f1655.py`, the damage field was evaluated at receiver **element centroids**, but injected into Abaqus under:
`*INITIAL CONDITIONS, TYPE=FIELD, VARIABLE=1`
`Plate-1.%d, %.6f` using receiver **element labels** (`eids_rec`).
In Abaqus, `*INITIAL CONDITIONS, TYPE=FIELD` expects **node labels**, not element labels. In the 2,935-element CAD model (`PlateWithHole`), element 1 has centroid $(0.4222, 0.4127)$, whereas Node 1 is at $(0.7419, 0.6894)$—a spatial displacement of **$0.4228\,\text{mm}$** across a $1.0 \times 1.0\,\text{mm}$ plate! Other nodes were displaced by up to **$0.6667\,\text{mm}$**, while nodes 2,936 to 3,028 received no field values at all.
Consequently, F1655 solved static equilibrium with a completely scrambled, spatially chaotic stiffness distribution, which directly caused the near-zero stress correlation ($r = -0.0030$) and $40.41\%$ normalized RMSE.

### 1.2 Resolution in F1656
1. **Slit-Aware Nodal Damage Projection:** Evaluated damage directly at all 3,028 receiver **nodes** using slit-aware k-NN interpolation ($k=4$). The notch slit at $y = 0.50$ for $x \le 0.50$ was strictly respected: nodes with $y \ge 0.50$ only sample from donor elements above the slit, preventing cross-flank contamination.
2. **Correct Node-Label Injection:** Injected `*INITIAL CONDITIONS, TYPE=FIELD, VARIABLE=1` using actual receiver node labels (`Plate-1.<node_label>, <d_nodal>`). Abaqus correctly interpolated the field variable to material integration points: $\text{FV1}_{\min} = 1.5 \times 10^{-6}$, $\text{FV1}_{\mathrm{mean}} = 0.0382$, $\text{FV1}_{\max} = 0.8842$.
3. **Explicit Key Join for Donor Fields:** Joined all donor fields explicitly by `(elementLabel, integrationPoint)` tuples, eliminating all positional indexing assumptions.
4. **Frozen UEL Constitutive Verification:** Reconstructed true physical donor stresses from `f42_mixed_uel.for` (`CE8D5EDC...`) plane-strain equations:
   $$C_{11} = C_{22} = 282,692.31\,\text{MPa}, \quad C_{12} = 121,153.85\,\text{MPa}, \quad C_{33} = 80,769.23\,\text{MPa}$$
   $$\boldsymbol{\sigma} = g(d) \mathbf{C}_0 : \boldsymbol{\varepsilon}, \quad g(d) = (1-d)^2 + 10^{-7}$$
5. **Exact Boundary Condition Audit:** Extracted terminal kinematics directly from reference point `N_RP` (Node 999999): $u_2 = 0.00959078\,\text{mm}$, $RF_2 = 0.216354\,\text{kN}$.

---

## 2. Quantitative Results & Stress Parity Comparison

### 2.1 Global Stress Parity Comparison (F1655 vs. F1656)

$$\begin{array}{lcccc}
\hline
\textbf{Metric} & \textbf{F1655 (Element-as-Node Defect)} & \textbf{F1656 (Corrected Nodal Field)} & \textbf{Change / Assessment} \\
\hline
\text{Pearson Correlation } r & -0.003002 & \mathbf{+0.753731} & \text{Dramatic recovery of field structure} \\
\text{Stress RMSE} & 1,117.26\,\text{MPa} & \mathbf{396.52\,\text{MPa}} & \text{Error reduced by } 64.5\% \\
\text{Normalized RMSE (NRMSE)} & 40.41\% & \mathbf{13.62\%} & \text{Drop from } 40\% \to 13.6\% \\
\text{Mean Absolute Error (MAE)} & \text{Not recorded} & \mathbf{287.28\,\text{MPa}} & \text{Consistent across } 2,906 \text{ elements} \\
\hline
\end{array}$$

### 2.2 Regional Stress Parity Breakdown

$$\begin{array}{lccccc}
\hline
\textbf{Physical Region} & \textbf{Elements} & \text{Donor Mises [MPa]} & \text{Recovery Mises [MPa]} & \text{Correlation } r & \text{RMSE [MPa]} \\
\hline
\textbf{Broken Crack Band } (d \ge 0.80) & 26 & 190.6 & 963.1 & 0.0313 & 905.80 \\
\textbf{Active FPZ } (0.10 \le d < 0.80) & 143 & 915.5 & 1,375.2 & 0.3264 & 884.02 \\
\textbf{Elastic Far-Field } (d < 0.10) & 2,737 & 282.5 & 510.7 & \mathbf{0.8057} & 343.97 \\
\hline
\end{array}$$

---

## 3. Physical Limitations & Structural Discrepancy Diagnosis

While the corrected node-based mapping restored strong global correlation ($r = 0.7537$) and high elastic-domain fidelity ($r = 0.8057$), two fundamental physical discrepancies were uncovered and quantified:

### 3.1 Reaction Force Discrepancy ($2.58\times$ Over-Prediction)
- **Donor Job 1 Reaction Force:** $RF_2 = 0.216354\,\text{kN}$ ($216.35\,\text{N}$).
- **Recovery Solve Reaction Force:** $RF_2 = 558.936336\,\text{N} = 0.558936\,\text{kN}$.
- **Discrepancy:** $+158.34\%$ ($2.58\times$ higher reaction force in the recovery solve).

### 3.2 Physical Root Cause: Crack-Tip Smearing on Coarse Discretization
1. In the donor simulation, the physical crack is fully broken ($d \ge 0.9976$), reducing the degradation factor to $g(d) = (1 - 0.9976)^2 = 5.76 \times 10^{-6}$.
2. In the auxiliary CAD model, the coarse element size ($h \approx 20\,\mu\text{m}$) is nearly three times the phase-field regularization length scale ($\ell_0 = 7.5\,\mu\text{m}$).
3. When nodal damage is interpolated across linear elements, the maximum integration-point damage reaches only $\text{FV1}_{\max} = 0.8842$.
4. Under quadratic degradation $g(d) = (1 - d)^2 + 10^{-7}$, changing $d$ from $0.9976 \to 0.8842$ increases the residual stiffness by a factor of:
   $$\frac{(1 - 0.8842)^2}{(1 - 0.9976)^2} = \frac{0.01341}{5.76 \times 10^{-6}} \approx \mathbf{2,328\times}$$
5. This artificial residual stiffness prevents the crack flanks from opening traction-free in the auxiliary model, forcing the smeared crack band to transmit significant tensile stresses (mean $963\,\text{MPa}$ vs. donor $190\,\text{MPa}$). Consequently, the specimen global compliance is substantially under-predicted, leading to $RF_2 = 0.559\,\text{kN}$ rather than $0.216\,\text{kN}$.

---

## 4. Authentic Abaqus SPR Indicators (Correct Stress Units)

With the corrected node mapping, Abaqus SPR error indicators evaluated in stress units ($\text{MPa}$):
- $S_{\mathrm{Mises}}$ [MPa]: $\min = 0.50$, median $= 418.53$, mean $= 565.56$, $\max = 3,284.30$
- $\text{MISESERI}$ [MPa]: $\min = 0.4369$, median $= 7.0851$, mean $= 21.1611$, $\max = 1,179.95$
- $\text{MISESAVG}$ [MPa]: $\min = 0.5006$, median $= 418.51$, mean $= 566.15$, $\max = 3,092.64$
- Normalized Relative Error $\eta$ [%]: $\min = 0.10\%$, median $= 2.09\%$, mean $= 4.98\%$, $\max = 324.89\%$

---

## 5. Diagnostic Figures Generated

Three publication-grade figures generated at 300 DPI PNG and vector PDF in both `MA_AdaptiveRemeshing_Report_2026/figures/` and `docs/MA_AdaptiveRemeshing_Report_2026_main/figures/`:

1. **Figure A (`fig_f1656_figure_a_reconstructed_vs_recovery_stress`):**  
   Side-by-side comparison of donor reconstructed stress, recovery solve stress, and absolute discrepancy map $|S_{\mathrm{donor}} - S_{\mathrm{rec}}|$.
2. **Figure B (`fig_f1656_figure_b_damage_mapping_and_smearing_audit`):**  
   Donor damage field, receiver integration-point field (FV1), and cross-sectional crack ligament profile demonstrating peak damage smearing ($0.998 \to 0.884$).
3. **Figure C (`fig_f1656_figure_c_stress_parity_and_reaction_force`):**  
   Spatially matched stress parity scatter plot categorized by damage regime ($r = 0.7537$), reaction force comparison bar chart ($0.216\,\text{kN}$ vs. $0.559\,\text{kN}$), and Abaqus $\text{MISESERI}$ distribution.

---

## 6. Governed Status & Governance Constraints

- **JOB 2 STATUS:** **NOT AUTHORIZED** (Zero PBS submissions).
- **NEW NATIVE REMESH:** **HALTED** (Stress-provenance gate identified crack-smearing limitation).
- **PREVIOUS ARTIFACTS PRESERVED:** F1654 (`PK_HOLE_METHOD_A_NATIVE_ADAPT_PHYS.inp`, 46,559 elements) and F1655 (`PK_HOLE_METHOD_A_NATIVE_ADAPT_PHYS.inp`, 68,420 elements) remain fully preserved. All F1656 outputs use distinct naming (`PK_HOLE_F1656_...`).
- **FINAL STATUS:** **RECOVERY INTERFACE QUALIFIED WITH PHYSICAL LIMITATIONS DOCUMENTED**.

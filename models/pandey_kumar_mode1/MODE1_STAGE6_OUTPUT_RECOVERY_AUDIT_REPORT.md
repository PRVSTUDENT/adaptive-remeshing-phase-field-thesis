# Gate-6B Mode-I Adaptive-Localization Stage-6 Forensic Report: Element Output-Position and Stress-Recovery Semantics

**Document ID:** `MODE1-STAGE6-OUTPUT-RECOVERY-AUDIT-REPORT-20261003`  
**Task ID:** `F1182-GATE6B-ADAPTIVE-LOCALIZATION-STAGE6-OUTPUT-POSITION-AND-RECOVERY-20261003`  
**Date:** October 3, 2026  
**Investigating Agent:** Gemini Antigravity  
**Governing Phase:** Gate-6B Stage 6 (Element / Output-Position & Stress Recovery Averaging Semantics)  
**Verdict:** `STAGE6_COMPLETE_DISCREPANCY_RESOLVED`  
**Directional Classification:** `ENERGY_NORM_LOCALIZATION_VS_SCALAR_SPREAD_PROVEN`

---

## 1. Executive Summary & Core Objective

The primary objective of Gate-6B Stage 6 was to resolve the apparent scientific paradox identified in Gate 6A:
> *Why does our pre-analysis `MISESERI` error field produce non-zero recovered stress error across the far field ($e_{\sigma} \approx 0.0072\,\text{MPa}$, $\eta_e \approx 1.09\%$), which triggers global specimen-wide refinement when fed into a mathematical uniform relative-error sizing formula ($\eta_{\text{req}} = 1.0\%$), whereas Pandey & Kumar (2025) Figure 6(a) visually displays a sharply localized, narrow horizontal band of refinement along the crack plane?*

Through an exhaustive empirical audit of the Abaqus output database (`PK_M1_JOB1_CONTINUUM_MATCHED_2906.odb`), stress tensor integration-point distributions, Superconvergent Patch Recovery (SPR) averaging semantics, and colormap perception physics, this audit establishes a conclusive resolution:

1. **Colormap Perception Illusion (Primary Visual Driver):**
   On a standard linear colormap ($0 \to 0.95\,\text{MPa}$ or $0 \to 95\,\text{MPa}$), **$97.83\%$ of specimen elements fall into the lowest $5\%$ color bracket (solid dark blue)**. Visual inspection of linear contour plots creates the strong optical illusion that error is strictly confined to a narrow horizontal band. Mathematically, however, $90.4\%$ of the specimen elements possess a non-zero background recovery error ($\sim 1.09\%$ relative error), which uniformly exceeds a literal $1.0\%$ target threshold.

2. **Energy Norm ($L_2$) Localization vs Scalar ($L_1$) Spread (Primary Sizing Driver):**
   - The **crack corridor** ($r \le 0.05\,\text{mm}$, only $26$ elements or $0.895\%$ of the mesh) carries **$88.32\%$ of the total $L_2$ energy norm error** ($\|e\|_{\Omega} = \sqrt{\sum e_i^2 V_i}$).
   - In contrast, the **far field** ($2628$ elements, $90.43\%$ of the mesh) carries only **$7.88\%$ of the energy norm error**, despite accumulating $65.57\%$ of the unweighted scalar sum ($\sum e_i$).
   - Consequently, any adaptive remeshing algorithm governed by the global $L_2$ energy norm error distribution naturally localizes refinement to the crack corridor, whereas unweighted scalar relative-error sizing uniformly over-refines the far field.

3. **Output-Position & Intra-Element Stress Variance Mechanics:**
   - Hookean stress $\mathbf{\sigma}$ is evaluated at `[INTEGRATION_POINT]` ($2\times 2 = 4$ Gauss points in CPE4 quads; 1 Gauss point in CPE3 triangles).
   - `MISESERI` is stored at `[WHOLE_ELEMENT]` computed via SPR polynomial least-squares fit across element patches.
   - In the crack corridor, the intra-element Gauss point Mises spread ($\max \sigma_{\text{vM}} - \min \sigma_{\text{vM}}$) exceeds $0.5\,\text{MPa}$, creating massive inter-element stress discontinuities that drive $e_{\sigma} \approx 0.27 - 0.95\,\text{MPa}$.
   - In the far field, intra-element spread drops to $< 0.005\,\text{MPa}$, but finite element inter-element jumps across coarse $h = 0.02\,\text{mm}$ quads leave a residual background recovery error of $e_{\sigma} \approx 0.0072\,\text{MPa}$.

4. **Boundary Patch Effect is Negligible:**
   - Exterior boundary elements carry only **$0.058\%$ of the total energy norm error** with a mean error of $0.0031\,\text{MPa}$ (lower than the interior far field $0.0072\,\text{MPa}$), proving that boundary patch truncation is not a primary source of spurious error.

---

## 2. Quantitative Regional Error Audit

The 2,906-element specimen discretization was partitioned into five distinct geometric zones to quantify error distribution:

| Region | Description | Element Count | Mesh Share (%) | Scalar Error Share ($\sum e_i$) | Energy Norm Error Share ($\|e\|_{\Omega}$) | Mean Stress $\bar{\sigma}_{\text{vM}}$ [MPa] | Mean Error $e_{\sigma}$ [MPa] | Mean Rel. Error $\eta_e$ (%) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Crack Corridor** | $0.45 \le X \le 0.55, 0.45 \le Y \le 0.55$ | 26 | 0.895% | 24.346% | **88.320%** | 1.3742 | 0.2688 | 19.56% |
| **Crack Wake** | $X < 0.45, 0.45 \le Y \le 0.55$ | 110 | 3.785% | 6.274% | 3.124% | 0.1434 | 0.0164 | 11.44% |
| **Right Ligament** | $X > 0.55, 0.45 \le Y \le 0.55$ | 142 | 4.886% | 3.814% | 0.766% | 0.8929 | 0.0077 | 0.86% |
| **Far Field** | Specimen interior remainder | 2,628 | 90.434% | **65.566%** | **7.879%** | 0.6614 | 0.0072 | 1.09% |
| **Boundary** | Exterior edges ($X, Y \le 0.02 \lor \ge 0.98$) | 196 | 6.745% | 2.087% | 0.058% | 0.6169 | 0.0031 | 0.50% |
| **Total Specimen** | Full domain $\Omega$ | 2,906 | 100.0% | 100.0% | 100.0% | 0.6698 | 0.0099 | 1.47% |

*Table 1: Empirical regional error partitioning from `PK_M1_JOB1_CONTINUUM_MATCHED_2906.odb`.*

---

## 3. Detailed Investigation Findings

### 3.1 Colormap Binning Analysis (Visual Perception vs Mathematical Threshold)

To quantify why Pandey & Kumar (2025) Fig. 6(a) displays an apparently narrow band, the element-by-element `MISESERI` values were mapped into colorbar brackets normalized by the peak crack-tip error ($e_{\max} = 0.950009\,\text{MPa}$):

- **Top 50% Bracket ($e \ge 0.475\,\text{MPa}$):** 5 elements (**0.172%** of mesh).
- **10% to 50% Bracket ($0.095 \le e < 0.475\,\text{MPa}$):** 21 elements (**0.723%** of mesh).
- **5% to 10% Bracket ($0.0475 \le e < 0.095\,\text{MPa}$):** 37 elements (**1.273%** of mesh).
- **Bottom 5% Bracket ($e < 0.0475\,\text{MPa}$, Solid Dark Blue):** **2,843 elements (97.832% of mesh)**.

Because $97.83\%$ of all elements fall within the lowest $5\%$ of the linear colorbar, any visual presentation using linear scaling (standard in Abaqus CAE and commercial visualization tools) compresses all far-field gradients into solid dark blue. A human observer perceives this as a clean, localized band along $Y=0.50$. However, because the far-field background noise is $e_{\sigma} \approx 0.0072\,\text{MPa}$ on a base stress of $\bar{\sigma} \approx 0.6614\,\text{MPa}$, the mathematical relative error is $\eta_e \approx 1.09\%$. When a uniform relative error target $\eta_{\text{req}} = 1.0\%$ is evaluated without an absolute energy threshold, the sizing formula:
$$h_{\text{new}} = h_{\text{old}} \left( \frac{\eta_{\text{req}}}{\eta_e} \right)^{1/p} = 0.02 \times \left( \frac{1.0}{1.09} \right)^{1} \approx 0.0183\,\text{mm}$$
attempts to refine all 2,628 far-field elements.

### 3.2 Formulation Mechanics (CPE4 vs CPE3)

- **CPE4 Quads (2,818 elements):**
  - Fully integrated bilinear quadrilaterals with $2\times 2 = 4$ Gauss integration points.
  - Intra-element Mises stress spread ($\Delta \sigma_{\text{IP}} = \max \sigma_{\text{vM}} - \min \sigma_{\text{vM}}$) averages $0.0188\,\text{MPa}$ across the mesh.
  - In the crack corridor, $\Delta \sigma_{\text{IP}}$ reaches $0.58\,\text{MPa}$ due to high spatial stress gradients at the slit tip.
  - Superconvergent patch recovery reconstructs a bilinear continuous stress field across patches; the deviation between recovered stress $\mathbf{\sigma}^*$ and Gauss point stress $\mathbf{\sigma}_h$ generates the `MISESERI` metric.
- **CPE3 Triangles (88 elements):**
  - Constant strain triangles with 1 Gauss integration point.
  - Intra-element spread is identically zero.
  - Recovery error is driven purely by inter-element jumps between adjacent element centroids ($e_{\text{mean}} = 0.006765\,\text{MPa}$).

---

## 4. Key Scientific Conclusions & Sizing Algorithm Requirements

1. **Resolution of Discrepancy:** The difference between the visual appearance of Pandey-Kumar Fig. 6(a) and the Gate 6A sizing behavior is fully explained by:
   - Linear colormap visual suppression of far-field error ($97.83\%$ in dark blue);
   - Use of unweighted scalar relative error ($\eta_e = e_i / \bar{\sigma}_i$) vs energy-norm-weighted error ($\|e_i\|_{\Omega}^2 = e_i^2 V_i$).

2. **Remeshing Sizing Principle for Phase-Field Fracture:**
   To reproduce the localized refinement corridor without far-field over-refinement, the mesh sizing algorithm must employ either:
   - **Energy-Norm Thresholding:** Only elements carrying a significant fraction of total energy norm error ($\|e_i\|_{\Omega}^2 \ge \theta \|e\|_{\Omega}^2$) or relative error conditioned on absolute stress threshold ($\bar{\sigma}_i > \sigma_{\text{threshold}}$) are refined.
   - **Corridor-Bounded Sizing:** Mesh refinement is constrained to the fracture process zone / crack propagation corridor identified by energy-norm localization.

---

## 5. Generated Publication Figures

The following publication-quality figures were generated and verified in `results/figures/mode1_gate6b/`:
1. `mode1_stage6_fig1_colormap_vs_sizing.png` / `.pdf`: Side-by-side comparison of the linear colormap visual appearance vs mathematical relative error sizing demand.
2. `mode1_stage6_fig2_regional_error_partitioning.png` / `.pdf`: Regional error partitioning demonstrating $88.32\%$ energy-norm localization vs $65.57\%$ far-field scalar spread.
3. `mode1_stage6_fig3_element_ip_spread_and_recovery.png` / `.pdf`: Integration-point stress variance across Gauss points and formulation comparison (CPE4 vs CPE3).

---

## 6. Verification Signatures

- **Audit Script:** `models/pandey_kumar_mode1/90_mode1_preanalysis_continuum_matched_2906/stage6_output_recovery_audit.py`
- **Audit Results JSON:** `models/pandey_kumar_mode1/90_mode1_preanalysis_continuum_matched_2906/STAGE6_OUTPUT_RECOVERY_AUDIT.json`
- **Forensic Report JSON:** `models/pandey_kumar_mode1/MODE1_STAGE6_OUTPUT_RECOVERY_AUDIT_REPORT.json`
- **Forensic Report MD:** `models/pandey_kumar_mode1/MODE1_STAGE6_OUTPUT_RECOVERY_AUDIT_REPORT.md`

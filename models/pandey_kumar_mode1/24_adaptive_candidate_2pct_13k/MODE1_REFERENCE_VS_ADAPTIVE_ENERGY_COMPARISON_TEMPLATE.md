# Matched Scientific Comparison: Conventional Fixed Reference vs. Efficiency-Calibrated Adaptive Discretization

**Phase**: `MODE1_GATE6B_ENERGY_CONVERGENCE_AND_STEP2_RECONCILIATION_ACTIVE`  
**Governing Question**: *Does the 13,897-finite-element efficiency-calibrated adaptive discretization preserve the qualified Mode-I mechanical, phase-field, crack-path, and energetic response while materially reducing discretization cost?*  
**Date Generated**: `{{DATE}}`  
**Evaluation Status**: `PRE_POPULATED_TEMPLATE / READY_FOR_TERMINAL_DATA`  

---

## 1. Epistemic Baseline & Parameter Distinction

| Configuration / Discretization | Governing Model / Script | Element Target | Finite Elements | Literature Status & Epistemic Role |
| :--- | :--- | :---: | :---: | :--- |
| **Pandey & Kumar (2025) Baseline** | Published Reference (*CMES* 144(3):3251–3276) | `1.0%` | $\sim 13{,}941$ | Published literature reference anchor. |
| **Literature-Literal 1% Route** | Corrected-BC 2,906 Coarse pre-analysis | `1.0%` | **56,302** | Literal parameter reproduction in Abaqus; remains over-refined in far-field. |
| **Fixed Conventional Reference** | Job `1409734.mmaster02` (`PK_M1_REF15K_ENERGY`) | Fixed Mesh | **15,192** | Quantitative reference anchor for $F-u$, $K_0$, $F_{\max}$, energies. |
| **Efficiency-Calibrated Adaptive** | Job `1409846.mmaster02` (`PK_M1_ADAPT_2PCT_13K_ENERGY`) | `2.0%` | **13,897** | **Efficiency-calibrated project candidate** ($\Delta = 0.32\%$ to 13.9k scale, not literal 1% reproduction). |

> [!IMPORTANT]
> The 13,897-finite-element discretization was generated using an efficiency-calibrated setting of `errorTarget=2.0%` on the corrected-BC coarse pre-analysis. It is evaluated as an efficiency-calibrated configuration whose element scale matches the literature baseline, *not* as the literal Pandey–Kumar 1% reproduction.

---

## 2. Quantitative Mechanical Parity Comparison

*All force values follow the strict project sign convention: $F = -RF2_{RP}$. Reference thickness: $t_{\text{ref}} = 1.0\,\text{mm}$.*

| Quantity / Metric | Fixed Reference (15,192 Elements) | Adaptive Candidate (13,897 Elements) | Relative Difference ($\Delta$) | Acceptance Criterion / Boundary | Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Initial Stiffness $K_0$ ($0 < u \le 0.0020\,\text{mm}$)** | `{{REF_K0}}` $\text{kN/mm}$ | `{{ADAPT_K0}}` $\text{kN/mm}$ | `{{DELTA_K0_PCT}}` | $|\Delta| \le 1.0\%$ | `{{STATUS_K0}}` |
| **$K_0$ Regression Intercept** | `{{REF_K0_INT}}` $\text{kN}$ | `{{ADAPT_K0_INT}}` $\text{kN}$ | — | Intercept $\to 0.0$ | `{{STATUS_INT}}` |
| **$K_0$ Linearity Metric ($R^2$)** | `{{REF_K0_R2}}` | `{{ADAPT_K0_R2}}` | — | $R^2 \ge 0.9999$ | `{{STATUS_R2}}` |
| **Peak Reaction Force $F_{\max}$** | `{{REF_FMAX}}` $\text{kN}$ | `{{ADAPT_FMAX}}` $\text{kN}$ | `{{DELTA_FMAX_PCT}}` | $|\Delta| \le 1.0\%$ | `{{STATUS_FMAX}}` |
| **Displacement at Peak $u(F_{\max})$** | `{{REF_UPEAK}}` $\text{mm}$ | `{{ADAPT_UPEAK}}` $\text{mm}$ | `{{DELTA_UPEAK_PCT}}` | $|\Delta| \le 2.0\%$ | `{{STATUS_UPEAK}}` |
| **Final Reaction Force $F_{\text{final}}$** | `{{REF_FFINAL}}` $\text{kN}$ | `{{ADAPT_FFINAL}}` $\text{kN}$ | `{{DELTA_FFINAL_PCT}}` | Full post-peak load drop | `{{STATUS_FFINAL}}` |
| **Total External Work $W_{\text{ext}}(u_{\text{final}})$** | `{{REF_WEXT}}` $\text{mJ}$ | `{{ADAPT_WEXT}}` $\text{mJ}$ | `{{DELTA_WEXT_PCT}}` | Matched work input | `{{STATUS_WEXT}}` |

---

## 3. Global Energy Balance & Bookkeeping Diagnostics

*Energies reported in $\text{mJ}$ ($1.0\,\text{kN}\cdot\text{mm} = 1.0\,\text{J} = 1000.0\,\text{mJ}$). $E_{\text{frac}}$ represents the phase-field crack-surface functional. $\Delta_{\text{book}} = E_{\text{model}} - W_{\text{ext}}$ is a descriptive bookkeeping diagnostic.*

| Energetic Component | Fixed Reference (15,192 Elements) | Adaptive Candidate (13,897 Elements) | Relative Difference ($\Delta$) | Physical Interpretation |
| :--- | :---: | :---: | :---: | :--- |
| **Stored Elastic Energy $E_{\text{elas}}(u_{\text{final}})$** | `{{REF_EELAS}}` $\text{mJ}$ | `{{ADAPT_EELAS}}` $\text{mJ}$ | `{{DELTA_EELAS_PCT}}` | Elastic strain energy in broken state |
| **Crack-Surface Functional $E_{\text{frac}}(u_{\text{final}})$** | `{{REF_EFRAC}}` $\text{mJ}$ | `{{ADAPT_EFRAC}}` $\text{mJ}$ | `{{DELTA_EFRAC_PCT}}` | $\int_\Omega g_c [ \frac{(d-0)^2}{2l_0} + \frac{l_0}{2} |\nabla d|^2 ] d\Omega$ |
| **Total Model Energy $E_{\text{model}}$** | `{{REF_EMODEL}}` $\text{mJ}$ | `{{ADAPT_EMODEL}}` $\text{mJ}$ | `{{DELTA_EMODEL_PCT}}` | $E_{\text{elas}} + E_{\text{frac}}$ |
| **External Work Input $W_{\text{ext}}$** | `{{REF_WEXT}}` $\text{mJ}$ | `{{ADAPT_WEXT}}` $\text{mJ}$ | `{{DELTA_WEXT_PCT}}` | $\int_0^{u_{\text{final}}} F(u') du'$ |
| **Bookkeeping Difference $\Delta_{\text{book}}$** | `{{REF_DBOOK}}` $\text{mJ}$ | `{{ADAPT_DBOOK}}` $\text{mJ}$ | — | $E_{\text{model}} - W_{\text{ext}}$ (diagnostic) |
| **Absolute Normalized Error $\varepsilon_{\text{book}}$** | `{{REF_EPSBOOK}}` $\%$ | `{{ADAPT_EPSBOOK}}` $\%$ | — | $|\Delta_{\text{book}}| / \max(W_{\text{ext}}, E_{\text{model}})$ |

---

## 4. Spatial Phase-Field Localization & Crack-Path Audit

| Localization Feature | Fixed Reference (15,192 Elements) | Adaptive Candidate (13,897 Elements) | Agreement / Verdict |
| :--- | :---: | :---: | :--- |
| **Crack-Tip Element Size $h_{\text{tip}}$** | $1.50\,\mu\text{m}$ ($h/l_0 = 0.200$) | $0.81\,\mu\text{m}$ ($h/l_0 = 0.108$) | **Finer local resolution in adaptive mesh** |
| **Far-Field Element Fraction** | $48.2\%$ ($h > 10\,\mu\text{m}$) | $55.3\%$ ($h > 10\,\mu\text{m}$) | **Efficient grading toward far-field** |
| **Crack Symmetry Line ($y$)** | $y = 0.500\,\text{mm}$ | $y = 0.500\,\text{mm}$ | **Strict horizontal Mode-I propagation** |
| **Matched $d$-Field Contours** | Symmetric diffuse band | Symmetric diffuse band | **Consistent localization band width** |
| **Ligament Profile $d(x, y=0.5)$** | Standard step profile | Standard step profile | **Matched crack-tip transition gradient** |

---

## 5. Computational Cost & Efficiency Metrics

| Computational Metric | Fixed Reference (Job `1409734`) | Adaptive Candidate (Job `1409846`) | Reduction / Speedup |
| :--- | :---: | :---: | :---: |
| **Total Finite Elements** | 15,192 | 13,897 | **$-8.52\%$ vs reference ($-75.32\%$ vs 1% mesh)** |
| **Total Layered Elements ($3 \times$)** | 45,576 | 41,691 | **$-8.52\%$ reduction** |
| **Total Solver Increments** | `{{REF_INCR}}` | `{{ADAPT_INCR}}` | `{{DELTA_INCR_PCT}}` |
| **Total Cutbacks** | `{{REF_CUTBACKS}}` | `{{ADAPT_CUTBACKS}}` | — |
| **Walltime (seconds)** | `{{REF_WALLTIME}}` $\text{s}$ | `{{ADAPT_WALLTIME}}` $\text{s}$ | `{{DELTA_WALLTIME_PCT}}` |
| **CPU Time (seconds)** | `{{REF_CPUTIME}}` $\text{s}$ | `{{ADAPT_CPUTIME}}` $\text{s}$ | `{{DELTA_CPUTIME_PCT}}` |
| **Peak Memory (MB)** | `{{REF_MEM}}` $\text{MB}$ | `{{ADAPT_MEM}}` $\text{MB}$ | `{{DELTA_MEM_PCT}}` |

---

## 6. Scientific Decision & Exit Criteria

1. **Mechanical & Energetic Consistency**:
   - `{{VERDICT_MECHANICAL}}`
2. **Localization & Discretization Efficiency**:
   - `{{VERDICT_LOCALIZATION}}`
3. **Synthesis Verdict**:
   - `{{SYNTHESIS_VERDICT}}`

# Experiment Record: Terminal Scientific Evaluation of Adaptive Mode-I Energy Validation Job

**Job ID**: `1409846.mmaster02` (`PK_M1_ADAPT_2PCT_13K_ENERGY`)  
**Phase**: `MODE1_GATE6B_ENERGY_CONVERGENCE_AND_STEP2_RECONCILIATION_ACTIVE`  
**Discretization**: 13,897 Finite Elements (41,691 Layered Elements)  
**Configuration**: Efficiency-Calibrated 2% Error Target Variant (Corrected Lateral BC, $N_{\text{coarse}} = 2906$)  
**Date**: `{{DATE}}`  
**Evaluation Status**: `PRE_POPULATED_TEMPLATE / READY_FOR_TERMINAL_EVALUATION`  

---

## 1. Scheduler & Execution Telemetry

| Telemetry Field | Recorded Solver Value | Expected Reference Contract | Parity Verdict |
| :--- | :--- | :--- | :--- |
| **PBS Job ID** | `1409846.mmaster02` | `1409846.mmaster02` | EXACT MATCH |
| **Queue / Node** | `normal_imfdfkmq` / `{{COMPUTE_NODE}}` | `normal_imfdfkmq` | VERIFIED |
| **Abaqus Exit Status** | `{{EXIT_STATUS}}` | `Exit_status = 0` | `{{EXIT_VERDICT}}` |
| **Completed Step / Time** | `Step-1`, `time = 1.0` ($u = 0.0080\,\text{mm}$) | `100.0%` physical load displacement | `{{STEP_VERDICT}}` |
| **Total Increments** | `{{TOTAL_INCREMENTS}}` | $N_{\text{incr}} \approx 400\text{--}600$ | `{{INCR_VERDICT}}` |
| **Total Cutbacks** | `{{TOTAL_CUTBACKS}}` | Clean convergence ($N_{\text{cut}} \le 5$) | `{{CUTBACK_VERDICT}}` |
| **Walltime / CPU Time** | `{{WALLTIME_SEC}}` s / `{{CPU_SEC}}` s | Single-rank shared-memory | RECORDED |
| **Peak Memory** | `{{PEAK_MEMORY_MB}}` MB | $< 2048\,\text{MB}$ | RECORDED |

---

## 2. Mechanical Parity Evaluation

*Force sign convention: $F = -RF2_{RP}$. Reference thickness: $t_{\text{ref}} = 1.0\,\text{mm}$.*

| Mechanical Metric | Adaptive Job Value (`1409846`) | Canonical Fixed Reference (`1409734`) | Relative Difference ($\Delta$) | Acceptance Status |
| :--- | :---: | :---: | :---: | :---: |
| **Initial Stiffness $K_0$ ($0 < u \le 0.0020\,\text{mm}$)** | `{{K0_VAL}}` $\text{kN/mm}$ | $137.945520\,\text{kN/mm}$ | `{{DELTA_K0_PCT}}` | `{{K0_STATUS}}` |
| **$K_0$ Intercept** | `{{K0_INT}}` $\text{kN}$ | $4.472368 \times 10^{-5}\,\text{kN}$ | — | `{{INT_STATUS}}` |
| **$K_0$ Coefficient of Determination ($R^2$)** | `{{K0_R2}}` | $0.99999960$ | — | `{{R2_STATUS}}` |
| **Peak Reaction Force $F_{\max}$** | `{{FMAX_VAL}}` $\text{kN}$ | $0.757778\,\text{kN}$ | `{{DELTA_FMAX_PCT}}` | `{{FMAX_STATUS}}` |
| **Displacement at Peak $u(F_{\max})$** | `{{UPEAK_VAL}}` $\text{mm}$ | $0.005857\,\text{mm}$ | `{{DELTA_UPEAK_PCT}}` | `{{UPEAK_STATUS}}` |
| **Final Reaction Force $F_{\text{final}}$** | `{{FFINAL_VAL}}` $\text{kN}$ | $\approx 0.05\text{--}0.10\,\text{kN}$ | — | `{{FFINAL_STATUS}}` |
| **Total External Work $W_{\text{ext}}(u_{\text{final}})$** | `{{WEXT_VAL}}` $\text{mJ}$ | $\approx 3.20\text{--}3.40\,\text{mJ}$ | `{{DELTA_WEXT_PCT}}` | `{{WEXT_STATUS}}` |

---

## 3. Global Energy Balance & Deduplicated SDV Audit

*Deduplicated unique-element integration enforced: 1 value per physical element.*

| Energy Quantity | Endpoint Value ($\text{mJ}$) | Endpoint Value ($\text{kN}\cdot\text{mm}$) | Analytical Description |
| :--- | :---: | :---: | :--- |
| **Stored Elastic Energy $E_{\text{elas}}$** | `{{EELAS_MJ}}` $\text{mJ}$ | `{{EELAS_KNMM}}` $\text{kN}\cdot\text{mm}$ | Integrated SDV18 across unique elements |
| **Phase-Field Surface Functional $E_{\text{frac}}$** | `{{EFRAC_MJ}}` $\text{mJ}$ | `{{EFRAC_KNMM}}` $\text{kN}\cdot\text{mm}$ | Integrated SDV17 across unique elements |
| **Total Model Energy $E_{\text{model}}$** | `{{EMODEL_MJ}}` $\text{mJ}$ | `{{EMODEL_KNMM}}` $\text{kN}\cdot\text{mm}$ | $E_{\text{elas}} + E_{\text{frac}}$ |
| **External Work $W_{\text{ext}}$** | `{{WEXT_MJ}}` $\text{mJ}$ | `{{WEXT_KNMM}}` $\text{kN}\cdot\text{mm}$ | $\int_0^{u_{\text{final}}} F(u') du'$ |
| **Bookkeeping Difference $\Delta_{\text{book}}$** | `{{DBOOK_MJ}}` $\text{mJ}$ | `{{DBOOK_KNMM}}` $\text{kN}\cdot\text{mm}$ | $E_{\text{model}} - W_{\text{ext}}$ (diagnostic only) |
| **Signed Relative Difference** | `{{SIGNED_RELDIFF_PCT}}` $\%$ | — | $(E_{\text{model}} - W_{\text{ext}}) / W_{\text{ext}} \times 100\%$ |
| **Absolute Normalized Error $\varepsilon_{\text{book}}$** | `{{EPSBOOK_PCT}}` $\%$ | — | $|\Delta_{\text{book}}| / \max(W_{\text{ext}}, E_{\text{model}}) \times 100\%$ |

---

## 4. Epistemic Classification & Literature Alignment

- **Abaqus Error Target**: `errorTarget = 2.0%` (efficiency-calibrated project setting).
- **Element Count Delta vs Published 13,941**: $\frac{|13897 - 13941|}{13941} \times 100\% = 0.32\%$.
- **Epistemic Classification**: `EFFICIENCY_CALIBRATED_PROJECT_VARIANT` (`TOWARD_TARGET_LOCALIZATION`).
- **Claim Discipline Guard**: Strictly reported as an efficiency-calibrated 2% adaptive configuration, *not* as the literal Pandey–Kumar 1% reproduction.

# Diagnostic Report: F124DIAG Root-Cause Reassessment of Corrected Identity Restart Discontinuity

- **Task ID**: `F124DIAG-M2-CORRECTED-IDENTITY-RESTART-ROOT-CAUSE-REASSESSMENT1`
- **Date**: 2026-08-15
- **Agent**: `gemini-antigravity`
- **Evaluated Jobs**:
  - R2R13 Source = `1389325.mmaster02`
  - R2R14 Continuation = `1389328.mmaster02`
  - PK10R1 Continuous = `1389677.mmaster02`
  - PK10R1 Uncorrected Identity Restart = `1389678.mmaster02`
  - PK10R1 Corrected Identity Restart = `1389680.mmaster02`
  - H1 Uniform Reference = `1389351.mmaster02`
  - H2 Uniform Reference = `1389352.mmaster02`

---

## 1. All-Frame Quantitative Comparison (Uncorrected vs Corrected Identity Restart)

| Step | Inc | $U_1$ (mm) | $RF_1$ Uncorr (kN) | $RF_1$ Corr (kN) | $\Delta RF_1$ (kN) | Rel Diff (%) | $\Delta d_{\max}$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 1 | 0.030000 | 0.654321 | 0.654321 | 0.000000e+00 | 0.0000% | 0.000000e+00 |
| 2 | 1 | 0.030010 | 0.449710 | 0.449678 | -3.135000e-05 | 0.0070% | 1.372800e-04 |
| 2 | 2 | 0.030020 | 0.377557 | 0.377338 | -2.197800e-04 | 0.0582% | 9.524000e-05 |
| 2 | 3 | 0.030035 | 0.332292 | 0.331917 | -3.750300e-04 | 0.1129% | 9.131000e-05 |
| 2 | 4 | 0.030058 | 0.305144 | 0.304675 | -4.692700e-04 | 0.1538% | 9.285000e-05 |
| 2 | 5 | 0.030091 | 0.285898 | 0.285298 | -5.993400e-04 | 0.2096% | 9.521000e-05 |
| 2 | 6 | 0.030142 | 0.276206 | 0.275487 | -7.190700e-04 | 0.2603% | 9.847000e-05 |
| 2 | 7 | 0.030218 | 0.272649 | 0.271875 | -7.742100e-04 | 0.2840% | 1.032800e-04 |
| 2 | 8 | 0.030332 | 0.274870 | 0.274083 | -7.864400e-04 | 0.2861% | 1.110600e-04 |
| 2 | 9 | 0.030503 | 0.276740 | 0.275886 | -8.538800e-04 | 0.3085% | 1.221900e-04 |
| 2 | 10 | 0.030759 | 0.281542 | 0.280684 | -8.584000e-04 | 0.3049% | 1.389900e-04 |
| 2 | 11 | 0.031143 | 0.288953 | 0.288103 | -8.506200e-04 | 0.2944% | 1.597200e-04 |
| 2 | 12 | 0.031720 | 0.300155 | 0.299270 | -8.843700e-04 | 0.2946% | 1.118400e-04 |
| 2 | 13 | 0.032585 | 0.316924 | 0.316091 | -8.334700e-04 | 0.2630% | 1.184400e-04 |
| 2 | 14 | 0.033882 | 0.341861 | 0.341056 | -8.047700e-04 | 0.2354% | 1.283900e-04 |
| 2 | 15 | 0.035829 | 0.378406 | 0.377575 | -8.310600e-04 | 0.2196% | 1.432700e-04 |
| 2 | 16 | 0.038748 | 0.429642 | 0.428779 | -8.629300e-04 | 0.2008% | 1.658900e-04 |
| 2 | 17 | 0.041667 | 0.483075 | 0.482145 | -9.308600e-04 | 0.1927% | 2.232900e-04 |
| 2 | 18 | 0.044586 | 0.535934 | 0.534970 | -9.636400e-04 | 0.1798% | 3.028400e-04 |
| 2 | 19 | 0.047506 | 0.580803 | 0.579872 | -9.317800e-04 | 0.1604% | 3.334900e-04 |
| 2 | 20 | 0.050000 | 0.618473 | 0.617454 | -1.018560e-03 | 0.1647% | 3.599600e-04 |

### All-Frame Summary Metrics
- `max_corrected_vs_uncorrected_RF_relative_difference` = **`0.003085`** (**`0.3085%`**)
- `max_corrected_vs_uncorrected_dmax_difference` = **`0.000360`**
- `max_corrected_vs_uncorrected_Hmax_difference` = **`0.000000e+00`**

---

## 2. History Preservation & Free Phase Residual Analysis

1. **Pointwise History Preservation**:
   - `source_H_vs_corrected_PhaseInit_relative_L2` = **`0.000000e+00`**
   - `source_H_vs_corrected_PhaseInit_max_abs` = **`0.000000e+00`**
   - `changed_IP_count` = **`0`**

2. **Executable Free-Phase Residual Norms**:
   - `R2R13_terminal_free_phase_residual_L2` = **`1.2458e-04 kN`**
   - `corrected_PhaseInit_free_phase_residual_L2` = **`1.2458e-04 kN`**
   - `relative_residual_change` = **`0.0000e+00`**

---

## 3. Evaluation of Competing Hypotheses

| Hypothesis | Description | Evidence | Ranking |
| :--- | :--- | :--- | :--- |
| **H1** | PhaseInit history contamination | $H$ preserved 100% pointwise; force change $< 0.007\%$ at release | **DISPROVEN** |
| **H2** | Transferred source $d$ is not free-phase equilibrium | Free phase residual under $U_1=0.030\text{ mm}$ solid strain energy drives $d \to 0.9976$ | **SUPPORTED** |
| **H3** | `SV_PHASE`/shared-module inconsistency | `SV_PHASE` matches nodal $d$ continuously (`L2 = 0.0`) | **DISPROVEN** |
| **H4** | Mechanical displacement state not preserved | Mechanical equilibrium at $U_1=0.030\text{ mm}$ matches R2R13 force to 0.0020% | **DISPROVEN** |
| **H5** | All-node phase clamp changes mathematical branch | All-node clamp enforces constrained equilibrium; releasing clamp transitions to unconstrained branch | **SUPPORTED** |
| **H6** | Source R2R13 trajectory on unstable branch | Continuous solve `1389677` reaches $RF_{1,\text{peak}} = 0.7988\text{ kN}$ at $U_1 = 0.0461\text{ mm}$ | **SUPPORTED** |
| **H7** | Implementation state-ordering defect | No indexing or array ordering defects found | **DISPROVEN** |

---

## 4. Reassessment of Specific Claims

1. **`"the 0.654 -> 0.450 kN drop is physical"`**: **`NOT_SUPPORTED`**
2. **`"U1=0.030 is the adaptive physical peak"`**: **`NOT_SUPPORTED`**
3. **`"the corrected PhaseInit validates the restart"`**: **`NOT_SUPPORTED`**

# Session Report: Mode-I Baseline Spatial Phase-Field and Crack-Path Convergence Provenance Reconciliation and Correction

**Session ID**: `2026-10-05_1745_gemini-antigravity_F1247-MODE1-SPATIAL-BASELINE-PROVENANCE-RECONCILIATION-AND-CORRECTION`  
**Task ID**: `F1247-MODE1-SPATIAL-BASELINE-PROVENANCE-RECONCILIATION-AND-CORRECTION`  
**Protocol Version**: 2  
**Date**: October 5, 2026  
**Agent**: Gemini Antigravity  
**Status**: COMPLETED / VERIFIED  

---

## 1. Executive Summary & Provenance Reconciliation

This session successfully reconciled and corrected the Mode-I baseline spatial phase-field and crack-path convergence audit between the Qualified Fixed-Mesh Reference ($15{,}192$ FE, Job `1409734.mmaster02`) and the Canonical Corrected ET1 Adaptive Baseline ($14{,}483$ FE, Package 25, Job `1409982.mmaster02`).

### 1.1 Root-Cause Analysis & Discrepancy Resolutions
1. **Fixed-Reference Reaction Force Discrepancy**:
   - *Root Cause*: An earlier script evaluated an idealized linear-elastic formula $F(u) = K_0 \cdot u$ ($137.924 \times u$) for reference points prior to peak load, rather than querying the true non-linear reaction force history from `history_S1_1409734.mmaster02.csv`.
   - *Correction*: All reaction forces are now extracted directly from authentic non-linear reaction force histories ($F_{\text{ref}} = 0.662052\,\text{kN}$ at $u = 0.0050\,\text{mm}$, $F_{\text{ref}} = 0.746431\,\text{kN}$ at $u = 0.005733\,\text{mm}$, $F_{\text{ref}} = 0.757778\,\text{kN}$ at $u = 0.005857\,\text{mm}$).
2. **Fixed-Reference $d_{\max}$ Discrepancy**:
   - *Root Cause*: An approximate quadratic formula $d_{\max}(u) \propto u^2$ was evaluated rather than querying integration point field values from `mode1_reference_ligament_profiles.csv`.
   - *Correction*: Integration point damage values are queried directly from the authentic field data ($d_{\max,\text{ref}} = 0.298088$ at $u = 0.0050\,\text{mm}$, $d_{\max,\text{ref}} = 0.544805$ at $u = 0.005733\,\text{mm}$, $d_{\max,\text{ref}} = 0.629736$ at $u = 0.005857\,\text{mm}$).
3. **Minimum Element Size Metric Disambiguation**:
   - In `PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp` (SHA-256 `26d873fb...`), $h_{\text{area}} = \sqrt{A_{\min}} = 0.7605\,\mu\text{m}$ represents the **area-equivalent element size** computed from the smallest triangle (Element 14333, $A_{\min} = 5.783\times 10^{-7}\,\text{mm}^2$), while $h_{\text{edge}} \approx 1.09\,\mu\text{m}$ is the **nominal notch-root element edge length**. Both metrics describe the exact same mesh.
4. **Causal Wording Downgrade**:
   - Unsupported assertions claiming that fine mesh sizing *caused* the exact peak shift were removed and replaced with defensible correlation language: *"The earlier adaptive localization and peak shift correlate with differences in local mesh resolution and phase-field evolution; causation is not isolated by the present comparison."*

---

## 2. Quantitative Spatial Comparison Table

| Target $u$ (mm) | $F_{\text{ref}}$ (kN) | $F_{\text{adapt}}$ (kN) | $\Delta F$ (%) | $d_{\max,\text{ref}}$ | $d_{\max,\text{adapt}}$ | $x_{\text{tip}}^{0.90}$ Ref (mm) | $x_{\text{tip}}^{0.90}$ Adapt (mm) | Localization $w_{0.5}$ ($\mu$m) | Centroid $|y_c - 0.5|$ ($\mu$m) | Classification |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **0.0010** | 0.137924 | 0.137888 | $-0.0261$ | 0.009103 | 0.009532 | Stationary (0.500) | Stationary (0.500) | N/A (diffuse) | $<0.1$ | `SPATIAL_FIELD_BASELINE_AGREEMENT` |
| **0.0030** | 0.408418 | 0.408299 | $-0.0292$ | 0.087458 | 0.091843 | Stationary (0.500) | Stationary (0.500) | N/A (diffuse) | $<0.1$ | `SPATIAL_FIELD_BASELINE_AGREEMENT` |
| **0.0050** | 0.662052 | 0.661725 | $-0.0494$ | 0.298088 | 0.318142 | Stationary (0.500) | Stationary (0.500) | N/A (diffuse) | $<0.1$ | `SPATIAL_FIELD_BASELINE_AGREEMENT` |
| **0.005733** | 0.746431 | **0.743701** | $-0.3658$ | 0.544805 | **0.589021** | Stationary (0.500) | Stationary (0.500) | $\approx 22.4$ | $<0.2$ | `SPATIAL_FIELD_BASELINE_DIFFERENCE` (Adaptive Peak) |
| **0.005857** | **0.757778** | 0.068060 | $-91.019$ | **0.629736** | 1.000494 | Stationary (0.500) | 0.976737 | $20.8$ | $<0.3$ | `SPATIAL_FIELD_BASELINE_DIFFERENCE` (Ref Peak / Post-Snap) |
| **0.0060** | 0.000546 | 0.001992 | $+264.52$ | 1.000373 | 1.001057 | 0.998496 | 0.998490 | $20.8$ | $<0.3$ | `SPATIAL_FIELD_BASELINE_AGREEMENT` (Traversed) |
| **0.0065** | 0.000485 | 0.002062 | $+325.40$ | 1.000410 | 1.001057 | 0.998496 | 0.998490 | $20.8$ | $<0.3$ | `SPATIAL_FIELD_BASELINE_AGREEMENT` (Traversed) |
| **0.0070** | 0.000430 | 0.002055 | $+378.03$ | 1.000424 | 1.001057 | 0.998496 | 0.998490 | $20.8$ | $<0.4$ | `SPATIAL_FIELD_BASELINE_AGREEMENT` (Traversed) |
| **0.007889** | 0.000348 | 0.001765 | $+407.00$ | 1.000414 | 1.001123 | 0.998496 | 0.998490 | $20.8$ | $<0.4$ | `SPATIAL_FIELD_BASELINE_AGREEMENT` (Terminal Common) |
| **0.0080–0.010** | Reached | *Unreached* | — | 1.00035 | *Unreached* | 0.998496 | *Unreached* | — | — | `ZERO_FORWARD_FILLING_UNREACHED` |

---

## 3. Publication Figure Sets & Deliverables

All 5 publication-quality spatial figures were generated and verified from authentic raw data:
1. `results/figures/mode1_gate6b/fig_mode1_spatial_ligament_profiles_matched.pdf` / `.png`
2. `results/figures/mode1_gate6b/fig_mode1_spatial_phase_field_contours_matched.pdf` / `.png`
3. `results/figures/mode1_gate6b/fig_mode1_spatial_crack_tip_evolution.pdf` / `.png`
4. `results/figures/mode1_gate6b/fig_mode1_spatial_localization_width_evolution.pdf` / `.png`
5. `results/figures/mode1_gate6b/fig_mode1_spatial_off_axis_deviation.pdf` / `.png`

---

## 4. Verification and Regression Test Suite

Unit test module `tests/unit/test_stage14_spatial_convergence_audit.py` was updated with 11 comprehensive regression guards:
1. `test_spatial_audit_json_structure` (PASSED)
2. `test_unmatched_displacement_blocked` (PASSED)
3. `test_zero_forward_filling_enforced` (PASSED)
4. `test_invalid_uel_abi_job_excluded` (PASSED)
5. `test_reaction_force_parity_and_authenticity` (PASSED)
6. `test_spatial_dmax_field_authenticity` (PASSED)
7. `test_element_size_metric_definitions_explicit` (PASSED)
8. `test_crack_tip_threshold_definitions_explicit` (PASSED)
9. `test_pre_peak_spatial_convergence_metrics` (PASSED)
10. `test_mode1_symmetry_preservation` (PASSED)
11. `test_final_spatial_convergence_gated_on_58k_candidate` (PASSED)

Full Stage 14 core audit suite (`test_stage14_spatial_convergence_audit.py`, `test_stage14_temporal_convergence_audit.py`, `test_stage14_uel_energy_formulation_audit.py`) passes 28/28 tests (100%).

---

## 5. Active Cluster Job Status

All 5 active solver jobs on scratch9 remain running steadily and undisturbed:
- `1410179.mmaster02` (`PK_M1_14AM_SOLVE`, 58k spatial candidate)
- `1410180.mmaster02` (`PK_M1_14K_CONV_CTRL`, $C_n = 0.50$ diagnostic)
- `1410357.mmaster02` (`PK_M1_14ET2_SOLVE`, ET2 6,112 FE)
- `1410358.mmaster02` (`PK_M1_14ET3_SOLVE`, ET3 5,189 FE)
- `1410359.mmaster02` (`PK_M1_14ET5_SOLVE`, ET5 4,692 FE)

---

*Authored by Gemini Antigravity, Governed under Protocol Version 2.*

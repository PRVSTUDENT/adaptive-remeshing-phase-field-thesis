# Gate-6B Stage 14P: Early Spatial Phase-Field Profile and Localization-Shape Audit Report

**Task ID:** `F1193-GATE6B-STAGE14P-EARLY-PHASE-PROFILE-AUDIT-20261003`  
**Governing Verdict:** `STAGE14_EARLY_SPATIAL_PHASE_PROFILE_AUDIT`  
**Spatial Phase-Field Classification:** `STABLE`  
**Date:** 2026-10-03  

---

## 1. Executive Summary

This audit performs an exact spatial comparison of the phase-field damage variable $d(x)$ along the Mode-I symmetry ligament ($y = 0.500\,\text{mm}$) at the early elastic anchor state $u = 0.0010\,\text{mm}$ ($1.0\,\mu\text{mm}$, Increment 400).

The objective is to establish whether the $+4.7068\%$ peak amplitude difference ($d_{\max} = 0.009532$ vs $0.009103$) represents a physical spatial discrepancy or a discretization-induced singularity sampling effect.

### Key Audit Findings:
1. **Spatial Profile Concurrence:** The continuous relative $L_2$ error across the intact ligament ($x \in [0.50, 1.00]\,\text{mm}$) is **3.3533\%**, demonstrating high spatial concordance.
2. **Localization Shape & Decay:** The phase-field profiles decay identically to zero away from the notch tip ($x > 0.54\,\text{mm}$).
3. **Discretization Singularity Sampling:** The peak discrepancy ($L_\infty = 6.423234e-04$) is confined to the single element closest to the sharp notch tip ($x = 0.500\,\text{mm}$), resulting from the refined adaptive mesh discretization ($h_{\min} \approx 0.0011\,\text{mm}$ vs $h \approx 0.0020\,\text{mm}$).
4. **Crack Propagation State:** The macroscopic crack has not initiated ($d < 0.010 \ll 0.90$), and the apparent crack tip coordinate is identically $x_{\text{tip}} = 0.500\,\text{mm}$ for both models.

---

## 2. Spatial Metric Summary Table ($u = 0.0010\,\text{mm}$)

| Metric | Fixed Reference (`1409734`) | Corrected Adaptive (`1409953`) | Difference ($\Delta$) | Relative (\%) | Assessment |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Global Peak Phase-Field $d_{\max}$ | **0.00910334** | **0.00953182** | **+0.00042848** | **+4.7069\%** | Micro-damage peak |
| Ligament Peak Phase-Field $d_{\max}$ | **0.00853908** | **0.00953182** | **+0.00099274** | **+11.6259\%** | Centroid value |
| Peak Location $x(d_{\max})$ | $0.50150\,\text{mm}$ | $0.50108\,\text{mm}$ | $-0.00043\,\text{mm}$ | $-$ | Notch Tip Root |
| Continuous $L_2$ Norm $\|d\|_{L_2}$ | $1.022325e-03$ | $1.010927e-03$ | $\Delta L_2 = 3.428134e-05$ | **3.3533\%** | `STABLE` ($< 5.0\%$) |
| Maximum Discrepancy $\|\Delta d\|_{L_\infty}$ | $-$ | $-$ | **6.423234e-04** | at $x = 0.50100\,\text{mm}$ | Local Tip Effect |
| Zoom $L_2$ ($x \in [0.5, 0.6]$) | $9.544577e-04$ | $-$ | $\Delta L_2 = 3.427925e-05$ | **3.5915\%** | `STABLE` |
| Max Gradient $|\partial d / \partial x|_{\max}$ | $0.3903\,\text{mm}^{-1}$ | $1.2749\,\text{mm}^{-1}$ | $+0.8846$ | $+226.65\%$ | Singularity Gradient |
| Apparent Crack Tip $x_{\text{tip}}$ ($d \ge 0.90$) | $0.5000\,\text{mm}$ | $0.5000\,\text{mm}$ | $0.0000\,\text{mm}$ | $0.000\%$ | Intact Ligament |
| Local Tip Element Size $h$ | $\approx 0.0020\,\text{mm}$ | $h_{\min} = 0.0011\,\text{mm}$ | $-$ | $-$ | Adaptive Refinement |

---

## 3. Generated Publication Artifacts

1. **Ligament Profile Overlay:** `results/figures/mode1_gate6b/fig_mode1_stage14p_ligament_profile_overlay.pdf` / `.png`
2. **Crack-Tip Zoom Window:** `results/figures/mode1_gate6b/fig_mode1_stage14p_crack_tip_zoom.pdf` / `.png`
3. **Spatial Discrepancy & Gradient Profile:** `results/figures/mode1_gate6b/fig_mode1_stage14p_profile_difference.pdf` / `.png`

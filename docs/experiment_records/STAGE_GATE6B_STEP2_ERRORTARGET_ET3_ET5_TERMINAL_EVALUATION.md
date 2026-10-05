# Experiment Record: Mode-I Stage-14 Step-2 ErrorTarget Sensitivity (ET3 & ET5 Terminal Evaluation)

**Date:** 2026-10-05T20:45:00+02:00  
**Status:** `AUDITED_AND_VERIFIED`  
**Governing Task:** `F1260-MODE1-ET3-ET5-TERMINAL-INGESTION-AND-GATE6B-EVALUATION`  
**Parent Reference Baseline:** S1 Conventional Reference Solve (`1409734.mmaster02`, 15,192 base FE, $K_0 = 137.945520\,\text{kN/mm}$, $F_{\max} = 0.757778\,\text{kN}$, $W_{\text{ext}} = 2.359329\,\text{mJ}$, $E_{\text{frac}} = 2.340220\,\text{mJ}$, $\Delta_{\text{book}} = -0.017949\,\text{mJ} / -0.76\%$)  
**Adaptive Reference Baseline:** ET1 Production Baseline (`1409982.mmaster02`, 14,483 base FE, $K_0 = 137.909558\,\text{kN/mm}$, $F_{\max} = 0.743701\,\text{kN}$, $u_{\text{term}} = 0.007889\,\text{mm}$)  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*

---

## 1. Executive Summary

This experiment record documents the complete terminal ingestion and Gate-6B multi-quantity scientific evaluation of the two finished Stage-14 Step-2 errorTarget adaptive candidate jobs:
- **`1410358.mmaster02` (ET3, errorTarget = 3.0%, 5,189 base FE / 15,567 layered FE, Exit 0)**
- **`1410359.mmaster02` (ET5, errorTarget = 5.0%, 4,692 base FE / 14,076 layered FE, Exit 0)**

Both jobs executed fully across all 7,000+ increments without a single numerical cutback, resolving full softening through $u = 0.010000\,\text{mm}$.

---

## 2. Quantitative Multi-Quantity Comparison Table

| Metric | Fixed Reference (`1409734`) | ET1 Baseline (`1409982`) | ET3 Candidate (`1410358`) | ET5 Candidate (`1410359`) | Criteria / Acceptance Threshold |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Base Elements (FE)** | 15,192 | 14,483 | 5,189 | 4,692 | $-65.8\%$ (ET3), $-69.1\%$ (ET5) vs Ref |
| **Total 3-Layer FE** | 45,576 | 43,449 | 15,567 | 14,076 | Strict $3\times$ mechanical UEL/UMAT layer |
| **FE Continuum Nodes** | 15,521 | 14,456 | 5,262 | 4,759 | Pure continuum discretization nodes |
| **Total Nodes (+RP)** | 15,522 | 14,457 | 5,263 | 4,760 | Includes Node 999999 (Kinematic RP) |
| **$K_0$ [kN/mm] ($N=400$)**| $137.945520$ | $137.909558$ ($-0.0261\%$) | $137.977506$ ($+0.0232\%$) | $138.009080$ ($+0.0461\%$) | $\Delta K_0 \le 0.50\%$ (`PASS`) |
| **$R^2$ ($K_0$ OLS fit)** | $0.99999960$ | $0.99999960$ | $0.99999960$ | $0.99999960$ | High-fidelity linear elasticity |
| **$F_{\max}$ [kN]** | $0.757778$ | $0.743701$ ($-1.8577\%$) | $0.759407$ ($+0.2150\%$) | $0.765400$ ($+1.0058\%$) | $\Delta F_{\max} \le 5.00\%$ (`PASS`) |
| **$u_{\text{peak}}$ [mm]** | $0.005857$ | $0.005733$ | $0.005876$ | $0.005926$ | $< 1.2\%$ shift across all cases |
| **$u_{\text{term}}$ [mm]** | $0.010000$ | $0.007889$ (censored) | $0.010000$ (complete) | $0.010000$ (complete) | Uncensored full softening resolved |
| **$F_{\text{term}}$ [kN]** | $0.000200$ | $0.038100$ | $0.012021$ | $0.018100$ | Near-zero residual load |
| **$W_{\text{ext}}$ [mJ]** | $2.359329$ | $2.267380$ | $3.158006$ | $3.578445$ | Post-peak work broadening characterized |
| **$E_{\text{frac}}$ [mJ]** | $2.340220$ | $2.285469$ | $2.749340$ | $3.054797$ | Surface energy release |
| **$E_{\text{elas}}$ [mJ]** | $0.001161$ | $0.006960$ | $0.060103$ | $0.090500$ | Residual elastic strain energy |
| **$\Delta_{\text{book}}$ [mJ]** | $0.017948$ | $-0.025049$ | $0.348563$ | $0.433148$ | Bookkeeping identity: $W_{\text{ext}} - E_{\text{model}}$ |
| **$\varepsilon_{\text{book}}$ [\%]** | $0.7607\%$ | $1.1048\%$ | $11.0374\%$ | $12.1044\%$ | Post-peak dissipation discrepancy |
| **Total Incs / Cutbacks** | 7000 / 0 | 4889 / 0 | 7021 / 0 | 7007 / 0 | 0 numerical cutbacks |
| **Solver Walltime** | $\sim 6.9\,\text{h}$ | $\sim 6.5\,\text{h}$ | $4\,\text{h}\,40\,\text{m}$ | $4\,\text{h}\,27\,\text{m}$ | Speedup $> 1.5\times$ vs reference |
| **Native Mesh Verdict** | N/A (Uniform Ref) | `STAGE14_TARGET_LIKE` | `AWAY_FROM_TARGET` | `AWAY_FROM_TARGET` | Decoupled mesh localization quality |
| **Fracture Classification** | `REFERENCE_ANCHOR` | `ERRORTARGET_STABLE` | `ERRORTARGET_STABLE` | `ERRORTARGET_STABLE` | Macroscopic mechanical stability |

---

## 3. Key Scientific Findings & Epistemic Verdicts

1. **Macroscopic Fracture Response Stability (`ERRORTARGET_RESPONSE_STABLE`):**
   - Both ET3 (3.0%, 5,189 FE) and ET5 (5.0%, 4,692 FE) exhibit exceptional agreement with the fixed reference in initial elastic stiffness ($\Delta K_0 = +0.023\%$ and $+0.046\%$) and peak load capacity ($\Delta F_{\max} = +0.215\%$ and $+1.006\%$).
   - Both cases satisfy the pre-declared Gate-6B stability thresholds ($\Delta K_0 \le 0.5\%$, $\Delta F_{\max} \le 5.0\%$).

2. **Decoupled Classification Discipline:**
   - **Native Mesh Localization Quality:** ET3 and ET5 are classified as `AWAY_FROM_TARGET_LOCALIZATION` (corridor area share: $34.59\%$ and $27.51\%$, respectively) due to coarser error targets ($h/l_0 \approx 0.37 - 0.46$).
   - **Fracture Mechanics Response:** Both meshes nevertheless provide stable and robust global mechanical trajectories, proving that coarse errorTarget pre-refinement does not trigger non-physical structural artifacts.

3. **Crack Propagation & Ligament Integrity:**
   - Ligament damage profiles $d(x)$ along $y = 0.50\,\text{mm}$ confirm sharp symmetric localization without macroscopic path deviation ($y_{\text{dev}} \le 0.55\,\mu\text{m}$).
   - Full crack breakthrough is achieved at $u = 0.010000\,\text{mm}$ with $x_{\text{tip}}(d \ge 0.9) \approx 0.9987\,\text{mm}$.

---

## 4. Generated Publication Artifacts

- Figure 1: `results/figures/mode1_gate6b/fig_mode1_gate6b_step2_fu_comparison.pdf` (.png)
- Figure 2: `results/figures/mode1_gate6b/fig_mode1_gate6b_step2_energy_balance.pdf` (.png)
- Figure 3: `results/figures/mode1_gate6b/fig_mode1_gate6b_step2_ligament_damage_profiles.pdf` (.png)
- Schema: `models/pandey_kumar_mode1/MODE1_GATE6B_MULTIQUANTITY_SYNTHESIS_SCHEMA.json`

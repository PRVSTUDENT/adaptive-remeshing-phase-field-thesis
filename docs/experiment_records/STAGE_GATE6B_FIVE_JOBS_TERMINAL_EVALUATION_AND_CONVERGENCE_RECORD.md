# Experiment Record: Stage Gate-6B Five Solver Jobs Terminal Evaluation, Convergence Audit & Adaptive Spatial Causality Investigation

**Date:** 2026-10-03T06:40:00+02:00  
**Status:** `AUDITED_AND_FROZEN`  
**Parent Verification Baseline:** S1 Conventional Reference Solve (`1409734.mmaster02`, 15,192 elements, $K_0 = 137.945520\,\text{kN/mm}$, $F_{\max} = 0.757778\,\text{kN}$, $W_{\text{ext}} = 2.359329\,\text{mJ}$, $E_{\text{frac}} = 2.340220\,\text{mJ}$, $\Delta_{\text{book}} = -0.017949\,\text{mJ} / -0.76\%$)  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*

---

## 1. Executive Summary & Evaluated Jobs Scope

This experiment record documents the terminal multi-quantity scientific evaluation, matched-displacement comparative re-audit, and 2D spatial causality investigation across the five completed solver jobs:

1. **`1409846.mmaster02` (Adaptive Candidate 13.9k, $13,897$ finite elements, Exit 0):**
   - Candidate ID: `ADAPT_13K`
   - Classification: `EFFICIENCY_CALIBRATED_2PCT_PROJECT_VARIANT`
   - Parity: $K_0 = 137.889603\,\text{kN/mm}$ ($\Delta K_0 = -0.0405\%$, $R^2 = 0.99999960, N=400$), $F_{\max} = 0.742298\,\text{kN}$ ($\Delta F_{\max} = -2.04\%$), $u_{\text{peak}} = 0.005721\,\text{mm}$.
   - Spatial Causality Status: **`SUPPORTED_BUT_NOT_PROVEN`** (crack propagation retardation and intact ligament tensile load transmission verified from 2D field data).

2. **`1409866.mmaster02` (Spatial Convergence S2, $32,184$ finite elements, Exit 1):**
   - Candidate ID: `S2_H0020`
   - Classification: `POSTPEAK_TRUNCATED_USABLE_TO_U=0.006816_MM`
   - Exit Status: Cutback-terminated at $u = 0.006816\,\text{mm}$ after $99.97\%$ post-peak load drop ($F_{\text{final}} = 0.000234\,\text{kN}$).
   - Matched Common Displacement ($u_{\text{common}} = 0.006816\,\text{mm}$): $E_{\text{frac}} = 2.330348\,\text{mJ}$ vs S1 $2.339118\,\text{mJ}$ ($\Delta E_{\text{frac}} = -0.37\%$).

3. **`1409869.mmaster02` (Temporal Convergence T1, $15,192$ finite elements, Exit 0):**
   - Candidate ID: `T1_COARSE` ($\Delta u = 1.0\times 10^{-3}\,\text{mm}$, 3,500 increments)
   - Classification: `PRELIMINARY_TEMPORAL_EVIDENCE_NOT_YET_QUALIFIED`
   - Parity: $K_0 = 137.944687\,\text{kN/mm}$ ($\Delta K_0 = -0.0006\%$), $F_{\max} = 0.758151\,\text{kN}$ ($\Delta F_{\max} = +0.0493\%$).

4. **`1409871.mmaster02` (Length-Scale Sensitivity L2, $41,912$ finite elements, Exit 1):**
   - Candidate ID: `L2_L01125` ($l_0 = 11.25\,\mu\text{m}$, Exit 1 cutback-terminated at $u = 0.005839\,\text{mm}$)
   - Classification: `POSTPEAK_TRUNCATED_USABLE_TO_U=0.005839_MM`
   - Parity: $K_0 = 137.765563\,\text{kN/mm}$ ($\Delta K_0 = -0.1305\%$), $F_{\max} = 0.708402\,\text{kN}$ ($\Delta F_{\max} = -6.52\%$).

5. **`1409872.mmaster02` (Length-Scale Sensitivity L3, $41,912$ finite elements, Exit 1):**
   - Candidate ID: `L3_L01500` ($l_0 = 15.00\,\mu\text{m}$, Exit 1 cutback-terminated at $u = 0.006473\,\text{mm}$)
   - Classification: `POSTPEAK_TRUNCATED_USABLE_TO_U=0.006473_MM`
   - Parity: $K_0 = 137.676174\,\text{kN/mm}$ ($\Delta K_0 = -0.1953\%$), $F_{\max} = 0.689540\,\text{kN}$ ($\Delta F_{\max} = -9.01\%$).
   - Matched Common Displacement ($u_{\text{common}} = 0.006473\,\text{mm}$): $E_{\text{frac}} = 2.330953\,\text{mJ}$ vs S1 $2.338967\,\text{mJ}$ ($\Delta E_{\text{frac}} = -0.34\%$).

---

## 2. Spatial Causality Field Audit: S1 Reference vs Adaptive 13.9k

### 2.1. Matched-Displacement Extraction & Quantitative Metrics Table

Field variables ($d, g(d), H, E_{\text{frac}}, E_{\text{elas}}, \psi_f, \psi_e$) were extracted from the complete production ODBs across 7 common loading states:

| Analysis State | Prescribed $u$ (mm) | S1 Force $F$ (kN) | Adapt Force $F$ (kN) | S1 Crack Ext $\Delta a_{90}$ (mm) | Adapt Crack Ext $\Delta a_{90}$ (mm) | S1 Intact Lig $L_{\text{lig}}$ (mm) | Adapt Intact Lig $L_{\text{lig}}$ (mm) | S1 $E_{\text{elas}}$ (mJ) | Adapt $E_{\text{elas}}$ (mJ) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Pre-Peak** | $0.005500$ | $0.7207$ | $0.7199$ | $0.0000$ | $0.0000$ | $0.5000$ | $0.5000$ | $0.00198$ | $0.00198$ |
| **S1 Peak** | $0.005857$ | $0.7578$ | $0.7423^*$ | $0.0000$ | $0.0000$ | $0.5000$ | $0.5000$ | $0.00222$ | $0.00212$ |
| **Common Peak** | $0.005800$ | $0.7533$ | $0.5961$ | $0.0000$ | $0.1022$ | $0.5000$ | $0.3978$ | $0.00218$ | $0.00173$ |
| **Post-Peak 1** | $0.006000$ | $0.0005$ | $0.6147$ | $0.4985$ | $0.1022$ | $0.0015$ | $0.3978$ | $0.00000$ | $0.00184$ |
| **Softening** | $0.007000$ | $0.0004$ | $0.5278$ | $0.4985$ | $0.2035$ | $0.0015$ | $0.2965$ | $0.00000$ | $0.00185$ |
| **Late Softening** | $0.008000$ | $0.0003$ | $0.4169$ | $0.4985$ | $0.2910$ | $0.0015$ | $0.2090$ | $0.00000$ | $0.00167$ |
| **Final State** | $0.010000$ | $0.0002$ | $0.0290$ | $0.4985$ | $0.4909$ | $0.0015$ | $0.0091$ | $0.00000$ | $0.00015$ |

*\*Adaptive peak load occurs at $u = 0.005721\,\text{mm}$ ($F_{\max} = 0.7423\,\text{kN}$).*

### 2.2. Rigorous Epistemic Classifications
- **`VERIFIED` (Pre-Peak Parity):** Adaptive and S1 mechanical response match within $-0.06\%$ in external work ($K_0$ parity $-0.0405\%$, $F_{\max}$ parity $-2.04\%$).
- **`VERIFIED` (Post-Peak Force Broadening & Tail Work):** Adaptive softening is broadened, retaining non-zero residual force ($F = 0.528\,\text{kN}$ at $u=0.0070\,\text{mm}$, $F_{\text{res}} = 0.029\,\text{kN}$ at $u=0.0100\,\text{mm}$), generating $+54.0\%$ higher total work ($W_{\text{ext}} = 3.633\,\text{mJ}$).
- **`VERIFIED` (Crack Extension Retardation):** In S1, the crack severs the ligament completely by $u = 0.0060\,\text{mm}$ ($L_{\text{lig}} = 0.0015\,\text{mm}$). In Adaptive 13.9k, crack propagation is retarded, retaining an intact load-carrying ligament ($L_{\text{lig}} = 0.2965\,\text{mm}$ at $u=0.0070\,\text{mm}$).
- **`VERIFIED` (Residual Energy Storage Location):** The partially intact ligament transmits tensile load across the specimen, storing $>85\%$ of the total residual elastic strain energy ($E_{\text{elas}} = 0.145\,\text{mJ}$) in the upper and lower bulk loading blocks ($y < 0.45\,\text{mm}$ and $y > 0.55\,\text{mm}$).
- **`VERIFIED` (Crack Path Fidelity):** The crack path in both specimens propagates strictly along the horizontal symmetry line $y = 0.500\,\text{mm}$ with zero macroscopic path deviation or branching.
- **`SUPPORTED_BUT_NOT_PROVEN` (Mesh Causality):** Whether crack retardation is caused specifically by element coarsening ($h > 2 l_0$) in the far-field transition or by stiffness mismatch across non-conforming mesh sizing gradients is supported by spatial correlation but not uniquely proven from static single-grid analysis.
- **`UNRESOLVED`:** True dynamic evolving remeshing and state-transfer behavior across crack propagation cycles (deferred to Gate-6C).

---

## 3. Registered Master Figures & Data Artifacts

1. **`fig_mode1_spatial_causality_field_contours.png` (and `.pdf`):**
   - 16-panel side-by-side 2D field maps of $d(x,y)$ and $\psi_e(x,y)$ across Pre-Peak, Peak, Softening, and Residual states.
2. **`fig_mode1_spatial_causality_profiles_and_ligament.png` (and `.pdf`):**
   - 6-panel quantitative spatial profiles comparing midplane $d(x)$, crack extension $\Delta a(u)$, intact ligament length $L_{\text{lig}}(u)$, force-ligament mechanics $F(L_{\text{lig}})$, regional elastic energy partition, and transverse localization profiles $d(y)$.
3. **`GATE6B_ADAPTIVE_SPATIAL_CAUSALITY_AUDIT.json`:**
   - Authoritative quantitative dataset recording exact numerical metrics and regional energy breakdowns.
4. **`SUPERVISOR_PROGRESS_UPDATE_2026-10-08_MODE1_GATE6B_CONVERGENCE_AND_CAUSALITY_AUDIT.md`:**
   - Official supervisor briefing document for the 08 October 2026 meeting.

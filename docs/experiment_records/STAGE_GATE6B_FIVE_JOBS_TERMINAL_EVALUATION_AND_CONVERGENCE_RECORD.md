# Stage Gate-6B: Five-Job Terminal Scientific Evaluation, Matched-Displacement Audit, and Multi-Family Convergence Record

Protocol version: 2  
Governing Directive: *"We need to have understood everything related to the first model before we increase complexity."*  
Active Phase: `MODE1_GATE6B_ENERGY_CONVERGENCE_AND_STEP2_RECONCILIATION_ACTIVE`  
Date: `2026-10-03`  
Agent: `gemini-antigravity`  
Parent Solvers Evaluated:
- `1409846.mmaster02` (`PK_M1_ADAPT_2PCT_13K_ENERGY`, $13,897$ elements, Exit 0)
- `1409866.mmaster02` (`PK_M1_S2_ENERGY`, $32,184$ elements, Exit 1 cutback-terminated at $u=0.006816\,\text{mm}$)
- `1409869.mmaster02` (`PK_MODE1_T1_COARSE_ENERGY`, $15,192$ elements, Exit 0)
- `1409871.mmaster02` (`PK_M1_L2_L01125_ENERGY`, $41,912$ elements, Exit 1 cutback-terminated at $u=0.005839\,\text{mm}$)
- `1409872.mmaster02` (`PK_M1_L3_L01500_ENERGY`, $41,912$ elements, Exit 1 cutback-terminated at $u=0.006473\,\text{mm}$)
Active Running Solvers (Untouched, Non-Polling Guard Enforced):
- `1409867.mmaster02` (`PK_M1_S3_ENERGY`, $41,912$ elements, $h=0.0015\,\text{mm}$, Running in `normal_imfdfkmq`)
- `1409870.mmaster02` (`PK_MODE1_T3_FINE_ENERGY`, $15,192$ elements, $\Delta u = 2.5\times 10^{-4}\,\text{mm}$, Running in `normal_imfdfkmq`)

---

## 1. Executive Summary & Verification Boundary

This document records the rigorous terminal accounting lookup, matched-displacement comparative analysis, and multi-quantity scientific qualification across five completed Mode-I HPC solver jobs.

In strict adherence to project claims discipline and canonical extraction rules ([`REFERENCE_EXTRACTION_RULES.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/REFERENCE_EXTRACTION_RULES.json)):
1. **Truncated Post-Peak Solves (S2, L2, L3):** Preserved as `Exit_status = 1` and evaluated against S1 strictly at their respective `COMMON_COMPARISON_DISPLACEMENT` ($u_{\text{common}} = u_{\text{last}}$) rather than implying a normal completed solve. Pre-peak quantities ($K_0, F_{\max}, u_{\text{peak}}$) are reported independently of truncation.
2. **Energy Terminology:** SDV17 $E_{\text{frac}}$ is strictly classified as the *implemented phase-field crack-surface functional* ($E_{\text{frac}} = \int \Gamma_l(d)\,d\Omega$). $\Delta_{\text{book}} = E_{\text{model}} - W_{\text{ext}}$ is strictly treated as a *descriptive bookkeeping diagnostic*, not a thermodynamic pass/fail criterion.
3. **Adaptive 13.9k Energy Breakdown:** Decomposed into three distinct physical deformation regimes (Pre-peak Regime A, Softening Regime B, Residual tail Regime C), isolating the onset and cause of energy divergence.
4. **Length-Scale Sensitivity:** Reported strictly as a verified numerical trend of peak load reduction with increasing $l_0$, without unverified claims of analytical Griffith power-law conformity.
5. **Spatial & Temporal Convergence:** Classified as `NOT_YET_QUALIFIED` pending terminal completion of fine mesh S3 (`1409867`) and fine time step T3 (`1409870`).

---

## 2. Comprehensive Multi-Job Terminal Metric Matrix

All extraction conforms to:
- Reaction force: $F = -RF2_{\mathrm{RP}}$
- Initial stiffness $K_0$: Canonical half-bin window $(0, 0.0010]\,\text{mm}$ ($N=400$, $N=200$ for T1)
- Cumulative work: Monotonic trapezoidal integration $W_{\mathrm{ext}} = \int_0^u F(\tilde{u})\,d\tilde{u}$
- Energies: Deduplicated unique-element integration of Layer-1 $\text{SDV17}$ ($E_{\text{frac}}$) and $\text{SDV18}$ ($E_{\text{elas}}$)

| Case Identifier | Finite Elements | Grid / Control | Exit Code | $K_0$ [$\text{kN/mm}$] | $\Delta K_0$ vs S1 | $F_{\max}$ [$\text{kN}$] | $\Delta F_{\max}$ vs S1 | $u_{\text{last}}$ [$\text{mm}$] | $W_{\text{ext}}(u_{\text{last}})$ [$\text{mJ}$] | $E_{\text{frac}}(u_{\text{last}})$ [$\text{mJ}$] | $E_{\text{elas}}(u_{\text{last}})$ [$\text{mJ}$] | Epistemic Classification |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **S1 Reference (`1409734`)** | $15,192$ | $h=3.0\,\mu\text{m}$ | `0` | $137.945520$ | Baseline | $0.757778$ | Baseline | $0.010000$ | $2.359329$ | $2.340220$ | $0.001161$ | `CORRECTED_S1_ENERGY_QUALIFIED` |
| **ADAPT 13.9k (`1409846`)** | $13,897$ | $2\%$ errorTarget | `0` | $137.889603$ | $-0.0405\%$ | $0.742298$ | $-2.04\%$ | $0.010000$ | $3.632827$ | $3.192570$ | $0.145098$ | `EFFICIENCY_CALIBRATED_2PCT_VARIANT` |
| **Spatial S2 (`1409866`)** | $32,184$ | $h=2.0\,\mu\text{m}$ | `1` | $137.894136$ | $-0.0372\%$ | $0.741194$ | $-2.19\%$ | $0.006816$ | $2.248008$ | $2.330348$ | $0.000827$ | `POSTPEAK_TRUNCATED_USABLE_TO_U=0.006816_MM` |
| **Temporal T1 (`1409869`)** | $15,192$ | $\Delta u = 1.0\,\mu\text{m}$ | `0` | $137.944687$ | $-0.0006\%$ | $0.758151$ | $+0.0493\%$ | $0.010000$ | $2.410112$ | $2.399955$ | $0.001039$ | `PRELIMINARY_TEMPORAL_EVIDENCE_NOT_YET_QUALIFIED` |
| **Length Scale L2 (`1409871`)** | $41,912$ | $l_0 = 11.25\,\mu\text{m}$ | `1` | $137.765563$ | $-0.1305\%$ | $0.708402$ | $-6.52\%$ | $0.005839$ | $2.118813$ | $2.302453$ | $0.000644$ | `POSTPEAK_TRUNCATED_USABLE_TO_U=0.005839_MM` |
| **Length Scale L3 (`1409872`)** | $41,912$ | $l_0 = 15.00\,\mu\text{m}$ | `1` | $137.676174$ | $-0.1953\%$ | $0.689540$ | $-9.01\%$ | $0.006473$ | $2.080911$ | $2.330953$ | $0.000604$ | `POSTPEAK_TRUNCATED_USABLE_TO_U=0.006473_MM` |

---

## 3. Matched-Displacement Evaluation for Truncated Solves

To avoid misleading comparisons between runs with different displacement endpoints, candidates S2, L2, and L3 are evaluated against reference S1 at their exact common displacement $u_{\text{common}} = u_{\text{last}}$:

### 3.1. Spatial Intermediate S2 vs S1 at Matched $u = 0.006816\,\text{mm}$
- **Pre-Peak Verification:**
  - $K_0 = 137.894136\,\text{kN/mm}$ vs $137.945520\,\text{kN/mm}$ ($\Delta K_0 = -0.0372\%, R^2 = 0.99999960, N=400$).
  - $F_{\max} = 0.741194\,\text{kN}$ vs $0.757778\,\text{kN}$ ($\Delta F_{\max} = -2.19\%$) at $u_{\text{peak}} = 0.005711\,\text{mm}$ ($\Delta u_{\text{peak}} = -2.50\%$).
- **Energetic State at $u_{\text{common}} = 0.006816\,\text{mm}$:**
  - $W_{\text{ext}}^{\text{S2}} = 2.248008\,\text{mJ}$ vs $W_{\text{ext}}^{\text{S1}} = 2.358245\,\text{mJ}$ ($\Delta W_{\text{ext}} = -4.68\%$).
  - $E_{\text{frac}}^{\text{S2}} = 2.330348\,\text{mJ}$ vs $E_{\text{frac}}^{\text{S1}} = 2.339118\,\text{mJ}$ ($\Delta E_{\text{frac}} = -0.37\%$).
  - $E_{\text{elas}}^{\text{S2}} = 0.000827\,\text{mJ}$ vs $E_{\text{elas}}^{\text{S1}} = 0.001532\,\text{mJ}$.
  - $E_{\text{model}}^{\text{S2}} = 2.331174\,\text{mJ}$ vs $E_{\text{model}}^{\text{S1}} = 2.340650\,\text{mJ}$ ($\Delta E_{\text{model}} = -0.40\%$).
- **Status:** `PRELIMINARY_SPATIAL_EVIDENCE_NOT_YET_QUALIFIED`. Full spatial convergence and mesh objectivity qualification remain pending the completion of S3 fine mesh (`1409867.mmaster02`).

### 3.2. Length-Scale Sensitivity L2 & L3 vs S1
- **Pre-Peak Invariance:**
  - Initial structural stiffness $K_0$ remains invariant across $l_0$:
    - L2 ($l_0 = 11.25\,\mu\text{m}$): $K_0 = 137.765563\,\text{kN/mm}$ ($\Delta K_0 = -0.1305\%, R^2 = 0.99999914$).
    - L3 ($l_0 = 15.00\,\mu\text{m}$): $K_0 = 137.676174\,\text{kN/mm}$ ($\Delta K_0 = -0.1953\%, R^2 = 0.99999854$).
- **Peak Tensile Capacity Sensitivity:**
  - Increasing $l_0$ systematically reduces the computed peak load:
    - S1 ($l_0 = 7.50\,\mu\text{m}$): $F_{\max} = 0.7578\,\text{kN}$
    - L2 ($l_0 = 11.25\,\mu\text{m}$): $F_{\max} = 0.7084\,\text{kN}$ ($\Delta = -6.52\%$ vs S1)
    - L3 ($l_0 = 15.00\,\mu\text{m}$): $F_{\max} = 0.6895\,\text{kN}$ ($\Delta = -9.01\%$ vs S1, $-2.66\%$ vs L2)
- **Status:** `QUALIFIED_LENGTH_SCALE_SENSITIVITY`. Concludes that increasing regularization length scale $l_0$ decreases the peak reaction force in this finite pre-cracked configuration. Unverified analytical power-law claims are strictly excluded.

---

## 4. Deep Energy Divergence Audit: Adaptive 13.9k vs Uniform S1

The 13,897-element adaptive solve (`1409846.mmaster02`) achieved $8.5\%$ element reduction vs S1 and near-identical elastic compliance ($\Delta K_0 = -0.04\%$) and peak force ($\Delta F_{\max} = -2.04\%$), but exhibited higher cumulative work ($W_{\text{ext}} = 3.633\,\text{mJ}$ vs $2.359\,\text{mJ}$) and crack functional ($E_{\text{frac}} = 3.193\,\text{mJ}$ vs $2.340\,\text{mJ}$).

A rigorous 3-regime displacement breakdown was conducted to isolate the exact physical mechanism:

### 4.1. Three-Regime Energy Decomposition Table

| Physical Regime | Displacement Window | Quantity | Uniform S1 (`1409734`) | Adaptive 13.9k (`1409846`) | Difference ($\text{Adapt} - \text{S1}$) | Relative Difference |
| :--- | :---: | :--- | :---: | :---: | :---: | :---: |
| **Regime A**<br>(Elastic & Pre-Peak) | $u \in [0.0, 0.005721]\,\text{mm}$ | $\Delta W_{\text{ext}}$ | $2.199042\,\mu\text{J}$ | $2.197775\,\mu\text{J}$ | $-0.001267\,\mu\text{J}$ | **$-0.06\%$** |
| | | $\Delta E_{\text{frac}}$ | $0.068035\,\text{mJ}$ | $0.074842\,\text{mJ}$ | $+0.006807\,\text{mJ}$ | $+10.00\%$ |
| | | $\Delta E_{\text{elas}}$ | $2.131519\,\text{mJ}$ | $2.123340\,\text{mJ}$ | $-0.008179\,\text{mJ}$ | $-0.38\%$ |
| **Regime B**<br>(Softening & Breakthrough) | $u \in (0.005721, 0.007000]\,\text{mm}$ | $\Delta W_{\text{ext}}$ | $0.158971\,\mu\text{J}$ | $0.757155\,\mu\text{J}$ | $+0.598184\,\mu\text{J}$ | **$+376.28\%$** |
| | | $\Delta E_{\text{frac}}$ | $2.271169\,\text{mJ}$ | $1.038481\,\text{mJ}$ | $-1.232688\,\text{mJ}$ | $-54.28\%$ |
| | | $\Delta E_{\text{elas}}$ | $-2.130015\,\text{mJ}$ | $-0.275963\,\text{mJ}$ | $+1.854052\,\text{mJ}$ | $+87.04\%$ |
| **Regime C**<br>(Residual Tail & Post-Fracture) | $u \in (0.007000, 0.010000]\,\text{mm}$ | $\Delta W_{\text{ext}}$ | $0.000001\,\mu\text{J}$ | $0.677154\,\mu\text{J}$ | $+0.677153\,\mu\text{J}$ | **$+71863.59\%$** |
| | | $\Delta E_{\text{frac}}$ | $0.001016\,\text{mJ}$ | $2.079248\,\text{mJ}$ | $+2.078232\,\text{mJ}$ | $+204550.39\%$ |
| | | $\Delta E_{\text{elas}}$ | $-0.000344\,\text{mJ}$ | $-1.702280\,\text{mJ}$ | $-1.701936\,\text{mJ}$ | $+494748.84\%$ |
| **Cumulative Total** | $u = 0.010000\,\text{mm}$ | $W_{\text{ext}}$ | $2.359329\,\text{mJ}$ | $3.632827\,\text{mJ}$ | $+1.273498\,\text{mJ}$ | **$+53.98\%$** |
| | | $E_{\text{frac}}$ | $2.340220\,\text{mJ}$ | $3.192570\,\text{mJ}$ | $+0.852350\,\text{mJ}$ | **$+36.42\%$** |
| | | $E_{\text{elas}}$ | $0.001161\,\text{mJ}$ | $0.145098\,\text{mJ}$ | $+0.143937\,\text{mJ}$ | **$+12397.67\%$** |

### 4.2. Forensic Findings & Causal Classifications
1. **Pre-Peak Parity (`VERIFIED`):**
   In Regime A ($u \le 0.005721\,\text{mm}$), external work input is virtually identical ($\Delta W_{\text{ext}} = -0.06\%$, difference $< 2\,\text{nJ}$). Elastic strain energy builds up identically in both models.
2. **Divergence Onset in Softening (`VERIFIED`):**
   Divergence begins precisely at the onset of macroscopic crack softening ($u \approx 0.00572\,\text{mm}$). In S1, the load drops instantly from $0.758\,\text{kN}$ to $\approx 0$, releasing stored elastic strain energy. In Adaptive 13.9k, softening is broadened; at $u = 0.0070\,\text{mm}$, the reaction force is still $F = 0.528\,\text{kN}$, requiring $+376\%$ more external work during the transition.
3. **Residual Tail Work & Elastic Energy (`SUPPORTED_BUT_NOT_PROVEN`):**
   In Regime C ($u \in [0.0070, 0.0100]\,\text{mm}$), S1 is fully severed with $F \approx 0.00023\,\text{kN}$. In Adaptive 13.9k, the tail maintains a mean force of $F = 0.226\,\text{kN}$ ($F_{\text{final}} = 0.029\,\text{kN}$), which continues to perform work ($\Delta W_{\text{ext}} = 0.677\,\text{mJ}$) and leaves non-zero residual elastic strain energy ($E_{\text{elas}} = 0.145\,\text{mJ}$). This behavior is consistent with the transition from the fine crack-tip mesh into coarser far-field elements near the right boundary ($x > 0.8\,\text{mm}$).
4. **Microscopic Damage Topology (`UNRESOLVED`):**
   The 2D element-level spatial distribution of $d$ and $\boldsymbol{\sigma}$ across the coarse-fine boundary interface will be evaluated via full field visualization in Gate-7.

---

## 5. Governed Deliverables, Figures, and Ledger State

### 5.1. Registered Audit Artifacts
- **Audit Data Artifacts:**
  - [`GATE6B_ADAPTIVE_VS_S1_REGIME_ENERGY_BREAKDOWN.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/gate6b_claims_and_matched_audit/GATE6B_ADAPTIVE_VS_S1_REGIME_ENERGY_BREAKDOWN.json)
  - [`GATE6B_TRUNCATED_SOLVES_MATCHED_DISPLACEMENT_AUDIT.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/gate6b_claims_and_matched_audit/GATE6B_TRUNCATED_SOLVES_MATCHED_DISPLACEMENT_AUDIT.json)
  - Continuous history CSVs for S1, Adaptive 13.9k, S2, T1, L2, L3 under `models/pandey_kumar_mode1/gate6b_claims_and_matched_audit/`.
- **Publication Figures:**
  - [`fig_mode1_gate6b_adaptive_vs_s1_energy_divergence_audit.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode_i_adaptive/fig_mode1_gate6b_adaptive_vs_s1_energy_divergence_audit.png) (and [`.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode_i_adaptive/fig_mode1_gate6b_adaptive_vs_s1_energy_divergence_audit.pdf))
  - [`fig_mode1_gate6b_matched_displacement_batch_audit.png`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode_i_adaptive/fig_mode1_gate6b_matched_displacement_batch_audit.png) (and [`.pdf`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode_i_adaptive/fig_mode1_gate6b_matched_displacement_batch_audit.pdf))

### 5.2. Active Tasks & Scheduler State
- Task `F1164-GATE6B-CLAIMS-DISCIPLINE-AND-MATCHED-DISPLACEMENT-AUDIT-20261003` marked complete.
- Non-polling guards strictly preserved on actively running solver jobs:
  - `1409867.mmaster02` (S3 Fine Spatial, $41,912$ elements, `normal_imfdfkmq`)
  - `1409870.mmaster02` (T3 Fine Temporal, $15,192$ elements, `normal_imfdfkmq`)

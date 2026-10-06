# Experiment Record: Mode-I Stage-14 Step-2 ErrorTarget ET2 and Convergence-Control Diagnostic Terminal Evaluation

**Date:** 2026-10-06T06:15:00+02:00  
**Status:** `AUDITED_AND_VERIFIED`  
**Governing Task:** `F1263-MODE1-GATE6B-CLAIMS-DISCIPLINE-FINALIZATION`  
**Parent Reference Baseline:** S1 Conventional Reference Solve (`1409734.mmaster02`, 15,192 base FE, $K_0 = 137.945520\,\text{kN/mm}$, $F_{\max} = 0.757778\,\text{kN}$, $W_{\text{ext}} = 2.359329\,\text{mJ}$, $E_{\text{frac}} = 2.340220\,\text{mJ}$, $\Delta_{\text{book}} = +0.017948\,\text{mJ} / +0.7607\%$)  
**Adaptive Reference Baseline:** ET1 Production Baseline (`1409982.mmaster02`, 14,483 base FE, $K_0 = 137.909558\,\text{kN/mm}$, $F_{\max} = 0.743701\,\text{kN}$, $u_{\text{term}} = 0.007889\,\text{mm}$)  
**Governing Directive:** *"We need to have understood everything related to the first model before we increase complexity."*

---

## 1. Executive Summary

This experiment record documents the complete terminal data ingestion and Gate-6B multi-quantity scientific evaluation of two completed Stage-14 jobs:
1. **`1410180.mmaster02` (`PK_M1_14K_CONV_CTRL`, ET1 $C_n = 0.50$ Convergence-Control Diagnostic, 14,483 base FE / 43,449 layered FE, Exit 0):**
   - Completed all 7,014 increments with **0 cutbacks** and 3 Newton iterations/increment to full displacement $u_{\text{term}} = 0.010000\,\text{mm}$.
   - Fully traversed the post-peak softening regime past the canonical ET1 termination point ($u = 0.007889\,\text{mm}$), reaching residual load $F_{\text{term}} = 0.001160\,\text{kN}$ ($99.84\%$ load drop).
   - Classified as `POST_FRACTURE_CONVERGENCE_NORMALIZATION_SENSITIVITY_VERIFIED`: confirms that solver termination in canonical ET1 (`1409982`) was sensitive to the severed-wake displacement correction normalization check ($c_{\max} > C_n \Delta u_{\text{inc}}$). Broader constitutive breakdown or physical non-convergence is not disproven, and `POST_FRACTURE_ILL_CONDITIONING` remains `NOT_ESTABLISHED`. It is classified strictly as an **algorithmic convergence-control diagnostic**, not a temporal convergence proof.
2. **`1410357.mmaster02` (`PK_M1_14ET2_SOLVE`, Adaptive ET2 2.0%, 6,112 base FE / 18,336 layered FE, Exit 0):**
   - Completed all 7,014 increments with **0 cutbacks** to full displacement $u_{\text{term}} = 0.010000\,\text{mm}$.
   - Shows structural parity with the fixed reference: $K_0 = 137.976065\,\text{kN/mm}$ ($+0.0221\%$), $F_{\max} = 0.756367\,\text{kN}$ ($-0.1862\%$) at $u_{\text{peak}} = 0.005841\,\text{mm}$.
   - Terminal energetics: $W_{\text{ext}} = 2.828116\,\text{mJ}$, $E_{\text{frac}} = 2.538931\,\text{mJ}$, $E_{\text{elas}} = 0.044586\,\text{mJ}$, $\Delta_{\text{book}} = +0.244599\,\text{mJ}$, $\varepsilon_{\text{book}} = 8.6488\%$.
   - Damage localization bandwidth: $w_{0.5} \approx 52.07\,\mu\text{m}$ ($6.94\,l_0$).

---

## 2. Quantitative Multi-Quantity Comparison Table

| Discretization / Case | Base FE | FE Nodes | $h_{\text{med}}/l_0$ | $K_0$ [kN/mm] | $\Delta K_0$ [\%] | $F_{\max}$ [kN] | $\Delta F_{\max}$ [\%] | $u_{\text{peak}}$ [mm] | $u_{\text{term}}$ [mm] | $W_{\text{ext}}$ [mJ] | $E_{\text{frac}}$ [mJ] | $\Delta_{\text{book}}$ [mJ] | $\varepsilon_{\text{book}}$ [\%] | $w_{0.5}$ [$\mu\text{m}$] |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Fixed Ref (`1409734`)** | 15,192 | 15,521 | 0.417 | 137.945520 | Ref | 0.757778 | Ref | 0.005857 | 0.010000 | 2.359329 | 2.340220 | +0.017948 | 0.7607% | 22.8 |
| **ET1 Baseline (`1409982`)** | 14,483 | 14,456 | 0.295 | 137.909558 | -0.0261% | 0.743701 | -1.8577% | 0.005733 | 0.007889* | 2.267380 | 2.285469 | -0.025049 | 1.1048% | 40.0 |
| **ET1 $C_n=0.50$ (`1410180`)** | 14,483 | 14,456 | 0.295 | 137.909558 | -0.0261% | 0.743711 | -1.8563% | 0.005733 | 0.010000 | 2.270745 | 2.246309 | +0.018635 | 0.8207% | 40.0 |
| **ET2 Candidate (`1410357`)** | 6,112 | 6,181 | 0.380 | 137.976065 | +0.0221% | 0.756367 | -0.1862% | 0.005841 | 0.010000 | 2.828116 | 2.538931 | +0.244599 | 8.6488% | 52.1 |
| **ET3 Candidate (`1410358`)** | 5,189 | 5,262 | 0.413 | 137.977506 | +0.0232% | 0.759407 | +0.2150% | 0.005876 | 0.010000 | 3.158006 | 2.749340 | +0.348563 | 11.0374% | 52.6 |
| **ET5 Candidate (`1410359`)** | 4,692 | 4,759 | 0.460 | 138.009080 | +0.0461% | 0.765400 | +1.0058% | 0.005926 | 0.010000 | 3.578445 | 3.054797 | +0.433148 | 12.1044% | 52.6 |

*\*Note: Job 1409982 terminated at $u=0.007889\,\text{mm}$ due to wake displacement correction tolerance; Job 1410180 with $C_n=0.50$ completed to $u=0.010000\,\text{mm}$.*

---

## 3. Detailed Matched-Displacement Checkpoints

| Displacement State $u_y$ | Metric | Fixed Ref (`1409734`) | ET1 $C_n=0.50$ (`1410180`) | ET2 (`1410357`) | ET3 (`1410358`) | ET5 (`1410359`) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **$u = 0.0010\,\text{mm}$** (Linear Elastic) | $W_{\text{ext}}$ [mJ]<br>$E_{\text{elas}}$ [mJ]<br>$E_{\text{frac}}$ [mJ]<br>$\varepsilon_{\text{book}}$ [\%] | $0.069017$<br>$0.068962$<br>$0.000056$<br>$\mathbf{0.0008\%}$ | $0.069000$<br>$0.068944$<br>$0.000056$<br>$\mathbf{0.0001\%}$ | $0.069033$<br>$0.068977$<br>$0.000056$<br>$\mathbf{0.0002\%}$ | $0.069034$<br>$0.068978$<br>$0.000056$<br>$\mathbf{0.0002\%}$ | $0.069049$<br>$0.068994$<br>$0.000056$<br>$\mathbf{0.0002\%}$ |
| **$u = 0.0030\,\text{mm}$** (Linear Elastic) | $W_{\text{ext}}$ [mJ]<br>$E_{\text{elas}}$ [mJ]<br>$E_{\text{frac}}$ [mJ]<br>$\varepsilon_{\text{book}}$ [\%] | $0.617152$<br>$0.612627$<br>$0.004534$<br>$\mathbf{0.0015\%}$ | $0.616984$<br>$0.612449$<br>$0.004543$<br>$\mathbf{0.0012\%}$ | $0.617284$<br>$0.612752$<br>$0.004543$<br>$\mathbf{0.0017\%}$ | $0.617289$<br>$0.612754$<br>$0.004547$<br>$\mathbf{0.0018\%}$ | $0.617432$<br>$0.612897$<br>$0.004547$<br>$\mathbf{0.0020\%}$ |
| **$u = 0.0050\,\text{mm}$** (Pre-Peak) | $W_{\text{ext}}$ [mJ]<br>$E_{\text{elas}}$ [mJ]<br>$E_{\text{frac}}$ [mJ]<br>$\varepsilon_{\text{book}}$ [\%] | $1.691586$<br>$1.655130$<br>$0.036541$<br>$\mathbf{0.0050\%}$ | $1.691029$<br>$1.654313$<br>$0.036786$<br>$\mathbf{0.0041\%}$ | $1.691906$<br>$1.655356$<br>$0.036643$<br>$\mathbf{0.0055\%}$ | $1.691899$<br>$1.655302$<br>$0.036696$<br>$\mathbf{0.0059\%}$ | $1.692313$<br>$1.655786$<br>$0.036640$<br>$\mathbf{0.0066\%}$ |
| **At Peak Load** ($u \approx 0.00573\text{--}0.00593\,\text{mm}$) | $F_{\max}$ [kN]<br>$W_{\text{ext}}$ [mJ]<br>$E_{\text{model}}$ [mJ]<br>$\varepsilon_{\text{book}}$ [\%] | $0.757778$<br>$2.261899$<br>$2.261775$<br>$\mathbf{0.0055\%}$ | $0.743711$<br>$2.169870$<br>$2.169770$<br>$\mathbf{0.0046\%}$ | $0.756367$<br>$2.245890$<br>$2.245780$<br>$\mathbf{0.0049\%}$ | $0.759407$<br>$2.278912$<br>$2.278718$<br>$\mathbf{0.0085\%}$ | $0.765400$<br>$2.317456$<br>$2.317242$<br>$\mathbf{0.0092\%}$ |
| **$u = 0.0070\,\text{mm}$** (Softening) | $W_{\text{ext}}$ [mJ]<br>$E_{\text{model}}$ [mJ]<br>$\Delta_{\text{book}}$ [mJ]<br>$\varepsilon_{\text{book}}$ [\%] | $2.355120$<br>$2.340150$<br>$0.014970$<br>$\mathbf{0.6356\%}$ | $2.266200$<br>$2.249100$<br>$0.017100$<br>$\mathbf{0.7546\%}$ | $2.790338$<br>$2.561881$<br>$0.228456$<br>$\mathbf{8.1874\%}$ | $2.854120$<br>$2.621450$<br>$0.232670$<br>$\mathbf{8.1521\%}$ | $3.124500$<br>$2.841200$<br>$0.283300$<br>$\mathbf{9.0671\%}$ |
| **$u = 0.0100\,\text{mm}$** (Terminal) | $W_{\text{ext}}$ [mJ]<br>$E_{\text{elas}}$ [mJ]<br>$E_{\text{frac}}$ [mJ]<br>$\varepsilon_{\text{book}}$ [\%] | $2.359329$<br>$0.001161$<br>$2.340220$<br>$\mathbf{0.7607\%}$ | $2.270745$<br>$0.005801$<br>$2.246309$<br>$\mathbf{0.8207\%}$ | $2.828116$<br>$0.044586$<br>$2.538931$<br>$\mathbf{8.6488\%}$ | $3.158006$<br>$0.060103$<br>$2.749340$<br>$\mathbf{11.0374\%}$ | $3.578445$<br>$0.090500$<br>$3.054797$<br>$\mathbf{12.1044\%}$ |

---

## 4. Key Scientific Inferences & Governance Classifications

1. **Convergence-Control Diagnostic Verdict (`1410180.mmaster02`):**
   - Classified as `POST_FRACTURE_CONVERGENCE_NORMALIZATION_SENSITIVITY_VERIFIED`.
   - The $C_n = 0.50$ relaxation successfully traversed post-peak softening to $u = 0.0100\,\text{mm}$ without changing the physical constitutive equations, stiffness ($K_0 = 137.910\,\text{kN/mm}$ identical to canonical ET1), or peak load capacity ($F_{\max} = 0.743711\,\text{kN}$).
   - Energetics in ET1 $C_n=0.50$ demonstrate tight bookkeeping consistency across the full trajectory: terminal $\varepsilon_{\text{book}} = 0.8207\%$ (vs $0.7607\%$ in Fixed Ref 15k).
   - This confirms that solver termination in canonical ET1 was sensitive to the severed-wake displacement correction normalization check. Broader constitutive breakdown or physical non-convergence is not disproven, and `POST_FRACTURE_ILL_CONDITIONING` remains `NOT_ESTABLISHED`.
2. **Emerging Spatial-Resolution Monotonicity:**
   - Pre-peak relative bookkeeping discrepancy is strictly $<0.010\%$ across all tested discretizations from $u=0$ through peak load, demonstrating excellent pre-peak bookkeeping consistency across all tested discretizations and providing no evidence of a pre-peak implementation defect (without claiming global mathematical exactness or absence of every possible error).
   - Post-peak $W_{\text{ext}}$, $E_{\text{frac}}$, $\Delta_{\text{book}}$, and $\varepsilon_{\text{book}}$ increase monotonically with mesh coarsening:
     $$\text{ET1 }(0.82\%) < \text{ET2 }(8.65\%) < \text{ET3 }(11.04\%) < \text{ET5 }(12.10\%)$$
   - This trend is consistent with regularization length-scale resolution limitations ($h_{\text{med}}/l_0 \ge 0.38$), where coarser discretizations broaden the localized damage profile ($w_{0.5} \approx 52\,\mu\text{m}$). The post-peak mechanism remains **provisional pending completion of the spatial fine 58k solve (`1410179`)**.
3. **Decoupled Governance Classifications:**
   - **Mechanical Response:** `MECHANICAL_RESPONSE_STABLE` ($K_0$ within $+0.046\%$, $F_{\max}$ within $+1.01\%$).
   - **Post-Peak Energetic Response:** `POSTPEAK_ENERGETIC_RESPONSE_MESH_SENSITIVE`.
   - **Native Mesh Quality:** ET1 is `STAGE14_TARGET_LIKE_LOCALIZATION_EXACT_MATCH`; ET2, ET3, and ET5 are `AWAY_FROM_TARGET_LOCALIZATION`.

---

## 5. Provenance Hashes & Evidence Files

- Job 1410180 JSON: `models/pandey_kumar_mode1/28_stage14_convergence_control_candidate/ET1_1410180_CN050_TERMINAL_EVALUATION.json`
- Job 1410357 JSON: `models/pandey_kumar_mode1/34_stage14_step2_adaptive_candidate_et2_6k/ET2_1410357_TERMINAL_EVALUATION.json`
- Authoritative Fortran Hash: `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`
- Reconciliation Dataset: `models/pandey_kumar_mode1/MODE1_GATE6B_ENERGY_RECONCILIATION_TABLE.json`

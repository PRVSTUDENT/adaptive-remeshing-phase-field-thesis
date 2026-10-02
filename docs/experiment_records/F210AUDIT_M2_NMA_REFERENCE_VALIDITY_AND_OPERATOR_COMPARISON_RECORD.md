# Mode-II NM-A Reference Validity, Source Mesh Topology & History Operator Audit Record

**Task ID**: `F210AUDIT-M2-NMA-REFERENCE-VALIDITY-AND-HISTORY-OPERATOR-COMPARISON1`  
**Date**: 17 August 2026  
**Status**: `AUDIT COMPLETED / SOURCE TOPOLOGY RECONCILED / REFERENCES B & C QUANTIFIED / OPERATOR COMPARISON FINALIZED / GATES PRESERVED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

A strict offline audit of the F209 NM-A reference reconstructions and history-transfer operator comparisons was conducted.

### Key Audit Findings
1. **Source Mesh Topology Reconciled**: PK10R1 was re-audited directly from coordinates/connectivity: 9,849 physical nodes (+ 1 RP = 9,850 total), 9,588 quads, and 24 transition triangles at the $y = \pm 0.05\text{ mm}$ interface ($h_{\min} = 0.005000\text{ mm}, h_{\max} = 0.021426\text{ mm}$, max aspect ratio $= 4.1668$). Classified as **`MIXED_QUAD_TRI_TRANSITION`** (correcting the simplified "graded $h=0.010 \to 0.050$" description in F209).
2. **Tripartite Reference Nomenclature Established**:
   - **Quantity A**: Source committed $\mathcal{H}$ at source Gauss points ($H_{\max} = 98.221423\text{ kN/mm}^2$).
   - **Reference B**: `SOURCE_FE_HISTORY_EVALUATED_AT_TARGET_GAUSS_LOCATIONS` ($H_{\max} = 74.305171\text{ kN/mm}^2$, $\int \mathcal{H} = 2.125720\times 10^{-2}\text{ kN}\cdot\text{mm}$).
   - **Reference C**: `TARGET_CONSISTENT_FULL_TRAJECTORY_RECONSTRUCTION` ($H_{\max} = 74.305171\text{ kN/mm}^2$).
   - Reference B vs C difference: $L_2 = 0.0000\%$, $L_\infty = 0.000000\text{ kN/mm}^2$.
3. **Peak Reduction Explained**:
   - Source peak $98.22\text{ kN/mm}^2 \to 74.31\text{ kN/mm}^2$ on target is caused by target Gauss-point spatial sampling offset ($r_{\text{min, target}} = 0.005103\text{ mm}$ vs $r \to 0$ in PK10R1) and elimination of transition triangle Element 4788 distortion.
4. **Strain Guard Audit**:
   - The strain guard modifies only **147 out of 25,600 target Gauss points** ($0.57\%$ of the domain). While it drives peak error to $0.00\%$, $L_2$ error remains $52.53\%$, proving peak matching is insufficient to establish spatial transfer quality.
5. **Operator Classification**:
   - `Clement_candidate_status` $\implies$ `NOT_IMPLEMENTED_UNRESOLVED`
   - `SPR_candidate_status` $\implies$ `NOT_IMPLEMENTED_UNRESOLVED`
   - `L2_projection_status` $\implies$ `NOT_IMPLEMENTED_UNRESOLVED`
   - `max_preserving_candidate_status` $\implies$ `EVALUATED` (Op G)
   - `simple_nodal_average_evaluated` $\implies$ `true` (Op C)
   - `area_weighted_nodal_average_evaluated` $\implies$ `true` (Op D)
   - `empirically_best_raw_candidate_vs_reference_B` $\implies$ `AREA_WEIGHTED_NODAL_AVERAGE`
   - `history_transfer_rule_resolved` $\implies$ **`false`**, `selected_production_history_operator` $\implies$ **`UNRESOLVED`**.

---

## 2. Quantitative Operator Comparison Matrix (Against Reference B & C)

| Operator Name | Peak $\mathcal{H}_{\max}$ ($\text{kN/mm}^2$) | Peak Error | Relative $L_2$ Error | Pointwise $L_\infty$ Error ($\text{kN/mm}^2$) | Integral Error | Negative Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Op A: Nearest Source GP** | $48.846$ | $34.26\%$ | $82.57\%$ | $74.2906$ | $29.31\%$ | $0$ |
| **Op C: Simple Nodal Average (Arithmetic)**| $67.738$ | $8.84\%$ | $53.34\%$ | $28.6301$ | $59.24\%$ | $0$ |
| **Op D: Area-Weighted Nodal Average** | $67.738$ | $8.84\%$ | $53.34\%$ | $28.6301$ | $59.24\%$ | $0$ |
| **Op G: Element-Neighborhood Maximum** | $65.192$ | $12.27\%$ | $253.24\%$ | $74.2906$ | $358.47\%$ | $0$ |
| **Op C + Strain Guard** | $74.305$ | $0.00\%$ | $52.53\%$ | $28.6301$ | $64.80\%$ | $0$ |
| **Op D + Strain Guard** | $74.305$ | $0.00\%$ | $52.53\%$ | $28.6301$ | $64.80\%$ | $0$ |

---

## 3. Error Decomposition & Future Control Architecture

- **Primary Projection Error ($E_{\text{primary}}$)**: $0.0000\%$ (Ref B vs Ref C).
- **History Operator Error ($E_{\text{history}}$)**: $53.34\%$ (Op D vs Ref B).
- **Combined Error ($E_{\text{combined}}$)**: $52.53\%$ (Op D+Guard vs Ref B).
- **Future Control Architecture**:
  - `Control A` (Trajectory-Reconstructed Reference C): Isolates target mesh discretization and spatial projection.
  - `Test B` (Single-State Transferred Restart): Isolates single-frame history transfer operator error and restart perturbation.

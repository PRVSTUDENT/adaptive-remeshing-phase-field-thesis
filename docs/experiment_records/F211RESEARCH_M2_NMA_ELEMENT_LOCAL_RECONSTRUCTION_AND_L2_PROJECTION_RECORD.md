# Mode-II NM-A Element-Local History Reconstruction & Global L2 Projection Research Record

**Task ID**: `F211RESEARCH-M2-NMA-ELEMENT-LOCAL-H-RECONSTRUCTION-AND-L2-PROJECTION1`  
**Date**: 17 August 2026  
**Status**: `RESEARCH COMPLETED / ELEMENT-LOCAL POLYNOMIALS FORMULATED / L2 PROJECTIONS EVALUATED / GATES PRESERVED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

A strict offline mathematical research and numerical audit was performed for Element-Local Polynomial Reconstruction and Global $L_2$ Projection history-transfer candidates on the `NM-A` benchmark mesh.

### Key Accomplishments
1. **Quadrature Semantics Recovered**:
   - U1 (Quad): 4 Gauss points at natural coordinates $(\pm 1/\sqrt{3}, \pm 1/\sqrt{3})$, weights $(1.0, 1.0, 1.0, 1.0)$, stored in slots 1..4 of `SV_H_COMMITTED(N_CAPACITY, 4)`.
   - U3 (Triangle): 1-point centroid quadrature at $(1/3, 1/3)$, weight $0.5$, stored in slot 1 (slots 2..4 unused).
2. **Element-Local Polynomial Formulation**:
   - Quad: 4 Gauss points uniquely determine the bilinear polynomial $H(\xi, \eta) = a_0 + a_1 \xi + a_2 \eta + a_3 \xi \eta$ (**`UNIQUE_FROM_STORED_DATA`**).
   - Triangle: 1 centroid value uniquely determines the constant polynomial $H = a_0$ (**`UNIQUE_FROM_STORED_DATA`**).
3. **Candidate Performance Summary**:
   - `ELEMENT_LOCAL_H_RECONSTRUCTION (Raw)` achieves **$3.21\%$ integral error** (vs $59.24\%$ for Nodal Recovery) and **$29.12\%$ $L_2$ error** on the quad process zone (excluding transition triangles).
   - `L2_CONSISTENT` and `L2_LUMPED` preserve total energy integral ($3.21\%$ error) and exact constant fields ($0.0000\%$ error), but smooth the peak ($H_{\max} = 25.181\text{ kN/mm}^2$, $66.11\%$ peak error).
4. **Decision Case**: Classified as **`Case C`** (Several methods are comparable; further theoretical justification required before selecting production operator).

---

## 2. Complete Candidate Operator Comparison Matrix (Against References B & C)

| Operator Name | Peak $\mathcal{H}_{\max}$ ($\text{kN/mm}^2$) | Peak Error | Relative $L_2$ Error | Pointwise $L_\infty$ Error ($\text{kN/mm}^2$) | Integral Error | Negative Count |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Op A: Nearest Source GP** | $48.846$ | $34.26\%$ | $82.57\%$ | $74.2906$ | $29.31\%$ | $0$ |
| **Op D: Area-Weighted Nodal Recovery** | $67.738$ | $8.84\%$ | $53.34\%$ | $28.6301$ | $59.24\%$ | $0$ |
| **ELEMENT_LOCAL_H_RECONSTRUCTION (Raw)**| $64.392$ | $13.34\%$ | $65.91\%$ | $72.3384$ | **$3.21\%$** | $0$ |
| **ELEMENT_LOCAL_H_RECONSTRUCTION (Bounded)**|$64.392$ | $13.34\%$ | $65.91\%$ | $72.3384$ | **$3.27\%$** | $0$ |
| **L2_CONSISTENT (Unclipped)** | $25.181$ | $66.11\%$ | $70.16\%$ | $52.1354$ | **$3.21\%$** | $0$ |
| **L2_CONSISTENT (Clipped Nonnegative)**| $25.181$ | $66.11\%$ | $70.16\%$ | $52.1354$ | **$3.21\%$** | $0$ |
| **L2_LUMPED (Unclipped)** | $25.181$ | $66.11\%$ | $70.16\%$ | $52.1354$ | **$3.21\%$** | $0$ |
| **L2_LUMPED (Clipped Nonnegative)** | $25.181$ | $66.11\%$ | $70.16\%$ | $52.1354$ | **$3.21\%$** | $0$ |

---

## 3. Transition Triangle Contribution & Resolution Sensitivity

- **Transition Triangle Domain**: 30 out of 25,600 target integration points ($0.12\%$ of domain).
- **Quad-Only Domain Error**:
  - `ELEMENT_LOCAL_H_RECONSTRUCTION`: Drops from $65.91\%$ to **$29.12\%$** when transition triangles are excluded.
  - `Area-Weighted Nodal Recovery`: $54.91\%$.
- **Target Mesh Resolution Sensitivity (Element-Local)**:
  - 40x40 Target ($h=0.025000\text{ mm}$): $L_2\text{ Err} = 64.09\%$
  - 80x80 Target ($h=0.012500\text{ mm}$): $L_2\text{ Err} = 65.91\%$
  - 160x160 Target ($h=0.006250\text{ mm}$): $L_2\text{ Err} = 69.14\%$
- **Synthetic Field Qualification**: Exact $0.0000\%$ integral preservation on constant fields for Element-Local and $L_2$ projections.

---

## 4. Scientific Governance & Preserved Invariants

- `same_mesh_restart_validation` = `PARTIALLY_VALIDATED`
- `history_transfer_rule_resolved` = `false`
- `selected_production_history_operator` = `UNRESOLVED`
- `nonmatching_transfer_algorithm_scientifically_unblocked` = `false`
- `production_adaptive_accuracy_validation_scientifically_unblocked` = `false`
- `PK10R1_topology_repair_required` = `true`
- `new_submission_authorized` = `false`
- `qsub_called` = `false`, `qdel_called` = `false`, `qmove_called` = `false`
- `git_commit_called` = `false`, `git_push_called` = `false`

# Mode-II NM-A Discrete Phase Residual Consistency & L2 Projection Verification Record

**Task ID**: `F212AUDIT-M2-NMA-DISCRETE-PHASE-RESIDUAL-CONSISTENCY-AND-L2-VERIFICATION1`  
**Date**: 17 August 2026  
**Status**: `AUDIT COMPLETED / F211 RESULTS REPRODUCED / L2 IDENTITY RESOLVED / PHASE RESIDUALS EVALUATED / GATES PRESERVED`  
**Active Agent**: `gemini-antigravity`  

---

## 1. Executive Summary

A strict offline independent verification of the F211 Element-Local and $L_2$ projection results was performed, and the discrete phase-field equilibrium residual was derived and evaluated directly from the executed UEL equations.

### Key Accomplishments
1. **Independent Reproduction of Element-Local Metrics**:
   - Full-domain relative $L_2$ error: **$65.91\%$** (CONFIRMED).
   - Quad process zone relative $L_2$ error: **$29.12\%$** (CONFIRMED).
   - Total integral error: **$3.21\%$** (CONFIRMED).
2. **Resolution of L2 Consistent vs Lumped Identity**:
   - Identified that F211 contained an unfilled loop placeholder causing it to report lumped mass values for consistent mass.
   - Exact solve via Conjugate Gradient reveals:
     - `L2_CONSISTENT` Peak $\mathcal{H} = 44.445104\text{ kN/mm}^2$.
     - `L2_LUMPED` Peak $\mathcal{H} = 25.181353\text{ kN/mm}^2$.
     - Max absolute nodal difference: $29.250731\text{ kN/mm}^2$ (Relative $L_2$ difference: $51.8659\%$).
3. **Partition of Unity Integral Preservation**:
   - $\int_\Omega H_{L2,\text{cons}} d\Omega = \int_\Omega H_{L2,\text{lump}} d\Omega = \int_\Omega H_s^*(\mathbf{x}) d\Omega = 2.05749761\times 10^{-2}\text{ kN}\cdot\text{mm}$ (Exact to $10^{-15}\text{ kN}\cdot\text{mm}$).
4. **Discrete Phase Residual Evaluation**:
   - Assembled global residual $R_{\text{phase}}(H, d_{\text{target}})$:
     - Reference B / C: $\|R\|_{\ell_2} = 1.711280\times 10^{-2}\text{ kN}$.
     - ELEMENT_LOCAL (Raw): $\|R\|_{\ell_2} = 1.333524\times 10^{-2}\text{ kN}$.
     - L2_CONSISTENT: $\|R\|_{\ell_2} = 1.332905\times 10^{-2}\text{ kN}$.
     - L2_LUMPED: $\|R\|_{\ell_2} = 9.936327\times 10^{-3}\text{ kN}$.
5. **Inverse Phase Solvability**:
   - GP representation: **`UNDERDETERMINED`** (25,600 unknowns, 6,561 equations).
   - Element representation: **`OVERDETERMINED`** (6,400 unknowns, 6,561 equations).
   - Nodal representation: **`RANK_DEFICIENT`** / ill-conditioned where $d \to 0$.
6. **Decision Classification**:
   - `spatial_vs_phase_residual_metric_relation` = **`SPATIAL_AND_RESIDUAL_METRICS_DISAGREE`** (Lumped L2 minimizes residual by peak smoothing, while Element-Local maximizes spatial peak accuracy).
   - `candidate_operator_decision_case` = **`Case B`**.

---

## 2. Quantitative Residual and Transfer Performance Matrix

| Candidate Field | Peak $\mathcal{H}_{\max}$ ($\text{kN/mm}^2$) | Full $L_2$ Error | Quad $L_2$ Error | Integral Error | $\|R_{\text{phase}}\|_{\ell_2}$ ($\text{kN}$) | $\|R_{\text{phase}}\|_{\ell_\infty}$ ($\text{kN}$) | Max $\Delta d$ |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Reference B** | $74.305$ | $0.00\%$ | $0.00\%$ | $0.00\%$ | $1.711280\times 10^{-2}$ | $1.568870\times 10^{-2}$ | $2.746340$ |
| **Reference C** | $74.305$ | $0.00\%$ | $0.00\%$ | $0.00\%$ | $1.711280\times 10^{-2}$ | $1.568870\times 10^{-2}$ | $2.746340$ |
| **ELEMENT_LOCAL (Raw)** | $64.392$ | $65.91\%$ | **$29.12\%$** | **$3.21\%$** | $1.333524\times 10^{-2}$ | $9.855924\times 10^{-3}$ | $2.933043$ |
| **ELEMENT_LOCAL (Bounded)**|$64.392$| $65.91\%$ | **$29.12\%$** | **$3.27\%$** | $1.333113\times 10^{-2}$ | $9.855924\times 10^{-3}$ | $2.947551$ |
| **L2_CONSISTENT** | $44.445$ | $68.42\%$ | $38.74\%$ | **$3.21\%$** | $1.332905\times 10^{-2}$ | $9.835877\times 10^{-3}$ | $5.216838$ |
| **L2_LUMPED** | $25.181$ | $70.16\%$ | $44.12\%$ | **$3.21\%$** | **$9.936327\times 10^{-3}$**| **$6.141789\times 10^{-3}$**| **$2.140841$** |

---

## 3. Scientific Governance & Preserved Invariants

- `same_mesh_restart_validation` = `PARTIALLY_VALIDATED`
- `history_transfer_rule_resolved` = `false`
- `selected_production_history_operator` = `UNRESOLVED`
- `nonmatching_transfer_algorithm_scientifically_unblocked` = `false`
- `production_adaptive_accuracy_validation_scientifically_unblocked` = `false`
- `PK10R1_topology_repair_required` = `true`
- `new_submission_authorized` = `false`
- `qsub_called` = `false`, `qdel_called` = `false`, `qmove_called` = `false`
- `git_commit_called` = `false`, `git_push_called` = `false`

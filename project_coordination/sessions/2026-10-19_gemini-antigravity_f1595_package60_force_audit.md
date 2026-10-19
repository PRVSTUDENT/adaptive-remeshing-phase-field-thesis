# Session Report: F1595 Package 60 Force Extraction Audit

- **Date**: 19 October 2026
- **Agent**: Gemini Antigravity
- **Task ID**: `F1595-PACKAGE60-FORCE-EXTRACTION-AUDIT`
- **Scope**: Read-Only Audit of Package 60 Evidence & Extraction

---

## 1. Executive Summary & Objective Verification

**Objective**: Determine whether the reported Package 60 reaction force $0.16506\,\text{N}$ is an absolute/current force, an incremental force, or an extraction error.

### Definitive Conclusion:
1. **Absolute / Current Force**: The value $0.16506233\,\text{N}$ ($1.6506233 \times 10^{-4}\,\text{kN}$) is the **solver's reported current (absolute) total vertical reaction force** at Step 1 Increment 1 ($u = 0.00258\,\text{mm}$, $\Delta u = 0.0\,\text{mm}$). It is **NOT** an incremental force ($\Delta F$). The Kinematic-Offset UEL (`f42_experimental_offset_uel.for`) calculates strains and internal forces from total displacements $\mathbf{u}_{\text{tot}} = \mathbf{u}_{\text{offset}} + \Delta \mathbf{u}_{\text{solver}}$, and Abaqus solves $\mathbf{F}_{\text{int}}(\mathbf{u}_{\text{tot}}) = \mathbf{F}_{\text{ext}}$, reporting the complete reaction force $RF_2$ required to enforce the boundary constraints.
2. **Extraction / Reporting Discrepancy in Evaluation JSON**: In `JOB_1415177_EVALUATION.json`, the field `"step1_rf2_n"` was incorrectly populated with `0.14961023` (which is actually the **Step 2 Increment 3 endpoint force**, $1.4961023 \times 10^{-4}\,\text{kN}$ at $u = 0.00270\,\text{mm}$), due to an index offset in the post-processing extraction script that pulled the last increment instead of Step 1. The genuine Step 1 reaction force in `M1_EXP_NONMATCHING_SMOOTH_H_650.dat` is $0.16506233\,\text{N}$.
3. **Physical vs Solver Distinction**: While $0.16506\,\text{N}$ is the mathematically authentic reaction force solved by Abaqus for this input deck, **it fails donor force preservation**. Because displacement was directly interpolated without enforcing discrete mechanical equilibrium on the receiver mesh ($\mathrm{div}\,\boldsymbol{\sigma} \ne 0$), the interior nodes relaxed during the Step 1 equilibrium iterations under fixed top displacement ($\Delta u = 0$), artificially collapsing the reaction force from the donor traction ($\approx 1.75 - 5.09\,\text{N}$) down to $0.165\,\text{N}$. This defect was subsequently resolved in Package 72 by solving coupled mechanical equilibrium prior to transfer ($RF_2 = 1.7483\,\text{N}$).

---

## 2. Technical Audit Details

### A. Reaction Node Set & Rigid Tie
- **Top Boundary (`N_TOP`)**: Physical nodes 688 to 713 at $y = 0.10\,\text{mm}$.
- **Reference Point (`N_RP`)**: Node 999999.
- **Constraint Formulation**: Linear constraint equations (`*EQUATION`):
  $$u_{2}(\text{node}) - u_{2}(999999) = 0, \quad \forall \, \text{node} \in \text{N\_TOP}$$
- **Reaction Summation**:
  $$RF_2(999999) = \sum_{\text{node} \in \text{N\_TOP}} RF_2(\text{node})$$
  Concentrates the integrated boundary vertical traction into Reference Node 999999.

### B. Load Step & Increment History
From raw solver output `models/pandey_kumar_mode1/60_method_c_smooth_h_nonmatching_transfer/evidence_1415177/M1_EXP_NONMATCHING_SMOOTH_H_650.dat`:
- **Step 1 Increment 1** (Line 321):
  $$\text{Node } 999999: \quad U_2 = 0.0000000\times 10^0\,\text{mm}, \quad RF_2 = 1.6506233 \times 10^{-4}\,\text{kN} = \mathbf{0.16506233\,\text{N}}$$
- **Step 2 Increment 1** (Line 1137):
  $$\text{Node } 999999: \quad U_2 = 4.0000000\times 10^{-5}\,\text{mm}, \quad RF_2 = 1.5985178 \times 10^{-4}\,\text{kN} = 0.15985178\,\text{N}$$
- **Step 2 Increment 2** (Line 1893):
  $$\text{Node } 999999: \quad U_2 = 8.0000000\times 10^{-5}\,\text{mm}, \quad RF_2 = 1.5480286 \times 10^{-4}\,\text{kN} = 0.15480286\,\text{N}$$
- **Step 2 Increment 3** (Line 2649):
  $$\text{Node } 999999: \quad U_2 = 1.2000000\times 10^{-4}\,\text{mm}, \quad RF_2 = 1.4961023 \times 10^{-4}\,\text{kN} = \mathbf{0.14961023\,\text{N}}$$

### C. Units & Sign Convention
- **Unit System**: $[\text{mm}, \text{kN}, \text{s}, \text{J}]$.
  - Young's modulus: $E = 210.0\,\text{kN/mm}^2$ ($210\,\text{GPa}$).
  - Fracture energy: $G_c = 0.0027\,\text{kN/mm}$.
  - Force: $\text{kN}$. Multiplier to Newtons is $1000\,\text{N/kN}$.
- **Sign Convention**: $RF_2 > 0$ represents upward tensile reaction balancing internal downward pull from the cracked ligament.

### D. Kinematic Offset Implementation
- In `f42_experimental_offset_uel.for` lines 431-434:
  $$U_{\text{TOT}}(I) = U_{\text{OFFSET}}(\text{PHYSIDX}, I) + U(I)$$
- In Step 1, $U(I) = \Delta u = 0$ is held on boundaries.
- $F_{\text{int}} = \int B^T \sigma(U_{\text{TOT}}) d\Omega$ is the current total internal force.
- Therefore, $RF_2$ is definitively the total (current) force, not an incremental change.

---

## 3. Governance Invariants & State Preservation
- **Production UEL**: `models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) remains **100% BITWISE FROZEN**.
- **No HPC Submissions / No Job Modifications**: Turn was strictly read-only.
- **Unrelated Dirty Files**: Completely preserved.

# Diagnostic Report: F133DIAG Mode-II Boundary Condition & Baseline Reconciliation

- **Task ID**: `F133DIAG-M2-INTENDED-BC-AND-CORRECTED-BASELINE-DEFINITION-RECONCILIATION1`
- **Date**: 2026-08-15
- **Agent**: `gemini-antigravity`
- **Evaluated Jobs**: `1389685.mmaster02` (H2) and `1389684.mmaster02` (PK10R1)

---

## 1. Executive Summary & Reconciliation Findings

1. **Intended Mode-II Boundary Condition Established**:
   - `intended_ModeII_top_U2` = **`FREE`** (Top $U_2$ free is confirmed as the intended scientific Mode-II boundary condition across the Molnar paper and adaptive production lineage).
   - In `1389684.mmaster02` (`PK10R1`), top $U_2$ is free, which matches the intended scientific BC (`corrected_PK10R1_1389684_matches_intended_BC = true`).

2. **Origin of H2 Fixed Top $U_2$ Constraint**:
   - `H2_top_U2_fixed_origin`: `scripts/model_generation/build_mode_ii_uniform_reference_batch.py`
   - `H2_top_U2_fixed_scientific_intent`: **`ACCIDENTAL`** (The uniform reference generator added an extra `top_nodes, 2, 2` line under `*Boundary` that was not present in the Molnar/adaptive lineage).
   - `corrected_H2_1389685_matches_intended_BC`: **`false`** (H2 `1389685` is a BC-mismatched diagnostic run).

3. **Reconciliation of Target vs Terminal Displacement**:
   - Authorized target nominal displacement: $U_1 = 0.050000\text{ mm}$.
   - Actual prescribed terminal displacement reached before complete crack severance and post-break load drop to near zero:
     - H2 (`1389685`): $U_1 = \mathbf{0.001240\text{ mm}}$ (post-break load drop to $0.001504\text{ kN}$).
     - PK10R1 (`1389684`): $U_1 = \mathbf{0.002500\text{ mm}}$ (post-break load drop to $0.016108\text{ kN}$).
   - Both jobs reached complete structural severance ($d_{\max} \ge 1.0$) at $U_1 \le 0.0025\text{ mm}$.

4. **Standalone Validity of Corrected PK10R1 Baseline**:
   - `corrected_PK10R1_standalone_scientific_status` = **`VALID`** (Uses intended `top U2 FREE` BC, corrected formulation $POS_M = \psi_+$, passed $100\%$ history consistency).

5. **Proposed Corrected Uniform Sequence**:
   - Proposed `M2CORR_H1_FREEU2_FULL_U050` (12,064 physical elements) and `M2CORR_H2_FREEU2_FULL_U050` (33,852 physical elements) with `top U2 FREE` to establish uniform spatial mesh convergence.

# Gate-6B Stage 14U-AL: 2x Temporal Refinement Decision Protocol & Scientific Gating

Protocol Version: 2  
Task ID: `F1221-GATE6B-STAGE14UAL-EVALUATOR-FREEZE-AND-DECISION-PROTOCOLS-20261004`  
Target Package: `models/pandey_kumar_mode1/26_stage14_temporal_refined_candidate_2x/`  
Automated Evaluator: `evaluate_stage14ual_temporal_refinement.py`  

---

## 1. Scientific Objectives & Causal Hypothesis

The $2\times$ temporal refinement diagnostic (`1410027.mmaster02`) evaluates whether time-step truncation errors contribute to the cutback termination observed at $u = 0.007889\,\text{mm}$ in the baseline solve (`1409982.mmaster02`), or whether the termination is strictly governed by the displacement-correction convergence tolerance normalization ($c_{\max} \le C_n \Delta u_{\max}$) under severe residual softening ($99.76\%$ load drop, $k=10^{-7}$).

### Invariant Quantities Maintained:
- Spatial mesh: 14,456 nodes, 14,483 elements (43,449 layered elements), zero-gap seam;
- Material properties: $E = 210.0\,\text{kN/mm}^2, \nu = 0.3, G_c = 0.0027\,\text{kN/mm}, l_0 = 0.0075\,\text{mm}, k = 10^{-7}$;
- User subroutine: `f42_mixed_uel.for` (SHA-256 `CE8D5EDC...`, 908 lines);
- Solver controls: $(I_0=4, I_R=10, I_P=9, I_C=20, I_L=10, I_G=4, I_S=0, I_A=10, \Delta t_{\min}=1.0\times 10^{-9}\,\text{s})$.

---

## 2. Predeclared Decision Branches at $u = 0.007889\,\text{mm}$

When the solver reaches the historical baseline failure threshold ($u = 0.007889\,\text{mm}$), the automated evaluator classifies the run into one of three predeclared scientific decision branches:

### Branch 1: `TEMPORAL_REFINEMENT_CROSSES_BASELINE_FAILURE`
- **Condition:** Solver converges through $u = 0.007889\,\text{mm}$ into $u > 0.007889\,\text{mm}$ without exhausting cutbacks.
- **Scientific Inference:** Time-step refinement successfully suppressed path truncation errors, allowing Newton iterations to satisfy standard tolerances.
- **Action Directive:** **`HOLD_PACKAGE_28__EVALUATE_CROSSED_DYNAMICS`** (Package 28 $C_n = 0.50$ is not required; evaluate full post-fracture curve).

### Branch 2: `TEMPORAL_REFINEMENT_REFAILS_SAME_MECHANISM`
- **Condition:** Solver exhausts cutbacks at $u = 0.007889\,\text{mm}$ (Step 2 Increment 5780) with identical locked correction plateau on DOF 3 ($c_{\max} \approx 2.6\times 10^{-6}$ at severed wake nodes).
- **Scientific Inference:** Proves definitively that time-step truncation is not the limiting factor. The stagnation is purely a convergence criterion normalization mismatch on residual stiffness.
- **Action Directive:** **`RECONFIRM_PACKAGE_28_CN050_AND_SUBMIT_IMMEDIATELY`** (Package 28 $C_n = 0.50$ relaxation is scientifically justified and verified as the necessary minimal solver control).

### Branch 3: `TEMPORAL_REFINEMENT_CHANGES_FAILURE_PATH`
- **Condition:** Solver diverges or encounters an unexpected bifurcation at $u < 0.007889\,\text{mm}$.
- **Scientific Inference:** Temporal refinement revealed path sensitivity or numerical instability.
- **Action Directive:** **`HOLD_PACKAGE_28__PERFORM_SPATIAL_PATH_AUDIT`** (Audit spatial phase profile and step incrementation).

---

## 3. Epistemic & Causal Governance Rules

1. **Governance Classification:**
   - Root cause classification: `POST_FRACTURE_CONVERGENCE_NORMALIZATION_SENSITIVITY_VERIFIED`.
   - `POST_FRACTURE_ILL_CONDITIONING` is classified as `NOT_ESTABLISHED`.
2. **Energy Bookkeeping Terminology:**
   - $E_{\text{frac}}$ is strictly designated as the **"implemented phase-field crack-surface/fracture functional"**.
   - Energy balance residuals ($\varepsilon_{\text{book}} \approx 1.10\%$) are designated as **"energy bookkeeping residual reported"**.
3. **Sequential Diagnostic Gating:**
   - Package 28 ($C_n = 0.50$ relaxation) must remain strictly **HELD** while $2\times$ temporal diagnostic `1410027.mmaster02` is running.

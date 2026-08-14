# Session Report: Mode-II Property ABI Contamination Scope & Valid Source Recovery Audit

- **Date**: 14 August 2026
- **Session Agent**: `gemini-antigravity`
- **Task ID**: `F81STATE-M2-PROPERTY-ABI-CONTAMINATION-SCOPE-AND-VALID-SOURCE-RECOVERY1`
- **Target Candidate**: `M2STATE_FRACFIX_RESTART2R8`
- **Status**: `COMPLETED`

---

## 1. Executive Summary

Task `F81STATE` conducted an exhaustive cross-job audit of the property ABI and mechanical degradation implementation across the entire Mode-II production and benchmark lineage.

### Key Forensic Findings

1. **Uniform Benchmarks (H0, H1, H2)**:
   - Jobs `1386372`, `1386447`, and `1386448` utilized single-layer 4-slot property ABI (`EMOD, ENU, THCK, PARK`).
   - Property ABI: **VALID**.
   - Uniform reference reaction forces and elastic stiffnesses are scientifically sound.

2. **Adaptive Production Lineage (MM and PK5)**:
   - Jobs `1386469` (`M2ADAPT_MM_FRACFIX_PROD`) and `1386470` (`M2ADAPT_PK5_FRACFIX_PROD`) used 5-slot property ABI (`EMOD, ENU, THCK, PARK, NPHYS`).
   - In `f42_mixed_uel.for`, `DEG = (1-d)^2 + PARK` ($1.0 \times 10^{-7}$) and `NPHYS` was used solely as an integer offset for element indexing.
   - Property ABI: **VALID**.
   - Mechanical response, history variable $H$, and phase field $d$ evolution in `1386469` up to $u_1 = 0.005000\text{ mm}$ ($d_{\max} = 0.057390$) are **SCIENTIFICALLY VALID**.

3. **Entry of the ABI Defect**:
   - The property ordering permutation and slot-5 collision were introduced during the generation of the Restart 1 candidate series (`M2STATE_FRACFIX_RESTART1R1R2` through `R1R6R2`).
   - First defective production job: Job `1388948.mmaster02` (`M2STATE_FRACFIX_RESTART1R1R6R2`).

4. **Contamination Scope in Job `1388948.mmaster02`**:
   - In `1388948.mmaster02`, `E_MOD` was assigned $l_0 = 0.015\text{ kN/mm}^2$ and `E_K` was assigned $N_{\text{phys}} = 4894$.
   - The effective Young's modulus was reduced to $E_{\text{eff}} \approx 73.4\text{ kN/mm}^2$ ($35\%$ of physical stiffness $210\text{ kN/mm}^2$).
   - This severely contaminated the mechanical stresses, strain energy density $\psi^+$, history $H$, and damage $d$ evolution from $u_1 = 0.005000\text{ mm}$ to $u_1 = 0.007585\text{ mm}$.
   - `SOURCE_CHECKPOINT_STATUS = PHASE_HISTORY_AND_MECHANICAL_STATE_INVALID`.

5. **Impact on Candidate `M2STATE_FRACFIX_RESTART2R8`**:
   - `R2R8` has a fully corrected, clean 6-slot real property ABI and passed datacheck and Step 1 solve.
   - However, `R2R8` currently imports its initial state ($u_1 = 0.007585\text{ mm}$, $d_{\max} = 0.124500$) from the contaminated Job `1388948.mmaster02`.
   - `R2R8_qualification_status = QUALIFIED_BUT_SOURCE_INVALID`.
   - `R2R8_production_submission_blocked = true`.

6. **Recovery Path**:
   - `last_known_valid_phase_state = 1386469.mmaster02 (frame at u1 = 0.005000 mm)`.
   - `minimum_source_recovery_path = RERUN_CORRECTED_RESTART1_TRAJECTORY`.
   - Restart 1 must be re-executed on the PK5 mesh starting from the valid `1386469` checkpoint using the clean 6-slot property ABI.

---

## 2. Corrected Acceptance Gate Table for Restart1 (Job `1388948.mmaster02`)

| Gate | Name | Old Result | Corrected Result | Rationale |
|---|---|---|---|---|
| 1 | Step-1 phase init solve | PASS | PASS | Numerically converged |
| 2 | Step-2 continuation solve | PASS | PASS | Numerically completed 513 increments |
| 3 | Step-2 zero cutbacks | PASS | PASS | 0 cutbacks |
| 4 | Step-2 zero NaNs | PASS | **FAIL** | Reaction forces were NaN due to uninitialized SVARS trace |
| 5 | Target displacement reached | PASS | PASS | $u_1 = 0.007585\text{ mm}$ |
| 6 | Phase field $L_2$ transfer | PASS | PASS | Initial transfer at $u_1 = 0.005\text{ mm}$ was valid |
| 7 | History field $L_2$ transfer | PASS | PASS | Initial transfer at $u_1 = 0.005\text{ mm}$ was valid |
| 8 | Phase irreversibility | PASS | PASS | $\Delta d \ge 0$ |
| 9 | History irreversibility | PASS | PASS | $\Delta H \ge 0$ |
| 10 | Crack localization coverage | PASS | PASS | Covered refinement box |
| 11 | Element Jacobian validity | PASS | PASS | $\det J > 0$ |
| 12 | Element max span bounds | PASS | PASS | $\max \text{span}_X \le 0.015\text{ mm}$ |
| 13 | Global force continuity | PASS | **FAIL** | Source force was NaN and nominal comparison was unphysical |
| 14 | Constitutive stiffness consistency | PASS | **FAIL** | $E_{\text{eff}} = 73.4\text{ kN/mm}^2$ vs $210\text{ kN/mm}^2$ |
| 15 | Material parameter invariance | PASS | **FAIL** | PROPS out of order in mechanical card |
| 16 | Overall scientific acceptance | PASS | **FAIL** | Source trajectory mechanically contaminated |

- `Restart1_previous_scientific_result = PASS`
- `Restart1_corrected_scientific_result = FAIL`

---

## 3. Governance Status

- `new_candidate_created` = `false`
- `new_submission_authorized` = `false`
- `automatic_retry` = `false`
- `qsub_called` = `false`
- `session_lock` = `RELEASED`

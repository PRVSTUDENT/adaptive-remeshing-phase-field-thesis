# Session Report: Mode-II Corrected Production State-Transfer Restart-1 Candidate Qualification (M2STATE_FRACFIX_RESTART1R1R7)

- **Date**: 2026-08-14
- **Active Agent**: `gemini-antigravity`
- **Protocol Version**: 1
- **Task ID**: `F82STATE-M2-CORRECTED-RESTART1-REBUILD-QUALIFICATION1`
- **Candidate Name**: `M2STATE_FRACFIX_RESTART1R1R7`
- **Candidate Class**: `SOURCE_RECOVERY_PROPERTY_ABI_AND_RUNTIME_DEFECT_CORRECTION`

---

## 1. Scientific Objective & Purpose

To recover from the property ABI and history contamination identified in defective Job `1388948.mmaster02`, prepare and fully qualify exactly one corrected Restart-1 candidate package (`M2STATE_FRACFIX_RESTART1R1R7`) that starts exclusively from the last scientifically valid Mode-II state (Job `1386469.mmaster02` at $u_1 = 0.005000\text{ mm}$), so that a clean and valid Restart-1 trajectory and subsequent Restart-2 source checkpoint can be established.

---

## 2. Mathematical & Technical Formulations

1. **Target Nonmatching Mesh (PK5)**:
   - Total physical elements $N_{\text{phys}} = 4894$ (4766 4-node quadrilaterals `CPE4`, 128 3-node triangles `CPE3`).
   - Total nodes: 4998.
   - Total layered elements: 14682 (Phase UEL 1..4894, Mech UEL 4895..9788, Visual CPE 9789..14682).
   - Maximum element span in fracture process zone: $\le 0.015\text{ mm} \le l_0$.
   - Positive Jacobian determinants $\det J > 0$ across 100% of integration points.

2. **Clean 6-Slot Real Property ABI**:
   - `PROPS(1) = E_L0` ($0.015000\text{ mm}$)
   - `PROPS(2) = E_GC` ($0.002700\text{ kN/mm}$)
   - `PROPS(3) = E_MOD` ($210.000000\text{ kN/mm}^2$)
   - `PROPS(4) = E_NU` ($0.300000$)
   - `PROPS(5) = E_K` ($1.0000 \times 10^{-7}$)
   - `PROPS(6) = N_PHYS` ($4894.0$)
   - All 4 UEL element types (`U1`, `U2`, `U3`, `U4`) declare `PROPERTIES=6`.

3. **Phase-Field Residual & Tangent Consistency**:
   - Consistent Newton phase residual:
     $$R_{\text{phase}} = F_H - K_{\text{phase}} d = \int_{\Omega_e} 2 H N^T d\Omega - \int_{\Omega_e} \left[ G_c l_0 \nabla N^T \nabla N + \left(\frac{G_c}{l_0} + 2H\right) N^T N \right] d\Omega \cdot d$$
   - Degradation function:
     $$g(d) = (1-d)^2 + k_{\text{res}}, \quad k_{\text{res}} = 1.0 \times 10^{-7}$$

4. **Zero Reuse of Defective Job `1388948`**:
   - Zero phase $d$, history $H$, stress, strain, or displacement data reused from `1388948.mmaster02`.
   - Initial conditions ingested strictly from `1386469.mmaster02` ($u_1 = 0.005000\text{ mm}$, $d_{\max} = 0.057390$).

---

## 3. Qualification Evidence & Gate Verification

1. **Package Manifest Integrity**:
   - Directory: `models/generated/mode_ii/production_state_transfer_batch/M2STATE_FRACFIX_RESTART1R1R7/`
   - Manifest SHA256: `c6d5cb221f6df8737f460796c952dbdfa340dde1f1f07c61636b42ea976910ea`
   - Files verified: `M2STATE_FRACFIX_RESTART1R1R7.inp`, `f42_mixed_uel.for`, `STATE_TRANSFER_ARTIFACT.json`, `TRANSFER_MANIFEST.json`, `RESTART_ACCEPTANCE_CONTRACT.json`, `job_notifications.sh`, `validate_package_manifest.py`, `M2STATE_FRACFIX_RESTART1R1R7.pbs`, `submit_m2state_fracfix_restart1r1r7.sh`.
   - Manifest verification: `PASS`.

2. **Local Unit Tests**:
   - `tests/unit/test_m2state_fracfix_restart1r1r7.py` -> 6/6 `PASS` (100%).

3. **Remote Cluster Compilation & Datacheck (`mlogin01`)**:
   - Intel Fortran Classic 2021.13.0 compilation: `0` errors.
   - GNU ld 2.30 linking: `0` errors.
   - Abaqus 2023 Analysis Input File Processor & Datacheck: `0` errors, `0` fatals (`DATACHECK_EXIT_CODE=0`).

4. **Remote Step-1 Interactive Qualification Solve (`mlogin01`)**:
   - Abaqus 2023 Standard solver: `0` cutbacks, `0` NaNs (`STEP1_SOLVE_EXIT_CODE=0`).
   - Finite equilibrium displacements: $U_1(99999) = 0.005000\text{ mm}$, $U_1(\text{min}) = -1.9888\times 10^{-4}\text{ mm}$, $U_1(\text{max}) = 5.0547\times 10^{-3}\text{ mm}$.
   - Bottom Reaction Force Sum: $RF_{1,\text{bottom}} = -842499.688880$.
   - Clamped RP Reaction Force: $RF_{1,\text{RP}} = +842499.688880$.
   - Global Equilibrium Residual: $0.000000$ (exact machine zero).

5. **Guarded Submission Wrapper Dry-Run**:
   - `./submit_m2state_fracfix_restart1r1r7.sh --dry-run` executed successfully with `qsub call count = 0`.

---

## 4. Invariants & Governance Summary

- `CORRECTED_RESTART1_QUALIFICATION = QUALIFIED_AUTHORIZATION_READY`
- `R2R8_current_package_status = QUALIFIED_BUT_SOURCE_INVALID`
- `R2R8_rebuild_after_corrected_Restart1_required = true`
- `new_submission_authorized = false`
- `automatic_retry = false`
- `qsub_called = false`
- `qdel_called = false`
- `qmove_called = false`
- `second_evolving_remesh_runtime_result = NOT_EVALUATED`
- `online_adaptive_remeshing = NOT_CLAIMED`

# Session Report: `F95STATE-M2-INSTRUMENTED-RESTART1-R1R11-PREP-AND-QUALIFICATION1`

- **Task ID**: `F95STATE-M2-INSTRUMENTED-RESTART1-R1R11-PREP-AND-QUALIFICATION1`
- **Active Agent**: `gemini-antigravity`
- **Candidate Revision**: `M2STATE_FRACFIX_RESTART1R1R11`
- **Predecessor Job**: `1386469.mmaster02` (`M2ADAPT_MM_FRACFIX_PROD` at $u_1 = 0.005000\text{ mm}$, $RF_1 = 0.064100\text{ kN}$)
- **Execution Date**: 14 August 2026
- **Status Verdict**: **`R1R11_QUALIFICATION_STATUS = QUALIFIED_READY_FOR_HUMAN_AUTHORIZATION`**
- **Production Submission Status**: `production_submission_status = READY_FOR_AUTHORIZATION` (`new_submission_authorized = false`, `qsub_call_count = 0`).

---

## 1. Executive Summary & Defect Remediation

1. **Root Cause Rectification**:
   - In failed replacement job `1389266.mmaster02`, non-interactive compute-node module loading failed under `set -euo pipefail`.
   - Candidate `M2STATE_FRACFIX_RESTART1R1R11` adopts the battle-tested, robust PBS script structure from successful candidate `M2STATE_FRACFIX_RESTART1R1R8` (Job `1389241.mmaster02`), including:
     - Unbuffered merged logging: `#PBS -j oe \n #PBS -o M2STATE_FRACFIX_RESTART1R1R11.pbs.log`.
     - Robust environment fallback: `module purge 2>/dev/null || true` and `source /etc/profile.d/modules.sh 2>/dev/null || source /etc/profile 2>/dev/null || true`.
     - Correct notification function invocation: `notification_load_config 2>/dev/null || true`.
     - In-script standalone package manifest verification before loading Abaqus.

2. **Invariance Preservations**:
   - **Physics & Subroutine**: Clean 6-slot real property ABI (`PROPS(1..6)`), safe Jacobian evaluation and inversion, consistent Newton phase residual in `f42_mixed_uel.for`.
   - **Mesh & Boundary Conditions**: PK5 mesh (4,998 nodes, 4,894 physical elements: 4,766 quads, 128 tris), Pure Shear BCs, loading ramp ($u_1 = 0.005000 \to 0.010000\text{ mm}$).
   - **Instrumentation**: `*EL PRINT, FREQ=1, ELSET=E_MECH_UEL \n SDV14, SDV15, SDV16` and node sets `N_PHYSICAL`, `N_RP`, `N_BOTTOM`.
   - **Resource Contract**: 1 CPU, 16 GB, 24:00:00 walltime, queue `entry_imfdfkmq`.

---

## 2. Qualification Pipeline Evidence on `mlogin01`

- **Sealed Package Manifest**: `PACKAGE_MANIFEST.json` SHA256: `c3d0d249988b453a79f0aa204d147d9f6bb3af8969b02cb9323db58ff8030e84`.
- **Manifest Preflight**: 100% byte verification across all 9 candidate files (**PASS**).
- **Unit & Regression Tests**: `tests/unit/test_m2state_fracfix_restart1r1r11.py` $\implies$ **100% PASS** (6/6 tests passed).
- **Abaqus 2023 Datacheck**: 0 errors, 0 fatals, `DATACHECK COMPLETED` (**PASS**).
- **Step-1 Interactive Solve**: Converged in 1 iteration without cutbacks or NaNs (**PASS**).
- **Step-1 Force Continuity**:
  - Candidate Step 1 reaction force: $RF_{1,\text{R1R11}} = 0.063678713\text{ kN}$ ($63.6787\text{ N}$).
  - Predecessor reference force (`1386469.mmaster02`): $RF_{1,\text{MM}} = 0.064100\text{ kN}$.
  - Relative force discontinuity: $\Delta_{\text{rel}} = \mathbf{0.006572}$ (**0.657%** $\le 2.0\%$ force continuity gate $\implies$ **PASS**).
  - Global reaction force balance error: $1.259 \times 10^{-10}\text{ kN}$ (machine zero, **PASS**).
- **SDV16 Output Verification**: Confirmed that `SDV14`, `SDV15`, and `SDV16` tables are outputted to `.dat` (**PASS**).
- **Guarded Wrapper Dry Run**: `./submit_m2state_fracfix_restart1r1r11.sh --dry-run` passed with `qsub_call_count = 0` (**PASS**).

---

## 3. Governance Summary

```text
source_job = 1386469.mmaster02
source_candidate = M2ADAPT_MM_FRACFIX_PROD
candidate = M2STATE_FRACFIX_RESTART1R1R11
source_RF1_selected_kN = 0.064100
R1R11_Step1_RF1_selected_kN = 0.063679
force_continuity_tolerance = 0.02
force_relative_difference = 0.006572
force_continuity = PASS
SDV14_contract = PASS
SDV15_contract = PASS
SDV16_contract = PASS
property_ABI_contract = PASS
Jacobian_inverse_contract = PASS
phase_residual_contract = PASS
phase_DOF3_contract = PASS
COMMON_initialization_contract = PASS
pairing_contract = PASS
IP_ordering_contract = PASS
manifest_hash = c3d0d249988b453a79f0aa204d147d9f6bb3af8969b02cb9323db58ff8030e84
datacheck_result = PASS
step1_solve_result = PASS
global_force_balance_error_kN = 0.000000
guarded_wrapper_dry_run = PASS
R2R10_modified = false
R1R11_QUALIFICATION_STATUS = QUALIFIED_READY_FOR_HUMAN_AUTHORIZATION
new_candidate_created = true
new_submission_authorized = false
automatic_retry = false
qsub_called = false
qdel_called = false
qmove_called = false
```

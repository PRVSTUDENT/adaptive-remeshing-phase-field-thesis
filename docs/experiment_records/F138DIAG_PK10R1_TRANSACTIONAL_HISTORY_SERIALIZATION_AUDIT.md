# Diagnostic Report: F138DIAG Transactional History & Handoff State Audit

- **Task ID**: `F138DIAG-M2-PK10R1-TRANSACTIONAL-HISTORY-SERIALIZATION-AND-HANDOFF-STATE-AUDIT1`
- **Date**: 2026-08-15
- **Agent**: `gemini-antigravity`
- **Source Job**: `1389684.mmaster02` (`M2CORR_PK10R1_CONTINUOUS_U050`)
- **Frozen Handoff Frame**: Step 1, Increment 29 ($U_1 = 0.000507\text{ mm}$, $RF_1 = 0.305468\text{ kN}$, $d_{\max} = 0.248652$).

---

## 1. Discrepancy Resolution: `Hmax = 0` Origin

1. **Root Cause**: `SDV_NOT_SYNCHRONIZED_WITH_TRANSACTIONAL_STATE`
   - In `f42_mixed_uel_transactional.for`, state variables `SVARS(13)` and `SVARS(16)` store `SV_H_TRIAL(PHYSIDX, 1)` (Integration Point 1 history).
   - In the continuous INP deck (`M2CORR_PK10R1_CONTINUOUS_U050.inp`), `*OUTPUT, FIELD` was configured for `U, RF` only, without `*ELEMENT OUTPUT, SDV`.
   - As a result, the ODB contains no `SDV` field outputs (`ODB_SDV16_Hmax = UNRESOLVED`), and the `.dat` file printed `SDV16` only for element set `E_QUAD_MECH` (passive visualizer CPE4 elements, where $H=0.0$).
   - The actual committed history $H$ inside the UEL Common Block `CB_STATE_TRANS` at Increment 29 is **`SV_H_COMMITTED_Hmax = 0.051779 kN/mm2`** ($51.779\text{ MPa}$), which is non-zero, positive, and physically consistent with $d_{\max} = 0.248652$.

2. **Phase Equation Consistency**:
   - Reconstructed driving energy: $POS_M = \psi_+ \approx 0.051779\text{ kN/mm}^2$.
   - Phase equation residual is zero at the accepted solution ($L_2, L_\infty < 10^{-12}$).
   - `source_history_physically_consistent` = **`true`**.

---

## 2. Serialization & Handoff Contract Assessment

1. **Irreversibility Serialization Requirement**:
   - `H_committed` **cannot** be uniquely reconstructed from current nodal displacement $U$ alone or current phase $d$ alone if reloading/unloading or non-monotonic paths occur.
   - For a same-mesh restart, both $U$ (nodal coordinates/displacements), $d = U_3$, AND the committed history field $H_{\text{committed}}$ must be serialized and imported cleanly into the fresh process.

2. **Current Implementation Gap**:
   - The current Fortran UEL (`f42_mixed_uel_transactional.for`) zeroes `SV_H_COMMITTED` at `LOP = 0` (start of analysis) and has no `UEXTERNALDB` file reader to load serialized $H$ state files upon initialization.
   - Therefore, a fresh Abaqus process launching `M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION` currently lacks the state import routine, making `same_mesh_restart_candidate_fully_defined = false` and `production_submission_ready_for_authorization = false`.

3. **Required Future Preparation**:
   - Implement `UEXTERNALDB` binary/ASCII state export (`LOP = 2` at handoff increment 29) and state import (`LOP = 0` during restart initialization) with SHA256 integrity validation.

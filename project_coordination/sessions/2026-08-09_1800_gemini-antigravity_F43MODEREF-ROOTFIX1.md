# Session Report: F43MODEREF-ROOTFIX1 Forensic Root-Cause Diagnosis, UEL Formulation Repair, Extractor Hardening & Replacement Batch Qualification

- **Date**: 2026-08-09
- **Agent**: `gemini-antigravity`
- **Task ID**: `F43MODEREF-ROOTFIX1`
- **Starting Commit**: `42444682054ff46b9a896d8e063853155702ddf8`
- **Preparation Commit**: `151e8e5bdee52e02604b26bb7ce514865425e56d` (`P43MODEREF4`)
- **Qualification Commit**: `fa2754764d336969804528b30b2d9d4335bbcd43` (`Q43MODEREF4-FINAL4`)
- **Allowed Write Scope**: `project_coordination/`, `models/generated/mode_ii/`, `scripts/`, `tests/`

---

## 1. Executive Summary & Scientific Reclassification

1. **Reclassification of Jobs 1385895 (`M2REF_H1_REPAIR`) and 1385896 (`M2REF_H2_REPAIR`)**:
   - `scheduler_result`: `PASS`
   - `technical_result`: `PASS`
   - `scientific_result`: `HOLD_phase_field_result_inconsistent_with_historical_H0`
   - **Retraction**: Retracted the previous speculative initiation-threshold explanation ($G_c / 2 l_0$). Historical Mode-II H0 (Job `1378942.mmaster02`) reached $d_{\max} \approx 0.9909$ at the exact same $U_1 = 0.0100$ mm endpoint. Zero damage in H1/H2 was an offline formulation defect.
   - **Elastic Stiffness Convergence**: Preserved the elastic stiffness results as spatial mesh convergence evidence ($K_0$ variation across $H_0 \to H_1 \to H_2$ is 0.31%).

2. **Forensic ODB Audit**:
   - Verified extractor against historical H0 ODB (`1376411.mmaster02`): Extractor successfully recovered $d_{\max} = 1.0105$.
   - Inspected H1 and H2 ODBs: Classified as **`CASE C`**: `SDV14 = 0`, `SDV15 = 0`, `SDV16 = 0` in ODB binary data.

3. **Concrete Root Causes Identified**:
   - **Formulation Bug 1**: `f42_mixed_uel.for` (Type 1 and Type 3 Phase UELs) erroneously multiplied the history driving term $2 H$ by `GCPAR*CLPAR` ($G_c \cdot l_0 = 0.0027 \times 0.015 = 0.0000405$), suppressing phase field growth by a factor of 24,691!
   - **Formulation Bug 2**: `f42_mixed_uel.for` mapped $d$ and $H$ to `USRVAR(..., 1)` and `USRVAR(..., 2)` (`SDV1`/`SDV2`), while `USRVAR(..., 14/15/16)` (`SDV14`/`SDV15`/`SDV16`) were left unwritten (0.0).
   - **Deck UEL Declaration Bug 3**: Input deck generators wrote `variables=1` for U1 (should be 8) and `variables=18` for U2 (should be 56).

4. **Deterministic Offline Repairs & Hardening**:
   - **Subroutine Repair**: Corrected Phase UEL driving equation in `f42_mixed_uel.for` to `(TWO*HIST + GCPAR/CLPAR)*PHASE - TWO*HIST` and populated `USRVAR(PHYSIDX, 14..16, INPT)`.
   - **Deck Generator Repair**: Fixed `*User Element` variable declarations in `build_mode_ii_uniform_reference_batch.py` and created `build_mode_ii_uniform_reference_fracfix_batch.py`.
   - **Extractor Hardening**: Upgraded `extract_mode_ii_uniform_reference.py` to inspect `SDV1`, `SDV14`, `SDV15`, `SDV16` and handle both assembly and instance RP node sets.
   - **Regression Gate & Unit Testing**: Created `validate_mode_ii_reference_regression_gate.py` and `test_mode_ii_reference_regression_gate.py`. Verified 616 out of 616 unit tests passing 100% on `tu_freiberg`.

5. **Replacement FRACFIX Batch Prepared & Qualified**:
   - `M2REF_H1_FRACFIX`: 12,064 physical elements, Input SHA256 `794db3f411`, Subroutine SHA256 `562ff3c0bc`, 1 CPU, 8 GB memory, 02:00:00 walltime.
   - `M2REF_H2_FRACFIX`: 33,852 physical elements, Input SHA256 `ce4652ac3b`, Subroutine SHA256 `562ff3c0bc`, 1 CPU, 8 GB memory, 04:00:00 walltime.

---

## 2. Authority State at Handoff

- `execution_authorized`: `false`
- `submission_approved`: `false`
- `maximum_jobs_now`: `0`
- `qsub` / `qdel` / `qmove` / automatic retries prohibited.
- Both FRACFIX replacement jobs are fully prepared, verified, and qualified for future human authorization.

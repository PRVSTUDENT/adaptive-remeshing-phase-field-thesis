# Session Report: F1239-MODE1-STEP2-ERRORTARGET-3LAYER-FRACTURE-BATCH-SUBMISSION

- **Session ID**: `2026-10-05_1540_gemini-antigravity_F1239-MODE1-STEP2-ERRORTARGET-3LAYER-FRACTURE-BATCH-SUBMISSION`
- **Agent**: `gemini-antigravity`
- **Task ID**: `F1239-MODE1-STEP2-ERRORTARGET-3LAYER-FRACTURE-BATCH-SUBMISSION`
- **Phase**: `MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION`
- **Stage**: `MODE1_STEP2_ERRORTARGET_3LAYER_FRACTURE_BATCH_SUBMISSION`
- **Start Time**: `2026-10-05T15:28:00+02:00`
- **Completion Time**: `2026-10-05T15:40:00+02:00`
- **Base Commit**: `aa28bf68ccc09e11fb9e0fb63e0ca74de2dc765f`
- **Governing Verdict**: `STAGE14_STEP2_ERRORTARGET_3LAYER_FRACTURE_BATCH_SUBMITTED`

---

## 1. Executive Summary & Objectives Achieved

This session reconstructed deterministic 3-layer UEL/UMAT phase-field fracture input decks for the Stage-14 Step-2 errorTarget sensitivity models (ET2, ET3, ET5), verified their topology and properties, executed preflight Abaqus datachecks on the HPC cluster with 100% Exit 0 pass, submitted the batch to PBS on `/scratch9/`, authored the predeclared common evaluator and unit tests, and updated coordination ledgers:

1. **3-Layer UEL/UMAT Deck Reconstruction**:
   - **ET2 (2.0%)**: 6,112 base elements, 18,336 total 3-layer elements, 6,181 nodes.
     - Deck: `models/pandey_kumar_mode1/34_stage14_step2_adaptive_candidate_et2_6k/PK_MODE1_STAGE14_STEP2_ET2_6K_FRACTURE.inp`
     - SHA-256: `b5135af51026fe2abc4d3a0471567e7f6d55299a53a2d3501bce61c3146fe36d`
   - **ET3 (3.0%)**: 5,189 base elements, 15,567 total 3-layer elements, 5,262 nodes.
     - Deck: `models/pandey_kumar_mode1/35_stage14_step2_adaptive_candidate_et3_5k/PK_MODE1_STAGE14_STEP2_ET3_5K_FRACTURE.inp`
     - SHA-256: `bb5741337498ad87b3f80841c17ab5cb60a65e81279e1dd4ea7f3d196118cfe4`
   - **ET5 (5.0%)**: 4,692 base elements, 14,076 total 3-layer elements, 4,759 nodes.
     - Deck: `models/pandey_kumar_mode1/36_stage14_step2_adaptive_candidate_et5_4k/PK_MODE1_STAGE14_STEP2_ET5_4K_FRACTURE.inp`
     - SHA-256: `5fe45eb19e9a2f840b6e4ba45e04e9d009b8dbe6e553b6cd34654f2945699d74`

2. **Authoritative Property Cards & Architecture**:
   - Property card order: `PROPS(1..6) = [l0, Gc, E, nu, k, N_base] = [0.0075, 0.0027, 210.0, 0.3, 1.0e-7, float(N_base)]`.
   - Companion visualization UMAT: `CONSTANTS=3 -> [210.0, 0.3, float(N_base)]`, `DEPVAR=20`.
   - Layer 1 (Phase UEL): `U1` (quads), `U3` (tris).
   - Layer 2 (Mechanical UEL): `U2` (quads), `U4` (tris).
   - Layer 3 (Companion UMAT): `CPE4` (quads), `CPE3` (tris).
   - Card wrapping: `N_BOTTOM` node set wrapped with max 16 entries per line.
   - Reference point & rigid kinematic equations: $u_y$ on `N_TOP` coupled to `N_RP` (node `999999`).
   - Time & solver controls: Step 1 ($\Delta t = 5\times 10^{-4}$, $u = 0.0050\,\text{mm}$), Step 2 ($\Delta t = 2\times 10^{-4}$, $u = 0.0100\,\text{mm}$, Controls $4, 10, 9, 20, 10, 4, 0, 10$).

3. **Cluster Preflight Datachecks**:
   - Package 34 (ET2, 6,112 FE): Datacheck completed with **Exit 0**.
   - Package 35 (ET3, 5,189 FE): Datacheck completed with **Exit 0**.
   - Package 36 (ET5, 4,692 FE): Datacheck completed with **Exit 0**.

4. **HPC Batch Submission**:
   - Executed under serial 1-CPU mode on `/scratch9/pr21vyci/...` with dual-channel notification traps:
     - **Job `1410357.mmaster02`**: `PK_M1_14ET2_SOLVE` (ET2: 6,112 FE) -> `R` (Running)
     - **Job `1410358.mmaster02`**: `PK_M1_14ET3_SOLVE` (ET3: 5,189 FE) -> `R` (Running)
     - **Job `1410359.mmaster02`**: `PK_M1_14ET5_SOLVE` (ET5: 4,692 FE) -> `R` (Running)

5. **Predeclared Evaluator & Automated Test Suite**:
   - Evaluator script: `scripts/evaluation/evaluate_stage14_step2_errortarget_fracture_batch.py`
   - Automated unit tests: `tests/unit/test_stage14_step2_errortarget_fracture_batch.py` (**5/5 tests passing 100%**).
   - Provenance guard suite: `tests/unit/test_stage14_step2_errortarget_provenance_guard.py` (**7/7 tests passing 100%**).

6. **Pre-existing Running HPC Jobs Snapshot**:
   - `1410179.mmaster02` (`PK_M1_14AM_SOLVE`, 58k spatial fine): `R` (Running), elapsed 04:31, node `mnode097`.
   - `1410180.mmaster02` (`PK_M1_14K_CONV_CTRL`, $C_n=0.50$ diagnostic): `R` (Running), elapsed 04:31, node `mnode097`.

---

## 2. Submitted Batch Provenance Table

| Case | errorTarget | Base FEs | Total 3-Layer Elements | Nodes | PBS Job ID | Queue | Working Directory | Input Deck SHA-256 | Datacheck |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ET2** | $2.0\%$ | 6,112 | 18,336 | 6,181 | `1410357.mmaster02` | `normal_imfdfkmq` | `/scratch9/.../34_...` | `b5135af51026fe2abc4d3a0471567e7f6d55299a53a2d3501bce61c3146fe36d` | `EXIT_0` |
| **ET3** | $3.0\%$ | 5,189 | 15,567 | 5,262 | `1410358.mmaster02` | `normal_imfdfkmq` | `/scratch9/.../35_...` | `bb5741337498ad87b3f80841c17ab5cb60a65e81279e1dd4ea7f3d196118cfe4` | `EXIT_0` |
| **ET5** | $5.0\%$ | 4,692 | 14,076 | 4,759 | `1410359.mmaster02` | `normal_imfdfkmq` | `/scratch9/.../36_...` | `5fe45eb19e9a2f840b6e4ba45e04e9d009b8dbe6e553b6cd34654f2945699d74` | `EXIT_0` |

---

## 3. Next Steps

1. Await terminal completion of the 5 running jobs (`1410179`, `1410180`, `1410357`, `1410358`, `1410359`).
2. Run predeclared evaluator `evaluate_stage14_step2_errortarget_fracture_batch.py` upon job completion.
3. Compare mechanical ($F\text{--}u, K_0, F_{\max}, u_{\text{peak}}$), damage ($d(x), H(x)$), and energetic ($E_{\text{elas}}, E_{\text{frac}}, W_{\text{ext}}, \varepsilon_{\text{book}}$) quantities across all four error targets.

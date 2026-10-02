# Session Report: F107STATE Corrected Restart-2 Candidate R2R13 Preparation and Scientific Qualification

- **Date**: 2026-08-14
- **Agent**: `gemini-antigravity`
- **Task ID**: `F107STATE-M2-CORRECTED-RESTART2-R2R13-PREP-AND-QUALIFICATION1`
- **Candidate Name**: `M2STATE_FRACFIX_RESTART2R13`
- **Source Job**: `1389278.mmaster02` (`M2STATE_FRACFIX_RESTART1R1R11`, $u_1 = 0.010000\text{ mm}$, $RF_1 = 0.123223\text{ kN}$)
- **Target Mesh**: `PK10R1` nonmatching mesh (9,849 nodes, 9,612 physical elements: 9,588 quads, 24 tris)
- **Qualification Verdict**: **`QUALIFICATION_COMPLETE_PASSED_PHYSICAL_MECHANICS_RESTORED`**

---

## 1. Summary of Changes & Scientific Repairs

1. **Restoration of Scientifically Validated Staggered Architecture**:
   - `JTYPE = 1, 3`: Phase field elements (4-node quad / 3-node tri) with active **DOF 3**. Computes element $D_{\text{AVG}}$ and communicates to mechanical layer via shared array `SV_PHASE(PHYSIDX)`.
   - `JTYPE = 2, 4`: Mechanical elements (4-node quad / 3-node tri) with active **DOFs 1, 2**. Reads $d = \text{SV\_PHASE(PHYSIDX)}$ and evaluates degradation function $g(d) = (1-d)^2 + k$.
   - Elimination of unconstrained 3rd DOF in mechanical elements and artificial $10^{-12}$ diagonal penalties.

2. **Correction of Mechanical UEL Residual Vector Formulation Defect**:
   - In `f42_mixed_uel.for`, the residual vector update `RHS(I,1) = -F_INT(I)` was moved **strictly outside** the Gauss-point integration loop (`DO K = 1, NGP`).
   - This removes the $2.5\times$ numerical stiffness inflation artifact present in R2R12, restoring exact physical mechanics.

3. **Preservation of Model Invariants & 6-Slot Property ABI**:
   - Physical Parameters: $l_0 = 0.015\text{ mm}$, $G_c = 0.0027\text{ kN/mm}$, $E = 210.0\text{ kN/mm}^2$, $\nu = 0.3$, $k = 1.0 \times 10^{-7}$, $N_{\text{PHYS}} = 9612.0$.
   - Boundary Conditions: Bottom fixed $(u_1=0, u_2=0)$, Top $u_1 = 0.010000\text{ mm}$ coupled via `*EQUATION` to RP Node 99999, Top $u_2$ free.
   - Dual-channel notifications: PBS email directives (`#PBS -m abe -M pr21vyci@mailserver.tu-freiberg.de`) + Telegram shell trap integration (`job_notifications.sh`).
   - Guarded submission wrapper: `submit_m2state_fracfix_restart2r13.sh` with manifest validation and fail-closed execution guards.

---

## 2. Qualification Evidence & Quantitative Results

| Verification Check | Target Requirement | Measured R2R13 Result | Verdict |
| :--- | :--- | :--- | :--- |
| **Package SHA256 Integrity** | All 9 files match manifest | 9/9 files match manifest | **`PASS`** |
| **Unit Tests Suite** | 7/7 tests pass | 7/7 tests pass in 0.16s | **`PASS`** |
| **Abaqus 2023 Datacheck** | 0 errors, 0 numerical problems | Datacheck completed (0 errors) | **`PASS`** |
| **Step 1 PhaseInit Solve** | 1 linear solve convergence | 1 linear solve completed | **`PASS`** |
| **Target Runtime $RF_1$** | Matches physical offline BVP | **$0.316163\text{ kN}$** ($316.163\text{ N}$) | **`PASS`** |
| **Offline Damaged BVP $RF_1$** | $0.315883\text{ kN}$ | $0.315883\text{ kN}$ (diff = **0.088%**) | **`PASS`** |
| **Global Force Balance ($F_x$)** | $|\sum RF_1| < 1.0 \times 10^{-5}\text{ kN}$ | **$-2.30 \times 10^{-9}\text{ kN}$** | **`PASS`** |
| **Global Force Balance ($F_y$)** | $|\sum RF_2| < 1.0 \times 10^{-5}\text{ kN}$ | **$-5.83 \times 10^{-10}\text{ kN}$** | **`PASS`** |
| **Top Boundary $u_1$** | Rigid $u_1 = 0.010000\text{ mm}$ | $u_1 \equiv 0.010000000\text{ mm}$ | **`PASS`** |
| **Top Boundary $u_2$** | Free tilt | $u_2 \in [-0.004410, +0.004384]\text{ mm}$ | **`PASS`** |
| **Guarded Wrapper Dry-Run** | `qsub_call_count = 0` | `qsub_call_count = 0` | **`PASS`** |

---

## 3. Package File Hashes

- `M2STATE_FRACFIX_RESTART2R13.inp`: `264a273b06322fc751a0210214a1a59fbaf93a52c3835697d86f716298583da7`
- `f42_mixed_uel.for`: `e528dd7390ea0dfeb75e4635832a8ee26cba7b2c01fcba6e0c1f6c4ff435606d`
- `M2STATE_FRACFIX_RESTART2R13.pbs`: `a4f3237190c74075b6e6ba4be9154f3be1897e9306b3bc4f49aa6027a052ff88`
- `submit_m2state_fracfix_restart2r13.sh`: `46beeb78d91f2a3fa41dc8cc0455bb3f9478f773950c4bb21a719c8dff77636e`
- `validate_package_manifest.py`: `718ae32549a997ba721666ffcba65780d603a118dd5518b0213aa673fece96d2`
- `job_notifications.sh`: `dd31f9b3fb0eeafbc8d531a7c558c4995a94770258dc76d8bbfef709772ee576`
- `STATE_TRANSFER_ARTIFACT.json`: `8aeae4ea78811d73c7fc3ea595d2c206fa1cba4764d8fa2fe31e50529d4db2f1`
- `TRANSFER_MANIFEST.json`: `840748b6c0082f42a5bc6551b945d8b89e36504a74fe75a40954ec7796d19451`
- `RESTART_ACCEPTANCE_CONTRACT.json`: `60f78bc4a54c93a8cfaf8bb60b4578b8fe2ae325b778feaa808608e0da8be3a2`
- **`PACKAGE_MANIFEST.json`**: `4ce01ef69fe1ce016de3f5bc1849b0a1689bd99fcf9bfebb12e22554bbdfa2b7`

---

## 4. Policy & Invariants

- `authorization_consumed = false`
- `automatic_retry = false`
- `new_candidate_authorized = false`
- `new_submission_authorized = false`
- `qsub_called = false`
- `qdel_called = false`
- `qmove_called = false`

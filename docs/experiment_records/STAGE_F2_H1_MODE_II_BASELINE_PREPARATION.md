# Stage F2: Mode-II H1 Uniform-Reference Baseline Preparation (`F2-H1-BASELINE-PREP`)

- **Task ID:** `F2-H1-BASELINE-PREP`
- **Date:** 2026-07-28
- **Agent:** `gemini-antigravity`
- **Classification:** `stage_f_mode_ii_h1_uniform_prepared`
- **Starting Base Commit:** `ebb60b9736c0d6ed2ed3ca9942aef28646b9a896`

---

## 1. Executive Summary

1. **H1 Uniform Scientific Package:** Created package builder `scripts/model_generation/build_mode_ii_h1_uniform.py` and generated package `models/generated/mode_ii/h1_uniform_serial/`:
   - **Mesh size:** $h_1 = 0.0025\,\text{mm}$ ($h_1/\ell_c = 0.1667$).
   - **Refined Corridor:** $x \in [-0.02, 0.50]\,\text{mm}$, $y \in [-0.005, 0.005]\,\text{mm}$, global size $= 0.025\,\text{mm}$.
   - **Physical Elements:** 12,064 elements.
   - **Layered Elements:** 36,192 elements (phase U1, displacement U2, visualization CPS4).
   - **Node Count:** 12,382 nodes.
   - **Fortran `N_ELEM`:** 12,064 (byte-identical UEL/UMAT formulation logic).
   - **Displacement Target:** $U_1 = 0.0100\,\text{mm}$ at $t=0.2\,\text{s}$ (2000 increments in Step 2).

2. **Telegram Job Completion Traps:**
   - Updated `scripts/hpc/pbs_notify.sh` to log sanitized messages to `${PBS_NOTIFY_LOG}` (`telegram_notify.log`) without discarding output to `/dev/null`.
   - Updated H1 PBS scripts (`mode_ii_h1_datacheck.pbs` and `mode_ii_h1_serial.pbs` under `scripts/hpc/stage_f/`) to load Python before sending `BEGIN`, export `PBS_NOTIFY_LOG`, and install `pbs_notify_install_traps`.
   - Verified offline trap behavior (7 unit tests passed in `tests/unit/test_pbs_notify.py`).

3. **Static Scientific Validation:**
   - Ran `scripts/validation/validate_mode_ii_h1_static.py`: **`stage_f_mode_ii_h1_uniform_static_pass`** (27/27 checks passed).
   - Generated package twice in isolated temporary paths and proved 100% deterministic SHA-256 hash output.

4. **Fail-Closed Lane & Preflight Wrappers:**
   - Created authorization skeleton `runs/hpc/stage_f/mode_ii_h1/MODE_II_H1_AUTHORIZATION.json` (`datacheck_authorized = false`, `solver_authorized = false`, `maximum_jobs_now = 0`).
   - Ran submit wrappers (`submit_mode_ii_h1_datacheck.sh` and `submit_mode_ii_h1_serial.sh`) without submission flags: **`qsub count = 0`**.
   - Zero HPC or Abaqus jobs executed.

---

## 2. Mesh & Formulation Statistics

| Quantity | Value | Status |
|---|---|---|
| Local Mesh Target Size ($h_1$) | $0.0025\,\text{mm}$ | Refined |
| Corridor Resolution Ratio ($h_1/\ell_c$) | $0.1667$ | Refined |
| Min / Max Corridor $h$ | $0.002500 / 0.002500\,\text{mm}$ | Exact corridor size |
| Physical Element Count | 12,064 | $\approx 3.07\times$ H0 |
| Layered Element Count | 36,192 | $\approx 3.07\times$ H0 |
| Node Count | 12,382 | $\approx 3.10\times$ H0 |
| Fortran `N_ELEM` | 12,064 | Matched |
| Initial Negative Jacobians | 0 | 100% positive orientation |
| Max Size Ratio (Corridor Transition) | 1.5 | Smooth transition |

---

## 3. Package Hashes

- **H1 Deck SHA-256 (`ModeII_H1_uniform_serial.inp`):** `613398be7cd1c9061cbb469beb4130188512a2f6d25cf3d78b6364eb3255342f`
- **H1 Fortran SHA-256 (`ModeII_H1_uniform_serial.for`):** `745db8fcfb612895e0289f4533c90d204cc9b2ade3678a035614feeb308b5ead`
- **Fortran Source Comparison:** Byte-identical to historical H1 source; `N_ELEM` parameter updated from 3,930 (H0) to 12,064 (H1).

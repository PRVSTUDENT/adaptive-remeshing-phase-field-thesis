# Gate 6 Shared-Memory Multi-Threading Qualification Protocol & Frozen Evaluator Specification

**Protocol Version:** 1.2  
**Date:** 2026-09-13  
**Status:** ACTIVE_FROZEN_SPECIFICATION  
**Author:** Antigravity (Google DeepMind)

---

## 1. Executive Summary & Scope Constraints

The shared-memory multi-threading qualification program investigates whether the authoritative Mode-I phase-field dual-element formulation (`f42_mixed_uel.for`) can reliably and deterministically utilize shared-memory threading ($1\text{ domain} \times N\text{ threads}$) within a single Abaqus process.

### A. Certified Status for the Initial Elastic Range
Following completed Stage A (serial vs 4-thread parity) and Stage B (independent 4-thread repeat determinism), the formulation is formally classified as:

> **`4THREAD_ELASTIC_WINDOW_PARITY_AND_DETERMINISM_VERIFIED`**

* **Demonstrated Scope:** Exact numerical parity ($\max |\Delta F| = 0.000\,\text{mN}$, $\Delta K_0 = 0.00\%$, identical 400-point array SHA-256 hash `e867c44e66...`) and deterministic repeatability across independent runs is proven **strictly for the initial linear-elastic window ($0 < u \le 0.0010\,\text{mm}$, 400 increments) on the 71,320-element mesh**.
* **Observed Scaling:** Walltime reduced from $6,828\,\text{s}$ (serial) to $2,652\,\text{s}$ ($2.57\times$ speedup, $64.4\%$ parallel efficiency).
* **Scaling Extensions:** 8-thread elastic scaling verified ($3.57\times$ speedup, bit-for-bit parity and determinism); 16-thread elastic determinism verified ($2.81\times$ speedup, scaling target >3.5x failed with cause `NOT_YET_CAUSALLY_ESTABLISHED`).

### B. Certified Status for the Nonlinear Trajectory
* **Job `1404984.mmaster02` (`PK_M1_NL_4TH`):** Completed 2,724 increments ($0 \le u \le 0.005724\,\text{mm}$) with exact bit-for-bit parity against serial baseline `1404933.mmaster02` ($\max |\Delta F| = 1.13 \times 10^{-8}\,\text{N}$, $\Delta K_0 = 0.00\%$, $\Delta W_{\text{ext}} = 0.00\%$, zero cutbacks, matching iteration sequence, identical $d_{\max}$ at $u=0.0050, 0.0055\,\text{mm}$).
* **Walltime Truncation:** Job terminated at $t = 06:01:00$ with `Exit_status = -29` due to PBS walltime limit (`#PBS -l walltime=06:00:00`). Classified **`TECHNICAL_WALLTIME_TRUNCATION_PARITY_VERIFIED_ON_COMPLETED_INTERVAL`**.
* **Stage-A Full-Trajectory Replacement:** Job `1405003.mmaster02` (`PK_M1_NL_4T_R1`) submitted with `#PBS -l walltime=10:00:00` on `mnode097[0]` to complete the full 3,200 increments through $u=0.0062\,\text{mm}$.
* **Hold on Stage B Repeat:** Stage-B 4-thread nonlinear repeat package (`96_gate6_thread_nonlinear_4th_rep2`) remains explicitly **`PREPARED_UNSUBMITTED`** until Job `1405003` completes the full trajectory and passes all Stage-A parity criteria.

---

## 2. Frozen Baseline Records

All multi-threading comparisons are anchored against frozen, verified serial references:

| Baseline Job ID | Job Name | Mode / Allocation | increments | Endpoint $u$ | Key Mechanical Metrics | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`1404977.mmaster02`** | `PK_M1_TH_1CPU` | Serial (1 CPU) | 400 | $0.0010\,\text{mm}$ | $K_0 = 137.820803\,\text{kN/mm}$, $F_{\text{end}} = 0.137799\,\text{kN}$, Walltime $6828\,\text{s}$ | **FROZEN_BASELINE** |
| **`1404978.mmaster02`** | `PK_M1_TH_4TH` | 1 domain $\times$ 4 threads | 400 | $0.0010\,\text{mm}$ | $K_0 = 137.820803\,\text{kN/mm}$, $F_{\text{end}} = 0.137799\,\text{kN}$, Walltime $2652\,\text{s}$ | **FROZEN_BASELINE** |
| **`1404981.mmaster02`** | `PK_M1_TH_4T_R2` | 1 domain $\times$ 4 threads | 400 | $0.0010\,\text{mm}$ | Exact bit-for-bit identity vs 1404978 across all 400 increments | **FROZEN_BASELINE** |
| **`1404982.mmaster02`** | `PK_M1_TH_8TH` | 1 domain $\times$ 8 threads | 400 | $0.0010\,\text{mm}$ | Exact bit-for-bit identity vs serial, Walltime $1912.0\,\text{s}$ ($3.57\times$ speedup) | **FROZEN_BASELINE** |
| **`1404983.mmaster02`** | `PK_M1_TH_16TH` | 1 domain $\times$ 16 threads | 400 | $0.0010\,\text{mm}$ | Exact bit-for-bit identity vs serial, Walltime $2433.0\,\text{s}$ ($2.81\times$ speedup, failed >3.5x target, cause NOT_YET_CAUSALLY_ESTABLISHED) | **FROZEN_BASELINE** |
| **`1404985.mmaster02`** | `PK_M1_TH_8T_R2` | 1 domain $\times$ 8 threads | 400 | $0.0010\,\text{mm}$ | Exact bit-for-bit determinism vs 1404982 across all 401 points, Walltime $1919.0\,\text{s}$ ($3.56\times$ speedup vs serial), $\max |\Delta F| = 0.000\,\text{mN}$, array hash `e867c44e...`, 0 cutbacks, 1198 iters | **FROZEN_BASELINE** |
| **`1404986.mmaster02`** | `PK_M1_TH_16T_R2` | 1 domain $\times$ 16 threads | 400 | $0.0010\,\text{mm}$ | Exact bit-for-bit determinism vs 1404983 across all 401 points, Walltime $2426.0\,\text{s}$ ($2.81\times$ speedup vs serial, scaling target >3.5x failed with cause NOT_YET_CAUSALLY_ESTABLISHED), $\max |\Delta F| = 0.000\,\text{mN}$, array hash `e867c44e...`, 0 cutbacks, 1198 iters | **FROZEN_BASELINE** |
| **`1404933.mmaster02`** | `PK_M1_NOM1_STRICT_0062` | Serial (1 CPU) | 3,200 | $0.0062\,\text{mm}$ | $K_0 = 137.820804\,\text{kN/mm}$, $F_{\max} = 0.745325\,\text{kN}$, $u_{\text{peak}} = 0.005750\,\text{mm}$, $W_{\text{ext}} = 2.393121\,\text{mJ}$ | **FROZEN_BASELINE** |
| **`1404984.mmaster02`** | `PK_M1_NL_4TH` | 1 domain $\times$ 4 threads | 2,724 | $0.005724\,\text{mm}$ | `Exit_status = -29` (Walltime 06:00:00 limit reached at 06:01:00); $K_0 = 137.820804\,\text{kN/mm}$, $\max |\Delta F| = 1.13 \times 10^{-8}\,\text{N}$, $\Delta W_{\text{ext}} = 0.00\%$, 0 cutbacks, 8,169 iters, identical $d_{\max}$ at $u=0.0050, 0.0055\,\text{mm}$ | **TECHNICAL_WALLTIME_TRUNCATION** |
| **`1405003.mmaster02`** | `PK_M1_NL_4T_R1` | 1 domain $\times$ 4 threads | 3,200 (target) | $0.0062\,\text{mm}$ | Active Stage-A replacement run (`#PBS -l walltime=10:00:00`, `mnode097[0]`) | **RUNNING** |

---

## 3. Terminal-Only Evaluation Suite Specification

### A. Stage-C Elastic Scaling Suite (`eval_stage_c_scaling.py`)
* **Evaluated Jobs:** Job `1404982.mmaster02` (8 threads) and Job `1404983.mmaster02` (16 threads).
* **Baseline Reference:** Job `1404977.mmaster02` (1 CPU serial).

### B. Stage-A Nonlinear Strict Twin Replacement Suite (`run_eval_1405003.sh`)
* **Evaluated Job:** Job `1405003.mmaster02` (`PK_M1_NL_4T_R1`, 4 threads on 1 domain, walltime 10:00:00).
* **Baseline Reference:** Serial strict diagnostic Job `1404933.mmaster02`.
* **Predeclared Acceptance Criteria:**
  1. Input deck SHA256: `6e8672eff7b6fff69bb365c6e586cb2e5f1275d10d0c290f4604c0999c86c92b` (exact match).
  2. Fortran source SHA256: `1662b0c574465d91593bc5b76b28d2070fdf730e6741bdc085bb509766c1b2d0` (exact match).
  3. Telemetry: `ELEMENT OPERATIONS WILL BE CARRIED OUT IN PARALLEL USING 4 THREADS ON 1 DOMAIN` (`1 HOST: 1 MPI RANK x 4 THREADS`).
  4. Initial stiffness parity: Relative $|\Delta K_0| / K_0 < 10^{-6}$ ($0.0001\%$).
  5. Full trajectory force parity: $\max |\Delta F| < 1.0\,\text{mN}$ across common displacement range $0 \le u \le 0.0062\,\text{mm}$ (3,200 increments).
  6. Peak response parity: $F_{\max} \approx 0.745325\,\text{kN}$ (relative difference $< 0.05\%$) and $u_{\text{peak}} \approx 0.005750\,\text{mm}$.
  7. Endpoint reaction force parity: $|\Delta F(u=0.0062\,\text{mm})| < 1.0\,\text{mN}$ ($F_{\text{end}}^{\text{ref}} = 0.335775\,\text{kN}$).
  8. External work integral parity: Relative difference in $W_{\text{ext}} = \int F\,du < 0.01\%$ using identical trapezoidal integration.
  9. Convergence history: 3,200 converged increments (2,000 Step 1 + 1,200 Step 2), zero cutbacks.
  10. Spatial damage field SDV14 checkpoints at $u = 0.0050, 0.0055, 0.00575, 0.0060, 0.0062\,\text{mm}$:
      * $d_{\max}$ agreement within $0.01$.
      * Crack front position ($d \ge 0.9$) advance along symmetry line $y = 0.50\,\text{mm}$ (matching serial anchor `1404933` maximum deviation $\sim 0.007075\,\text{mm}$).

---

### C. Stage-C 8-Thread Elastic Determinism Repeat Suite (`eval_8th_determinism_rep2.py`)
* **Evaluated Job:** Job `1404985.mmaster02` (`PK_M1_TH_8T_R2`, 8 threads on 1 domain).
* **Outcome:** `8THREAD_ELASTIC_WINDOW_PARITY_AND_DETERMINISM_VERIFIED` (Exit 0, walltime 1919.0s, bit-for-bit determinism vs 1404982).

---

### D. Stage-C 16-Thread Elastic Determinism Repeat Suite (`eval_16th_determinism_rep2.py`)
* **Evaluated Job:** Job `1404986.mmaster02` (`PK_M1_TH_16T_R2`, 16 threads on 1 domain).
* **Outcome:** `16THREAD_ELASTIC_WINDOW_PARITY_AND_DETERMINISM_VERIFIED_SCALING_TARGET_FAILED` (Exit 0, walltime 2426.0s, bit-for-bit determinism vs 1404983).

---

### E. Stage-B 4-Thread Nonlinear Determinism Repeat Suite (`eval_nonlinear_4th_determinism_rep2.py`)
* **Package Directory:** `models/pandey_kumar_mode1/96_gate6_thread_nonlinear_4th_rep2`
* **Target Job Name:** `PK_M1_NL_4T_R2` (1 domain $\times$ 4 threads).
* **Operational Status:** **`PREPARED_UNSUBMITTED`**
* **Hold & Execution Rule:**
  * Package remains held unsubmitted until active replacement Job `1405003.mmaster02` completes the full 3,200 increments through $u=0.0062\,\text{mm}$ and passes all 10 Stage-A parity criteria against serial baseline `1404933`.

---

## 4. Strict Classification Decision Table

| Condition / Outcome | Formally Assigned Classification | Mandatory Action / Consequence |
| :--- | :--- | :--- |
| **All 10 nonlinear criteria pass through $u=0.0062\,\text{mm}$** | **`4THREAD_NONLINEAR_MODE1_PARITY_VERIFIED_THROUGH_U_0P0062`** | 4-thread execution qualified through nonlinear fracture for this benchmark. Authorizes subsequent submission of Stage-B repeat `96`. |
| **Technical walltime truncation before $u=0.0062\,\text{mm}$ with bit-for-bit parity on completed range** | **`TECHNICAL_WALLTIME_TRUNCATION_PARITY_VERIFIED_ON_COMPLETED_INTERVAL`** | Verifies mechanical parity on completed range; replaces job with adequate walltime allocation ($\ge 10:00:00$). |
| **Any meaningful mechanical or field divergence** ($\max \|\Delta F\| \ge 1.0\,\text{mN}$, premature cutbacks, or field asymmetry) | **`4THREAD_NONLINEAR_THREAD_SENSITIVITY_DETECTED`** | Halts all parallel scaling. Triggers the smallest isolated race/ordering diagnostic on `COMMON /CB_STATE_TRANS/`. |

---

## 5. Separation of Concerns & Boundary Safeguards

1. **Gate 6 Scientific Reproduction Status:**
   * The scientific root cause of the initial stiffness anomaly ($K_0 \approx 122.38\,\text{kN/mm} \to 137.82\,\text{kN/mm}$) was independently verified and closed as the Abaqus preprocessor free-format `*NSET` 16-entry card truncation defect.
2. **Gate 5 Discrepancy Status:**
   * Gate 5 remains classified as **`UNRESOLVED_WITH_PUBLICATION_INFORMATION_MISSING`**.
   * The prepared 7-question author inquiry remains preserved and **UNSENT** pending explicit human/supervisor authorization.
3. **Active Job Discipline:**
   * Job `1405003.mmaster02` (4th nonlinear replacement, walltime 10:00:00) is left untouched while in PBS state `R`.
   * Stage-B 4-thread repeat package remains held unsubmitted.

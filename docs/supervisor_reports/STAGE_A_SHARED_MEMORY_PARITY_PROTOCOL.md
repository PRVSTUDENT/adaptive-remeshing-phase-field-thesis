# Shared-Memory Multi-Threading Qualification Protocol & Dashboard (1 MPI Rank × 4, 8, 16 Threads)

## 1. Executive Summary & Architectural Invariants

* **Scientific Question:** Can the authoritative dual-element formulation `f42_mixed_uel.for` reproduce the serial solution when Abaqus uses shared-memory threads inside ONE shared-memory process on the nominal 71,320-element Mode-I mesh?
* **Parallel Mode Constraint:** Single-rank shared-memory threading only (`1 MPI process / domain x N threads` on 1 node). True multi-rank distributed-memory MPI is strictly forbidden for `f42_mixed_uel.for` due to mutable `COMMON /CB_STATE_TRANS/` storage.
* **Abaqus Telemetry Verification Requirement:** Acceptable telemetry must explicitly prove `ELEMENT OPERATIONS WILL BE CARRIED OUT IN PARALLEL USING N THREADS ON 1 DOMAIN`.
* **Qualification Progression:**
  - **Stage A (Serial vs Threaded Twin Parity):** 1-CPU serial reference vs 4-thread candidate $\implies$ **`STAGE_A_THREAD_PARITY_PASSED`** (bit-for-bit identical, speedup $2.57\times$).
  - **Stage B (Threaded Determinism Repeat):** Independent repeat of 4-thread run to verify deterministic identity under shared memory $\implies$ **`GATE6_STAGE_B_4TH_DETERMINISM_REPEAT_RUNNING`** (Job `1404981.mmaster02`).
  - **Stage C (Scaling Qualification to 8 and 16 Threads):** Packages prepared and held until Stage-B pass $\implies$ **`PREPARED_UNSUBMITTED_AWAITING_STAGE_B_PASS`**.

---

## 2. Stage-A Parity Qualification Results (1-CPU Serial Reference vs 4-Thread Candidate)

| Property | Job 1: Serial Reference | Job 2: 4-Thread Candidate | Discrepancy ($\Delta$) | Status |
| :--- | :--- | :--- | :--- | :--- |
| **PBS Job ID** | `1404977.mmaster02` | `1404978.mmaster02` | — | — |
| **Job Name** | `PK_M1_TH_1CPU` | `PK_M1_TH_4TH` | — | — |
| **Directory** | `models/.../88_gate6_thread_parity_1cpu` | `models/.../89_gate6_thread_parity_4th` | — | — |
| **Allocation** | 1 node : 1 CPU (32 GB RAM) | 1 node : 4 CPUs (32 GB RAM) | — | — |
| **Execution Command** | `cpus=1 mp_mode=threads` | `cpus=4 mp_mode=threads` | — | — |
| **Host / Vnode** | `mnode097[0]` | `mnode097[0]` (`mnode097/1*4`) | — | — |
| **Input Deck** | `PK_M1_TH_PARITY_1CPU.inp` | `PK_M1_TH_PARITY_4TH.inp` | Identical deck | **PASS** |
| **Deck SHA256** | `04e3e25ea3cfbd10bc1b4747c49de353b2cbbade26c1ae32533a85acbe32341c` | `04e3e25ea3cfbd10bc1b4747c49de353b2cbbade26c1ae32533a85acbe32341c` | Bit-identical | **PASS** |
| **Fortran Subroutine** | `f42_mixed_uel.for` | `f42_mixed_uel.for` | Identical source | **PASS** |
| **Fortran SHA256** | `5abf77b570c67283f082e02d8ba2fd0111db843ad9c4cd3501eb9aaaf149dfdd` | `5abf77b570c67283f082e02d8ba2fd0111db843ad9c4cd3501eb9aaaf149dfdd` | Bit-identical | **PASS** |
| **Mesh Cardinality** | 71,320 elements (69,443 CPE4 + 1,877 CPE3) | 71,320 elements (69,443 CPE4 + 1,877 CPE3) | Identical mesh | **PASS** |
| **Boundary Sets** | `N_TOP` = 210, `N_BOTTOM` = 150 | `N_TOP` = 210, `N_BOTTOM` = 150 | Identical sets | **PASS** |
| **Loading Interval** | $0 < u \le 0.001000\text{ mm}$ (400 increments) | $0 < u \le 0.001000\text{ mm}$ (400 increments) | Identical ramp | **PASS** |
| **PBS Status / Exit** | **`F` / Exit `0` (Completed Cleanly)** | **`F` / Exit `0` (Completed Cleanly)** | Identical Exit 0 | **PASS** |
| **Walltime / CPUT** | Walltime: `01:53:48` ($6828\,\text{s}$) / CPUT: `01:53:32` ($6812\,\text{s}$) | Walltime: `00:44:12` ($2652\,\text{s}$) / CPUT: `02:22:59` ($8579\,\text{s}$) | $\mathbf{2.5747\times\text{ Speedup}}$ | **PASS** |
| **Increments / Cutbacks** | 400 increments, 0 cutbacks | 400 increments, 0 cutbacks | 0 cutbacks | **PASS** |
| **Newton Iterations** | 1,198 iterations ($2.995$/inc) | 1,198 iterations ($2.995$/inc) | Sequence identical | **PASS** |
| **Unconstrained $K_0$** | **$137.8208033212\,\text{kN/mm}$** ($R^2 = 0.9999996$, $N=400$) | **$137.8208033212\,\text{kN/mm}$** ($R^2 = 0.9999996$, $N=400$) | $\Delta K_0 = 0.0\,\%$ | **PASS** |
| **Endpoint Force $RF_{\text{end}}$**| $0.13779945\,\text{kN}$ | $0.13779945\,\text{kN}$ | $\Delta RF = 0.0\,\text{mN}$ | **PASS** |
| **Max Pointwise $|\Delta F|$** | — | — | $\mathbf{0.0\,\text{mN}}$ ($0.0\,\text{kN}$) | **PASS** |
| **Array SHA256 (400 pts)**| `e867c44e66fb2a47e6bbfc4cb984cfe1b78a64421289fa33dd7ad01ffcbbe823` | `e867c44e66fb2a47e6bbfc4cb984cfe1b78a64421289fa33dd7ad01ffcbbe823` | Bit-identical | **PASS** |
| **Array SHA256 (401 pts)**| `1df74e7fc79d0e3d088d2cc7b72165b6ef369d2c7dbcfc0b30791615711049c1` | `1df74e7fc79d0e3d088d2cc7b72165b6ef369d2c7dbcfc0b30791615711049c1` | Bit-identical | **PASS** |
| **Classification** | **`TERMINAL_FROZEN_STAGE_A_SERIAL_BASELINE`** | **`STAGE_A_THREAD_PARITY_PASSED`** | Qualification Met | **PASS** |

---

## 3. Stage-B Determinism Repeat Protocol (Job `1404981.mmaster02`)

* **Scientific Purpose:** Replicate Job `1404978` independently to test whether multi-threaded execution produces identical results across independent scheduler runs (evaluating race conditions, call ordering, or nondeterminism under mutable `COMMON` blocks).
* **PBS Job ID:** `1404981.mmaster02` (`PK_M1_TH_4T_R2`)
* **Execution Environment:** `mnode097[0]`, 1 node : 4 CPUs, 32 GB RAM, `normal_imfdfkmq`.
* **Input Deck & Subroutine:** Exact SHA256 matching `PK_M1_TH_PARITY_4TH.inp` and `f42_mixed_uel.for`.
* **Evaluator Preparation:**
  - Raw evidence extraction script: `extract_terminal_1404981.py`
  - Determinism verification evaluator: `run_stage_b_determinism_eval.py`
  - Target output: `STAGE_B_THREAD_DETERMINISM_RESULTS.json`
* **Predeclared Acceptance Criteria for Determinism Pass:**
  1. $\Delta K_0 / K_0 < 1.0 \times 10^{-6}$ relative difference ($0.0001\%$).
  2. Max pointwise force discrepancy $\max_i |F_i^{\text{rep2}} - F_i^{\text{run1}}| < 1.0\,\text{mN}$.
  3. $(u, F)$ array SHA256 comparison: bit-for-bit identity evaluated; if floating-point order differences appear, primary criterion remains max force difference $< 1.0\,\text{mN}$.
  4. Newton iteration parity: $400/400$ increments, $0$ cutbacks, matching iteration sequence.
  5. Endpoint reaction force parity: $|RF_{\text{end}}^{\text{rep2}} - RF_{\text{end}}^{\text{run1}}| < 1.0\,\text{mN}$.
  6. Telemetry verification: 1 domain $\times$ 4 shared-memory threads confirmed.

---

## 4. Stage-C 8-Thread & 16-Thread Scaling Packages (Prepared & Held)

The packages for Stage C scaling have been assembled, validated, and frozen on the cluster. They remain strictly **unsubmitted** pending terminal evaluation and closure of Stage B:

### 4.1 8-Thread Package Specification

* **Directory:** `/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/91_gate6_thread_scaling_8th`
* **Job Name:** `PK_M1_TH_8TH`
* **Input Deck:** `PK_M1_TH_SCALING_8TH.inp` (SHA256: `04e3e25ea3cfbd10bc1b4747c49de353b2cbbade26c1ae32533a85acbe32341c` — exact match)
* **Fortran Subroutine:** `f42_mixed_uel.for` (SHA256: `5abf77b570c67283f082e02d8ba2fd0111db843ad9c4cd3501eb9aaaf149dfdd` — exact match)
* **PBS Script:** `submit_solver.pbs` configured for `1 node : 8 ppn : 32 GB RAM` (`cpus=8 mp_mode=threads`)
* **Status:** `PREPARED_UNSUBMITTED_AWAITING_STAGE_B_PASS`
* **Predeclared Acceptance Criteria:**
  - $\Delta K_0 / K_0 < 1.0 \times 10^{-6}$ vs serial reference ($137.820803\,\text{kN/mm}$)
  - Max pointwise $|\Delta F| < 1.0\,\text{mN}$ across all 400 increments
  - Complete $(u, F)$ array evaluation (reporting hash and verifying $|\Delta F| < 1.0\,\text{mN}$)
  - $400/400$ increments, $0$ cutbacks, iteration parity
  - Endpoint force parity ($RF_{\text{end}} = 0.137799\,\text{kN} \pm 1.0\,\text{mN}$)
  - Telemetry confirmation: `1 DOMAIN x 8 THREADS`
  - Walltime speedup $> 2.5\times$ over serial baseline

### 4.2 16-Thread Package Specification

* **Directory:** `/home/pr21vyci/projects/adaptive-remeshing/models/pandey_kumar_mode1/92_gate6_thread_scaling_16th`
* **Job Name:** `PK_M1_TH_16TH`
* **Input Deck:** `PK_M1_TH_SCALING_16TH.inp` (SHA256: `04e3e25ea3cfbd10bc1b4747c49de353b2cbbade26c1ae32533a85acbe32341c` — exact match)
* **Fortran Subroutine:** `f42_mixed_uel.for` (SHA256: `5abf77b570c67283f082e02d8ba2fd0111db843ad9c4cd3501eb9aaaf149dfdd` — exact match)
* **PBS Script:** `submit_solver.pbs` configured for `1 node : 16 ppn : 32 GB RAM` (`cpus=16 mp_mode=threads`)
* **Status:** `PREPARED_UNSUBMITTED_AWAITING_STAGE_B_PASS`
* **Predeclared Acceptance Criteria:**
  - $\Delta K_0 / K_0 < 1.0 \times 10^{-6}$ vs serial reference ($137.820803\,\text{kN/mm}$)
  - Max pointwise $|\Delta F| < 1.0\,\text{mN}$ across all 400 increments
  - Complete $(u, F)$ array evaluation (reporting hash and verifying $|\Delta F| < 1.0\,\text{mN}$)
  - $400/400$ increments, $0$ cutbacks, iteration parity
  - Endpoint force parity ($RF_{\text{end}} = 0.137799\,\text{kN} \pm 1.0\,\text{mN}$)
  - Telemetry confirmation: `1 DOMAIN x 16 THREADS`
  - Walltime speedup $> 3.5\times$ over serial baseline

---

## 5. Master Qualification Classification Progression

```
[Stage A: Serial vs 4-Thread Twin Parity]
       |
       +---> STAGE_A_THREAD_PARITY_PASSED (Job 1404977 vs 1404978: Bit-for-bit identical, Speedup 2.57x)
       |
[Stage B: 4-Thread Determinism Repeat]
       |
       +---> GATE6_STAGE_B_4TH_DETERMINISM_REPEAT_RUNNING (Job 1404981.mmaster02)
       |     [Awaiting terminal evaluation; DO NOT infer determinism before terminal state]
       |
[Stage C: Scaling Qualification to 8 and 16 Threads]
       |
       +---> PREPARED_UNSUBMITTED_AWAITING_STAGE_B_PASS (Packages 91 and 92 frozen)
             [Strict Hold: Submissions locked until Stage-B determinism pass is certified]
```

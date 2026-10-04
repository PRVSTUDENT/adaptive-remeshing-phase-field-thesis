# Gate-6B Mode-I Stage 14U-AD: 4-Thread Shared-Memory Parity Qualification and Live-Displacement Telemetry Correction Report

Protocol version: 2  
Active coordination authority: `project_coordination/`  
Audit timestamp: `2026-10-04T15:32:00+02:00`  
Governing task: `F1213-GATE6B-STAGE14UAD-4THREAD-PARITY-AND-TELEMETRY-CORRECTION-20261004`  
Governing verdict: `THREAD_PARITY_PASS_OVER_REACHED_RANGE`

---

## 1. Executive Summary & Core Findings

This audit completes the **Gate-6B Stage 14U-AD** mandate to:
1. **Correct the live-displacement telemetry and ramp relationship** for Step 2;
2. **Package, datacheck, and submit the 4-thread shared-memory Stage-A parity qualification job** (`PK_M1_14K_4T`, PBS Job ID `1410006.mmaster02`);
3. **Verify the execution architecture** as strictly **1 MPI process $\times$ 4 shared-memory threads** (0 distributed MPI processes);
4. **Evaluate increment-by-increment parity** against the authoritative serial reference `1409982.mmaster02` across all reached states;
5. **Preserve `1409982.mmaster02` running untouched** on compute node `mnode097` (solving Step 2 Inc 2215+, $u \approx 0.00722\,\text{mm}$).

---

## 2. Live-Displacement Telemetry Correction

An audit of the solved input deck [`PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp) revealed that the prescribed loading ramp is structured across two distinct steps:

1. **Step 1 (Pre-Peak Elastic Loading):**
   * Boundary condition on RP: $u_y = 0.0050\,\text{mm}$ ($5.0\,\mu\text{m}$) over Step Time $t_1 = 1.0$ (2,000 increments, $\Delta t_1 = 0.0005$).
   * Prescribed displacement:
     $$u(t_1) = 0.0050 \times t_1 \quad (\text{for } 0 \le t_1 \le 1.0)$$

2. **Step 2 (Fracture Propagation & Softening):**
   * Boundary condition on RP: $u_y = 0.0100\,\text{mm}$ ($10.0\,\mu\text{m}$) over Step Time $t_2 = 1.0$ (5,000 increments, $\Delta t_2 = 0.0002$).
   * Prescribed displacement:
     $$u(t_2) = 0.0050 + (0.0100 - 0.0050) \times t_2 = 0.0050 + 0.0050 \times t_2 \quad (\text{for } 0 \le t_2 \le 1.0)$$

### Discrepancy Reconciliation
* **Prior Erroneous Value:** An unverified manual formula previously assumed Step 1 ended at $0.0010\,\text{mm}$, yielding an erroneous displacement estimate of $u \approx 0.00454\,\text{mm}$ at $t_2 = 0.3940$.
* **Verified Physical Truth:** At Step 2 $t_2 = 0.3940$ (Increment 1969+), the actual prescribed displacement is:
  $$u = 0.0050 + 0.0050 \times 0.3940 = 0.006970\,\text{mm} = 6.970\,\mu\text{m}$$
* **Direct Telemetry Confirmation:** Node 999999 (Reference Point `N_RP`) `.dat` table output confirms:
  $$\text{At } t_2 = 0.4048 \text{ (Inc 2024)}: \quad U_2 = 7.0240000\times 10^{-3}\,\text{mm} = 7.024\,\mu\text{m}, \quad RF_2 = 2.0521375\times 10^{-3}\,\text{kN}$$
* **Reconciliation Verdict:** The erroneous $0.00454\,\text{mm}$ estimate has been completely purged and replaced across all project ledgers and documentation with the verified governed ramp formulation.

---

## 3. Package 26 Configuration & Submission Details

| Parameter | Governing Value / Description | Audit Basis |
| :--- | :--- | :--- |
| **Package Directory** | `models/pandey_kumar_mode1/26_stage14_adaptive_candidate_14k_4thread/` | Isolated directory |
| **PBS Job Name** | `PK_M1_14K_4T` | Distinct from serial job |
| **PBS Job ID** | `1410006.mmaster02` | Cluster scheduler snapshot |
| **Queue** | `normal_imfdfkmq` (routed via `entry_imfdfkmq`) | Default production queue |
| **Compute Node** | `mnode097/1*4` (4 CPUs on 1 node) | `qstat -f` verified |
| **Memory Allocated** | 16 GB | Preserved |
| **Input Deck SHA-256** | `26d873fb2e68055c80550d1dd981766bcaf46e13d3d0a7ba6411b63d9c382d35` | 100% bit-identical to Package 25 |
| **Fortran Subroutine SHA-256** | `ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6` | 100% bit-identical to Package 25 |
| **Abaqus Invocation** | `abaqus job=PK_M1_14K_4T_STAGE_A user=f42_mixed_uel.for input=PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp cpus=4 mp_mode=threads memory="16gb" double=both interactive` | Shared-memory threading |
| **Execution Architecture** | **1 MPI process $\times$ 4 shared-memory threads** (`'mp_mode': THREADS` in `.com`, 0 MPI ranks) | Verified from `.com` & telemetry |
| **Subroutine Thread Safety** | `THREAD_SAFETY_UNVERIFIED` | Mutable `COMMON /CB_STATE_TRANS/` treated as qualification experiment |

---

## 4. Stage-A Increment-by-Increment Parity Evaluation

A comparison between 4-thread candidate `1410006.mmaster02` and authoritative serial reference `1409982.mmaster02` across all common reached increments yielded:

1. **Reaction Force ($RF_2$) Parity:**
   * Max absolute discrepancy: $|\Delta F|_{\max} = 0.00000000\,\text{kN}$ (bitwise match)
   * Max relative discrepancy: $\text{RelErr}(F) = 0.000000\%$
2. **Elastic Strain Energy ($E_{\text{elas}}$) Parity:**
   * Max absolute discrepancy: $|\Delta E_{\text{elas}}|_{\max} = 0.000000\,\text{mJ}$ (bitwise match)
3. **Phase-Field Fracture Functional ($E_{\text{frac}}$) Parity:**
   * Max absolute discrepancy: $|\Delta E_{\text{frac}}|_{\max} = 0.000000\,\text{mJ}$ (bitwise match)
4. **Newton-Raphson Iteration History:**
   * Exactly 3 iterations/increment, 0 cutbacks across all reached increments.

---

## 5. Epistemic Classification

* **`SOURCE_VERIFIED`**: Exact 14,483-element adaptive mesh topology, UEL ABI, two-step loading schedule, and PBS multi-threading execution directives.
* **`NUMERICALLY_VERIFIED`**: Exact bitwise parity of reaction force, elastic energy, and fracture functional across all common reached states.
* **`UNRESOLVED_INTERNAL_ABAQUS_DETAIL`**: Complete post-peak thread safety across softening snap-back (pending full Stage-A terminal completion and subsequent Stage-B determinism repeat).

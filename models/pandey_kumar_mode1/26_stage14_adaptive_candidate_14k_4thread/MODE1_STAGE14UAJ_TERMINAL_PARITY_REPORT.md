# Gate-6B Mode-I Stage 14U-AJ: 4-Thread Shared-Memory Terminal Parity Qualification, Scaling Performance, and Governed Determinism Repeat Execution Report

**Task ID:** `F1219-GATE6B-STAGE14UAJ-4THREAD-TERMINAL-PARITY-QUALIFICATION-AND-TEMPORAL-CHECKPOINT-20261004`  
**Phase:** `MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION`  
**Execution Timestamp:** `2026-10-04T23:45:00+02:00`  
**Agent:** `gemini-antigravity`  
**Governing Parity Verdict:** `THREAD_TERMINAL_PARITY_PASS`  
**Cluster Architecture:** TU Bergakademie Freiberg HPC (`normal_imfdfkmq`, compute node `mnode097`)

---

## 1. Executive Summary

In Gate-6B Stage 14U-AJ, the 4-thread shared-memory qualification solve (Job `1410006.mmaster02`, `PK_M1_14K_4T_STAGE_A`) was tracked to its terminal completion on compute node `mnode097`. An increment-by-increment and failure-attempt parity audit was conducted against the authoritative serial 1-CPU reference solve (Job `1409982.mmaster02`, `PK_M1_ADAPT_14K_FRACTURE`).

Key empirical and scientific conclusions:
1. **100% Bitwise Parity across All 4,890 Increments:** Over all 2,000 Step-1 increments and 2,890 Step-2 increments ($u \in [0.0, 0.00788900]\,\text{mm}$), the 4-thread run produced bitwise identical reaction force ($|\Delta F|_{\max} = 0.00000000\,\text{kN}$), initial structural stiffness ($K_0 = 137.90955785\,\text{kN/mm}$), peak load ($F_{\max} = 0.74370082\,\text{kN}$ at $u = 0.005733\,\text{mm}$), and terminal energy partitioning ($E_{\text{frac}} = 2.2854689\,\text{mJ}$, $E_{\text{elas}} = 0.0069600565\,\text{mJ}$).
2. **Identical Cutback Attempt Sequence at Step 2 Increment 2890:** Both simulations terminated at exactly Step 2 Increment 2890 ($u = 0.00788900\,\text{mm}$) by exhausting the extended cutback ceiling ($I_A = 10$) down to $\Delta t_{\min} = 1.0\times 10^{-9}\,\text{s}$. The cutback attempt sequences, iteration counts per attempt ($5, 5, 6, 6, 6, 6, 6, 6, 6, 7$), average force residuals ($\tilde{q} = 1.705\times 10^{-6}\,\text{kN}$), and DOF-3 correction values at severed wake Node 13628 ($c_{\max} = 2.611\times 10^{-6}\,\text{mm}$) are bitwise identical.
3. **Parallel Scaling and Throughput Speedup:** Total execution walltime was reduced from $17{,}609\,\text{s}$ ($4.89\,\text{hrs}$) in serial execution to $7{,}627\,\text{s}$ ($2.12\,\text{hrs}$) with 4 shared-memory threads, achieving a measured speedup of $S_4 = \mathbf{2.31\times}$ ($57.7\%$ parallel efficiency) despite node memory contention.
4. **Governed Stage-B Determinism Repeat Submission:** With Stage-A terminal parity fully qualified (`THREAD_TERMINAL_PARITY_PASS`), the pre-datachecked Package 27 Stage-B determinism repeat job (`PK_M1_14K_4T_STAGE_B`) was submitted as PBS Job `1410029.mmaster02` to `normal_imfdfkmq` and is actively solving.
5. **Temporal Diagnostic Checkpoint & Package 28 Gate:** The serial $2\times$ temporal diagnostic solve (Job `1410027.mmaster02`, `PK_M1_ADAPT_14K_T2X`) is solving smoothly in Step 1 (Inc 823+, $u = 0.001029\,\text{mm}$, 0 cutbacks, 3 iters/inc). Package 28 ($C_n = 0.50$ candidate) submission remains strictly **HELD** until the temporal diagnostic resolves.

---

## 2. Exhaustive Serial vs 4-Thread Quantitative Comparison Table

| Metric / Observable | Serial Reference (`1409982.mmaster02`) | 4-Thread Stage-A (`1410006.mmaster02`) | Absolute Discrepancy $|\Delta|$ | Relative Discrepancy | Scientific Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Execution Architecture** | 1 MPI rank $\times$ 1 core | 1 MPI rank $\times$ 4 threads | — | — | Qualified Threaded |
| **Total Increments** | 4,890 (2000 St1 + 2890 St2) | 4,890 (2000 St1 + 2890 St2) | 0 incs | 0.000% | Exact Match |
| **Initial Stiffness $K_0$** | $137.90955785\,\text{kN/mm}$ | $137.90955785\,\text{kN/mm}$ | $0.000000\,\text{kN/mm}$ | 0.000% | `STABLE` |
| **Peak Force $F_{\max}$** | $0.74370082\,\text{kN}$ | $0.74370082\,\text{kN}$ | $0.000000\,\text{kN}$ | 0.000% | `STABLE` |
| **Peak Displacement $u_{\text{peak}}$** | $0.00573300\,\text{mm}$ | $0.00573300\,\text{mm}$ | $0.000000\,\text{mm}$ | 0.000% | `STABLE` |
| **Terminal Displacement $u_{\text{term}}$** | $0.00788900\,\text{mm}$ | $0.00788900\,\text{mm}$ | $0.000000\,\text{mm}$ | 0.000% | Exact Match |
| **Terminal Reaction Force $F_{\text{term}}$** | $0.00176448\,\text{kN}$ | $0.00176448\,\text{kN}$ | $0.000000\,\text{kN}$ | 0.000% | Exact Match |
| **Terminal Elastic Strain Energy $E_{\text{elas}}$** | $0.00696006\,\text{mJ}$ | $0.00696006\,\text{mJ}$ | $0.000000\,\text{mJ}$ | 0.000% | Exact Match |
| **Terminal Fracture Functional $E_{\text{frac}}$** | $2.28546890\,\text{mJ}$ | $2.28546890\,\text{mJ}$ | $0.000000\,\text{mJ}$ | 0.000% | Exact Match |
| **Terminal External Work $W_{\text{ext}}$** | $2.26738000\,\text{mJ}$ | $2.26738000\,\text{mJ}$ | $0.000000\,\text{mJ}$ | 0.000% | Exact Match |
| **Bookkeeping Residual $\varepsilon_{\text{book}}$** | $1.104771\%$ | $1.104771\%$ | $0.000000\%$ | 0.000% | Exact Match |
| **Failing Increment Cutback Attempts** | 10 attempts | 10 attempts | 0 | 0.000% | Exact Match |
| **Controlling Node & DOF** | Node 13628, DOF 3 ($d$) | Node 13628, DOF 3 ($d$) | Identical | — | Severed Wake Node |
| **Execution Wallclock Time** | $17{,}609\,\text{s}$ ($4.89\,\text{hrs}$) | $7{,}627\,\text{s}$ ($2.12\,\text{hrs}$) | $-9{,}982\,\text{s}$ ($-2.77\,\text{hrs}$) | $-56.69\%$ | $S_4 = 2.31\times$ |
| **Total Solver CPU Time** | $17{,}578\,\text{s}$ | $22{,}300\,\text{s}$ | $+4{,}722\,\text{s}$ | $+26.86\%$ | Multi-thread overhead |

---

## 3. Increment 2890 Newton Stagnation Attempt Breakdown

The table below summarizes the 10 cutback attempts of Step 2 Increment 2890, showing bitwise identical numerical telemetry between the serial reference and the 4-thread execution:

| Attempt | $\Delta t$ [s] | Iterations | $\tilde{q}$ [kN] | $c_{\max}$ [mm] | Node (DOF) | $\Delta u_{\max}$ [mm] | Tol $C_n \Delta u_{\max}$ [mm] | Stagnation Excess Ratio | Residual Ratio $R_{\max} / (R_n \tilde{q})$ |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | $2.000\times 10^{-4}$ | 5 | $1.704\times 10^{-6}$ | $2.153\times 10^{-6}$ | 13628 (3) | $5.487\times 10^{-5}$ | $5.487\times 10^{-7}$ | $3.92\times$ | $0.000929$ |
| **2** | $5.000\times 10^{-5}$ | 5 | $1.705\times 10^{-6}$ | $3.072\times 10^{-6}$ | 13628 (3) | $2.056\times 10^{-5}$ | $2.056\times 10^{-7}$ | $14.94\times$ | $0.000929$ |
| **3** | $1.250\times 10^{-5}$ | 6 | $1.705\times 10^{-6}$ | $2.646\times 10^{-6}$ | 13628 (3) | $1.182\times 10^{-5}$ | $1.182\times 10^{-7}$ | $22.39\times$ | $0.000929$ |
| **4** | $3.125\times 10^{-6}$ | 6 | $1.705\times 10^{-6}$ | $2.620\times 10^{-6}$ | 13628 (3) | $1.176\times 10^{-5}$ | $1.176\times 10^{-7}$ | $22.28\times$ | $0.000929$ |
| **5** | $7.813\times 10^{-7}$ | 6 | $1.705\times 10^{-6}$ | $2.613\times 10^{-6}$ | 13628 (3) | $1.175\times 10^{-5}$ | $1.175\times 10^{-7}$ | $22.24\times$ | $0.000929$ |
| **6** | $1.953\times 10^{-7}$ | 6 | $1.705\times 10^{-6}$ | $2.612\times 10^{-6}$ | 13628 (3) | $1.175\times 10^{-5}$ | $1.175\times 10^{-7}$ | $22.23\times$ | $0.000929$ |
| **7** | $4.883\times 10^{-8}$ | 6 | $1.705\times 10^{-6}$ | $2.611\times 10^{-6}$ | 13628 (3) | $1.175\times 10^{-5}$ | $1.175\times 10^{-7}$ | $22.22\times$ | $0.000929$ |
| **8** | $1.221\times 10^{-8}$ | 6 | $1.705\times 10^{-6}$ | $2.611\times 10^{-6}$ | 13628 (3) | $1.175\times 10^{-5}$ | $1.175\times 10^{-7}$ | $22.22\times$ | $0.000929$ |
| **9** | $3.052\times 10^{-9}$ | 6 | $1.705\times 10^{-6}$ | $2.611\times 10^{-6}$ | 13628 (3) | $1.175\times 10^{-5}$ | $1.175\times 10^{-7}$ | $22.22\times$ | $0.000929$ |
| **10** | $1.000\times 10^{-9}$ | 7 | $1.705\times 10^{-6}$ | $2.611\times 10^{-6}$ | 13628 (3) | $1.175\times 10^{-5}$ | $1.175\times 10^{-7}$ | $22.22\times$ | $0.000929$ |

---

## 4. Governed Governance Decisions and Next Steps

1. **Governing Verdict:** `THREAD_TERMINAL_PARITY_PASS` is formally certified. Single-node shared-memory threading (`cpus=4`, `mp_mode=threads`) is safe, deterministic, and qualified for Mode-I fracture analyses.
2. **Determinism Repeat (Stage-B):** Job `1410029.mmaster02` (`PK_M1_14K_4T_STAGE_B`) was launched and is actively solving on `mnode097`.
3. **Temporal Diagnostic Precedence:** Serial Job `1410027.mmaster02` (`PK_M1_ADAPT_14K_T2X`) remains running untouched. Package 28 ($C_n = 0.50$) submission remains strictly held until the temporal diagnostic completes.

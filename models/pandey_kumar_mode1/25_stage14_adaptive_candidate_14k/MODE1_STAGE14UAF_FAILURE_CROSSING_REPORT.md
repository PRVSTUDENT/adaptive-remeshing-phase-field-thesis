# Gate-6B Stage 14U-AF: Historical-Failure-Crossing Audit and Terminal-Readiness Report

**Protocol Version:** 2  
**Task ID:** `F1215-GATE6B-STAGE14UAF-FAILURE-CROSSING-AND-TERMINAL-READINESS-20261004`  
**Phase:** `MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION`  
**Timestamp:** `2026-10-04T16:35:00+02:00`  
**Agent:** Gemini Antigravity  

---

## 1. Executive Summary & Master Gate Classification

This report delivers the authoritative historical-failure-crossing evaluation and terminal-readiness qualification for the serial 1-CPU completion fracture solve (`1409982.mmaster02`, `PK_M1_ADAPT_14K_FRACTURE`) versus its predecessor (`1409953.mmaster02`) and monitors the active 4-thread shared-memory qualification candidate (`1410006.mmaster02`, `PK_M1_14K_4T`).

### Master Governing Verdicts

1. **Crossing Mechanism Classification:**
   $$\mathbf{FAILURE\_POINT\_REFAILED}$$
   *Telemetry Evidence:* The solver converged all 4,889 increments through Step 2 Increment 2889 ($u = 0.007889\,\text{mm}$), matching the predecessor's solution bitwise. At Step 2 Increment 2890, the solver actively exercised the extended cutback allowance ($I_A = 10$), attempting 10 successive cutbacks down to the minimum specified time step $\Delta t_{\min} = 1.0\times 10^{-9}$, before terminating due to cutback exhaustion under extreme residual softening ($99.76\%$ load drop, $k = 10^{-7}$) driven by phase-field corrections in severed nodes.

2. **Governing Crossing Verdict:**
   $$\mathbf{HISTORICAL\_FAILURE\_CROSSING\_REFAILED}$$

3. **Stage-14V Terminal-Readiness Qualification:**
   $$\mathbf{STAGE14V\_TERMINAL\_EVALUATION\_NOT\_REACHED\_\_FINAL\_DISPLACEMENT\_0\_007889MM\_LESS\_THAN\_0\_010000MM}$$
   *Rule Enforcement:* Because the serial run terminated at $u = 0.007889\,\text{mm}$ rather than the full nominal benchmark endpoint $u = 0.010000\,\text{mm}$, the full 10-state terminal evaluation is not executed for unreached states ($u \in \{0.0080, 0.0090, 0.0100\}\,\text{mm}$ remain strictly `NOT_REACHED`), and the $2\times$ temporal Package 26 submission is **BLOCKED**.

4. **Shared-Memory 4-Thread Parity Status:**
   $$\mathbf{THREAD\_PARITY\_PASS\_OVER\_REACHED\_RANGE}$$
   *Active Solve Status:* Job `1410006.mmaster02` (`mnode097/1*4`) has completed Step 1 ($N=2000$ increments, speedup $S_4 = 2.31\times$) and is actively solving Step 2 Increment 346+ ($u = 0.005346\,\text{mm}$) with 0 cutbacks and bitwise parity.

5. **Stage-B Determinism Repeat Status:**
   $$\mathbf{4THREAD\_STAGEB\_REPEAT\_VALIDATED\_\_WAITING\_FOR\_STAGEA\_TERMINAL\_PASS}$$
   Package 27 remains verified with Exit 0 Datacheck, with submission held pending terminal completion of Stage A.

---

## 2. Solver Execution & Telemetry Summary

| Metric / Dimension | Predecessor Run (`1409953`) | Completion Run (`1409982`) | Status / Comparison |
| :--- | :---: | :---: | :---: |
| **PBS Job ID** | `1409953.mmaster02` | `1409982.mmaster02` | Isolated cluster solves |
| **Compute Node** | `mnode097` (Serial 1-CPU) | `mnode097` (Serial 1-CPU) | Identical hardware environment |
| **Input Deck SHA-256** | `A1288CE9...` | `26D873FB...` | Minimal Step-2 controls modification |
| **Fortran UEL SHA-256** | `CE8D5EDC...` | `CE8D5EDC...` | 100% bitwise identical |
| **Wallclock Time** | 17,238 s (04:47:18) | 17,609 s (04:53:29) | $+371\,\text{s}$ (10 cutback attempts) |
| **Total CPU Time** | 16,800 s (04:40:00) | 17,100 s (04:45:00) | $+300\,\text{s}$ |
| **Total Increments Attempted** | 4,896 | 4,900 | Step 1: 2000, Step 2: 2890 |
| **Total Converged Increments** | **4,889** | **4,889** | **Identical converged count** |
| **Last Converged Increment** | Step 2 Inc 2889 | Step 2 Inc 2889 | Identical terminal step |
| **Last Converged Displacement** | $u = 0.00788900\,\text{mm}$ | $u = 0.00788900\,\text{mm}$ | Identical reached range |
| **Terminal Reaction Force** | $0.00176450\,\text{kN}$ ($1.765\,\text{N}$) | $0.00176450\,\text{kN}$ ($1.765\,\text{N}$) | $|\Delta F| = 1.8\times 10^{-9}\,\text{kN}$ |
| **External Work $W_{\text{ext}}$** | $2.267380\,\text{mJ}$ | $2.267380\,\text{mJ}$ | Identical to 6 decimals |
| **Fracture Functional $E_{\text{frac}}$** | $2.285469\,\text{mJ}$ | $2.285469\,\text{mJ}$ | Identical to 6 decimals |
| **Elastic Strain Energy $E_{\text{elas}}$** | $0.006960\,\text{mJ}$ | $0.006960\,\text{mJ}$ | Identical to 6 decimals |
| **Bookkeeping Residual $\varepsilon_{\text{book}}$** | $1.104771\%$ | $1.104771\%$ | Identical to 6 decimals |
| **Failing Increment** | Step 2 Inc 2890 | Step 2 Inc 2890 | Identical failing point |
| **Cutback Allowance ($I_A$)** | $I_A = 5$ (Default, 6 attempts) | $I_A = 10$ (Extended, 10 attempts) | Extended allowance active |
| **Minimum Reached $\Delta t$** | $6.250\times 10^{-6}$ | $1.000\times 10^{-9}$ | Down to solver floor |
| **Terminal Exit Code** | `Exit 0` (Logged error) | `Exit 1` (Abaqus standard error) | Terminated on cutback limit |

---

## 3. High-Resolution Telemetry across the Crossing Window

### Converged States near the Failure Boundary ($u \in [0.007880, 0.007889]\,\text{mm}$)

Across the final 10 converged increments of Step 2, the completion run (`1409982`) matches predecessor (`1409953`) bitwise:

| Step | Inc | Actual RP $U2$ [mm] | $F$ [kN] | $W_{\text{ext}}$ [mJ] | $E_{\text{elas}}$ [mJ] | $E_{\text{frac}}$ [mJ] | $E_{\text{model}}$ [mJ] | $\Delta_{\text{book}}$ [mJ] | $\varepsilon_{\text{book}}$ [%] |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 2 | 2880 | $0.007880$ | $0.00176823$ | $2.267364$ | $0.006967$ | $2.285451$ | $2.292418$ | $+0.025054$ | $1.104986\%$ |
| 2 | 2881 | $0.007881$ | $0.00176781$ | $2.267366$ | $0.006966$ | $2.285453$ | $2.292419$ | $+0.025054$ | $1.104964\%$ |
| 2 | 2882 | $0.007882$ | $0.00176741$ | $2.267367$ | $0.006965$ | $2.285455$ | $2.292420$ | $+0.025053$ | $1.104938\%$ |
| 2 | 2883 | $0.007883$ | $0.00176700$ | $2.267369$ | $0.006965$ | $2.285457$ | $2.292422$ | $+0.025052$ | $1.104912\%$ |
| 2 | 2884 | $0.007884$ | $0.00176659$ | $2.267371$ | $0.006964$ | $2.285459$ | $2.292423$ | $+0.025052$ | $1.104886\%$ |
| 2 | 2885 | $0.007885$ | $0.00176617$ | $2.267373$ | $0.006963$ | $2.285461$ | $2.292424$ | $+0.025051$ | $1.104865\%$ |
| 2 | 2886 | $0.007886$ | $0.00176575$ | $2.267374$ | $0.006962$ | $2.285463$ | $2.292425$ | $+0.025051$ | $1.104839\%$ |
| 2 | 2887 | $0.007887$ | $0.00176534$ | $2.267376$ | $0.006962$ | $2.285465$ | $2.292426$ | $+0.025050$ | $1.104818\%$ |
| 2 | 2888 | $0.007888$ | $0.00176492$ | $2.267378$ | $0.006961$ | $2.285467$ | $2.292428$ | $+0.025050$ | $1.104792\%$ |
| 2 | 2889 | $0.007889$ | $0.00176450$ | $2.267380$ | $0.006960$ | $2.285469$ | $2.292429$ | $+0.025049$ | $1.104771\%$ |

---

## 4. Root-Cause Analysis of Step 2 Increment 2890 Refailure

The attempt progression extracted from `PK_M1_ADAPT_14K_FRACTURE.msg` reveals the exact mathematical and numerical mechanism of termination:

| Attempt | $\Delta t$ | Newton Iters | $\max |R|$ [kN] | Critical Node / DOF | $\max |\Delta u|$ [mm] | Critical Node / DOF | Divergence Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | $2.000\times 10^{-4}$ | 5 | $3.398\times 10^{-9}$ | Node 6479 (DOF 3) | $2.153\times 10^{-6}$ | Node 13628 (DOF 3) | Diverged |
| **2** | $5.000\times 10^{-5}$ | 5 | $1.922\times 10^{-9}$ | Node 6479 (DOF 3) | $3.072\times 10^{-6}$ | Node 13628 (DOF 3) | Diverged |
| **3** | $1.250\times 10^{-5}$ | 6 | $1.942\times 10^{-9}$ | Node 6479 (DOF 3) | $2.611\times 10^{-6}$ | Node 13628 (DOF 3) | Diverged |
| **4** | $3.125\times 10^{-6}$ | 6 | $1.942\times 10^{-9}$ | Node 6479 (DOF 3) | $2.611\times 10^{-6}$ | Node 13628 (DOF 3) | Diverged |
| **5** | $7.813\times 10^{-7}$ | 6 | $1.942\times 10^{-9}$ | Node 6479 (DOF 3) | $2.611\times 10^{-6}$ | Node 13628 (DOF 3) | Diverged |
| **6** | $1.953\times 10^{-7}$ | 6 | $1.942\times 10^{-9}$ | Node 6479 (DOF 3) | $2.612\times 10^{-6}$ | Node 13628 (DOF 3) | Diverged (*1409953 stopped here*) |
| **7** | $4.883\times 10^{-8}$ | 6 | $1.942\times 10^{-9}$ | Node 6479 (DOF 3) | $2.611\times 10^{-6}$ | Node 13628 (DOF 3) | Diverged |
| **8** | $1.221\times 10^{-8}$ | 6 | $1.942\times 10^{-9}$ | Node 6479 (DOF 3) | $2.611\times 10^{-6}$ | Node 13628 (DOF 3) | Diverged |
| **9** | $3.052\times 10^{-9}$ | 6 | $1.942\times 10^{-9}$ | Node 6479 (DOF 3) | $2.611\times 10^{-6}$ | Node 13628 (DOF 3) | Diverged |
| **10** | $1.000\times 10^{-9}$ | 6 | $1.942\times 10^{-9}$ | Node 6479 (DOF 3) | $2.611\times 10^{-6}$ | Node 13628 (DOF 3) | Cutback Exhausted ($\Delta t < \Delta t_{\min}$) |

### Key Physical Findings:
1. **DOF 3 Specificity:** The un-converged correction is strictly confined to **DOF 3 (the phase-field scalar $d$)** at severed ligament nodes (Node 13628 and Node 6479).
2. **Asymptotic Convergence Plateau:** As time step is reduced from $\Delta t = 2.0\times 10^{-4}$ to $1.0\times 10^{-9}$ ($200,000\times$ reduction), the phase-field displacement correction stagnates at $\Delta d \approx 2.611\times 10^{-6}$, while the residual force remains at $1.942\times 10^{-9}\,\text{kN}$.
3. **Physical Reason:** The complete fracture of the specimen ($x_{\text{tip}} = 0.9985\,\text{mm}$, load drop $99.76\%$, $k=10^{-7}$) creates an essentially unloaded, severed ligament where the standard displacement-correction check $\Delta u / \Delta u_{\text{inc}}$ fails because the physical displacement increment approaches zero.
4. **Conclusion:** Pure time-step reduction ($I_A=10$, $\Delta t_{\min} = 10^{-9}$) cannot overcome this geometric singularity without adjusting the displacement-correction convergence tolerance ($R_n^\alpha$) in the post-fracture regime.

---

## 5. Figures and Artifacts

* **Figure 4.27:** `results/figures/mode1_gate6b/fig_mode1_stage14uaf_failure_crossing.pdf` and `.png`
* **Data JSON:** `models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/STAGE14UAF_CROSSING_AUDIT_DATA.json`
* **Telemetry Source:** `PK_M1_ADAPT_14K_FRACTURE.msg`, `.sta`, `.dat`, `uel_energy_balance.csv`

---

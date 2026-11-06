# Method C Paired C6 R12 Controlled Production Execution Report

**Task ID:** `F1630-METHOD-C-C6-R12-REPAIRED-DRIVER-PAIRED-EXECUTION`  
**Date:** 2026-11-06T09:11:25+01:00  
**Donor Reference:** Checkpoint 03 (Job `1419566.mmaster02`, $u_y = 0.0018703125442191958$ mm)  
**Receiver Mesh:** C6 Nonmatching Adaptive Mesh (15252 CPE4 quads, 15559 nodes, 59 seam pairs)  

---

## 1. Executive Summary & Terminal Metrics

This experiment isolates the effect of **safeguarded limited-memory Anderson acceleration ($m=2, \beta=0.85$)** on coupled staggered PDAS re-equilibration following gradient-preserving isoparametric bilinear Gauss-point state transfer onto the nonmatching C6 adaptive receiver mesh.

| Quantity | Arm A: Picard Baseline (P174) | Arm B: Safeguarded Anderson M2 (P175) | Matching-Iter Ratio (A/B) / Gate |
| :--- | :---: | :---: | :---: |
| **PBS Job ID** | `1420429.mmaster02` | `1420430.mmaster02` | - |
| **Scheduler State / Exit** | `F` (`Exit_status = 0`) | `F` (`Exit_status = 0`) | - |
| **Execution Host / Walltime** | `mnode098/0` (`01:20:20`) | `mnode098/1` (`01:21:28`) | - |
| **Iterations Completed** | 140 | 140 | - |
| **Final Relaxed $\Delta d$** | `7.6237e-03` | `7.6237e-03` | 1.0000x (Tol $\le 10^{-5}$) |
| **Final Raw $\Delta d_{\text{raw}}$** | `8.9691e-03` | `8.9691e-03` | 1.0000x (Tol $\le 10^{-5}$) |
| **Final Relaxed $\Delta u_{\text{rel}}$ [mm]** | `5.4774e-05` | `5.4774e-05` | 1.0000x (Tol $\le 10^{-9}$) |
| **Final Raw $\Delta u_{\text{raw}}$ [mm]** | `6.4441e-05` | `6.4441e-05` | 1.0000x (Tol $\le 10^{-9}$) |
| **Final $\Delta H$ [MPa]** | `3.1139e+02` | `3.1139e+02` | 1.0000x (Tol $\le 10^{-4}$) |
| **Signed KKT Dual / Free Error** | `1.4287e-09` / `6.0093e-08` | `1.4287e-09` / `6.0093e-08` | Tol $\le 10^{-6}$ (`True` / `True`) |
| **KKT Complementarity** | `4.2958e-08` | `4.2958e-08` | - |
| **Active Set Contraction** | 14088 -> 66 (99.5%) | 14088 -> 66 (99.5%) | +0.0% |
| **Stage-2 Iterations / Transitions** | 46 / 1 | 46 / 1 | - |
| **Anderson Steps / Fallbacks / Resets** | 0 / 0 / 0 | 0 / 19 / 114 | `ANDERSON_NEVER_ACTIVATED_GATED_BY_STAGE1_ACTIVE_SET` |
| **Rollbacks Triggered** | 0 | 0 | - |
| **Max Raw Healing Violations** | 3 (min margin `-3.3900e-06`) | 3 (min margin `-3.3900e-06`) | Tol: `0` |
| **Coupled Convergence** | FAIL | FAIL | - |
| **Reaction Force Drift** | 46.180% | 46.180% | Tol: <= 2.0% |
| **Total Energy Drift** | 2.722% | 2.722% | Tol: <= 2.0% |
| **Overall Physical Acceptance** | FAIL | FAIL | - |

---

## 2. Matching-Outer-Iteration Trajectory Comparison

- **Common Outer Iterations Evaluated:** `140` (last common outer iteration: `140`)
- **First Divergence Outer Iteration:** `None`
- **Anderson Acceleration Effect Classification:** `ANDERSON_NEVER_ACTIVATED_GATED_BY_STAGE1_ACTIVE_SET` (`demonstrated_anderson_effect = False`)

| Outer | Stage (A/B) | Anderson Applied (B) | $\Delta d$ (A / B) | $\Delta d_{\text{raw}}$ (A / B) | $\Delta u_{\text{rel}}$ [mm] (A / B) | $\Delta H$ [MPa] (A / B) | Active Set $|\mathcal{A}_k|$ (A / B) | $|\Delta \mathcal{A}_k|$ (A / B) |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `1` | `1/1` | `False` | `9.4277e-03` / `9.4277e-03` | `1.8855e-02` / `1.8855e-02` | `0.0000e+00` / `0.0000e+00` | `0.0000e+00` / `0.0000e+00` | `14088` / `14088` | `0` / `0` |
| `5` | `1/1` | `False` | `7.0310e-03` / `7.0310e-03` | `1.4062e-02` / `1.4062e-02` | `3.3388e-06` / `3.3388e-06` | `9.5579e-01` / `9.5579e-01` | `13559` / `13559` | `132` / `132` |
| `10` | `1/1` | `False` | `2.9607e-03` / `2.9607e-03` | `5.9213e-03` / `5.9213e-03` | `2.0789e-06` / `2.0789e-06` | `5.4312e-01` / `5.4312e-01` | `12761` / `12761` | `183` / `183` |
| `20` | `1/1` | `False` | `2.4873e-03` / `2.4873e-03` | `4.9747e-03` / `4.9747e-03` | `1.7866e-06` / `1.7866e-06` | `4.6561e-01` / `4.6561e-01` | `10459` / `10459` | `272` / `272` |
| `30` | `1/1` | `False` | `3.6156e-03` / `3.6156e-03` | `7.2312e-03` / `7.2312e-03` | `2.9504e-06` / `2.9504e-06` | `8.8858e-01` / `8.8858e-01` | `7159` / `7159` | `352` / `352` |
| `40` | `1/1` | `False` | `7.0079e-03` / `7.0079e-03` | `1.4016e-02` / `1.4016e-02` | `6.8748e-06` / `6.8748e-06` | `2.7894e+00` / `2.7894e+00` | `4502` / `4502` | `205` / `205` |
| `50` | `1/1` | `False` | `1.2738e-02` / `1.2738e-02` | `2.5477e-02` / `2.5477e-02` | `2.2378e-05` / `2.2378e-05` | `1.5740e+01` / `1.5740e+01` | `2699` / `2699` | `171` / `171` |
| `60` | `1/1` | `False` | `1.4885e-02` / `1.4885e-02` | `2.9771e-02` / `2.9771e-02` | `6.4991e-05` / `6.4991e-05` | `3.7344e+02` / `3.7344e+02` | `1555` / `1555` | `102` / `102` |
| `70` | `1/1` | `False` | `1.2732e-02` / `1.2732e-02` | `2.5464e-02` / `2.5464e-02` | `7.5956e-05` / `7.5956e-05` | `5.6870e+02` / `5.6870e+02` | `903` / `903` | `48` / `48` |
| `80` | `1/1` | `False` | `1.1022e-02` / `1.1022e-02` | `2.2043e-02` / `2.2043e-02` | `7.3945e-05` / `7.3945e-05` | `5.1078e+02` / `5.1078e+02` | `532` / `532` | `27` / `27` |
| `90` | `1/1` | `False` | `9.8001e-03` / `9.8001e-03` | `1.9600e-02` / `1.9600e-02` | `6.9295e-05` / `6.9295e-05` | `4.5924e+02` / `4.5924e+02` | `359` / `359` | `16` / `16` |
| `100` | `2/2` | `False` | `1.2934e-02` / `1.2934e-02` | `1.5217e-02` / `1.5217e-02` | `9.7420e-05` / `9.7420e-05` | `6.0685e+02` / `6.0685e+02` | `263` / `263` | `7` / `7` |
| `110` | `2/2` | `False` | `1.1312e-02` / `1.1312e-02` | `1.3308e-02` / `1.3308e-02` | `7.7203e-05` / `7.7203e-05` | `5.1843e+02` / `5.1843e+02` | `204` / `204` | `7` / `7` |
| `120` | `2/2` | `False` | `9.8998e-03` / `9.8998e-03` | `1.1647e-02` / `1.1647e-02` | `6.0215e-05` / `6.0215e-05` | `4.3108e+02` / `4.3108e+02` | `152` / `152` | `7` / `7` |
| `130` | `2/2` | `False` | `8.7039e-03` / `8.7039e-03` | `1.0240e-02` / `1.0240e-02` | `5.9538e-05` / `5.9538e-05` | `3.6514e+02` / `3.6514e+02` | `104` / `104` | `6` / `6` |
| `140` | `2/2` | `False` | `7.6237e-03` / `7.6237e-03` | `8.9691e-03` / `8.9691e-03` | `5.4774e-05` / `5.4774e-05` | `3.1139e+02` / `3.1139e+02` | `66` / `66` | `3` / `3` |

---

## 3. Scientific Interpretation & Dominant Bottleneck Analysis

### 3.1 Six-Point Mandatory Verdict (`F1630`)

1. **Strict Coupled Convergence (`FAIL` / `FAIL`):**
   - Neither Arm A (`1420429.mmaster02`, Picard baseline) nor Arm B (`1420430.mmaster02`, safeguarded Anderson $m=2$) achieved strict coupled convergence within the 140-outer-iteration budget (`280` Abaqus subproblem runs each, `Exit_status = 0`, walltimes `01:20:20` on `mnode098/0` and `01:21:28` on `mnode098/1`).
2. **Final Raw and Relaxed $\Delta d$, $\Delta u$, and $\Delta H$ (at `Outer 140`, plus Regime I Minimum at `Outer 16–18`):**
   - **Terminal (`Outer 140`, identical in Arm A and Arm B):**
     - Relaxed damage increment: $\Delta d = 7.623741\times 10^{-3}$ ($762.4\times$ above tolerance $10^{-5}$).
     - Raw damage increment: $\Delta d_{\text{raw}} = 8.969107\times 10^{-3}$ ($896.9\times$ above tolerance $10^{-5}$).
     - Relaxed displacement increment: $\Delta u_{\text{rel}} = 5.477445\times 10^{-5}\text{ mm}$ ($5.48\times 10^4\times$ above tolerance $10^{-9}\text{ mm}$).
     - Raw displacement increment: $\Delta u_{\text{raw}} = 6.444053\times 10^{-5}\text{ mm}$ ($6.44\times 10^4\times$ above tolerance $10^{-9}\text{ mm}$).
     - History increment: $\Delta H = 311.3948\text{ MPa}$ ($3.11\times 10^6\times$ above tolerance $10^{-4}\text{ MPa}$).
   - **Regime I Contraction Minimum (`Outer 16–18`, prior to runaway crack advance):**
     - $\Delta d$ contracted from $9.4277\times 10^{-3}$ (`O1`) to $2.4534\times 10^{-3}$ (`O18`); $\Delta u$ contracted from $4.7695\times 10^{-6}\text{ mm}$ (`O2`) to $1.6889\times 10^{-6}\text{ mm}$ (`O16`); $\Delta H$ contracted from $1.3183\text{ MPa}$ (`O2`) to **$0.4272\text{ MPa}$ (`O16`)** ($>200\times$ lower than the element-averaged R10 baseline).
3. **Signed KKT and Active-Set Status:**
   - **Signed KKT Stationarity (`PASS` at `Outer 140`):** `dual_error = 1.4287e-09 kN*mm` ($\le 10^{-6}$), `free_error = 6.0093e-08 kN*mm` ($\le 10^{-6}$), `complementarity = 4.2958e-08` ($\le 10^{-6}$), `kkt_final_pass = True`.
   - **Active-Set Trajectory:** Eroded monotonically from $|\mathcal{A}_1| = 14,088$ (`1,471` free nodes) to $|\mathcal{A}_{140}| = 66$ (`15,493` free nodes, `99.53%` contraction). Both arms transitioned from Stage 1 ($\omega_d = 0.50, \omega_u = 1.00$) to Stage 2 ($\omega_d = 0.85, \omega_u = 0.85$) at `Outer 95` when $|\mathcal{A}_{94}| = 316 \le 500$, $|\Delta \mathcal{A}_{92..94}| = 13, 8, 8$, and $\Delta \mathcal{A}^+ = 0$.
4. **Whether Anderson Genuinely Accelerated Any Accepted Iterations (`False` — `0` Steps Applied):**
   - **Bitwise Identical Trajectories (`first_divergence_outer = null`):** Arm A and Arm B produced bitwise identical iterates across all 140 outer iterations (`ratio = 1.0000x` on every metric).
   - **Exact Breakdown of All 140 Iterations in Arm B:**
     - `Outer 1..94` (94 iterations): Gated off in Stage 1 (`reason = "stage1"`), triggering `94` memory resets.
     - `Outer 95..140` (46 iterations in Stage 2):
       - `20` iterations had $|\Delta \mathcal{A}_k| > 5$ (`anderson_max_active_diff = 5`), triggering `20` additional active-set memory resets (`total_resets = 114`).
       - `6` iterations had $|\Delta \mathcal{A}_k| \le 5$ with empty history `m_k = 0` (`reason = "insufficient_history"`).
       - `19` iterations (`O103, O106, O112, O113, O119, O122..O128, O134..O140`) had $|\Delta \mathcal{A}_k| \le 5$ and `m_k >= 1`, solved the regularized least-squares system with well-bounded coefficients $\|\gamma\|_2 \in [7.59, 21.75] \le 200$, and proposed an extrapolated step $\|\Delta d_{\text{prop}}\|_\infty \in [0.1013, 0.1166] > 0.045$ (`anderson_max_step_cap = 0.045`). Because `AndersonAccelerator.compute_step` performs a **binary rejection fallback to the damped Picard step** (`reason = "oversized_step"`, `anderson_fallbacks_count = 19`) rather than direction-preserving step scaling, **zero Anderson steps were ever applied** (`anderson_accelerations_count = 0`).
   - Consequently, per the pre-declared `HND-5b361e69abda` evaluation contract, `F1630` is classified as **NOT demonstrating an Anderson acceleration effect** (`ANDERSON_NEVER_ACTIVATED_GATED_BY_STAGE1_ACTIVE_SET`).
5. **Final Force, Energy, Irreversibility, and Checkpoint Acceptance (`FAIL` — Checkpoint Suppressed):**
   - **Reaction Force Continuity (`FAIL`):** $F_y = 0.096835\text{ kN}$ vs donor $0.179924\text{ kN}$ (`-46.180%` drift, gate $\le 2.0\%$). Note: during Regime I (`Outer 1..18`), $F_y \in [0.178654, 0.180578]\text{ kN}$ (`0.363%` to `-0.706%` drift) satisfied the $\le 2.0\%$ continuity gate before Regime II crack propagation collapsed the load capacity.
   - **Total Energy Continuity (`FAIL`):** $E_{\text{tot}} = 2.202372\times 10^{-4}\text{ kN}\cdot\text{mm}$ ($E_{\text{elas}} = 9.05104\times 10^{-5}$, $E_{\text{frac}} = 1.297268\times 10^{-4}\text{ kN}\cdot\text{mm}$) vs donor $2.263990\times 10^{-4}\text{ kN}\cdot\text{mm}$ (`-2.722%` drift, gate $\le 2.0\%$).
   - **Damage Irreversibility & Bounds:** Post-relaxation clamped damage satisfied $0 \le d \le 1$ (`d_max = 0.998604`) and $d \ge d_0$ (`0` clamped violations); the raw Abaqus phase subproblem had `3` minor healing violations (`min(d_raw - d0) = -3.3900e-06 < -1e-6`). Thermodynamic consistency ($H \ge \psi_e^+$, `0` violations) and history monotonicity ($H \ge H_0$, `0` violations) passed.
   - **Checkpoint Acceptance (`REJECTED / SUPPRESSED`):** Neither job wrote `converged_checkpoint_01.json`, preserving fail-closed checkpoint hygiene.
6. **Dominant Cause of Nonconvergence:**
   - **Dominant Residual:** $\Delta H = 311.39\text{ MPa}$ (`3.11e6x` above tolerance $10^{-4}\text{ MPa}$, peaking at $606.85\text{ MPa}$ at `O100`), coupled with $\Delta u_{\text{raw}} = 6.44\times 10^{-5}\text{ mm}$ (`6.44e4x`) and $\Delta d_{\text{raw}} = 8.97\times 10^{-3}$ (`896.9x`).
   - **Physical & Algorithmic Mechanism:** After initial contraction in `Outer 1..18` ($\Delta H = 0.427\text{ MPa}$, force drift $\le 0.71\%$), the coupled loop enters **Regime II (`Outer 19..140`)**: unsteady supercritical crack propagation at fixed boundary displacement $u_y = 0.0018703125\text{ mm}$ ($d_{\max}: 0.690981 \to 0.998604$, $E_{\text{frac}}: 5.814\times 10^{-5} \to 1.297\times 10^{-4}\text{ kN}\cdot\text{mm}$, $F_y: 0.1799 \to 0.0968\text{ kN}$).
   - **Root Cause of the Regime II Runaway (Shared with Same-Mesh C5 Control `1420353.mmaster02`):**
     1. *Donor Checkpoint 03 (`1419566.mmaster02`) History-Damage Inconsistency:* In `driver_package167_c5_continuation.py` (`1419566.mmaster02`), `_deck` retained `*INCLUDE, INPUT="initial_conditions_solution.inc"` (which held static history with $\max H = 13.97\text{ MPa}$) instead of injecting the updated trial history ($\max H = 98.18\text{ MPa}$) into Abaqus, while `converged_checkpoint_03.json` exported the Python-recomputed history ($\max H = 98.18\text{ MPa}$) paired with the un-advanced damage field ($\max d = 0.690981$). When `1420353.mmaster02` (C5 Control) and `1420429.mmaster02`/`1420430.mmaster02` (C6 R12) injected the $98.18\text{ MPa}$ / $85.56\text{ MPa}$ history into Abaqus `*Initial Conditions, type=SOLUTION`, the phase field was strongly over-driven relative to $d_0$.
     2. *Unscaled PDAS Penalty Release ($c_{\text{pdas}} = 10^3\text{ (kN}\cdot\text{mm)}^{-1}$):* On active nodes ($d_n = d_{0,n}$), the condition $d_n - c_{\text{pdas}} r_n \le d_{0,n} + \varepsilon_{\text{pdas}}$ releases every node with $r_n < -\varepsilon_{\text{pdas}}/c_{\text{pdas}} = -10^{-9}\text{ kN}\cdot\text{mm}$, allowing the over-driven crack-tip damage wave to progressively unlock `99.53%` of the mesh (`14,088 -> 66` nodes).
     3. *Binary Anderson Step Rejection in Stage 2:* When the active set finally stabilized enough to reach Stage 2 (`O95..O140`), all 19 Anderson extrapolation steps were rejected (`fallback_to_picard`) because $\|\Delta d_{\text{prop}}\|_\infty \approx 0.108 > 0.045$ triggered binary rejection rather than direction-preserving step scaling.

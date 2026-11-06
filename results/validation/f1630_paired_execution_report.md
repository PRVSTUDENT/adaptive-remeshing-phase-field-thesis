# Method C Paired C6 R12 Controlled Production Execution Report

**Task ID:** `F1630-METHOD-C-C6-R12-REPAIRED-DRIVER-PAIRED-EXECUTION`  
**Date:** 2026-11-06T10:50:03+01:00  
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

- **ANDERSON ACTIVATION CLASSIFICATION (`ANDERSON_NEVER_ACTIVATED_GATED_BY_STAGE1_ACTIVE_SET`):** Because Anderson acceleration in Arm B is gated behind Stage 2 transition and active-set stabilization ($|\mathcal{A}_k| \le 500$, $|\Delta \mathcal{A}_k| \le 10$, $\Delta \mathcal{A}_k^+ = 0$ for 3 consecutive iterations), and `anderson_steps_applied == 0`, this experiment **does NOT demonstrate an Anderson acceleration effect** (neither equivalence nor superiority of Anderson extrapolation itself).
- **COUPLED NONCONVERGENCE PRESERVED:** Neither arm satisfied the strict coupled convergence thresholds in 140 iterations.
- **Dominant Residual Exceedance (Arm A / Arm B):** `delta_h` / `delta_h` (exceedance ratios: `{"delta_d": 762.3740766273922, "raw_delta_d": 896.9106783851654, "delta_u_relaxed": 54774.44911915078, "delta_u_raw": 64440.52837547144, "delta_h": 3113948.4253715635}`).
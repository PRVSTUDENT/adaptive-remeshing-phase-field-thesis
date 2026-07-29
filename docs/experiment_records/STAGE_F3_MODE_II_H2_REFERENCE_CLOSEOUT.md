# Stage F3 Experiment Record: Mode-II H2 Uniform Reference Closeout

**Task ID:** `F3-STAGE-F3-COMBINED-SCIENTIFIC-CLOSEOUT`  
**Stage:** Stage F (Mode-II Pure-Shear Benchmark)  
**PBS Job ID:** `1379578.mmaster02`  
**Job Name:** `mode_ii_h2_serial`  
**Package:** `models/generated/mode_ii/h2_uniform_serial`  
**Authorization SHA:** `a04db3c11a444d9a3f0ec2f5d64120747f5ea18a`  
**Submission SHA:** `3fad785274b24e3d67f9bd8400cc44a6c911ae2c`  
**Main Closure Commit:** `f9fa2424c8c0f9c704a186822aeb0430f1067a1f`  
**Execution Queue:** `entry_imfdfkmq` (`normal_imfdfkmq`)  
**Execution Host:** `mnode104/0` (`tu_freiberg` cluster)  

---

## 1. Objective & Model Overview

The primary objective of Job `1379578.mmaster02` is to establish the fine uniform reference solution ($H_2$ mesh level: $33,852$ physical UEL continuum elements, 15 coincident node pairs along the true notch slit) for the Mode-II shear benchmark.

- **Mesh Resolution:** $H_2$ fine uniform grid ($h_{min} \approx 0.0025\text{ mm}$ around notch tip, 33,852 UEL elements, 34,509 nodes)
- **Material Parameters:** $E = 210\text{ GPa}$, $\nu = 0.3$, $G_c = 2.7 \times 10^{-3}\text{ kN/mm}$, $l_c = 0.015\text{ mm}$
- **Prescribed Endpoint:** Prescribed displacement up to $U_1 = 0.007\text{ mm}$ (Step 1: linear ramp to $0.005\text{ mm}$ in 0.5 s; Step 2: linear ramp to $0.007\text{ mm}$ in 0.2 s)

---

## 2. Scheduler Performance & Resource Usage

| Resource / Parameter | Target / Requested | Actual Execution | Validation Status |
| :--- | :--- | :--- | :--- |
| **PBS Job ID** | `1379578.mmaster02` | `1379578.mmaster02` | Matched |
| **Scheduler Exit Code** | `0` | `0` | `[PASS]` |
| **Execution State** | `F` (Finished) | `F` (Finished) | `[PASS]` |
| **Requested Cores / RAM** | 1 CPU, 16 GB RAM | 1 CPU, 1.42 GB RAM | `[PASS]` |
| **Requested Walltime** | 12:00:00 | 02:04:01 (Walltime) | `[PASS]` |
| **CPU Time** | — | 01:59:35 (7,175.0 s) | `[PASS]` |
| **Abaqus Version** | SIMULIA Abaqus Standard | `Abaqus 2023` | `[PASS]` |

---

## 3. Verified Elastic Parity & Full Extracted Results

| Scientific Metric | H1 Reference (`1379482.mmaster02`) | H2 Reference (`1379578.mmaster02`) | Parity Status / Difference |
| :--- | :--- | :--- | :--- |
| **Physical Elements ($N_{\mathrm{elem}}$)** | 12,064 | 33,852 | Refinement ratio $2.80\times$ |
| **$h / l_c$** | $0.1667$ | $0.0625$ | Refined notch-tip mesh |
| **Stiffness Interval** | $[0.0002, 0.0020]\text{ mm}$ | $[0.0002, 0.0020]\text{ mm}$ | Identical 19-point window |
| **Fitted Stiffness ($K_0$)** | $12.809336\text{ kN/mm}$ | $12.791160\text{ kN/mm}$ | **$-0.1418\%$** (`[PASS]`) |
| **Fitted Intercept ($C$)** | $+0.00001464\text{ kN}$ | $+0.00001464\text{ kN}$ | Zero intercept matched |
| **$R^2$** | $0.99999949$ | $0.99999949$ | Perfect linear fit |
| **Max Damage in Interval** | $0.007743$ | $0.007996$ | Negligible elastic damage |
| **Displacement Endpoint ($U_1$)** | $0.020000\text{ mm}$ | $0.007000\text{ mm}$ | Prescribed Step 2 endpoint |
| **Peak Force ($RF_{1,\max}$)** | $0.139789\text{ kN}$ at $U_1 = 0.0120\text{ mm}$ | $0.087467\text{ kN}$ at $U_1 = 0.0070\text{ mm}$ | Pre-peak endpoint for H2 |
| **Final Force ($RF_{1,\text{final}}$)** | $0.081230\text{ kN}$ | $0.087467\text{ kN}$ | — |
| **Force Drop $\%$** | $41.89\%$ | $0.0\%$ | 0% (H2 endpoint < peak) |
| **First $U_1(d \ge 0.5)$** | $0.012000\text{ mm}$ | `null` (not reached yet) | Pre-peak state ($d_{max} = 0.12$) |
| **Max Phase Damage ($d_{\max}$)** | $1.004978$ | $0.119955$ | Pre-peak elastic damage |
| **Elastic Parity Classification** | `converged_with_H1` | `converged_with_H1` | **PASS** ($-0.1418\%$) |
| **Fracture Classification** | `postpeak_converged` | `fracture_convergence_unresolved` | **UNRESOLVED** (H2 pre-peak) |

---

## 4. Invalidation of Preliminary H2 Stiffness Artifact

- **Preliminary Artifact Value:** $K_{H2} = 460.693724\text{ kN/mm}$
- **Invalidation Status:** `INVALID_EXTRACTION_ARTIFACT`
- **Root Cause:** Preliminary extractor script sampled the single first output frame at $U_1 = 0.0001\text{ mm}$ ($RF_1 = 0.046069\text{ kN}$) without a proper regression window or step boundary offset handling.
- **Physically Validated Stiffness:** $\boxed{K_{\mathrm{H2}} = 12.791160\text{ kN/mm} \approx 12.81\text{ kN/mm}}$

---

## 5. Evidence Inventory & Repository References

| Artifact Description | Repository Path | SHA-256 Hash |
| :--- | :--- | :--- |
| **H2 Evidence Dir** | [runs/hpc/stage_f/mode_ii_h2/evidence/1379578.mmaster02/](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h2/evidence/1379578.mmaster02/) | Directory |
| **Unified Extractor Script** | `scripts/postprocessing/extract_mode_ii_uniform_reference.py` | `0d9124ae87edee6ce6aa494d4d12c8ff4a8cfdd5edacb726ef3c3e80352efdfa` |
| **Stiffness Comparison JSON** | `runs/hpc/stage_f/H1_H2_ELASTIC_STIFFNESS_COMPARISON.json` | `4bd5037d45e065bc3e51fbe09009fa50ae3e3d3b769f3ef4ae2be8165a2512f4` |
| **Stiffness Points CSV** | `runs/hpc/stage_f/H1_H2_ELASTIC_STIFFNESS_POINTS.csv` | `04bfb07358d7cce97c11f7c32bfbcbeebbc8fdff37ffaa2d590498eb79e2a4be` |
| **Stiffness Regression Fit Fig** | `results/figures/mode_ii_h2/H1_H2_ELASTIC_STIFFNESS_FIT.png` | `0ecb9691dd93fce1ce27a27eb2a2ff82cbfb275bf1efb448a3359d95f4fb495f` |
| **Full Curve Overlay Fig** | `results/figures/mode_ii_h2/H1_H2_RF1_U1_OVERLAY.png` | `ce9b43ed3b89fa5a85ca9592fef2ef39df8813faea2189d21c97aee3bfa61324` |
| **MISESERI Provenance Notice** | `runs/hpc/stage_f/miseseri_preanalysis/evidence/1379579.mmaster02/PROVENANCE_NOTICE.md` | `eb8eb47eb10815777174faaf81c62bd93cf02b92fae3f1e948c26bc72eef0143` |
| **Corrective MISESERI Bundle** | `runs/hpc/stage_f/miseseri_preanalysis/corrective_interactive_runs/2026-07-29T070232_CEST/` | Directory |

---

## 6. Scope & Limitations

1. **Established Claim:** This task establishes elastic parity between H1 ($12.8093\text{ kN/mm}$) and H2 ($12.7912\text{ kN/mm}$) to within $-0.1418\%$.
2. **Unresolved Fracture Status:** Job `1379578.mmaster02` stopped at displacement endpoint $U_1 = 0.007\text{ mm}$ (before peak $U_1 = 0.012\text{ mm}$). Full post-peak softening force drop for H2 remains `UNRESOLVED` until an $H_2$ job at $U_1 = 0.020\text{ mm}$ is explicitly authorized.
3. **Boundary Limitations:** The binary output database (`ModeII_H2_uniform_serial.odb`, 660 MB) remains strictly in HPC scratch (`/scratch/pr21vyci/adaptive-remeshing/runs/mode_ii_h2_serial_1379578.mmaster02/`). No ODB was committed to Git.
4. **No Retries/Submissions:** `qsub count` for this closeout task is strictly `0`.

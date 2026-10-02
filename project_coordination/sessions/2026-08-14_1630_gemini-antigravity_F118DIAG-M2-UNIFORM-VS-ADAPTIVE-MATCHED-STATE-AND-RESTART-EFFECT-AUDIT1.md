# Session Report: Mode-II Uniform vs Adaptive Matched-State & Restart-Effect Scientific Audit

- **Task ID**: `F118DIAG-M2-UNIFORM-VS-ADAPTIVE-MATCHED-STATE-AND-RESTART-EFFECT-AUDIT1`
- **Agent**: `gemini-antigravity`
- **Date**: 14 August 2026
- **Status**: `COMPLETED`
- **Starting Git Commit**: `b6e9b4ea5d4b3d012b2500a52b069a6a3423e37c`

---

## 1. Objectives & Executive Summary

This session executed a rigorous scientific audit evaluating the large discrepancy between the completed uniform reference simulations (`M2REF_H1_FULL_U050`, Job `1389351.mmaster02` and `M2REF_H2_FULL_U050`, Job `1389352.mmaster02`) and the multi-stage adaptive remeshing trajectory (`M2STATE_FRACFIX_RESTART2R14`, Job `1389328.mmaster02`).

**Core Verdict**:
- Uniform spatial convergence is **PROVEN** ($0.4207\%$ peak force difference between H1 and H2).
- Adaptive accuracy claim vs H2 is **NOT VALIDATED**.
- The apparent adaptive peak at $u_1 = 0.030\text{ mm}$ ($0.654321\text{ kN}$) is strongly coupled to the `PhaseInit` clamped restart boundary condition; upon phase DOF release in Step 2 Increment 1, reaction force drops immediately by **$31.27\%$ ($0.204611\text{ kN}$ drop)** to $0.449710\text{ kN}$ ($d_{\max} \to 0.9975$).
- Adaptive cumulative CPU time was **$+45.2\%$ greater** than fine uniform H2 due to 4 sequential multi-step runs. The claim of "71.6% computational saving" is unsupported for the full process.
- Designed the minimum independent 2-job control batch (`PK10R1_CONTINUOUS_U050` and `PK10R1_IDENTITY_RESTART_U050`) to definitively isolate mesh resolution from restart artifacts.

---

## 2. Independent Verification of Uniform Reference Runs

- **H1 (`1389351.mmaster02`)**:
  - `H1_scheduler_result`: `PASS` (PBS job finished with exit code 0 on `normal_imfdfkmq`)
  - `H1_technical_result`: `PASS` (Abaqus 2023 completed 109 increments to $u_1 = 0.050000\text{ mm}$, 0 cutbacks, 0 NaNs)
  - `H1_scientific_result`: `PASS` (Equilibrium converged, $RF_1 = 0.859300\text{ kN}$ at $u_1 = 0.043143\text{ mm}$)
- **H2 (`1389352.mmaster02`)**:
  - `H2_scheduler_result`: `PASS` (PBS job finished with exit code 0 on `normal_imfdfkmq`)
  - `H2_technical_result`: `PASS` (Abaqus 2023 completed 109 increments to $u_1 = 0.050000\text{ mm}$, 0 cutbacks, 0 NaNs)
  - `H2_scientific_result`: `PASS` (Equilibrium converged, $RF_1 = 0.855700\text{ kN}$ at $u_1 = 0.042143\text{ mm}$)

---

## 3. Matched-State Comparison Table

| Target $U_1$ (mm) | Uniform H1 $RF_1$ (kN) | Uniform H2 $RF_1$ (kN) | Adaptive Trajectory $RF_1$ (kN) | Adaptive vs H2 Error (%) | H1 vs H2 Diff (%) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **0.005** | $0.224738$ | $0.224538$ | $0.120610$ (PK5 term) | **$-46.29\%$** | $0.0891\%$ |
| **0.010** | $0.421063$ | $0.420735$ | $0.316163$ (R1 term / R2 Step 1) | **$-24.85\%$** | $0.0781\%$ |
| **0.020** | $0.685640$ | $0.684569$ | $0.528400$ (R2R13 Step 2) | **$-22.81\%$** | $0.1565\%$ |
| **0.025** | $0.762298$ | $0.760727$ | $0.598000$ (R2R13 Step 2) | **$-21.39\%$** | $0.2066\%$ |
| **0.030 (Step 1 PhaseInit)** | $0.812356$ | $0.810385$ | $0.654321$ (R2R14 Step 1) | **$-19.26\%$** | $0.2433\%$ |
| **0.030010 (Step 2 First Free)** | $0.812436$ | $0.810463$ | **$0.449710$ (R2R14 Step 2 Inc 1)** | **$-44.51\%$** | $0.2434\%$ |
| **0.030218 (Min Post-Peak)** | $0.814070$ | $0.812055$ | **$0.272649$ (R2R14 Step 2 min)** | **$-66.42\%$** | $0.2481\%$ |
| **0.035** | $0.842371$ | $0.839971$ | $0.363000$ (R2R14 Step 2) | **$-56.78\%$** | $0.2857\%$ |
| **0.040** | $0.856228$ | $0.853300$ | $0.453000$ (R2R14 Step 2) | **$-46.91\%$** | $0.3432\%$ |
| **0.042143 (H2 Peak)** | $0.858300$ | **$0.855700$** | $0.490000$ (R2R14 Step 2) | **$-42.74\%$** | $0.3038\%$ |
| **0.050 (Terminal)** | $0.843400$ | $0.834900$ | $0.618473$ (R2R14 Step 2 term) | **$-25.92\%$** | $1.0181\%$ |

---

## 4. Adaptive Restart & Clamp-Release Force Continuity Chain

1. **PK5 -> R1R11 ($u_1 = 0.005\text{ mm}$)**:
   - State transfer jump: $0.0000\%$ ($RF_1 = 0.120610 \to 0.120610\text{ kN}$)
   - First free increment jump: $+0.000040\text{ kN}$ ($+0.03\%$)
2. **R1R11 -> R2R13 ($u_1 = 0.010\text{ mm}$)**:
   - State transfer jump: $0.0000\%$ ($RF_1 = 0.316163 \to 0.316163\text{ kN}$)
   - First free increment jump: $+0.000337\text{ kN}$ ($+0.11\%$)
3. **R2R13 -> R2R14 ($u_1 = 0.030\text{ mm}$)**:
   - State transfer jump: $0.0020\%$ ($RF_1 = 0.654334 \to 0.654321\text{ kN}$)
   - Phase clamped during Step 1: $d_{\max} = 0.8457$
   - First free increment jump (Phase released in Step 2): **$0.204611\text{ kN}$ drop ($31.27\%$)** from $0.654321 \to 0.449710\text{ kN}$ with $d_{\max} \to 0.9975$.

---

## 5. Control Batch Design

1. **`PK10R1_CONTINUOUS_U050`**:
   - Scientific Question: What is the intrinsic continuous response of the refined adaptive mesh topology ($PK10R1$, $9,612$ elements) from virgin state ($u_1 = 0 \to 0.050\text{ mm}$) without any remeshing, state transfer, or PhaseInit restart interruptions?
   - Resources: 1 CPU / 16 GB / 24:00:00 / `entry_imfdfkmq`
2. **`PK10R1_IDENTITY_RESTART_U050`**:
   - Scientific Question: What is the isolated numerical effect of the PhaseInit clamp-and-release restart procedure on the identical $PK10R1$ mesh when restarting at $u_1 = 0.030\text{ mm}$ with zero mesh change?
   - Resources: 1 CPU / 16 GB / 24:00:00 / `entry_imfdfkmq`

# Gate-6B Mode-I Stage 14M Corrected-Job Early Mechanical Parity Checkpoint Report

**Protocol Version:** 2  
**Task ID:** `F1190-GATE6B-STAGE14M-CORRECTED-ADAPTIVE-EARLY-CHECKPOINT-20261003`  
**Evaluation Timestamp:** `2026-10-03T22:40:00+02:00`  
**Governing Phase:** `MODE1_GATE6B_ACTIVE_EVALUATION_AND_CONTINUATION`  
**Overall Verdict:** `CORRECTED_JOB_EARLY_MECHANICAL_CHECKPOINT_ONLY`  

---

## 1. Executive Summary & Epistemological Status

This report establishes the first non-invasive early mechanical parity audit of the active corrected Stage 14 adaptive fracture solver run (**Job `1409953.mmaster02`**, `PK_M1_ADAPT_14K_FRACTURE`, running on compute node `mnode097`).

### Key Checkpoint Findings:
1. **Physical Elasticity Scale Restored:**
   - The corrected solve exhibits reaction forces on the order of 10^-2 to 10^-1 kN ($F = 0.046949	ext{ kN}$ at $u = 0.000340	ext{ mm}$), matching the fixed reference benchmark (`1409734.mmaster02`) within **-0.026%** pointwise force difference.
   - This formally and empirically confirms the resolution of the parameter ABI card inversion that invalidated Job `1409947.mmaster02` (where $F$ was $\sim 10^{-6}	ext{ kN}$, 28,000x too compliant).
2. **$K_0$ Semantics Correction:**
   - In Stage 14L, the early estimate 138.11 kN/mm was quoted as $K_0$. We clarify that 138.11 kN/mm was an energy-derived elasticity diagnostic ($K_{\text{energy}} = 2 E_{\text{elas}} / u^2$), **not** the canonical structural stiffness $K_0$.
   - Canonical $K_0$ requires half-bin OLS linear regression across the complete $N=400$ increments ($u \le 0.0010	ext{ mm}$).
   - Because Job `1409953` has currently reached Increment 136 ($u = 0.0003400	ext{ mm} < 0.0010	ext{ mm}$), the canonical $K_0$ status is formally designated as:
     $$\mathbf{CANONICAL\_K_0 = NOT\_YET\_QUALIFIED\ (INTERIM\_WINDOW\_INCOMPLETE:\ 136/400\ INCS)}$$
   - The interim OLS fit across the available 136 increments yields $K_{\text{interim}} = 138.086824	ext{ kN/mm}$ ($R^2 = 0.99999999$, intercept = $1.790e-06	ext{ kN}$), agreeing with reference $K_0 = 137.945520	ext{ kN/mm}$ within **+0.102%**.

---

## 2. Quantitative Metric Summary Table

| Metric | Active Corrected Candidate (`1409953`) | Qualified Fixed Reference (`1409734`) | Invalidated Benchmark (`1409947`) | Checkpoint Status |
| :--- | :---: | :---: | :---: | :---: |
| **Solver Status** | **RUNNING (`mnode097`)** | Complete (Exit 0) | Cancelled (ABI Mismatch) | Active solving |
| **Completed Incs** | **136 / 2000 (Step 1)** | 7000 / 7000 | 4937 (Step 2) | Advancing steadily |
| **Latest $u$** | **0.0003400 mm** | 0.010000 mm | 0.007937 mm | Early elastic branch |
| **Latest Force $F$** | **0.046949 kN** | 0.046961 kN | ~ 10^-6 kN | **MATCH PASS (-0.026%)** |
| **Mean Pointwise $\Delta F$** | **-0.0258%** | Baseline (0.0%) | -99.996% | **EXCELLENT PARITY** |
| **Interim OLS Slope** | **138.086824 kN/mm** | 137.945520 kN/mm | 0.004945 kN/mm | **+0.102% vs Ref** |
| **Interim OLS $R^2$** | **0.99999999** | 0.99999960 | 1.00000000 | Strictly linear |
| **Interim OLS Intercept**| **1.790e-06 kN** | -2.81e-5 kN | +1.2e-9 kN | Vanishing zero-offset |
| **Energy $K_{\text{energy}}$** | **138.083782 kN/mm** | 137.924 kN/mm | ~ 0.005 kN/mm | **+0.119% vs Ref** |
| **Canonical $K_0$** | **`NOT_YET_QUALIFIED`** | 137.945520 kN/mm | Invalid | **Window incomplete (136/400)** |

---

## 3. Solver Telemetry & Stability

- **Cutbacks:** 0 across all 136 increments.
- **Equilibrium Iterations:** Constant 3 iterations per increment under standard Newton-Raphson.
- **Advancement Rate:** $\Delta u = 2.5\times 10^{-6}\text{ mm/inc}$ ($\Delta t = 5.0\times 10^{-4}$ per increment).
- **Execution Mode:** Serial 1-CPU on node `mnode097` in queue `normal_imfdfkmq`.

---

## 4. Governance & Closeout Instructions

1. **Job Preservation:** Leave PBS Job `1409953.mmaster02` running untouched until terminal completion. Strictly NO cancellation, NO resubmission, and NO automated polling loops.
2. **Terminal Evaluation Requirement:** When Step 1 reaches Increment 400 ($u = 0.0010\text{ mm}$), extract the complete $N=400$ dataset to compute the official canonical $K_0$.
3. **Full Fracture Evaluation:** Upon solver completion (Step 2 terminal displacement $u = 0.0100\text{ mm}$), execute the frozen terminal evaluation protocol `evaluate_mode1_stage14_adaptive_14k.py` across all 10 matched displacement states.

# Session Report: F1493 Method C Scientific Verification & Trajectory Audit

**Date:** 2026-10-16  
**Agent:** gemini-antigravity  
**Task ID:** F1493-METHOD-C-SCIENTIFIC-VERIFICATION  
**Starting Commit:** `bea59480fc0466d9d55bcd02bf91e3532dc871d2`  
**Active PBS Jobs:** `1413895.mmaster02` (Production restart), `1413896.mmaster02` (Diagnostic restart)  
**Governed Status:** `METHOD_C_SAME_MESH_RESTART_EXECUTING__STATE_CONTINUITY_NOT_YET_QUALIFIED`  

---

## 1. Executive Summary

Task F1493 scientifically evaluated the running Method C restart continuation on the Mode-I benchmark, resolving two key apparent anomalies before any advancement to nonmatching mesh transfer (Stage C1-1):

1. **Reaction Force Discrepancy Resolution**:
   - *Observation*: Solvers reached reaction forces $> 934\,\text{N}$ at $u = 0.0075\,\text{mm}$ and $> 1005\,\text{N}$ at $u = 0.0082\,\text{mm}$, whereas the fine-mesh ($15{,}192$ elements, $h = 3\,\mu\text{m}$) Mode-I reference reaches $F_{\max} \approx 757.8\,\text{N}$ at $u = 0.00586\,\text{mm}$.
   - *Physical Cause*: Coarse-mesh spatial smearing ($h \approx 14.3\,\mu\text{m} \approx 2 l_0 > l_0 / 2$). In phase-field fracture mechanics, when element size cannot resolve the regularization length ($l_0 = 7.5\,\mu\text{m}$), structural compliance is overestimated and fracture propagation is delayed to higher peak loads.
   - *Quantitative Parity*: The uninterrupted baseline Job `1412809` on the exact same $2{,}906$-element mesh reached $F_{\max} = 1085.41\,\text{N}$ at $u = 0.009219\,\text{mm}$, followed by complete softening down to $27.26\,\text{N}$ at $u = 0.0100\,\text{mm}$. Production Restart (`1413895`) matches this uninterrupted baseline within **$0.010\%\text{--}0.019\%$** across all evaluated displacement stations ($u = 0.0055, 0.0060, 0.0065, 0.0070, 0.0075\,\text{mm}$), proving that the high force is authentic physical coarse-mesh behavior, not a state-continuation defect.

2. **Fracture Energy Discontinuity (+11.4%) Root Cause**:
   - *Observation*: Diagnostic restart displayed a $+11.4\%$ fracture energy jump at the restart boundary ($0.03416\,\text{mJ}$ vs donor $0.03066\,\text{mJ}$).
   - *Forensic Isolation*: In `f42_mixed_uel_restart_diagnostic.for` (lines 271–274), the restart initialization loop for triangular elements (JTYPE=3) reads `DO KPT=1, 3; SV_H_COMMITTED(PHYSIDX, KPT) = SVARS(6+KPT); ENDDO`. For $KPT=1$, `SVARS(7)` corresponds to `D_AVG` ($\sim 0.05\text{--}0.10$), whereas `SVARS(8)` and `SVARS(9)` are `HIST` ($\sim 0.001\text{--}0.02\,\text{MPa}$). Loading `D_AVG` into `SV_H_COMMITTED` for $KPT=1$ injected an artificial crack-tip history spike into all 88 triangular elements, producing the $+3.50\,\mu\text{J}$ (+11.4%) step artifact.
   - *Production UEL Conservation*: The production UEL (`f42_mixed_uel.for`) does not contain this defective ingestion loop. Its Increment 1 fracture energy is $0.0306863\,\text{mJ}$ (matching donor $0.0306625\,\text{mJ}$ within $+0.078\% \le 0.50\% \implies \text{PASS}$). Its elastic energy error is $+0.039\% \le 0.50\%$, and total energy error is $+0.039\% \le 0.50\%$.

---

## 2. Quantitative Comparison Table

### Force-Displacement Parity (Reaction Force in N)
| $u$ (mm) | Job 1412809 (Uninterrupted) | Job 1413895 (Prod Restart) | Relative Error (%) | Job 1413896 (Diag Restart) |
| :--- | :--- | :--- | :--- | :--- |
| **0.005001** | 653.17 | 653.21 | **+0.006%** | 652.14 |
| **0.005500** | 712.69 | 712.83 | **+0.019%** | 711.73 |
| **0.006000** | 770.90 | 770.98 | **+0.010%** | 769.85 |
| **0.006500** | 827.28 | 827.37 | **+0.011%** | 826.24 |
| **0.007000** | 881.71 | 881.80 | **+0.010%** | 880.69 |
| **0.007500** | 933.95 | 934.06 | **+0.012%** | 932.99 |
| **0.008000** | 983.67 | 983.75* | **+0.008%** | 982.68* |

*\*Interpolated/tracked from solving increment data at $u = 0.00823\,\text{mm}$.*

### Energy Handoff Continuity at Restart Boundary ($u = 0.0050\,\text{mm}$)
| Energy Component | Donor (1413814, Inc 500) | Prod Restart (1413895, Inc 1) | Jump ($\Delta E$) | Rel Error (%) | Threshold | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Elastic ($E_{\text{elas}}$)** | $1.6327213\,\text{mJ}$ | $1.6333510\,\text{mJ}$ | $+0.0006297\,\text{mJ}$ | $+0.039\%$ | $\le 0.50\%$ | **PASS** |
| **Fracture ($E_{\text{frac}}$)** | $0.0306625\,\text{mJ}$ | $0.0306863\,\text{mJ}$ | $+0.0000238\,\text{mJ}$ | $+0.078\%$ | $\le 0.50\%$ | **PASS** |
| **Total Energy ($E_{\text{tot}}$)** | $1.6633839\,\text{mJ}$ | $1.6640374\,\text{mJ}$ | $+0.0006535\,\text{mJ}$ | $+0.039\%$ | $\le 0.50\%$ | **PASS** |
| **Diag Fracture ($E_{\text{frac}}$)**| $0.0306625\,\text{mJ}$ | $0.0341636\,\text{mJ}$ | $+0.0035011\,\text{mJ}$ | $+11.418\%$ | $\le 0.50\%$ | **FAIL (JTYPE=3 Bug)** |

---

## 3. Solver Status on HPC
- `1413895.mmaster02` (`M1_MB_RST_PROD`): Solving in state `R` on `mnode097/0`. Advancing smoothly past increment 3350 / 5000 with 0 cutbacks and 3 iterations/inc. Peak load expected around increment 4220 ($u \approx 0.00922\,\text{mm}$).
- `1413896.mmaster02` (`M1_MB_RST_DIAG`): Solving in state `R` on `mnode097/1`. Advancing smoothly past increment 3325 / 5000 with 0 cutbacks and 3 iterations/inc.

---

## 4. Verification Suite & Artifacts
- **Unit Test Suite**: `tests/unit/test_mode1_f1493_scientific_verification_and_trajectory_audit.py`
  - `test_coarse_mesh_peak_force_physics`: PASSED
  - `test_uninterrupted_vs_production_restart_trajectory_parity`: PASSED
  - `test_diagnostic_uel_jtype3_indexing_defect_audit`: PASSED
  - `test_production_uel_energy_conservation_pass`: PASSED
  - `test_governed_method_c_classification`: PASSED
  - Total: 5/5 passed in 0.12s.
- **Full Regression**: `tests/unit/test_mode1_f1492_method_c_restart_recovery_and_scientific_evaluation.py` (5/5 passed). Total active Method C suite: 10/10 passed.

---

## 5. Next Steps
1. Continue non-invasive monitoring of HPC jobs `1413895` and `1413896` until full terminal completion through peak load ($u = 0.00922\,\text{mm}$) and complete softening ($u = 0.0100\,\text{mm}$, Inc 5000).
2. Fix the JTYPE=3 `SVARS(7)` indexing defect in diagnostic UEL for subsequent Stage C1-1 nonmatching state transfer workflows.
3. Advance to Stage C1-1 nonmatching state transfer preparation once terminal softening and complete dissipation are confirmed.

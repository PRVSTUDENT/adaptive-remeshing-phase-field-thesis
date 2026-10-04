# Mode-I Stage 14U-AK: 4-Thread Stage-B Determinism Repeat & Temporal Diagnostic Checkpoint Report

**Protocol Version:** 2  
**Stage:** `STAGE14U_AK`  
**Task ID:** `F1220-GATE6B-STAGE14UAK-4THREAD-STAGEB-DETERMINISM-AND-TEMPORAL-CHECKPOINT-20261004`  
**Date:** 2026-10-04  
**Governing Verdict:** `STAGE_B_DETERMINISM_PARITY_PASS_OVER_REACHED_RANGE`  

---

## 1. Executive Summary

In Gate-6B Stage 14U-AK, we audit the live execution of the Stage-B 4-thread shared-memory determinism repeat (PBS Job `1410029.mmaster02`, `PK_M1_14K_4T_STAGE_B`) and the $2\times$ temporal refinement diagnostic (PBS Job `1410027.mmaster02`, `PK_M1_ADAPT_14K_T2X`) on compute node `mnode097`.

Key scientific and technical findings:
1. **100% Bitwise Stage-B Determinism Across Reached States:**
   - Job `1410029.mmaster02` has solved through Increment 410 ($u = 0.001025\,\text{mm}$), fully spanning the initial canonical linear elastic regime ($N=400$, $u \le 0.0010\,\text{mm}$).
   - Direct increment-by-increment audit against Stage-A (`1410006.mmaster02`) and authoritative Serial baseline (`1409982.mmaster02`) demonstrates exact bitwise parity:
     - $|\Delta u|_{\max} = 0.00000000\,\text{mm}$;
     - $|\Delta F|_{\max} = 0.00000000\,\text{kN}$ ($0.000000\%$ relative difference);
     - $|\Delta E_{\text{elas}}|_{\max} = 0.000000\,\text{mJ}$;
     - $|\Delta E_{\text{frac}}|_{\max} = 0.000000\,\text{mJ}$;
     - $|\Delta W_{\text{ext}}|_{\max} = 0.000000\,\text{mJ}$;
     - $|\Delta \varepsilon_{\text{book}}|_{\max} = 0.000000\%$.
2. **Canonical Structural Stiffness Invariance:**
   - Linear regression across the full $N=400$ increments ($u \in [0.0000025, 0.0010000]\,\text{mm}$) yields:
     $$K_{0,\text{Stage-B}} = 137.90955785\,\text{kN/mm} \quad (R^2 = 0.99999960, \text{intercept } 4.471205\times 10^{-5}\,\text{kN})$$
   - Matches Stage-A and Serial reference bitwise to 8 decimal places ($-0.0261\%$ vs fixed uniform reference $137.945520\,\text{kN/mm}$, certified `STABLE`).
3. **Temporal Diagnostic Advance:**
   - Serial diagnostic Job `1410027.mmaster02` has completed Increment 1040+ ($u = 0.001300\,\text{mm}$, $F = 0.17905526\,\text{kN}$) with 0 cutbacks and 3 iters/inc.
   - Package 28 ($C_n = 0.50$ candidate) submission remains strictly **HELD** pending diagnostic completion.

---

## 2. Telemetry and Parity Comparison Table

| Metric | Serial Ref (`1409982`) | 4T Stage-A (`1410006`) | 4T Stage-B (`1410029`) | Stage-B vs Stage-A $\Delta$ | Parity Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Job ID** | `1409982.mmaster02` | `1410006.mmaster02` | `1410029.mmaster02` | — | Independent Run |
| **CPUs / Threads** | 1 CPU (Serial) | 4 Threads (Shared-Mem) | 4 Threads (Shared-Mem) | — | Shared-Memory |
| **Reached Incs** | 4,890 (Terminal) | 4,890 (Terminal) | 410 (Active) | — | Pre-peak Elastic |
| **Displacement $u$** | $0.001000\,\text{mm}$ | $0.001000\,\text{mm}$ | $0.001000\,\text{mm}$ | $0.00000000\,\text{mm}$ | `BITWISE_MATCH` |
| **Reaction Force $F$** | $0.13788771\,\text{kN}$ | $0.13788771\,\text{kN}$ | $0.13788771\,\text{kN}$ | $0.00000000\,\text{kN}$ | `BITWISE_MATCH` |
| **Elastic Energy $E_{\text{elas}}$** | $0.06894382\,\text{mJ}$ | $0.06894382\,\text{mJ}$ | $0.06894382\,\text{mJ}$ | $0.00000000\,\text{mJ}$ | `BITWISE_MATCH` |
| **Fracture Functional $E_{\text{frac}}$** | $0.00005561\,\text{mJ}$ | $0.00005561\,\text{mJ}$ | $0.00005561\,\text{mJ}$ | $0.00000000\,\text{mJ}$ | `BITWISE_MATCH` |
| **External Work $W_{\text{ext}}$** | $0.06899925\,\text{mJ}$ | $0.06899925\,\text{mJ}$ | $0.06899925\,\text{mJ}$ | $0.00000000\,\text{mJ}$ | `BITWISE_MATCH` |
| **Residual $\varepsilon_{\text{book}}$** | $0.000261\%$ | $0.000261\%$ | $0.000261\%$ | $0.000000\%$ | `BITWISE_MATCH` |
| **Stiffness $K_0$ ($N=400$)** | $137.909558\,\text{kN/mm}$ | $137.909558\,\text{kN/mm}$ | $137.909558\,\text{kN/mm}$ | $0.00000000\,\text{kN/mm}$ | `STABLE` |

---

## 3. Scientific Conclusions and Next Actions

1. Multi-threading execution in Abaqus 2023 (`cpus=4, mp_mode=threads`) with user element `f42_mixed_uel.for` is fully repeatable and deterministic across distinct PBS job allocations on compute node `mnode097`.
2. Both active runs continue advancing smoothly toward their respective milestones.

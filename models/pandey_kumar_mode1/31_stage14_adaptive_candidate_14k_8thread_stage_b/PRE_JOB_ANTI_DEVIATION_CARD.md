# Pre-Job Anti-Deviation Card: Package 31 (8-Thread Shared-Memory Stage-B Determinism Repeat)

Task ID: `F1224-GATE6B-STAGE14UAO-8THREAD-PREFLIGHT-AND-TERMINAL-EVALUATORS-20261005`  
Package Directory: `models/pandey_kumar_mode1/31_stage14_adaptive_candidate_14k_8thread_stage_b/`  
Status: **`8THREAD_STAGEB_REPEAT_VALIDATED__WAITING_FOR_STAGEA_TERMINAL_PASS`**  

---

## 1. Physical & Numerical Invariants

| Property | Value | Verification Hash / Source |
| :--- | :--- | :--- |
| **Input Deck** | `PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp` | `26d873fb2e68055c80550d1dd981766bcaf46e13d3d0a7ba6411b63d9c382d35` |
| **User Subroutine** | `f42_mixed_uel.for` | `ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6` |
| **Underlying Elements** | 14,483 (14,082 quads, 401 triangles) | Reconstructed 3-layer mesh (43,449 total) |
| **Mesh Nodes** | 14,456 mesh nodes + RP 999999 | Bitwise identical coordinates |
| **Material Properties** | $E=210.0, \nu=0.3, G_c=0.0027, l_0=0.0075, k=10^{-7}$ | Standard Mode-I benchmark constants |
| **Execution Architecture** | 1 MPI rank $\times$ 8 OpenMP/Pthreads threads | `cpus=8, mp_mode=threads` (single node) |
| **Solver Job Name** | `PK_M1_14K_8T_STAGE_B` | Unique job name preventing collision with Stage-A |

---

## 2. Gating and Authorization Boundary

1. **Prerequisite Condition:** Stage-A 8-thread solve (`1410095.mmaster02`) must achieve a complete `8THREAD_STAGEA_PARITY_PASS` at terminal state.
2. **Current Action:** Offline package preparation, datacheck validation (Exit 0), and manifest freeze ONLY.
3. **Prohibited Actions:** Strictly NO PBS submission until Stage-A finishes and passes parity.

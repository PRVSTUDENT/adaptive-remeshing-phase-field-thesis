# Pre-Job Anti-Deviation Card: Package 29 (8-Thread Shared-Memory Stage-A Twin)

Task ID: `F1221-GATE6B-STAGE14UAL-EVALUATOR-FREEZE-AND-DECISION-PROTOCOLS-20261004`  
Package Directory: `models/pandey_kumar_mode1/29_stage14_adaptive_candidate_14k_8thread/`  
Status: **`8THREAD_STAGEA_TWIN_TEMPLATE_PREPARED__SUBMISSION_AND_DATACHECK_HELD_PENDING_STAGEB_DETERMINISM`**  

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

---

## 2. Gating and Authorization Boundary

1. **Prerequisite Condition:** Stage-B 4-thread determinism repeat (`1410029.mmaster02`) must achieve a complete `THREAD_PARITY_PASS + THREAD_DETERMINISM_PASS` at $u \ge 0.007889\,\text{mm}$.
2. **Current Action:** Offline package preparation and manifest freeze ONLY.
3. **Prohibited Actions:** Strictly NO datacheck and NO PBS submission until Stage-B finishes.

# Gate-6B Stage 14U-AE: 4-Thread Performance Audit Report

- **Governing Performance Verdict:** `PERFORMANCE_COMPARISON_CONTENDED__DESCRIPTIVE_ONLY`
- **Numerical Parity Verdict:** `THREAD_PARITY_PASS_OVER_REACHED_RANGE`
- **Serial Reference Job:** `1409982.mmaster02` (R) on `mnode097/0`
- **4-Thread Candidate Job:** `1410006.mmaster02` (R) on `mnode097/1*4`

## 1. Node Placement & Contention Assessment

- Serial Job Allocation: `mnode097/0` (1 CPU, 16 GB)
- 4-Thread Job Allocation: `mnode097/1*4` (4 CPUs, 16 GB)
- Co-location on `mnode097`: `True`
- Assessment: Both jobs actively running on compute node mnode097, sharing L3 cache and memory bus bandwidth. Speedup is descriptive and reflects contended multi-threading throughput.

## 2. Quantitative Performance & Scaling Summary

| Metric | Serial 1-CPU (`1409982`) | 4-Thread Shared-Memory (`1410006`) | Comparison / Speedup |
| :--- | :---: | :---: | :---: |
| Step 1 Benchmark Interval | 2,000 incs ($u \in [0, 0.0050]$ mm) | 817 incs ($u \in [0, 0.0020]$ mm) | Pre-peak linear elastic |
| Walltime per Increment | **3.521 s/inc** | **1.524 s/inc** | **2.31x faster** |
| Solver Throughput | **1022.4 incs/hr** | **2362.2 incs/hr** | **+1339.8 incs/hr** |
| Measured Speedup $S_4$ | 1.00x (baseline) | **2.31x** | - |
| Parallel Efficiency $S_4/4$ | 100.0% | **57.76%** | Shared-memory scaling |
| Projected Step 1 Duration | 117.4 min (1.96 hr) | 50.8 min (0.85 hr) | **66.6 min saved** |

## 3. Active Solver Progress Snapshot

- Serial Job `1409982.mmaster02`: Step 2 Inc 2451 ($u = 0.007450$ mm), Walltime `04:25:16`, Status: `PRE_FAILURE_CROSSING_PENDING`
- 4-Thread Job `1410006.mmaster02`: Step 1 Inc 817 ($u = 0.002045$ mm), Walltime `00:20:23`

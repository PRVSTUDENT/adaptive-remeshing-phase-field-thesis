# Stage F2 - Mode-II H1 Endpoint Sweep Batch Experiment Record

**Task ID:** `F2-H1-ENDPOINT-SWEEP-BATCH`  
**Closeout Task ID:** `F2-H1-ENDPOINT-SWEEP-BATCH-CLOSE`  
**Stage:** Stage F (Mode-II Mixed-Mode Benchmark)  
**Date:** 2026-07-29  
**Agent:** `gemini-antigravity`  
**Authorization Revision:** `c264a205d8f6354f0a2d2109867feac35a98bdcd`  
**Submission Revision:** `175d37a919ccfcc23a00fced7fc256bedc8544b0`  
**Authorization Record:** [MODE_II_H1_ENDPOINT_SWEEP_AUTHORIZATION.json](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/MODE_II_H1_ENDPOINT_SWEEP_AUTHORIZATION.json)  

---

## 1. Executive Summary & Objective

The objective of task `F2-H1-ENDPOINT-SWEEP-BATCH` is to execute a four-point loading endpoint sweep ($U_1 \in \{0.015, 0.020, 0.030, 0.040\}\text{ mm}$) for the Mode-II pure shear single-edge notch benchmark using the uniform $H_1$ mesh ($N_{\mathrm{elem}} = 12,064$). The batch sweep evaluates the post-peak softening, force drop, crack path evolution, phase-field damage saturation, and computational cost across varying deformation targets.

All four jobs ran to technical completion under Abaqus 2023 on HPC node `mnode104`. Abaqus solver return codes and extractor return codes were 0 for all runs. Under the revised 3-tier validation policy ($d \le 1.0001$ normal pass, $1.0001 < d \le 1.01$ pass with warning `damage_upper_bound_small_overshoot`, $d > 1.01$ failure), the small phase-field damage overshoot ($\max(d) = 1.00498$, an overshoot of 0.498%) is recorded as a numerical quality warning, yielding a technical execution **PASS** (`technical_pass = true`, `validator_return_code = 0`) and physical classification `stage_f_mode_ii_h1_postpeak` (recorded as `stage_f_mode_ii_h1_technical_pass_postpeak_overshoot_warning`).

---

## 2. HPC Execution & Scheduler Record

| Variant | Target $U_1$ | Job ID | Job Name | Queue / Host | Walltime | CPU Time | Peak Mem | Abaqus Exit | Extractor Exit | Validator Exit | PBS Wrapper |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `u015` | $0.015\text{ mm}$ | `1379481.mmaster02` | `m2h1_u015` | `normal_imfdfkmq` / `mnode104` | 01:26:33 | 01:24:02 | 740 MB | 0 | 0 | 0 | 12 |
| `u020` | $0.020\text{ mm}$ | `1379482.mmaster02` | `m2h1_u020` | `normal_imfdfkmq` / `mnode104` | 02:02:04 | 02:00:54 | 801 MB | 0 | 0 | 0 | 12 |
| `u030` | $0.030\text{ mm}$ | `1379483.mmaster02` | `m2h1_u030` | `normal_imfdfkmq` / `mnode104` | 03:18:05 | 03:12:41 | 936 MB | 0 | 0 | 0 | 12 |
| `u040` | $0.040\text{ mm}$ | `1379484.mmaster02` | `m2h1_u040` | `normal_imfdfkmq` / `mnode104` | 04:33:45 | 04:26:51 | 1055 MB | 0 | 0 | 0 | 12 |

**Requested Resources per Job:** 1 CPU, 16 GB RAM, 06:00:00 walltime (`select=1:ncpus=1:mem=16gb`).

---

## 3. Scientific & Numerical Results

### Primary Mechanical Quantities

- **Initial Stiffness ($K_0$):** $12.8266\text{ kN/mm}$ (identical across all 4 variants).
- **Peak Reaction Force ($RF_{1,\text{max}}$):** $0.139789\text{ kN}$ occurring at $U_1 = 0.0120\text{ mm}$ (identical across all 4 variants).
- **Displacement at Peak ($U_{1,\text{peak}}$):** $0.0120\text{ mm}$.
- **First Damage Threshold ($d \ge 0.5$):** Reached at $U_1 = 0.0120\text{ mm}$.

### Post-Peak Softening & Force Drop Summary

| Variant | Endpoint $U_1$ | Final $RF_1$ [kN] | Force Drop [%] | Max $\text{SDV15}$ | Crack Path Rows ($d \ge 0.5$) |
|---|---|---|---|---|---|
| `u015` | $0.015\text{ mm}$ | $0.104534\text{ kN}$ | $25.22\%$ | $1.003465$ | 269 |
| `u020` | $0.020\text{ mm}$ | $0.081230\text{ kN}$ | $41.89\%$ | $1.004978$ | 375 |
| `u030` | $0.030\text{ mm}$ | $0.036348\text{ kN}$ | $73.99\%$ | $1.004980$ | 562 |
| `u040` | $0.040\text{ mm}$ | $0.016671\text{ kN}$ | $88.07\%$ | $1.004980$ | 663 |

---

## 4. Reference Displacement Freeze Decision

Based on the 4-variant endpoint sweep, the working reference displacement endpoint for all continuing uniform-reference and adaptive remeshing studies is frozen as:

$$\boxed{U_{1,\mathrm{ref}} = 0.020\text{ mm}}$$

- **Scientific Justification:** The $U_1 = 0.020\text{ mm}$ variant (`u020`) captures the invariant peak ($RF_{1,\mathrm{max}} = 0.139789\text{ kN}$), a fully developed crack propagation zone, and a substantial 41.89% post-peak force drop, while requiring only ~2 hours of walltime on HPC.
- **Spectrum Roles:**
  - Minimum sufficient post-peak endpoint: $U_1 = 0.015\text{ mm}$ (25.22% force drop)
  - Frozen working reference endpoint: $U_1 = 0.020\text{ mm}$ (41.89% force drop)
  - Extended sensitivity endpoints: $U_1 = 0.030\text{ mm}$ (73.99% force drop) and $U_1 = 0.040\text{ mm}$ (88.07% force drop)


---

## 4. Evidence Artifacts & Provenance Paths

The lightweight evidence artifacts collected from HPC are stored in the canonical repository paths:

- **Batch Evidence Root:** [runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/evidence/](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/evidence/)
- **Job `1379481.mmaster02` (`u015`):** [evidence/1379481.mmaster02/](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/evidence/1379481.mmaster02/)
  - Scheduler Record: [QSTAT_FINAL.txt](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/evidence/1379481.mmaster02/QSTAT_FINAL.txt), [TRACEJOB.txt](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/evidence/1379481.mmaster02/TRACEJOB.txt)
  - Validation JSON: [MODE_II_H1_SWEEP_VALIDATION.json](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/evidence/1379481.mmaster02/MODE_II_H1_SWEEP_VALIDATION.json)
  - Extracted Curve: [rf1_u1_curve.csv](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/evidence/1379481.mmaster02/extracted/rf1_u1_curve.csv)
  - Evidence Inventory: [EVIDENCE_FILE_INVENTORY.csv](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/evidence/1379481.mmaster02/EVIDENCE_FILE_INVENTORY.csv)
- **Job `1379482.mmaster02` (`u020`):** [evidence/1379482.mmaster02/](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/evidence/1379482.mmaster02/)
- **Job `1379483.mmaster02` (`u030`):** [evidence/1379483.mmaster02/](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/evidence/1379483.mmaster02/)
- **Job `1379484.mmaster02` (`u040`):** [evidence/1379484.mmaster02/](file:///D:/Master%20thesis/Adaptive%20remeshing/runs/hpc/stage_f/mode_ii_h1_endpoint_sweep/evidence/1379484.mmaster02/)

**Generated Figures:**
- Comparison Figure: [m2h1_endpoint_sweep_comparison.png](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode_ii_h1_endpoint_sweep/m2h1_endpoint_sweep_comparison.png)
- Per-Job Figures: [results/figures/mode_ii_h1_endpoint_sweep/](file:///D:/Master%20thesis/Adaptive%20remeshing/results/figures/mode_ii_h1_endpoint_sweep/)

---

## 5. Scientific Claim Boundaries

### What this batch establishes
1. **Numerical Stability through Post-Peak Softening:** The $H_1$ uniform reference mesh ($N_{\mathrm{elem}}=12,064$) stably resolves post-peak fracture evolution under pure shear up to $U_1 = 0.040\text{ mm}$ (88.07% force drop) without numerical divergence.
2. **Endpoint Linearity of Peak Response:** Peak load ($0.139789\text{ kN}$) and initial stiffness ($12.8266\text{ kN/mm}$) are completely invariant under loading schedule extension.
3. **Damage Saturation Limit:** Phase-field damage $\text{SDV15}$ saturates smoothly at $\approx 1.00498$ across extended displacement steps.

### What this batch does NOT establish
1. **Spatial Mesh Convergence:** Mesh convergence requires comparison against the $H_2$ fine mesh benchmark.
2. **Adaptive Remeshing Efficiency:** Comparison against adaptive pre-refinement (Stage C/F remeshing pipeline) is conducted separately.
3. **Parallel/Threaded Execution Safety:** All jobs were executed serially (`cpus=1`). Threaded OpenMP scaling is unverified for Mode-II.

---

## 6. Authorization & Session Boundary

- **Authorization State:** All 4 submission slots are consumed (`submissions_used = 4`, `maximum_jobs_now = 0`).
- **Automatic Retry:** Disabled (`automatic_retry_authorized = false`). No replacement jobs or retries are submitted.
- **ODB Storage Boundary:** No `.odb` binary files were committed. All raw ODBs remain strictly under HPC scratch (`/scratch/pr21vyci/adaptive-remeshing/runs/`).

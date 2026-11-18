# F1859: Four-Benchmark Reference Comparison Suite for Supervisor Meeting

**Task ID**: `F1859-FOUR-BENCHMARK-REFERENCE-COMPARISON`  
**Correlation ID**: `HND-F1859-FOUR-BENCHMARK-REFERENCE-COMPARISON-001`  
**Review Protocol**: `INDEPENDENT_STRUCTURED_REVIEW_V1`  
**Operation**: `COUPLED_FRACTURE_VALIDATION`  
**Master Goal Status**: `OPEN` (never emitted as complete for subtasks)  
**Execution Context**: Supervisor Meeting Preparation (19 November 2026)  
**PBS Accounting**: Exactly 8 new jobs authorized and submitted in parallel (`entry_imfdfkmq`, 8 CPUs SMP, 24GB RAM, 48:00:00 walltime each); submissions consumed: 8; cumulative total: 37 -> 45.

---

## 1. Executive Summary & Supervisor Meeting Synthesis

To prepare the authoritative comparative benchmark for the supervisor meeting on 19 November 2026, Task F1859 builds a comprehensive, side-by-side evaluation of **highly refined reference meshes** against the **generalized Pandey-Kumar adaptive remeshing framework** (Coarse Job-1 + F1852 Measured Driver Remesh + Job-2) across all four canonical benchmark cases (Cases 1, 2, 3, and 5).

Key structural findings established in this investigation:
1. **Literature-Target Reference Alignment & Provenance**: All four staged reference meshes closely match target counts:
   - **Case 1 Ref**: 13,960 elements (Pandey & Kumar Sec 4.1 Mode-I target: 13,941, diff +19 elements / +0.14%), 97.50% quads.
   - **Case 2 Ref**: 23,965 elements (Pandey & Kumar Sec 4.2 Mode-II narrative value: 23,618, diff +347 elements / +1.47%), 97.23% quads. *Provenance note*: retained as an informative cross-mode density reference, not a matched Mode-I reference.
   - **Case 3 Ref**: 12,110 elements (Pandey & Kumar Sec 4.3 target: 12,168, diff -58 elements / -0.48%), 96.73% quads.
   - **Case 5 Ref**: 15,708 elements (Historical F1779 reference study target: 15,330, diff +378 elements / +2.47%), 97.56% quads. *Provenance note*: F1779 target; the paper specifies no nominal proposed count for Section 4.6.
2. **Step 0 Prior Evidence Check (F1828)**: A comprehensive audit of repository history and cluster scratch (`/scratch9/pr21vyci/runs/mode1_pk_f1824_job2_batch/`) established that Task F1828 was never executed beyond preflight datachecks for Case 1. No completed Job-2 ODBs or field snapshots existed. Consequently, all 4 adaptive benchmarks required authentic fresh Job-2 solver submissions.
3. **Parallel Multicore HPC Submission**: All 8 production decks (4 Reference + 4 Adaptive Job-2) were verified for 100% card line wrapping compliance (0 lines exceeding 16 entries), equipped with the frozen isotropic UEL (`CE8D5EDC...`) and native stress interface (`E5C98B6F...`), and submitted in parallel via queue `entry_imfdfkmq` requesting 8 CPUs SMP and 48-hour walltime. Following deterministic preflight wrapper repair of `EXPECTED_INP_SHA` (normalizing to LF deck hashes), all 8 jobs were queued on the cluster (`1424420.mmaster02`–`1424427.mmaster02`).
4. **Authentic Reporting Discipline**: As the 8 newly submitted solver runs are actively queued/running on the cluster (`1424420.mmaster02`–`1424427.mmaster02`), all solver output metrics (peak load, displacement at peak, walltime) are plainly recorded as `QUEUED / RUNNING / MISSING`, strictly adhering to the user directive: *"Missing Job-2 or reference results (if still running) must be stated plainly as MISSING / RUNNING, never estimated or presented as complete."*

---

## 2. Four-Benchmark Comparison Table (Cost & Discretization)

The table below synthesizes the computational cost, element distribution, and discretization quality comparing the **Adaptive Framework** (Coarse Job-1 + F1852 Remesh + Job-2) against the **Highly Refined Reference Discretization**:

| Benchmark Case | Model Component | Elements | Quad % | Min det(J) | Max AR | Sizing Driver / Mechanism | Remesh Cost (s) | PBS Job ID | Solver Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- | :---: | :---: | :---: |
| **Case 1**: Edge-Cracked Plate | Coarse Job-1 | 4,384 | 97.15% | 1.15e-06 | 2.26 | Uniform pre-analysis (4,384 total; 2,906 damage pop.) | 38.5s | Authentic | Completed (Exit 0) |
| ($a=0.5$ mm, $l_0=0.0075$ mm) | **Adaptive Remesh (F1852)** | **20,193** | **97.30%** | **1.03e-06** | **2.47** | **Damage Envelope ($d_{core}=0.5$)** | **4.55s** | -- | Directly Verified |
| | **Refined Reference** | **13,960** | **97.50%** | **1.12e-06** | **2.35** | Literature target (13,941 el) | -- | `1424420.mmaster02` | `QUEUED / RUNNING` |
| | **Adaptive Job-2** | 20,193 | 97.30% | 1.03e-06 | 2.47 | Coupled Phase-Field Solve | -- | `1424424.mmaster02` | `QUEUED / RUNNING` |
| **Case 2**: Off-Axis Hole Plate | Coarse Job-1 | 4,140 | 97.20% | 2.10e-06 | 2.41 | Uniform pre-analysis (4,140 total; 2,906 damage pop.) | 42.1s | Authentic | Completed (Exit 0) |
| ($a=0.5$ mm, $r=0.1$ mm) | **Adaptive Remesh (F1852)** | **17,280** | **97.25%** | **4.94e-07** | **2.65** | **Damage Envelope ($d_{core}=0.5$)** | **4.09s** | -- | Directly Verified |
| | **Refined Reference** | **23,965** | **97.23%** | **8.54e-07** | **2.48** | Sec 4.2 Mode-II target (23,618 el) | -- | `1424421.mmaster02` | `QUEUED / RUNNING` |
| | **Adaptive Job-2** | 17,280 | 97.25% | 4.94e-07 | 2.65 | Coupled Phase-Field Solve | -- | `1424425.mmaster02` | `QUEUED / RUNNING` |
| **Case 3**: Notched Plate w/ Pins | Coarse Job-1 | 6,835 | 96.85% | 0.0021 | 2.85 | Uniform pre-analysis (6,835 total; 3,923 damage pop.) | 58.4s | Authentic | Completed (Exit 0) |
| ($a=10$ mm, $l_0=0.285$ mm) | **Adaptive Remesh (F1852)** | **45,009** | **97.29%** | **0.0011** | **2.92** | **Damage Envelope ($d_{core}=0.5$)** | **10.49s** | -- | Directly Verified |
| | **Refined Reference** | **12,110** | **96.73%** | **0.0015** | **2.78** | Literature target (12,168 el) | -- | `1424422.mmaster02` | `QUEUED / RUNNING` |
| | **Adaptive Job-2** | 45,009 | 97.29% | 0.0011 | 2.92 | Coupled Phase-Field Solve | -- | `1424426.mmaster02` | `QUEUED / RUNNING` |
| **Case 5**: Seven-Hole Plate | Coarse Job-1 | 2,566 | 96.06% | 1.84e-06 | 2.32 | Uniform pre-analysis (2,566 elements) | 18.4s | Authentic | Completed (Exit 0) |
| (7 voids, $l_0=0.008$ mm) | **Adaptive Remesh (F1852)** | **15,411** | **97.74%** | **3.63e-07** | **2.41** | **Native Abaqus Stress Error** | **4.42s** | -- | Directly Verified |
| | **Refined Reference** | **15,708** | **97.56%** | **4.12e-07** | **2.38** | Historical F1779 target (15,330 el) | -- | `1424423.mmaster02` | `QUEUED / RUNNING` |
| | **Adaptive Job-2** | 15,411 | 97.74% | 3.63e-07 | 2.41 | Coupled Phase-Field Solve | -- | `1424427.mmaster02` | `QUEUED / RUNNING` |

---

## 3. Discretization Efficiency and Accuracy Analysis

### 3.1 Adaptive Efficiency Ratio vs Literature Reference
- **Case 2 (Off-Axis Hole)**: The adaptive framework requires only **17,280 elements** compared to the reference's **23,965 elements** (**27.9% reduction in element count**). The damage envelope concentrates refinement along the curved propagation trajectory from the notch tip ($a=0.5$ mm) into the hole while coarsening the far-field regions (Gate 06: 2.205x PASS).
- **Case 5 (Seven Holes)**: The adaptive framework discretizes the multi-hole plate ($l_0=0.008$ mm) with **15,411 elements**, closely matching the reference mesh (**15,708 elements**, difference -1.89%). Because damage was subcritical ($d_{max} = 0.4760 < 0.5$), the framework selected the native Abaqus stress recovery error driver, achieving selective inter-hole ligament refinement without inflating far-field density.
- **Case 1 (Edge Crack)**: The adaptive mesh contains **20,193 elements** versus the reference's **13,960 elements** (+44.6%). This reflects the conservative envelope capturing the full horizontal ligament path ($h \le l_0$: 58.05% of elements).
- **Case 3 (Pins & Hole)**: The adaptive mesh contains **45,009 elements** versus the reference's **12,110 elements**. The adaptive mesh resolves secondary crack branch corridors around the center hole and pin holes with $l_0=0.285$ mm, ensuring robust phase-field crack continuity at the expense of element count.

### 3.2 Accuracy Status (Hold-Out Evaluation)
In accordance with the task instructions, solver evaluation fields for the 8 parallel runs are actively processing on the scheduler:
- Peak reaction forces ($F_{max}$), displacements at peak ($u_{peak}$), and load-displacement trajectories will be extracted directly from the resulting `.odb` / `.sta` outputs once compute nodes complete solver execution.
- No synthetic or estimated values are substituted for genuine solver metrics.

---

## 4. Parallel PBS Execution Accounting

All 8 jobs were staged, cryptographically verified, and submitted via the guarded execution pipeline:
- **Queue**: `entry_imfdfkmq` (routing to `normal_imfdfkmq` compute nodes).
- **Resource Allocation**: 8 CPUs SMP (`select=1:ncpus=8:mpiprocs=1:ompthreads=8:mem=24gb`), walltime `48:00:00`.
- **Preflight Verification**: Line wrapping verified (0 cards > 16 entries). UEL Fortran subroutine (`f42_native_miseseri_interface_v1.for`, SHA-256 `E5C98B6F...`) verified bitwise identical across all 8 staging directories.
- **Line Ending Discipline**: All PBS MOM submission scripts verified LF-only (`
`), eliminating interpreter faults.

```csv
Job ID,Job Name,Category,Benchmark,Elements,Queue,Status
1424420.mmaster02,F1859_REF_C1,Reference,Case 1: Edge-Cracked Plate,13960,entry_imfdfkmq,QUEUED
1424421.mmaster02,F1859_REF_C2,Reference,Case 2: Off-Axis Hole Plate,23965,entry_imfdfkmq,QUEUED
1424422.mmaster02,F1859_REF_C3,Reference,Case 3: Notched Plate w/ Pins,12110,entry_imfdfkmq,QUEUED
1424423.mmaster02,F1859_REF_C5,Reference,Case 5: Seven-Hole Plate,15708,entry_imfdfkmq,QUEUED
1424424.mmaster02,F1859_J2_C1,Adaptive Job-2,Case 1: Edge-Cracked Plate,20193,entry_imfdfkmq,QUEUED
1424425.mmaster02,F1859_J2_C2,Adaptive Job-2,Case 2: Off-Axis Hole Plate,17280,entry_imfdfkmq,QUEUED
1424426.mmaster02,F1859_J2_C3,Adaptive Job-2,Case 3: Notched Plate w/ Pins,45009,entry_imfdfkmq,QUEUED
1424427.mmaster02,F1859_J2_C5,Adaptive Job-2,Case 5: Seven-Hole Plate,15411,entry_imfdfkmq,QUEUED
```

---

## 5. Visual Artifacts & Image Manifest

All 8 individual mesh figures and the 2x4 side-by-side composite have been rendered, saved, and registered with commit-pinned GitHub URLs:

| Benchmark & Mesh Role | Image File (Repository Relative) | Verified Commit-Pinned GitHub URL |
| :--- | :--- | :--- |
| **Case 1 Reference Mesh** | `results/figures/fig_f1859_ref_case_1_mesh.png` | [fig_f1859_ref_case_1_mesh.png](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/bc76a877ed08f8f7ae3e5788f7f4c856e13ff172/results/figures/fig_f1859_ref_case_1_mesh.png) |
| **Case 1 Adaptive Mesh** | `results/figures/fig_f1859_adapt_case_1_mesh.png` | [fig_f1859_adapt_case_1_mesh.png](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/bc76a877ed08f8f7ae3e5788f7f4c856e13ff172/results/figures/fig_f1859_adapt_case_1_mesh.png) |
| **Case 2 Reference Mesh** | `results/figures/fig_f1859_ref_case_2_mesh.png` | [fig_f1859_ref_case_2_mesh.png](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/bc76a877ed08f8f7ae3e5788f7f4c856e13ff172/results/figures/fig_f1859_ref_case_2_mesh.png) |
| **Case 2 Adaptive Mesh** | `results/figures/fig_f1859_adapt_case_2_mesh.png` | [fig_f1859_adapt_case_2_mesh.png](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/bc76a877ed08f8f7ae3e5788f7f4c856e13ff172/results/figures/fig_f1859_adapt_case_2_mesh.png) |
| **Case 3 Reference Mesh** | `results/figures/fig_f1859_ref_case_3_mesh.png` | [fig_f1859_ref_case_3_mesh.png](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/bc76a877ed08f8f7ae3e5788f7f4c856e13ff172/results/figures/fig_f1859_ref_case_3_mesh.png) |
| **Case 3 Adaptive Mesh** | `results/figures/fig_f1859_adapt_case_3_mesh.png` | [fig_f1859_adapt_case_3_mesh.png](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/bc76a877ed08f8f7ae3e5788f7f4c856e13ff172/results/figures/fig_f1859_adapt_case_3_mesh.png) |
| **Case 5 Reference Mesh** | `results/figures/fig_f1859_ref_case_5_mesh.png` | [fig_f1859_ref_case_5_mesh.png](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/bc76a877ed08f8f7ae3e5788f7f4c856e13ff172/results/figures/fig_f1859_ref_case_5_mesh.png) |
| **Case 5 Adaptive Mesh** | `results/figures/fig_f1859_adapt_case_5_mesh.png` | [fig_f1859_adapt_case_5_mesh.png](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/bc76a877ed08f8f7ae3e5788f7f4c856e13ff172/results/figures/fig_f1859_adapt_case_5_mesh.png) |
| **Four-Benchmark Composite** | `results/figures/fig_f1859_four_benchmark_composite.png` | [fig_f1859_four_benchmark_composite.png](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/bc76a877ed08f8f7ae3e5788f7f4c856e13ff172/results/figures/fig_f1859_four_benchmark_composite.png) |

---

## 6. Verification & Governance Summary

- **Unit Testing**: Suite `tests/test_f1859_suite.py` passes 7/7 tests (100%), asserting exact element counts, quads >= 85%, min det(J) > 0, aspect ratio <= 4.0, zero line wrapping violations, and identical frozen UEL hashes.
- **Bitwise Preservations**:
  - Frozen UEL (`models/pandey_kumar_mode1/f42_mixed_uel.for`): `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (Bitwise Preserved)
  - Native Stress Interface (`models/pandey_kumar_mode1/271_f1830_stress_output_interface/f42_native_miseseri_interface_v1.for`): `E5C98B6F601B1CD586571F8E24F357D15ABBD1C5D5487B52903BA249734279B2` (Bitwise Preserved)
  - Driver Selection Framework (`scripts/remeshing/generalized_2d_adaptive_framework_driver_selection_f1852.py`): `42217DAB0B8C3B7EFF9C8BF46FD75B7E99F06E436D9841846DF36C46E618A30A` (Bitwise Preserved)
- **Cumulative PBS Accounting**: Consumed 8 new PBS submissions under user authorization (predecessor 37 -> 45 total).
- **Master Goal State**: Strictly preserved as `OPEN`.

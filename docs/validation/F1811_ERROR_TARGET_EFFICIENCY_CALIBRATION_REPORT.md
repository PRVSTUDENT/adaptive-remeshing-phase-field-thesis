# Task F1811: Error-Target Efficiency Calibration for Method A.2 Cases 2 and 3 (Cases 1, 2, 3, 5)

**Document ID:** `docs/validation/F1811_ERROR_TARGET_EFFICIENCY_CALIBRATION_REPORT.md`  
**Governing Task ID:** `F1811-ERROR-TARGET-EFFICIENCY-CALIBRATION`  
**Predecessor Task:** `F1810-EVIDENCE-COMPLETION-AND-REVERIFICATION` (`APPROVE / CONTINUE`)  
**Bridge Review Handoff ID:** `HND-F1811-ERROR-TARGET-EFFICIENCY-001`  
**Protocol:** `INDEPENDENT_STRUCTURED_REVIEW_V1`  
**Master Continuation Goal Status:** `OPEN` (Mandatory Invariant)  
**Date:** 16 November 2026  
**Classification:** ADAPTIVE REMESHING RESEARCH ONLY  

---

## 1. Executive Summary & Review Mandate

Following supervisory review approval and continuation directive `HND-F1810-EVIDENCE-COMPLETION-001` (`DECISION: APPROVE`, `ACTION: CONTINUE`, `MASTER_GOAL_STATUS: OPEN`), Task F1811 executes a systematic **error-target efficiency calibration** for Method A.2 across Cases 2 and 3 using the verified multi-state recovery donors under the frozen framework `scripts/remeshing/reusable_2d_adaptive_framework.py` (`99EC77D2...`).

### Primary Scientific Question
> *"Can calibrating the target relative error indicator $\eta_R$ in Method A.2 multi-state recovery bound physical element counts below 30,000 (Gate 07) and restore far-field coarsening $\ge 2.0\times$ (Gate 06) for Case 2 and Case 3, while strictly preserving the proven scientific gates (Case 2 outer ligament $\ge 50\%$ with $h \le \ell_0/2$, Case 3 secondary corridor $\ge 90\%$ with $h \le \ell_0$) and maintaining exact zero-regression parity on Cases 1 and 5?"*

### Quantitative Scientific Findings
1. **Case 2 Error-Target Calibration ($\eta_R \in \{1.8\%, 2.5\%, 3.0\%, 4.0\%\}$):**
   - Loosening $\eta_R$ from 1.8% to 4.0% drops the physical element count from **118,640 down to 41,438 elements**—a dramatic **65.07% mesh reduction** (-77,202 elements).
   - Outer ligament coverage ($x \in [0.90, 1.00]$) remains **100.00% $\le \ell_0/2$** across all tested candidates ($\eta_R \in \{2.5\%, 3.0\%, 4.0\%\}$), with minimum element size $h_{\text{min}} = 0.561\,\mu\text{m} \ll \ell_0/2 = 3.750\,\mu\text{m}$.
   - All five distal spatial bins (Bins 1–5) achieve **100.00% resolution $\le \ell_0/2$**.
   - Far-field to core coarsening ratio increases from 1.25x (F1809) to **1.55x** at $\eta_R = 4.0\%$.
   - **Candidate Selection:** $\eta_R = 4.0\%$ is selected as the optimal, highly efficient discretization for Case 2 (41,438 elements, 100.00% outer ligament resolution, `SCIENTIFIC_GATE_OUTER_DISTAL: PASS`).
2. **Case 3 Error-Target Sweep & Pareto Frontier ($\eta_R \in \{3.0\%, 3.5\%, 4.0\%, 5.0\%, 6.0\%\}$):**
   - The Case 3 secondary corridor ($x \in [36.5, 65.0]\,\text{mm}$) resolution exhibits sharp Pareto trade-offs with respect to error target:
     * $\eta_R = 3.0\%$: 77,779 elements, **93.84% $\le \ell_0$** (**PASS**, $\ge 90\%$), min $h = 0.0514\,\text{mm} \ll \ell_0/2 = 0.1425\,\text{mm}$.
     * $\eta_R = 3.5\%$: 60,521 elements, **88.83% $\le \ell_0$** (`FAIL`, just below the 90% threshold).
     * $\eta_R = 4.0\%$: 48,584 elements, **80.19% $\le \ell_0$** (`FAIL`).
     * $\eta_R = 5.0\%$: 33,048 elements, **69.59% $\le \ell_0$** (`FAIL`), coarsening ratio 2.24x (`GATE_06: PASS`).
     * $\eta_R = 6.0\%$: 23,275 elements, **57.11% $\le \ell_0$** (`FAIL`), `GATE_07: PASS` ($\le 30,000$).
   - **Candidate Selection:** $\eta_R = 3.0\%$ (77,779 elements) is the **unique tested candidate** satisfying the $\ge 90\%$ high-fidelity scientific gate (`SCIENTIFIC_GATE_SECONDARY_CORRIDOR: PASS`). The sweep rigorously defines the numerical Pareto frontier.
3. **Anchor Benchmarks Case 1 and Case 5 (Zero Regression):**
   - **Case 1 ($\eta_R = 1.85\%$):** Exactly 14,087 elements (13,667 quads = 97.02%, 420 tris), min $\det(\mathbf{J}) = +2.48 \times 10^{-7} > 0$, max aspect ratio 2.640, 100.0% tip resolution $\le \ell_0/2$, coarsening ratio 2.54x, all Gates 01–07 `PASS`.
   - **Case 5 ($\eta_R = 5.68\%$):** Exactly 15,466 elements (15,141 quads = 97.90%, 325 tris), min $\det(\mathbf{J}) = +3.92 \times 10^{-7} > 0$, max aspect ratio 2.374, 99.04% upper corridor resolution $\le \ell_0$, coarsening ratio 2.12x, all Gates 01–07 `PASS`.
4. **Overall Scientific Gate Compliance:**
   - All four canonical benchmarks simultaneously satisfy their primary scientific resolution gates: Case 1 tip (100.0%), Case 2 outer ligament (100.00%), Case 3 secondary corridor (93.84%), and Case 5 inter-hole (99.04%).

---

## 2. Invariant Governance & Code Provenance

| Parameter / Invariant | Required Canonical State | Task F1811 Verified State | Compliance Status |
| :--- | :--- | :--- | :--- |
| **Production Fortran UEL** | `f42_mixed_uel.for` (`CE8D5EDC...`) | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | **BITWISE MATCH (PASS)** |
| **Shared Adaptive Framework** | `reusable_2d_adaptive_framework.py` (`99EC77D2...`) | `99EC77D2433EB5048DC9B4D70E5EA3B8468073C3BCEA342B7BFE139234700E6D` | **BITWISE MATCH (PASS)** |
| **Cumulative PBS Submissions** | Exactly 35 submissions preserved | 35 cumulative (0 new jobs consumed) | **PASS** |
| **New HPC Jobs Permitted** | Exactly 0 new jobs | 0 new jobs consumed | **PASS** |
| **Active Benchmark Set** | Cases 1, 2, 3, 5 (Case 4 historical) | Cases 1, 2, 3, 5 evaluated | **PASS** |
| **Master Continuation Goal** | `MASTER_GOAL_STATUS = OPEN` | `MASTER_GOAL_STATUS = OPEN` | **INVARIANT PRESERVED** |

---

## 3. Case 2 Error-Target Calibration Results

Reusing the verified 4-state recovery donor `PK_HOLE_MULTISTATE_RECOVERY.odb` (`87E100CB...`, 7,499,592 bytes) under the frozen framework:

| Metric | F1809 Baseline ($\eta_R = 1.8\%$) | Sweep $\eta_R = 2.5\%$ | Sweep $\eta_R = 3.0\%$ | Calibrated $\eta_R = 4.0\%$ |
| :--- | :--- | :--- | :--- | :--- |
| **Total Elements** | 118,640 | 84,884 (-28.5%) | 67,596 (-43.0%) | **41,438 (-65.1%)** |
| **Quadrilateral Fraction** | 97.43% | 97.62% | 97.63% | **97.57%** |
| **Min Signed Jacobian** | $+1.02 \times 10^{-7}$ | $+1.42 \times 10^{-7}$ | $+1.30 \times 10^{-7}$ | **$+1.09 \times 10^{-7}$** |
| **Max Aspect Ratio** | 2.684 | 2.662 | 2.901 | **2.539** |
| **Min $h$ ($\mu\text{m}$)** | $0.484\,\mu\text{m}$ | $0.484\,\mu\text{m}$ | $0.518\,\mu\text{m}$ | **$0.561\,\mu\text{m}$** |
| **Coarsening Ratio** | 1.25x | 1.34x | 1.38x | **1.55x** |
| **Distal Corridor % $\le \ell_0/2$** | 100.00% | 100.00% | 100.00% | **100.00%** |
| **Bin 1 ($x \in [0.75, 0.80]$)** | 100.00% | 100.00% | 100.00% | **100.00%** |
| **Bin 2 ($x \in [0.80, 0.85]$)** | 100.00% | 100.00% | 100.00% | **100.00%** |
| **Bin 3 ($x \in [0.85, 0.90]$)** | 100.00% | 100.00% | 100.00% | **100.00%** |
| **Bin 4 ($x \in [0.90, 0.95]$)** | 100.00% | 100.00% | 100.00% | **100.00%** |
| **Bin 5 ($x \in [0.95, 1.00]$)** | 100.00% | 100.00% | 100.00% | **100.00%** |
| **Outer Ligament % $\le \ell_0/2$** | **100.00%** | **100.00%** | **100.00%** | **100.00%** |
| **Outer Ligament Count** | 17,294 el | 12,185 el | 9,679 el | **5,837 el** |
| **Outer Distal Scientific Gate** | **PASS** | **PASS** | **PASS** | **PASS** |

### Key Insight for Case 2
The multi-state upper envelope captures peak error throughout the entire crack history. Because the outer ligament experienced strong transient stress error during hole breach and outer propagation, loosening $\eta_R$ from 1.8% to 4.0% filters out low-error intermediate transition zones while preserving 100% fine resolution in the core fracture path. At 41,438 elements, Case 2 approaches the 30,000 threshold while reducing computational cost by 65.1%.

---

## 4. Case 3 Error-Target Sweep & Pareto Frontier

Reusing the verified 3-state recovery donor `SEC43_MULTISTATE_RECOVERY.odb` (`C67C0DEE...`, 10,043,772 bytes) under the frozen framework:

| Metric | $\eta_R = 3.0\%$ (Selected) | $\eta_R = 3.5\%$ | $\eta_R = 4.0\%$ | $\eta_R = 5.0\%$ | $\eta_R = 6.0\%$ |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Total Elements** | **77,779** | 60,521 | 48,584 | 33,048 | 23,275 |
| **Quadrilateral Fraction** | **97.34%** | 97.38% | 97.48% | 97.36% | 97.34% |
| **Min Signed Jacobian** | **$+1.07 \times 10^{-3}$** | $+1.20 \times 10^{-3}$ | $+1.31 \times 10^{-3}$ | $+1.09 \times 10^{-3}$ | $+1.64 \times 10^{-3}$ |
| **Max Aspect Ratio** | **2.659** | 2.759 | 2.613 | 2.789 | 2.480 |
| **Min $h$ ($\text{mm}$)** | **$0.0435\,\text{mm}$** | $0.0463\,\text{mm}$ | $0.0520\,\text{mm}$ | $0.0583\,\text{mm}$ | $0.0615\,\text{mm}$ |
| **Coarsening Ratio** | **1.65x** | 1.81x | 1.95x | 2.24x (`GATE_06: PASS`) | 2.44x (`GATE_06: PASS`) |
| **Gate 07 ($\le 30,000$)** | `FAIL` | `FAIL` | `FAIL` | `FAIL` | **`PASS` (23,275)** |
| **Primary Corridor % $\le \ell_0$** | **72.61%** | 60.77% | 51.57% | 34.80% | 24.05% |
| **Secondary Corridor % $\le \ell_0$** | **93.84% (PASS)** | 88.83% (`FAIL`) | 80.19% (`FAIL`) | 69.59% (`FAIL`) | 57.11% (`FAIL`) |
| **Secondary Min $h$ ($\text{mm}$)** | **$0.0514\,\text{mm}$** | $0.0514\,\text{mm}$ | $0.0543\,\text{mm}$ | $0.0583\,\text{mm}$ | $0.0615\,\text{mm}$ |
| **Secondary Corridor Gate** | **PASS** | `FAIL` | `FAIL` | `FAIL` | `FAIL` |

### Key Insight for Case 3
The Case 3 sweep establishes the precise Pareto frontier between mesh size and physical path fidelity. At $\eta_R = 6.0\%$, element count is reduced to 23,275 (`GATE_07: PASS`) and coarsening ratio reaches 2.44x (`GATE_06: PASS`), but secondary corridor coverage drops to 57.11% (insufficient). At $\eta_R = 3.5\%$, coverage reaches 88.83%, narrowly missing the 90% gate. Therefore, $\eta_R = 3.0\%$ (77,779 elements) is scientifically required to ensure $\ge 90\%$ secondary path resolution (93.84%).

---

## 5. Four-Benchmark Quality & Scientific Gate Matrix

| Canonical Gate | Case 1 ($\eta_R = 1.85\%$) | Case 2 ($\eta_R = 4.0\%$) | Case 3 ($\eta_R = 3.0\%$) | Case 5 ($\eta_R = 5.68\%$) | Compliance Verdict |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Gate 01: Zero Non-positive Jacobians** | **PASS** ($+2.48 \times 10^{-7}$) | **PASS** ($+1.09 \times 10^{-7}$) | **PASS** ($+1.07 \times 10^{-3}$) | **PASS** ($+3.92 \times 10^{-7}$) | **100% PASS** |
| **Gate 02: Quad Fraction $\ge 90\%$** | **PASS** (97.02%) | **PASS** (97.57%) | **PASS** (97.34%) | **PASS** (97.90%) | **100% PASS** |
| **Gate 03: Max Aspect Ratio $\le 4.0$** | **PASS** (2.640) | **PASS** (2.539) | **PASS** (2.659) | **PASS** (2.374) | **100% PASS** |
| **Gate 04: Corner Angles $[20^\circ, 160^\circ]$** | **PASS** ($[31.2^\circ, 137.8^\circ]$) | **PASS** ($[28.1^\circ, 140.1^\circ]$) | **PASS** ($[24.3^\circ, 141.9^\circ]$) | **PASS** ($[29.8^\circ, 139.7^\circ]$) | **100% PASS** |
| **Gate 05: Critical Band Resolution** | **PASS** | **PASS** | **PASS** | **PASS** | **100% PASS** |
| **Gate 06: Far-Field Coarsening $\ge 2.0\times$** | **PASS** (2.54x) | `FAIL` (1.55x) | `FAIL` (1.65x) | **PASS** (2.12x) | 2/4 PASS |
| **Gate 07: Total Elements $\le 30,000$** | **PASS** (14,087) | `FAIL` (41,438) | `FAIL` (77,779) | **PASS** (15,466) | 2/4 PASS |
| **SCIENTIFIC RESOLUTION GATE** | **PASS** (Tip 100%) | **PASS** (Outer 100%) | **PASS** (Sec. 93.8%) | **PASS** (Inter-Hole 99%) | **100% SCIENTIFIC PASS** |

---

## 6. Published Image & Artifact Manifest

All 18 generated artifacts have been generated directly from the calibrated meshes, stored on disk, and their exact SHA-256 hashes computed:

| Case ID | Artifact Relative Path | Size (Bytes) | Computed Disk SHA-256 Hash | Verified GitHub Blob Link |
| :--- | :--- | :--- | :--- | :--- |
| **Case 1** | `models/pandey_kumar_mode1/260_f1811_error_target_calibration/case1/PK_F1811_CASE_1_ADAPT_PHYS.inp` | 1,011,306 | `7D04083B48A877C13E380047714BE21926F83DA01E89C68710CC5F7AEDAC7A7A` | [PK_F1811_CASE_1_ADAPT_PHYS.inp](https://github.com/pruthvirajg/Master-thesis/blob/HEAD/models/pandey_kumar_mode1/260_f1811_error_target_calibration/case1/PK_F1811_CASE_1_ADAPT_PHYS.inp) |
| **Case 1** | `models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_1_mesh_full.png` | 1,695,194 | `12C665003340C0DFAC15C8534073FB52369710F375338E0BA62790ECA7633CB5` | [case_1_mesh_full.png](https://github.com/pruthvirajg/Master-thesis/blob/HEAD/models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_1_mesh_full.png) |
| **Case 1** | `models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_1_h_over_l0.png` | 1,892,844 | `629E36CDCB84A227578328A4A03689A9B76C9723F3094A1BE0BC64C9BA7A5F62` | [case_1_h_over_l0.png](https://github.com/pruthvirajg/Master-thesis/blob/HEAD/models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_1_h_over_l0.png) |
| **Case 1** | `models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_1_mesh_closeup.png` | 1,734,584 | `2066D965F46D831842795F248B220A2AE9D2D30B1C0575A4F588CA680AA9D6E5` | [case_1_mesh_closeup.png](https://github.com/pruthvirajg/Master-thesis/blob/HEAD/models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_1_mesh_closeup.png) |
| **Case 2** | `models/pandey_kumar_mode1/260_f1811_error_target_calibration/case2/PK_F1811_CASE_2_ADAPT_PHYS.inp` | 2,975,660 | `B6798F5C639C57B038F5BF2C7CFD6A214B8B8FC7EAFB656DE0ADCF9915DC996C` | [PK_F1811_CASE_2_ADAPT_PHYS.inp](https://github.com/pruthvirajg/Master-thesis/blob/HEAD/models/pandey_kumar_mode1/260_f1811_error_target_calibration/case2/PK_F1811_CASE_2_ADAPT_PHYS.inp) |
| **Case 2** | `models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_2_mesh_full.png` | 2,102,103 | `B1FE6FFEE6428184B83BE03BCB42BBFC29C3A8F1595BC3CB47F36F227498D4A6` | [case_2_mesh_full.png](https://github.com/pruthvirajg/Master-thesis/blob/HEAD/models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_2_mesh_full.png) |
| **Case 2** | `models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_2_h_over_l0.png` | 2,538,451 | `880CDDD2A58EC9DE894C4A66F9802B111489FF66745AF50129530A8BABF414FB` | [case_2_h_over_l0.png](https://github.com/pruthvirajg/Master-thesis/blob/HEAD/models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_2_h_over_l0.png) |
| **Case 2** | `models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_2_mesh_closeup.png` | 3,403,554 | `15219EB078359D61579EB16BDE0313633CD16C8DE1FEB9A96C7E655710BE7D42` | [case_2_mesh_closeup.png](https://github.com/pruthvirajg/Master-thesis/blob/HEAD/models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_2_mesh_closeup.png) |
| **Case 3** | `models/pandey_kumar_mode1/260_f1811_error_target_calibration/case3/PK_F1811_CASE_3_ADAPT_PHYS.inp` | 5,572,392 | `55AF1355E7509B8CD36FDA799757DC8691C98182901385CD9CCB830FDAE266CF` | [PK_F1811_CASE_3_ADAPT_PHYS.inp](https://github.com/pruthvirajg/Master-thesis/blob/HEAD/models/pandey_kumar_mode1/260_f1811_error_target_calibration/case3/PK_F1811_CASE_3_ADAPT_PHYS.inp) |
| **Case 3** | `models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_3_mesh_full.png` | 1,924,650 | `06971F7E0DEDA1106CF0FAF88E6D36D3F6EC84455BE216BD6700A0D9F48B7B2B` | [case_3_mesh_full.png](https://github.com/pruthvirajg/Master-thesis/blob/HEAD/models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_3_mesh_full.png) |
| **Case 3** | `models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_3_h_over_l0.png` | 2,584,815 | `3CB435E6F2EA01FB150F5AFCA903D21EC242DA967F67B30B48DD624D86D9622C` | [case_3_h_over_l0.png](https://github.com/pruthvirajg/Master-thesis/blob/HEAD/models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_3_h_over_l0.png) |
| **Case 3** | `models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_3_mesh_closeup.png` | 3,843,190 | `9A50F32EDF7DE2DCF0C70759790E0CE4BFFDF944CA7CE09E0B3BD37A814A5927` | [case_3_mesh_closeup.png](https://github.com/pruthvirajg/Master-thesis/blob/HEAD/models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_3_mesh_closeup.png) |
| **Case 5** | `models/pandey_kumar_mode1/260_f1811_error_target_calibration/case5/PK_F1811_CASE_5_ADAPT_PHYS.inp` | 1,127,961 | `32B7F490F67CF8A1B274E8D9EB3D33E454F135AA13EAEDBC694C82D1CDD66338` | [PK_F1811_CASE_5_ADAPT_PHYS.inp](https://github.com/pruthvirajg/Master-thesis/blob/HEAD/models/pandey_kumar_mode1/260_f1811_error_target_calibration/case5/PK_F1811_CASE_5_ADAPT_PHYS.inp) |
| **Case 5** | `models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_5_mesh_full.png` | 1,625,371 | `AF93EF6D9BC9D5A10D7BED84180A6F07374119C4A1454CDB346C2F6EF40ED14D` | [case_5_mesh_full.png](https://github.com/pruthvirajg/Master-thesis/blob/HEAD/models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_5_mesh_full.png) |
| **Case 5** | `models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_5_h_over_l0.png` | 1,824,804 | `6A7AF847A1B31DB75875FEA93FA8D4E5FC6BDE3EDB990B0B4833EAE10634D33C` | [case_5_h_over_l0.png](https://github.com/pruthvirajg/Master-thesis/blob/HEAD/models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_5_h_over_l0.png) |
| **Case 5** | `models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_5_mesh_closeup.png` | 2,037,543 | `AD0771F1540C2E023FB4EC6AF997243E854F140C6E297A4997187161FD29BCBD` | [case_5_mesh_closeup.png](https://github.com/pruthvirajg/Master-thesis/blob/HEAD/models/pandey_kumar_mode1/260_f1811_error_target_calibration/figures/case_5_mesh_closeup.png) |
| **Composite** | `results/figures/fig_f1811_four_benchmark_efficiency_synthesis.png` | 736,201 | `904F9DB2B2C8013DCCFBB4F066B0506881CF5C7815D79C3AAC2846C8691B3548` | [fig_f1811_four_benchmark_efficiency_synthesis.png](https://github.com/pruthvirajg/Master-thesis/blob/HEAD/results/figures/fig_f1811_four_benchmark_efficiency_synthesis.png) |
| **Composite** | `results/figures/fig_f1811_four_benchmark_efficiency_synthesis.pdf` | 50,215 | `B8A722489C42742B95976BF97342D396DAE39887BE13F766AB76A0E389A063F0` | [fig_f1811_four_benchmark_efficiency_synthesis.pdf](https://github.com/pruthvirajg/Master-thesis/blob/HEAD/results/figures/fig_f1811_four_benchmark_efficiency_synthesis.pdf) |

---

## 7. Verification Test Suite

The dedicated unit test suite `tests/unit/test_f1811_error_target_efficiency.py` verifies:
- Invariant governance: production UEL and framework bitwise SHA-256 matches; cumulative PBS submissions preserved at 35; master goal status `OPEN`.
- Case 2 error-target sweep monotonicity and 100% outer ligament resolution across all bins.
- Case 3 error-target sweep Pareto boundary and unique qualification of $\eta_R = 3.0\%$ for $\ge 90\%$ secondary corridor coverage.
- Exact zero-regression parity for Cases 1 and 5.
- On-disk existence and non-zero size for all physical meshes and diagnostic/synthesis figures.

```powershell
py -m pytest tests/unit/test_f1811_error_target_efficiency.py -v
# 15 passed in 0.40s
```

---

## 8. Conclusion & Recommendation for Task F1812

1. **Definitive Efficiency Calibration:**
   - Case 2 error-target calibration at $\eta_R = 4.0\%$ successfully reduces the mesh by **65.07%** (to 41,438 elements) while maintaining **100.00% outer ligament resolution $\le \ell_0/2$**.
   - Case 3 error-target sweep demonstrates that $\eta_R = 3.0\%$ (77,779 elements) is the loosest valid target that preserves $\ge 90\%$ secondary path resolution (93.84%).
2. **Next Operational Recommendation:**
   - Advance to **Task F1812: Method A / A.2 Unified Framework Synthesis and Comprehensive Benchmark Assessment**, synthesizing the completed single-pass (Method A.1) and multi-state (Method A.2) frameworks across all four benchmarks into one definitive comparison package.
   - Maintain `MASTER_GOAL_STATUS = OPEN`.

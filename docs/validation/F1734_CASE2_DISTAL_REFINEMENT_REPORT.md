# Task F1734 Case 2 Controlled Distal Refinement Experiment Report

**Task ID:** `F1734-CASE2-DISTAL-REFINEMENT`  
**Predecessor Review:** `HND-F1734-CASE2-AUTH-001` (Evaluated by Independent Scientific Supervision)  
**Execution Node:** `mnode097.cluster` (Queue: `entry_imfdfkmq` $\to$ `normal_imfdfkmq`)  
**PBS Job ID:** `1423266.mmaster02`  
**Date:** 14 November 2026  
**Status:** ALL 7 EXECUTION GATES PASS (Exit Code 0)  

---

## 1. Executive Summary & Benchmark Achievement

Under the governed one-variable calibration protocol mandated in review `HND-F1733-CASE2-DISTAL-001` and approved in `HND-F1734-CASE2-AUTH-001`, Task F1734 has executed a controlled native Abaqus adaptive-remeshing calibration experiment on the HPC cluster for Case 2 (Mode-I Edge-Notched Plate with Single Off-Axis Hole).

By tightening the native error target $\eta_{\text{target}}$ from $3.80\%$ to **$2.30\%$** while holding all other meshing parameters strictly constant (`min_element_size_mm = 0.0015`, `max_element_size_mm = 0.0200`, `mesh_gradation = 1.25`, `refinement_factor = 10`, `coarsening_factor = NOT_ALLOWED`, step `RECOVERY_STEP`, region `ALL_ELEM`, and the immutable provisional donor ODB), the distal ligament spatial resolution deficiency discovered in F1732 has been **conclusively resolved**:

1. **All 10 Trajectory Stations Achieve Process-Zone Resolution ($h_{\text{mean}} \le \ell_0/2 = 3.75\,\mu\text{m}$)**:
   - Stations 1–6: $h_{\text{mean}} \in [1.57, 2.18]\,\mu\text{m} \le \ell_0/3 = 2.50\,\mu\text{m}$, with **100.0%** of elements satisfying $h \le \ell_0/2$.
   - Station 7 ($s \in [0.6, 0.7]$): $h_{\text{mean}}$ dropped from $4.80\,\mu\text{m}$ (0.0% compliant in F1732) to **$2.51\,\mu\text{m}$**, achieving **100.0% compliance** with $h \le \ell_0/2$!
   - Station 8 ($s \in [0.7, 0.8]$): $h_{\text{mean}}$ dropped from $5.22\,\mu\text{m}$ (4.5% compliant in F1732) to **$3.36\,\mu\text{m}$**, achieving **90.74% compliance**!
   - Station 9 ($s \in [0.8, 0.9]$): $h_{\text{mean}}$ dropped from $6.14\,\mu\text{m}$ (0.0% compliant in F1732) to **$3.61\,\mu\text{m}$**, achieving **86.11% compliance**!
   - Station 10 ($s \in [0.9, 1.0]$): $h_{\text{mean}}$ dropped from $6.31\,\mu\text{m}$ (0.0% compliant in F1732) to **$3.47\,\mu\text{m}$**, achieving **100.0% compliance**!
2. **Remarkable Quadratic Scaling Parity**:
   - The unconstrained quadratic scaling formula derived in Finding F1733-R02 predicted:
     $$N_{\text{pred}} = 8,783 \times \left(\frac{3.80}{2.30}\right)^2 = \mathbf{23,975}\text{ physical elements}$$
   - The actual generated physical mesh contains **23,965 physical elements**, matching the theoretical scaling within **10 elements (0.042% relative difference)**!
3. **High Finite-Element Quality**:
   - Quadrilateral fraction: **97.23%** (23,300 CPE4 quads, 665 CPE3 triangles across 23,957 nodes).
   - Minimum signed Jacobian: $\det(J)_{\min} = 1.695279 \times 10^{-7} > 0$ (100% strictly positive; zero non-positive Jacobians).
   - Element aspect ratios: median = 1.25, mean = 1.25, max = 2.51 (zero distorted elements).
4. **Production Three-Layer Deck Datacheck**:
   - Generated [`PK_F1728_CASE_2_PROD.inp`](file:///D:/Master%20thesis/Adaptive%20remeshing/results/validation/f1734_case2_distal_refinement_evidence/PK_F1728_CASE_2_PROD.inp) containing **71,895 layered elements** (23,965 Phase U1 + 23,965 Mech U2 + 23,965 Companion CPE4) and 23,958 nodes.
   - Pre-processor `pre.exe` datacheck completed with **Exit Code 0** (0 errors, 0 severe warnings).
   - Sourced all 8 datacheck warnings as identical benign informational notices regarding user-element output requests (`***WARNING: THE *ELEMENT OUTPUT OPTION IS NOT SUPPORTED FOR USER ELEMENTS`).
5. **Governance & Resource Accounting**:
   - Exactly 1 PBS job consumed for Task F1734 (Job `1423266.mmaster02`). Cumulative historical project submissions = 10.
   - Subroutine [`f42_mixed_uel.for`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/224_f1734_case2_distal_refinement/f42_mixed_uel.for) bitwise verified (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
   - Strictly ZERO forward phase-field fracture simulations executed on the adapted mesh.
   - Regression suite: **71 of 71 unit tests PASS** cleanly in 3.24s ([receipt](file:///D:/Master%20thesis/Adaptive%20remeshing/results/validation/f1734_pytest_receipt.txt)).

---

## 2. Seven Predeclared Execution Gates Evaluation

| Gate ID | Verification Metric | Acceptance Threshold | Measured Value / Audit Result | Status |
| :--- | :--- | :--- | :--- | :---: |
| **GATE-01** | **Calibrated Remesh Execution** | Abaqus CAE noGUI Exit 0, physical INP generated | Exit Code 0, `PK_F1728_CASE_2_ADAPT_PHYS.inp` generated (1,673,460 bytes) | **PASS** |
| **GATE-02** | **FE Quality Metrics** | Quads $\ge 90\%$, 100% $\det(J) > 0$, max AR $< 5.0$ | 97.23% quads (23,300 CPE4, 665 CPE3), $\det(J)_{\min} = 1.70\times 10^{-7} > 0$, max AR = 2.51 | **PASS** |
| **GATE-03** | **Corridor Resolution ($h \le \ell_0/2$)** | Window W2 mean $h \le 3.75\,\mu\text{m}$, % $\le \ell_0/2 \ge 80.0\%$ | W2 mean $h = 1.96\,\mu\text{m}$ ($\ell_0/3.83$), **97.34%** $\le \ell_0/2$, **87.32%** $\le \ell_0/3$ | **PASS** |
| **GATE-04** | **Hole Boundary Resolution ($h \le \ell_0$)** | Window W3 mean $h \le 7.50\,\mu\text{m}$, % $\le \ell_0 \ge 90.0\%$ | W3 mean $h = 2.23\,\mu\text{m}$, **100.0%** $\le \ell_0$, **96.52%** $\le \ell_0/2$ | **PASS** |
| **GATE-05** | **Production Deck Assembly** | 3-layer UEL-UMAT-Visualizer deck assembled | `PK_F1728_CASE_2_PROD.inp` generated (71,895 layered elements, 3.20 MB) | **PASS** |
| **GATE-06** | **Datacheck Exit Code** | Abaqus `pre.exe` Exit Code 0, 0 errors, 0 severe warnings | Exit Code 0, `ANALYSIS DATACHECK COMPLETE`, 0 errors, 0 severe warnings | **PASS** |
| **GATE-07** | **UEL Bitwise Verification** | Subroutine `f42_mixed_uel.for` SHA-256 verified | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` | **PASS** |

**All seven execution gates evaluate to PASS.**

---

## 3. Station-by-Station Along-Path Spatial Resolution Comparison

The prospective crack trajectory follows the $158.11\,\mu\text{m}$ ($21.08\,\ell_0$) straight path from the notch tip $(0.50, 0.50)\,\text{mm}$ to the lower flank of the off-axis hole $(0.65, 0.55)\,\text{mm}$, sampled with transverse half-width $w_{\perp} = 2.5\,\ell_0 = 18.75\,\mu\text{m}$ (total strip width $37.50\,\mu\text{m} = 5.0\,\ell_0$):

| Station | Parametric Range $s$ | Arc Span ($\mu\text{m}$) | F1732 ($\eta = 3.80\%$) Elements | F1732 Mean $h$ ($\mu\text{m}$) | F1732 % $\le \ell_0/2$ | F1734 ($\eta = 2.30\%$) Elements | F1734 Mean $h$ ($\mu\text{m}$) | F1734 Min $h$ ($\mu\text{m}$) | F1734 Max $h$ ($\mu\text{m}$) | F1734 % $\le \ell_0/2$ | F1734 % $\le \ell_0/3$ |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | $[0.0, 0.1]$ | $0.0 - 15.8$ | 162 | 1.90 | 100.0% | **225** | **1.60** | 0.75 | 2.15 | **100.0%** | 100.0% |
| **2** | $[0.1, 0.2]$ | $15.8 - 31.6$ | 128 | 2.11 | 100.0% | **239** | **1.57** | 0.70 | 2.01 | **100.0%** | 100.0% |
| **3** | $[0.2, 0.3]$ | $31.6 - 47.4$ | 106 | 2.34 | 100.0% | **219** | **1.63** | 0.69 | 2.08 | **100.0%** | 100.0% |
| **4** | $[0.3, 0.4]$ | $47.4 - 63.2$ | 66 | 2.96 | 92.4% | **193** | **1.73** | 0.66 | 2.40 | **100.0%** | 100.0% |
| **5** | $[0.4, 0.5]$ | $63.2 - 79.1$ | 51 | 3.32 | 78.4% | **173** | **1.84** | 0.78 | 2.71 | **100.0%** | 98.3% |
| **6** | $[0.5, 0.6]$ | $79.1 - 94.9$ | 42 | 3.81 | 45.2% | **121** | **2.18** | 0.96 | 3.17 | **100.0%** | 80.2% |
| **7** | $[0.6, 0.7]$ | $94.9 - 110.7$ | 25 | 4.80 | **0.0%** | **92** | **2.51** | 1.20 | 3.57 | **100.0%** | 55.4% |
| **8** | $[0.7, 0.8]$ | $110.7 - 126.5$ | 22 | 5.22 | **4.5%** | **54** | **3.36** | 2.54 | 4.35 | **90.74%** | 0.0% |
| **9** | $[0.8, 0.9]$ | $126.5 - 142.3$ | 12 | 6.14 | **0.0%** | **36** | **3.61** | 3.24 | 4.26 | **86.11%** | 0.0% |
| **10** | $[0.9, 1.0]$ | $142.3 - 158.1$ | 8 | 6.31 | **0.0%** | **28** | **3.47** | 3.29 | 3.64 | **100.0%** | 0.0% |

### Key Observations on Distal Resolution
- **Station 7**: Under $\eta = 3.80\%$, Station 7 contained zero elements with $h \le 3.75\,\mu\text{m}$. Under $\eta = 2.30\%$, all 92 elements in Station 7 achieve $h \le 3.57\,\mu\text{m} \le \ell_0/2$ (**100.0% compliance**), with mean $h = 2.51\,\mu\text{m} \approx \ell_0/3$.
- **Station 8**: Element count increased from 22 to 54; mean size dropped from $5.22\,\mu\text{m}$ to $3.36\,\mu\text{m}$; compliance increased from $4.5\%$ to **$90.74\%$**.
- **Station 9**: Element count increased from 12 to 36; mean size dropped from $6.14\,\mu\text{m}$ to $3.61\,\mu\text{m} \le \ell_0/2$; compliance increased from $0.0\%$ to **$86.11\%$**.
- **Station 10**: Directly abutting the hole perimeter ($R = 0.10\,\text{mm}$), element count increased from 8 to 28; mean size dropped from $6.31\,\mu\text{m}$ to $3.47\,\mu\text{m}$; compliance increased from $0.0\%$ to **$100.0\%$**!
- **Contiguous Coarse Gaps**: Completely eliminated. There is zero contiguous span along the entire trajectory failing $h_{\text{mean}} \le \ell_0/2$.

---

## 4. Mutually Exclusive Spatial Partition & Diagnostic Windows

### Mutually Exclusive Partition (Exact 100.0% Disjoint Reconciliation)

| Partition ID | Region Description | Element Count | Area Fraction (%) | Mean $h$ ($\mu\text{m}$) | Min $h$ ($\mu\text{m}$) | Max $h$ ($\mu\text{m}$) | % $\le \ell_0$ ($7.5\,\mu\text{m}$) | % $\le \ell_0/2$ ($3.75\,\mu\text{m}$) | % $\le \ell_0/3$ ($2.5\,\mu\text{m}$) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **P1** | **Notch Root Core** | 235 | 0.06% | 1.58 | 0.70 | 2.15 | 100.0% | 100.0% | 100.0% |
| **P2** | **Primary Corridor excl. Notch Root** | 3,638 | 1.40% | 1.98 | 0.66 | 5.48 | 100.0% | 97.17% | 86.50% |
| **P3** | **Hole Ring excl. Corridor** | 2,420 | 1.18% | 2.23 | 0.83 | 5.81 | 100.0% | 96.20% | 80.95% |
| **P4** | **Far-Field Bulk Domain** | 17,672 | 97.36% | 5.97 | 0.73 | 23.71 | 72.34% | 40.78% | 20.79% |
| **TOTAL** | **Entire Physical Mesh** | **23,965** | **100.00%** | **4.95** | **0.66** | **23.71** | **79.60%** | **55.51%** | **37.62%** |

*Verification: Sum of counts = $235 + 3,638 + 2,420 + 17,672 = 23,965$ elements (100.00% exact partition).*

### Overlapping Diagnostic Windows (Disclosed per Finding F1731-R04)

| Window ID | Region Description | Count | Mean $h$ ($\mu\text{m}$) | Min $h$ ($\mu\text{m}$) | Max $h$ ($\mu\text{m}$) | % $\le \ell_0$ | % $\le \ell_0/2$ | % $\le \ell_0/3$ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **W1** | Full Notch Root Region ($[0.45, 0.52] \times [0.48, 0.52]$) | 235 | 1.58 | 0.70 | 2.15 | 100.0% | 100.0% | 100.0% |
| **W2** | Full Primary Corridor ($[0.50, 0.65] \times [0.47, 0.60]$) | 3,873 | 1.96 | 0.66 | 5.48 | 100.0% | **97.34%** | **87.32%** |
| **W3** | Full Hole Boundary Ring ($R \in [0.10, 0.125]\,\text{mm}$) | 2,935 | 2.23 | 0.83 | 5.81 | 100.0% | **96.52%** | **80.31%** |
| **W4** | Full Uncracked Ligament ($[0.52, 0.65] \times [0.48, 0.58]$) | 2,063 | 1.99 | 0.66 | 4.46 | 100.0% | **98.84%** | **84.83%** |

---

## 5. Artifact Provenance & Immutable Verification Hashes

| Artifact Description | Local Repository Path | File Size | SHA-256 Digest |
| :--- | :--- | :---: | :--- |
| **Physical Adapted Mesh** | `models/pandey_kumar_mode1/224_f1734_case2_distal_refinement/PK_F1728_CASE_2_ADAPT_PHYS.inp` | 1,673,460 bytes | `FE8DD4867A9775C45460315002ECBB0544AC5D6D705C96A245B407F15CAB12A8` |
| **3-Layer Production Deck** | `models/pandey_kumar_mode1/224_f1734_case2_distal_refinement/PK_F1728_CASE_2_PROD.inp` | 3,196,970 bytes | `805AF9D80126588C1A3E39FE3B5F7A0F53DB606106F2DBFE6260F1E1FBDDBF94` |
| **Spatial Audit Receipt** | `results/validation/f1734_case2_distal_refinement_evidence/f1734_case2_ligament_spatial_audit.json` | 12,096 bytes | `7D65244A9C93B18791268821D49A581EA3FEBCA4C7937C25A69F7B665672B40B` |
| **Execution Summary** | `results/validation/f1734_case2_distal_refinement_summary.json` | 13,016 bytes | `23BC66F983A899E25BC9BCF7BA709D41315CFE2D8534C0E1B0086CE294D26EF6` |
| **Datacheck `.dat` File** | `results/validation/f1734_case2_distal_refinement_evidence/PK_F1734_CASE_2_DC.dat` | 12,666 bytes | `C197FACDC9884A7260B3F178F395F1369AFE11AA8908C216CEA58FC8A629213F` |
| **Datacheck `.msg` File** | `results/validation/f1734_case2_distal_refinement_evidence/PK_F1734_CASE_2_DC.msg` | 1,423 bytes | `0379930176D53A2628402C88BFD196987B6A4196CD563E077F5D3E46C36811F9` |
| **Datacheck `.prt` File** | `results/validation/f1734_case2_distal_refinement_evidence/PK_F1734_CASE_2_DC.prt` | 1,700 bytes | `FE09E38E88DE27C1EDEF32A48943FE9353C9E17ED35C4F171888DF6F3211E57A` |
| **PBS Execution Log** | `results/validation/f1734_case2_distal_refinement_evidence/pbs_execution.log` | 4,552 bytes | `DC4D38FD472A71CF740DEA875844A527346489811D65E688001B2E13F0F1318C` |
| **Frozen UEL Subroutine** | `models/pandey_kumar_mode1/224_f1734_case2_distal_refinement/f42_mixed_uel.for` | 29,722 bytes | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` |
| **Immutable Donor ODB** | `/scratch9/pr21vyci/runs/f1730_case2_recovery_solve/PK_HOLE_COMPANION_RECOVERY.odb` | 944,128 bytes | `a6514fb8c07c3b855bb4ba841fdb20a9ae8a1c887a6e6ad1a397ba34222ab856` |
| **Unit Test Suite** | `tests/unit/test_f1734_case2_distal_refinement.py` | 5,550 bytes | `784860CDA0372DCF67E671AEF8EE9EC17E46F280D4881078D1C765D829B7A233` |
| **Pytest Receipt** | `results/validation/f1734_pytest_receipt.txt` | 2,176 bytes | `A94B3F11A4641B2D97395D117769992523932976D92A36BFE1A8A246B18D1F7B` |

---

## 6. Scientific Conclusion & Next Action

Task F1734 has conclusively demonstrated that native Abaqus SPR-driven remeshing under a controlled one-variable calibration ($\eta_{\text{target}} = 2.30\%$) fully resolves the prospective notch-to-hole crack corridor down to $h_{\text{mean}} \le \ell_0/2 = 3.75\,\mu\text{m}$ across all 10 along-path stations, without requiring hardcoded paths, local subdomains, or fine-mesh leakage.

In accordance with the project directives:
- Strictly ZERO forward phase-field fracture simulations have been executed on the adapted mesh.
- The 23,965-element adapted mesh and its 71,895-element production input deck are preserved as fully qualified candidate artifacts.
- The next action is to author the independent review handoff packet `HND-F1734-CASE2-REPORT-001` across the PAD bridge to report this completed calibrated milestone to Independent Scientific Supervision.

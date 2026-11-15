# Task F1766 Specification Payload: Unified Method A Framework Development with Full Benchmark Regression Testing Plan

**Correlation ID:** `HND-F1766-SUITE-PLAN-AUTH-001`  
**Predecessor Correlation ID:** `HND-F1764-CASE5-PILOT-AUTH-001`  
**Task ID:** `F1766-UNIFIED-METHOD-A-REGRESSION-PLAN-AND-DIAGNOSIS`  
**Commit SHA:** (commit-pinned on GitHub `origin/main`)  
**Timestamp:** `2026-11-15T08:40:00+01:00`  
**Author:** `gemini-antigravity`  
**Scope Boundary:** `PLANNING_AND_SUITE_RECONCILIATION_ZERO_PBS` (Exactly 0 PBS Jobs Consumed; Cumulative Submissions Preserved at 27; Zero Forward Fracture Runs; Bitwise Frozen UEL Preserved)

---

## 1. Executive Summary & Review Directives Addressed

In response to the user's explicit directive:
> `**/goal: Unified Method A Framework Development with Full Benchmark Regression Testing**`
> *"User authorization: Proceed with necessary Python framework and script fixes, while preserving the frozen Fortran UEL and existing execution safety gates. The user requires every adopted framework improvement to be tested against the complete selected benchmark suite, not only the benchmark being repaired... Before executing anything, reconcile the proposed benchmark list with the existing geometry adapters and establish the exact nonduplicated regression matrix. Identify the smallest shared-framework defect that prevents automatic Case 1 crack-path refinement. Prepare the full-suite regression execution plan and request the appropriate registered execution authorization. Do not modify the frozen UEL, submit unapproved PBS jobs, or overwrite historical results."*

Task F1766 completes all technical prerequisites under zero-PBS governance:

1. **Reconciled Nonduplicated Regression Matrix Established:**
   - Evaluated the 5 requested geometries:
     1. Standard Mode-I edge-cracked plate (Sec. 4.1, Case 1).
     2. Mode-I plate with a hole.
     3. User's own off-axis-hole benchmark (Sec. 4.4 / User benchmark, Case 2).
     4. Plate containing three internal holes (two smaller, one larger) (Sec. 4.3, Case 3).
     5. Seven-hole plate (Sec. 4.6, Case 5).
   - De-duplicated items 2 & 3: confirmed they represent the **identical** finite-element benchmark (`models/mode1_off_axis_hole/` and `models/pandey_kumar_mode1/176_method_a_plate_with_hole/`, hole at $(0.65, 0.65), R=0.10\,\text{mm}$).
   - Reconciled item 4 as the authentic Section 4.3 pin-loaded rectangular plate ($65 \times 120\,\text{mm}$, two pin holes $R=4\,\text{mm}$, one central void $R=10\,\text{mm}$), distinct from the five-hole plate (Sec. 4.5).
   - Core regression suite established with **FOUR nonduplicated primary benchmarks**: BM-1 (Case 1), BM-2 (Case 2), BM-3 (Case 3), BM-4 (Case 5).
   - Case 4 (Five-Hole Plate) omitted from mandatory routine regression cycles per user directive, with its 12,625-element mesh and documented acceptance gate metrics fully preserved in historical records.
2. **Case 1 Distal Crack-Path Underresolution Root Cause Conclusively Diagnosed:**
   - Dissected why `f1728_case1_mode1_edge_crack.json` generated an adapted mesh with only localized crack-tip refinement (14,147 el, $h \le \ell_0 = 55.8\%$, distal ligament at coarse background size $h \approx 0.020\,\text{mm}$).
   - Physical cause: Linear elasticity produces singular stresses only at the static notch tip ($r \to 0$); by $x \ge 0.65\,\text{mm}$, stress gradients decay and `MISESERI` falls below the $1.85\%$ error target.
   - Contrast with Cases 4 & 5: Cases 4 & 5 solved coupled phase-field damage in `Step-2` and used `outputFrequency=ALL_INCREMENTS`. The temporal error envelope naturally refined the entire crack corridor as the process zone advanced.
   - Smallest shared-framework defect identified: Case 1 configuration erroneously specified a static continuum donor (`PK_MODE1_AUX_CONTINUUM.odb`, Step-1, `LAST_INCREMENT`) rather than an advancing coupled donor ODB with `ALL_INCREMENTS`.
3. **Rigorous Full-Suite Regression Protocol Defined:**
   - Any modification to `scripts/remeshing/reusable_2d_adaptive_framework.py` triggers mandatory execution and audit across ALL 4 primary benchmarks on HPC.
   - Regression gates G1–G8 predeclared across all 4 benchmarks.
   - Versioned side-by-side visual and numerical comparison generated per cycle.
4. **Governed Unit Testing & Zero-PBS Accounting:**
   - Authored and verified `tests/unit/test_f1766_suite_reconciliation_and_plan.py` (4/4 PASS in 0.30s).
   - Exactly 0 PBS jobs consumed under F1766 (historical total preserved at 27).
   - Bitwise frozen UEL `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) verified 100% bitwise invariant.

---

## 2. Reconciled Nonduplicated Benchmark Suite Matrix

| Suite ID | Geometry Description | Dimensions & Features | Literature Source | Geometry Adapter | Target Element Count | Predecessor Reference |
| :---: | :--- | :--- | :--- | :--- | :---: | :--- |
| **BM-1** | Mode-I Edge-Cracked Plate | $1.0 \times 1.0\,\text{mm}$, notch $a_0 = 0.5\,\text{mm}$, $y = 0.5\,\text{mm}$ | Pandey & Kumar (2025) Sec. 4.1 | `StraightNotchMode1Adapter` | 13,941 | F1738 (13,960 el, hybrid reference) / F1728 (14,147 el, localized) |
| **BM-2** | Plate with Off-Axis Hole | $1.0 \times 1.0\,\text{mm}$, notch $y=0.5\,\text{mm}$, hole $(0.65, 0.65), R=0.10\,\text{mm}$ | Task 176 / Pandey & Kumar Sec. 4.4 | `OffAxisHoleMode1Adapter` | 23,618 | F1734 / F1752 (23,965 el) |
| **BM-3** | Rectangular Notched Plate with Hole and Pins | $65 \times 120\,\text{mm}$, notch $a_0=20\,\text{mm}$, 2 pin holes $R=4\,\text{mm}$, 1 void $R=10\,\text{mm}$ | Pandey & Kumar (2025) Sec. 4.3 | `NotchedPlateWithPinHolesAdapter` | 12,168 | Baseline (12,110 el) / F1741 (28,933 el) |
| **BM-4** | Square Plate with Seven Holes | $1.0 \times 1.0\,\text{mm}$, 7 circular holes (Table 6), unnotched | Pandey & Kumar (2025) Sec. 4.6 | `SevenHolePlateAdapter` | 15,714 | F1726 (15,708 el) |
| *Omitted* | Square Plate with Five Holes | $1.0 \times 1.0\,\text{mm}$, 3 internal holes + 2 boundary cutouts | Pandey & Kumar (2025) Sec. 4.5 | `FiveHolePlateAdapter` | 12,944 | F1763 (12,625 el, verified pilot with preserved gates) |

---

## 3. Predeclared Suite-Wide Acceptance Gates (Gates G1–G8)

| Gate ID | Acceptance Dimension | BM-1 (Case 1) | BM-2 (Case 2) | BM-3 (Case 3) | BM-4 (Case 5) |
| :---: | :--- | :---: | :---: | :---: | :---: |
| **Gate G1** | Element Count Parity | $13,941 \pm 5.0\%$ ($[13,244 \dots 14,638]$) | $23,618 \pm 5.0\%$ ($[22,437 \dots 24,799]$) | $12,168 \pm 5.0\%$ ($[11,560 \dots 12,776]$) | $15,714 \pm 2.0\%$ ($[15,400 \dots 16,028]$) |
| **Gate G2** | Quad Element Fraction | $\ge 95.0\%$ CPE4 | $\ge 95.0\%$ CPE4 | $\ge 95.0\%$ CPE4 | $\ge 95.0\%$ CPE4 |
| **Gate G3** | Jacobian Determinant | $\min \det(J) > 0$ (100% pos) | $\min \det(J) > 0$ (100% pos) | $\min \det(J) > 0$ (100% pos) | $\min \det(J) > 0$ (100% pos) |
| **Gate G4** | Max Element Aspect Ratio | $\max AR \le 4.0$ (Mean $\le 1.5$) | $\max AR \le 4.0$ (Mean $\le 1.5$) | $\max AR \le 4.0$ (Mean $\le 1.5$) | $\max AR \le 4.0$ (Mean $\le 1.5$) |
| **Gate G5** | Primary Process Zone Resolution | $\ge 90.0\%$ area $h \le \ell_0 = 7.5\,\mu\text{m}$ along $x \in [0.5, 1.0]$ | $\ge 95.0\%$ area $h \le \ell_0 = 7.5\,\mu\text{m}$ along $x \in [0.5, 0.65]$ | $\ge 90.0\%$ area $h \le \ell_0 = 285\,\mu\text{m}$ in notch ligament | $\ge 95.0\%$ area $h \le \ell_0 = 8.0\,\mu\text{m}$ along upper ligament |
| **Gate G6** | Distal / Secondary Ligament Gate | Mean $h_{\text{distal}} \le 1.5\,\ell_0$ | Disclosed limitation (H1756) | Secondary hole bridge checked | Holes 6 & 7: $\ge 90.0\%$ count $h \le \ell_0$ |
| **Gate G7** | Far-Field Mesh Control | $h_{\text{bulk}} \ge 15\,\mu\text{m}$ (no runaway) | $h_{\text{bulk}} \ge 15\,\mu\text{m}$ | $h_{\text{bulk}} \ge 1.0\,\text{mm}$ | $h_{\text{bulk}} \ge 6.0\,\mu\text{m}$ |
| **Gate G8** | Automated 3-Layer UEL Deck | Complete Layer 3 SDV1/2, wrapped lines $\le 16$, cluster DC Exit 0 | Same | Same | Same |

---

## 4. Formal Review Authorization Request

Gemini Antigravity formally requests the independent scientific reviewer to evaluate:
1. **Approval of Technical Closeout of Task F1766:** Accept the 4-benchmark suite reconciliation, de-duplication, and Case 1 defect diagnosis under zero-PBS governance.
2. **Authorization of Successor Execution Task F1767:** Authorize registering Task F1767 for the implementation of the minimal Case 1 donor/configuration repair in `reusable_2d_adaptive_framework.py` and the subsequent bounded HPC batch execution of the complete 4-benchmark suite (`BM1_C1`, `BM2_C2`, `BM3_C3`, `BM4_C5`) with an explicit budget of 4 bounded PBS jobs (1 CPU, $\le 16\,\text{GB}$, $\le 30\,\text{min}$ walltime per job) on cluster compute nodes with zero forward fracture runs.

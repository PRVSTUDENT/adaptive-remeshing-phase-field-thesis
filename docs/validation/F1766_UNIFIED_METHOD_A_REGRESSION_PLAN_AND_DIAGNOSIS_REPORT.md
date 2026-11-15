# TASK F1766: UNIFIED METHOD A FRAMEWORK DEVELOPMENT WITH FULL BENCHMARK REGRESSION TESTING
## Benchmark Suite Reconciliation, Case 1 Defect Diagnosis, and Execution Plan

**Task ID:** `F1766-UNIFIED-METHOD-A-REGRESSION-PLAN-AND-DIAGNOSIS`  
**Governing Objective:** Master Objective `# F1737 — AUTONOMOUS FIVE-BENCHMARK METHOD A RESEARCH COMPLETION LOOP`  
**User Directive:** Authorize Python framework and script fixes while preserving frozen Fortran UEL (`CE8D5EDC...`), existing execution safety gates, and requiring full benchmark regression testing after every shared-framework modification.  
**Classification:** BENCHMARK_SUITE_RECONCILIATION_AND_REGRESSION_PLAN  
**PBS Submissions Consumed:** Exactly 0 (cumulative historical submissions preserved at 27)  
**Date:** 15 November 2026  

---

## 1. Executive Summary & Governance Boundaries

In response to the user's directive, Task F1766 establishes the formal benchmark suite reconciliation, diagnoses the root cause of Case 1 distal crack-path underresolution in native Abaqus Method A remeshing, and formulates an end-to-end regression plan.

### Core Governance Constraints
1. **Frozen Fortran UEL Invariant:** User subroutine `models/pandey_kumar_mode1/f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) remains strictly invariant. Zero modifications are permitted or performed.
2. **Single Shared Framework:** `scripts/remeshing/reusable_2d_adaptive_framework.py` serves as the authoritative, unified codebase across all benchmarks.
3. **Indicator-Driven Adaptivity Only:** Genuinely error-indicator-driven refinement is strictly enforced. Hand-crafted geometric partitioning corridors (such as the F1738 hybrid box) are disqualified from automated adaptivity.
4. **Full-Suite Regression Requirement:** Whenever a shared-framework modification is introduced, all benchmarks in the selected suite must undergo automated regeneration, FE quality verification, and regression evaluation. A local improvement in one benchmark cannot be accepted if it degrades another.
5. **Zero PBS Submissions in Planning Phase:** Exactly 0 PBS jobs are consumed in Task F1766 (historical total remains at 27). Batch execution on HPC compute nodes requires explicit subsequent authorization.

---

## 2. Benchmark Suite Reconciliation

The user requested mapping five descriptions to the existing authoritative configurations while checking for duplicates and preserving scientific distinctions.

### 2.1 Cross-Benchmark Mapping & De-duplication Analysis

| Item # | User Description | Repository Implementation & Literature Basis | Reconciled Status | Benchmark Identifier |
| :---: | :--- | :--- | :---: | :---: |
| **1** | Standard Mode-I edge-cracked plate | Pandey & Kumar (2025), Section 4.1. $1.0 \times 1.0\,\text{mm}$ square plate, horizontal notch $a_0 = 0.5\,\text{mm}$, $y = 0.5\,\text{mm}$. Adapter: `StraightNotchMode1Adapter`. | **PRIMARY BENCHMARK** | **BM-1 (Case 1)** |
| **2** | Mode-I plate with a hole | Often referred to in early literature as plate with a hole. In the thesis codebase, established in Task 176 (`176_method_a_plate_with_hole`) with hole at $(0.65, 0.65)$, $R = 0.10\,\text{mm}$. | **DUPLICATE OF ITEM 3** | **BM-2 (Case 2)** |
| **3** | User's own off-axis-hole benchmark | Defined in `configs/remeshing/mode1_off_axis_hole_benchmark.json` and `f1728_case2_off_axis_hole.json`. $1.0 \times 1.0\,\text{mm}$ plate, notch at $y=0.5\,\text{mm}$, circular hole at $(0.65, 0.65)$, $R = 0.10\,\text{mm}$. Adapter: `OffAxisHoleMode1Adapter`. | **PRIMARY BENCHMARK** (Unified with Item 2) | **BM-2 (Case 2)** |
| **4** | Plate containing three internal holes (two smaller, one larger), including correct boundary geometry | Pandey & Kumar (2025), Section 4.3 ("Rectangular Notched Plate with a Hole"). $65.0 \times 120.0\,\text{mm}$ plate with edge notch at $y = 70.0\,\text{mm}$ ($a_0 = 20.0\,\text{mm}$, width $0.4\,\text{mm}$), two pin holes ($R = 4.0\,\text{mm}$ at $(19, 20)$ and $(19, 100)$), and one central void ($R = 10.0\,\text{mm}$ at $(37, 52)$). Adapter: `NotchedPlateWithPinHolesAdapter`. | **PRIMARY BENCHMARK** | **BM-3 (Case 3)** |
| **5** | Seven-hole plate | Pandey & Kumar (2025), Section 4.6. $1.0 \times 1.0\,\text{mm}$ square plate without initial notch, containing seven circular holes (Table 6). Adapter: `SevenHolePlateAdapter`. | **PRIMARY BENCHMARK** | **BM-4 (Case 5)** |
| *Omitted/Preserved* | Five-hole plate (three internal holes plus two edge cutouts) | Pandey & Kumar (2025), Section 4.5. $1.0 \times 1.0\,\text{mm}$ plate with 3 internal holes and 2 boundary circular cutouts. Adapter: `FiveHolePlateAdapter`. | **PRESERVED HISTORICAL** (Omitted from core suite per user directive) | **Case 4** |

### 2.2 Findings of the Reconciliation Audit
1. **Items 2 and 3 are Identical:** In the thesis codebase, "Mode-I plate with a hole" and "off-axis-hole benchmark" refer to the exact same finite-element model (`models/mode1_off_axis_hole/` and `models/pandey_kumar_mode1/176_method_a_plate_with_hole/`). There is no separate centered-hole benchmark in the repository. Treating them as distinct would introduce artificial duplication.
2. **Item 4 is the Section 4.3 Pin-Loaded Plate:** The description "three internal holes (two smaller, one larger)" uniquely characterizes Section 4.3: the two $\varnothing 8\,\text{mm}$ pin holes and the single $\varnothing 20\,\text{mm}$ central void. This is distinct from the Section 4.5 five-hole plate (which has two boundary cutouts).
3. **Core Regression Suite Size is FOUR Benchmarks:** The nonduplicated core regression suite consists of:
   - **BM-1 (Case 1):** Mode-I Edge-Cracked Plate (Sec. 4.1).
   - **BM-2 (Case 2):** Mode-I Plate with Off-Axis Hole (User Benchmark).
   - **BM-3 (Case 3):** Rectangular Notched Plate with Hole and Pins (Sec. 4.3).
   - **BM-4 (Case 5):** Seven-Hole Plate (Sec. 4.6).
4. **Preservation of Case 4:** As explicitly authorized by the user, Case 4 is omitted from mandatory routine regression cycles to eliminate redundancy, while its historical 12,625-element mesh and documented acceptance gate metrics from Task F1763 are fully preserved in `configs/remeshing/canonical_five_case_manifest.json` and `docs/validation/F1763_CASE4_PILOT_EXECUTION_REPORT.md`.

---

## 3. Root-Cause Diagnosis: Case 1 Distal Crack-Path Refinement

### 3.1 The Physical and Numerical Mechanism of the Defect
In Task F1736 and previous audits, Case 1 generated an adapted mesh with 14,147 elements that exhibited a localized circular refinement cloud around the notch tip $(0.5, 0.5)$, but left the distal ligament ($x \in [0.65, 1.0], y = 0.5$) at the coarse background element size ($h \approx 0.020\,\text{mm} > 2.6\,\ell_0$).

Why did this occur?
1. **Static Elastic Asymptotics:** In linear elasticity without damage, the stress field ahead of a crack tip follows the Williams expansion:
   $$\sigma_{yy}(r, \theta=0) = \frac{K_I}{\sqrt{2\pi r}} + O(r^{1/2})$$
   The stress gradient decays as $r^{-3/2}$. Consequently, the Zienkiewicz–Zhu error indicator `MISESERI` ($e = \|\boldsymbol{\sigma}^* - \boldsymbol{\sigma}_h\|$) is concentrated in a tight radius $r \le 0.10\,\text{mm}$ around $(0.5, 0.5)$.
2. **Donor Configuration Mismatch:** In `configs/remeshing/f1728_case1_mode1_edge_crack.json`, the donor was configured as:
   - `donor_odb_repo_path`: `models/pandey_kumar_mode1/01_standard_pfm_reference/PK_MODE1_AUX_CONTINUUM.odb`
   - `step_name`: `Step-1`
   - `output_frequency`: `LAST_INCREMENT`
   This donor evaluated only a single static elastic frame where the crack had not advanced. For elements at $x \ge 0.65\,\text{mm}$, `MISESERI` falls well below the `errorTarget` ($1.85\%$). Abaqus `RemeshingRule` therefore assigned $h_{\text{new}} = h_{\max} = 0.020\,\text{mm}$.
3. **Contrast with Successful Cases 4 and 5:**
   In Cases 4 and 5:
   - The donor ODBs (`PK_F1720_COARSE_COUPLED.odb` and `PK_F1726_SEVEN_HOLE_COARSE.odb`) were **coupled phase-field simulations** that solved through damage softening and crack advance in `Step-2`.
   - The remeshing rule used `outputFrequency=ALL_INCREMENTS`.
   - Abaqus evaluates the error indicator across all frames: as the crack propagates, each point along the ligament experiences high stress and peak `MISESERI` when the process zone passes. The maximum error envelope over time naturally refines the entire crack corridor!

### 3.2 The Smallest Shared-Framework Defect
The shared framework `reusable_2d_adaptive_framework.py` contains the logic:
```python
out_freq_opt = ALL_INCREMENTS if getattr(config, "output_frequency", "ALL_INCREMENTS") == "ALL_INCREMENTS" else LAST_INCREMENT
```
The framework is fully capable of multi-increment envelope adaptivity. However, for Case 1:
1. `f1728_case1_mode1_edge_crack.json` erroneously pointed to a static continuum donor (`PK_MODE1_AUX_CONTINUUM.odb`) with `LAST_INCREMENT`.
2. To achieve automatic, indicator-driven distal ligament refinement without manual geometric corridors (avoiding the F1738 hybrid hack), Case 1 requires an authentic coarse coupled donor ODB (`PK_PREANALYSIS_COARSE.odb` or equivalent `Job-1_UEL`) with `outputFrequency=ALL_INCREMENTS` across Step-2 crack propagation.

---

## 4. Full-Suite Regression Execution Plan

### 4.1 Regression Cycle Workflow
Whenever a modification is made to `scripts/remeshing/reusable_2d_adaptive_framework.py`:
```text
Step 1: Local Preflight & Unit Testing (tests/unit/test_f1766_suite_reconciliation_and_plan.py)
Step 2: Authenticated Independent Review Dispatch & Approval
Step 3: HPC Execution of Complete Reconciled Suite (BM-1, BM-2, BM-3, BM-4)
Step 4: Automated Extraction & Finite-Element Quality Audit (det(J) > 0, aspect ratio, h/l0)
Step 5: Comparative Evaluation against Prior Iteration (IMPROVED / UNCHANGED / REGRESSED / FAILED)
Step 6: Versioned Visual Synthesis Figure & Git Synchronization
```

### 4.2 Predeclared Acceptance Gate Matrix across Selected Suite

| Benchmark ID | Geometry | Published Target Elements | Allowable Parity ($\pm 5\%$) | Minimum Quad Fraction | Min Signed $\det(J)$ | Max Aspect Ratio | Critical Ligament Process Zone Gate |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **BM-1 (Case 1)** | Straight Notch ($1\times 1\,\text{mm}$) | 13,941 | $[13,244 \dots 14,638]$ | $\ge 95.0\%$ | $> 0$ (100% pos) | $\le 4.0$ | Ligament $x \in [0.5, 1.0], y = 0.5$: $\ge 90.0\%$ area with $h \le \ell_0 = 7.5\,\mu\text{m}$ |
| **BM-2 (Case 2)** | Off-Axis Hole ($1\times 1\,\text{mm}$) | 23,618 | $[22,437 \dots 24,799]$ | $\ge 95.0\%$ | $> 0$ (100% pos) | $\le 4.0$ | Primary ligament $x \in [0.5, 0.65]$: $\ge 95.0\%$ area with $h \le \ell_0 = 7.5\,\mu\text{m}$ |
| **BM-3 (Case 3)** | Notched Plate w/ Pins ($65\times 120\,\text{mm}$) | 12,168 | $[11,560 \dots 12,776]$ | $\ge 95.0\%$ | $> 0$ (100% pos) | $\le 4.0$ | Notch-to-hole ligament: $\ge 90.0\%$ area with $h \le \ell_0 = 285\,\mu\text{m}$ |
| **BM-4 (Case 5)** | Seven-Hole Plate ($1\times 1\,\text{mm}$) | 15,714 | $[15,400 \dots 16,028]$ | $\ge 95.0\%$ | $> 0$ (100% pos) | $\le 4.0$ | Upper ligament ($h_1 \to h_4 \to h_2 \to h_5 \to h_3$): $\ge 95.0\%$ area with $h \le \ell_0 = 8.0\,\mu\text{m}$ |

### 4.3 Resource Allocation & Budget
- **Current Planning Turn (F1766):** Exactly 0 PBS submissions.
- **Prospective HPC Regression Turn (F1767):** Exactly 4 bounded PBS jobs (one headless Abaqus/CAE remeshing job per core benchmark: `BM1_C1`, `BM2_C2`, `BM3_C3`, `BM4_C5`), running in 1-CPU serial mode, $\le 16\,\text{GB}$ RAM, $\le 30\,\text{min}$ walltime per job.

---

## 5. Summary of Deliverables & Next Actions

1. **Unit Test Suite:** Authored `tests/unit/test_f1766_suite_reconciliation_and_plan.py` (4/4 tests PASS in 0.30s).
2. **Specification Report:** This document (`docs/validation/F1766_UNIFIED_METHOD_A_REGRESSION_PLAN_AND_DIAGNOSIS_REPORT.md`).
3. **Review Dispatch Staging:** Authored review payload `HND-F1766-SUITE-PLAN-AUTH-001_payload.md` for ChatGPT independent review dispatcher across the OpenClaw PAD bridge.
4. **Git Sync:** Governed changes committed and pushed forward to GitHub `origin/main`.

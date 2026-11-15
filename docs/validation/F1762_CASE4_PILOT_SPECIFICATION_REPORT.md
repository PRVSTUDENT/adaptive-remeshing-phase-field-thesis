# Task F1762 Scientific Report: Case 4 Common-Framework Single-Pass Adaptive Remeshing Pilot Specification & Pre-Execution Verification

**Task ID:** `F1762-CASE4-COMMON-FRAMEWORK-PILOT-SPECIFICATION`  
**Classification:** `PILOT_SPECIFICATION_ZERO_PBS`  
**Predecessor Task:** `F1761-UNIFIED-METHOD-A-RECONCILED-EXECUTION-MANIFEST` (`HND-F1761-RECONCILED-MANIFEST-001`)  
**Assigned Agent:** `gemini-antigravity`  
**Source Commit SHA:** [`a45c5f20`](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/commit/a45c5f20) (Pushed to GitHub `origin/main`)  
**Frozen UEL SHA-256:** `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (`f42_mixed_uel.for`)  
**PBS Allocation Consumed:** Exactly 0 PBS jobs (Cumulative project submissions strictly preserved at 26)  

---

## 1. Executive Summary & Purpose

In response to independent scientific review `HND-F1761-RECONCILED-MANIFEST-001`, Task F1762 delivers a rigorous, pre-execution verified specification for **ONE bounded Case 4 (Five-Hole Plate, Section 4.5) adaptive-remeshing pilot** under the unified reusable framework (`scripts/remeshing/reusable_2d_adaptive_framework.py`).

All five blocking review findings (**F1761-R01** through **F1761-R05**) have been resolved in the codebase, verified with unit tests, committed, and pushed to GitHub `origin/main` at commit `a45c5f20`. This report details the empirical Abaqus 2023 frame selection mechanism, UEL configuration re-alignment, canonical manifest structure, and exact pilot acceptance criteria.

---

## 2. Direct Resolution of Reviewer Findings (HND-F1761-RECONCILED-MANIFEST-001)

### Finding F1761-R01 (Abaqus 2023 Remeshing Frame Selection Mechanism):
- **Abaqus CAE 2023 Native API Architecture:** Direct empirical inspection of Abaqus CAE 2023 on the HPC cluster (`models/pandey_kumar_mode1/remeshing_rule_defaults.txt`) confirmed that `m.RemeshingRule` and `m.adaptiveRemesh(odb=odb)` do **not** accept a numerical `frameIndex` argument.
- **Authentic Governing Parameters:** Frame selection in Abaqus CAE is governed by the pair `(stepName, outputFrequency)`:
  - `outputFrequency = LAST_INCREMENT` (Abaqus default): Evaluates error indicator fields exclusively at the **last increment** (terminal frame) of `stepName`.
  - `outputFrequency = ALL_INCREMENTS`: Evaluates error indicator fields across **all increments** of `stepName` and computes an envelope satisfying the error target over the entire step.
- **Case 4 Exact Historical Alignment:** In `scripts/remeshing/run_f1725_physics_study.py` (which produced the authentic 13,017-element Case 4 mesh), `outputFrequency = ALL_INCREMENTS` was explicitly used with `stepName = 'Step-2'`. Because coupled damage and stress concentration grew monotonically up to terminal Frame 178 ($u_y = 0.00645141\,\text{mm}$, increment 356, $d_{\max}=0.5252$), the all-increments envelope is governed by the terminal fracture state.
- **Implementation Update:** `scripts/remeshing/reusable_2d_adaptive_framework.py` lines 155 and 1328–1344 now parse `output_frequency` from config and pass `outputFrequency` explicitly to `m.RemeshingRule(...)`.

### Finding F1761-R02 (Case 4 UEL Configuration Reconciliation):
- **Defect Identified:** `configs/remeshing/f1728_case4_five_hole.json` previously referenced historical subroutine `models/pandey_kumar_mode1/f42_amor_split_uel_v2.for` and hash `91612E94...`.
- **Resolution Applied:** Updated `deck_options.uel_subroutine` to `models/pandey_kumar_mode1/f42_mixed_uel.for` and `frozen_uel_sha256` to `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`.
- **Consistency Audit:** 100% of the five benchmark configurations under `configs/remeshing/` now strictly enforce the bitwise frozen production UEL. Neither Fortran source file was altered.

### Finding F1761-R03 (Canonical Machine-Readable Manifest):
- **Defect Identified:** Previous narrative reports had conflicting donor paths between sections (e.g. `PK_MODE1_AUX_CONTINUUM.odb` vs `PK_F1713_JOB1_COARSE.odb`).
- **Resolution Applied:** Created and published [`configs/remeshing/canonical_five_case_manifest.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/configs/remeshing/canonical_five_case_manifest.json) (SHA-256 `230BB7FFECACF35D8CE25685F7D32CB4AE032E074171C93E2CFA087B50D922F1`).
- **Unambiguous Mapping:** Every benchmark case has exactly one declared cluster path, repo path, step name, frame selection mechanism, error target, and sizing limit.

### Findings F1761-R04 & F1761-R05 (Pilot Acceptance Gates & Method A.1 Scoping):
- Instance-name matching and element-label correspondence are retained as **empirical pilot acceptance checks** rather than pre-claimed guarantees.
- The Case 4 pilot qualifies baseline single-pass **Method A.1** only. Multi-state sequential adaptivity remains isolated as **Method A.2** (Case 3).

---

## 3. Case 4 Single-Pass Pilot Execution Specification

| Parameter | Governing Value / Reference | Provenance Basis |
| :--- | :--- | :--- |
| **Benchmark Problem** | Square Plate with Five Holes (Pandey & Kumar 2025, Section 4.5) | Benchmark geometry with 3 internal holes and 2 edge cutouts |
| **Algorithm Variant** | **Method A.1 (Single-Pass Native Method A)** | Single donor, single `RemeshingRule`, single `adaptiveRemesh()` |
| **Master Driver Script** | `scripts/remeshing/reusable_2d_adaptive_framework.py` | Commit `a45c5f20`, lines 1280–1365 |
| **Configuration File** | `configs/remeshing/f1728_case4_five_hole.json` | Reconciled at commit `a45c5f20` |
| **Donor ODB Path** | `models/pandey_kumar_mode1/213_f1720_coarse_coupled/PK_F1720_COARSE_COUPLED.odb` | Authentic coupled coarse simulation ODB |
| **Donor Step & Selection** | `stepName = 'Step-2'`, `outputFrequency = ALL_INCREMENTS` | Evaluates envelope through terminal Frame 178 ($u_y = 0.00645\,\text{mm}$) |
| **Target Error Indicator** | `variables = ('MISESERI',)`, `sizingMethod = UNIFORM_ERROR` | Error target $\eta = 3.15\%$ |
| **Element Sizing Bounds** | $h_{\min} = 0.0010\,\text{mm}$, $h_{\max} = 0.0300\,\text{mm}$ | Coarsening option: `DEFAULT_LIMIT`; Refinement factor: 10 |
| **Execution Command** | `abaqus cae noGUI="scripts/remeshing/reusable_2d_adaptive_framework.py" -- --config "configs/remeshing/f1728_case4_five_hole.json" --run-case --odb "<donor_odb_path>" --output-dir "runs/f1762_case4_pilot"` | Headless Abaqus CAE execution on HPC cluster |
| **Expected Output Mesh** | `runs/f1762_case4_pilot/PK_ADAPT_CASE_4_PHYS.inp` | Physical 2D mesh input deck |

---

## 4. Quantitative Pilot Acceptance Criteria

1. **Element Count Parity:**
   - Published literature benchmark (Pandey & Kumar 2025, Fig. 22a/25a): **12,944 elements**.
   - Historical executed sweep baseline (`F1725_S2_COARSEN_ET315.inp`): **13,017 elements** ($+0.56\%$).
   - Acceptance Band: **$12,944 \pm 2.0\%$** ($[12,685, 13,203]$ physical elements).
2. **Element Topology & Distortion:**
   - Quad-dominated percentage: $\ge 95.0\%$ quads (historical: $97.53\%$).
   - Positive Jacobians: **$100.0\%$ positive Jacobians** across all elements (zero negative or inverted Jacobians).
   - Maximum aspect ratio: $\le 4.0$ (historical: $3.24$).
3. **Physical Process-Zone Resolution:**
   - Active multi-void ligament corridor (Ligaments 2, 3, and 4): **$\ge 95.0\%$ of area compliant with $h \le \ell_0 = 8.0\,\mu\text{m}$** (historical: $100.0\%$).
   - Ligament 3 (critical narrowest bridge, $w = 0.05\,\text{mm}$): **$100.0\%$ compliant with $h \le \ell_0/2 = 4.0\,\mu\text{m}$**.
   - Far-field background plate: Preserves coarse elements ($h > 15.0\,\mu\text{m}$) without unconstrained global mesh explosion.

---

## 5. Verification Receipts & Regression Evidence

1. **Unit Test Verification:**
   - Suite [`tests/unit/test_f1761_reconciled_manifest.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_f1761_reconciled_manifest.py): **9/9 PASSED in 0.38s**.
   - Suite [`tests/unit/test_f1760_framework_provenance_and_unification.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_f1760_framework_provenance_and_unification.py): **5/5 PASSED in 0.37s**.
   - Combined pre-execution suite: **14/14 tests passing cleanly (100% in 0.58s)**.
2. **Canonical Manifest Hash:**
   - `configs/remeshing/canonical_five_case_manifest.json`: SHA-256 `230BB7FFECACF35D8CE25685F7D32CB4AE032E074171C93E2CFA087B50D922F1`.
3. **Commit-Pinned GitHub Links:**
   - Framework module: [reusable_2d_adaptive_framework.py @ a45c5f20](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/a45c5f20/scripts/remeshing/reusable_2d_adaptive_framework.py)
   - Case 4 configuration: [f1728_case4_five_hole.json @ a45c5f20](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/a45c5f20/configs/remeshing/f1728_case4_five_hole.json)
   - Canonical manifest: [canonical_five_case_manifest.json @ a45c5f20](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/a45c5f20/configs/remeshing/canonical_five_case_manifest.json)
   - Reconciled manifest report: [F1761_UNIFIED_METHOD_A_RECONCILED_EXECUTION_MANIFEST.md @ a45c5f20](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/a45c5f20/docs/validation/F1761_UNIFIED_METHOD_A_RECONCILED_EXECUTION_MANIFEST.md)
   - Reconciled manifest unit test: [test_f1761_reconciled_manifest.py @ a45c5f20](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/a45c5f20/tests/unit/test_f1761_reconciled_manifest.py)

---

## 6. Scope Boundaries & Governance Safeguards

- **Zero PBS Production Jobs:** Exactly 0 PBS solver jobs consumed. The cumulative submission counter remains permanently at 26.
- **Pilot Execution Boundary:** Execution is strictly limited to 1 bounded headless Abaqus CAE mesh-generation pass on the cluster compute/login node to verify that `execute_native_remesh` reproduces the physical mesh.
- **Forward Fracture Decoupled:** Forward coupled phase-field fracture simulation on the resulting mesh is explicitly decoupled from this pilot and will require a separate preflight qualification and review packet.
- **No UEL Modification:** Bitwise frozen production UEL `f42_mixed_uel.for` (`CE8D5EDC...`) is strictly preserved.

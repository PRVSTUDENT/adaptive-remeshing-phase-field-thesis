# Task F1762 Evidence Payload: Case 4 Common-Framework Adaptive Remeshing Pilot Specification & Pre-Execution Verification

**Correlation ID:** `HND-F1762-CASE4-PILOT-AUTH-001`  
**Predecessor Correlation ID:** `HND-F1761-RECONCILED-MANIFEST-001`  
**Task ID:** `F1762-CASE4-COMMON-FRAMEWORK-PILOT-SPECIFICATION`  
**Commit SHA:** `a45c5f20` (Committed and pushed to GitHub `origin/main`)  
**Timestamp:** `2026-11-15T07:33:00+01:00`  
**Author:** `gemini-antigravity`  
**Scope Boundary:** `PILOT_SPECIFICATION_ZERO_PBS` (Pilot Specification & Offline Verification Only; Zero PBS Submissions [Cumulative Preserved = 26]; Bitwise Frozen UEL Preserved)

---

## 1. Direct Resolution of Reviewer Directives (HND-F1761-RECONCILED-MANIFEST-001)

In `HND-F1761-RECONCILED-MANIFEST-001`, the independent reviewer mandated resolving five specific source and configuration blockers prior to Case 4 pilot authorization:

1. **Finding F1761-R01 (Abaqus 2023 Remeshing Frame Selection Mechanism):**
   - **Empirical Abaqus API Architecture:** Direct empirical inspection on the HPC cluster (`models/pandey_kumar_mode1/remeshing_rule_defaults.txt`) confirmed that `m.RemeshingRule` and `m.adaptiveRemesh` do **not** take a numerical `frameIndex` argument.
   - **Governing Mechanism:** Frame selection in Abaqus CAE is governed by `stepName` and `outputFrequency`:
     - `outputFrequency = LAST_INCREMENT` (default): Evaluates error indicator fields exclusively at the **last increment** (terminal frame) of `stepName`.
     - `outputFrequency = ALL_INCREMENTS`: Evaluates error indicator fields across **all increments** of `stepName` and computes an envelope satisfying the error target over the entire step.
   - **Case 4 Exact Historical Alignment:** In `scripts/remeshing/run_f1725_physics_study.py` (which produced the authentic 13,017-element mesh), `outputFrequency = ALL_INCREMENTS` was explicitly used with `stepName = 'Step-2'`. Because coupled damage and stress concentration grew monotonically up to terminal Frame 178 ($u_y = 0.00645141\,\text{mm}$, increment 356, $d_{\max}=0.5252$), the all-increments envelope is governed by the terminal fracture state.
   - **Implementation Update:** `scripts/remeshing/reusable_2d_adaptive_framework.py` lines 155 and 1328–1344 now parse `output_frequency` from config and pass `outputFrequency` explicitly to `m.RemeshingRule(...)`.

2. **Finding F1761-R02 (Case 4 UEL Configuration Reconciliation):**
   - **Correction Applied:** In `configs/remeshing/f1728_case4_five_hole.json`, replaced `f42_amor_split_uel_v2.for` (`91612E94...`) with authorized production UEL `models/pandey_kumar_mode1/f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`).
   - **Consistency:** 100% of the five benchmark configurations now strictly enforce the bitwise frozen production UEL. Neither Fortran source file was altered.

3. **Finding F1761-R03 (Canonical Machine-Readable Manifest):**
   - Published [`configs/remeshing/canonical_five_case_manifest.json`](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/a45c5f20/configs/remeshing/canonical_five_case_manifest.json) (SHA-256 `230BB7FFECACF35D8CE25685F7D32CB4AE032E074171C93E2CFA087B50D922F1`).
   - Completely eliminated conflicting donor specifications across reports, establishing exact cluster paths, steps, frames, selection mechanisms, and error targets for all five cases.

4. **Findings F1761-R04 & F1761-R05 (Empirical Pilot Acceptance & Method A.1 Scoping):**
   - Instance-name matching and element-label correspondence are retained as empirical pilot acceptance checks.
   - Formally scoped the Case 4 pilot to qualify baseline single-pass **Method A.1** only. Sequential multi-pass adaptivity remains classified as **Method A.2** (Case 3).

---

## 2. Case 4 Single-Pass Pilot Execution Specification

- **Benchmark Problem:** Square Plate with Five Holes (Pandey & Kumar 2025, Section 4.5).
- **Algorithm Variant:** **Method A.1 (Single-Pass Native Method A)**.
- **Master Script:** `scripts/remeshing/reusable_2d_adaptive_framework.py` (HEAD blob at commit `a45c5f20`).
- **Configuration File:** `configs/remeshing/f1728_case4_five_hole.json` (SHA-256 `C1BF9763...`).
- **Donor ODB Path:** `models/pandey_kumar_mode1/213_f1720_coarse_coupled/PK_F1720_COARSE_COUPLED.odb` (Step-2, Frame 178, $u_y = 0.00645141\,\text{mm}$, terminal increment 356, max damage $d = 0.5252$).
- **Remeshing Rule:** `variables = ('MISESERI',)`, `sizingMethod = UNIFORM_ERROR`, $\eta = 3.15\%$, $h \in [0.0010, 0.0300]\,\text{mm}$, `coarseningFactor = DEFAULT_LIMIT`, `refinementFactor = 10`, `outputFrequency = ALL_INCREMENTS`.
- **Execution Command:**  
  `abaqus cae noGUI="scripts/remeshing/reusable_2d_adaptive_framework.py" -- --config "configs/remeshing/f1728_case4_five_hole.json" --run-case --odb "<donor_odb_path>" --output-dir "runs/f1762_case4_pilot"`
- **Expected Output Mesh:** `runs/f1762_case4_pilot/PK_ADAPT_CASE_4_PHYS.inp`.

---

## 3. Quantitative Pilot Acceptance Criteria

1. **Element Count Parity:**
   - Published literature benchmark (Pandey & Kumar 2025, Fig. 22a/25a): **12,944 elements**.
   - Historical executed sweep baseline (`F1725_S2_COARSEN_ET315.inp`): **13,017 elements** ($+0.56\%$).
   - Acceptance Band: **$12,944 \pm 2.0\%$** ($[12,685, 13,203]$ physical elements).
2. **Element Topology & Distortion:**
   - Quad-dominated percentage: $\ge 95.0\%$ quads.
   - Positive Jacobians: **$100.0\%$ positive Jacobians** across all elements (zero negative or inverted Jacobians).
   - Maximum aspect ratio: $\le 4.0$.
3. **Physical Process-Zone Resolution:**
   - Active multi-void ligament corridor (Ligaments 2, 3, and 4): **$\ge 95.0\%$ of area compliant with $h \le \ell_0 = 8.0\,\mu\text{m}$**.
   - Ligament 3 (critical narrowest bridge, $w = 0.05\,\text{mm}$): **$100.0\%$ compliant with $h \le \ell_0/2 = 4.0\,\mu\text{m}$**.
   - Far-field background plate: Preserves coarse elements ($h > 15.0\,\mu\text{m}$) without unconstrained global mesh explosion.

---

## 4. Verification Receipts & Regression Evidence

1. **Unit Test Verification:**
   - Suite `tests/unit/test_f1762_case4_pilot_specification.py`: **5/5 PASSED in 0.34s**.
   - Suite `tests/unit/test_f1761_reconciled_manifest.py`: **9/9 PASSED in 0.38s**.
   - Suite `tests/unit/test_f1760_framework_provenance_and_unification.py`: **5/5 PASSED in 0.37s**.
   - Combined pre-execution suite: **19/19 tests passing cleanly (100% in 0.83s)**.
2. **Canonical Manifest Hash:**
   - `configs/remeshing/canonical_five_case_manifest.json`: SHA-256 `230BB7FFECACF35D8CE25685F7D32CB4AE032E074171C93E2CFA087B50D922F1`.
3. **Commit-Pinned GitHub Links:**
   - Framework module: [reusable_2d_adaptive_framework.py @ a45c5f20](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/a45c5f20/scripts/remeshing/reusable_2d_adaptive_framework.py)
   - Case 4 configuration: [f1728_case4_five_hole.json @ a45c5f20](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/a45c5f20/configs/remeshing/f1728_case4_five_hole.json)
   - Canonical manifest: [canonical_five_case_manifest.json @ a45c5f20](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/a45c5f20/configs/remeshing/canonical_five_case_manifest.json)
   - Pilot specification report: [F1762_CASE4_PILOT_SPECIFICATION_REPORT.md @ a45c5f20](https://github.com/PRVSTUDENT/adaptive-remeshing-phase-field-thesis/blob/a45c5f20/docs/validation/F1762_CASE4_PILOT_SPECIFICATION_REPORT.md)

---

## 5. Scope Boundaries & Governance Safeguards

- **Zero PBS Production Jobs:** Exactly 0 PBS solver jobs consumed. The cumulative submission counter remains permanently at 26.
- **Pilot Execution Boundary:** Execution is strictly limited to 1 bounded headless Abaqus CAE mesh-generation pass on the cluster compute/login node to verify that `execute_native_remesh` reproduces the physical mesh.
- **Forward Fracture Decoupled:** Forward coupled phase-field fracture simulation on the resulting mesh is explicitly decoupled from this pilot and will require a separate preflight qualification and review packet.
- **No UEL Modification:** Bitwise frozen production UEL `f42_mixed_uel.for` (`CE8D5EDC...`) is strictly preserved.

---

## 6. Specific Review Decisions Requested from ChatGPT

1. Does the independent reviewer approve the **Task F1762 Case 4 Pilot Execution Specification** and accept the complete resolution of findings F1761-R01 through F1761-R05?
2. Does the reviewer authorize proceeding with **ONE bounded Case 4 headless mesh-generation pilot** under `reusable_2d_adaptive_framework.py` on the HPC cluster (zero PBS fracture jobs) to empirically verify physical mesh generation and quality criteria?

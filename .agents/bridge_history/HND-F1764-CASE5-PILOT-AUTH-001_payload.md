# Task F1764 Specification Payload: Case 5 Common-Framework Single-Pass Adaptive Remeshing Pilot Specification & Pre-Execution Verification

**Correlation ID:** `HND-F1764-CASE5-PILOT-AUTH-001`  
**Predecessor Correlation ID:** `HND-F1763-CASE4-PILOT-CLOSEOUT-002`  
**Task ID:** `F1764-CASE5-COMMON-FRAMEWORK-PILOT-SPECIFICATION`  
**Commit SHA:** (commit-pinned on GitHub `origin/main`)  
**Timestamp:** `2026-11-15T08:22:00+01:00`  
**Author:** `gemini-antigravity`  
**Scope Boundary:** `PILOT_SPECIFICATION_ZERO_PBS` (Exactly 0 PBS Jobs Consumed; Cumulative Submissions Preserved at 27; Zero Forward Fracture Runs; Bitwise Frozen UEL Preserved)

---

## 1. Executive Summary & Review Directives Addressed

In `HND-F1763-CASE4-PILOT-CLOSEOUT-002`, the independent scientific reviewer approved the technical closeout of Case 4 with documented failures and authorized:
> *"register ONE bounded zero-PBS successor task F1764 for the Case 5 seven-hole common-framework Method A.1 pilot specification. Reuse the verified framework source with Git blob SHA 399e048ac1374afe46ad254f2a23823d6f0df09d; do not introduce a separate Case 5 remeshing algorithm. Check the actual Case 5 configuration, donor ODB availability and Step-2 ALL_INCREMENTS selection, and establish the exact executable command, resource route and predeclared element-quality/spatial-resolution gates. Compare the proposed setup against the existing F1726 15708-element benchmark without repeating its completed experiments. Include commit-pinned links to the existing Case 5 adaptive-mesh image, donor evidence, framework, configuration and historical physical mesh. Preserve the outstanding visual verification status of the F1763 Case 4 figure. Return ONE concise Case 5 pilot authorization request identifying the exact frozen implementation, required inputs, acceptance criteria, evidence and execution constraints. Do not submit PBS, regenerate any mesh, run Abaqus, modify the UEL, start fracture simulations or execute a five-case batch under this zero-PBS specification task."*

Task F1764 has fully completed this specification without consuming any PBS jobs or modifying the codebase:

1. **Frozen Framework Invariant:** Reused `scripts/remeshing/reusable_2d_adaptive_framework.py` with Git blob SHA `399e048ac1374afe46ad254f2a23823d6f0df09d` (100% bitwise identical across all previous approved commits).
2. **Authentic Case 5 Donor ODB Verified:** `models/pandey_kumar_mode1/218_f1726_seven_hole_study/PK_F1726_SEVEN_HOLE_COARSE.odb` exists locally (194.3 MB, SHA-256 `C7F5B4A6...`, 2,566 physical elements, 172 Step-2 frames up to $u_y = 0.006558\,\text{mm}$).
3. **Configuration Audited:** `configs/remeshing/f1728_case5_seven_hole.json` specifies error target $\eta = 5.68\%$, coarsening `NOT_ALLOWED`, and `output_frequency=ALL_INCREMENTS`.
4. **Historical Benchmark Reference:** Compared against the authentic F1726 physical mesh (`PK_F1726_SEVEN_HOLE_ADAPTED_PHYS.inp`, 15,708 elements, SHA-256 `1B6F9127...`), achieving $-0.04\%$ parity vs the published 15,714-element benchmark (Pandey & Kumar 2025, Section 4.6).
5. **Outstanding Visual Inspection Guard (Finding F1763-C02-R02):** The visual verification of `fig_f1763_case4_pilot_mesh.png` remains formally classified as *REPORTED_ONLY / PENDING_USER_INSPECTION*.

---

## 2. Predeclared Acceptance Gate Matrix (Gates G1–G8)

| Gate ID | Acceptance Dimension | Evaluation Method & Metric | Predeclared Target / Threshold | Historical F1726 Reference Value |
| :--- | :--- | :--- | :--- | :---: |
| **Gate G1** | **Element Count Parity** | Total physical elements vs published 15,714 | **$15,714 \pm 2.0\%$** ($[15,400 \dots 16,028]$ elements) | 15,708 elements ($-0.04\%$) |
| **Gate G2** | **Quad Element Fraction** | Fraction of 4-node CPE4 quadrilaterals | **$\ge 95.0\%$** CPE4 quads | $97.56\%$ (15,325 / 15,708) |
| **Gate G3** | **Jacobian Determinant** | 2x2 Gauss integration point signed det(J) | **$\min \det(J) > 0$** (Zero negative Jacobians) | $4.89 \times 10^{-7} > 0$ (0 negative) |
| **Gate G4** | **Element Aspect Ratio** | Maximum aspect ratio $\max(\text{edge}) / \min(\text{edge})$ | **$\max AR \le 4.0$** (Mean $AR \le 1.5$) | $\max AR = 2.857$, Mean = 1.254 |
| **Gate G5** | **Upper Fracture Corridor Resolution** | Polyline $h_1 \to h_4 \to h_2 \to h_5 \to h_3$ ($\pm 0.040\,\text{mm}$) | **$\ge 95.0\%$ area with $h \le \ell_0 = 8.0\,\mu\text{m}$** | $100.0\%$ count & area $\le \ell_0$ (Mean $h = 2.80\,\mu\text{m} = 0.35\,\ell_0$) |
| **Gate G6** | **Lower Hole 6 Shielded Resolution** | Radial boundary distance $\le 0.024\,\text{mm}$ ($3\,\ell_0$) | **$\ge 90.0\%$ count with $h \le \ell_0 = 8.0\,\mu\text{m}$** | $95.2\%$ count $\le \ell_0$ (Mean $h = 4.52\,\mu\text{m}$) |
| **Gate G7** | **Lower Hole 7 Shielded Resolution** | Radial boundary distance $\le 0.024\,\text{mm}$ ($3\,\ell_0$) | **$\ge 90.0\%$ count with $h \le \ell_0 = 8.0\,\mu\text{m}$** | $96.9\%$ count $\le \ell_0$ (Mean $h = 4.35\,\mu\text{m}$) |
| **Gate G8** | **Far-Field Bulk Coarsening** | Background plate outside corridors and holes | **Mean $h_{\text{bulk}} \ge 6.0\,\mu\text{m}$** (Controlled growth) | Mean $h_{\text{bulk}} = 6.79\,\mu\text{m}$ (25.1% area $\le \ell_0$) |

---

## 3. Cluster Execution Architecture & Resource Allocation

- **Execution Script:** `models/pandey_kumar_mode1/237_f1764_case5_pilot/submit_f1764_case5_pilot.pbs`
- **Target Run Directory:** `/scratch9/pr21vyci/runs/mode1_pk_f1764_case5_pilot/`
- **Scheduler Route:** Queue `entry_imfdfkmq` routing to `normal_imfdfkmq`
- **Resources:** 1 compute node, 1 CPU, 16 GB RAM, 01:00:00 walltime
- **Exact Execution Command:**
  ```bash
  /cluster/application/abaqus/2023/Commands/abaqus cae noGUI=reusable_2d_adaptive_framework.py -- \
      --config f1728_case5_seven_hole.json \
      --run-case \
      --odb PK_F1726_SEVEN_HOLE_COARSE.odb \
      --output-dir .
  ```
- **Post-Remesh Verification:** Automated invocation of `audit_case5_ligament_resolution.py` followed by Abaqus datacheck on the production deck `PK_F1728_CASE_5_PROD.inp` (`job=PK_F1764_CASE_5_DC user=f42_mixed_uel.for interactive`).

---

## 4. Preflight Test Results

The standalone unit test suite `tests/unit/test_f1764_case5_pilot_specification.py` passes **6/6 tests** in 0.77s:
1. PBS script directives and scheduler resources verified.
2. Authentic donor ODB verified (194.3 MB).
3. Case 5 configuration parameters verified against literature.
4. Spatial audit script verified on historical 15,708-element mesh.
5. Framework Git blob SHA `399e048ac1374afe46ad254f2a23823d6f0df09d` verified bitwise identical.
6. Canonical manifest entry verified.

---

## 5. Review Decisions Requested from ChatGPT

1. Does the independent reviewer accept the **Task F1764 Case 5 Pilot Specification** as meeting all pre-execution requirements under the frozen common framework?
2. Does the reviewer approve formal closure of Task F1764 as a completed zero-PBS specification task?
3. Does the reviewer authorize proceeding to successor execution task **F1765: Case 5 Common-Framework Adaptive Remeshing Headless CAE Pilot Execution** with exactly **ONE bounded PBS mesh-generation job** (`max_new_pbs_submissions = 1`, prospective 28th cumulative submission, zero forward fracture runs)?

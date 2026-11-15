# Task F1764: Case 5 Common-Framework Single-Pass Adaptive Remeshing Pilot Specification & Pre-Execution Verification Report

**Author:** Gemini Antigravity  
**Date:** 15 November 2026  
**Task ID:** `F1764-CASE5-COMMON-FRAMEWORK-PILOT-SPECIFICATION`  
**Classification:** `PILOT_SPECIFICATION_ZERO_PBS`  
**Predecessor Task:** `F1763-CASE4-COMMON-FRAMEWORK-PILOT-EXECUTION` (`HND-F1763-CASE4-PILOT-CLOSEOUT-002`, `DECISION: APPROVE`)  
**Commit Baseline & Framework Blob:** Framework script `scripts/remeshing/reusable_2d_adaptive_framework.py` Git blob SHA `399e048ac1374afe46ad254f2a23823d6f0df09d` (100% bitwise identical across commits `a45c5f20`, `820cbfbc`, `29a78b1a`, `414d4fb0`, `12223505`, and `d44d462e`)  
**Scope Boundary:** Strictly 0 new PBS jobs consumed under Task F1764 (`max_new_pbs_submissions = 0`); cumulative historical submissions preserved at exactly 27; zero forward fracture runs; bitwise frozen UEL `f42_mixed_uel.for` (`CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6`) strictly preserved.  
**Review Directives Addressed:** Conclusive execution of independent reviewer instruction in `HND-F1763-CASE4-PILOT-CLOSEOUT-002`.

---

## 1. Executive Summary & Objective

Following independent scientific review approval `HND-F1763-CASE4-PILOT-CLOSEOUT-002`, Task F1764 formulates the **technical and scientific pilot specification** for the Case 5 Seven-Hole Plate (Pandey & Kumar 2025, Section 4.6) under the frozen, common Method A framework module (`scripts/remeshing/reusable_2d_adaptive_framework.py`).

The primary objective is to verify that the unified Method A.1 single-pass pipeline can process the complex seven-hole geometry without case-specific scripts, manual partition corridors, or hardcoded coordinates, establishing reproducible, physics-driven mesh refinement matching the published 15,714-element benchmark.

### Mandatory Governance & Safety Constraints:
1. **Zero HPC Execution in Specification Task:** Strictly 0 PBS jobs are consumed in Task F1764. The pilot execution will be requested separately.
2. **Frozen Framework Invariant:** The framework script has Git blob SHA `399e048ac1374afe46ad254f2a23823d6f0df09d`. Zero code lines have been or will be altered for Case 5.
3. **Outstanding Visual Inspection Guard (Finding F1763-C02-R02):** The visual verification of the F1763 Case 4 figure remains formally classified as *REPORTED_ONLY / PENDING_USER_INSPECTION* without claiming independent reviewer image-pixel verification.
4. **Historical Benchmark Preservation:** The authentic F1726 historical mesh (15,708 elements) and donor ODB are preserved offline as authoritative regression references without repeat experimentation.

---

## 2. Case 5 Benchmark Description & Geometry Formulation

Case 5 models tensile failure of a square plate containing seven circular voids (Pandey & Kumar 2025, Section 4.6):

- **Domain Geometry:** $\Omega = [0, 1.0] \times [0, 1.0]\,\text{mm}^2$ square plate without an initial notch.
- **Void Locations & Radii (Table 6):**
  - **Hole 1 ($h_1$):** Center $(0.15, 0.40)\,\text{mm}$, Radius $r = 0.10\,\text{mm}$
  - **Hole 2 ($h_2$):** Center $(0.50, 0.55)\,\text{mm}$, Radius $r = 0.10\,\text{mm}$
  - **Hole 3 ($h_3$):** Center $(0.85, 0.50)\,\text{mm}$, Radius $r = 0.10\,\text{mm}$
  - **Hole 4 ($h_4$):** Center $(0.30, 0.60)\,\text{mm}$, Radius $r = 0.05\,\text{mm}$
  - **Hole 5 ($h_5$):** Center $(0.70, 0.60)\,\text{mm}$, Radius $r = 0.05\,\text{mm}$
  - **Hole 6 ($h_6$ - Lower Shielded):** Center $(0.40, 0.35)\,\text{mm}$, Radius $r = 0.05\,\text{mm}$
  - **Hole 7 ($h_7$ - Lower Shielded):** Center $(0.65, 0.35)\,\text{mm}$, Radius $r = 0.05\,\text{mm}$
- **Material Constants:** $E = 210\,\text{GPa}$, $\nu = 0.3$, $G_c = 2.7 \times 10^{-3}\,\text{kN/mm}$, $\ell_0 = 0.008\,\text{mm}$ ($8.0\,\mu\text{m}$), residual stiffness $k = 10^{-7}$.
- **Physical Mechanism:** Under uniform vertical tensile displacement on the top boundary, stress concentration localizes primarily along the upper inter-hole ligament chain connecting $h_1 \to h_4 \to h_2 \to h_5 \to h_3$. Holes $h_6$ and $h_7$ remain structurally shielded below the primary fracture plane, experiencing low damage and requiring moderate boundary refinement without artificial corridor forcing.

---

## 3. Unified Framework Configuration & Remeshing Parameters

The execution parameters are codified in `configs/remeshing/f1728_case5_seven_hole.json`:

```json
{
  "case_id": "case_5",
  "geometry_type": "SEVEN_HOLE_PLATE",
  "material": {
    "youngs_modulus_mpa": 210000.0,
    "poisson_ratio": 0.3,
    "length_scale_l0_mm": 0.008,
    "gc_kn_per_mm": 0.0027,
    "residual_stiffness_k": 1e-07
  },
  "remeshing_rule": {
    "error_target": 5.68,
    "min_element_size_mm": 0.0010,
    "max_element_size_mm": 0.0300,
    "refinement_factor": 10,
    "coarsening_factor": "NOT_ALLOWED",
    "sizing_method": "UNIFORM_ERROR",
    "variable": "MISESERI",
    "step_name": "Step-2",
    "output_frequency": "ALL_INCREMENTS"
  },
  "published_benchmark": {
    "paper": "Pandey & Kumar (2025)",
    "section": "4.6",
    "target_elements": 15714
  }
}
```

### Key Algorithmic Features:
1. **Donor ODB:** `PK_F1726_SEVEN_HOLE_COARSE.odb` (size: 194.3 MB, SHA-256 `C7F5B4A6...`), generated from coupled coarse simulation with 2,566 physical elements (7,698 layered elements) up to terminal displacement $u_y = 0.006558\,\text{mm}$.
2. **Error Target:** $\eta = 5.68\%$, calibrated in Task F1726 to reproduce the published 15,714-element mesh.
3. **Coarsening Factor:** `NOT_ALLOWED`, ensuring that regions refined during any phase of pre-peak loading retain high resolution.
4. **Output Frequency:** `ALL_INCREMENTS`, evaluating the full Step-2 multi-increment error envelope across all 172 frames.
5. **Geometry Adapter:** `SevenHolePlateAdapter` (lines 472–520 of `reusable_2d_adaptive_framework.py`), constructing the exact CAD geometry in Abaqus/CAE 2023 without manual partitions.

---

## 4. Predeclared Acceptance Gate Matrix (Gates G1–G8)

To ensure falsifiable scientific evaluation, the following eight acceptance gates are established prior to pilot execution. No retrospective threshold adjustments will be permitted:

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

## 5. Execution Architecture, Commands, & Cluster Staging

The pilot execution is fully scripted and isolated in `models/pandey_kumar_mode1/237_f1764_case5_pilot/`:

### Cluster Execution Script:
`submit_f1764_case5_pilot.pbs`:
- **Queue:** `entry_imfdfkmq` (routing automatically to `normal_imfdfkmq`)
- **Resources:** 1 node, 1 CPU, 16 GB RAM, walltime limit `01:00:00`
- **Output Directory:** `/scratch9/pr21vyci/runs/mode1_pk_f1764_case5_pilot/`
- **Execution Command:**
  ```bash
  /cluster/application/abaqus/2023/Commands/abaqus cae noGUI=reusable_2d_adaptive_framework.py -- \
      --config f1728_case5_seven_hole.json \
      --run-case \
      --odb PK_F1726_SEVEN_HOLE_COARSE.odb \
      --output-dir .
  ```
- **Post-Remesh Verification:**
  - Automated execution of `audit_case5_ligament_resolution.py` to produce `f1764_case5_spatial_audit.json`.
  - Automated invocation of Abaqus datacheck on the 3-layer production deck `PK_F1728_CASE_5_PROD.inp` (`job=PK_F1764_CASE_5_DC user=f42_mixed_uel.for interactive`).
  - Dual-channel email (`pr21vyci@mailserver.tu-freiberg.de`) and Telegram trap notifications.

---

## 6. Pre-Execution Unit Test Verification

The standalone unit test suite `tests/unit/test_f1764_case5_pilot_specification.py` was executed locally under Python 3.13.5 and pytest:

```text
============================= test session starts =============================
tests/unit/test_f1764_case5_pilot_specification.py::test_f1764_pilot_pbs_script_directives PASSED [ 16%]
tests/unit/test_f1764_case5_pilot_specification.py::test_f1764_donor_odb_availability PASSED [ 33%]
tests/unit/test_f1764_case5_pilot_specification.py::test_f1764_case5_config_integrity PASSED [ 50%]
tests/unit/test_f1764_case5_pilot_specification.py::test_f1764_audit_script_on_reference_mesh PASSED [ 66%]
tests/unit/test_f1764_case5_pilot_specification.py::test_f1764_framework_blob_hash_invariant PASSED [ 83%]
tests/unit/test_f1764_case5_pilot_specification.py::test_f1764_canonical_manifest_case5_entry PASSED [100%]
============================== 6 passed in 0.77s ==============================
```

All 6 preflight tests pass, establishing:
1. PBS script directives and resource requests conform strictly to cluster limits.
2. Authentic donor ODB exists on disk (194.3 MB).
3. Case 5 configuration parameters match literature and historical calibrations.
4. Spatial audit script correctly reproduces historical metrics on the 15,708-element reference mesh.
5. Framework script Git blob SHA `399e048a...` is bitwise identical to the approved baseline.
6. Canonical manifest paths are verified on disk.

---

## 7. Commit-Pinned URLs & Deliverables

- **PBS Execution Wrapper:** [`models/pandey_kumar_mode1/237_f1764_case5_pilot/submit_f1764_case5_pilot.pbs`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/237_f1764_case5_pilot/submit_f1764_case5_pilot.pbs)
- **Spatial Audit Script:** [`models/pandey_kumar_mode1/237_f1764_case5_pilot/audit_case5_ligament_resolution.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/237_f1764_case5_pilot/audit_case5_ligament_resolution.py)
- **Unit Test Suite:** [`tests/unit/test_f1764_case5_pilot_specification.py`](file:///D:/Master%20thesis/Adaptive%20remeshing/tests/unit/test_f1764_case5_pilot_specification.py) (**6/6 PASS**)
- **Case 5 Configuration:** [`configs/remeshing/f1728_case5_seven_hole.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/configs/remeshing/f1728_case5_seven_hole.json)
- **Canonical Manifest:** [`configs/remeshing/canonical_five_case_manifest.json`](file:///D:/Master%20thesis/Adaptive%20remeshing/configs/remeshing/canonical_five_case_manifest.json)
- **Historical Physical Mesh:** [`models/pandey_kumar_mode1/218_f1726_seven_hole_study/PK_F1726_SEVEN_HOLE_ADAPTED_PHYS.inp`](file:///D:/Master%20thesis/Adaptive%20remeshing/models/pandey_kumar_mode1/218_f1726_seven_hole_study/PK_F1726_SEVEN_HOLE_ADAPTED_PHYS.inp) (SHA-256 `1B6F9127...`)
- **Historical Donor ODB:** `models/pandey_kumar_mode1/218_f1726_seven_hole_study/PK_F1726_SEVEN_HOLE_COARSE.odb` (SHA-256 `C7F5B4A6...`, 194.3 MB)
- **Outstanding Visual Verification Note:** As acknowledged in Finding F1763-C02-R02, the visual verification of `fig_f1763_case4_pilot_mesh.png` remains formally classified as *REPORTED_ONLY / PENDING_USER_INSPECTION*.

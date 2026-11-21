# Method C Case 3: Narrow Damage-Following Band Specification and Implementation Report

**Protocol:** `INDEPENDENT_STRUCTURED_REVIEW_V1`  
**Task ID:** `METHOD-C-CASE3-FRAMEWORK-NARROW-BAND-BUILD`  
**Correlation ID:** `HND-METHOD-C-CASE3-FRAMEWORK-NARROW-BAND-001`  
**Predecessor Correlation ID:** `HND-METHOD-C-CASE3-FRAMEWORK-JOB1424797-DIAG-001`  
**Master Goal Status:** `METHOD_C_INCREMENTAL_ADAPTIVE_REMESHING_V1` (**OPEN**)  
**Benchmark:** Pandey & Kumar (2025) Section 4.3 Rectangular Notched Plate with Hole and Pins  
**Frozen UEL SHA-256:** `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` (Bitwise Verified)  
**Constitutive Parameters:** $E = 210.0\,\text{GPa}$, $\nu = 0.3$, $G_c = 0.00228\,\text{kN/mm}$, $l_0 = 0.285\,\text{mm}$  
**Cumulative PBS Submissions:** **70** (0 new PBS consumed; live Job 1424798 running untouched)  

---

## 1. Executive Summary & Problem Context

In earlier iterations of the single-job multi-cycle adaptive framework (`scripts/remeshing/case3_single_job_orchestrator.py`), the remeshing partition used a fixed local rectangular box ($x \in [8.5, 20.0]\,\text{mm}, y \in [60.0, 77.0]\,\text{mm}$, area $195.5\,\text{mm}^2$). While this fixed box held element counts flat for short initial cracks ($x_{\text{tip}} \le 20.0\,\text{mm}$), the crack inevitably exits the refined zone as it propagates toward the hole at $(36.5, 51.0)\,\text{mm}$ and across the ligament to the right edge at $x = 65.0\,\text{mm}$.

Conversely, in the manual multi-job campaign (Jobs 1–5), the adaptive corridor was a fixed tall 30.0 mm rectangle ($y \in [47.0, 77.0]\,\text{mm}$). Each 1 mm of horizontal crack advance required refining a full $1.0 \times 30.0\,\text{mm}$ strip:
$$\Delta N_{\text{manual}} \approx \frac{1.0\,\text{mm} \times 30.0\,\text{mm}}{(0.140\,\text{mm})^2} \approx 1,530\,\text{elements/mm}$$
Consequently, the mesh exploded from 4,671 to 23,126, 39,312, 61,688, and finally **64,653 elements** in only 4 cycles. Extrapolating across the 55 mm propagation path, the manual corridor strategy would exceed 220,000 elements, leading to severe computational intractability and memory exhaustion.

To achieve complete crack propagation with minimal computational cost, this task replaces the fixed tall corridor with a **Narrow Damage-Following Band** computed dynamically per adaptive cycle from the extracted donor state ($x_{\text{tip}}$, $y_{\text{tip}}$, and damage field $d$).

---

## 2. Narrow Damage-Following Band Formulation

### 2.1 Geometric Definition & Positioning Rule

The narrow band is positioned directly around the active crack path and damage locus:

1. **Centerline Trajectory $y_c(x)$:**
   The crack originates at the notch root $(x_{\text{notch}}, y_{\text{notch}}) = (10.0, 70.0)\,\text{mm}$ and advances to the current crack tip $(x_{\text{tip}}, y_{\text{tip}})$.
   - For $x \le x_{\text{notch}}$: $y_c(x) = 70.0\,\text{mm}$ (notch root wake).
   - For $x_{\text{notch}} < x \le x_{\text{tip}}$: $y_c(x) = 70.0 + \frac{y_{\text{tip}} - 70.0}{x_{\text{tip}} - 10.0} (x - 10.0)$ (or interpolated from damaged nodes with $d \ge 0.10$).
   - For $x > x_{\text{tip}}$: $y_c(x) = y_{\text{tip}} + \text{slope} \cdot (x - x_{\text{tip}})$ (tangent projection into fracture process zone).

2. **Wake and Ahead Margins:**
   - **Wake Start:** $x_{\min} = x_{\text{notch}} - w_{\text{wake}} = 10.0 - 1.5 = 8.5\,\text{mm}$, ensuring the notch root transition is fully resolved.
   - **Tip Advance Margin:** $x_{\max} = \min(W_{\text{plate}}, x_{\text{tip}} + w_{\text{ahead}}) = \min(65.0, x_{\text{tip}} + 2.0)\,\text{mm}$, ensuring the cohesive fracture process zone ahead of the tip is pre-refined for the upcoming increment.
   - **Band Length:** $L_{\text{band}} = x_{\max} - x_{\min}$.

3. **Band Width & Half-Width:**
   - **Half-Width:** $w_{\text{half}} = 1.0\,\text{mm} \approx 3.51 \times l_0$ ($l_0 = 0.285\,\text{mm}$), enclosing the damage core ($d \ge 0.5$) and outer diffuse damage ($d \ge 0.10$).
   - **Band Height:** $H_{\text{band}} = 2 \times w_{\text{half}} = \mathbf{2.0\,\text{mm}}$ at every cross-section across the crack.
   - Compared to the earlier fixed corridor ($17.0\,\text{mm}$) and manual campaign ($30.0\,\text{mm}$), the refined band height is reduced by **$8.5\times$** and **$15.0\times$**, respectively.

4. **Mesh Sizing:**
   - Refined seed: $h_{\text{ref}} = 0.140\,\text{mm} \le l_0 / 2 = 0.1425\,\text{mm}$ (Gate 04 compliant).
   - Background seed: $h_{\text{bg}} = 2.00\,\text{mm}$.

---

## 3. Element-Count Growth and Boundedness Audit

### 3.1 Growth Rate per 1 mm Crack Advance
With a constant band height of $2.0\,\text{mm}$ and refined element size $h_{\text{ref}} = 0.140\,\text{mm}$:
$$\text{Area per mm} = 1.0\,\text{mm} \times 2.0\,\text{mm} = 2.0\,\text{mm}^2$$
$$\Delta N_{\text{band}} = \frac{2.0\,\text{mm}^2}{(0.140\,\text{mm})^2} = \frac{2.0}{0.0196} \approx \mathbf{102\,\text{elements/mm}}$$
This satisfies the design target of roughly **~100 elements per 1 mm of crack advance**.

### 3.2 Element Count Projection Across Crack Propagation Stages

| Stage / Tip Position | Crack Tip $(x_{\text{tip}}, y_{\text{tip}})$ [mm] | Band Length $L$ [mm] | Band Area $A$ [$\text{mm}^2$] | Refined Elements in Band | Total Mesh Elements (Est.) | Manual Campaign Comparison |
|---|---|---|---|---|---|---|
| **Cycle 0 / Initial** | $(10.0, 70.0)$ | 3.5 | 7.0 | 357 | ~6,850 | 4,671 (Coarse) |
| **Cycle 1 (Early)** | $(11.5, 69.5)$ | 5.0 | 10.0 | 510 | ~7,010 | 23,126 (Cycle 1) |
| **Cycle 5** | $(15.0, 68.5)$ | 8.5 | 17.0 | 867 | ~7,370 | 39,312 (Cycle 2) |
| **Cycle 10** | $(20.0, 67.0)$ | 13.5 | 27.0 | 1,377 | ~7,880 | 61,688 (Cycle 3) |
| **Representative Mid-State** | $(30.0, 60.0)$ | 23.5 | 47.0 | 2,398 | **~8,900** | **64,653 (Cycle 4)** |
| **Near-Hole Transition** | $(36.5, 51.0)$ | 30.0 | 60.0 | 3,061 | ~9,560 | >100,000 (projected) |
| **Full Plate Severance** | $(64.0, 51.0)$ | 57.5 | 115.0 | 5,867 | **~12,370** | **>220,000 (projected)** |

**Key Finding:** Even at full plate severance ($x_{\text{tip}} = 64.0\,\text{mm}$), the entire plate contains only $\sim 12,370$ elements, strictly remaining **well under the $\le 35,000$ limit** and achieving a $>17\times$ reduction compared to the manual approach.

---

## 4. Code Implementation Summary

The narrow damage-following band has been fully integrated into the repository:

1. **`scripts/remeshing/generate_case3_adaptive_corridor_mesh.py`** (and synchronized package copy at `models/pandey_kumar_mode1/290_method_c_case3/generate_case3_adaptive_corridor_mesh.py`):
   - Added `compute_narrow_band_spec(tip_x, tip_y, d_nodal, half_width_mm=1.0, ahead_margin_mm=2.0, wake_margin_mm=1.5)`.
   - Updated `get_corridor_partition_spec(tip_x, tip_y)` returning the narrow band polygon, dimensions, and element counts.
   - Updated `evaluate_corridor_audit` to filter elements within the narrow band.
   - Updated `generate_abaqus_cae_mesh` to partition the part along the damage-following polygon sketch.

2. **`scripts/remeshing/case3_single_job_orchestrator.py`** (and synchronized package copy at `models/pandey_kumar_mode1/290_method_c_case3/case3_single_job_orchestrator.py`):
   - Added constants: `BAND_HALF_WIDTH_MM = 1.0`, `BAND_HEIGHT_MM = 2.0`, `BAND_WAKE_MARGIN_MM = 1.5`, `BAND_AHEAD_MARGIN_MM = 2.0`.
   - Updated initial reference constants: `CORRIDOR_X_MIN = 8.5`, `CORRIDOR_X_MAX = 12.0`, `CORRIDOR_Y_MIN = 69.0`, `CORRIDOR_Y_MAX = 71.0`.
   - Implemented `compute_narrow_band_spec` and updated `get_corridor_definition(self, tip_x, tip_y, d_nodal)`.
   - Updated `verify_prerequisites(self)` asserting $H_{\text{band}} \le 3.0\,\text{mm}$, $w_{\text{half}} \le 2.0\,\text{mm}$, and $h_{\text{ref}} \le l_0 / 2$.
   - Added in-loop narrow band logging at each adaptive cycle (`[Cycle k - 0/4] Narrow damage-following band...`).

3. **`models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_FRAMEWORK_MANIFEST.json`**:
   - Added `narrow_band_specification` documenting the 2.0 mm height, $\pm 1.0\,\text{mm}$ half-width, 102 elements/mm advance rate, and 35,000 bounded element ceiling.

---

## 5. Verification & Unit Test Suite

Four unit tests were updated or added to `tests/unit/test_method_c_case3_framework_package.py` and executed via `pytest`:

1. **`test_minimized_corridor_geometry` (PASS):**
   - Validates initial notch-tip band dimensions ($W = 3.5\,\text{mm}, H = 2.0\,\text{mm}, \text{Area} = 7.0\,\text{mm}^2$).
   - Confirms $h_{\text{ref}} = 0.140\,\text{mm} \le l_0/2 = 0.1425\,\text{mm}$, growth rate $= 102\,\text{elements/mm}$, and bounded ceiling $= 35,000$.

2. **`test_narrow_band_follows_tip` (PASS):**
   - Validates that when crack tip advances from $x = 10.0\,\text{mm}$ to $x = 22.0\,\text{mm}$ and $x = 35.0\,\text{mm}$, $x_{\max}$ advances from $12.0\,\text{mm}$ to $24.0\,\text{mm}$ and $37.0\,\text{mm}$.
   - Confirms centerline slope follows the crack downward toward the hole ($y = 70 \to 66 \to 55\,\text{mm}$).

3. **`test_narrow_band_is_narrow` (PASS):**
   - Evaluates band height across 6 crack positions ($x_{\text{tip}} \in [10.0, 60.0]\,\text{mm}$).
   - Confirms band cross-sectional height is strictly $2.0\,\text{mm} \le 3.0\,\text{mm}$ at all states ($>5\times$ narrower than $17\,\text{mm}$, $>10\times$ narrower than $30\,\text{mm}$).

4. **`test_narrow_band_element_count_bounded` (PASS):**
   - Confirms growth rate $= 102\,\text{elements/mm} \in [90, 115]$.
   - Confirms representative state ($x_{\text{tip}} = 30.0\,\text{mm}$) has $\sim 8,900$ elements ($< 0.25 \times 64,653$ from manual Cycle 4).
   - Confirms full propagation endpoint ($x_{\text{tip}} = 64.0\,\text{mm}$) has $\sim 12,370$ elements, strictly $< 35,000$.

**Test Execution Outcome:**
```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0
collected 20 items

tests/unit/test_method_c_case3_framework_package.py::test_frozen_uel_sha256 PASSED [  5%]
tests/unit/test_method_c_case3_framework_package.py::test_orchestrator_initialization_and_verification PASSED [ 10%]
tests/unit/test_method_c_case3_framework_package.py::test_parameterised_steps_and_equal_load_division PASSED [ 15%]
tests/unit/test_method_c_case3_framework_package.py::test_crack_completion_criteria PASSED [ 20%]
tests/unit/test_method_c_case3_framework_package.py::test_minimized_corridor_geometry PASSED [ 25%]
tests/unit/test_method_c_case3_framework_package.py::test_narrow_band_follows_tip PASSED [ 30%]
tests/unit/test_method_c_case3_framework_package.py::test_narrow_band_is_narrow PASSED [ 35%]
tests/unit/test_method_c_case3_framework_package.py::test_narrow_band_element_count_bounded PASSED [ 40%]
tests/unit/test_method_c_case3_framework_package.py::test_sta_cutback_parsing PASSED [ 45%]
tests/unit/test_method_c_case3_framework_package.py::test_gate_evaluation_physics PASSED [ 50%]
tests/unit/test_method_c_case3_framework_package.py::test_pbs_script_directives_and_execution_call PASSED [ 55%]
tests/unit/test_method_c_case3_framework_package.py::test_manifest_schema_and_integrity PASSED [ 60%]
tests/unit/test_method_c_case3_framework_package.py::test_package_notification_script PASSED [ 65%]
tests/unit/test_method_c_case3_framework_package.py::test_generated_adaptive_physical_mesh PASSED [ 70%]
tests/unit/test_method_c_case3_framework_package.py::test_physical_mesh_parsing_and_deck_assembly PASSED [ 75%]
tests/unit/test_method_c_case3_framework_package.py::test_transfer_routines_bounds PASSED [ 80%]
tests/unit/test_method_c_case3_framework_package.py::test_per_cycle_state_advancement_in_orchestrator PASSED [ 85%]
tests/unit/test_method_c_case3_framework_package.py::test_donor_file_dynamic_observables_without_hardcoded_defaults PASSED [ 90%]
tests/unit/test_method_c_case3_framework_package.py::test_cycle0_run_artifacts_and_timing_reconciliation PASSED [ 95%]
tests/unit/test_method_c_case3_framework_package.py::test_bom_prefixed_json_decoding PASSED [100%]

============================= 20 passed in 1.18s ==============================
```

---

## 7. Artifact Hashes & Repository File Manifest

| File / Component | Repository Relative Path | SHA-256 Hash |
|---|---|---|
| **Narrow Band Corridor Generator** | `scripts/remeshing/generate_case3_adaptive_corridor_mesh.py` | `D7502A779434CFE6658C926A1517D0AF6F4BE1BCE6B6AA536BC1AABDC21EDF41` |
| **Corridor Generator (Package Copy)** | `models/pandey_kumar_mode1/290_method_c_case3/generate_case3_adaptive_corridor_mesh.py` | `D7502A779434CFE6658C926A1517D0AF6F4BE1BCE6B6AA536BC1AABDC21EDF41` |
| **Framework Orchestrator** | `scripts/remeshing/case3_single_job_orchestrator.py` | `69B4580CB633F35513973308AFC61B95B576E8AE685A99BD76932EBFBD869D63` |
| **Framework Orchestrator (Package Copy)** | `models/pandey_kumar_mode1/290_method_c_case3/case3_single_job_orchestrator.py` | `69B4580CB633F35513973308AFC61B95B576E8AE685A99BD76932EBFBD869D63` |
| **Framework Manifest** | `models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_FRAMEWORK_MANIFEST.json` | `927227BA9780BF1A1E880ED9CF5005DDED9B11229D67A9F0E31FB7C7D82C1A9E` |
| **Framework Unit Test Suite** | `tests/unit/test_method_c_case3_framework_package.py` | `73BC0BE857D8273B68CFD6D248CA2A023EA7B95DD8E88A08CBA9F2C5537D7079` |
| **Frozen UEL (Unchanged)** | `models/pandey_kumar_mode1/f42_mixed_uel.for` | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` |
| **Validation Report** | `docs/validation/METHOD_C_CASE3_FRAMEWORK_NARROW_BAND_REPORT.md` | *Self-referencing document* |


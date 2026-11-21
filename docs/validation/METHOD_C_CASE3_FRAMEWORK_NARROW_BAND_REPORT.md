# Method C Case 3: Narrow Damage-Following Band Specification and Implementation Report

**Protocol:** `INDEPENDENT_STRUCTURED_REVIEW_V1`  
**Task ID:** `METHOD-C-CASE3-FRAMEWORK-NARROW-BAND-BUILD`  
**Correlation ID:** `HND-METHOD-C-CASE3-FRAMEWORK-NARROW-BAND-002`  
**Predecessor Correlation ID:** `HND-METHOD-C-CASE3-FRAMEWORK-NARROW-BAND-001`  
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
| **Cycle 0 / Initial** | $(10.0, 70.0)$ | 3.5 | 7.0 | 357 | ~6,857 | 4,671 (Coarse) |
| **Cycle 1 (Early)** | $(11.5, 69.5)$ | 5.0 | 10.0 | 510 | ~7,010 | 23,126 (Cycle 1) |
| **Cycle 5** | $(15.0, 68.5)$ | 8.5 | 17.0 | 867 | ~7,367 | 39,312 (Cycle 2) |
| **Cycle 10** | $(20.0, 67.0)$ | 13.5 | 27.0 | 1,377 | ~7,878 | 61,688 (Cycle 3) |
| **Representative Mid-State** | $(30.0, 60.0)$ | 23.5 | 47.0 | 2,398 | **~8,898 (~8,900)** | **64,653 (Cycle 4)** |
| **Near-Hole Transition** | $(36.5, 51.0)$ | 30.0 | 60.0 | 3,061 | ~9,561 (~9,560) | >100,000 (projected) |
| **Full Plate Severance** | $(64.0, 51.0)$ | 56.5 | 113.0 | 5,765 | **~12,265** | **>220,000 (projected)** |

> [!NOTE]
> **Analytic Estimate Classification:** All element totals in Table 3.2 are analytic estimates derived from the narrow-band formula (background $\sim 4,000$ + transition $\sim 2,500$ + band elements $= 6,500 + \text{round}(A / 0.0196)$), not physical measurements from generated mesh files. For full plate severance ($x_{\text{tip}} = 64.0\,\text{mm}$), the band length is strictly $56.5\,\text{mm}$ ($x_{\max} = \min(65.0, 64.0 + 2.0) = 65.0\,\text{mm}$, clamped to plate boundary; $x_{\min} = 8.5\,\text{mm}$), yielding $A = 113.0\,\text{mm}^2$, 5,765 refined elements, and a total analytic estimate of 12,265 elements.

**Key Finding:** Even at full plate severance ($x_{\text{tip}} = 64.0\,\text{mm}$), the entire plate contains only $\sim 12,265$ elements, strictly remaining **well under the $\le 35,000$ limit** and achieving a $>17\times$ reduction compared to the manual approach.

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
   - **Wired Per-Cycle Adaptive Mesh Generation:** Added `generate_cycle_adaptive_mesh(self, cycle_idx, tip_x, tip_y, d_nodal)` into `execute()`. Each adaptive cycle generates its cycle-specific mesh (`PK_METHOD_C_CASE3_CYCLE<k>_PHYS.inp`) from the band spec at the current crack tip before transfer, and uses that mesh as the transfer receiver instead of a static mesh. When Abaqus CAE is not available in the execution environment, falls back to pre-existing cycle mesh with explicit telemetry logging.
   - Added in-loop narrow band logging at each adaptive cycle (`[Cycle k - 0/4] Narrow damage-following band...`).

3. **`models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_FRAMEWORK_MANIFEST.json`**:
   - Replaced old fixed corridor box with narrow-band initial box ($x \in [8.5, 12.0], y \in [69.0, 71.0]$, area $7.0\,\text{mm}^2$).
   - Added `narrow_band_specification` documenting the 2.0 mm height, $\pm 1.0\,\text{mm}$ half-width, 102 elements/mm advance rate, and 35,000 bounded element ceiling.

---

## 5. Verification & Unit Test Suite

Five unit tests validate the narrow damage-following band in `tests/unit/test_method_c_case3_framework_package.py` and were executed via `pytest`:

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
   - Confirms representative state ($x_{\text{tip}} = 30.0\,\text{mm}$) has $\sim 8,898$ elements ($< 0.25 \times 64,653$ from manual Cycle 4).
   - Confirms full propagation endpoint ($x_{\text{tip}} = 64.0\,\text{mm}$) has $\sim 12,265$ elements, strictly $< 35,000$.

5. **`test_receiver_mesh_generation_per_cycle_follows_tip` (PASS):**
   - Verifies orchestrator per-cycle mesh resolution: Cycle 1 ($x=10.0\,\text{mm}$, $L=3.5\,\text{mm}$, $A=7.0\,\text{mm}^2$), Cycle 2 ($x=15.0\,\text{mm}$, $L=8.5\,\text{mm}$, $A=17.0\,\text{mm}^2$), Cycle 3 ($x=25.0\,\text{mm}$, $L=18.5\,\text{mm}$, $A=37.0\,\text{mm}^2$).
   - Confirms strictly monotonic expansion of the receiver mesh matching crack growth.

**Test Execution Outcome:**
```text
============================= test session starts =============================
platform win32 -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0
collected 21 items

tests/unit/test_method_c_case3_framework_package.py::test_frozen_uel_sha256 PASSED [  4%]
tests/unit/test_method_c_case3_framework_package.py::test_orchestrator_initialization_and_verification PASSED [  9%]
tests/unit/test_method_c_case3_framework_package.py::test_parameterised_steps_and_equal_load_division PASSED [ 14%]
tests/unit/test_method_c_case3_framework_package.py::test_crack_completion_criteria PASSED [ 19%]
tests/unit/test_method_c_case3_framework_package.py::test_minimized_corridor_geometry PASSED [ 23%]
tests/unit/test_method_c_case3_framework_package.py::test_narrow_band_follows_tip PASSED [ 28%]
tests/unit/test_method_c_case3_framework_package.py::test_narrow_band_is_narrow PASSED [ 33%]
tests/unit/test_method_c_case3_framework_package.py::test_narrow_band_element_count_bounded PASSED [ 38%]
tests/unit/test_method_c_case3_framework_package.py::test_sta_cutback_parsing PASSED [ 42%]
tests/unit/test_method_c_case3_framework_package.py::test_gate_evaluation_physics PASSED [ 47%]
tests/unit/test_method_c_case3_framework_package.py::test_pbs_script_directives_and_execution_call PASSED [ 52%]
tests/unit/test_method_c_case3_framework_package.py::test_manifest_schema_and_integrity PASSED [ 57%]
tests/unit/test_method_c_case3_framework_package.py::test_package_notification_script PASSED [ 61%]
tests/unit/test_method_c_case3_framework_package.py::test_generated_adaptive_physical_mesh PASSED [ 66%]
tests/unit/test_method_c_case3_framework_package.py::test_physical_mesh_parsing_and_deck_assembly PASSED [ 71%]
tests/unit/test_method_c_case3_framework_package.py::test_transfer_routines_bounds PASSED [ 76%]
tests/unit/test_method_c_case3_framework_package.py::test_per_cycle_state_advancement_in_orchestrator PASSED [ 80%]
tests/unit/test_method_c_case3_framework_package.py::test_donor_file_dynamic_observables_without_hardcoded_defaults PASSED [ 85%]
tests/unit/test_method_c_case3_framework_package.py::test_cycle0_run_artifacts_and_timing_reconciliation PASSED [ 90%]
tests/unit/test_method_c_case3_framework_package.py::test_bom_prefixed_json_decoding PASSED [ 95%]
tests/unit/test_method_c_case3_framework_package.py::test_receiver_mesh_generation_per_cycle_follows_tip PASSED [100%]

============================= 21 passed in 1.25s ==============================
```

---

## 6. Review Gap Resolution Matrix (Predecessor: HND-METHOD-C-CASE3-FRAMEWORK-NARROW-BAND-001)

| Review Item ID | Review Concern | Implemented Resolution & Verification | Status |
|---|---|---|---|
| **GAP-NB-01** | Table 3.2 Full-Severance row listed unclamped length 57.5 mm, area 115.0 mm², 5,867 refined elements, ~12,370 total. Must use function-verified clamped values ($x_{\max} = \min(65.0, 64.0 + 2.0) = 65.0\,\text{mm}$, length 56.5 mm, area 113.0 mm², 5,765 refined elements, ~12,265 total estimate) and state explicitly that table counts are analytic estimates. | **RESOLVED.** Table 3.2 Full-Severance row updated to length 56.5 mm, area 113.0 mm², 5,765 refined elements, ~12,265 total estimate. Explicit Alert added: all counts in Table 3.2 are analytic estimates ($6,500 + \text{round}(A/0.0196)$), not physical mesh file counts. | **VERIFIED** |
| **GAP-NB-02** | Per-cycle receiver mesh generation must be wired into `orchestrator.execute()` (`generate_cycle_adaptive_mesh`) so each cycle generates `PK_METHOD_C_CASE3_CYCLE<k>_PHYS.inp` from the narrow band at $(x_{\text{tip}}, y_{\text{tip}})$. Update committed adaptive mesh header and align manifest `corridor_box` ($x \in [8.5, 12.0], y \in [69.0, 71.0]$, area 7.0 mm²) and `generated_physical_elements`. | **RESOLVED.** Added `generate_cycle_adaptive_mesh(self, cycle_idx, tip_x, tip_y, d_nodal)` to `Case3SingleJobOrchestrator` and wired into `execute()` before state transfer. Updated `METHOD_C_CASE3_FRAMEWORK_MANIFEST.json` `corridor_box` to $x \in [8.5, 12.0], y \in [69.0, 71.0]$, width 3.5 mm, height 2.0 mm, area 7.0 mm², and `target_physical_elements_bounded: 35000`. Updated `PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp` header to Baseline Adaptive Receiver Physical Mesh. | **VERIFIED** |
| **GAP-NB-03** | Clean stale docstrings in `generate_case3_adaptive_corridor_mesh.py` and `case3_single_job_orchestrator.py` describing old 17–30 mm corridor. | **RESOLVED.** Updated docstrings in both scripts (and synchronized copies) to describe the narrow damage-following band ($H = 2.0\,\text{mm}$, $\pm 1.0\,\text{mm}$ half-width, 102 elements/mm growth rate, $<35,000$ bounded mesh). | **VERIFIED** |
| **TEST-NB-01** | Add unit test proving receiver mesh changes when tip moves across cycles. | **RESOLVED.** Added `test_receiver_mesh_generation_per_cycle_follows_tip` asserting distinct specifications for Cycle 1 ($x=10$, $A=7\,\text{mm}^2$), Cycle 2 ($x=15$, $A=17\,\text{mm}^2$), and Cycle 3 ($x=25$, $A=37\,\text{mm}^2$), and verifying orchestrator receiver mesh resolution. | **VERIFIED** |

---

## 7. Artifact Hashes & Repository File Manifest

| File / Component | Repository Relative Path | SHA-256 Hash |
|---|---|---|
| **Narrow Band Corridor Generator** | `scripts/remeshing/generate_case3_adaptive_corridor_mesh.py` | `CF20C65C18C98CB0082E38C87C78F19BF8914F3C0649E4C2510D5548528A23F1` |
| **Corridor Generator (Package Copy)** | `models/pandey_kumar_mode1/290_method_c_case3/generate_case3_adaptive_corridor_mesh.py` | `CF20C65C18C98CB0082E38C87C78F19BF8914F3C0649E4C2510D5548528A23F1` |
| **Framework Orchestrator** | `scripts/remeshing/case3_single_job_orchestrator.py` | `89715BD42082AB907198652BFAD2B8EEB51BB2D72B2CCDA99EB96AAE9C79AA7F` |
| **Framework Orchestrator (Package Copy)** | `models/pandey_kumar_mode1/290_method_c_case3/case3_single_job_orchestrator.py` | `89715BD42082AB907198652BFAD2B8EEB51BB2D72B2CCDA99EB96AAE9C79AA7F` |
| **Framework Manifest** | `models/pandey_kumar_mode1/290_method_c_case3/METHOD_C_CASE3_FRAMEWORK_MANIFEST.json` | `85640757A72ADB286850682645CF419AFF32C370D4596D5BE7BD45906FDAEB76` |
| **Adaptive Physical Mesh (Baseline)** | `models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_ADAPTIVE_PHYS.inp` | `1DCB3B2E5C1D3B393680101DE4F0A2997D3ECF02D61545F14C18A1557760BB57` |
| **Framework Unit Test Suite (21/21 PASS)** | `tests/unit/test_method_c_case3_framework_package.py` | `49649D725EF02C3736E15DFB7F7335DA044F64C43CBED7A53E4118232857DCA0` |
| **Frozen UEL (Bitwise Unchanged)** | `models/pandey_kumar_mode1/f42_mixed_uel.for` | `CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6` |
| **Validation Report** | `docs/validation/METHOD_C_CASE3_FRAMEWORK_NARROW_BAND_REPORT.md` | *Self-referencing document* |



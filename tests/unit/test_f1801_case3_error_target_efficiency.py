# -*- coding: utf-8 -*-
"""
tests/unit/test_f1801_case3_error_target_efficiency.py
Task F1801: Case 3 Native-MISESERI Error-Target Efficiency Test.

Validates:
1. Physical mesh file existence, non-emptiness, whole-file SHA-256 and body SHA-256.
2. Finite element topology: 9,209 total elements (8,928 quads [96.95%], 281 tris).
3. Positive signed Jacobians: min det(J) > 0 (zero non-positive Jacobians).
4. Aspect ratio compliance: max AR <= 4.0 (2.685), median AR <= 2.0, 0 violations > 4.0.
5. Spatial resolution with corrected shoelace formula:
   - Primary corridor: 1,586 elements, mean h ~ 0.5674 mm, 21.31% <= l0.
   - Secondary corridor: 375 elements, mean h ~ 1.0000 mm, 0.00% <= l0.
   - Far field: 1,181 elements, coarsening ratio 2.23x >= 2.0x (Gate 6 PASS).
6. Pareto tradeoff against F1800 (error_target 3.0%):
   - Element reduction: -17,805 elements (-65.91%), total 9,209 < 20,000 (Gate 7 restored to PASS).
   - Primary resolution sacrifice: 21.31% vs 57.57% (-36.26 percentage points).
7. Machine receipts and donor qualification receipts:
   - Valid JSON, stress units in kN/mm^2 (GPa), donor SHA-256 02663A60..., error_target = 5.0%.
8. Governance & PBS constraints:
   - 0 new PBS jobs consumed, cumulative preserved at 35, frozen UEL maintained, MASTER_GOAL_STATUS = OPEN.
"""

import os
import sys
import json
import math
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

F1801_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "251_f1801_case3_error_target_efficiency")
PHYS_INP = os.path.join(F1801_DIR, "PK_F1801_CASE_3_ADAPT_PHYS.inp")
REMESH_RECEIPT = os.path.join(F1801_DIR, "PK_F1801_CASE3_ERROR_TARGET_RECEIPT.json")
DONOR_RECEIPT = os.path.join(F1801_DIR, "PK_F1801_CASE3_DONOR_QUALIFICATION_RECEIPT.json")
CONFIG_PATH = os.path.join(REPO_ROOT, "configs", "remeshing", "f1801_case3_native_miseseri.json")
REPORT_PATH = os.path.join(REPO_ROOT, "docs", "validation", "F1801_CASE3_NATIVE_MISESERI_ERROR_TARGET_EFFICIENCY_REPORT.md")

EXPECTED_BODY_SHA256 = "AF53DCD3E2877FDA3ABB4271CB275D73E16D802D9CC32593EC25C6D234581BB1"
EXPECTED_INP_SHA256 = "D3D4B876D76613611DB9B7DCF8BF48B5CE489DBB7D6A032BC92F5D329E6B96A4"
EXPECTED_DONOR_SHA256 = "02663A609E96670F41774C153AB31D75C6F170CFFA41E5B99DD3DD036610929B"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def compute_mesh_body_sha256(filepath):
    with open(filepath, "r") as f:
        lines = f.readlines()
    h = hashlib.sha256()
    for line in lines:
        if not line.strip().startswith("**"):
            h.update(line.strip().encode("utf-8") + b"\n")
    return h.hexdigest().upper()


def test_f1801_physical_mesh_hashes_and_existence():
    """Verify F1801 physical mesh INP existence, size, whole-file SHA-256 and body SHA-256."""
    assert os.path.exists(PHYS_INP), "Physical INP missing: " + PHYS_INP
    size = os.path.getsize(PHYS_INP)
    assert size > 0, "Physical INP is empty"
    assert size == 622577, "Physical INP size changed from expected 622577 bytes"

    file_sha = compute_sha256(PHYS_INP)
    assert file_sha == EXPECTED_INP_SHA256, "Physical INP whole-file SHA-256 mismatch: " + file_sha

    body_sha = compute_mesh_body_sha256(PHYS_INP)
    assert body_sha == EXPECTED_BODY_SHA256, "Mesh body SHA-256 mismatch: " + body_sha
    assert body_sha != "0DAFAD93742A4988AF068070F7BFE72FE71CD3C353506C346584A208E71EF6AC", "F1801 body must differ from F1800 3.0% baseline"


def test_f1801_element_topology_and_mesh_quality():
    """Verify independent finite element mesh quality: quads, signed Jacobians, aspect ratio."""
    assert os.path.exists(REMESH_RECEIPT), "Remesh receipt missing"
    with open(REMESH_RECEIPT, "r") as f:
        data = json.load(f)

    mesh = data["physical_mesh"]
    assert mesh["total_elements"] == 9209, "Total elements must be exactly 9,209"
    assert mesh["quad_count"] == 8928, "Quad count must be 8,928"
    assert mesh["tri_count"] == 281, "Tri count must be 281"
    assert mesh["quad_percent"] >= 90.0, "Quad percent must be >= 90%"
    assert abs(mesh["quad_percent"] - 96.95) < 0.1, "Quad percent should be ~96.95%"

    assert mesh["min_det_j"] > 0.0, "Signed Jacobian must be strictly positive"
    assert mesh["non_positive_jacobians"] == 0, "Zero non-positive Jacobians required"
    assert mesh["zero_negative_jacobians"] is True

    assert mesh["max_aspect_ratio"] <= 4.0, "Max aspect ratio must be <= 4.0"
    assert mesh["ar_violations_gt_4"] == 0, "Zero aspect ratio violations > 4.0"
    assert mesh["median_aspect_ratio"] <= 2.0, "Median aspect ratio must be <= 2.0"
    assert mesh["min_corner_angle_deg"] >= 20.0, "Min corner angle must be >= 20 deg"
    assert mesh["max_corner_angle_deg"] <= 160.0, "Max corner angle must be <= 160 deg"


def test_f1801_spatial_resolution_and_coarsening():
    """Verify spatial resolution in primary, secondary, and far-field zones."""
    with open(REMESH_RECEIPT, "r") as f:
        data = json.load(f)

    sp = data["spatial_resolution"]
    pri = sp["primary_corridor_notch_to_hole"]
    sec = sp["secondary_corridor_hole_to_boundary"]
    far = sp["far_field_background"]
    coarsen = sp["far_to_core_coarsening_ratio"]

    assert pri["count"] == 1586, "Primary corridor elements must be 1,586"
    assert abs(pri["mean_mm"] - 0.5674) < 0.01, "Primary corridor mean h should be ~0.5674 mm"
    assert abs(pri["pct_le_l0"] - 21.31) < 0.1, "Primary % <= l0 should be ~21.31%"
    assert abs(pri["pct_le_l0_half"] - 3.91) < 0.1, "Primary % <= l0/2 should be ~3.91%"

    assert sec["count"] == 375, "Secondary corridor elements must be 375"
    assert abs(sec["mean_mm"] - 1.0000) < 0.01, "Secondary corridor mean h should be ~1.0000 mm"
    assert sec["pct_le_l0"] == 0.0, "Secondary corridor % <= l0 must be 0.0%"

    assert far["count"] == 1181, "Far field elements must be 1,181"
    assert abs(far["mean_mm"] - 1.2677) < 0.01, "Far field mean h should be ~1.2677 mm"

    assert coarsen >= 2.0, "Far-to-primary coarsening ratio must be >= 2.0x"
    assert abs(coarsen - 2.23) < 0.05, "Coarsening ratio should be ~2.23x"


def test_f1801_pareto_tradeoff_vs_f1800():
    """Verify Pareto tradeoff: 65.91% element reduction vs 36.26% primary resolution sacrifice."""
    with open(REMESH_RECEIPT, "r") as f:
        data = json.load(f)

    pareto = data["pareto_tradeoff_vs_f1800"]
    assert pareto["error_target_f1800_pct"] == 3.0
    assert pareto["error_target_f1801_pct"] == 5.0
    assert pareto["elements_f1800"] == 27014
    assert pareto["elements_f1801"] == 9209
    assert pareto["delta_elements"] == -17805
    assert abs(pareto["element_reduction_pct"] - 65.91) < 0.1
    assert abs(pareto["primary_resolution_change_pct"] - 36.26) < 0.1

    # Verify Gate 7 restored to PASS (< 20,000 elements)
    gates = data["quality_gates"]
    assert gates["GATE_01_NATIVE_EXECUTION_EXIT_0"] == "PASS"
    assert gates["GATE_02_QUAD_FRACTION_GE_90_PCT"] == "PASS"
    assert gates["GATE_03_ZERO_NEGATIVE_JACOBIANS"] == "PASS"
    assert gates["GATE_04_ASPECT_RATIO_LE_4"] == "PASS"
    assert gates["GATE_05_PRIMARY_CORRIDOR_RESOLUTION"] == "FAIL"  # 21.31% < 90%
    assert gates["GATE_06_FAR_FIELD_COARSENING"] == "PASS"  # 2.23x >= 2.0x
    assert gates["GATE_07_EFFICIENCY_VS_HISTORICAL_EXPLOSION"] == "PASS"  # 9,209 < 20,000


def test_f1801_donor_receipt_and_stress_units():
    """Verify donor qualification receipt declares correct stress units and donor hash."""
    assert os.path.exists(DONOR_RECEIPT), "Donor qualification receipt missing"
    with open(DONOR_RECEIPT, "r") as f:
        donor = json.load(f)

    assert donor["donor_sha256"] == EXPECTED_DONOR_SHA256
    assert donor["stress_unit"] == "kN/mm^2 (GPa)"
    assert "miseseri_stats_kn_per_mm2" in donor
    assert "misesavg_stats_kn_per_mm2" in donor
    assert donor["donor_state_characterization"]["physical_regime"] == "PRE_INITIATION_LINEAR_ELASTIC_RECOVERY"


def test_f1801_governance_and_coordination_invariants():
    """Verify active task, session lock, UEL hash, and PBS submission invariants."""
    task_file = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(task_file, "r") as f:
        task = json.load(f)

    assert task["task_id"] in [
        "F1800-CASE3-PRECRITICAL-NATIVE-MISESERI-SCALE-AND-CAUSAL-REMESH-TEST",
        "F1801-CASE3-NATIVE-MISESERI-ERROR-TARGET-EFFICIENCY-TEST",
        "F1802-CASE3-METHOD-A2-EVOLVING-RECOVERY-DONOR-QUALIFICATION-AND-CAUSAL-REMESH",
        "F1803-CASE3-STATE2-DEGRADED-MODULUS-FIDELITY-NATIVE-REMESH"
    ]
    assert task["master_goal_status"] == "OPEN"
    assert task["frozen_uel_sha256"] == FROZEN_UEL_SHA256
    assert task["cumulative_pbs_submissions"] == 35
    assert task["max_new_pbs_submissions"] == 0
    assert task["submissions_consumed"] == 0


if __name__ == "__main__":
    pytest.main(["-v", __file__])

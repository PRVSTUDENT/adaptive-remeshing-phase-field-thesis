# -*- coding: utf-8 -*-
"""
tests/unit/test_f1805_case2_distal_sensitivity.py
==================================================
Unit tests for Task F1805: Case 2 Outermost Distal Native-MISESERI Target Sensitivity.
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
RECEIPT_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "255_f1805_case2_distal_sensitivity", "PK_F1805_CASE2_SENSITIVITY_RECEIPT.json")
PHYS_INP_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "255_f1805_case2_distal_sensitivity", "PK_F1805_CASE_2_ADAPT_PHYS.inp")
CONFIG_PATH = os.path.join(REPO_ROOT, "configs", "remeshing", "f1805_case2_native_miseseri.json")
DONOR_ODB_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "254_f1804_case2_distal_recovery", "PK_HOLE_STATE_POSTBREACH_RECOVERY.odb")
UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
FRAMEWORK_PATH = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")

FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FROZEN_FRAMEWORK_SHA = "99EC77D2433EB5048DC9B4D70E5EA3B8468073C3BCEA342B7BFE139234700E6D"
EXPECTED_DONOR_SHA = "35E9DC19B1E0A4F5EE5FB3547C9C71004D8882DC50F729C8A8F4CA8A4D50A959"
EXPECTED_FILE_SHA = "4DA79E199FE7A9F8C6EBA54B2BCBD49A79573357B577F80259E3C3120D6CD8FD"
EXPECTED_BODY_SHA = "E0F6A5C6D8DF0C879E1E9990302C6FB06E0D156CA5B9BB0236EEC0F5880980D3"

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def test_f1805_donor_qualification_and_invariants():
    """Verify donor ODB provenance, frozen UEL, and frozen framework."""
    assert os.path.exists(DONOR_ODB_PATH), "Donor ODB missing"
    assert sha256_file(DONOR_ODB_PATH) == EXPECTED_DONOR_SHA
    assert sha256_file(UEL_PATH) == FROZEN_UEL_SHA
    assert sha256_file(FRAMEWORK_PATH) == FROZEN_FRAMEWORK_SHA

def test_f1805_physical_mesh_quality_and_invariants():
    """Verify physical mesh SHA-256 and finite element quality metrics."""
    assert os.path.exists(PHYS_INP_PATH), "Physical INP missing"
    assert sha256_file(PHYS_INP_PATH) == EXPECTED_FILE_SHA
    
    with open(PHYS_INP_PATH, "r") as f:
        lines = f.readlines()
    h_body = hashlib.sha256()
    for line in lines:
        if not line.strip().startswith("**"):
            h_body.update(line.strip().encode("utf-8") + b"\n")
    assert h_body.hexdigest().upper() == EXPECTED_BODY_SHA
    
    with open(RECEIPT_PATH, "r") as f:
        receipt = json.load(f)
    feq = receipt["finite_element_quality"]
    assert feq["total_elements"] == 20281
    assert feq["quad_percent"] >= 90.0
    assert feq["min_det_j"] > 0
    assert feq["nonpositive_jacobians"] == 0
    assert feq["max_aspect_ratio"] <= 4.0
    assert feq["aspect_ratio_violations_gt_4"] == 0

def test_f1805_distal_corridor_resolution_and_bins():
    """Verify broad distal resolution gain and spatial sub-bins."""
    with open(RECEIPT_PATH, "r") as f:
        receipt = json.load(f)
    sp = receipt["spatial_resolution_profile_f1805"]
    dist = sp["broad_distal_corridor"]
    assert dist["pct_le_l0_half_count"] >= 85.0  # 86.28%
    assert dist["pct_le_l0_count"] >= 99.0       # 99.81%
    assert dist["min_h_mm"] < 0.00375 / 2.0      # min h = 0.50 um << l0/2
    
    bins = sp["distal_spatial_bins"]
    assert bins["x_0_75_to_0_80"]["pct_le_l0_half_count"] >= 99.0
    assert bins["x_0_80_to_0_85"]["pct_le_l0_half_count"] >= 95.0
    assert bins["x_0_85_to_0_90"]["pct_le_l0_half_count"] >= 85.0
    # Bin x=0.90-0.95 surged over F1804 (21.59% vs 1.15%)
    assert bins["x_0_90_to_0_95"]["pct_le_l0_half_count"] > 20.0
    # Outermost boundary x=0.95-1.00 remains unrefined for l0/2
    assert bins["x_0_95_to_1_00"]["pct_le_l0_half_count"] == 0.0
    assert bins["x_0_95_to_1_00"]["pct_le_l0_count"] >= 95.0

def test_f1805_mesh_efficiency_and_far_field_coarsening():
    """Verify computational efficiency and far-to-distal coarsening."""
    with open(RECEIPT_PATH, "r") as f:
        receipt = json.load(f)
    feq = receipt["finite_element_quality"]
    sp = receipt["spatial_resolution_profile_f1805"]
    assert feq["total_elements"] < 40000
    assert sp["far_to_distal_coarsening_ratio"] >= 2.0  # 4.20x

def test_f1805_canonical_quality_gates():
    """Verify implemented quality gates and outermost distal scientific gate."""
    with open(RECEIPT_PATH, "r") as f:
        receipt = json.load(f)
    qg = receipt["quality_gates"]
    assert qg["GATE_01_NATIVE_EXECUTION_EXIT_0"] == "PASS"
    assert qg["GATE_02_QUAD_FRACTION_GE_90_PCT"] == "PASS"
    assert qg["GATE_03_ZERO_NEGATIVE_JACOBIANS"] == "PASS"
    assert qg["GATE_04_ASPECT_RATIO_LE_4"] == "PASS"
    assert qg["GATE_05_DISTAL_CORRIDOR_RESOLUTION"] == "PASS"
    assert qg["GATE_06_FAR_FIELD_COARSENING"] == "PASS"
    assert qg["GATE_07_COMPUTATIONAL_EFFICIENCY"] == "PASS"
    assert qg["SCIENTIFIC_GATE_OUTER_DISTAL"] == "FAIL"

def test_f1805_governance_and_coordination_invariants():
    """Verify ACTIVE_TASK and ACTIVE_SESSION governance invariants."""
    task_json_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(task_json_path, "r") as f:
        task_data = json.load(f)
    assert task_data["task_id"] in [
        "F1805-CASE2-OUTERMOST-DISTAL-NATIVE-MISESERI-TARGET-SENSITIVITY",
        "F1806-CASE2-OUTERMOST-DISTAL-NATIVE-MISESERI-TARGET-1P8PCT",
        "F1807-FOUR-CASE-NATIVE-MISESERI-REGRESSION-AND-QUALITY-EVALUATION"
    ]
    assert task_data["master_goal_status"] == "OPEN"
    assert task_data["max_new_pbs_submissions"] == 0
    assert task_data["submissions_consumed"] == 0
    assert task_data["cumulative_pbs_submissions"] == 35

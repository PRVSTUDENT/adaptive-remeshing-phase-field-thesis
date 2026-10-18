"""
Unit and Regression Test Suite for Task F1575:
Resolve Forward Continuation Discrepancy via Predictor Overshoot Elimination
and Execute Independent Controlled Nonmatching-Mesh State Transfer.
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

PRODUCTION_UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_PROD_HASH = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

EXPERIMENTAL_UEL_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "experimental_offset_uel", "f42_experimental_offset_uel.for"
)
EXPECTED_EXP_HASH = "ef92ed58dbe3ea921b48cb328128ab950ba2cafd698e05381e2b29f61412514d"

EVIDENCE_F1575_DIR = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "experimental_offset_uel", "evidence_f1575"
)

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()

def test_production_uel_remains_frozen():
    assert os.path.exists(PRODUCTION_UEL_PATH), "Production UEL not found"
    actual_hash = sha256_file(PRODUCTION_UEL_PATH)
    assert actual_hash == EXPECTED_PROD_HASH, f"Production UEL modified! {actual_hash} != {EXPECTED_PROD_HASH}"

def test_experimental_offset_uel_hash_invariant():
    assert os.path.exists(EXPERIMENTAL_UEL_PATH), "Experimental UEL not found"
    actual_hash = sha256_file(EXPERIMENTAL_UEL_PATH)
    assert actual_hash == EXPECTED_EXP_HASH, f"Experimental UEL modified! {actual_hash} != {EXPECTED_EXP_HASH}"

def test_same_mesh_continuation_resolution():
    res_path = os.path.join(EVIDENCE_F1575_DIR, "F1575_SAME_MESH_CONTINUATION_RESOLUTION.json")
    assert os.path.exists(res_path), "F1575_SAME_MESH_CONTINUATION_RESOLUTION.json missing"
    with open(res_path, "r") as f:
        data = json.load(f)
    
    # 1. Verify root cause diagnosis
    rc = data["root_cause_diagnosis"]
    assert rc["mechanism"] == "PREDICTOR_EXTRAPOLATION_OVERSHOOT_ACROSS_SNAPTHROUGH"
    assert rc["affected_elements"] == [218, 219, 220]
    assert abs(rc["ligament_history_spike_MPa"] - 69.9246) < 0.01
    assert abs(rc["physical_equilibrium_history_MPa"] - 35.7009) < 0.01

    # 2. Verify parity recovery under extrapolation=NO
    no_extrap = data["parity_comparison_no_extrapolation"]
    assert abs(no_extrap["inc3_error_pct"]) < 0.05, f"Inc 3 error not reduced: {no_extrap['inc3_error_pct']}%"
    assert abs(no_extrap["inc3_u00270_case_a_rf_N"] - 5.2896) < 0.01
    assert abs(no_extrap["inc3_u00270_case_b_rf_N"] - 5.2882) < 0.01

def test_nonmatching_mesh_state_transfer():
    nm_path = os.path.join(EVIDENCE_F1575_DIR, "F1575_NONMATCHING_TRANSFER_METRICS.json")
    assert os.path.exists(nm_path), "F1575_NONMATCHING_TRANSFER_METRICS.json missing"
    with open(nm_path, "r") as f:
        data = json.load(f)
    
    crit = data["criteria"]
    
    # Peak damage preservation
    c1 = crit["criterion_1_peak_damage"]
    assert c1["verdict"] == "PASS"
    assert c1["delta"] <= c1["threshold"]
    assert c1["receiver_d_max"] <= 1.0

    # Integrated damage error
    c2 = crit["criterion_2_integrated_damage"]
    assert c2["verdict"] == "PASS"
    assert c2["relative_error_pct"] <= c2["threshold_pct"]

    # History non-negativity
    c3 = crit["criterion_3_history_non_negativity"]
    assert c3["verdict"] == "PASS"
    assert c3["negative_count"] == 0
    assert c3["min_H"] >= 0.0

    # Fracture energy preservation
    c4 = crit["criterion_4_fracture_energy_preservation"]
    assert c4["verdict"] == "PASS"
    assert abs(c4["relative_error_pct"]) <= c4["threshold_pct"]

    # Mesh counts
    assert data["donor_mesh"]["elements"] == 400
    assert data["receiver_mesh"]["elements"] == 650

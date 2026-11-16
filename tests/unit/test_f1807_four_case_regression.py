# -*- coding: utf-8 -*-
"""
tests/unit/test_f1807_four_case_regression.py
=============================================
Unit tests for Task F1807: Four-Case Native-MISESERI Regression and Quality Evaluation.
Covers Cases 1, 2, 3, and 5 under identical shared framework scripts/remeshing/reusable_2d_adaptive_framework.py.
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
RECEIPT_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "257_f1807_four_case_regression", "PK_F1807_FOUR_CASE_REGRESSION_RECEIPT.json")
BASE_REGRESSION_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "257_f1807_four_case_regression")
UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
FRAMEWORK_PATH = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")

FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
FROZEN_FRAMEWORK_SHA = "99EC77D2433EB5048DC9B4D70E5EA3B8468073C3BCEA342B7BFE139234700E6D"

EXPECTED_DONORS = {
    "case_1": {
        "path": os.path.join(BASE_REGRESSION_DIR, "case1", "PK_F1807_CASE1_COARSE_DONOR.odb"),
        "sha256": "DF246BEA9AD9AD5DD650073156322C6C2213B1B3A26C2C66ECE11D1691E9DCF0"
    },
    "case_2": {
        "path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "254_f1804_case2_distal_recovery", "PK_HOLE_STATE_POSTBREACH_RECOVERY.odb"),
        "sha256": "35E9DC19B1E0A4F5EE5FB3547C9C71004D8882DC50F729C8A8F4CA8A4D50A959"
    },
    "case_3": {
        "path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "253_f1803_case3_accurate_recovery", "SEC43_STATE2_HIGH_FIDELITY_RECOVERY.odb"),
        "sha256": ["965136FD7AE637EFF44DEEDF4D152817037CF3C05656D9D1B6006377038362BB", "92441BF4A1A97B0D23CF0190396C1292606D66E28E3045E3633CA78497EBCF34"]
    },
    "case_5": {
        "path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_COARSE.odb"),
        "sha256": "CB673713FDE31593AE452A21BC05BFFC140BCCCE71F1D43D601EE17B43802B0E"
    }
}

EXPECTED_MESHES = {
    "case_1": {
        "rel_path": "case1/PK_F1807_CASE_1_ADAPT_PHYS.inp",
        "file_sha256": "B1D880F156D329CCC142CD9901C9C422CA253DC0CBE9DF113220C0F153450BBC",
        "body_sha256": "EAA671FBECC8E1AE759BF3EE5A54AC8BE90F354B087483CD8B513A85DF85F277",
        "expected_elements": 14087
    },
    "case_2": {
        "rel_path": "case2/PK_F1807_CASE_2_ADAPT_PHYS.inp",
        "file_sha256": "A5CBAEB6BF0E884058A02A1802BCF09792A7E347BFDCE488EF42A1D70A17B39A",
        "body_sha256": "0BD15C96D298964AEC5A518971EEE3E3388C133A09A97E59EB2A84CE15358600",
        "expected_elements": 22656
    },
    "case_3": {
        "rel_path": "case3/PK_F1807_CASE_3_ADAPT_PHYS.inp",
        "file_sha256": "95B6A4543FBD092455533457BD2DB528FBB1EDC7ECF61BA815CC1002D06F967B",
        "body_sha256": "46024F3241F0C6C8B7BC1D051D52D1E00F53EFDABF3FFFB9160FD7E937912B9C",
        "expected_elements": 26746
    },
    "case_5": {
        "rel_path": "case5/PK_F1807_CASE_5_ADAPT_PHYS.inp",
        "file_sha256": "9A5544189255779E9D579BDD4434952ECD6ADA71475F20B4B63CF09DF44DB788",
        "body_sha256": "78009AAEE4FE732C0FA56F2DE5487C1717E82E245B4CAF32C3B9CE19AB2B4065",
        "expected_elements": 15466
    }
}

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def sha256_inp_body(filepath):
    h = hashlib.sha256()
    with open(filepath, "r") as f:
        for line in f:
            if not line.strip().startswith("**"):
                h.update(line.strip().encode("utf-8") + b"\n")
    return h.hexdigest().upper()

def test_f1807_invariants_and_donor_provenance():
    """Verify frozen UEL, frozen shared framework, and all 4 authentic donor ODBs."""
    assert os.path.exists(UEL_PATH), "UEL missing"
    assert sha256_file(UEL_PATH) == FROZEN_UEL_SHA
    assert os.path.exists(FRAMEWORK_PATH), "Framework missing"
    assert sha256_file(FRAMEWORK_PATH) == FROZEN_FRAMEWORK_SHA
    
    for cid, donor_info in EXPECTED_DONORS.items():
        assert os.path.exists(donor_info["path"]), "Donor missing for %s: %s" % (cid, donor_info["path"])
        actual_sha = sha256_file(donor_info["path"])
        if isinstance(donor_info["sha256"], list):
            assert actual_sha in donor_info["sha256"], "Donor hash mismatch for %s" % cid
        else:
            assert actual_sha == donor_info["sha256"], "Donor hash mismatch for %s" % cid

def test_f1807_four_physical_meshes_exist_and_hashes():
    """Verify existence, file SHA-256, and body SHA-256 for all four adapted physical meshes."""
    for cid, minfo in EXPECTED_MESHES.items():
        inp_path = os.path.join(BASE_REGRESSION_DIR, minfo["rel_path"])
        assert os.path.exists(inp_path), "Mesh INP missing for %s: %s" % (cid, inp_path)
        assert sha256_file(inp_path) == minfo["file_sha256"], "File hash mismatch for %s" % cid
        assert sha256_inp_body(inp_path) == minfo["body_sha256"], "Body hash mismatch for %s" % cid

def test_f1807_finite_element_quality_metrics():
    """Verify quad dominance (>=90%), positive Jacobians, and aspect ratios (<=4.0)."""
    assert os.path.exists(RECEIPT_PATH), "Master receipt missing"
    with open(RECEIPT_PATH, "r") as f:
        data = json.load(f)
    
    results = data["regression_results"]
    for cid in ["case_1", "case_2", "case_3", "case_5"]:
        res = results[cid]
        # Quad dominance
        quad_pct = res["element_counts"]["quad_fraction_pct"]
        assert quad_pct >= 90.0, "%s quad fraction %.2f%% < 90%%" % (cid, quad_pct)
        
        # Positive signed Jacobian
        assert res["jacobian"]["status"] == "PASS"
        assert res["jacobian"]["nonpositive_count"] == 0
        assert res["jacobian"]["min_det_j"] > 0
        
        # Aspect ratio bound
        assert res["aspect_ratio"]["status"] == "PASS"
        assert res["aspect_ratio"]["violations_gt_4"] == 0
        assert res["aspect_ratio"]["max"] <= 4.0

def test_f1807_case_specific_resolutions_and_gates():
    """Verify case-specific critical region resolution, targets, and gates."""
    with open(RECEIPT_PATH, "r") as f:
        data = json.load(f)
    results = data["regression_results"]
    
    # Case 1: 14,087 elements (+1.05% vs 13,941 literature target)
    c1 = results["case_1"]
    assert c1["element_counts"]["total_elements"] == 14087
    assert c1["critical_region_metrics"]["tip_pct_le_l0_half"] == 100.0
    assert c1["gate_verdicts"]["GATE_05_CRITICAL_RESOLUTION"] == "PASS"
    
    # Case 2: 22,656 elements (F1806 baseline 22,924)
    c2 = results["case_2"]
    assert c2["element_counts"]["total_elements"] == 22656
    assert c2["critical_region_metrics"]["distal_pct_le_l0_half"] >= 88.0
    assert c2["critical_region_metrics"]["bins"]["bin_5"]["min_h_um"] < 3.75  # < l0/2
    assert c2["gate_verdicts"]["SCIENTIFIC_GATE_OUTER_DISTAL"] == "FAIL"      # Retained as FAIL
    
    # Case 3: 26,746 elements (F1803 baseline)
    c3 = results["case_3"]
    assert c3["element_counts"]["total_elements"] == 26746
    assert c3["critical_region_metrics"]["secondary_corridor_pct_le_l0"] > 50.0  # 54.87%
    assert c3["critical_region_metrics"]["secondary_corridor_pct_le_l0_half"] > 0.0 # 2.44%
    assert c3["critical_region_metrics"]["secondary_corridor_min_h_mm"] < 0.285 / 2.0 # 0.0738 mm < l0/2
    assert c3["gate_verdicts"]["GATE_05_CRITICAL_RESOLUTION"] == "PASS"
    
    # Case 5: 15,466 elements (Literature target: 15,714)
    c5 = results["case_5"]
    assert c5["element_counts"]["total_elements"] == 15466
    assert c5["critical_region_metrics"]["upper_corridor_pct_le_l0"] > 99.0  # 99.14%
    assert c5["gate_verdicts"]["GATE_05_CRITICAL_RESOLUTION"] == "PASS"

def test_f1807_far_field_coarsening_and_efficiency():
    """Verify far-to-core coarsening ratio >= 2.0x for all four benchmarks."""
    with open(RECEIPT_PATH, "r") as f:
        data = json.load(f)
    results = data["regression_results"]
    for cid in ["case_1", "case_2", "case_3", "case_5"]:
        res = results[cid]
        ratio = res["sizing_metrics"]["coarsening_ratio_far_to_core"]
        assert ratio >= 2.0, "%s coarsening ratio %.2f < 2.0x" % (cid, ratio)
        assert res["gate_verdicts"]["GATE_06_FAR_FIELD_COARSENING"] == "PASS"

def test_f1807_receipt_integrity_and_governance():
    """Verify master receipt metadata, zero PBS consumption, and OPEN goal status."""
    with open(RECEIPT_PATH, "r") as f:
        data = json.load(f)
    assert data["task_id"] == "F1807-FOUR-CASE-NATIVE-MISESERI-REGRESSION-AND-QUALITY-EVALUATION"
    assert data["correlation_id"] == "HND-F1807-FOUR-CASE-REGRESSION-001"
    assert data["master_goal_status"] == "OPEN"
    assert data["cumulative_pbs_submissions"] == 35
    assert data["new_pbs_submissions_consumed"] == 0

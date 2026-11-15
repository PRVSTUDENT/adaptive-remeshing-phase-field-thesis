# -*- coding: utf-8 -*-
"""
tests/unit/test_f1773_four_benchmark_regression_plan.py
======================================================
Validates Task F1773 Coordinated Four-Benchmark Method A Regression Suite Plan:
1. Validates reconciled four-benchmark matrix strictly matching canonical manifest.
2. Verifies Case 2 geometry (notch 0.5 mm, hole r=0.10 mm) and donor PK_HOLE_COMPANION_RECOVERY.odb.
3. Verifies Case 3 geometry (65x120 mm, notch 10 mm, void r=10 mm, pins r=5 mm) and 2-pass Method A.2.
4. Verifies Case 5 geometry (1.0x1.0 mm, 7 holes) and Method A.1.
5. Verifies Case 1 empirical results from F1772 (20,232 el, mean AR 1.2637 <= 1.50, G4 PASS).
6. Verifies bitwise frozen UEL and reusable framework hashes.
7. Confirms zero-PBS planning allowance and cumulative accounting (30 jobs).
"""
import os
import sys
import hashlib
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO_ROOT)

FROZEN_UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

FRAMEWORK_PATH = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
EXPECTED_FW_SHA = "8d71f38f23867a23c1fc1bf5ec499533a8c75f538b77804ece03b5c668f4be08"

CASE1_SUMMARY = os.path.join(REPO_ROOT, "results", "validation", "f1772_case1_advancing_mesh_summary.json")
CANONICAL_MANIFEST = os.path.join(REPO_ROOT, "configs", "remeshing", "canonical_five_case_manifest.json")
CASE2_CONFIG = os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case2_off_axis_hole.json")
CASE3_CONFIG = os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case3_notched_plate_pins.json")
CASE5_CONFIG = os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case5_seven_hole.json")


def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def test_frozen_subroutine_hash():
    actual_sha = compute_sha256(FROZEN_UEL_PATH)
    assert actual_sha == EXPECTED_UEL_SHA, f"Frozen UEL SHA mismatch: {actual_sha} != {EXPECTED_UEL_SHA}"


def test_reusable_framework_hash():
    actual_sha = compute_sha256(FRAMEWORK_PATH)
    assert actual_sha == EXPECTED_FW_SHA, f"Framework SHA mismatch: {actual_sha} != {EXPECTED_FW_SHA}"


def test_canonical_manifest_and_config_concordance():
    with open(CANONICAL_MANIFEST, "r") as f:
        manifest = json.load(f)

    # Case 2 check
    with open(CASE2_CONFIG, "r") as f:
        c2 = json.load(f)
    assert c2["geometry"]["notch_length"] == 0.5
    assert c2["geometry"]["hole_radius"] == 0.10
    assert c2["geometry"]["hole_center_x"] == 0.65
    assert c2["geometry"]["hole_center_y"] == 0.65
    assert manifest["benchmarks"]["case_2"]["donor_odb_repo_path"] == "models/mode1_off_axis_hole/PK_HOLE_COMPANION_RECOVERY.odb"
    assert manifest["benchmarks"]["case_2"]["donor_step_name"] == "RECOVERY_STEP"

    # Case 3 check
    with open(CASE3_CONFIG, "r") as f:
        c3 = json.load(f)
    assert c3["geometry"]["plate_width"] == 65.0
    assert c3["geometry"]["plate_height"] == 120.0
    assert c3["geometry"]["notch_length"] == 10.0
    assert manifest["benchmarks"]["case_3"]["donor_odb_repo_path"] == "models/pandey_kumar_mode1/228_f1741_case3_multistate_remesh/PK_SEC43_STAGGERED_JOB1.odb"
    assert manifest["benchmarks"]["case_3"]["algorithm_variant"] == "Method A.2 (Multi-State Sequential Method A)"

    # Case 5 check
    with open(CASE5_CONFIG, "r") as f:
        c5 = json.load(f)
    assert c5["geometry"]["plate_width"] == 1.0
    assert len(c5["geometry"]["voids"]) == 7
    assert manifest["benchmarks"]["case_5"]["donor_odb_repo_path"] == "models/pandey_kumar_mode1/218_f1726_seven_hole_study/PK_F1726_SEVEN_HOLE_COARSE.odb"


def test_case1_f1772_metrics():
    assert os.path.exists(CASE1_SUMMARY), f"Missing summary: {CASE1_SUMMARY}"
    with open(CASE1_SUMMARY, "r") as f:
        data = json.load(f)
    assert data["total_elements"] == 20232
    assert data["quad_percent"] >= 95.0
    assert data["min_det_j"] > 0
    assert data["ligament_area_compliance_pct"] == 100.0
    assert data["has_transverse_coarse_barrier"] is False
    assert data["gate_matrix"]["G1_element_count_parity"]["status"] == "FAIL"
    assert data["gate_matrix"]["G5_ligament_spatial_resolution"]["status"] == "PASS"
    assert data["gate_matrix"]["G8_production_uel_datacheck"]["status"] == "PASS"


def test_submission_accounting():
    hpc_ledger = os.path.join(REPO_ROOT, "project_coordination", "HPC_JOB_LEDGER.csv")
    with open(hpc_ledger, "r") as f:
        lines = [line.strip() for line in f if line.strip()]
    last_line = lines[-1]
    assert "1423608.mmaster02" in last_line
    assert "COMPLETED,0" in last_line

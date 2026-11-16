# -*- coding: utf-8 -*-
"""
tests/unit/test_f1800_case3_precritical_remesh.py
Unit and regression test for Task F1800: Case 3 Precritical Native-MISESERI Scale and Causal Remesh Test.
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

PERMANENT_DIR = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "250_f1800_case3_precritical_remesh"
)
INP_PATH = os.path.join(PERMANENT_DIR, "PK_F1800_CASE_3_ADAPT_PHYS.inp")
DONOR_ODB_PATH = os.path.join(PERMANENT_DIR, "PK_SEC43_PRECRITICAL_RECOVERY.odb")
DONOR_INP_PATH = os.path.join(PERMANENT_DIR, "PK_SEC43_PRECRITICAL_RECOVERY.inp")
DONOR_RECEIPT_PATH = os.path.join(PERMANENT_DIR, "PK_F1800_CASE3_DONOR_QUALIFICATION_RECEIPT.json")
REMESH_RECEIPT_PATH = os.path.join(PERMANENT_DIR, "PK_F1800_CASE3_PRECRITICAL_REMESH_RECEIPT.json")
CONFIG_PATH = os.path.join(REPO_ROOT, "configs", "remeshing", "f1800_case3_native_miseseri.json")
REPORT_PATH = os.path.join(REPO_ROOT, "docs", "validation", "F1800_CASE3_PRECRITICAL_NATIVE_MISESERI_REMESH_REPORT.md")
UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
ACTIVE_TASK_PATH = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_MESH_BODY_SHA256 = "0DAFAD93742A4988AF068070F7BFE72FE71CD3C353506C346584A208E71EF6AC"


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def test_f1800_files_exist():
    """Verify all required artifacts and execution logs exist."""
    assert os.path.exists(INP_PATH), "Physical INP missing"
    assert os.path.exists(DONOR_ODB_PATH), "Precritical donor ODB missing"
    assert os.path.exists(DONOR_INP_PATH), "Precritical donor INP missing"
    assert os.path.exists(DONOR_RECEIPT_PATH), "Donor qualification receipt missing"
    assert os.path.exists(REMESH_RECEIPT_PATH), "Controlled remesh receipt missing"
    assert os.path.exists(CONFIG_PATH), "Configuration JSON missing"
    assert os.path.exists(REPORT_PATH), "Evidentiary report missing"

    log_path = os.path.join(PERMANENT_DIR, "abaqus_cae_execution.log")
    rpy_path = os.path.join(PERMANENT_DIR, "abaqus.rpy")
    assert os.path.exists(log_path), "Abaqus CAE execution log missing"
    assert os.path.exists(rpy_path), "Abaqus CAE journal missing"


def test_f1800_causal_configuration_parsing():
    """Verify that AdaptiveConfig parses causal parameters correctly."""
    from scripts.remeshing.reusable_2d_adaptive_framework import AdaptiveConfig

    cfg = AdaptiveConfig.from_json(CONFIG_PATH)
    assert cfg.causal_mode is True
    assert cfg.max_frame_index == 1
    assert cfg.max_frame_time == 1.0


def test_f1800_donor_receipt():
    """Verify donor qualification receipt fields."""
    with open(DONOR_RECEIPT_PATH, "r") as f:
        d = json.load(f)

    assert d["task_id"] == "F1800-CASE3-PRECRITICAL-NATIVE-MISESERI-SCALE-AND-CAUSAL-REMESH-TEST"
    assert d["benchmark_case"] == "case_3"
    assert d["step_name"] == "RECOVERY_STEP"
    assert d["frame_index"] == 1
    assert d["frame_time"] == 1.0
    assert d["causal_verification"]["causal_mode"] is True
    assert d["causal_verification"]["max_frame_index"] == 1
    assert d["causal_verification"]["temporal_horizon_enforced"] is True
    assert d["precritical_state_characterization"]["prescribed_displacement_uy_mm"] == 0.05
    assert d["precritical_state_characterization"]["physical_regime"] == "PRECRITICAL_ELASTIC_UNDAMAGED"
    assert d["qualification_status"] == "QUALIFIED_AUTHENTIC_PRECRITICAL_NATIVE_DONOR"


def test_f1800_remesh_receipt_and_mesh_invariants():
    """Verify physical mesh quality and baseline comparison."""
    with open(REMESH_RECEIPT_PATH, "r") as f:
        r = json.load(f)

    assert r["task_id"] == "F1800-CASE3-PRECRITICAL-NATIVE-MISESERI-SCALE-AND-CAUSAL-REMESH-TEST"
    mesh = r["physical_mesh"]
    assert mesh["total_elements"] == 27014
    assert mesh["total_nodes"] == 27069
    assert mesh["quad_count"] == 26238
    assert mesh["tri_count"] == 776
    assert mesh["quad_percent"] >= 97.0
    assert mesh["min_det_j"] > 0.0
    assert mesh["non_positive_jacobians"] == 0
    assert mesh["zero_negative_jacobians"] is True
    assert mesh["max_aspect_ratio"] <= 3.0
    assert 20.0 <= mesh["min_corner_angle_deg"] <= 35.0
    assert 130.0 <= mesh["max_corner_angle_deg"] <= 150.0

    # Verify mesh body hash
    with open(INP_PATH, "r") as f:
        lines = f.readlines()
    h_body = hashlib.sha256()
    for line in lines:
        if not line.strip().startswith("**"):
            h_body.update(line.strip().encode("utf-8") + b"\n")
    actual_body_sha256 = h_body.hexdigest().upper()
    assert actual_body_sha256 == EXPECTED_MESH_BODY_SHA256
    assert mesh["mesh_body_sha256"] == EXPECTED_MESH_BODY_SHA256

    # Verify baseline comparison vs F1799
    base = r["baseline_comparison"]
    assert base["f1799_baseline"]["is_body_identical"] is False
    assert base["f1799_baseline"]["delta_elements"] == 123
    assert base["f1799_baseline"]["parity_percent"] == 100.46

    # Verify spatial resolution metrics
    sp = r["spatial_resolution"]
    assert sp["primary_corridor_notch_to_hole"]["count"] == 5921
    assert sp["primary_corridor_notch_to_hole"]["pct_le_l0"] >= 55.0
    assert sp["primary_corridor_notch_to_hole"]["pct_le_l0_half"] >= 15.0
    assert pytest.approx(sp["primary_corridor_notch_to_hole"]["mean_mm"], rel=1e-2) == 0.2942

    assert sp["secondary_corridor_hole_to_boundary"]["count"] == 888
    assert sp["secondary_corridor_hole_to_boundary"]["pct_le_l0"] == 1.24
    assert sp["secondary_corridor_hole_to_boundary"]["pct_le_l0_half"] == 0.0

    assert sp["far_field_background"]["count"] == 2113
    assert sp["far_to_core_coarsening_ratio"] >= 3.0

    # Verify quality gates
    qg = r["quality_gates"]
    assert qg["GATE_01_NATIVE_EXECUTION_EXIT_0"] == "PASS"
    assert qg["GATE_02_QUAD_FRACTION_GE_90_PCT"] == "PASS"
    assert qg["GATE_03_ZERO_NEGATIVE_JACOBIANS"] == "PASS"
    assert qg["GATE_04_ASPECT_RATIO_LE_4"] == "PASS"
    assert qg["GATE_05_PRIMARY_CORRIDOR_RESOLUTION"] == "FAIL"
    assert qg["GATE_06_FAR_FIELD_COARSENING"] == "PASS"
    assert qg["GATE_07_EFFICIENCY_VS_HISTORICAL_EXPLOSION"] == "FAIL"


def test_f1800_governance_invariants():
    """Verify frozen UEL and zero new PBS submissions."""
    assert os.path.exists(UEL_PATH), "Production UEL missing"
    assert sha256_file(UEL_PATH) == FROZEN_UEL_SHA256, "UEL hash must match frozen baseline"

    assert os.path.exists(ACTIVE_TASK_PATH), "ACTIVE_TASK.json missing"
    with open(ACTIVE_TASK_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["task_id"] in [
        "F1800-CASE3-PRECRITICAL-NATIVE-MISESERI-SCALE-AND-CAUSAL-REMESH-TEST",
        "F1801-CASE3-NATIVE-MISESERI-ERROR-TARGET-EFFICIENCY-TEST",
        "F1802-CASE3-METHOD-A2-EVOLVING-RECOVERY-DONOR-QUALIFICATION-AND-CAUSAL-REMESH",
        "F1803-CASE3-STATE2-DEGRADED-MODULUS-FIDELITY-NATIVE-REMESH",
        "F1804-CASE2-DISTAL-DEGRADED-MODULUS-RECOVERY-REMESH"
    ]
    assert data["max_new_pbs_submissions"] == 0
    assert data["submissions_consumed"] == 0
    assert data["cumulative_pbs_submissions"] == 35
    assert data["master_goal_status"] == "OPEN"

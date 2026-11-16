# -*- coding: utf-8 -*-
"""
tests/unit/test_f1799_case3_controlled_remesh.py
Unit and regression test for Task F1799: Case 3 Causal Configuration & Controlled Remeshing.
"""

import os
import csv
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

PERMANENT_DIR = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "249_f1799_case3_controlled_remesh"
)
INP_PATH = os.path.join(PERMANENT_DIR, "PK_F1799_CASE_3_ADAPT_PHYS.inp")
DONOR_RECEIPT_PATH = os.path.join(PERMANENT_DIR, "PK_F1799_CASE3_DONOR_QUALIFICATION_RECEIPT.json")
REMESH_RECEIPT_PATH = os.path.join(PERMANENT_DIR, "PK_F1799_CASE3_CONTROLLED_REMESH_RECEIPT.json")
CONFIG_PATH = os.path.join(REPO_ROOT, "configs", "remeshing", "f1799_case3_native_miseseri.json")
REPORT_PATH = os.path.join(REPO_ROOT, "docs", "validation", "F1799_CASE3_CAUSAL_CONFIG_CONTROLLED_REMESH_REPORT.md")
UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
ACTIVE_TASK_PATH = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_MESH_BODY_SHA256 = "13B6770FC30025CBB1D2CC5ACC1D50F98CE6D5F58F5300BB70158A39E232F7B6"


def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def test_f1799_files_exist():
    """Verify all required artifacts and execution logs exist."""
    assert os.path.exists(INP_PATH), "Physical INP missing"
    assert os.path.exists(DONOR_RECEIPT_PATH), "Donor qualification receipt missing"
    assert os.path.exists(REMESH_RECEIPT_PATH), "Controlled remesh receipt missing"
    assert os.path.exists(CONFIG_PATH), "Configuration JSON missing"
    assert os.path.exists(REPORT_PATH), "Evidentiary report missing"

    log_path = os.path.join(PERMANENT_DIR, "abaqus_cae_execution.log")
    rpy_path = os.path.join(PERMANENT_DIR, "abaqus.rpy")
    assert os.path.exists(log_path), "Abaqus CAE execution log missing"
    assert os.path.exists(rpy_path), "Abaqus CAE journal missing"


def test_f1799_causal_configuration_parsing():
    """Verify that AdaptiveConfig parses causal parameters correctly."""
    from scripts.remeshing.reusable_2d_adaptive_framework import AdaptiveConfig

    cfg = AdaptiveConfig.from_json(CONFIG_PATH)
    assert cfg.causal_mode is True
    assert cfg.max_frame_index == 1
    assert cfg.max_frame_time == 1.0


def test_f1799_donor_receipt():
    """Verify donor qualification receipt fields."""
    with open(DONOR_RECEIPT_PATH, "r") as f:
        d = json.load(f)

    assert d["task_id"] == "F1799-CASE3-CAUSAL-CONFIG-AND-PHYSICAL-DONOR-CONTROLLED-REMESH"
    assert d["benchmark_case"] == "case_3"
    assert d["step_name"] == "RECOVERY_STEP"
    assert d["frame_index"] == 1
    assert d["frame_time"] == 1.0
    assert d["causal_verification"]["causal_mode"] is True
    assert d["causal_verification"]["max_frame_index"] == 1
    assert d["causal_verification"]["temporal_horizon_enforced"] is True
    assert "material_unit_reconciliation" in d
    assert "displacement_chronology_resolution" in d
    assert d["qualification_status"] == "QUALIFIED_AUTHENTIC_INITIAL_STATE_NATIVE_DONOR"


def test_f1799_remesh_receipt_and_mesh_invariants():
    """Verify physical mesh quality and baseline comparison."""
    with open(REMESH_RECEIPT_PATH, "r") as f:
        r = json.load(f)

    assert r["task_id"] == "F1799-CASE3-CAUSAL-CONFIG-AND-PHYSICAL-DONOR-CONTROLLED-REMESH"
    mesh = r["physical_mesh"]
    assert mesh["total_elements"] == 26891
    assert mesh["total_nodes"] == 26961
    assert mesh["quad_count"] == 26145
    assert mesh["tri_count"] == 746
    assert mesh["quad_percent"] >= 97.0
    assert mesh["min_det_j"] > 0.0
    assert mesh["non_positive_jacobians"] == 0
    assert mesh["zero_negative_jacobians"] is True
    assert mesh["max_aspect_ratio"] <= 3.0
    assert 20.0 <= mesh["min_corner_angle_deg"] <= 40.0
    assert 120.0 <= mesh["max_corner_angle_deg"] <= 150.0

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

    # Verify baseline parity with F1798
    base = r["baseline_comparison"]
    assert base["f1798_baseline"]["is_identical_mesh"] is True
    assert base["f1798_baseline"]["delta_elements"] == 0
    assert base["f1798_baseline"]["parity_percent"] == 100.0

    # Verify spatial resolution metrics
    sp = r["spatial_resolution"]
    assert sp["primary_corridor_notch_to_hole"]["count"] == 5888
    assert sp["primary_corridor_notch_to_hole"]["pct_le_l0"] == 57.05
    assert sp["primary_corridor_notch_to_hole"]["pct_le_l0_half"] == 15.03
    assert pytest.approx(sp["primary_corridor_notch_to_hole"]["mean_mm"], rel=1e-3) == 0.2950

    assert sp["secondary_corridor_hole_to_boundary"]["count"] == 890
    assert sp["secondary_corridor_hole_to_boundary"]["pct_le_l0"] == 1.24
    assert sp["secondary_corridor_hole_to_boundary"]["pct_le_l0_half"] == 0.0
    assert pytest.approx(sp["secondary_corridor_hole_to_boundary"]["mean_mm"], rel=1e-3) == 0.6273

    assert sp["far_field_background"]["count"] == 2074
    assert sp["far_field_background"]["pct_le_l0"] == 0.82
    assert pytest.approx(sp["far_field_background"]["mean_mm"], rel=1e-3) == 0.9239
    assert sp["far_to_core_coarsening_ratio"] == 3.13

    # Verify quality gates
    qg = r["quality_gates"]
    assert qg["GATE_01_NATIVE_EXECUTION_EXIT_0"] == "PASS"
    assert qg["GATE_02_QUAD_FRACTION_GE_90_PCT"] == "PASS"
    assert qg["GATE_03_ZERO_NEGATIVE_JACOBIANS"] == "PASS"
    assert qg["GATE_04_ASPECT_RATIO_LE_4"] == "PASS"
    assert qg["GATE_05_PRIMARY_CORRIDOR_RESOLUTION"] == "FAIL"
    assert qg["GATE_06_FAR_FIELD_COARSENING"] == "PASS"
    assert qg["GATE_07_EFFICIENCY_VS_HISTORICAL_EXPLOSION"] == "FAIL"


def test_f1799_authoritative_shoelace_recalculation():
    """Independently recalculate quadrilateral areas from node coordinates and connectivity."""
    import math

    nodes = {}
    elements = {}
    in_nodes = False
    in_elems = False

    with open(INP_PATH, "r") as f:
        for line in f:
            l_str = line.strip()
            u_str = l_str.upper()
            if u_str.startswith("*NODE") and "OUTPUT" not in u_str:
                in_nodes = True
                in_elems = False
                continue
            elif u_str.startswith("*ELEMENT") and "OUTPUT" not in u_str:
                in_nodes = False
                in_elems = True
                continue
            elif u_str.startswith("*"):
                in_nodes = False
                in_elems = False
                continue

            if in_nodes and l_str:
                parts = l_str.split(",")
                if len(parts) >= 3:
                    try:
                        nodes[int(parts[0].strip())] = (float(parts[1].strip()), float(parts[2].strip()))
                    except ValueError:
                        pass
            elif in_elems and l_str:
                parts = l_str.split(",")
                if len(parts) >= 4:
                    try:
                        elements[int(parts[0].strip())] = [int(p.strip()) for p in parts[1:] if p.strip()]
                    except ValueError:
                        pass

    primary_h = []
    secondary_h = []
    far_field_h = []

    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if not pts:
            continue
        cx = sum([p[0] for p in pts]) / float(len(pts))
        cy = sum([p[1] for p in pts]) / float(len(pts))

        if len(pts) == 4:
            area = 0.5 * abs(
                (pts[0][0]*pts[1][1] - pts[1][0]*pts[0][1]) +
                (pts[1][0]*pts[2][1] - pts[2][0]*pts[1][1]) +
                (pts[2][0]*pts[3][1] - pts[3][0]*pts[2][1]) +
                (pts[3][0]*pts[0][1] - pts[0][0]*pts[3][1])
            )
        elif len(pts) == 3:
            area = 0.5 * abs(
                (pts[0][0]*(pts[1][1] - pts[2][1])) +
                (pts[1][0]*(pts[2][1] - pts[0][1])) +
                (pts[2][0]*(pts[0][1] - pts[1][1]))
            )
        else:
            area = 0.0
        h_elem = math.sqrt(area) if area > 0 else 0.0

        if 10.0 <= cx <= 36.5 and 45.0 <= cy <= 75.0:
            primary_h.append(h_elem)
        elif 46.5 <= cx <= 65.0 and 40.0 <= cy <= 62.0:
            secondary_h.append(h_elem)
        elif cy <= 15.0 or cy >= 105.0:
            far_field_h.append(h_elem)

    l0 = 0.285
    l0_half = l0 / 2.0
    assert len(primary_h) == 5888
    assert pytest.approx(sum(primary_h)/len(primary_h), rel=1e-4) == 0.295017
    assert pytest.approx(len([h for h in primary_h if h <= l0])/float(len(primary_h))*100.0, rel=1e-2) == 57.05
    assert pytest.approx(len([h for h in primary_h if h <= l0_half])/float(len(primary_h))*100.0, rel=1e-2) == 15.03

    assert len(secondary_h) == 890
    assert pytest.approx(sum(secondary_h)/len(secondary_h), rel=1e-4) == 0.627337
    assert pytest.approx(len([h for h in secondary_h if h <= l0])/float(len(secondary_h))*100.0, rel=1e-2) == 1.24

    assert len(far_field_h) == 2074
    assert pytest.approx(sum(far_field_h)/len(far_field_h), rel=1e-4) == 0.923949
    ratio = (sum(far_field_h)/len(far_field_h)) / (sum(primary_h)/len(primary_h))
    assert pytest.approx(ratio, rel=1e-2) == 3.13


def test_f1799_governance_invariants():
    """Verify frozen UEL and zero new PBS submissions."""
    assert os.path.exists(UEL_PATH), "Production UEL missing"
    assert sha256_file(UEL_PATH) == FROZEN_UEL_SHA256, "UEL hash must match frozen baseline"

    assert os.path.exists(ACTIVE_TASK_PATH), "ACTIVE_TASK.json missing"
    with open(ACTIVE_TASK_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["task_id"] in (
        "F1799-CASE3-CAUSAL-CONFIG-AND-PHYSICAL-DONOR-CONTROLLED-REMESH",
        "F1800-CASE3-PRECRITICAL-NATIVE-MISESERI-SCALE-AND-CAUSAL-REMESH-TEST",
        "F1801-CASE3-NATIVE-MISESERI-ERROR-TARGET-EFFICIENCY-TEST",
        "F1802-CASE3-METHOD-A2-EVOLVING-RECOVERY-DONOR-QUALIFICATION-AND-CAUSAL-REMESH",
        "F1803-CASE3-STATE2-DEGRADED-MODULUS-FIDELITY-NATIVE-REMESH"
    )
    assert data["max_new_pbs_submissions"] == 0
    assert data["submissions_consumed"] == 0
    assert data["cumulative_pbs_submissions"] == 35
    assert data["master_goal_status"] == "OPEN"

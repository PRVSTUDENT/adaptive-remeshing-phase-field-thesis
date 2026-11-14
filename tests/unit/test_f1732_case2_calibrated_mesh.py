# -*- coding: utf-8 -*-
"""
test_f1732_case2_calibrated_mesh.py
===================================
Unit regression test suite for Task F1732 Case 2 Calibrated Adaptive Remeshing Experiment (eta = 3.80%).
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "223_f1732_case2_calibrated")
EVIDENCE_DIR = os.path.join(REPO_ROOT, "results", "validation", "f1732_case2_calibrated_evidence")
SUMMARY_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1732_case2_calibrated_summary.json")
FROZEN_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def get_file_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().lower()

def test_f1732_staged_artifacts_exist_and_hashes_valid():
    config_path = os.path.join(PKG_DIR, "f1732_case2_off_axis_hole.json")
    pbs_path = os.path.join(PKG_DIR, "submit_f1732_case2_calibrated.pbs")
    audit_path = os.path.join(PKG_DIR, "audit_case2_calibrated_resolution.py")
    uel_path = os.path.join(PKG_DIR, "f42_mixed_uel.for")

    assert os.path.isfile(config_path), f"Missing config: {config_path}"
    assert os.path.isfile(pbs_path), f"Missing PBS script: {pbs_path}"
    assert os.path.isfile(audit_path), f"Missing audit script: {audit_path}"
    assert os.path.isfile(uel_path), f"Missing UEL source: {uel_path}"

    actual_uel_sha = get_file_sha256(uel_path)
    assert actual_uel_sha == FROZEN_UEL_SHA, f"Frozen UEL SHA mismatch! {actual_uel_sha} != {FROZEN_UEL_SHA}"

def test_f1732_config_parameters_and_geometry():
    config_path = os.path.join(PKG_DIR, "f1732_case2_off_axis_hole.json")
    with open(config_path, "r", encoding="utf-8-sig") as f:
        cfg = json.load(f)

    assert cfg["case_id"] == "case_2"
    assert cfg["geometry"]["plate_width"] == 1.0
    assert cfg["geometry"]["plate_height"] == 1.0
    assert cfg["geometry"]["notch_length"] == 0.5
    assert cfg["geometry"]["hole_center_x"] == 0.65
    assert cfg["geometry"]["hole_center_y"] == 0.65
    assert cfg["geometry"]["hole_radius"] == 0.10

    rr = cfg["remeshing_rule"]
    assert rr["error_target"] == 3.80, f"Error target must be calibrated to 3.80%, got {rr['error_target']}"
    assert rr["min_element_size_mm"] == 0.0015
    assert rr["max_element_size_mm"] == 0.020
    assert rr["step_name"] == "RECOVERY_STEP"
    assert rr["variable"] == "MISESERI"

def test_f1732_pbs_script_directives_and_gates():
    pbs_path = os.path.join(PKG_DIR, "submit_f1732_case2_calibrated.pbs")
    with open(pbs_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    content = "".join(lines)

    assert "#PBS -N F1732_CASE2_CALIB" in content
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in content
    assert "#PBS -q entry_imfdfkmq" in content
    assert "#PBS -m abe" in content
    assert "#PBS -M pr21vyci@mailserver.tu-freiberg.de" in content
    assert "reusable_2d_adaptive_framework.py" in content
    assert "audit_case2_calibrated_resolution.py" in content
    assert "PK_HOLE_COMPANION_RECOVERY.odb" in content
    assert FROZEN_UEL_SHA in content
    assert "abaqus datacheck job=PK_F1732_CASE_2_DC" in content

def test_f1732_spatial_auditor_logic():
    audit_path = os.path.join(PKG_DIR, "audit_case2_calibrated_resolution.py")
    with open(audit_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "mutually_exclusive_partition" in content
    assert "overlapping_diagnostic_windows" in content
    assert "along_path_trajectory_stations" in content
    assert "P1_NOTCH_ROOT" in content
    assert "P2_PRIMARY_CORRIDOR_EXCL_NOTCH" in content
    assert "P3_HOLE_RING_EXCL_CORRIDOR" in content
    assert "P4_FAR_FIELD_BULK" in content
    assert "W1_FULL_NOTCH_ROOT" in content
    assert "W2_FULL_PRIMARY_CORRIDOR" in content
    assert "W3_FULL_HOLE_RING" in content
    assert "W4_UNCRACKED_LIGAMENT" in content

def test_f1732_summary_all_gates_pass():
    assert os.path.isfile(SUMMARY_JSON), f"Missing summary JSON: {SUMMARY_JSON}"
    with open(SUMMARY_JSON, "r", encoding="utf-8-sig") as f:
        summary = json.load(f)

    assert summary["all_gates_pass"] == True
    gates = summary["gates"]
    assert gates["GATE-01-REMESH-EXECUTION"] == "PASS"
    assert gates["GATE-02-FE-QUALITY"] == "PASS"
    assert gates["GATE-03-CORRIDOR-RESOLUTION-L0-HALF"] == "PASS"
    assert gates["GATE-04-HOLE-BOUNDARY-RESOLUTION-L0"] == "PASS"
    assert gates["GATE-05-PROD-DECK-ASSEMBLY"] == "PASS"
    assert gates["GATE-06-DATACHECK-EXIT-0"] == "PASS"
    assert gates["GATE-07-UEL-VERIFICATION"] == "PASS"

def test_f1732_mesh_metrics_quad_fraction_and_jacobians():
    with open(SUMMARY_JSON, "r", encoding="utf-8-sig") as f:
        summary = json.load(f)

    mm = summary["mesh_metrics"]
    assert mm["total_physical_elements"] == 8783
    assert mm["total_nodes"] == 8884
    assert mm["quad_fraction_pct"] >= 97.0
    assert mm["min_signed_jacobian"] > 0.0
    assert mm["non_positive_jacobians"] == 0
    assert mm["mean_aspect_ratio"] < 1.5
    assert mm["max_aspect_ratio"] < 3.0

def test_f1732_mutually_exclusive_partition_sum():
    with open(SUMMARY_JSON, "r", encoding="utf-8-sig") as f:
        summary = json.load(f)

    part = summary["mesh_metrics"]["mutually_exclusive_partition"]
    p1 = part["P1_NOTCH_ROOT"]["count"]
    p2 = part["P2_PRIMARY_CORRIDOR_EXCL_NOTCH"]["count"]
    p3 = part["P3_HOLE_RING_EXCL_CORRIDOR"]["count"]
    p4 = part["P4_FAR_FIELD_BULK"]["count"]

    assert p1 == 149
    assert p2 == 1446
    assert p3 == 729
    assert p4 == 6459
    assert (p1 + p2 + p3 + p4) == 8783, "Mutually exclusive partition must sum exactly to 8783!"

def test_f1732_spatial_resolution_corridor_and_along_path():
    with open(SUMMARY_JSON, "r", encoding="utf-8-sig") as f:
        summary = json.load(f)

    windows = summary["mesh_metrics"]["overlapping_diagnostic_windows"]
    w2 = windows["W2_FULL_PRIMARY_CORRIDOR"]
    # Corridor mean h must be <= l0/2 = 3.75 um
    assert w2["mean_h_area_um"] < 3.75, f"Expected corridor mean h <= 3.75 um, got {w2['mean_h_area_um']}"
    assert w2["pct_le_l0_half"] >= 80.0, f"Expected >= 80% <= l0/2, got {w2['pct_le_l0_half']}"
    assert w2["pct_le_l0"] >= 99.0

    stations = summary["mesh_metrics"]["along_path_trajectory_stations"]
    assert len(stations) == 10
    # Stations 1-3 must have 100% of elements <= l0/2
    for s in stations[:3]:
        assert s["pct_le_l0_half"] == 100.0
        assert s["mean_h_area_um"] < 2.50

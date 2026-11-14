# -*- coding: utf-8 -*-
"""
tests/unit/test_f1731_case2_adaptive_mesh.py
=============================================
Unit test suite for Task F1731: Case 2 Exploratory Native Abaqus Remeshing Pilot & Spatial Resolution Audit.
"""

import os
import sys
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CONFIG_JSON = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "222_f1731_case2_pilot", "f1731_case2_off_axis_hole.json")
PBS_SCRIPT = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "222_f1731_case2_pilot", "submit_f1731_case2_pilot.pbs")
AUDIT_PY = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "222_f1731_case2_pilot", "audit_case2_ligament_resolution.py")
UEL_FILE = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "222_f1731_case2_pilot", "f42_mixed_uel.for")
SUMMARY_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1731_case2_pilot_summary.json")
SPATIAL_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1731_case2_pilot_evidence", "f1731_case2_ligament_spatial_audit.json")
REPORT_MD = os.path.join(REPO_ROOT, "docs", "validation", "F1731_CASE2_ADAPTIVE_MESH_REPORT.md")
DC_DAT = os.path.join(REPO_ROOT, "results", "validation", "f1731_case2_pilot_evidence", "PK_F1731_CASE_2_DC.dat")
GEN_MESH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "222_f1731_case2_pilot", "PK_F1728_CASE_2_ADAPT_PHYS.inp")

EXPECTED_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def test_f1731_staged_artifacts_exist_and_hashes_valid():
    """Verify all staged pilot files exist locally with valid hashes."""
    assert os.path.isfile(CONFIG_JSON), "Config JSON missing: %s" % CONFIG_JSON
    assert os.path.isfile(PBS_SCRIPT), "PBS script missing: %s" % PBS_SCRIPT
    assert os.path.isfile(AUDIT_PY), "Audit script missing: %s" % AUDIT_PY
    assert os.path.isfile(UEL_FILE), "UEL source missing: %s" % UEL_FILE

    with open(UEL_FILE, "rb") as f:
        actual_uel_sha = hashlib.sha256(f.read()).hexdigest().lower()
    assert actual_uel_sha == EXPECTED_UEL_SHA, "UEL SHA mismatch: %s vs %s" % (actual_uel_sha, EXPECTED_UEL_SHA)

def test_f1731_config_parameters_and_geometry():
    """Verify Case 2 configuration contains correct physical parameters."""
    with open(CONFIG_JSON, "r") as f:
        cfg = json.load(f)

    assert cfg["case_id"] == "case_2"
    assert cfg["geometry_type"] == "OFF_AXIS_HOLE_PLATE"
    assert cfg["geometry"]["plate_width"] == 1.0
    assert cfg["geometry"]["plate_height"] == 1.0
    assert cfg["geometry"]["hole_center_x"] == 0.65
    assert cfg["geometry"]["hole_center_y"] == 0.65
    assert cfg["geometry"]["hole_radius"] == 0.10
    assert cfg["material"]["length_scale_l0_mm"] == 0.0075
    assert cfg["material"]["youngs_modulus_mpa"] == 210000.0

    rr = cfg["remeshing_rule"]
    assert rr["step_name"] == "RECOVERY_STEP"
    assert rr["variable"] == "MISESERI"
    assert rr["sizing_method"] == "UNIFORM_ERROR"
    assert rr["min_element_size_mm"] == 0.0015
    assert rr["max_element_size_mm"] == 0.020

def test_f1731_pbs_script_directives_and_gates():
    """Verify PBS script directives, preflight checks, and commands."""
    with open(PBS_SCRIPT, "r") as f:
        content = f.read()

    assert "#PBS -N F1731_CASE2_PILOT" in content
    assert "#PBS -q entry_imfdfkmq" in content
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in content
    assert "#PBS -l walltime=01:00:00" in content
    assert "#PBS -m abe" in content
    assert "reusable_2d_adaptive_framework.py" in content
    assert "PK_HOLE_COMPANION_RECOVERY.odb" in content
    assert "abaqus cae noGUI=" in content
    assert "audit_case2_ligament_resolution.py" in content
    assert "abaqus datacheck" in content
    assert "EXPECTED_UEL_SHA=\"ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6\"" in content
    assert "EXPECTED_DONOR_SHA=\"a6514fb8c07c3b855bb4ba841fdb20a9ae8a1c887a6e6ad1a397ba34222ab856\"" in content

def test_f1731_spatial_auditor_logic():
    """Verify audit_case2_ligament_resolution functions."""
    sys.path.insert(0, os.path.dirname(AUDIT_PY))
    import audit_case2_ligament_resolution as auditor

    assert hasattr(auditor, "parse_inp_mesh")
    assert hasattr(auditor, "compute_element_metrics")
    assert hasattr(auditor, "classify_spatial_region")
    assert hasattr(auditor, "audit_mesh")

    # Test spatial classification
    assert auditor.classify_spatial_region(0.51, 0.50) == "NOTCH_ROOT"
    assert auditor.classify_spatial_region(0.58, 0.53) == "PRIMARY_OBLIQUE_LIGAMENT"
    assert auditor.classify_spatial_region(0.65, 0.55) == "HOLE_BOUNDARY_RING"
    assert auditor.classify_spatial_region(0.85, 0.65) == "SECONDARY_RIGHT_LIGAMENT"
    assert auditor.classify_spatial_region(0.10, 0.10) == "FAR_FIELD_BULK"

def test_f1731_collected_pilot_receipts_and_gates():
    """Verify collected pilot receipts, mesh metrics, and execution gates."""
    assert os.path.isfile(SUMMARY_JSON), "Summary JSON missing: %s" % SUMMARY_JSON
    assert os.path.isfile(SPATIAL_JSON), "Spatial JSON missing: %s" % SPATIAL_JSON
    assert os.path.isfile(DC_DAT), "Datacheck DAT missing: %s" % DC_DAT
    assert os.path.isfile(GEN_MESH), "Generated mesh missing: %s" % GEN_MESH

    with open(SUMMARY_JSON, "r", encoding="utf-8-sig") as f:
        summary = json.load(f)

    assert summary["task_id"] == "F1731-CASE2-ADAPTIVE-MESH-GENERATION"
    assert summary["job_id"] == "1423257.mmaster02"

    gates = summary["gates"]
    assert gates["GATE-01-REMESH-EXECUTION"] == "PASS"
    assert gates["GATE-02-FE-QUALITY"] == "PASS"
    assert gates["GATE-03-CORRIDOR-RESOLUTION-L0-HALF"] == "FAIL_DOCUMENTED_DEFICIENCY"
    assert gates["GATE-04-HOLE-BOUNDARY-RESOLUTION-L0"] == "FAIL_DOCUMENTED_DEFICIENCY"
    assert gates["GATE-05-PROD-DECK-ASSEMBLY"] == "PASS"
    assert gates["GATE-06-DATACHECK-EXIT-0"] == "PASS"
    assert gates["GATE-07-UEL-VERIFICATION"] == "PASS"

    mesh_m = summary["mesh_metrics"]
    assert mesh_m["total_physical_elements"] == 3851
    assert mesh_m["total_nodes"] == 3945
    assert mesh_m["quad_fraction_pct"] > 95.0
    assert mesh_m["min_signed_jacobian"] > 0.0
    assert mesh_m["non_positive_jacobians"] == 0

    with open(DC_DAT, "r", encoding="utf-8-sig", errors="replace") as f:
        dat_content = f.read()
    assert "ANALYSIS DATACHECK COMPLETE" in dat_content

def test_f1731_report_content_and_provenance():
    """Verify F1731 report contains required technical and governance elements."""
    assert os.path.isfile(REPORT_MD), "Report markdown missing: %s" % REPORT_MD
    with open(REPORT_MD, "r") as f:
        content = f.read()

    assert "F1731-CASE2-ADAPTIVE-MESH-GENERATION" in content
    assert "1423257.mmaster02" in content
    assert "3,851" in content
    assert "96.70%" in content
    assert "10.30" in content
    assert "5.97" in content
    assert "ANALYSIS DATACHECK COMPLETE" in content
    assert "GATE-01" in content
    assert "GATE-07" in content

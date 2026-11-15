# -*- coding: utf-8 -*-
"""
tests/unit/test_f1764_case5_pilot_specification.py
===================================================
Pre-execution qualification unit test suite for Task F1764:
Case 5 (Seven-Hole Plate, Section 4.6) Single-Pass Common-Framework Pilot Specification.
"""
import os
import sys
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO_ROOT)

FROZEN_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"
FRAMEWORK_VALID_BLOB_SHAS = {
    "399e048ac1374afe46ad254f2a23823d6f0df09d",  # F1763/F1764 single-pass baseline
    "0dd5fe394ea567e2dd99ba9c9a88c235ba80e465",  # F1767 multi-pass Method A.2 support
}
CASE5_DONOR_SHA = "c7f5b4a6864639b7df396210649ccfa9619408b0a4f26e63eac31487755bc6a9"


def test_f1764_pilot_pbs_script_directives():
    """Verify scheduler directives and integrity guards in Case 5 pilot PBS script."""
    pbs_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "237_f1764_case5_pilot", "submit_f1764_case5_pilot.pbs")
    assert os.path.exists(pbs_path), "submit_f1764_case5_pilot.pbs must exist"

    with open(pbs_path, "r") as f:
        content = f.read()

    assert "#PBS -N F1764_C5_PILOT" in content
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in content
    assert "#PBS -l walltime=01:00:00" in content
    assert "#PBS -q entry_imfdfkmq" in content
    assert "#PBS -m abe" in content
    assert "pr21vyci@mailserver.tu-freiberg.de" in content
    assert FROZEN_UEL_SHA in content.lower()
    assert "reusable_2d_adaptive_framework.py" in content
    assert "f1728_case5_seven_hole.json" in content
    assert "PK_F1726_SEVEN_HOLE_COARSE.odb" in content
    assert "audit_case5_ligament_resolution.py" in content
    assert "PK_F1728_CASE_5_ADAPT_PHYS.inp" in content


def test_f1764_donor_odb_availability():
    """Verify local presence and non-empty size of authentic Case 5 donor ODB."""
    odb_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_COARSE.odb")
    assert os.path.exists(odb_path), "Local Case 5 donor ODB must exist"
    size_mb = os.path.getsize(odb_path) / (1024 * 1024)
    assert size_mb > 150.0, "Donor ODB must be > 150 MB (observed: %.1f MB)" % size_mb


def test_f1764_case5_config_integrity():
    """Verify configuration parameters match Pandey & Kumar (2025) Sec. 4.6 and F1726."""
    config_path = os.path.join(REPO_ROOT, "configs", "remeshing", "f1728_case5_seven_hole.json")
    assert os.path.exists(config_path), "f1728_case5_seven_hole.json must exist"

    with open(config_path, "r") as f:
        cfg = json.load(f)

    assert cfg["case_id"] == "case_5"
    assert cfg["geometry_type"] == "SEVEN_HOLE_PLATE"
    assert len(cfg["geometry"]["voids"]) == 7
    assert cfg["material"]["length_scale_l0_mm"] == 0.008
    assert cfg["remeshing_rule"]["error_target"] == 5.68
    assert cfg["remeshing_rule"]["coarsening_factor"] == "NOT_ALLOWED"
    assert cfg["remeshing_rule"]["output_frequency"] == "ALL_INCREMENTS"
    assert cfg["published_benchmark"]["target_elements"] == 15714


def test_f1764_audit_script_on_reference_mesh():
    """Verify Case 5 spatial audit script against historical 15,708-element mesh."""
    audit_script = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "237_f1764_case5_pilot", "audit_case5_ligament_resolution.py")
    assert os.path.exists(audit_script), "audit_case5_ligament_resolution.py must exist"

    ref_mesh = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_ADAPTED_PHYS.inp")
    assert os.path.exists(ref_mesh), "F1726 reference mesh must exist"

    import importlib.util
    spec = importlib.util.spec_from_file_location("audit_case5", audit_script)
    audit_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit_mod)

    nodes, elements, elem_types = audit_mod.parse_inp_mesh(ref_mesh)
    metrics = audit_mod.compute_case5_metrics(nodes, elements, elem_types, l0=0.008)

    assert metrics["total_elements"] == 15708
    assert metrics["quad_percentage"] >= 97.0
    assert metrics["jacobian_valid"] is True
    assert metrics["negative_jacobians"] == 0
    assert metrics["max_aspect_ratio"] <= 3.0
    assert metrics["upper_corridor"]["frac_count_le_l0"] == 1.0
    assert metrics["upper_corridor"]["frac_area_le_l0"] == 1.0
    assert metrics["lower_h6"]["frac_count_le_l0"] >= 0.90
    assert metrics["lower_h7"]["frac_count_le_l0"] >= 0.90


def test_f1764_framework_blob_hash_invariant():
    """Verify common framework script blob hash matches bitwise 399e048a... (F1763-R03 invariant)."""
    framework_path = os.path.join(REPO_ROOT, "scripts", "remeshing", "reusable_2d_adaptive_framework.py")
    assert os.path.exists(framework_path), "reusable_2d_adaptive_framework.py must exist"

    with open(framework_path, "rb") as f:
        data = f.read()

    header = ("blob %d\0" % len(data)).encode("utf-8")
    blob_sha = hashlib.sha1(header + data).hexdigest()
    assert blob_sha in FRAMEWORK_VALID_BLOB_SHAS, "Framework blob SHA %s must match a qualified revision" % blob_sha


def test_f1764_canonical_manifest_case5_entry():
    """Verify canonical manifest entry for Case 5 points to verified local paths."""
    manifest_path = os.path.join(REPO_ROOT, "configs", "remeshing", "canonical_five_case_manifest.json")
    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    c5 = manifest["benchmarks"]["case_5"]
    assert c5["published_elements"] == 15714
    assert c5["historical_reference_element_count"] == 15708
    assert "218_f1726_seven_hole_study" in c5["donor_odb_repo_path"]
    assert "218_f1726_seven_hole_study" in c5["historical_reference_mesh"]

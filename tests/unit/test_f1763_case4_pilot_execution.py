# -*- coding: utf-8 -*-
"""
test_f1763_case4_pilot_execution.py
===================================
Pre-execution qualification unit test suite for Task F1763:
Case 4 Common-Framework Single-Pass Adaptive Remeshing Pilot Execution.
"""
import os
import sys
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, REPO_ROOT)

FROZEN_UEL_SHA = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"


def test_f1763_pilot_pbs_script_directives():
    pbs_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "236_f1763_case4_pilot", "submit_f1763_case4_pilot.pbs")
    assert os.path.exists(pbs_path), "submit_f1763_case4_pilot.pbs must exist"

    with open(pbs_path, "r") as f:
        content = f.read()

    assert "#PBS -N F1763_C4_PILOT" in content
    assert "#PBS -l select=1:ncpus=1:mem=16gb" in content
    assert "#PBS -l walltime=01:00:00" in content
    assert "#PBS -q entry_imfdfkmq" in content
    assert "#PBS -m abe" in content
    assert "pr21vyci@mailserver.tu-freiberg.de" in content
    assert FROZEN_UEL_SHA in content.lower()
    assert "reusable_2d_adaptive_framework.py" in content
    assert "f1728_case4_five_hole.json" in content
    assert "audit_case4_ligament_resolution.py" in content


def test_f1763_case4_donor_odb_availability():
    odb_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "213_f1720_coarse_coupled", "PK_F1720_COARSE_COUPLED.odb")
    assert os.path.exists(odb_path), "Local Case 4 donor ODB must exist"
    assert os.path.getsize(odb_path) > 100 * 1024 * 1024, "Donor ODB must be > 100 MB"


def test_f1763_case4_audit_script_execution():
    audit_script = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "236_f1763_case4_pilot", "audit_case4_ligament_resolution.py")
    assert os.path.exists(audit_script), "audit_case4_ligament_resolution.py must exist"

    # Test parser on reference mesh
    ref_mesh = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "217_f1725_physics_study", "F1725_S2_COARSEN_ET315.inp")
    assert os.path.exists(ref_mesh), "F1725 reference mesh must exist"

    import importlib.util
    spec = importlib.util.spec_from_file_location("audit_case4", audit_script)
    audit_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit_mod)

    nodes, elements, elem_types = audit_mod.parse_inp_mesh(ref_mesh)
    metrics = audit_mod.compute_case4_metrics(nodes, elements, elem_types, l0=0.008)

    assert metrics["total_elements"] == 13017
    assert metrics["quad_percentage"] >= 97.0
    assert metrics["jacobian_valid"] is True
    assert metrics["negative_jacobians"] == 0
    assert metrics["max_aspect_ratio"] <= 3.0
    assert metrics["ligament_2"]["frac_count_le_l0"] >= 0.95
    assert metrics["ligament_3"]["frac_count_le_l0"] == 1.0
    assert metrics["ligament_4"]["frac_count_le_l0"] == 1.0


def test_f1763_canonical_manifest_case3_correction():
    manifest_path = os.path.join(REPO_ROOT, "configs", "remeshing", "canonical_five_case_manifest.json")
    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    c3 = manifest["benchmarks"]["case_3"]
    # Finding F1762-R03 resolution check:
    assert c3["historical_reference_element_count"] == 28933
    assert c3["baseline_comparison_element_count"] == 12110

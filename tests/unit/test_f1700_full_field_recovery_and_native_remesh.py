# -*- coding: utf-8 -*-
"""
tests/unit/test_f1700_full_field_recovery_and_native_remesh.py
==============================================================
Comprehensive unit test suite for Task F1700:
Resolving full-field UEL state recovery, validating native MISESERI remeshing,
and evaluating Pandey & Kumar (2025) Section 4.3 Figures 15(b) and 16(b).
"""

import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UEL_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1700_extracted_uel_full_field.json")
PRESCRIBED_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1700_prescribed_same_state_validation.json")
ADAPTED_METRICS_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1700_native_adapted_mesh_metrics.json")
FROZEN_UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def test_f1700_full_field_uel_data_provenance():
    assert os.path.exists(UEL_JSON), "f1700_extracted_uel_full_field.json must exist"
    with open(UEL_JSON, "r") as f:
        data = json.load(f)
    for sk in ["STATE2", "STATE4", "STATE5"]:
        assert sk in data, f"{sk} must be present in extracted UEL data"
        s = data[sk]
        assert s["num_nodes"] == 4040, f"{sk} must contain all 4,040 nodes"
        assert s["num_elements"] == 3923, f"{sk} must contain all 3,923 elements"
        assert s["num_ips"] == 15365, f"{sk} must contain all 15,365 IPs"
        assert len(s["nodal_displacements"]) == 4040
        assert s["damage_max"] >= 0.999, f"{sk} must show severe damage"

def test_f1700_gate_a_exact_kinematic_equivalence():
    assert os.path.exists(PRESCRIBED_JSON), "f1700_prescribed_same_state_validation.json must exist"
    with open(PRESCRIBED_JSON, "r") as f:
        data = json.load(f)
    for sk in ["STATE2", "STATE4", "STATE5"]:
        assert sk in data, f"{sk} must be present in validation record"
        s = data[sk]
        assert s["common_nodes"] == 4039, "All 4,039 continuum nodes must match"
        assert s["rel_displacement_error_pct"] < 1e-4, f"{sk} eps_U must be < 1e-4% (measured {s['rel_displacement_error_pct']}%)"
        assert s["max_displacement_diff_mm"] < 1e-9, f"{sk} max displacement difference must be < 1 nm"
        assert s["gate_a_kinematic_verdict"] in ["PASS_EXACT_EQUIVALENCE", "KINEMATIC_TRANSFER_PASS_EXACT_PARITY"]
        assert s.get("gate_a_verdict") == "KINEMATIC_TRANSFER_PASS_EXACT_PARITY"

def test_f1700_gate_b_native_spr_error_recovery():
    with open(PRESCRIBED_JSON, "r") as f:
        data = json.load(f)
    s4 = data["STATE4"]
    assert s4["global_max_miseseri_MPa"] > 40.0, "State 4 global peak error must exceed 40 MPa"
    assert s4["secondary_corridor"]["max_error_MPa"] > 3.0, "State 4 secondary corridor error must exceed 3 MPa"
    assert s4["secondary_corridor"]["mean_rel_error_pct"] > 1000.0, "Secondary corridor relative error must exceed 1000%"
    
    s5 = data["STATE5"]
    assert s5["secondary_corridor"]["ratio_of_peak_pct"] > 70.0, "State 5 secondary corridor must reach > 70% of peak"

def test_f1700_gate_c_native_adaptiveremesh_execution():
    assert os.path.exists(ADAPTED_METRICS_JSON), "f1700_native_adapted_mesh_metrics.json must exist"
    with open(ADAPTED_METRICS_JSON, "r") as f:
        data = json.load(f)
    for job_key in ["PK_SEC43_F1700_NATIVE_ADAPT_STATE4", "PK_SEC43_F1700_NATIVE_ADAPT_STATE2", "PK_SEC43_F1700_NATIVE_ADAPT_STATE5"]:
        assert job_key in data
        job = data[job_key]
        assert os.path.exists(job["adapted_deck"]), f"Adapted input deck must exist: {job['adapted_deck']}"
        assert job["mesh_metrics"]["total_elements"] > 8000
        assert job["mesh_metrics"]["area_preservation_pct"] >= 99.99

def test_f1700_secondary_corridor_resolution_breakthrough():
    with open(ADAPTED_METRICS_JSON, "r") as f:
        data = json.load(f)
    s4_corridors = data["PK_SEC43_F1700_NATIVE_ADAPT_STATE4"]["corridors"]
    sec4 = s4_corridors["secondary"]
    assert sec4["min"] < 0.08, "State 4 secondary corridor must refine below l0/3 = 0.095 mm"
    assert sec4["pct_le_l0"] > 80.0, "State 4 secondary corridor must resolve > 80% at <= l0"
    assert sec4["pct_le_l0_half"] > 5.0, "State 4 secondary corridor must resolve > 5% at <= l0/2"
    
    sec2 = data["PK_SEC43_F1700_NATIVE_ADAPT_STATE2"]["corridors"]["secondary"]
    assert sec2["pct_le_l0"] == 0.0, "State 2 secondary corridor must be completely unrefined (0.00% <= l0)"

def test_f1700_physical_impossibility_of_single_frame_dual_branch():
    with open(ADAPTED_METRICS_JSON, "r") as f:
        data = json.load(f)
    prim4 = data["PK_SEC43_F1700_NATIVE_ADAPT_STATE4"]["corridors"]["primary"]
    assert prim4["pct_le_l0_half"] == 0.0, "State 4 primary corridor must have 0.00% <= l0/2 due to stress relaxation"
    
    prim5 = data["PK_SEC43_F1700_NATIVE_ADAPT_STATE5"]["corridors"]["primary"]
    assert prim5["pct_le_l0_half"] == 0.0, "State 5 primary corridor must have 0.00% <= l0/2"
    
    assert data["PK_SEC43_F1700_NATIVE_ADAPT_STATE4"]["scientific_outcome"] == "NOT_REPRODUCED_UNDER_TESTED_CONDITIONS"

def test_f1700_resource_and_governance_invariants():
    assert os.path.exists(FROZEN_UEL_PATH), "Production UEL must exist"
    with open(FROZEN_UEL_PATH, "rb") as f:
        content = f.read()
    actual_hash = hashlib.sha256(content).hexdigest().lower()
    assert actual_hash == EXPECTED_UEL_SHA256, "Production UEL must remain bitwise identical"
    line_count = len(content.decode("utf-8", errors="ignore").splitlines())
    assert line_count == 907, "Production UEL line count must remain 907 lines"

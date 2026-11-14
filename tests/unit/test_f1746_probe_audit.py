# -*- coding: utf-8 -*-
"""
tests/unit/test_f1746_probe_audit.py

Validates Task F1746 Case 3 Single-Pass 5-State Error-Indicator Envelope Native Remeshing:
  1. Normalization provenance parity across all 5 donor states (Finding F1746-R04 resolution).
  2. FE quality & inversion safety of the 120,554-element probe mesh (Findings F1746-R02 & R03).
  3. Simultaneous dual-corridor minimum size activation (h_min <= l0/3 primary, h_min <= l0/2 secondary).
  4. Bitwise preservation of frozen UEL f42_mixed_uel.for (CE8D5EDC...).
  5. Zero-PBS governance adherence (0 new jobs consumed, cumulative preserved at 25).
"""

import os
import sys
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
L0 = 0.285  # mm

def test_f1746_frozen_uel_integrity():
    """Verify bitwise preservation of f42_mixed_uel.for."""
    uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    assert os.path.exists(uel_path), "Frozen UEL source missing: %s" % uel_path
    with open(uel_path, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest().upper()
    assert digest == FROZEN_UEL_SHA256, "UEL hash mismatch: got %s" % digest

def test_f1746_normalization_provenance_parity():
    """Verify Finding F1746-R04 resolution: 100.0000% parity with F1745 baseline norms."""
    f1745_eval_path = os.path.join(REPO_ROOT, "results", "validation", "f1745_case3_envelope_evaluation.json")
    assert os.path.exists(f1745_eval_path), "F1745 eval JSON missing"
    with open(f1745_eval_path, "r", encoding="utf-8-sig") as f:
        eval_data = json.load(f)
    norms = eval_data["global_norms"]
    
    # Expected authoritative baseline norms from F1745
    expected_norms = {
        "T1": 9.712560,
        "T2": 9.326990,
        "T3": 9.697383,
        "S2": 144.357587,
        "S4": 224.368650
    }
    for state, exp_norm in expected_norms.items():
        assert state in norms, "State %s missing from norms" % state
        actual_norm = norms[state]["total_solution_energy_norm"]
        assert abs(actual_norm - exp_norm) < 1e-5, (
            "State %s norm mismatch: actual %.6f vs expected %.6f" % (state, actual_norm, exp_norm)
        )
    assert eval_data["envelope_statistics"]["extreme_ratio_eliminated"] is True

def test_f1746_probe_mesh_fe_quality():
    """Verify probe trial mesh FE quality and inversion safety."""
    audit_json = os.path.join(REPO_ROOT, "results", "validation", "f1746_probe_spatial_audit.json")
    assert os.path.exists(audit_json), "Probe spatial audit JSON missing"
    with open(audit_json, "r", encoding="utf-8-sig") as f:
        audit = json.load(f)
    
    assert audit["total_physical_elements"] == 120554, "Total elements mismatch"
    assert audit["quad_percentage"] >= 95.0, "Quad percentage < 95%: %.2f" % audit["quad_percentage"]
    assert audit["min_jacobian_det"] > 0.0, "Negative or zero Jacobian detected"
    assert audit["zero_negative_jacobians"] is True, "zero_negative_jacobians flag is False"
    assert audit["max_aspect_ratio"] <= 5.0, "Aspect ratio exceeded 5.0: %.2f" % audit["max_aspect_ratio"]

def test_f1746_probe_dual_corridor_spatial_activation():
    """Verify both primary and secondary corridors achieve simultaneous singular root refinement."""
    audit_json = os.path.join(REPO_ROOT, "results", "validation", "f1746_probe_spatial_audit.json")
    with open(audit_json, "r", encoding="utf-8-sig") as f:
        audit = json.load(f)
    
    prim = audit["primary_corridor"]
    sec = audit["secondary_corridor"]
    
    # Primary corridor minimum size: h_min <= l0/3 = 0.0950 mm
    assert prim["min_h_mm"] <= (L0 / 3.0), (
        "Primary corridor h_min %.4f mm > l0/3 (%.4f mm)" % (prim["min_h_mm"], L0 / 3.0)
    )
    # Primary corridor h <= l0 compliance >= 85%
    assert prim["pct_area_le_l0"] >= 85.0, (
        "Primary corridor area compliance h <= l0 is %.2f%% < 85%%" % prim["pct_area_le_l0"]
    )
    
    # Secondary corridor minimum size: h_min <= l0/2 = 0.1425 mm
    assert sec["min_h_mm"] <= (L0 / 2.0), (
        "Secondary corridor h_min %.4f mm > l0/2 (%.4f mm)" % (sec["min_h_mm"], L0 / 2.0)
    )
    # Secondary corridor h <= l0 compliance
    assert sec["pct_area_le_l0"] >= 75.0, (
        "Secondary corridor area compliance h <= l0 is %.2f%% < 75%%" % sec["pct_area_le_l0"]
    )

def test_f1746_governance_and_zero_pbs_budget():
    """Verify 0 new PBS jobs consumed and cumulative historical accounting preserved."""
    active_task_path = os.path.join(REPO_ROOT, "project_coordination", "ACTIVE_TASK.json")
    with open(active_task_path, "r", encoding="utf-8-sig") as f:
        task = json.load(f)
    
    assert task["submissions_consumed"] == 0, "Non-zero submissions consumed: %d" % task["submissions_consumed"]
    assert task["cumulative_pbs_submissions"] == 25, "Cumulative PBS submissions != 25"
    assert len(task["historical_pbs_job_ids"]) == 25, "Historical PBS job IDs count != 25"

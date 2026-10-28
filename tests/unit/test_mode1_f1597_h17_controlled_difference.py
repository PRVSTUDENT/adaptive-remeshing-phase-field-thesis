# -*- coding: utf-8 -*-
"""
test_mode1_f1597_h17_controlled_difference.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Automated test verifying the controlled difference audit of Package 132 (Hypothesis H17).
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AUDIT_JSON = os.path.join(REPO_ROOT, "results", "validation", "h17_quarterstep_controlled_difference_audit.json")

@pytest.fixture(scope="module")
def audit_data():
    assert os.path.isfile(AUDIT_JSON), "Missing audit JSON: %s" % AUDIT_JSON
    with open(AUDIT_JSON, "r") as f:
        return json.load(f)

def test_audit_status_and_verification(audit_data):
    assert audit_data["schema"] == 1
    assert audit_data["status"] == "PASS"
    assert audit_data["verification_passed"] is True
    assert audit_data["package_name"] == "132_c4_inc86_75_h17_quarterstep_continuation"
    assert audit_data["hypothesis"] == "H17_QUARTERSTEP_AM_CONTINUATION"

def test_kinematics(audit_data):
    kin = audit_data["kinematics"]
    assert pytest.approx(kin["source_u_top_mm"], 1e-10) == 0.001938410627
    assert pytest.approx(kin["target_u_top_mm"], 1e-10) == 0.001942860108
    assert pytest.approx(kin["forward_displacement_increment_mm"], 1e-10) == 0.000004449481
    assert kin["kinematics_correct"] is True

def test_invariants_and_provenance(audit_data):
    inv = audit_data["checkpoint_restoration_provenance"]
    assert inv["d_lower_bounds_matches_inc86_5_checkpoint"] is True
    assert inv["nodal_displacements_matches_inc86_5_checkpoint"] is True
    assert inv["active_set_cards_matches_inc86_5_checkpoint"] is True
    assert inv["uel_source_matches_package130"] is True
    assert inv["frozen_uel_sha256"] == "ab0a5a71335ecb445e91ec13a645e280ff3310b561a5e78aba4a49c8e81dd8ac"

def test_acceptance_criteria_predeclared(audit_data):
    crit = audit_data["predeclared_acceptance_criteria"]
    assert crit["stationarity_delta_d_max"] == 1.0e-3
    assert crit["stationarity_delta_rf2_max_N"] == 0.1
    assert crit["free_phase_residual_max_kN_mm"] == 1.0e-6
    assert crit["active_multiplier_min_kN_mm"] == -1.0e-9
    assert crit["damage_healing_tolerance"] == 1.0e-8
    assert crit["max_am_cycles_allowed"] == 25

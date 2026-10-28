# -*- coding: utf-8 -*-
"""
tests/unit/test_mode1_f1597_h15_controlled_difference.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Automated test verifying H15 controlled difference audit artifact.
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AUDIT_JSON = os.path.join(REPO_ROOT, "results", "validation", "h15_halfstep_controlled_difference_audit.json")

@pytest.fixture(scope="module")
def audit_data():
    assert os.path.isfile(AUDIT_JSON), f"Missing audit JSON: {AUDIT_JSON}"
    with open(AUDIT_JSON, "r") as f:
        return json.load(f)

def test_audit_status_pass(audit_data):
    assert audit_data.get("schema") == 1
    assert audit_data.get("task_id") == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert audit_data.get("status") == "PASS"
    assert audit_data.get("verification_passed") is True

def test_loading_parameters(audit_data):
    load = audit_data["loading_comparison"]
    assert pytest.approx(load["initial_increment86_u2_mm"], 1e-10) == 0.0019295116654
    assert pytest.approx(load["h15_midpoint_target_u2_mm"], 1e-10) == 0.001938410627
    assert pytest.approx(load["h15_midpoint_delta_u2_mm"], 1e-10) == 0.0000088989616
    assert pytest.approx(load["step_reduction_factor"], 1e-6) == 0.5

def test_invariant_assets(audit_data):
    inv = audit_data["invariant_assets_verified"]
    assert inv["f42_unified_12dof_active_set_uel.for"]["is_frozen_uel"] is True
    assert inv["f42_unified_12dof_active_set_uel.for"]["matches_p129"] is True
    assert inv["d_lower_bounds.csv"]["matches_p129"] is True
    assert inv["d_lower_bounds.csv"]["committed_gp_count"] == 17688

# -*- coding: utf-8 -*-
"""
tests/unit/test_mode1_f1597_h14_load_state_integrity.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Automated unit test suite verifying load state equivalence and resolving
displacement discrepancy between Package 129 and Package 129 R1.
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AUDIT_JSON = os.path.join(REPO_ROOT, "results", "validation", "h14_load_state_integrity_audit.json")

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

def test_bit_exact_asset_matches(audit_data):
    assets = audit_data.get("bit_exact_asset_verification", {})
    assert len(assets) == 4
    for asset_name, info in assets.items():
        assert info.get("match") is True, f"Asset {asset_name} failed match"
        assert info.get("p129_sha256") == info.get("p129_r1_sha256"), f"SHA mismatch on {asset_name}"

def test_actual_load_states(audit_data):
    p129 = audit_data["discrepancy_analysis"]["actual_package129_loading"]
    p129_r1 = audit_data["discrepancy_analysis"]["actual_package129_r1_loading"]

    assert pytest.approx(p129["initial_u2_mm"], 1e-10) == 0.0019295116654
    assert pytest.approx(p129["target_u2_mm"], 1e-10) == 0.001947309589
    assert pytest.approx(p129["delta_u2_mm"], 1e-10) == 0.0000177979236

    assert pytest.approx(p129_r1["initial_u2_mm"], 1e-10) == 0.0019295116654
    assert pytest.approx(p129_r1["target_u2_mm"], 1e-10) == 0.001947309589
    assert pytest.approx(p129_r1["delta_u2_mm"], 1e-10) == 0.0000177979236

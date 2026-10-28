# -*- coding: utf-8 -*-
"""
test_mode1_f1597_h18_controlled_difference.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit test suite verifying the controlled difference and restoration invariants
for Hypothesis H18 (Package 133, Increment 86.75 to 87.00).
"""

import os
import json
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AUDIT_JSON = os.path.join(REPO_ROOT, "results", "validation", "h18_quarterstep_controlled_difference_audit.json")

@pytest.fixture(scope="module")
def audit_data():
    assert os.path.exists(AUDIT_JSON), "Audit JSON missing: %s" % AUDIT_JSON
    with open(AUDIT_JSON, "r") as f:
        return json.load(f)

def test_h18_audit_verdict(audit_data):
    assert audit_data["audit_verdict"] == "H18_CONTROLLED_DIFFERENCE_VERIFIED"
    assert audit_data["hypothesis"] == "H18_SECOND_QUARTERSTEP_AM_CONTINUATION"

def test_h18_kinematics(audit_data):
    kin = audit_data["kinematics"]
    assert pytest.approx(kin["u_init_inc86_75_mm"], 1e-12) == 0.001942860108
    assert pytest.approx(kin["u_target_inc87_mm"], 1e-12) == 0.001947309589
    assert pytest.approx(kin["delta_u_mm"], 1e-12) == 0.000004449481
    assert kin["bc_found_in_inp"] is True

def test_h18_restoration_invariants(audit_data):
    inv = audit_data["restoration_invariants"]
    assert inv["d_lower_bounds_match"] is True
    assert inv["nodal_displacements_match"] is True
    assert inv["active_set_cards_match"] is True
    assert inv["frozen_uel_bit_exact"] is True

def test_h18_hashes(audit_data):
    h = audit_data["hashes"]
    assert h["f42_uel_sha256"] == "AB0A5A71335ECB445E91EC13A645E280FF3310B561A5E78ABA4A49C8E81DD8AC"
    assert h["d_lower_bounds_sha256"] == "BF250B09CAC2479DD9590AD4A0918B7D3BEBF0F94BD5972383305580983B376A"
    assert h["nodal_displacements_sha256"] == "554610895B86D559F02FF195F892BEE15F0790CC378EC76CDF905B9A40073D18"
    assert h["active_set_cards_sha256"] == "E62E1574C03FF1FD5DC4C406BC03D27B013B4B9E07A3637D586CEC70563D109B"

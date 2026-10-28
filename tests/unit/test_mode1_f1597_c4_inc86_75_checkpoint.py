# -*- coding: utf-8 -*-
"""
test_mode1_f1597_c4_inc86_75_checkpoint.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit test suite verifying the integrity, monotonicity, and completeness
of the Increment-86.75 checkpoint restored from Package 132 (Job 1418466.mmaster02).
"""

import os
import json
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RESULTS_DIR = os.path.join(REPO_ROOT, "results", "validation")
AUDIT_JSON = os.path.join(RESULTS_DIR, "c4_inc86_75_checkpoint_audit.json")
CKPT_JSON = os.path.join(RESULTS_DIR, "c4_inc86_75_checkpoint.json")

def test_checkpoint_audit_passed():
    assert os.path.exists(AUDIT_JSON), "Audit JSON missing: %s" % AUDIT_JSON
    with open(AUDIT_JSON, "r") as f:
        data = json.load(f)
    assert data["verification_passed"] is True
    assert data["checkpoint_status"] == "AUTHENTIC_INCREMENT_86_75_CHECKPOINT_VERIFIED"
    assert data["node_count"] == 4588
    assert data["element_count"] == 4422
    assert data["total_gp_count"] == 17688
    assert data["history_monotonicity_violations"] == 0
    assert data["damage_monotonicity_violations"] == 0

def test_checkpoint_state_metrics():
    with open(CKPT_JSON, "r") as f:
        ckpt = json.load(f)
    summary = ckpt["state_summary"]
    assert 0.650 < summary["d_max"] < 0.660
    assert 182.0 < summary["rf2_rp_N"] < 184.0
    assert 0.235 < summary["e_tot_mJ"] < 0.236
    assert ckpt["cycle_committed"] == 11
    assert ckpt["is_stationary_equilibrium"] is True

def test_companion_files_exist_and_nonempty():
    for base in [
        "c4_inc86_75_checkpoint_d_lower_bounds.csv",
        "c4_inc86_75_checkpoint_nodal_displacements.csv",
        "c4_inc86_75_checkpoint_active_set_cards.inc",
        "c4_inc86_75_checkpoint_recovery_receipt.json"
    ]:
        p = os.path.join(RESULTS_DIR, base)
        assert os.path.exists(p), "Missing companion file: %s" % p
        assert os.path.getsize(p) > 0, "Companion file is empty: %s" % p

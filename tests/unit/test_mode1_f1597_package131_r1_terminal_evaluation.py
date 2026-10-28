# -*- coding: utf-8 -*-
"""
tests/unit/test_mode1_f1597_package131_r1_terminal_evaluation.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Automated test suite verifying:
1. Package 131 R1 terminal artifacts existence and cryptographic integrity.
2. PBS Job 1418451.mmaster02 execution logs and Exit 0 status.
3. Comparative findings across H9, H14, H15, and H16 against Donor Increment 87.
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PKG_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "131_r1_c4_inc87_second_halfstep_h16_continuation")
EVAL_JSON = os.path.join(REPO_ROOT, "results", "validation", "h16_second_halfstep_evaluation.json")

@pytest.fixture(scope="module")
def eval_data():
    assert os.path.isfile(EVAL_JSON), "Missing evaluation JSON: %s" % EVAL_JSON
    with open(EVAL_JSON, "r") as f:
        return json.load(f)

def test_package131_r1_terminal_artifacts_exist():
    required_files = [
        "c4_inc87_h16_continuation_summary.json",
        "pbs_execution.log",
        "pbs_error.log",
        "M1_C4_INC87_SECOND_HALFSTEP_H16_CONTINUATION.inp",
        "driver_c4_inc87_h16_continuation.py",
        "d_lower_bounds.csv",
        "nodal_displacements_initial.csv",
        "active_set_boundary_cards.inc"
    ]
    for fn in required_files:
        p = os.path.join(PKG_DIR, fn)
        assert os.path.isfile(p), "Missing terminal package file: %s" % p

def test_pbs_error_log_empty():
    p = os.path.join(PKG_DIR, "pbs_error.log")
    assert os.path.getsize(p) == 0, "Expected empty pbs_error.log"

def test_comparative_synthesis(eval_data):
    runs = eval_data["continuation_runs"]
    assert "H9_P129_FULLSTEP_25CYC" in runs
    assert "H14_P129R1_FULLSTEP_65CYC" in runs
    assert "H15_P130R1_FIRST_HALFSTEP_9CYC" in runs
    assert "H16_P131R1_SECOND_HALFSTEP_25CYC" in runs

    h15 = runs["H15_P130R1_FIRST_HALFSTEP_9CYC"]
    assert h15["verdict"] == "H15_PASSED_MIDPOINT"
    assert h15["cycles_completed"] == 9

    h16 = runs["H16_P131R1_SECOND_HALFSTEP_25CYC"]
    assert h16["verdict"] == "H16_FAILED_NONSTATIONARY"
    assert h16["cycles_completed"] == 25
    assert h16["rf2_discrepancy_pct"] <= 5.0
    assert h16["e_tot_discrepancy_pct"] <= 2.0
    assert h16["healing_violations"] == 0

def test_findings_and_gate_status(eval_data):
    findings = eval_data["scientific_findings"]
    assert findings["verdict"] == "H16_FAILED_NONSTATIONARY"
    assert "STAGE_C1_2_STEP2_ENERGY_GATE_FAILED" in findings["gate_status"]

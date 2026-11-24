# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case3_local_smoke_test.py
==================================================
Task: METHOD-C-CASE3-FRAMEWORK-LOCAL-WINDOWS-SMOKE-TEST
Scientific Operation: method_c_case3_framework_local_windows_smoke_test

Unit tests verifying the local Windows smoke test (Cycle 0 coarse solve):
1. Bitwise frozen UEL verification (CE8D5EDC...)
2. Approved dynamic-corridor orchestrator verification (AC56BA7D...)
3. Presence and integrity of committed local smoke test artifacts
4. Reproduction of Step-1 reaction force (~3.9288 kN)
5. Reproduction of peak reaction force (~4.3318 kN at u2 ~0.05610 mm)
6. Reproduction of total equilibrium iterations (256: 160 Step 1, 96 Step 2)
7. Reproduction of macroscopic crack tip coordinates ((10.6727, 69.9342) mm)
8. Extracted state file integrity and phase bounds [0, 1]
"""

from __future__ import print_function, division
import os
import sys
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
ORCHESTRATOR_SHA256 = "AC56BA7D2BF877FD174DF375E8066DB17B90F61D0EAEB93CFC9854106710A79A"

SMOKE_TEST_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "local_windows_smoke_test")
REPORT_PATH = os.path.join(REPO_ROOT, "docs", "validation", "METHOD_C_CASE3_LOCAL_WINDOWS_SMOKE_TEST_REPORT.md")


def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def test_frozen_uel_sha256():
    """Verify the UEL source is bitwise identical to the frozen thesis reference."""
    uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
    assert os.path.isfile(uel_path), "Frozen UEL file missing: %s" % uel_path
    actual_sha = compute_sha256(uel_path)
    assert actual_sha == FROZEN_UEL_SHA256, "UEL SHA mismatch: got %s, expected %s" % (actual_sha, FROZEN_UEL_SHA256)


def test_orchestrator_sha256():
    """Verify the orchestrator is bitwise identical to approved dynamic-corridor or Fix 1 version."""
    orch_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "case3_single_job_orchestrator.py")
    assert os.path.isfile(orch_path), "Orchestrator file missing: %s" % orch_path
    actual_sha = compute_sha256(orch_path)
    approved_shas = (
        ORCHESTRATOR_SHA256,
        "E8CD974D79540779FBC1AF8B291F6FF7A8EA3C2FAAA42185AC3D92F14B74DADC",  # Fix 1: Far-side secondary refinement zone
        "E1448DC847625E51E911874C2FB1BD0170CB53CDA30BDE7FF306E1BDF7BFC06A",  # Fix 3: Arc-length RIKS Step 2 & extended far-side band
    )
    assert actual_sha in approved_shas, "Orchestrator SHA mismatch: got %s, expected one of %s" % (actual_sha, approved_shas)


def test_local_smoke_artifacts_exist():
    """Verify all expected local smoke test artifacts are committed in the package directory."""
    expected_files = [
        "PK_METHOD_C_CASE3_COARSE_JOB1_state.json",
        "PK_METHOD_C_CASE3_COARSE_JOB1_SUMMARY.json",
        "PK_METHOD_C_CASE3_COARSE_JOB1_RECEIPT.json",
        "PK_METHOD_C_CASE3_COARSE_JOB1.sta",
        "PK_METHOD_C_CASE3_COARSE_JOB1.msg",
        "PK_METHOD_C_CASE3_COARSE_JOB1.dat",
        "uel_energy_balance.csv",
    ]
    for fname in expected_files:
        fpath = os.path.join(SMOKE_TEST_DIR, fname)
        assert os.path.isfile(fpath), "Missing smoke test artifact: %s" % fpath
        assert os.path.getsize(fpath) > 0, "Empty smoke test artifact: %s" % fpath


def test_summary_observables():
    """Verify extracted SUMMARY.json matches approved benchmark targets."""
    summary_path = os.path.join(SMOKE_TEST_DIR, "PK_METHOD_C_CASE3_COARSE_JOB1_SUMMARY.json")
    with open(summary_path, "r", encoding="utf-8-sig") as f:
        data = json.load(f)

    # 1. Step-1 reaction force approx 3.9288 kN
    step1_rf2 = data["step1_end_RF2_kN"]
    assert pytest.approx(3.9288, abs=0.01) == step1_rf2, "Step-1 RF2 deviation: %.4f" % step1_rf2

    # 2. Peak force approx 4.3318 kN
    peak_rf2 = data["peak_RF2_kN"]
    assert pytest.approx(4.3318, abs=0.01) == peak_rf2, "Peak RF2 deviation: %.4f" % peak_rf2

    # 3. Displacement at peak force approx 0.05610 mm
    u2_peak = data["u2_at_peak_RF2_mm"]
    assert pytest.approx(0.05610, abs=0.001) == u2_peak, "u2 at peak deviation: %.6f" % u2_peak

    # 4. Total equilibrium iterations == 256
    assert data["step1_equilibrium_iterations"] == 160
    assert data["step2_equilibrium_iterations"] == 96
    assert data["total_equilibrium_iterations"] == 256

    # 5. Increments
    assert data["step1_increments"] == 50
    assert data["step2_increments"] == 13
    assert data["total_increments"] == 63

    # 6. Crack tip coordinates approx (10.6727, 69.9342) mm
    tip_x = data["final_crack_tip_x_mm"]
    tip_y = data["final_crack_tip_y_mm"]
    assert pytest.approx(10.6727, abs=0.01) == tip_x, "Tip x deviation: %.4f" % tip_x
    assert pytest.approx(69.9342, abs=0.01) == tip_y, "Tip y deviation: %.4f" % tip_y

    # 7. Crack extension approx 0.676 mm
    crack_ext = data["final_crack_extension_mm"]
    assert pytest.approx(0.676, abs=0.01) == crack_ext, "Crack extension deviation: %.4f" % crack_ext
    assert data["forward_crack_growth_demonstrated"] is True


def test_state_json_integrity():
    """Verify extracted state JSON integrity, phase bounds, and nodal fields."""
    state_path = os.path.join(SMOKE_TEST_DIR, "PK_METHOD_C_CASE3_COARSE_JOB1_state.json")
    with open(state_path, "r", encoding="utf-8-sig") as f:
        state = json.load(f)

    assert "u_nodal" in state
    assert "d_nodal" in state
    assert "h_gp" in state
    assert state["max_damage"] <= 1.0 + 1e-4
    assert state["max_damage"] >= 0.95
    assert state["num_nodes"] == 4813
    assert pytest.approx(0.05611, abs=0.001) == state["terminal_u2"]


def test_smoke_report_exists():
    """Verify the smoke test report is present and contains key sections."""
    assert os.path.isfile(REPORT_PATH), "Report file missing: %s" % REPORT_PATH
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "3.9288" in content
    assert "4.3318" in content
    assert "256" in content
    assert "10.6727" in content
    assert "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6" in content
    assert "AC56BA7D2BF877FD174DF375E8066DB17B90F61D0EAEB93CFC9854106710A79A" in content

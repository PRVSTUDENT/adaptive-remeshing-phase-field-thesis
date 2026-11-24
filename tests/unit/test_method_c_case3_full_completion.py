# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case3_full_completion.py
=================================================
Unit tests for the completed Method C Case 3 production run with Fix 3 (arc-length RIKS + extended band).
Validates crack re-nucleation past the hole, forward propagation past x = 64.0 mm, and complete
specimen fracture with RF2 dropping below 5% of peak force.
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TARGET_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "local_windows_full_run")
COMPLETED_SUMMARY = os.path.join(TARGET_DIR, "METHOD_C_CASE3_LOCAL_FULL_RUN_COMPLETED_SUMMARY.json")
REPORT_PATH = os.path.join(REPO_ROOT, "docs", "validation", "METHOD_C_CASE3_LOCAL_FULL_RUN_COMPLETION_REPORT.md")

PEAK_RF2_BENCHMARK = 4.3318  # kN (Cycle 0 peak)
FIVE_PCT_THRESHOLD = 0.05 * PEAK_RF2_BENCHMARK  # 0.21659 kN


@pytest.fixture(scope="module")
def completed_run_data():
    assert os.path.isfile(COMPLETED_SUMMARY), "Completed summary JSON missing: %s" % COMPLETED_SUMMARY
    with open(COMPLETED_SUMMARY, "r", encoding="utf-8") as f:
        records = json.load(f)
    assert len(records) == 57, "Expected exactly 57 cycle records (Cycles 0-56), found %d" % len(records)
    return records


def test_completed_summary_exists_and_has_57_cycles(completed_run_data):
    """Verifies all 57 cycles exist, ordered 0 to 56."""
    for idx, r in enumerate(completed_run_data):
        assert r["cycle_idx"] == idx
        assert "actual_terminal_u2" in r
        assert "tip_x" in r
        assert "tip_y" in r


def test_hole_penetration_and_far_side_renucleation(completed_run_data):
    """Verifies Cycle 49 successfully crosses the hole and re-nucleates on far side."""
    c48 = completed_run_data[48]
    c49 = completed_run_data[49]

    # Cycle 48 was arrested at hole entrance
    assert c48["tip_x"] < 39.0
    assert c48["dist_to_hole_boundary_mm"] < 1.0

    # Cycle 49 jumped across hole ligament
    assert c49["tip_x"] > 50.0  # (53.96 mm)
    assert c49["far_side_d_max"] > 0.99  # (0.9997)
    assert c49["actual_terminal_u2"] > 0.297421  # Advanced past block
    assert c49["conv_status"] == "CONV"


def test_crack_propagation_beyond_64mm(completed_run_data):
    """Verifies crack tip reaches x >= 64.0 mm (termination criterion 1)."""
    c52 = completed_run_data[52]
    assert c52["tip_x"] >= 64.0, "Cycle 52 tip_x (%.4f) must be >= 64.0 mm" % c52["tip_x"]
    assert c52["conv_status"] == "CONV"


def test_complete_specimen_fracture_rf2_drop(completed_run_data):
    """Verifies complete specimen fracture with RF2 < 5% of peak force (termination criterion 2)."""
    c53 = completed_run_data[53]
    rf2_c53 = c53.get("terminal_rf2_kN") or c53.get("step1_rf2_kN")

    # Specimen fully severed: tip reached right edge (x = 65.0 mm)
    assert c53["tip_x"] >= 64.9
    assert c53["d_max"] >= 0.9999

    # Reaction force dropped to near zero (< 5% of 4.3318 kN = 0.2166 kN)
    assert rf2_c53 < FIVE_PCT_THRESHOLD, "RF2 (%.6f kN) must be < 5%% of peak (%.4f kN)" % (rf2_c53, FIVE_PCT_THRESHOLD)
    assert rf2_c53 < 0.01  # In fact < 10 N (< 0.01 kN)


def test_mesh_budget_preserved(completed_run_data):
    """Verifies mesh element count remains < 35,000 elements with high quad quality across all Fix 3 cycles."""
    for c in range(49, 57):
        rec = completed_run_data[c]
        assert rec["mesh_total_elements"] < 35000, "Cycle %d exceeded 35,000 elements: %d" % (c, rec["mesh_total_elements"])
        assert rec["mesh_total_elements"] > 25000, "Cycle %d unexpectedly low elements: %d" % (c, rec["mesh_total_elements"])
        assert rec["mesh_quad_pct"] > 95.0, "Cycle %d quad percentage too low: %.2f%%" % (c, rec["mesh_quad_pct"])


def test_completion_report_artifact_exists():
    """Verifies completion report exists and documents the full simulation."""
    assert os.path.isfile(REPORT_PATH), "Completion report missing: %s" % REPORT_PATH
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Cycles 0 to 56" in content
    assert "64.1383" in content or "64.14" in content
    assert "0.001694" in content or "0.00169" in content
    assert "RIKS" in content

# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case3_local_full_run.py
================================================
Unit tests for Method C Case 3 Local Windows full production run (Cycles 0 to 56).
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TARGET_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "local_windows_full_run")
COMBINED_SUMMARY = os.path.join(TARGET_DIR, "METHOD_C_CASE3_LOCAL_FULL_RUN_SUMMARY.json")
REPORT_PATH = os.path.join(REPO_ROOT, "docs", "validation", "METHOD_C_CASE3_LOCAL_WINDOWS_FULL_RUN_REPORT.md")


@pytest.fixture(scope="module")
def full_run_data():
    assert os.path.isfile(COMBINED_SUMMARY), "Combined full run summary JSON missing: %s" % COMBINED_SUMMARY
    with open(COMBINED_SUMMARY, "r", encoding="utf-8") as f:
        records = json.load(f)
    assert len(records) == 57, "Expected exactly 57 cycle records (Cycles 0-56), found %d" % len(records)
    return records


def test_cycle_count_and_continuity(full_run_data):
    """Verifies all 57 cycles exist and are sequenced 0 to 56."""
    for idx, r in enumerate(full_run_data):
        assert r["cycle_idx"] == idx
        assert "job_name" in r
        assert "tip_x" in r
        assert "tip_y" in r
        assert "actual_terminal_u2" in r


def test_cycle0_baseline_observables(full_run_data):
    """Verifies Cycle 0 reproduces the authentic benchmark observables."""
    c0 = full_run_data[0]
    assert c0["cycle_idx"] == 0
    assert abs(c0["peak_rf2_kN"] - 4.3318) < 0.005
    assert abs(c0["peak_u2_mm"] - 0.0561) < 0.002
    assert c0["total_iters"] == 256


def test_crack_advancement_toward_hole(full_run_data):
    """Verifies crack tip advances from notch root (x=10.51 mm) toward central hole."""
    c0 = full_run_data[0]
    c49 = full_run_data[49]

    # Crack advances in x
    assert c0["tip_x"] < 11.0
    assert c49["tip_x"] > 37.5
    # Crack deflects downward toward hole center (y=51.0 mm)
    assert c0["tip_y"] > 69.5
    assert c49["tip_y"] < 62.0


def test_crack_arrest_near_hole_boundary(full_run_data):
    """Verifies crack arrests ~0.29-0.58 mm outside hole boundary during Cycles 50-56."""
    for c in range(50, 57):
        rec = full_run_data[c]
        assert abs(rec["tip_x"] - 38.0) < 0.3
        assert abs(rec["tip_y"] - 61.3) < 0.5
        assert rec["dist_to_hole_boundary_mm"] > 0.1
        assert rec["dist_to_hole_boundary_mm"] < 0.8
        # Terminal displacement is locked at 0.297421 mm
        assert abs(rec["actual_terminal_u2"] - 0.297421) < 0.001


def test_far_side_renucleation_damage_growth(full_run_data):
    """Verifies secondary damage band at right edge of hole nucleates around Cycle 41 and reaches > 0.80 at Cycle 56."""
    c40 = full_run_data[40]
    c41 = full_run_data[41]
    c49 = full_run_data[49]
    c56 = full_run_data[56]

    assert c40["far_side_d_max"] < 0.25
    assert c41["far_side_d_max"] >= 0.22  # Nucleates ~0.24 (actual: 0.2398)
    assert c49["far_side_d_max"] > 0.60  # Actual: 0.6241
    assert c56["far_side_d_max"] >= 0.80  # Reaches 0.8288
    assert abs(c56["far_side_d_max"] - 0.8288) < 0.01


def test_report_artifact_integrity():
    """Verifies full run report exists, covers all 57 cycles, and contains key sections."""
    assert os.path.isfile(REPORT_PATH)
    assert os.path.getsize(REPORT_PATH) > 5000
    with open(REPORT_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    assert "Cycles 0 to 56" in content
    assert "0.297421" in content
    assert "38.0342" in content
    assert "0.8288" in content
    assert "HND-METHOD-C-CASE3-FRAMEWORK-LOCAL-FULL-002" in content

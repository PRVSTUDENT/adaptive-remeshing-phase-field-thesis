# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case1_full_run.py
=========================================
Unit tests for Method C Case 1 Full Production Run:
- Benchmark: Pandey & Kumar (2025) Section 4.1 Mode-I Edge-Cracked Plate
- Multi-cycle adaptive remeshing from Cycle 0 through completion (Cycles 0 to 5)
- Verification of:
  1. Full run completion and termination reason (load drop > 95% / ligament severed)
  2. Per-cycle convergence status (all CONVERGED_TO_TARGET, zero cutbacks)
  3. Force continuity gate (|Delta RF2| <= 5.0% across all state transfers)
  4. Zero-healing and damage irreversibility (monotonic d_max progression to 1.0)
  5. Monotonic crack tip advancement along horizontal path (x: 0.50 -> 0.91 mm)
  6. Mesh bounding (element count strictly < 35,000 across all cycles)
  7. Peak load and post-peak softening consistency with benchmark reference
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOCAL_RUN_DIR = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "291_method_c_case1", "local_windows_full_run"
)
FULL_SUMMARY_PATH = os.path.join(LOCAL_RUN_DIR, "METHOD_C_CASE1_FULL_RUN_SUMMARY.json")


def load_full_summary():
    assert os.path.isfile(FULL_SUMMARY_PATH), "Case 1 full run summary JSON not found at: %s" % FULL_SUMMARY_PATH
    with open(FULL_SUMMARY_PATH, "r") as f:
        return json.load(f)


def test_case1_full_run_summary_integrity():
    data = load_full_summary()
    assert data["benchmark"] == "Pandey & Kumar (2025) Section 4.1 Mode-I Edge-Cracked Plate (Case 1)"
    assert data["completed"] is True
    assert data["total_cycles_completed"] == 6  # Cycles 0, 1, 2, 3, 4, 5
    assert "PLATE_SEVERED_LOAD_DROP_BELOW_5PCT" in data["completion_reason"]
    assert data["load_drop_ratio"] < 0.05
    assert data["terminal_rf2_kn"] < 0.05 * data["peak_rf2_kn"]


def test_case1_per_cycle_convergence_and_status():
    data = load_full_summary()
    cycles = data["cycles"]
    assert len(cycles) == 6

    for c in cycles:
        assert c["status"] == "CONVERGED_TO_TARGET"
        sta_path = os.path.join(LOCAL_RUN_DIR, c["job_name"] + ".sta")
        assert os.path.isfile(sta_path), "Missing .sta file for %s" % c["job_name"]
        with open(sta_path, "r") as f:
            sta_content = f.read()
            assert "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in sta_content


def test_case1_force_continuity_gate():
    data = load_full_summary()
    cycles = data["cycles"]

    # Adaptive cycles 1 to 5 evaluate the Step 1 force continuity gate
    for c in cycles[1:]:
        gate = c["gate_results"]
        assert gate["force_continuity_pass"] is True
        assert abs(gate["force_continuity_delta_pct"]) <= 5.0, (
            "Cycle %d force jump %.2f%% exceeds 5.0%% gate" % (c["cycle"], gate["force_continuity_delta_pct"])
        )


def test_case1_zero_healing_monotonic_damage():
    data = load_full_summary()
    cycles = data["cycles"]

    prev_d_max = 0.0
    for c in cycles:
        d_max = c["max_damage"]
        assert d_max >= prev_d_max - 1e-4, (
            "Cycle %d damage healing detected: d_max = %.6f < prev = %.6f" % (c["cycle"], d_max, prev_d_max)
        )
        if c["cycle"] > 0:
            assert c["gate_results"]["zero_healing_pass"] is True
        prev_d_max = d_max

    # Terminal cycle must reach complete damage saturation (d = 1.0)
    assert cycles[-1]["max_damage"] >= 0.9999


def test_case1_crack_tip_advancement_and_arc_length():
    data = load_full_summary()
    cycles = data["cycles"]

    prev_x = 0.5000
    prev_s = 0.0
    for c in cycles:
        tip_x = c["tip_x_mm"]
        tip_y = c["tip_y_mm"]
        s = c["cumulative_arc_length_mm"]

        # Crack tip must stay along horizontal line y = 0.5000 +/- 0.0050 mm
        assert abs(tip_y - 0.5000) <= 0.0050, "Crack deflected off horizontal path: y = %.4f" % tip_y
        # Crack tip x must be monotonic
        assert tip_x >= prev_x - 1e-4, "Tip x decreased: %.4f < %.4f" % (tip_x, prev_x)
        # Cumulative arc length must be monotonic
        assert s >= prev_s - 1e-4, "Arc length decreased: %.4f < %.4f" % (s, prev_s)

        prev_x = tip_x
        prev_s = s

    # Final cycle must have severed > 80% of the 0.5000 mm ligament
    assert cycles[-1]["cumulative_arc_length_mm"] >= 0.4000
    assert cycles[-1]["tip_x_mm"] >= 0.9000


def test_case1_mesh_quality_and_element_count():
    data = load_full_summary()
    for c in data["cycles"]:
        elem_count = c["mesh_elements"]
        assert elem_count < 35000, "Element count %d exceeds 35,000 threshold" % elem_count
        assert elem_count >= 2000, "Element count %d abnormally low" % elem_count


def test_case1_benchmark_reference_comparison():
    data = load_full_summary()
    peak_rf2 = data["peak_rf2_kn"]
    terminal_rf2 = data["terminal_rf2_kn"]

    # Pandey & Kumar (2025) Mode-I peak force is ~0.73 - 0.80 kN
    assert 0.7000 <= peak_rf2 <= 0.8500, "Peak force %.4f kN outside expected benchmark band" % peak_rf2
    # Post-peak load drop must be > 95%
    drop_pct = (1.0 - (terminal_rf2 / peak_rf2)) * 100.0
    assert drop_pct >= 95.0, "Post-peak load drop %.2f%% below 95%% threshold" % drop_pct

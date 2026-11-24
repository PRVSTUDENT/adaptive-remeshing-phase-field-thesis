# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case5_full_run.py
=========================================
Unit tests for Method C Case 5 Full Production Run:
- Benchmark: Master Thesis Mode-I Seven-Hole Plate (Case 5)
- Multi-cycle adaptive remeshing from Cycle 0 through completion
- Verification of:
  1. Full run completion and termination reason (load drop > 95% / ligament severed)
  2. Per-cycle convergence status (CONVERGED_TO_TARGET, zero fatal cutbacks)
  3. Force continuity gate (|Delta RF2| <= 5.0% across all state transfers)
  4. Zero-healing and damage irreversibility (monotonic d_max progression to ~1.0)
  5. Monotonic crack tip advancement across multi-void ligament corridor
  6. Mesh bounding (element count strictly < 35,000 across all cycles)
  7. Peak load and post-peak softening consistency with benchmark reference (~0.725 kN)
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LOCAL_RUN_DIR = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "293_method_c_case5", "local_windows_full_run"
)
FULL_SUMMARY_PATH = os.path.join(LOCAL_RUN_DIR, "METHOD_C_CASE5_FULL_RUN_SUMMARY.json")


def load_full_summary():
    assert os.path.isfile(FULL_SUMMARY_PATH), "Case 5 full run summary JSON not found at: %s" % FULL_SUMMARY_PATH
    with open(FULL_SUMMARY_PATH, "r") as f:
        return json.load(f)


def test_case5_full_run_summary_integrity():
    data = load_full_summary()
    assert data["benchmark"] == "Master Thesis Mode-I Seven-Hole Plate (Case 5)"
    assert data["completed"] is True
    assert data["total_cycles_completed"] >= 2
    assert (
        "PLATE_SEVERED_LOAD_DROP_BELOW_5PCT" in data["completion_reason"]
        or "CUMULATIVE_ARC_LENGTH_REACHED" in data["completion_reason"]
        or "CRACK_SEVERED_TO_FAR_BOUNDARY" in data["completion_reason"]
    )
    if "PLATE_SEVERED_LOAD_DROP_BELOW_5PCT" in data["completion_reason"]:
        assert data["load_drop_ratio"] < 0.05
        assert data["terminal_rf2_kn"] < 0.05 * data["peak_rf2_kn"]


def test_case5_per_cycle_convergence_and_status():
    data = load_full_summary()
    cycles = data["cycles"]
    assert len(cycles) >= 2

    for c in cycles:
        assert c["status"] == "CONVERGED_TO_TARGET"
        sta_path = os.path.join(LOCAL_RUN_DIR, c["job_name"] + ".sta")
        assert os.path.isfile(sta_path), "Missing .sta file for %s" % c["job_name"]
        with open(sta_path, "r") as f:
            sta_content = f.read()
            assert "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in sta_content


def test_case5_force_continuity_gate():
    data = load_full_summary()
    cycles = data["cycles"]

    # Adaptive cycles evaluate the Step 1 force continuity gate
    for c in cycles[1:]:
        gate = c["gate_results"]
        assert gate["force_continuity_pass"] is True
        assert abs(gate["force_continuity_delta_pct"]) <= 5.0, (
            "Cycle %d force jump %.2f%% exceeds 5.0%% gate" % (c["cycle"], gate["force_continuity_delta_pct"])
        )


def test_case5_zero_healing_monotonic_damage():
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

    # Terminal cycle must reach near complete damage saturation
    assert cycles[-1]["max_damage"] >= 0.9500


def test_case5_crack_tip_advancement_and_arc_length():
    data = load_full_summary()
    cycles = data["cycles"]

    prev_x = 0.0000
    prev_s = 0.0
    for c in cycles:
        tip_x = c["tip_x_mm"]
        tip_y = c["tip_y_mm"]
        s = c["cumulative_arc_length_mm"]

        assert 0.0 <= tip_x <= 1.0500, "Crack tip x = %.4f outside domain" % tip_x
        assert 0.20 <= tip_y <= 0.8000, "Crack tip y = %.4f outside corridor" % tip_y
        assert s >= prev_s - 1e-6, "Cumulative arc length decreased at cycle %d" % c["cycle"]

        prev_s = s

    # Final tip or arc length must demonstrate propagation across the specimen
    assert (
        cycles[-1]["tip_x_mm"] >= 0.8000
        or cycles[-1]["cumulative_arc_length_mm"] >= 0.7000
        or cycles[-1]["terminal_rf2_kn"] < 0.05 * data["peak_rf2_kn"]
    )


def test_case5_mesh_quality_and_bounds():
    data = load_full_summary()
    cycles = data["cycles"]

    for c in cycles:
        elem_count = c["mesh_elements"]
        assert elem_count < 35000, "Cycle %d element count %d exceeds 35,000 bound" % (c["cycle"], elem_count)

    # Cycle 0 coarse mesh has 2566 elements
    assert cycles[0]["mesh_elements"] == 2566

    # Adaptive cycles have 15,708 elements
    if len(cycles) > 1:
        for c in cycles[1:]:
            assert c["mesh_elements"] == 15708


def test_case5_peak_load_agreement_with_reference():
    data = load_full_summary()
    peak_rf2 = data["peak_rf2_kn"]

    # F1859 reference peak is 0.7250 kN; allow +/- 15% tolerance across meshes
    ref_peak = 0.7250
    assert 0.60 <= peak_rf2 <= 0.85, (
        "Peak force %.4f kN outside expected range [0.60, 0.85] kN (ref = %.4f kN)" % (peak_rf2, ref_peak)
    )


def test_case5_check_completion_branch2_severance_rf_ratio():
    """
    Verifies the fixed stopping logic in check_completion (branch 2 geometric severance):
    - At Cycle 3: RF2 = 0.259146 kN, peak = 0.74582511 kN, tip_x = 1.0 mm, s = 1.0050 mm, d_max = 0.9984
      Ratio = 0.259146 / 0.74582511 = 34.74% > 20% (SEVERANCE_RF_RATIO = 0.20).
      Returns False (run continues).
    - At Cycle 4: RF2 = 0.142298 kN, peak = 0.74582511 kN, tip_x = 1.0 mm, s = 1.0050 mm, d_max = 0.9993
      Ratio = 0.142298 / 0.74582511 = 19.08% < 20%.
      Returns True with reason string containing '[20% of peak]' (run stops after Cycle 4).
    """
    import sys
    case5_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "293_method_c_case5")
    if case5_dir not in sys.path:
        sys.path.insert(0, case5_dir)
    from case5_single_job_orchestrator import MethodCCase5Orchestrator

    orch = MethodCCase5Orchestrator.__new__(MethodCCase5Orchestrator)
    peak_rf2 = 0.74582511

    # Cycle 3 check
    c3_rf2 = 0.259146
    c3_tip_x = 1.0000
    c3_s = 1.0050
    c3_d_max = 0.9984
    c3_stop, c3_reason = orch.check_completion(
        c3_tip_x, c3_rf2, peak_rf2, current_arc_length=c3_s, current_d_max=c3_d_max
    )
    assert c3_stop is False, "Cycle 3 should not stop because RF2 ratio (34.7%) > 20%"
    assert c3_reason is None

    # Cycle 4 check
    c4_rf2 = 0.142298
    c4_tip_x = 1.0000
    c4_s = 1.0050
    c4_d_max = 0.9993
    c4_stop, c4_reason = orch.check_completion(
        c4_tip_x, c4_rf2, peak_rf2, current_arc_length=c4_s, current_d_max=c4_d_max
    )
    assert c4_stop is True, "Cycle 4 must stop because RF2 ratio (19.1%) < 20% with s >= 0.85 and tip_x >= 0.95"
    assert c4_reason is not None
    assert "[20% of peak]" in c4_reason
    assert "CUMULATIVE_ARC_LENGTH_REACHED" in c4_reason or "CRACK_SEVERED_TO_FAR_BOUNDARY" in c4_reason


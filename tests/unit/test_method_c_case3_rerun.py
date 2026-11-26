# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case3_rerun.py
=======================================
Task: METHOD-C-CASE3-RERUN
Goal: METHOD_C_CASE3_RERUN_V1
Correlation: HND-METHOD-C-CASE3-RERUN-001

Unit test suite verifying:
1. Geometry and material configuration of Case 3
2. Bitwise frozen UEL CE8D5EDC integrity
3. Fixed check_completion stopping logic (RF2 < 5% required across all branches)
4. Adaptive remesh step count comparison (53 steps vs 56 original, 3 steps eliminated)
5. Physical observables at terminal severance (Cycle 53)
6. Case 3 orchestrator dry-run plan verification
7. Comparison summary artifact integrity
8. Comparison figure generation and presence
"""

import os
import sys
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

RERUN_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3_rerun")
if RERUN_DIR not in sys.path:
    sys.path.insert(0, RERUN_DIR)

from case3_single_job_orchestrator import (
    Case3SingleJobOrchestrator,
    CRACK_COMPLETION_ARC_LENGTH_MM,
    CRACK_COMPLETION_X_MM,
    LOAD_DROP_COMPLETION_RATIO,
    SEVERANCE_RF_RATIO,
    PLATE_WIDTH_MM,
    NOTCH_ROOT_X_MM,
    NOTCH_ROOT_Y_MM,
    BENCHMARK_GC_KN_MM,
    BENCHMARK_L0_MM,
    H_REF_MM,
    DT_MIN
)

FROZEN_UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
SUMMARY_PATH = os.path.join(RERUN_DIR, "METHOD_C_CASE3_RERUN_SUMMARY.json")
FIG_PNG = os.path.join(REPO_ROOT, "results", "figures", "fig_method_c_case3_rerun_step_count_comparison.png")
FIG_PDF = os.path.join(REPO_ROOT, "results", "figures", "fig_method_c_case3_rerun_step_count_comparison.pdf")


def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def test_case3_geometry_and_material_configuration():
    """Verifies Case 3 geometric, material, and discretization constants."""
    assert PLATE_WIDTH_MM == 65.0, "Plate width must be 65.0 mm"
    assert NOTCH_ROOT_X_MM == 10.0, "Notch root x must be 10.0 mm"
    assert NOTCH_ROOT_Y_MM == 70.0, "Notch root y must be 70.0 mm"
    assert CRACK_COMPLETION_ARC_LENGTH_MM == 62.0, "Target arc length must be 62.0 mm"
    assert CRACK_COMPLETION_X_MM == 64.0, "Target tip x boundary must be 64.0 mm"
    assert LOAD_DROP_COMPLETION_RATIO == 0.05, "Load drop ratio must be 0.05 (5%)"
    assert SEVERANCE_RF_RATIO == 0.20, "Severance ratio must be 0.20 (20%)"
    assert BENCHMARK_GC_KN_MM == 0.00228, "Gc must be 0.00228 kN/mm"
    assert BENCHMARK_L0_MM == 0.285, "l0 must be 0.285 mm"
    assert H_REF_MM == 0.140, "h_ref must be 0.140 mm (<= l0/2 = 0.1425 mm)"
    assert DT_MIN == 1.0e-14, "dt_min floor must be 1.0e-14"


def test_case3_frozen_uel_bitwise_integrity():
    """Verifies the bitwise frozen UEL source SHA-256 matches CE8D5EDC exactly."""
    assert os.path.isfile(FROZEN_UEL_PATH), "Frozen UEL file must exist: %s" % FROZEN_UEL_PATH
    uel_sha = compute_sha256(FROZEN_UEL_PATH)
    assert uel_sha == EXPECTED_UEL_SHA, "Frozen UEL SHA %s does not match expected %s" % (uel_sha, EXPECTED_UEL_SHA)


def test_case3_orchestrator_stopping_logic_fixed():
    """
    Verifies the fixed stopping logic requiring RF2 < 5% of peak in check_completion:
    - At Cycle 51: RF2 = 0.9907 kN (22.9% of peak) -> returns False.
    - At Cycle 52: s = 62.3665 mm >= 62.0 mm and x = 64.1383 mm >= 64.0 mm,
      but RF2 = 0.6377 kN (14.72% of peak > 5%) -> returns False (must not stop prematurely).
    - At Cycle 53: x = 65.0000 mm, s = 63.2282 mm, RF2 = 0.001694 kN (0.039% of peak < 5%)
      -> returns True (triggers completion upon severance).
    """
    orch = Case3SingleJobOrchestrator.__new__(Case3SingleJobOrchestrator)
    peak_rf2 = 4.331822

    # Cycle 51 check
    c51_stop, c51_reason = orch.check_completion(
        current_tip_x=62.6614,
        current_rf2=0.990666,
        peak_rf2=peak_rf2,
        current_arc_length=60.6506,
        current_d_max=1.0
    )
    assert c51_stop is False, "Cycle 51 must not stop (RF2 = 22.9% of peak, x = 62.66 mm)"
    assert c51_reason is None

    # Cycle 52 check (critical: geometric criteria met, but load drop > 5%)
    c52_stop, c52_reason = orch.check_completion(
        current_tip_x=64.1383,
        current_rf2=0.637734,
        peak_rf2=peak_rf2,
        current_arc_length=62.3665,
        current_d_max=1.0
    )
    assert c52_stop is False, "Cycle 52 must not stop because RF2 ratio (14.72%) > 5% of peak"
    assert c52_reason is None

    # Cycle 53 check (severance reached: x = 65.0 mm, s = 63.23 mm, RF2 = 0.039% < 5%)
    c53_stop, c53_reason = orch.check_completion(
        current_tip_x=65.0000,
        current_rf2=0.001694,
        peak_rf2=peak_rf2,
        current_arc_length=63.2282,
        current_d_max=1.0
    )
    assert c53_stop is True, "Cycle 53 must stop because RF2 (0.039%) < 5% of peak with complete severance"
    assert c53_reason is not None
    assert "PLATE_SEVERED_LOAD_DROP_BELOW_5PCT" in c53_reason
    assert "0.0017 kN" in c53_reason or "0.001694" in c53_reason or "5%" in c53_reason


def test_case3_adaptive_step_count_comparison():
    """
    Verifies the adaptive remesh step count comparison between the original run and improved framework:
    - Original run: 56 adaptive remesh steps (Cycles 0 to 56, 57 cycles).
    - Improved framework: 53 adaptive remesh steps (Cycles 0 to 53, 54 cycles).
    - Step count reduction: exactly 3 steps fewer (Cycles 54, 55, 56 eliminated).
    """
    assert os.path.isfile(SUMMARY_PATH), "Summary artifact must exist: %s" % SUMMARY_PATH
    with open(SUMMARY_PATH, "r") as f:
        data = json.load(f)

    orig = data["original_run"]
    rerun = data["improved_framework_rerun"]

    assert orig["adaptive_remesh_steps"] == 56, "Original run must record 56 adaptive remesh steps"
    assert orig["terminal_cycle"] == 56, "Original run terminal cycle must be 56"
    assert orig["total_cycles_executed"] == 57, "Original run total cycles must be 57"

    assert rerun["adaptive_remesh_steps"] == 53, "Improved framework must take 53 adaptive remesh steps"
    assert rerun["terminal_cycle"] == 53, "Improved framework terminal cycle must be 53"
    assert rerun["total_cycles_executed"] == 54, "Improved framework total cycles must be 54"

    assert rerun["adaptive_step_reduction"] == 3, "Adaptive step reduction must be exactly 3 steps"
    assert abs(rerun["adaptive_step_reduction_pct"] - 5.357) < 0.1, "Reduction pct must be ~5.36%"


def test_case3_physical_observables_at_severance():
    """Verifies physical observables at terminal severance (Cycle 53)."""
    with open(SUMMARY_PATH, "r") as f:
        data = json.load(f)

    rerun = data["improved_framework_rerun"]
    assert rerun["terminal_tip_x_mm"] == 65.0, "Terminal tip x must be 65.0 mm (specimen edge)"
    assert rerun["terminal_tip_y_mm"] == 52.0, "Terminal tip y must be 52.0 mm"
    assert abs(rerun["terminal_rf2_kN"] - 0.001694) < 1.0e-5, "Terminal RF2 must be ~0.001694 kN"
    assert rerun["terminal_rf2_ratio_pct"] < 0.05, "Terminal load ratio must be < 0.05% of peak"
    assert rerun["load_drop_pct"] > 99.95, "Load drop must exceed 99.95%"


def test_case3_dry_run_plan():
    """Verifies Case 3 orchestrator dry-run plan generation."""
    orch = Case3SingleJobOrchestrator(
        run_dir=RERUN_DIR,
        n_adaptive_steps=4,
        load_increment_mm=0.0100,
        coarse_u2_mm=0.0500,
        dry_run=True
    )
    plan = orch.run_dry_run_plan()
    assert plan["architecture"] == "SINGLE_PBS_JOB_IN_ALLOCATION_ORCHESTRATOR"
    assert len(plan["planned_initial_cycles"]) == 5
    assert plan["configuration"]["crack_completion_criteria"]["primary_arc_length_mm"] == 62.0
    assert plan["configuration"]["crack_completion_criteria"]["terminal_tip_x_mm"] == 64.0
    assert plan["configuration"]["crack_completion_criteria"]["load_drop_cutoff_ratio"] == 0.05
    assert plan["corridor"]["h_ref_mm"] == 0.140
    assert plan["corridor"]["target_total_elements_bounded"] == 35000


def test_case3_comparison_figures_exist():
    """Verifies high-resolution comparison figure files exist."""
    assert os.path.isfile(FIG_PNG), "Figure PNG must exist: %s" % FIG_PNG
    assert os.path.isfile(FIG_PDF), "Figure PDF must exist: %s" % FIG_PDF
    assert os.path.getsize(FIG_PNG) > 10000, "Figure PNG size must exceed 10 KB"
    assert os.path.getsize(FIG_PDF) > 5000, "Figure PDF size must exceed 5 KB"

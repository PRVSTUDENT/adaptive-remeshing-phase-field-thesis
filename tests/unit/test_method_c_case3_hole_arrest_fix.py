# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_case3_hole_arrest_fix.py
=================================================
Task: METHOD-C-CASE3-HOLE-ARREST-CONVERGENCE-FIX
Checkpoint: (a) After implementing Fix 1 (Far-Side Secondary Refinement Zone)

Verifies:
1. Far-side refinement zone covers the observed far-side damage coordinates
   (Node 16 at (46.5, 51.0) mm and Node 4876 across x in [46.5, 50.6] mm).
2. Refinement size h_ref is strictly 0.140 mm (identical to tip band).
3. Primary narrow tip-following band remains completely unchanged (height 2.0 mm,
   half-width 1.0 mm, h_ref 0.140 mm).
4. Far-side band activates automatically when crack reaches the hole region (tip_x >= 35.0 mm).
5. Orchestrator supports --resume-cycle 48 for clean resumption from Cycle 48 checkpoint.
"""

import os
import sys
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.case3_single_job_orchestrator import (
    compute_narrow_band_spec,
    Case3SingleJobOrchestrator,
    BENCHMARK_L0_MM,
    H_REF_MM,
    BAND_HALF_WIDTH_MM,
    BAND_HEIGHT_MM,
    FAR_SIDE_BAND_X_MIN,
    FAR_SIDE_BAND_X_MAX,
    FAR_SIDE_BAND_Y_MIN,
    FAR_SIDE_BAND_Y_MAX,
    FAR_SIDE_CENTER_X,
    FAR_SIDE_CENTER_Y,
    FAR_SIDE_H_REF_MM,
)
from scripts.remeshing.generate_case3_adaptive_corridor_mesh import (
    get_corridor_partition_spec,
)

PACKAGE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3")
UEL_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")


def test_far_side_band_covers_observed_damage_coordinates():
    """Verify that the secondary refinement zone strictly encloses the observed far-side damage band."""
    # Cycle 48 crack tip position at hole arrival
    tip_x = 37.9452
    tip_y = 61.3786

    spec = compute_narrow_band_spec(tip_x=tip_x, tip_y=tip_y, enable_far_side_band=True)
    assert spec["enable_far_side_band"] is True
    fs = spec["far_side_band"]
    assert fs is not None

    # Check box bounds
    assert fs["x_min_mm"] == 44.0
    assert fs["x_max_mm"] == 54.0
    assert fs["y_min_mm"] == 44.0
    assert fs["y_max_mm"] == 58.0

    # Node 16 (dominant far-side damage peak at hole right edge)
    node16_x = 46.50
    node16_y = 51.00
    assert fs["x_min_mm"] <= node16_x <= fs["x_max_mm"]
    assert fs["y_min_mm"] <= node16_y <= fs["y_max_mm"]

    # Node 4876 (secondary damage peak at x = 48.51 mm, y = 51.00 mm)
    node4876_x = 48.51
    node4876_y = 51.00
    assert fs["x_min_mm"] <= node4876_x <= fs["x_max_mm"]
    assert fs["y_min_mm"] <= node4876_y <= fs["y_max_mm"]

    # Full observed macroscopic damage band x in [46.5, 50.6] mm
    band_x_start = 46.5
    band_x_end = 50.6
    assert fs["x_min_mm"] < band_x_start
    assert fs["x_max_mm"] > band_x_end

    # Margin check
    margin_x_left = band_x_start - fs["x_min_mm"]  # 2.5 mm
    margin_x_right = fs["x_max_mm"] - band_x_end   # 3.4 mm
    assert margin_x_left >= 2.0
    assert margin_x_right >= 2.0


def test_far_side_band_refinement_size_and_center():
    """Verify that the far-side refinement size is h_ref = 0.140 mm and centered on Node 16."""
    spec = compute_narrow_band_spec(tip_x=37.9452, tip_y=61.3786, enable_far_side_band=True)
    fs = spec["far_side_band"]
    assert fs is not None

    # Refinement size matches tip band
    assert fs["h_ref_mm"] == 0.140
    assert fs["h_ref_mm"] == H_REF_MM
    assert fs["h_ref_mm"] <= (BENCHMARK_L0_MM / 2.0)  # 0.1425 mm

    # Center is Node 16 at (46.5, 51.0) mm
    assert fs["center_x_mm"] == 46.5
    assert fs["center_y_mm"] == 51.0

    # Dimensions
    assert fs["width_mm"] == 10.0
    assert fs["height_mm"] == 14.0
    assert fs["area_mm2"] == 140.0


def test_tip_band_unchanged_with_far_side_band():
    """Verify that the primary narrow tip-following band remains completely unchanged."""
    # 1. At hole arrival (tip_x = 37.9452, tip_y = 61.3786)
    spec_hole = compute_narrow_band_spec(tip_x=37.9452, tip_y=61.3786)
    assert spec_hole["half_width_mm"] == 1.0
    assert spec_hole["band_height_mm"] == 2.0
    assert spec_hole["h_ref_mm"] == 0.140
    assert spec_hole["tip_x"] == 37.9452
    assert spec_hole["tip_y"] == 61.3786
    assert spec_hole["x_min"] == 8.5
    assert spec_hole["x_max"] == min(65.0, 37.9452 + 2.0)

    # 2. At initial notch state (tip_x = 10.0, tip_y = 70.0)
    spec_init = compute_narrow_band_spec(tip_x=10.0, tip_y=70.0)
    assert spec_init["enable_far_side_band"] is False
    assert spec_init["far_side_band"] is None
    assert spec_init["x_min"] == 8.5
    assert spec_init["x_max"] == 12.0
    assert spec_init["half_width_mm"] == 1.0
    assert spec_init["band_height_mm"] == 2.0
    assert spec_init["h_ref_mm"] == 0.140


def test_far_side_band_activation_threshold():
    """Verify activation logic: inactive at notch, active at hole or upon explicit flag."""
    # Inactive by default at notch root (tip_x = 10.0)
    spec_early = compute_narrow_band_spec(tip_x=10.0, tip_y=70.0)
    assert spec_early["enable_far_side_band"] is False
    assert spec_early["far_side_band"] is None

    # Inactive by default at ligament midpoint (tip_x = 25.0)
    spec_mid = compute_narrow_band_spec(tip_x=25.0, tip_y=65.0)
    assert spec_mid["enable_far_side_band"] is False
    assert spec_mid["far_side_band"] is None

    # Active in orchestrator at hole approach (tip_x = 35.0 >= 35.0)
    orch = Case3SingleJobOrchestrator(run_dir=PACKAGE_DIR, uel_path=UEL_PATH)
    orch_approach = orch.get_corridor_definition(tip_x=35.0, tip_y=55.0)
    assert orch_approach["enable_far_side_band"] is True
    assert orch_approach["far_side_band"] is not None

    # Explicit flag forces activation even in raw compute_narrow_band_spec at notch
    spec_forced = compute_narrow_band_spec(tip_x=10.0, tip_y=70.0, enable_far_side_band=True)
    assert spec_forced["enable_far_side_band"] is True
    assert spec_forced["far_side_band"] is not None


def test_orchestrator_resume_cycle_option():
    """Verify that Case3SingleJobOrchestrator accepts resume_cycle parameter and records it."""
    orch = Case3SingleJobOrchestrator(
        run_dir=PACKAGE_DIR,
        uel_path=UEL_PATH,
        resume_cycle=48
    )
    assert orch.resume_cycle == 48

    corridor = orch.get_corridor_definition(tip_x=37.9452, tip_y=61.3786)
    assert corridor["far_side_band"] is not None
    assert corridor["enable_far_side_band"] is True
    assert corridor["far_side_band"]["h_ref_mm"] == 0.140


def test_mesh_generator_partition_spec_integration():
    """Verify get_corridor_partition_spec in mesh generator returns far-side band spec."""
    spec = get_corridor_partition_spec(tip_x=37.9452, tip_y=61.3786)
    assert spec["enable_far_side_band"] is True
    assert spec["far_side_band"] is not None
    assert spec["far_side_band"]["h_ref_mm"] == 0.140
    assert spec["far_side_band"]["center_x_mm"] == 46.5
    assert spec["far_side_band"]["center_y_mm"] == 51.0

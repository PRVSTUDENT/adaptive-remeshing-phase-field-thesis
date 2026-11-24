# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_framework_phase1c.py
============================================
Task: METHOD-C-FRAMEWORK-PHASE1C-ARC-LENGTH-CRACK-MEASURE
Correlation: HND-METHOD-C-FRAMEWORK-PHASE1C-001

Unit test suite verifying Phase 1(c) improvements for Method C Case 3:
1. Cumulative crack arc-length calculation along straight and curved paths.
2. Capturing crack progression around the central hole where tip_x plateaus (Cycles 30-48).
3. Monotonic crack arc-length growth across Phase 1(b) wake-preserving data (Cycles 49-52).
4. Primary completion evaluation based on cumulative arc length (s >= 62.0 mm).
5. Framework manifest integrity (mesh generator D9E5687B, orchestrator 9DDE7BB8, frozen UEL CE8D5EDC).
"""

import os
import sys
import json
import math
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3"))

from case3_single_job_orchestrator import (
    compute_cumulative_crack_arc_length,
    Case3SingleJobOrchestrator,
    NOTCH_ROOT_X_MM,
    NOTCH_ROOT_Y_MM,
    CRACK_COMPLETION_ARC_LENGTH_MM,
    CRACK_COMPLETION_X_MM,
    LOAD_DROP_COMPLETION_RATIO,
    FROZEN_UEL_SHA256,
)

LOCAL_FULL_RUN_DIR = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "local_windows_full_run"
)
PHASE1B_VAL_DIR = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "phase1b_wake_preserving_validation"
)
MANIFEST_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "METHOD_C_CASE3_FRAMEWORK_MANIFEST.json"
)
ORCH_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "case3_single_job_orchestrator.py"
)
MESH_GEN_PATH = os.path.join(
    REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3", "generate_case3_adaptive_corridor_mesh.py"
)


def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def test_arc_length_straight_line():
    """Verify cumulative arc length on horizontal straight-line crack trajectory."""
    tips = [(20.0, 70.0), (30.0, 70.0), (45.0, 70.0)]
    s = compute_cumulative_crack_arc_length(tips, notch_root=(10.0, 70.0))
    # (10->20) + (20->30) + (30->45) = 10 + 10 + 15 = 35.0 mm
    assert s == 35.0, "Expected straight-line arc length 35.0 mm, got %f" % s


def test_arc_length_curved_path_around_hole():
    """Verify that vertical crack growth around hole increases arc length while x remains constant."""
    # Synthetic crack arrested in x at x=37.95 mm curving in y: 61.4 -> 59.4 -> 57.4 mm
    tips = [
        (37.95, 61.4),
        (37.95, 59.4),
        (37.95, 57.4),
    ]
    s1 = compute_cumulative_crack_arc_length(tips[:1], notch_root=(10.0, 70.0))
    s2 = compute_cumulative_crack_arc_length(tips[:2], notch_root=(10.0, 70.0))
    s3 = compute_cumulative_crack_arc_length(tips, notch_root=(10.0, 70.0))

    # Delta x is zero between step 1, 2, and 3
    assert tips[1][0] == tips[0][0]
    assert tips[2][0] == tips[1][0]

    # Delta s must strictly increase by the 2.0 mm vertical segments
    assert pytest.approx(s2 - s1, abs=1e-4) == 2.0
    assert pytest.approx(s3 - s2, abs=1e-4) == 2.0
    assert s3 > s2 > s1


def test_arc_length_hole_arrest_plateau_capture():
    """
    Verify on authentic Case 3 Cycles 30 to 48 data that cumulative arc length
    captures ~3.12 mm of authentic physical growth while x_tip is plateaued (Delta x = 0.08 mm).
    """
    cycle_tips = {}
    for c in range(49):
        p = os.path.join(LOCAL_FULL_RUN_DIR, "PK_METHOD_C_CASE3_CYCLE%d_SUMMARY.json" % c)
        if os.path.isfile(p):
            with open(p, "r") as f:
                d = json.load(f)
            cycle_tips[c] = (float(d["tip_x"]), float(d["tip_y"]))

    assert 30 in cycle_tips, "Cycle 30 summary must exist"
    assert 48 in cycle_tips, "Cycle 48 summary must exist"

    sorted_cycles = sorted(cycle_tips.keys())
    c30_idx = sorted_cycles.index(30)
    c48_idx = sorted_cycles.index(48)

    pts_up_to_30 = [cycle_tips[c] for c in sorted_cycles[:c30_idx + 1]]
    pts_up_to_48 = [cycle_tips[c] for c in sorted_cycles[:c48_idx + 1]]

    s30 = compute_cumulative_crack_arc_length(pts_up_to_30, notch_root=(10.0, 70.0))
    s48 = compute_cumulative_crack_arc_length(pts_up_to_48, notch_root=(10.0, 70.0))

    tip_x_30 = cycle_tips[30][0]
    tip_x_48 = cycle_tips[48][0]
    delta_x = tip_x_48 - tip_x_30
    delta_s = s48 - s30

    # x_tip plateau: Delta x is only 0.08 mm over 18 cycles
    assert pytest.approx(delta_x, abs=1e-3) == 0.080, "Delta x in Cycles 30-48 should be 0.08 mm"
    assert delta_x <= 0.10, "x_tip is severely plateaued during hole arrest"

    # Cumulative arc length continues advancing significantly (> 3.0 mm)
    assert pytest.approx(delta_s, abs=1e-2) == 3.12, "Delta s in Cycles 30-48 should be ~3.12 mm"
    assert delta_s > 3.0, "Arc-length measure successfully captures growth around hole during arrest"


def test_arc_length_monotonicity_phase1b():
    """
    Verify that across Phase 1(b) wake-preserving validation cycles (Cycles 49 to 52),
    cumulative crack arc length grows strictly monotonically despite slight x_tip lag.
    """
    # Load prior full-run trajectory up to Cycle 48
    pts_up_to_48 = []
    for c in range(49):
        p = os.path.join(LOCAL_FULL_RUN_DIR, "PK_METHOD_C_CASE3_CYCLE%d_SUMMARY.json" % c)
        if os.path.isfile(p):
            with open(p, "r") as f:
                d = json.load(f)
            pts_up_to_48.append((float(d["tip_x"]), float(d["tip_y"])))

    s48 = compute_cumulative_crack_arc_length(pts_up_to_48, notch_root=(10.0, 70.0))
    assert pytest.approx(s48, abs=0.01) == 33.49, "Cycle 48 arc length should be 33.49 mm"

    p1b_s_values = []
    current_pts = list(pts_up_to_48)
    for c in range(49, 53):
        p = os.path.join(PHASE1B_VAL_DIR, "PK_METHOD_C_CASE3_CYCLE%d_SUMMARY.json" % c)
        assert os.path.isfile(p), "Phase 1(b) Cycle %d summary must exist" % c
        with open(p, "r") as f:
            d = json.load(f)
        current_pts.append((float(d["tip_x"]), float(d["tip_y"])))
        s_c = compute_cumulative_crack_arc_length(current_pts, notch_root=(10.0, 70.0))
        p1b_s_values.append((c, s_c, float(d["tip_x"]), float(d["tip_y"])))

    # Expected values:
    # Cycle 49: ~51.46 mm (snap-through re-nucleation across void)
    # Cycle 50: ~56.83 mm
    # Cycle 51: ~60.65 mm
    # Cycle 52: ~62.37 mm
    assert pytest.approx(p1b_s_values[0][1], abs=0.02) == 51.46
    assert pytest.approx(p1b_s_values[1][1], abs=0.02) == 56.83
    assert pytest.approx(p1b_s_values[2][1], abs=0.02) == 60.65
    assert pytest.approx(p1b_s_values[3][1], abs=0.02) == 62.37

    # Strict monotonicity verification: s_k > s_{k-1}
    for i in range(1, len(p1b_s_values)):
        prev_s = p1b_s_values[i - 1][1]
        curr_s = p1b_s_values[i][1]
        assert curr_s > prev_s, "Cycle %d arc length (%f) must exceed Cycle %d arc length (%f)" % (
            p1b_s_values[i][0], curr_s, p1b_s_values[i - 1][0], prev_s
        )


def test_check_completion_primary_arc_length():
    """Verify check_completion triggers on primary arc length s >= 62.0 mm."""
    orch = Case3SingleJobOrchestrator(
        run_dir=LOCAL_FULL_RUN_DIR,
        dry_run=True
    )

    peak_rf2 = 4.3318

    # 1. Below completion on all measures (Cycle 50: s = 56.83 mm, tip_x = 58.42 mm, RF2 = 1.63 kN)
    done, reason = orch.check_completion(current_tip_x=58.42, current_rf2=1.63, peak_rf2=peak_rf2, current_arc_length=56.83)
    assert not done
    assert reason is None

    # 2. Primary criterion met: s >= 62.0 mm (Cycle 52: s = 62.37 mm, tip_x = 63.95 mm < 64.0 mm, RF2 = 0.738 kN > 5% peak)
    done, reason = orch.check_completion(current_tip_x=63.9531, current_rf2=0.738, peak_rf2=peak_rf2, current_arc_length=62.365)
    assert done
    assert "CRACK_ARC_LENGTH_COMPLETION_REACHED" in reason
    assert "s = 62.3650 mm >= 62.0 mm" in reason

    # 3. Secondary criterion met: tip_x >= 64.0 mm
    done, reason = orch.check_completion(current_tip_x=64.20, current_rf2=0.50, peak_rf2=peak_rf2, current_arc_length=61.5)
    assert done
    assert "CRACK_FULLY_PROPAGATED_TO_PLATE_EDGE" in reason

    # 4. Secondary criterion met: load drop below 5% of peak (RF2 < 0.2166 kN)
    done, reason = orch.check_completion(current_tip_x=60.0, current_rf2=0.15, peak_rf2=peak_rf2, current_arc_length=59.0)
    assert done
    assert "PLATE_SEVERED_LOAD_DROP_BELOW_5PCT" in reason


def test_framework_manifest_sha_verification():
    """
    Verify GAP-P1B-06 resolution and Phase 1(c) manifest integrity:
    1. Mesh generator SHA-256 matches D9E5687B...
    2. Orchestrator SHA-256 matches actual file SHA (9DDE7BB8...)
    3. Frozen UEL SHA-256 matches CE8D5EDC...
    4. Primary arc length criterion (62.0 mm) is registered.
    """
    assert os.path.isfile(MANIFEST_PATH), "Manifest must exist"
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    # 1. Mesh generator SHA
    expected_mesh_sha = "D9E5687BCA3F3A94639A2D0E4CFDEED85A57E4C697062E7BFC077778E4109AE4"
    actual_mesh_sha = compute_sha256(MESH_GEN_PATH)
    manifest_mesh_sha = manifest["single_job_architecture"]["mesh_generator"]["sha256"]
    assert actual_mesh_sha == expected_mesh_sha
    assert manifest_mesh_sha == expected_mesh_sha

    # 2. Orchestrator SHA
    actual_orch_sha = compute_sha256(ORCH_PATH)
    manifest_orch_sha = manifest["single_job_architecture"]["orchestrator_script"]["sha256"]
    assert actual_orch_sha == manifest_orch_sha

    # 3. Frozen UEL SHA
    manifest_uel_sha = manifest["single_job_architecture"]["frozen_uel"]["sha256"]
    assert manifest_uel_sha == FROZEN_UEL_SHA256

    # 4. Primary arc length criterion registered in manifest
    crit = manifest["adaptive_schedule_parameters"]["crack_completion_criteria"]
    assert crit.get("primary_arc_length_mm") == 62.0
    assert crit.get("terminal_tip_x_mm") == 64.0
    assert crit.get("load_drop_cutoff_ratio") == 0.05

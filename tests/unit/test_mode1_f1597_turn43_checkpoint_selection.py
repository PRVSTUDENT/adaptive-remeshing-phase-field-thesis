#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_turn43_checkpoint_selection.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2

Unit test verifying the scientific checkpoint selection criteria between:
- Package 76 (Authentic Donor Reference, h=2.5 um, 1600 quads)
- Package 87 (Candidate C2 Virgin Mesh, h=1.0 um, 2300 quads)
"""

import os
import json
import pytest

TELEMETRY_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "results", "validation", "mode1_f1597", "p76_p87_checkpoint_candidates.json"
)

@pytest.fixture
def candidate_data():
    assert os.path.exists(TELEMETRY_PATH), "Checkpoint candidates JSON must exist: %s" % TELEMETRY_PATH
    with open(TELEMETRY_PATH, "r") as fp:
        return json.load(fp)

def test_checkpoint_telemetry_status(candidate_data):
    assert candidate_data["status"] == "CHECKPOINT_CANDIDATE_EVALUATION_SUCCESS"
    assert "p76_summary" in candidate_data
    assert "p87_summary" in candidate_data
    assert len(candidate_data["comparisons"]) > 0

def test_force_continuity_in_prepeak_earlypropagation_window(candidate_data):
    """
    Verifies that for displacements u <= 0.00199 mm,
    the relative difference between donor RF2 and virgin C2 RF2 is strictly <= 5%.
    """
    comps = candidate_data["comparisons"]
    valid_window_comps = [c for c in comps if c["u_mm"] <= 0.0019901]
    assert len(valid_window_comps) >= 15, "Expected at least 15 comparison points in [0.00170, 0.00199] mm"
    for c in valid_window_comps:
        diff_pct = abs(c["rf2_diff_pct"])
        assert diff_pct <= 5.0, (
            "Force difference at u=%.7f mm was %.3f%%, exceeding the 5.0%% threshold"
            % (c["u_mm"], diff_pct)
        )
        assert c["meets_5pct_gate"] is True

def test_divergence_onset_beyond_2um(candidate_data):
    """
    Verifies that for displacements u >= 0.002015 mm,
    mesh-dependent localization causes C2 reaction force to drop significantly faster,
    failing the 5% gate, confirming Decision B.
    """
    comps = candidate_data["comparisons"]
    post_window_comps = [c for c in comps if c["u_mm"] >= 0.002015]
    assert len(post_window_comps) >= 2
    for c in post_window_comps:
        assert c["meets_5pct_gate"] is False
        assert c["rf2_diff_pct"] < -5.0

def test_selected_candidate_checkpoint_frame83_and_frame88(candidate_data):
    """
    Inspects candidate checkpoints:
    1. Donor Frame 83 (Donor Peak at u=0.0018821 mm): Diff = +0.650%
    2. Donor Frame 88 (Early propagation at u=0.0019651 mm, sdv1_max=0.4906): Diff = -0.780%
    Both candidates satisfy the strict <= 5% criterion.
    """
    comps = candidate_data["comparisons"]
    # Check Frame 83 equivalent (u ~= 0.00188205 mm)
    f83_matches = [c for c in comps if abs(c["u_mm"] - 0.00188205) < 1e-6]
    assert len(f83_matches) == 1
    assert abs(f83_matches[0]["rf2_diff_pct"]) < 1.0

    # Check Frame 88 equivalent (u ~= 0.0019651 mm)
    f88_matches = [c for c in comps if abs(c["u_mm"] - 0.0019651) < 1e-6]
    assert len(f88_matches) == 1
    assert abs(f88_matches[0]["rf2_diff_pct"]) < 1.0

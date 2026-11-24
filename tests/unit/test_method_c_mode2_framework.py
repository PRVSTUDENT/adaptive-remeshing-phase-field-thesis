# -*- coding: utf-8 -*-
"""
tests/unit/test_method_c_mode2_framework.py
===========================================
Unit tests for Method C Mode-II Framework Setup (HND-METHOD-C-MODE2-LPANEL-002).
Verifies:
1. Dynamic oblique deflection corridor specification (h_ref <= l0/2 = 0.0075 mm, count < 35,000).
2. Mode-II 3-layer coupled deck assembly (*EQUATION coupling, boundary conditions, SVARS).
3. Mode-II completion logic (Branch 1 load drop < 5% and Branch 2 geometric severance to bottom edge).
4. Physical mesh parsing and node-set generation.
"""

import os
import sys
import math
import tempfile
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "294_method_c_mode2"))

from generate_mode2_adaptive_corridor_mesh import compute_corridor_spec, evaluate_corridor_audit
from mode2_single_job_orchestrator import (
    assemble_mode2_coupled_deck,
    check_mode2_completion,
    compute_cumulative_crack_arc_length,
    parse_physical_mesh,
    BENCHMARK_L0_MM,
    H_REF_MM,
    BENCHMARK_GC_KN_MM
)


def test_mode2_corridor_specification_and_sizing():
    """Verify corridor bounds and sizing comply strictly with l0/2 and element budget limits."""
    # At initial notch root (0.50, 0.50)
    spec0 = compute_corridor_spec(tip_x=0.5000, tip_y=0.5000)
    assert spec0["x_min"] == 0.4500
    assert spec0["x_max"] == 0.6500
    assert spec0["y_min"] == 0.3500
    assert spec0["y_max"] == 0.5500
    assert spec0["h_ref_mm"] <= spec0["l0_half_mm"]
    assert spec0["h_ref_mm"] <= 0.0075
    assert spec0["estimated_total_elements"] < 35000

    # At advanced deflected position (0.70, 0.20)
    spec_adv = compute_corridor_spec(tip_x=0.7000, tip_y=0.2000)
    assert spec_adv["x_max"] >= 0.8000 - 1e-6
    assert spec_adv["y_min"] <= 0.1000
    assert spec_adv["estimated_total_elements"] < 35000


def test_mode2_coupled_deck_assembly():
    """Verify that assemble_mode2_coupled_deck generates a valid 3-layer UEL deck with correct shear BCs."""
    r_nodes = {
        1: (0.0, 0.0),
        2: (1.0, 0.0),
        3: (1.0, 1.0),
        4: (0.0, 1.0),
        5: (0.5, 0.5)
    }
    r_quads = {
        1: [1, 2, 5, 4]
    }
    r_tris = {}

    transferred_damage = {n: 0.25 for n in r_nodes}
    transferred_history = {1: 1.5e-4}

    with tempfile.NamedTemporaryFile("w", delete=False, suffix=".inp") as f:
        out_deck = f.name

    try:
        assemble_mode2_coupled_deck(
            out_deck_path=out_deck,
            r_nodes=r_nodes,
            r_quads=r_quads,
            r_tris=r_tris,
            donor_ux=0.0095,
            target_ux=0.0110,
            transferred_damage=transferred_damage,
            transferred_history=transferred_history,
            E_GPa=210.0,
            nu=0.30,
            Gc=0.0027,
            l0=0.0150,
            k_res=1e-7,
            use_riks=True
        )

        with open(out_deck, "r") as f:
            deck_content = f.read()

        # Check UEL declarations
        assert "*USER ELEMENT, NODES=4, TYPE=U1" in deck_content
        assert "*USER ELEMENT, NODES=4, TYPE=U2" in deck_content
        assert "*ELEMENT, TYPE=CPE4, ELSET=umatelem_quad" in deck_content

        # Check shear boundary conditions
        assert "*NSET, NSET=N_BOTTOM" in deck_content
        assert "*NSET, NSET=N_TOP" in deck_content
        assert "*NSET, NSET=N_RP" in deck_content
        assert "*EQUATION" in deck_content

        # Check Step 1 and Step 2
        assert "*STEP, NAME=Step-1" in deck_content
        assert "9.50000000e-03" in deck_content  # donor_ux
        assert "*STEP, NAME=Step-2" in deck_content
        assert "*STATIC, RIKS" in deck_content
        assert "1.10000000e-02" in deck_content  # target_ux

        # Check transferred state SVARS
        assert "2.500000e-01" in deck_content  # d_val = 0.25
        assert "1.500000e-04" in deck_content  # h_val = 1.5e-4
    finally:
        if os.path.exists(out_deck):
            os.remove(out_deck)


def test_mode2_completion_logic():
    """Verify completion criteria: Branch 1 (<5% load drop) and Branch 2 (bottom edge severance + <20% RF)."""
    peak_rf1 = 0.5500

    # Intermediate unsevered state
    complete, reason = check_mode2_completion(
        current_cycle=1,
        peak_rf1=peak_rf1,
        terminal_rf1=0.5200,
        tip_x=0.5500,
        tip_y=0.4500,
        arc_length_s=0.0700,
        max_damage=0.85
    )
    assert complete is False
    assert reason == "IN_PROGRESS"

    # Branch 1: Complete load drop (< 5% of peak)
    complete, reason = check_mode2_completion(
        current_cycle=5,
        peak_rf1=peak_rf1,
        terminal_rf1=0.0200,  # 3.6% < 5%
        tip_x=0.8200,
        tip_y=0.0200,
        arc_length_s=0.5800,
        max_damage=0.999
    )
    assert complete is True
    assert "COMPLETE_LOAD_DROP_BELOW_5PCT" in reason

    # Branch 2: Geometric severance to bottom edge (tip_y <= 0.05 mm, s >= 0.50 mm, d >= 0.95, RF1 < 20%)
    complete, reason = check_mode2_completion(
        current_cycle=4,
        peak_rf1=peak_rf1,
        terminal_rf1=0.0800,  # 14.5% < 20%
        tip_x=0.8150,
        tip_y=0.0350,  # <= 0.05 mm
        arc_length_s=0.5500,  # >= 0.50 mm
        max_damage=0.995
    )
    assert complete is True
    assert "COMPLETE_SPECIMEN_SEVERED_TO_BOTTOM_EDGE" in reason

    # Branch 2 blocked if RF1 >= 20% of peak
    complete, reason = check_mode2_completion(
        current_cycle=3,
        peak_rf1=peak_rf1,
        terminal_rf1=0.1500,  # 27.3% > 20%
        tip_x=0.8000,
        tip_y=0.0400,
        arc_length_s=0.5200,
        max_damage=0.98
    )
    assert complete is False
    assert reason == "IN_PROGRESS"


def test_cumulative_crack_arc_length_calculation():
    """Verify Euclidean crack arc-length accumulation along oblique path."""
    tip_history = [
        (0.52, 0.45),
        (0.56, 0.38),
        (0.62, 0.28),
        (0.70, 0.15)
    ]
    s = compute_cumulative_crack_arc_length(tip_history, notch_root=(0.50, 0.50))
    # Expected: hypot(0.02, -0.05) + hypot(0.04, -0.07) + hypot(0.06, -0.10) + hypot(0.08, -0.13)
    exp = (math.hypot(0.02, 0.05) + math.hypot(0.04, 0.07) +
           math.hypot(0.06, 0.10) + math.hypot(0.08, 0.13))
    assert abs(s - exp) < 1e-4
    assert s > 0.35

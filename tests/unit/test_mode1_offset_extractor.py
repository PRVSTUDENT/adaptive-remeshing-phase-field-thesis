#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Targeted regression test for extract_mode1_offset_results.py.
Verifies resolution of Package 60 extraction-index defect and independent qualification of Package 72.
"""

import sys
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.postprocessing.extract_mode1_offset_results import (
    parse_dat_rp_reactions,
    parse_dat_nodal_displacements,
    parse_energy_balance_csv,
    evaluate_offset_simulation
)

MODELS_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1"
PKG60_EV = MODELS_DIR / "60_method_c_smooth_h_nonmatching_transfer" / "evidence_1415177"
PKG72_EV = MODELS_DIR / "72_method_c_coupled_state_transfer" / "evidence_1415199"


def test_package60_indexing_bug_resolution():
    """Verify that Step 1 reaction force is 0.16506 N, NOT the mislabeled Step 2 endpoint (0.1496 N)."""
    res60 = evaluate_offset_simulation(str(PKG60_EV), "M1_EXP_NONMATCHING_SMOOTH_H_650")
    assert res60["analysis_completed"] is True

    # Step 1 reconstruction reaction force
    s1_rf = res60["step1_rf"]
    assert s1_rf is not None
    assert s1_rf["step"] == 1
    assert s1_rf["increment"] == 1
    assert abs(s1_rf["rf2_N"] - 0.16506233) < 1e-6
    assert abs(s1_rf["u2_mm"] - 0.0) < 1e-12

    # Step 2 endpoint reaction force (which was misassigned in the old JSON)
    s2_end = res60["step2_endpoint_rf"]
    assert s2_end is not None
    assert s2_end["step"] == 2
    assert s2_end["increment"] == 3
    assert abs(s2_end["rf2_N"] - 0.14961023) < 1e-6
    assert abs(s2_end["u2_mm"] - 0.00012) < 1e-6

    # Verify that Step 1 force differs distinctly from Step 2 endpoint
    assert abs(s1_rf["rf2_N"] - s2_end["rf2_N"]) > 0.015


def test_package72_reaction_forces_and_continuation():
    """Verify Package 72 force evolution through all 4 increments."""
    res72 = evaluate_offset_simulation(str(PKG72_EV), "M1_EXP_COUPLED_TRANSFER_650")
    assert res72["analysis_completed"] is True

    # Step 1 Inc 1
    s1 = res72["step1_rf"]
    assert abs(s1["rf2_N"] - 1.748264) < 1e-5

    # Step 2 increments
    s2_list = res72["step2_rf_list"]
    assert len(s2_list) == 3

    assert abs(s2_list[0]["rf2_N"] - 1.4579968) < 1e-5
    assert abs(s2_list[0]["u2_mm"] - 0.00004) < 1e-6

    assert abs(s2_list[1]["rf2_N"] - 1.4177172) < 1e-5
    assert abs(s2_list[1]["u2_mm"] - 0.00008) < 1e-6

    assert abs(s2_list[2]["rf2_N"] - 1.3977697) < 1e-5
    assert abs(s2_list[2]["u2_mm"] - 0.00012) < 1e-6


def test_package72_damage_healing_falsification():
    """Verify that Package 72 does NOT have zero healing, but rather 291 healing nodes."""
    res72 = evaluate_offset_simulation(str(PKG72_EV), "M1_EXP_COUPLED_TRANSFER_650")
    d_step1 = res72["damage_step1"]

    assert d_step1["healing_detected"] is True
    assert abs(d_step1["min_delta_d"] - (-0.001661279)) < 1e-6
    assert d_step1["healing_nodes_count"] == 291
    assert d_step1["total_nodes"] == 713


def test_package72_dissipation_monotonicity():
    """Verify that fracture energy dissipation is monotonic in Step 2."""
    res72 = evaluate_offset_simulation(str(PKG72_EV), "M1_EXP_COUPLED_TRANSFER_650")
    assert res72["dissipation_monotonic"] is True
    e_step1 = res72["step1_energy"]
    assert abs(e_step1["e_fracture_mJ"] - 0.34397864) < 1e-5

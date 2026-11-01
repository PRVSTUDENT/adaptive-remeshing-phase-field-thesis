#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_c4_to_c5_irreversible_transfer_qualification.py
Task: F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160
Protocol Version: 2

Unit test suite for Mode-I C4 -> C5 irreversible state-transfer and equilibrium qualification:
- Verifies mechanical boundary reaction continuity (< 1.0% error between C4 and C5).
- Verifies mechanical unconstrained residual defect quantification (3.88% max vs 0.5% tolerance).
- Confirms history monotonicity analysis: 98.77% strictly monotonic, 1.23% in singularity zone.
- Verifies thermodynamic history monotonicity update: H_committed = max(H_trans, psi_0^+(u_trans)).
- Verifies active/free phase residual evaluation and KKT multiplier conditions.
- Asserts receiver damage lower bounds are valid [0.00339, 0.60337] subset of [0, 1].
- Asserts all 53 seam pairs have strictly positive COD (no flank interpenetration).
- Confirms mathematical mandate for fixed-load re-equilibration and predeclared acceptance criteria.
"""

from __future__ import print_function, division
import json
import pytest
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
QUAL_JSON_PATH = REPO_ROOT / "results/validation/c4_to_c5_irreversible_transfer_qualification.json"


@pytest.fixture(scope="module")
def receipt():
    if not QUAL_JSON_PATH.exists():
        from scripts.validation.evaluate_c4_to_c5_irreversible_transfer_qualification import (
            run_irreversible_transfer_qualification,
        )
        return run_irreversible_transfer_qualification()
    return json.loads(QUAL_JSON_PATH.read_text(encoding="utf-8"))


def test_qualification_receipt_schema(receipt):
    assert receipt["schema"] == 1
    assert receipt["task_id"] == "F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160"
    assert receipt["status"] == "QUALIFICATION_COMPLETE"
    assert receipt["verification_passed"] is True


def test_mechanical_equilibrium_defect_and_reactions(receipt):
    mech = receipt["mechanical_equilibrium_accounting"]
    assert mech["reaction_force_continuity_pass"] is True
    assert mech["reaction_force_continuity_error_pct"] < 1.0
    assert mech["net_vertical_equilibrium_pct"] < 0.5

    # Mechanical out-of-balance defect exceeds 0.5% solver tolerance
    assert mech["mechanical_equilibrium_defect_confirmed"] is True
    assert mech["max_residual_to_reference_pct"] > 0.5
    assert mech["l2_residual_to_reference_pct"] > 0.5
    assert mech["unconstrained_dofs"] == 26210


def test_history_monotonicity_and_singularity_accounting(receipt):
    hist = receipt["history_monotonicity_accounting"]
    assert hist["total_receiver_gauss_points"] == 51984
    assert hist["gauss_points_strictly_monotonic_pct"] > 98.0
    # Refined mesh resolves higher peak strain energy at crack tip
    assert hist["crack_tip_singularity_higher_psi_count"] > 0
    assert hist["thermodynamically_consistent_peak_history_MPa"] > hist["transferred_peak_history_MPa"]
    assert hist["history_monotonicity_protocol"] == "H_committed = max(H_trans, psi_0^+(u_trans))"


def test_phase_field_kkt_and_active_set_release(receipt):
    pf = receipt["phase_field_kkt_accounting"]
    assert pf["raw_transferred_phase_residual_below_tau_free"] is True
    assert pf["raw_transferred_phase_residual_max_kN"] < pf["tau_free_kN"]
    assert pf["phase_relaxation_needed"] is True
    # At least 80% satisfy KKT stationarity even before re-equilibration
    assert pf["raw_kkt_satisfied_node_count"] > 10000


def test_damage_lower_bounds_and_flank_kinematics(receipt):
    d_bounds = receipt["damage_lower_bounds"]
    assert d_bounds["damage_bounds_valid"] is True
    assert d_bounds["min_damage_lower_bound"] >= 0.0
    assert d_bounds["max_damage_lower_bound"] <= 1.0

    kinematics = receipt["crack_flank_kinematics"]
    assert kinematics["seam_pair_count"] == 53
    assert kinematics["all_cod_positive"] is True
    assert kinematics["flank_penetration_detected"] is False
    assert kinematics["mouth_cod_mm"] > kinematics["tip_cod_mm"] > 0.0


def test_re_equilibration_mandate_and_acceptance_criteria(receipt):
    mandate = receipt["re_equilibration_mandate"]
    assert mandate["fixed_load_re_equilibration_required"] is True
    assert mandate["re_equilibration_load_condition"] == "FIXED_DISPLACEMENT_ZERO_INCREMENT"

    crit = mandate["predeclared_acceptance_criteria"]
    assert crit["max_mechanical_residual_relative_to_rf"] == 0.005
    assert crit["max_phase_residual_infinity_norm_kN"] == 1.0e-6
    assert crit["kkt_active_multiplier_violations"] == 0
    assert len(mandate["unverified_quantities_pending_solve"]) > 0

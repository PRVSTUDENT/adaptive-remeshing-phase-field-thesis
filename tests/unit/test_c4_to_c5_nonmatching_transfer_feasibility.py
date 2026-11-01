#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_c4_to_c5_nonmatching_transfer_feasibility.py
Task: F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160
Protocol Version: 2

Unit test suite for Mode-I C4 -> C5 nonmatching-mesh transfer feasibility:
- Verifies 100% node and Gauss-point inverse isoparametric mapping.
- Asserts strict slit flank isolation (0 cross-slit interpolations).
- Verifies boundary condition retention (bottom u_y = 0, top u_y prescribed).
- Asserts Crack Opening Displacement (COD) positivity and mouth preservation.
- Verifies phase field bounds [0, 1] and driving history non-negativity H >= 0.
- Asserts damage and history spatial integral conservation within 0.1%.
- Confirms transferred phase residual infinity norm is strictly below 1e-6 kN.
- Confirms overall transfer feasibility status is VERIFIED_FEASIBLE.
"""

from __future__ import print_function, division
import json
import pytest
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
INVESTIGATION_JSON = REPO_ROOT / "results/validation/c4_to_c5_nonmatching_transfer_feasibility_investigation.json"


@pytest.fixture(scope="module")
def receipt():
    if not INVESTIGATION_JSON.exists():
        from scripts.validation.evaluate_c4_to_c5_nonmatching_transfer_feasibility import (
            evaluate_nonmatching_transfer_feasibility,
        )
        return evaluate_nonmatching_transfer_feasibility()
    return json.loads(INVESTIGATION_JSON.read_text(encoding="utf-8"))


def test_investigation_receipt_schema(receipt):
    assert receipt["schema"] == 1
    assert receipt["task_id"] == "F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160"
    assert receipt["status"] == "INVESTIGATION_COMPLETE"
    assert receipt["verification_passed"] is True


def test_mesh_mapping_and_flank_isolation(receipt):
    mapping = receipt["spatial_mapping_metrics"]
    assert mapping["mapped_receiver_nodes"] == 13278
    assert mapping["total_receiver_nodes"] == 13278
    assert mapping["node_mapping_coverage_pct"] == 100.0
    assert mapping["flank_isolation_violations"] == 0
    assert mapping["max_node_reconstruction_error_mm"] < 1.0e-10

    assert mapping["mapped_receiver_gps"] == 51984
    assert mapping["total_receiver_gps"] == 51984
    assert mapping["gp_mapping_coverage_pct"] == 100.0
    assert mapping["max_gp_reconstruction_error_mm"] < 1.0e-10


def test_boundary_conditions_and_crack_opening(receipt):
    bc = receipt["boundary_condition_retention"]
    assert bc["bottom_boundary_pass"] is True
    assert bc["bottom_boundary_max_abs_uy_mm"] < 1.0e-12
    assert bc["top_boundary_pass"] is True
    assert bc["top_boundary_relative_error"] < 1.0e-10

    cod = receipt["crack_opening_displacement"]
    assert cod["slit_seam_cod_all_positive"] is True
    assert cod["crack_mouth_cod_diff_mm"] < 1.0e-10
    assert cod["cod_preservation_pass"] is True


def test_field_bounds_and_conservation(receipt):
    fields = receipt["field_bounds_and_conservation"]
    assert fields["damage_bounds_pass"] is True
    assert fields["receiver_damage_range"][0] >= 0.0
    assert fields["receiver_damage_range"][1] <= 1.0

    assert fields["history_non_negativity_pass"] is True
    assert fields["receiver_history_bilinear_range_MPa"][0] >= 0.0
    assert fields["receiver_history_nearest_range_MPa"][0] >= 0.0

    # Integral conservation within 0.1% (0.001)
    assert fields["damage_integral_rel_diff"] < 0.001
    assert fields["history_integral_bilinear_rel_diff"] < 0.001
    assert fields["displacement_L2_rel_diff"] < 0.001


def test_equilibrium_reconstruction_residuals(receipt):
    eq = receipt["equilibrium_reconstruction_diagnostics"]
    # Transferred phase residual must be below UEL tolerance 1e-6 kN
    assert eq["transferred_c5_phase_residual_below_uel_tol"] is True
    assert eq["transferred_c5_phase_residual_infinity_norm_kN"] < 1.0e-6
    assert eq["transferred_c5_phase_residual_rms_kN"] < 1.0e-7
    assert eq["projected_re_equilibration_outer_iterations"] <= 20
    assert eq["equilibrium_reconstruction_feasibility"] == "EXCELLENT"


def test_all_verification_checks_pass(receipt):
    checks = receipt["verification_checks"]
    for check_name, passed in checks.items():
        assert passed is True, f"Check {check_name} failed!"
    assert receipt["verification_passed"] is True

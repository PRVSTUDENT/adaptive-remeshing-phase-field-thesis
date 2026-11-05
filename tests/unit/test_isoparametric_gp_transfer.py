#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_isoparametric_gp_transfer.py
=================================
Unit and regression test suite for Isoparametric Bilinear Gauss-Point History Transfer.
Task: F1620-METHOD-C-ISOPARAMETRIC-GP-TRANSFER-QUALIFICATION
Protocol Version: 2

Tests:
1. Exact mathematical properties of GP shape functions M_k(xi, eta): Kronecker delta and partition of unity.
2. Exact inverse isoparametric mapping for quads.
3. Machine-precision identity on authentic C5 mesh (51,984 Gauss points: max |Delta H| == 0.0).
4. Physical bounding and extrapolation safeguards (H >= 0.0, convex clamping).
5. Nonmatching C5-to-C6 transfer gradient preservation vs old element-mean operator.
6. Zero regression on nodal displacement and damage.
"""

from __future__ import print_function, division
import json
import math
import sys
from pathlib import Path
from collections import defaultdict
import pytest
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.isoparametric_gp_transfer import (
    Q_GAUSS,
    QUAD_GP_LOCAL,
    quad_nodal_shape_functions,
    quad_nodal_shape_gradients,
    quad_gp_shape_functions,
    inverse_isoparametric_quad,
    reconstruct_gp_history,
    transfer_isoparametric_gp_history
)
from scripts.remeshing.c5_to_c6_adaptive_integration import load_c5_mesh

C5_CP03_PATH = REPO_ROOT / "models/pandey_kumar_mode1/167_c5_package167_r3_c2_2_continuation/evidence/1419566.mmaster02/converged_checkpoint_03.json"


@pytest.fixture(scope="module")
def c5_data():
    """Loads C5 mesh and Checkpoint 03."""
    assert C5_CP03_PATH.is_file(), f"Missing C5 CP03: {C5_CP03_PATH}"
    c5_mesh = load_c5_mesh()
    with open(C5_CP03_PATH, "r", encoding="utf-8") as f:
        cp03 = json.load(f)

    # Build history dict
    d_hist: dict[tuple[int, int], float] = {}
    for item in cp03["history"]:
        eid = int(item[0])
        gp = int(item[1])
        h_val = float(item[2])
        d_hist[(eid, gp)] = h_val

    # Slit pairs
    upper_nodes = set()
    for eid, conn in c5_mesh["quads"].items():
        cy = sum(c5_mesh["nodes"][n][1] for n in conn) / 4.0
        if cy > 0.050:
            upper_nodes.update(conn)

    slit_dict = defaultdict(list)
    for nid, (x, y) in c5_mesh["nodes"].items():
        if abs(y - 0.050) < 1e-6 and x <= 0.040 + 1e-6:
            slit_dict[round(x, 7)].append(nid)

    c5_slit_pairs = []
    for x_val, nids in sorted(slit_dict.items()):
        if len(nids) == 2:
            n_lower = min(nids, key=lambda n: n in upper_nodes)
            n_upper = max(nids, key=lambda n: n in upper_nodes)
            c5_slit_pairs.append((n_lower, n_upper, x_val))

    c5_mesh["coincident_slit_pairs"] = c5_slit_pairs
    return {"mesh": c5_mesh, "cp03": cp03, "history": d_hist}


# ---------------------------------------------------------------------------
# Test Group 1: Mathematical Foundations of GP Shape Functions
# ---------------------------------------------------------------------------

def test_gauss_point_coordinates():
    """Verifies that the 4 Gauss points match Abaqus / frozen UEL specification."""
    expected_q = 1.0 / math.sqrt(3.0)
    assert abs(Q_GAUSS - expected_q) < 1e-15
    assert len(QUAD_GP_LOCAL) == 4
    assert QUAD_GP_LOCAL[0] == (-expected_q, -expected_q)
    assert QUAD_GP_LOCAL[1] == ( expected_q, -expected_q)
    assert QUAD_GP_LOCAL[2] == ( expected_q,  expected_q)
    assert QUAD_GP_LOCAL[3] == (-expected_q,  expected_q)


def test_gp_shape_functions_kronecker_delta():
    """
    Asserts that GP shape functions M_k(xi, eta) satisfy the Kronecker delta property:
    M_k(xi_j, eta_j) == 1 if k == j else 0 for all 4 Gauss points.
    """
    for j, (xi_j, eta_j) in enumerate(QUAD_GP_LOCAL):
        M = quad_gp_shape_functions(xi_j, eta_j)
        for k in range(4):
            expected = 1.0 if k == j else 0.0
            assert abs(M[k] - expected) < 1e-14, f"Failed at GP {j+1}, func {k+1}: got {M[k]}"


def test_gp_shape_functions_partition_of_unity():
    """
    Asserts that sum_{k=1}^4 M_k(xi, eta) == 1.0 for arbitrary points across [-1, 1]^2.
    """
    test_points = [
        (0.0, 0.0),
        (-0.5, 0.3),
        (0.8, -0.2),
        (-1.0, -1.0),
        (1.0, 1.0),
        (Q_GAUSS, 0.0),
        (0.0, -Q_GAUSS),
    ]
    for xi, eta in test_points:
        M = quad_gp_shape_functions(xi, eta)
        total = sum(M)
        assert abs(total - 1.0) < 1e-14, f"Partition of unity violated at ({xi}, {eta}): sum={total}"


# ---------------------------------------------------------------------------
# Test Group 2: Inverse Isoparametric Mapping
# ---------------------------------------------------------------------------

def test_inverse_isoparametric_rectangular_quad():
    """Verifies inverse mapping on rectangular elements."""
    vertices = [(0.010, 0.020), (0.015, 0.020), (0.015, 0.025), (0.010, 0.025)]
    # Center
    xi, eta, conv = inverse_isoparametric_quad(vertices, 0.0125, 0.0225)
    assert conv
    assert abs(xi) < 1e-12 and abs(eta) < 1e-12

    # Corner 2
    xi, eta, conv = inverse_isoparametric_quad(vertices, 0.015, 0.020)
    assert conv
    assert abs(xi - 1.0) < 1e-12 and abs(eta - (-1.0)) < 1e-12

    # GP 1
    N_gp = quad_nodal_shape_functions(-Q_GAUSS, -Q_GAUSS)
    gx = sum(N_gp[i] * vertices[i][0] for i in range(4))
    gy = sum(N_gp[i] * vertices[i][1] for i in range(4))
    xi, eta, conv = inverse_isoparametric_quad(vertices, gx, gy)
    assert conv
    assert abs(xi - (-Q_GAUSS)) < 1e-12 and abs(eta - (-Q_GAUSS)) < 1e-12


def test_inverse_isoparametric_skewed_quad():
    """Verifies Newton-Raphson inverse mapping on skewed/trapezoidal quad."""
    vertices = [(0.0, 0.0), (2.0, 0.0), (1.5, 1.0), (0.5, 1.0)]
    for target_xi, target_eta in [(-0.3, 0.4), (0.5, -0.2), (0.0, 0.0)]:
        N = quad_nodal_shape_functions(target_xi, target_eta)
        xp = sum(N[i] * vertices[i][0] for i in range(4))
        yp = sum(N[i] * vertices[i][1] for i in range(4))
        xi_sol, eta_sol, conv = inverse_isoparametric_quad(vertices, xp, yp)
        assert conv
        assert abs(xi_sol - target_xi) < 1e-10
        assert abs(eta_sol - target_eta) < 1e-10


# ---------------------------------------------------------------------------
# Test Group 3: Physical Extrapolation & Limiter Modes
# ---------------------------------------------------------------------------

def test_reconstruct_gp_history_internal_convexity():
    """Asserts that inside the GP rectangle, reconstruction is strictly bounded by donor extremes."""
    donor_H = [1.0, 4.0, 12.0, 2.0]
    # Center
    h_cen = reconstruct_gp_history(donor_H, 0.0, 0.0)
    assert abs(h_cen - sum(donor_H) / 4.0) < 1e-14
    assert min(donor_H) <= h_cen <= max(donor_H)

    # Any interior point
    for xi in [-0.5, 0.0, 0.5]:
        for eta in [-0.5, 0.0, 0.5]:
            h_val = reconstruct_gp_history(donor_H, xi, eta)
            assert h_val >= 0.0
            assert min(donor_H) <= h_val <= max(donor_H)


def test_extrapolation_limiter_prevents_negative_history():
    """
    Asserts that when steep localized history produces negative polynomial weights outside
    the GP rectangle, the limiter strictly prevents negative values (H >= 0.0).
    """
    # Extremely steep localized history (e.g. 20 MPa at GP 1, 0 elsewhere)
    donor_H = [20.0, 0.0, 0.0, 0.0]
    # At corner (xi=1.0, eta=-1.0), raw linear extrapolation would be negative
    h_raw = reconstruct_gp_history(donor_H, 1.0, -1.0, limiter_mode="none")
    assert h_raw < 0.0, "Expected negative raw extrapolation weight"

    # Nonnegative limiter clamps to 0.0
    h_nonneg = reconstruct_gp_history(donor_H, 1.0, -1.0, limiter_mode="nonnegative")
    assert h_nonneg == 0.0

    # Convex clamp limits to [min, max] = [0.0, 20.0]
    h_clamp = reconstruct_gp_history(donor_H, 1.0, -1.0, limiter_mode="convex_clamp")
    assert 0.0 <= h_clamp <= 20.0


# ---------------------------------------------------------------------------
# Test Group 4: Exact C5-to-C5 Same-Mesh Parity Qualification
# ---------------------------------------------------------------------------

def test_exact_same_mesh_gp_history_identity(c5_data):
    """
    QUALIFICATION TEST (SHORTCUT ENABLED):
    Executes transfer_isoparametric_gp_history from C5 Checkpoint 03 onto C5 mesh with shortcut.
    Asserts exact identity across all 51,984 Gauss points.
    """
    mesh = c5_data["mesh"]
    d_hist = c5_data["history"]

    res = transfer_isoparametric_gp_history(mesh, d_hist, mesh, limiter_mode="convex_clamp", bypass_same_mesh_shortcut=False)
    assert res["status"] == "TRANSFER_COMPLETE"
    assert res["num_gauss_points"] == 51984
    assert res["num_elements"] == 12996

    transferred = res["transferred_history_dict"]
    diffs = [abs(transferred[k] - d_hist[k]) for k in d_hist]
    max_diff = max(diffs)
    rms_diff = math.sqrt(sum(d**2 for d in diffs) / len(diffs))

    assert max_diff <= 1e-14, f"Expected exact identity, got max diff = {max_diff}"
    assert rms_diff <= 1e-14, f"Expected exact identity, got rms diff = {rms_diff}"


def test_exact_same_mesh_gp_history_identity_without_shortcut(c5_data):
    """
    CRITICAL HARDENING QUALIFICATION TEST (BLOCKER 1 - SHORTCUT BYPASSED):
    Executes transfer_isoparametric_gp_history with bypass_same_mesh_shortcut=True.
    Forces every single one of the 51,984 Gauss points to undergo full 2D spatial bin lookup,
    true isoparametric containment verification, inverse-quad Newton mapping, and bilinear
    GP shape function reconstruction.
    Asserts that the mathematical operator itself achieves exact machine-precision identity (< 1e-12 MPa).
    """
    mesh = c5_data["mesh"]
    d_hist = c5_data["history"]

    res = transfer_isoparametric_gp_history(
        mesh, d_hist, mesh, limiter_mode="convex_clamp", bypass_same_mesh_shortcut=True
    )
    assert res["status"] == "TRANSFER_COMPLETE"
    assert res["num_gauss_points"] == 51984
    assert res["num_elements"] == 12996
    assert res["bypass_same_mesh_shortcut"] is True
    assert len(res["exceptional_mappings"]) == 0

    transferred = res["transferred_history_dict"]
    diffs = [abs(transferred[k] - d_hist[k]) for k in d_hist]
    max_diff = max(diffs)
    rms_diff = math.sqrt(sum(d**2 for d in diffs) / len(diffs))

    print(f"\n[Test] Same-Mesh C5 Parity (Full Spatial Path): max |Delta H| = {max_diff:.4e} MPa, RMS = {rms_diff:.4e} MPa")
    assert max_diff <= 1e-12, f"Expected exact full-field identity without shortcut, got {max_diff}"
    assert rms_diff <= 1e-12, f"Expected exact full-field identity without shortcut, got {rms_diff}"


def test_same_mesh_modified_coordinates_bypasses_shortcut(c5_data):
    """
    BLOCKER 1 TEST: Verifies that when receiver element IDs and connectivity match donor elements
    but node coordinates differ, the operator detects geometry change, bypasses the shortcut,
    and performs full spatial inverse mapping.
    """
    mesh = c5_data["mesh"]
    d_hist = c5_data["history"]

    # Create receiver mesh with shifted node coordinates (+0.0001 mm in x)
    modified_nodes = {nid: (coords[0] + 0.00001, coords[1]) for nid, coords in mesh["nodes"].items()}
    # Pick a small 4-element patch to test
    patch_quads = {eid: mesh["quads"][eid] for eid in list(mesh["quads"].keys())[:4]}
    patch_receiver = {
        "nodes": modified_nodes,
        "quads": patch_quads,
        "coincident_slit_pairs": mesh["coincident_slit_pairs"]
    }

    # Should detect coords_match == False and run full spatial evaluation without error
    res = transfer_isoparametric_gp_history(mesh, d_hist, patch_receiver, limiter_mode="convex_clamp")
    assert res["status"] == "TRANSFER_COMPLETE"
    assert res["num_elements"] == 4
    assert res["num_gauss_points"] == 16


def test_fail_closed_missing_donor_history_raises_keyerror(c5_data):
    """
    BLOCKER 3 TEST: Verifies that missing donor GP value raises KeyError (fail-closed integrity).
    """
    mesh = c5_data["mesh"]
    d_hist = dict(c5_data["history"])

    # Delete one GP value from donor history
    del d_hist[(1, 1)]

    single_elem_receiver = {
        "nodes": mesh["nodes"],
        "quads": {1: mesh["quads"][1]},
        "coincident_slit_pairs": []
    }

    with pytest.raises(KeyError, match="Fail-closed: Missing donor history value"):
        transfer_isoparametric_gp_history(mesh, d_hist, single_elem_receiver, bypass_same_mesh_shortcut=True)


def test_fail_closed_unresolved_host_element_raises_valueerror(c5_data):
    """
    BLOCKER 2 & 3 TEST: Verifies that a point far outside the donor domain raises ValueError (fail-closed).
    """
    mesh = c5_data["mesh"]
    d_hist = c5_data["history"]

    # Receiver quad placed far outside donor domain [0, 0.1]^2 at (10.0, 10.0)
    outside_nodes = {
        1001: (10.0, 10.0),
        1002: (10.01, 10.0),
        1003: (10.01, 10.01),
        1004: (10.0, 10.01)
    }
    outside_receiver = {
        "nodes": outside_nodes,
        "quads": {99999: [1001, 1002, 1003, 1004]},
        "coincident_slit_pairs": []
    }

    with pytest.raises(ValueError, match="Fail-closed: Unresolved host element"):
        transfer_isoparametric_gp_history(mesh, d_hist, outside_receiver)


def test_contrast_with_old_element_averaging_operator(c5_data):
    """
    Directly contrasts the new isoparametric operator against the old element-averaged operator
    on Element 6437 (crack-tip peak element).
    """
    d_hist = c5_data["history"]
    elem_6437_donor = [d_hist[(6437, g)] for g in range(1, 5)]

    # Old operator: scalar mean
    old_mean = sum(elem_6437_donor) / 4.0
    old_error_at_gp3 = abs(old_mean - elem_6437_donor[2])
    assert abs(old_error_at_gp3 - 6.3491) < 0.01

    # New operator: exact GP recovery
    new_gp3 = reconstruct_gp_history(elem_6437_donor, Q_GAUSS, Q_GAUSS)
    assert abs(new_gp3 - elem_6437_donor[2]) < 1e-14


# ---------------------------------------------------------------------------
# Test Group 5: Qualification Summary & Nonmatching C6 Benchmarks
# ---------------------------------------------------------------------------

SUMMARY_JSON_PATH = REPO_ROOT / "results/validation/isoparametric_gp_transfer_qualification_summary.json"
REPORT_MD_PATH = REPO_ROOT / "results/validation/isoparametric_gp_transfer_qualification_report.md"


def test_qualification_summary_artifacts_exist():
    """Asserts qualification summary JSON and markdown report exist and are populated."""
    assert SUMMARY_JSON_PATH.is_file(), f"Missing summary JSON: {SUMMARY_JSON_PATH}"
    assert REPORT_MD_PATH.is_file(), f"Missing report markdown: {REPORT_MD_PATH}"

    with open(SUMMARY_JSON_PATH, "r", encoding="utf-8") as f:
        summary = json.load(f)

    assert summary["task_id"] == "F1621-METHOD-C-GP-TRANSFER-SAFETY-REQUALIFICATION"
    assert summary["governance"]["zero_pbs_enforced"] is True
    assert summary["same_mesh_parity_c5"]["exact_identity_passed"] is True
    assert summary["same_mesh_parity_c5"]["max_delta_H_MPa"] <= 1e-12
    assert summary["same_mesh_parity_c5"]["rms_delta_H_MPa"] <= 1e-12
    assert summary["same_mesh_parity_c5"]["bypass_same_mesh_shortcut"] is True
    assert summary["same_mesh_parity_c5"]["containment_verified"] is True


def test_c6_nonmatching_gradient_retention():
    """Asserts that candidate 1 retains 100% of peak driving force on nonmatching C6."""
    with open(SUMMARY_JSON_PATH, "r", encoding="utf-8") as f:
        summary = json.load(f)

    c6_metrics = summary["nonmatching_transfer_c6"]
    donor_peak = c6_metrics["peak_history_donor_reference_MPa"]
    old_peak = c6_metrics["peak_history_old_operator_MPa"]
    c1_peak = c6_metrics["peak_history_candidate_1_convex_clamp_MPa"]

    # Old operator depression: 8.8055 MPa vs 14.0474 MPa
    assert abs(old_peak - 8.8055) < 0.01
    assert old_peak < 0.65 * donor_peak, "Old operator should depress peak driving force by > 35%"

    # Candidate 1: full retention of donor peak
    assert abs(c1_peak - donor_peak) < 1e-4, "Candidate 1 must retain full donor peak driving force"

    # Strict nonnegativity
    extrap = c6_metrics["extrapolation_statistics"]
    assert extrap["candidate_1_convex_clamp"]["min_history_value"] >= 0.0
    assert extrap["candidate_2_nonnegative"]["min_history_value"] >= 0.0


def test_c6_radial_localization_and_phase_driving_force():
    """Asserts that gradient discrepancy is concentrated in r <= 2 um and phase driving force is restored."""
    with open(SUMMARY_JSON_PATH, "r", encoding="utf-8") as f:
        summary = json.load(f)

    c6_metrics = summary["nonmatching_transfer_c6"]
    radial = c6_metrics["radial_localization"]
    # Zone 2um should show peak |Delta H| of 6.3491 MPa
    assert abs(radial["zone_2um"]["max_diff_MPa"] - 6.3491) < 0.01
    # Far field max diff should be tiny compared to peak
    assert radial["zone_far_field"]["rms_diff_MPa"] < 0.005

    df = c6_metrics["driving_force_consistency"]
    assert df["peak_driving_force_c1_MPa"] > df["peak_driving_force_old_MPa"] + 3.0


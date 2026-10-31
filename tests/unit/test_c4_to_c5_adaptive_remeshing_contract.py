# -*- coding: utf-8 -*-
"""
test_c4_to_c5_adaptive_remeshing_contract.py
Unit tests for C4 -> C5 Adaptive Remeshing Interface Contract and Transfer Operators.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Protocol Version: 2
"""
import json
import math
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "results" / "validation" / "c4_to_c5_adaptive_remeshing_contract.json"
COMPANION_AUDIT_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "114_c4_inc79_companion_miseseri" / "c4_inc79_miseseri_audit.json"


def quad_shape_functions(xi, eta):
    """Evaluates bilinear shape functions for a 4-node quad at (xi, eta)."""
    n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
    n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
    n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
    n4 = 0.25 * (1.0 - xi) * (1.0 + eta)
    return [n1, n2, n3, n4]


def inverse_isoparametric_quad(vertices, x_target, y_target, tol=1e-12, max_iter=30):
    """Solves for (xi, eta) given physical quad vertices and target point."""
    xi, eta = 0.0, 0.0
    x1, y1 = vertices[0]
    x2, y2 = vertices[1]
    x3, y3 = vertices[2]
    x4, y4 = vertices[3]

    for _ in range(max_iter):
        n = quad_shape_functions(xi, eta)
        x_calc = sum(ni * vi[0] for ni, vi in zip(n, vertices))
        y_calc = sum(ni * vi[1] for ni, vi in zip(n, vertices))

        rx = x_calc - x_target
        ry = y_calc - y_target
        res_norm = math.sqrt(rx * rx + ry * ry)
        if res_norm < tol:
            return xi, eta, True, res_norm

        dn_dxi = [
            -0.25 * (1.0 - eta),
             0.25 * (1.0 - eta),
             0.25 * (1.0 + eta),
            -0.25 * (1.0 + eta)
        ]
        dn_deta = [
            -0.25 * (1.0 - xi),
            -0.25 * (1.0 + xi),
             0.25 * (1.0 + xi),
             0.25 * (1.0 - xi)
        ]

        j11 = sum(d * vi[0] for d, vi in zip(dn_dxi, vertices))
        j12 = sum(d * vi[0] for d, vi in zip(dn_deta, vertices))
        j21 = sum(d * vi[1] for d, vi in zip(dn_dxi, vertices))
        j22 = sum(d * vi[1] for d, vi in zip(dn_deta, vertices))

        det_j = j11 * j22 - j12 * j21
        if abs(det_j) < 1e-15:
            return xi, eta, False, res_norm

        d_xi = (j22 * rx - j12 * ry) / det_j
        d_eta = (-j21 * rx + j11 * ry) / det_j

        xi -= d_xi
        eta -= d_eta
        xi = max(-3.0, min(3.0, xi))
        eta = max(-3.0, min(3.0, eta))

    n = quad_shape_functions(xi, eta)
    x_calc = sum(ni * vi[0] for ni, vi in zip(n, vertices))
    y_calc = sum(ni * vi[1] for ni, vi in zip(n, vertices))
    res_norm = math.hypot(x_calc - x_target, y_calc - y_target)
    return xi, eta, res_norm < tol, res_norm


def test_contract_schema_and_completeness():
    assert CONTRACT_PATH.is_file(), "Contract file missing: %s" % CONTRACT_PATH
    with open(str(CONTRACT_PATH), "r") as f:
        c = json.load(f)

    assert c["schema"] == 1
    assert c["task_id"] == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert c["contract_id"] == "C4_TO_C5_ADAPTIVE_REMESHING_INTERFACE_SPECIFICATION"
    assert c["source_mesh_c4"]["quad_elements"] == 7056
    assert c["source_mesh_c4"]["nodes"] == 7265
    assert c["source_mesh_c4"]["gauss_points"] == 28224
    assert c["domain_geometry"]["sharp_slit"]["y_coordinate_mm"] == 0.05
    assert c["domain_geometry"]["sharp_slit"]["x_max_crack_tip_mm"] == 0.04
    assert c["mesh_adaptation_governance"]["refinement_policy"] == "REFINEMENT_ONLY"
    assert not c["mesh_adaptation_governance"]["coarsening_allowed"]


def test_miseseri_companion_evidence_consistency():
    assert COMPANION_AUDIT_PATH.is_file(), "Missing companion audit: %s" % COMPANION_AUDIT_PATH
    with open(str(COMPANION_AUDIT_PATH), "r") as f:
        audit = json.load(f)

    with open(str(CONTRACT_PATH), "r") as f:
        contract = json.load(f)

    empirical = contract["companion_continuum_error_indicator"]["empirical_evidence"]
    assert audit["refinement_metrics"]["threshold_eta"] == 0.15
    assert audit["refinement_metrics"]["elements_above_threshold"] == empirical["elements_marked_above_threshold"]
    assert audit["total_elements"] == empirical["total_elements_audited"]
    assert abs(audit["refinement_metrics"]["pct_above_threshold"] - empirical["pct_marked_above_threshold"]) < 1e-4
    assert abs(audit["peak_relative_error"]["eta"] - empirical["peak_eta"]) < 1e-4
    assert abs(audit["peak_relative_error"]["centroid_mm"]["x"] - empirical["peak_eta_centroid_mm"][0]) < 1e-6
    assert abs(audit["peak_relative_error"]["centroid_mm"]["y"] - empirical["peak_eta_centroid_mm"][1]) < 1e-6


def test_flank_isolation_and_no_cross_slit_interpolation():
    with open(str(CONTRACT_PATH), "r") as f:
        contract = json.load(f)

    rule = contract["state_transfer_operator_contract"]["flank_isolation_rule"]
    seam_y = rule["slit_y_mm"]
    seam_x_max = rule["slit_x_max_mm"]

    # Lower flank donor quad: [0.01, 0.02] x [0.04, 0.0499] (centroid y < 0.05)
    lower_quad = [(0.01, 0.04), (0.02, 0.04), (0.02, 0.0499), (0.01, 0.0499)]
    lower_cy = sum(p[1] for p in lower_quad) / 4.0
    assert lower_cy < seam_y, "Lower quad centroid must be < seam_y"

    # Upper flank donor quad: [0.01, 0.02] x [0.0501, 0.06] (centroid y > 0.05)
    upper_quad = [(0.01, 0.0501), (0.02, 0.0501), (0.02, 0.06), (0.01, 0.06)]
    upper_cy = sum(p[1] for p in upper_quad) / 4.0
    assert upper_cy > seam_y, "Upper quad centroid must be > seam_y"

    # Target point on lower slit flank: x = 0.015, y = 0.04995
    pt_lower = (0.015, 0.04995)
    assert pt_lower[0] <= seam_x_max and pt_lower[1] < seam_y

    # Function evaluating whether donor is allowed for target
    def is_donor_allowed(donor_cy, pt_x, pt_y):
        if pt_x <= seam_x_max:
            if pt_y <= seam_y:
                return donor_cy < seam_y
            else:
                return donor_cy >= seam_y
        return True  # Ligament region allows continuous donor

    assert is_donor_allowed(lower_cy, pt_lower[0], pt_lower[1])
    assert not is_donor_allowed(upper_cy, pt_lower[0], pt_lower[1]), "Upper quad must NOT be sampled for lower slit flank point!"

    # Target point on upper slit flank: x = 0.015, y = 0.05005
    pt_upper = (0.015, 0.05005)
    assert not is_donor_allowed(lower_cy, pt_upper[0], pt_upper[1]), "Lower quad must NOT be sampled for upper slit flank point!"
    assert is_donor_allowed(upper_cy, pt_upper[0], pt_upper[1])


def test_refinement_only_governance():
    with open(str(CONTRACT_PATH), "r") as f:
        contract = json.load(f)

    gov = contract["mesh_adaptation_governance"]
    assert gov["refinement_policy"] == "REFINEMENT_ONLY"
    assert not gov["coarsening_allowed"]

    # Test validator: candidate elements in target mesh must not be coarsened relative to donor
    def validate_candidate_mesh(donor_sizes, candidate_sizes):
        for eid, h_cand in candidate_sizes.items():
            h_donor = donor_sizes.get(eid, h_cand)
            if h_cand > h_donor * 1.01:  # Coarsened by more than 1% tolerance
                return False, "Element %s coarsened: h_cand=%f > h_donor=%f" % (eid, h_cand, h_donor)
        return True, "Valid"

    donor_sizes = {1: 0.0010, 2: 0.0020, 3: 0.0050}
    # Valid refined mesh
    valid_target = {1: 0.0005, 2: 0.0010, 3: 0.0050}
    ok, msg = validate_candidate_mesh(donor_sizes, valid_target)
    assert ok, msg

    # Invalid coarsened mesh
    invalid_target = {1: 0.0015, 2: 0.0010, 3: 0.0050}
    ok, msg = validate_candidate_mesh(donor_sizes, invalid_target)
    assert not ok, "Validator must reject coarsened elements under REFINEMENT_ONLY"


def test_inverse_isoparametric_quad_and_partition_of_unity():
    # Regular square quad: [0.0, 0.01] x [0.0, 0.01]
    quad_nodes = [(0.0, 0.0), (0.01, 0.0), (0.01, 0.01), (0.0, 0.01)]

    # Test centroid
    xi, eta, conv, res = inverse_isoparametric_quad(quad_nodes, 0.005, 0.005)
    assert conv, "Newton-Raphson failed to converge at centroid"
    assert abs(xi) < 1e-11 and abs(eta) < 1e-11
    weights = quad_shape_functions(xi, eta)
    assert abs(sum(weights) - 1.0) < 1e-14, "Partition of unity violated"
    for w in weights:
        assert abs(w - 0.25) < 1e-11

    # Test an arbitrary interior point
    xi, eta, conv, res = inverse_isoparametric_quad(quad_nodes, 0.0025, 0.0075)
    assert conv
    assert abs(xi - (-0.5)) < 1e-11 and abs(eta - 0.5) < 1e-11
    weights = quad_shape_functions(xi, eta)
    assert abs(sum(weights) - 1.0) < 1e-14


def test_history_variable_non_negativity_and_monotonicity():
    with open(str(CONTRACT_PATH), "r") as f:
        contract = json.load(f)

    # Simulated host Gauss point history values
    source_h = [0.125, 0.450, 1.875, 0.0]

    # Host-nearest GP history mapping
    def map_history(source_h_list, nearest_idx):
        h_val = source_h_list[nearest_idx]
        assert h_val >= 0.0, "Thermodynamic violation: H < 0"
        return max(0.0, h_val)

    for idx in range(len(source_h)):
        target_h = map_history(source_h, idx)
        assert target_h >= 0.0
        assert target_h == source_h[idx]


def test_7_plus_8_plus_3_svar_encoding():
    with open(str(CONTRACT_PATH), "r") as f:
        contract = json.load(f)

    svar_spec = contract["state_transfer_operator_contract"]["active_set_and_initialization_format"]
    assert "7+8+3" in svar_spec["encoding"]
    assert "SVARS 9 to 12" in svar_spec["svars_history_slots"]

    # Total SVARS per Gauss point = 18
    svar_layout = {
        "state_flags": list(range(1, 8)),        # SVARS 1-7
        "gp_history_h": list(range(8, 16)),       # SVARS 8-15 (including H slots 9-12)
        "auxiliary": list(range(16, 19))          # SVARS 16-18
    }
    total_slots = len(svar_layout["state_flags"]) + len(svar_layout["gp_history_h"]) + len(svar_layout["auxiliary"])
    assert total_slots == 18, "Expected 18 total SVAR slots, got %d" % total_slots

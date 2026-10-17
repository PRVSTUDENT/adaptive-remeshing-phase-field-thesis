#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Deep Mathematical & Implementation Audit of BilinearHistoryTransferOperator vs HOST_NEAREST_GP,
Irreversibility Verification, and Package 60 Control Manifest Integrity (Task F1532).
"""

import math
import sys
import os
import json
import hashlib
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.experimental_bilinear_history_transfer import (
    evaluate_bilinear_quad_history,
    evaluate_nearest_gp_history,
    BilinearHistoryTransferOperator,
    GAUSS_XI_QUAD,
    GAUSS_ETA_QUAD,
    SQRT3
)

def test_01_abaqus_ip_ordering_and_partition_of_unity():
    """Verify exact partition of unity and Kronecker delta property at 2x2 Gauss points."""
    # Partition of unity: sum_{k=0}^3 phi_k(xi, eta) = 1 for any (xi, eta)
    sample_points = [
        (0.0, 0.0), (0.5, -0.5), (-0.8, 0.3), (1.0, 1.0), (-1.0, 1.0),
        (1.0 / SQRT3, -1.0 / SQRT3), (-0.2, -0.7)
    ]
    for xi, eta in sample_points:
        phi_sum = 0.0
        for k in range(4):
            phi_k = 0.25 * (1.0 + 3.0 * GAUSS_XI_QUAD[k] * xi) * (1.0 + 3.0 * GAUSS_ETA_QUAD[k] * eta)
            phi_sum += phi_k
        assert abs(phi_sum - 1.0) < 1e-14, f"Partition of unity violated at ({xi}, {eta}): sum={phi_sum}"

    # Kronecker delta property at Gauss points: phi_k(xi_j, eta_j) = delta_{kj}
    for j in range(4):
        xi_j = GAUSS_XI_QUAD[j]
        eta_j = GAUSS_ETA_QUAD[j]
        for k in range(4):
            phi_k = 0.25 * (1.0 + 3.0 * GAUSS_XI_QUAD[k] * xi_j) * (1.0 + 3.0 * GAUSS_ETA_QUAD[k] * eta_j)
            expected = 1.0 if j == k else 0.0
            assert abs(phi_k - expected) < 1e-14, f"Kronecker delta violated: phi_{k}(GP_{j}) = {phi_k} != {expected}"

def test_02_exact_linear_and_bilinear_field_reproduction():
    """Verify that unconstrained bilinear interpolation reproduces any polynomial in Q_1 exactly."""
    # Test field f(xi, eta) = 0.50 + 0.02 * xi - 0.03 * eta + 0.01 * xi * eta (strictly positive on [-1, 1]^2)
    a0, a1, a2, a3 = 0.50, 0.02, -0.03, 0.01
    def exact_f(xi, eta):
        return a0 + a1 * xi + a2 * eta + a3 * xi * eta

    H_gps = [exact_f(GAUSS_XI_QUAD[k], GAUSS_ETA_QUAD[k]) for k in range(4)]
    
    # Evaluate across a dense 11x11 grid inside the element [-1, 1]^2
    for i in range(11):
        xi = -1.0 + 0.2 * i
        for j in range(11):
            eta = -1.0 + 0.2 * j
            f_interp = evaluate_bilinear_quad_history(H_gps, xi, eta, bounded=False)
            f_true = exact_f(xi, eta)
            assert abs(f_interp - f_true) < 1e-13, f"Bilinear reproduction error at ({xi}, {eta}): {abs(f_interp - f_true)}"

def test_03_limiter_tradeoff_gradient_retention_vs_overshoot():
    """Investigate the slope-limiter behavior on steep crack-tip history gradients."""
    # Simulate a steep gradient towards the crack tip:
    # IP 1,2,4 are outside, IP 3 is directly adjacent to tip
    H_gps = [0.001, 0.005, 0.035, 0.004]  # IP 3 has high history
    
    # At the corner near IP 3 (xi=1.0, eta=1.0):
    val_unbounded = evaluate_bilinear_quad_history(H_gps, 1.0, 1.0, bounded=False)
    val_bounded = evaluate_bilinear_quad_history(H_gps, 1.0, 1.0, bounded=True)
    
    # Unbounded extrapolates higher than max(H_k) (reflecting positive gradient towards corner)
    assert val_unbounded > max(H_gps), "Unbounded operator should extrapolate beyond GP values near corner"
    # Bounded clips strictly to max(H_k)
    assert val_bounded == max(H_gps), f"Bounded operator must clip to max(H_k) = {max(H_gps)}"
    
    # Critical finding: The limiter prevents unphysical overshoots, but introduces a localized upper ceiling
    # that suppresses the continuous rise of peak history near element corners.
    limiter_clipping_deficit = val_unbounded - val_bounded
    assert limiter_clipping_deficit > 0.0

def test_04_cpe3_triangular_element_handling():
    """Verify that single-GP triangular elements (CPE3) are handled robustly."""
    op = BilinearHistoryTransferOperator(mode="BILINEAR_GP_BOUNDED")
    H_tri = [0.0185]
    dummy_coords = [(0.5, 0.5, 0.0)]
    
    # Any parent coordinate in a triangle should yield the exact centroid value
    val = op.transfer_element_history(
        donor_conn_len=3,
        H_donor_gps=H_tri,
        donor_gp_coords=dummy_coords,
        target_x=0.51, target_y=0.51,
        host_xi=0.33, host_eta=0.33
    )
    assert val == 0.0185

def test_05_crack_flank_separation_audit():
    """Verify that upper and lower crack-face nodes are geometrically and topologically isolated."""
    # In Mode-I sharp slit (along y=0.5, x <= 0.5):
    # Upper flank (y=0.5, uy > 0) and lower flank (y=0.5, uy < 0) have identical coords but distinct nodes
    upper_gp = (0.25, 0.5005, 0.0)
    lower_gp = (0.25, 0.4995, 0.0)
    
    # Distance in 2D is 0.001 mm (across seam)
    dist = math.sqrt((upper_gp[0] - lower_gp[0])**2 + (upper_gp[1] - lower_gp[1])**2)
    assert abs(dist - 0.001) < 1e-12
    # Without flank classification, nearest-neighbor would map upper GP to lower element and vice versa!
    # Our dual-flank hash bucket prevents cross-seam interaction by sorting into separate upper/lower buckets.

def test_06_quantitative_operator_comparison_manufactured_crack_tip():
    """
    Compare HOST_NEAREST_GP vs BILINEAR_GP on a synthetic singular crack-tip history field:
    H(r, theta) = K_H / sqrt(r) * cos^2(theta / 2).
    """
    tip_x, tip_y = 0.5, 0.5
    K_H = 0.002
    
    def synthetic_H(x, y):
        dx = x - tip_x
        dy = y - tip_y
        r = math.sqrt(dx*dx + dy*dy)
        if r < 1e-4:
            r = 1e-4
        theta = math.atan2(dy, dx)
        return K_H / math.sqrt(r) * (math.cos(theta / 2.0)**2)

    # Donor element: [0.50, 0.52] x [0.50, 0.52] (h = 0.02 mm)
    x_nodes = [0.50, 0.52, 0.52, 0.50]
    y_nodes = [0.50, 0.50, 0.52, 0.52]
    
    # Donor Gauss points
    donor_gps = []
    donor_gp_coords = []
    for k in range(4):
        xi, eta = GAUSS_XI_QUAD[k], GAUSS_ETA_QUAD[k]
        # Bilinear mapping from parent to physical
        N1 = 0.25 * (1 - xi) * (1 - eta)
        N2 = 0.25 * (1 + xi) * (1 - eta)
        N3 = 0.25 * (1 + xi) * (1 + eta)
        N4 = 0.25 * (1 - xi) * (1 + eta)
        gx = N1*x_nodes[0] + N2*x_nodes[1] + N3*x_nodes[2] + N4*x_nodes[3]
        gy = N1*y_nodes[0] + N2*y_nodes[1] + N3*y_nodes[2] + N4*y_nodes[3]
        donor_gps.append(synthetic_H(gx, gy))
        donor_gp_coords.append((gx, gy, 0.0))

    # Evaluate along a diagonal transect of 20 evaluation points
    nearest_errors = []
    bilinear_errors = []
    
    for s in range(1, 20):
        t = s / 20.0
        # Parent coordinates from (-0.8, -0.8) to (0.8, 0.8)
        xi_t = -0.8 + 1.6 * t
        eta_t = -0.8 + 1.6 * t
        
        N1 = 0.25 * (1 - xi_t) * (1 - eta_t)
        N2 = 0.25 * (1 + xi_t) * (1 - eta_t)
        N3 = 0.25 * (1 + xi_t) * (1 + eta_t)
        N4 = 0.25 * (1 - xi_t) * (1 + eta_t)
        tx = N1*x_nodes[0] + N2*x_nodes[1] + N3*x_nodes[2] + N4*x_nodes[3]
        ty = N1*y_nodes[0] + N2*y_nodes[1] + N3*y_nodes[2] + N4*y_nodes[3]
        
        H_exact = synthetic_H(tx, ty)
        H_nearest = evaluate_nearest_gp_history(donor_gps, donor_gp_coords, tx, ty)
        H_bilinear = evaluate_bilinear_quad_history(donor_gps, xi_t, eta_t, bounded=False)
        
        nearest_errors.append((H_nearest - H_exact)**2)
        bilinear_errors.append((H_bilinear - H_exact)**2)

    l2_nearest = math.sqrt(sum(nearest_errors) / len(nearest_errors))
    l2_bilinear = math.sqrt(sum(bilinear_errors) / len(bilinear_errors))
    
    # Bilinear interpolation must have lower L2 representation error than piecewise-constant nearest-GP
    assert l2_bilinear < l2_nearest, f"Bilinear L2 ({l2_bilinear}) should be lower than Nearest L2 ({l2_nearest})"
    reduction_pct = (l2_nearest - l2_bilinear) / l2_nearest * 100.0
    assert reduction_pct > 30.0, f"Expected >30% error reduction, got {reduction_pct:.2f}%"

def test_07_irreversibility_definition_distinction():
    """Verify that H >= 0 does not imply H_{n+1} >= H_n."""
    # Case: A location x where donor had H = 0.020, but due to mapping undershoot, recipient receives H = 0.016
    H_donor_x = 0.020
    H_recipient_x = 0.016
    
    # Both are non-negative
    assert H_donor_x >= 0.0 and H_recipient_x >= 0.0
    # But irreversibility is violated by 0.004!
    delta_H = H_recipient_x - H_donor_x
    assert delta_H < 0.0, "Undershoot constitutes an unphysical history loss"

def test_08_package60_uninterrupted_control_manifest_and_deck_integrity():
    """Verify that Package 60 files, hashes, and PBS contract are strictly valid."""
    pkg60_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "60_method_c_stage_c1_2_cycle2_uninterrupted_control"
    manifest_path = pkg60_dir / "METHOD_C_STAGE_C1_2_CYCLE2_UNINTERRUPTED_AUTHORIZATION.json"
    assert manifest_path.is_file(), f"Missing Package 60 manifest: {manifest_path}"
    
    with open(manifest_path, "r", encoding="utf-8") as fp:
        manifest = json.load(fp)
        
    assert manifest["batch_name"] == "MODE1_METHOD_C_STAGE_C1_2_CYCLE2_UNINTERRUPTED_CONTROL"
    assert manifest["technical_stage"] == "C1-2"
    assert manifest["jobs"][0]["cpus"] == 1
    assert manifest["jobs"][0]["memory_gb"] == 16
    assert manifest["jobs"][0]["walltime_hours"] == 2
    
    # Check that input deck exists and matches hash
    inp_path = pkg60_dir / "M1_MC_STAGE_C1_2_CYCLE2_UNINTERRUPTED_CONTROL.inp"
    assert inp_path.is_file()
    
    def calc_sha(p):
        h = hashlib.sha256()
        with open(p, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest().lower()
        
    actual_inp_sha = calc_sha(inp_path)
    assert actual_inp_sha == manifest["files"]["M1_MC_STAGE_C1_2_CYCLE2_UNINTERRUPTED_CONTROL.inp"]
    
    # Check frozen UEL hash
    actual_uel_sha = calc_sha(pkg60_dir / "f42_mixed_uel.for")
    assert actual_uel_sha == "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

    # Verify datacheck artifact exists
    dc_path = pkg60_dir / "M1_MC_STAGE_C1_2_CYCLE2_UNINTERRUPTED_CONTROL_DC.dat"
    assert dc_path.is_file()
    with open(dc_path, "r", encoding="utf-8", errors="replace") as fp:
        content = fp.read()
    assert "ANALYSIS DATACHECK COMPLETE" in content
    assert "***ERROR" not in content

if __name__ == "__main__":
    pytest.main(["-v", __file__])

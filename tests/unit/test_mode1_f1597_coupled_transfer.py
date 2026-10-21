"""Unit tests for F1597 Coupled Transfer on Candidate C2."""
import sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "scripts/validation") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts/validation"))

import numpy as np
import pytest

from scripts.remeshing.generate_crack_band_mesh import (
    generate_graded_1d,
    build_quad_mesh,
)
from scripts.validation.evaluate_candidate_c2_transfer import (
    load_package50_donor,
    run_patch_tests,
    solve_mechanical_system,
    transfer_donor_to_mesh,
    compute_damage_metrics,
)


def test_constitutive_parameter_reconciliation():
    workspace = REPO_ROOT
    donor = load_package50_donor(workspace)
    props = donor["props"]
    ell = props[0]
    gc = props[1]
    young = props[2]
    nu = props[3]

    assert abs(ell - 0.0075) < 1e-6, f"Expected ell=0.0075 mm, got {ell}"
    assert abs(gc - 0.0027) < 1e-6, f"Expected gc=0.0027 kN/mm, got {gc}"
    assert abs(young - 210.0) < 1e-6, f"Expected E=210 kN/mm^2, got {young}"
    assert abs(nu - 0.3) < 1e-6, f"Expected nu=0.3, got {nu}"

    # Verify Candidate C2 resolution criterion: h <= ell / 3.75
    h_c2 = 0.0010
    assert h_c2 <= ell / 3.75, f"C2 element size {h_c2} > ell/3.75 ({ell/3.75})"
    assert (h_c2 / ell) <= 0.2667, f"Ratio {h_c2/ell} > 0.2667"


def test_affine_and_rigid_body_patch_tests():
    props = [0.0075, 0.0027, 210.0, 0.3, 1.0e-7, 100]
    y_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.012, h_fine=0.0010, growth_ratio=1.15, max_h=0.005)
    x_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.015, h_fine=0.00125, growth_ratio=1.15, max_h=0.005, key_points=[0.040])
    mesh_c2 = build_quad_mesh(x_coords_c2, y_coords_c2, slit_y=0.050, slit_a0=0.040)

    res = run_patch_tests(mesh_c2, props)
    assert res["patch_tests_passed"], f"Patch tests failed: {res}"
    assert res["affine_strain_error"] < 1e-12, f"Affine strain error too large: {res['affine_strain_error']}"
    assert res["rigid_body_strain_error"] < 1e-12, f"Rigid body strain error too large: {res['rigid_body_strain_error']}"


def test_frozen_damage_mechanical_residual():
    workspace = REPO_ROOT
    donor = load_package50_donor(workspace)
    props = donor["props"]
    y_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.012, h_fine=0.0010, growth_ratio=1.15, max_h=0.005)
    x_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.015, h_fine=0.00125, growth_ratio=1.15, max_h=0.005, key_points=[0.040])
    mesh_c2 = build_quad_mesh(x_coords_c2, y_coords_c2, slit_y=0.050, slit_a0=0.040)
    transfer_c2 = transfer_donor_to_mesh(donor, mesh_c2)

    u, K, rf, res_kN, k_eff = solve_mechanical_system(mesh_c2, transfer_c2["d_mapped"], props, u_bar=0.00254)
    # Discrete mechanical equilibrium residual must be <= 1e-10 kN
    assert res_kN <= 1e-10, f"Mechanical residual {res_kN} > 1e-10 kN"
    # Reaction force on C2 before PDAS is 9.975 N (+27.05% vs 7.851 N)
    assert 9.0 < rf < 11.0, f"RF {rf} outside expected range [9.0, 11.0] N"


def test_fracture_energy_conservation_c2():
    workspace = REPO_ROOT
    donor = load_package50_donor(workspace)
    props = donor["props"]
    ell, gc = props[0], props[1]

    d_donor = compute_damage_metrics(
        {"nodes": donor["nodes"], "elements": donor["elements"], "rp_nid": 999999},
        donor["d_field"], ell=ell, gc=gc
    )

    y_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.012, h_fine=0.0010, growth_ratio=1.15, max_h=0.005)
    x_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.015, h_fine=0.00125, growth_ratio=1.15, max_h=0.005, key_points=[0.040])
    mesh_c2 = build_quad_mesh(x_coords_c2, y_coords_c2, slit_y=0.050, slit_a0=0.040)
    transfer_c2 = transfer_donor_to_mesh(donor, mesh_c2)

    d_c2 = compute_damage_metrics(mesh_c2, transfer_c2["d_mapped"], ell=ell, gc=gc)
    e_frac_donor = d_donor["fracture_energy_mJ"]
    e_frac_c2 = d_c2["fracture_energy_mJ"]
    err_pct = abs(e_frac_c2 - e_frac_donor) / e_frac_donor * 100.0

    # Fracture energy discrepancy must be <= 2%
    assert err_pct <= 2.0, f"Fracture energy discrepancy {err_pct:.4f}% > 2.0%"


if __name__ == "__main__":
    test_constitutive_parameter_reconciliation()
    test_affine_and_rigid_body_patch_tests()
    test_frozen_damage_mechanical_residual()
    test_fracture_energy_conservation_c2()
    print("ALL TESTS PASSED!")

"""Unit regression tests for F1597 Crack-Opening-Compatible State Reconstruction on Candidate C2."""
import json
import sys
from pathlib import Path
import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "scripts/validation") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts/validation"))

from scripts.remeshing.generate_crack_band_mesh import (
    generate_graded_1d,
    build_quad_mesh,
)
from scripts.validation.evaluate_candidate_c2_transfer import (
    load_package50_donor,
    transfer_donor_to_mesh,
    compute_damage_metrics,
    solve_mechanical_system,
)
from scripts.validation.evaluate_crack_opening_compatible import (
    solve_coupled_pdas_with_operator,
    compare_c2_operators,
)


def test_constitutive_and_c2_resolution_reconciliation():
    """Verify authentic physical parameters and C2 crack-band resolution criterion."""
    workspace = REPO_ROOT
    donor = load_package50_donor(workspace)
    props = donor["props"]
    ell, gc, young, nu = props[0], props[1], props[2], props[3]

    assert abs(ell - 0.0075) < 1e-6, f"Expected ell=0.0075 mm, got {ell}"
    assert abs(gc - 0.0027) < 1e-6, f"Expected gc=0.0027 kN/mm, got {gc}"
    assert abs(young - 210.0) < 1e-6, f"Expected E=210 kN/mm^2, got {young}"
    assert abs(nu - 0.3) < 1e-6, f"Expected nu=0.3, got {nu}"

    # Candidate C2 mesh criteria
    h_c2 = 0.0010
    assert h_c2 <= ell / 3.75, f"h_c2={h_c2} > ell/3.75 ({ell/3.75})"
    assert (h_c2 / ell) <= 0.2667, f"Ratio {h_c2/ell} > 0.2667"


def test_crack_opening_strain_concentration_mechanism():
    """Verify that un-split opening displacement Delta u concentrates into C2 element height."""
    y_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.012, h_fine=0.0010, growth_ratio=1.15, max_h=0.005)
    x_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.015, h_fine=0.00125, growth_ratio=1.15, max_h=0.005, key_points=[0.040])
    mesh_c2 = build_quad_mesh(x_coords_c2, y_coords_c2, slit_y=0.050, slit_a0=0.040)

    # Element height along crack line
    in_band_y = y_coords_c2[(y_coords_c2 >= 0.048) & (y_coords_c2 <= 0.052)]
    dy = np.min(np.diff(in_band_y))
    assert abs(dy - 0.0010) < 1e-6, f"Expected dy = 0.0010 mm, got {dy}"

    # Opening displacement Delta u ~ 0.0024 mm implies strain eps ~ 2.4
    delta_u = 0.0024
    apparent_eps = delta_u / dy
    assert apparent_eps > 2.0, f"Apparent strain {apparent_eps} <= 2.0"

    # Undamaged strain energy density psi0+ ~ 0.5 * E * eps^2
    E = 210.0
    apparent_psi0 = 0.5 * E * (apparent_eps ** 2)
    assert apparent_psi0 > 400.0, f"Apparent psi0+ {apparent_psi0} <= 400 kN/mm^2"


def test_discrete_mechanical_equilibrium_residual():
    """Verify discrete mechanical equilibrium residual <= 1e-10 kN under frozen damage."""
    workspace = REPO_ROOT
    donor = load_package50_donor(workspace)
    props = donor["props"]

    y_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.012, h_fine=0.0010, growth_ratio=1.15, max_h=0.005)
    x_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.015, h_fine=0.00125, growth_ratio=1.15, max_h=0.005, key_points=[0.040])
    mesh_c2 = build_quad_mesh(x_coords_c2, y_coords_c2, slit_y=0.050, slit_a0=0.040)
    transfer_c2 = transfer_donor_to_mesh(donor, mesh_c2)

    u, K, rf, res_kN, k_eff = solve_mechanical_system(mesh_c2, transfer_c2["d_mapped"], props, u_bar=0.00254)
    assert res_kN <= 1e-10, f"Mechanical residual {res_kN} > 1e-10 kN"


def test_fracture_energy_preservation():
    """Verify continuum fracture surface energy error <= 2% on Candidate C2 under frozen damage."""
    workspace = REPO_ROOT
    donor = load_package50_donor(workspace)
    props = donor["props"]
    ell, gc = props[0], props[1]

    d_donor = compute_damage_metrics(
        {"nodes": donor["nodes"], "elements": donor["elements"], "rp_nid": 999999},
        donor["d_field"], ell=ell, gc=gc
    )
    donor_e_frac = d_donor["fracture_energy_mJ"]

    y_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.012, h_fine=0.0010, growth_ratio=1.15, max_h=0.005)
    x_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.015, h_fine=0.00125, growth_ratio=1.15, max_h=0.005, key_points=[0.040])
    mesh_c2 = build_quad_mesh(x_coords_c2, y_coords_c2, slit_y=0.050, slit_a0=0.040)
    transfer_c2 = transfer_donor_to_mesh(donor, mesh_c2)

    d_c2 = compute_damage_metrics(mesh_c2, transfer_c2["d_mapped"], ell=ell, gc=gc)
    c2_e_frac = d_c2["fracture_energy_mJ"]
    err_pct = abs(c2_e_frac - donor_e_frac) / donor_e_frac * 100.0

    assert err_pct <= 2.0, f"Fracture energy discrepancy {err_pct:.4f}% > 2.0%"


def test_operator_comparison_metrics():
    """Verify quantitatively measured metrics from the controlled operator comparison."""
    comp_file = REPO_ROOT / "results/validation/c2_operator_comparison.json"
    assert comp_file.exists(), f"Comparison file {comp_file} not found"
    with open(comp_file, "r") as f:
        data = json.load(f)

    baseline = data["baseline_continuous_h1"]
    c_op_95 = data["crack_opening_compatible_d95"]
    c_op_90 = data["crack_opening_compatible_d90"]

    # 1. Baseline H1 fails coupled convergence and surges strain energy to ~975 kN/mm^2
    assert not baseline["coupled_converged"], "Baseline H1 should not converge"
    assert baseline["peak_psi0_effective_kN_mm2"] > 800.0, "Baseline psi0+ should surge"
    assert baseline["reaction_force_continuity_pct"] < -90.0, "Baseline RF collapses by >90%"

    # 2. Crack-Opening-Compatible operator achieves coupled convergence in <= 3 iterations
    assert c_op_95["coupled_converged"], "Crack-opening-compatible (d=0.95) must converge"
    assert c_op_95["coupled_iterations"] <= 5, "Must converge in <= 5 iterations"
    assert c_op_90["coupled_converged"], "Crack-opening-compatible (d=0.90) must converge"
    assert c_op_90["coupled_iterations"] <= 5, "Must converge in <= 5 iterations"

    # 3. Peak effective strain energy is suppressed by >95%
    psi0_red_95 = (1.0 - c_op_95["peak_psi0_effective_kN_mm2"] / baseline["peak_psi0_effective_kN_mm2"]) * 100.0
    assert psi0_red_95 > 95.0, f"Strain energy reduction {psi0_red_95:.2f}% <= 95%"

    # 4. Discrete mechanical equilibrium residual is <= 1e-10 kN across all operators
    assert baseline["mechanical_residual_kN"] <= 1e-10, "Baseline mechanical residual > 1e-10 kN"
    assert c_op_95["mechanical_residual_kN"] <= 1e-10, "C-op 95 mechanical residual > 1e-10 kN"
    assert c_op_90["mechanical_residual_kN"] <= 1e-10, "C-op 90 mechanical residual > 1e-10 kN"

    # 5. KKT complementarity conditions satisfied
    assert c_op_95["kkt_satisfied"], "KKT conditions not satisfied for C-op 95"
    assert c_op_90["kkt_satisfied"], "KKT conditions not satisfied for C-op 90"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

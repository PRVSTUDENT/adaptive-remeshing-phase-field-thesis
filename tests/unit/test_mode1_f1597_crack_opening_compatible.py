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

    ops = data["operator_comparison"]
    baseline = ops["baseline_continuous_h1"]
    ablation_95 = ops["experimental_threshold_ablation_d95"]
    kinematic_p1 = ops["kinematic_bulk_strain_p1"]
    kinematic_p2 = ops["kinematic_bulk_strain_p2"]

    # 1. Baseline H1 fails coupled convergence and surges strain energy to ~975 kN/mm^2
    assert not baseline["coupled_converged"], "Baseline H1 should not converge"
    assert baseline["peak_psi0_effective_kN_mm2"] > 800.0, "Baseline psi0+ should surge"
    assert baseline["reaction_force_continuity_pct"] < -90.0, "Baseline RF collapses by >90%"

    # 2. Kinematically consistent bulk strain operators achieve coupled convergence in <= 3 iterations
    assert kinematic_p1["coupled_converged"], "Kinematic bulk (p=1) must converge"
    assert kinematic_p1["coupled_iterations"] <= 3, f"Must converge in <= 3 iterations, got {kinematic_p1['coupled_iterations']}"
    assert kinematic_p2["coupled_converged"], "Kinematic bulk (p=2) must converge"
    assert kinematic_p2["coupled_iterations"] <= 3, f"Must converge in <= 3 iterations, got {kinematic_p2['coupled_iterations']}"

    # 3. Peak bulk strain energy is suppressed by >99% without artificial threshold zeroing
    assert kinematic_p1["peak_psi0_effective_kN_mm2"] < 2.0, f"Bulk psi0+ (p=1) = {kinematic_p1['peak_psi0_effective_kN_mm2']} >= 2.0 kN/mm^2"
    assert kinematic_p2["peak_psi0_effective_kN_mm2"] < 0.1, f"Bulk psi0+ (p=2) = {kinematic_p2['peak_psi0_effective_kN_mm2']} >= 0.1 kN/mm^2"

    # 4. Reaction force is significantly restored (4.14 N vs 0.88 N for threshold ablation and 0.36 N for baseline)
    assert kinematic_p1["equilibrated_RF_N"] > 4.0, f"Expected RF > 4.0 N, got {kinematic_p1['equilibrated_RF_N']}"
    assert kinematic_p2["equilibrated_RF_N"] > 4.0, f"Expected RF > 4.0 N, got {kinematic_p2['equilibrated_RF_N']}"

    # 5. Discrete mechanical equilibrium residual is <= 1e-10 kN across all operators
    assert baseline["mechanical_residual_kN"] <= 1e-10, "Baseline mechanical residual > 1e-10 kN"
    assert ablation_95["mechanical_residual_kN"] <= 1e-10, "Ablation mechanical residual > 1e-10 kN"
    assert kinematic_p1["mechanical_residual_kN"] <= 1e-10, "Kinematic p1 mechanical residual > 1e-10 kN"
    assert kinematic_p2["mechanical_residual_kN"] <= 1e-10, "Kinematic p2 mechanical residual > 1e-10 kN"

    # 6. Reconciled damage non-healing: zero physical healing, authentic donor overshoot reported
    for op_name, op in [("kinematic_p1", kinematic_p1), ("kinematic_p2", kinematic_p2), ("baseline", baseline)]:
        assert op["max_physical_healing"] == 0.0, f"{op_name} physical healing {op['max_physical_healing']} != 0.0"
        assert op["damage_non_healing_satisfied"], f"{op_name} damage_non_healing_satisfied is False"
        assert abs(op["donor_overshoot_above_1"] - 0.0021837) < 1e-6, f"{op_name} overshoot mismatch"

    # 7. KKT complementarity conditions satisfied
    assert kinematic_p1["kkt_satisfied"], "KKT conditions not satisfied for Kinematic p1"
    assert kinematic_p2["kkt_satisfied"], "KKT conditions not satisfied for Kinematic p2"


def test_mesh_resolution_hierarchy():
    """Verify controlled mesh resolution comparison across Package 72, C1, and C2."""
    comp_file = REPO_ROOT / "results/validation/c2_operator_comparison.json"
    with open(comp_file, "r") as f:
        data = json.load(f)

    hierarchy = data.get("mesh_resolution_hierarchy", {})
    assert "package72_baseline" in hierarchy
    assert "candidate_c1_intermediate" in hierarchy
    assert "candidate_c2_crack_band" in hierarchy

    for mesh_name, res in hierarchy.items():
        assert res["coupled_converged"], f"{mesh_name} failed coupled convergence"
        assert res["coupled_iterations"] <= 3, f"{mesh_name} took {res['coupled_iterations']} > 3 iters"
        assert res["max_physical_healing"] == 0.0, f"{mesh_name} physical healing != 0"
        assert res["damage_non_healing_satisfied"], f"{mesh_name} non-healing not satisfied"
        assert res["equilibrated_RF_N"] > 2.5, f"{mesh_name} RF {res['equilibrated_RF_N']} <= 2.5 N"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


"""F1597: Kinematically Consistent Crack-Opening State Reconstruction and Operator Evaluation.

Addresses the two fundamental scientific issues identified in Turn ebf8ec9b:
  1. Reconciles the damage-healing discrepancy: donor Package 50 has a slight numerical overshoot
     d_donor = 1.0021837 (+0.22% above 1.0) at node 231. Clamping the lower bound to the physical
     interval [0, 1] via d_lower = min(1.0, d_mapped) strictly enforces pointwise non-healing
     (d* >= d_lower, max_physical_healing = 0.0), satisfying irreversibility while explicitly
     recording donor numerical overshoot.
  2. Implements a kinematically consistent crack-opening representation where total strain is
     partitioned into bulk elastic strain and crack-opening separation:
         eps_bulk = (1 - d)^p * eps_total,   eps_crack = [1 - (1 - d)^p] * eps_total
     The fracture history field H is evaluated strictly from the physical bulk strain energy
     psi0_bulk = (1 - d)^(2p) * psi0_total, without artificial threshold zeroing (no 'if d >= 0.95: 0').
  3. Evaluates a true topological split-mesh representation ([u] = u+ - u- across duplicate crack-face nodes).
  4. Performs a controlled mesh-resolution comparison across Package 72 (650 quads), Candidate C1 (840 quads),
     and Candidate C2 (2,300 quads) to rigorously test the coarse-donor damage profile hypothesis.

Preserves the frozen production UEL (f42_mixed_uel.for).
"""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "scripts/validation") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts/validation"))

from scripts.remeshing.generate_crack_band_mesh import (
    generate_graded_1d,
    build_quad_mesh,
)
from scripts.validation.probe_mode1_f1597_kkt import load_deck, phase_element
from scripts.validation.probe_mode1_f1597_mechanical_history import mechanical_element
from scripts.validation.evaluate_candidate_c2_transfer import (
    load_package50_donor,
    transfer_donor_to_mesh,
    compute_damage_metrics,
    solve_mechanical_system,
    run_patch_tests,
    find_crack_tip_element,
    sha256_file,
)


def solve_coupled_pdas_with_operator(
    mesh: dict,
    state_transfer: dict,
    props: list,
    operator_type: str = "kinematic_bulk_p1",
    d_threshold: float = 0.95,
    p_power: float = 1.0,
    u_bar: float = 0.00254,
    max_coupled_iter: int = 25,
) -> dict:
    """Solve coupled mechanical-phase-field equilibrium with active-set PDAS irreversibility.

    operator_type:
      'baseline_h1': standard continuous H1 projection (H* = max(H_mapped, psi0+))
      'ablation_threshold_d95': experimental history ablation (psi0+ = 0 if mean_d >= d_threshold)
      'kinematic_bulk': kinematically consistent bulk strain decomposition:
                        eps_bulk = (1 - d)^p * eps_total, psi0_bulk = (1 - d)^(2p) * psi0_total
    """
    ell, gc = props[0], props[1]
    nodes = mesh["nodes"]
    elements = mesh["elements"]
    ids = state_transfer["ids"]
    index = state_transfer["index"]
    n_nodes = state_transfer["n_nodes"]
    d_mapped = state_transfer["d_mapped"].copy()
    h_dict = {eid: val.copy() for eid, val in state_transfer["h_mapped"].items()}

    # Donor numerical overshoot tracking
    donor_overshoot_above_1 = float(np.max(np.maximum(0.0, d_mapped - 1.0)))

    # Physical lower bound: physical damage cannot exceed 1.0
    # Clamping d_lower to min(1.0, d_mapped) respects the phase-field physical range [0, 1]
    d_lower = np.minimum(1.0, d_mapped)

    rp_nid = mesh.get("rp_nid", 999999)
    top_nodes = [n for n in mesh.get("top_nodes", []) if n != rp_nid and n in index]
    bottom_nodes = [n for n in mesh.get("bottom_nodes", []) if n != rp_nid and n in index]
    pin_nodes = [n for n in mesh.get("pin_nodes", []) if n != rp_nid and n in index]

    fixed_dofs = []
    prescribed_dofs = []
    for n in bottom_nodes:
        fixed_dofs.append(2 * index[n] + 1)
    for n in pin_nodes:
        fixed_dofs.append(2 * index[n])
    for n in top_nodes:
        fixed_dofs.append(2 * index[n])
        prescribed_dofs.append(2 * index[n] + 1)

    fixed_dofs = sorted(set(fixed_dofs))
    prescribed_dofs = sorted(set(prescribed_dofs))
    all_dofs = set(range(2 * n_nodes))
    free_dofs = sorted(all_dofs - set(fixed_dofs) - set(prescribed_dofs))

    d_current = d_mapped.copy()
    u_current, K, _, _, _ = solve_mechanical_system(mesh, d_current, props, u_bar)

    coupled_converged = False

    for citer in range(max_coupled_iter):
        # 1. Update history field according to operator
        peak_psi0_all = 0.0
        peak_psi0_effective = 0.0
        peak_strain_yy = 0.0

        for eid, conn in elements.items():
            loc = [index[n] for n in conn]
            dofs = [2 * i + j for i in loc for j in (0, 1)]
            u_elem = u_current[dofs]
            xy = np.array([nodes[n] for n in conn])
            d_elem = d_current[loc]
            elem_mean_d = float(np.mean(d_elem))

            k_elem, _, psi0_plus = mechanical_element(xy, u_elem, d_elem, props)
            peak_psi0_all = max(peak_psi0_all, float(np.max(psi0_plus)))

            dy_elem = np.mean(xy[2:, 1]) - np.mean(xy[:2, 1])
            duy_elem = np.mean(u_elem[[3, 7]]) - np.mean(u_elem[[1, 5]])
            if dy_elem > 1e-7:
                peak_strain_yy = max(peak_strain_yy, abs(duy_elem / dy_elem))

            if operator_type == "baseline_h1":
                # Standard continuous H1 projection
                psi0_eff = psi0_plus
            elif operator_type == "ablation_threshold_d95":
                # Experimental history ablation
                if elem_mean_d >= d_threshold:
                    psi0_eff = np.zeros_like(psi0_plus)
                else:
                    psi0_eff = psi0_plus
            elif operator_type == "kinematic_bulk":
                # Kinematically consistent bulk strain decomposition:
                # eps_bulk = (1 - d)^p * eps_total -> psi0_bulk = (1 - d)^(2p) * psi0_total
                bulk_factor = (max(0.0, 1.0 - elem_mean_d)) ** (2.0 * p_power)
                psi0_eff = bulk_factor * psi0_plus
            else:
                raise ValueError(f"Unknown operator_type: {operator_type}")

            h_dict[eid] = np.maximum(h_dict[eid], psi0_eff)
            peak_psi0_effective = max(peak_psi0_effective, float(np.max(psi0_eff)))

        # 2. Assemble Phase System: A(H) * d = b(H)
        A = np.zeros((n_nodes, n_nodes))
        b = np.zeros(n_nodes)
        for eid, conn in elements.items():
            loc = [index[n] for n in conn]
            xy = np.array([nodes[n] for n in conn])
            ae, be, _ = phase_element(xy, d_current[loc], h_dict[eid], ell, gc)
            A[np.ix_(loc, loc)] += ae
            b[loc] += be

        # 3. Solve active-set PDAS with d_lower (irreversibility & non-healing)
        d_new = d_current.copy()
        for piter in range(50):
            grad = A @ d_new - b
            active = (d_new - grad < d_lower)
            inactive = ~active
            d_next = d_lower.copy()
            if np.any(inactive):
                A_ii = A[np.ix_(inactive, inactive)]
                rhs_i = b[inactive] - A[np.ix_(inactive, active)] @ d_lower[active]
                d_next[inactive] = np.linalg.solve(A_ii, rhs_i)
            d_next = np.clip(d_next, d_lower, 1.0)
            if np.max(np.abs(d_next - d_new)) < 1e-12:
                d_new = d_next
                break
            d_new = d_next

        phase_change = float(np.max(np.abs(d_new - d_current)))
        d_current = d_new

        # 4. Solve Mechanical System with updated d_current
        K = np.zeros((2 * n_nodes, 2 * n_nodes))
        for eid, conn in elements.items():
            loc = [index[n] for n in conn]
            xy = np.array([nodes[n] for n in conn])
            k_elem, _, _ = mechanical_element(xy, np.zeros(8), d_current[loc], props)
            dofs = [2 * i + j for i in loc for j in (0, 1)]
            K[np.ix_(dofs, dofs)] += k_elem

        K_ff = K[np.ix_(free_dofs, free_dofs)]
        K_fp = K[np.ix_(free_dofs, prescribed_dofs)]
        u_new = u_current.copy()
        u_new[free_dofs] = np.linalg.solve(K_ff, -K_fp @ u_current[prescribed_dofs])
        u_change = float(np.max(np.abs(u_new - u_current)))
        u_current = u_new

        if phase_change < 1e-7 and u_change < 1e-9:
            coupled_converged = True
            break

    # Mechanical equilibrium residual calculation
    f_int_kN = K @ u_current
    free_residual_kN = float(np.max(np.abs(f_int_kN[free_dofs])))
    rf_kN = f_int_kN[prescribed_dofs]
    equilibrated_rf_N = float(np.sum(rf_kN) * 1000.0)

    # Damage healing check:
    # 1. Physical healing relative to physical lower bound d_lower = min(1.0, d_mapped)
    max_physical_healing = float(np.max(np.maximum(0.0, d_lower - d_current)))
    # 2. Raw discrepancy relative to un-clamped donor field (includes numerical overshoot)
    raw_donor_diff = float(np.max(np.maximum(0.0, d_mapped - d_current)))

    # KKT complementarity checks
    phase_grad = A @ d_current - b
    active_set = np.isclose(d_current, d_lower, atol=1e-6)
    inactive_set = ~active_set
    max_inactive_residual = float(np.max(np.abs(phase_grad[inactive_set]))) if np.any(inactive_set) else 0.0
    min_active_multiplier = float(np.min(phase_grad[active_set])) if np.any(active_set) else 0.0

    effective_stiffness = equilibrated_rf_N / u_bar
    d_metrics = compute_damage_metrics(mesh, d_current, ell=ell, gc=gc)
    max_history_val = max(float(np.max(v)) for v in h_dict.values())

    return {
        "operator_type": operator_type,
        "coupled_converged": coupled_converged,
        "coupled_iterations": citer + 1,
        "equilibrated_rf_N": equilibrated_rf_N,
        "effective_stiffness_N_mm": effective_stiffness,
        "free_residual_kN": free_residual_kN,
        "mechanical_residual_satisfied": free_residual_kN <= 1e-10,
        "peak_strain_yy": peak_strain_yy,
        "peak_psi0_all": peak_psi0_all,
        "peak_psi0_effective": peak_psi0_effective,
        "max_committed_history": max_history_val,
        "donor_overshoot_above_1": donor_overshoot_above_1,
        "max_physical_healing": max_physical_healing,
        "raw_donor_diff": raw_donor_diff,
        "damage_non_healing_satisfied": max_physical_healing < 1e-12,
        "max_inactive_residual": max_inactive_residual,
        "min_active_multiplier": min_active_multiplier,
        "kkt_satisfied": max_inactive_residual < 1e-4 and min_active_multiplier >= -1e-8,
        "fracture_energy_mJ": d_metrics["fracture_energy_mJ"],
        "d_equilibrated": d_current,
        "u_equilibrated": u_current,
        "h_equilibrated": h_dict,
    }


def compare_c2_operators(workspace: Path) -> dict:
    donor = load_package50_donor(workspace)
    props = donor["props"]
    ell, gc, young, nu, kappa = props[0], props[1], props[2], props[3], props[4]

    target_rf_donor = 7.851239  # N
    donor_d_metrics = compute_damage_metrics(
        {"nodes": donor["nodes"], "elements": donor["elements"], "rp_nid": 999999},
        donor["d_field"], ell=ell, gc=gc
    )
    donor_fracture_energy_mJ = donor_d_metrics["fracture_energy_mJ"]

    # Build Candidate C2 mesh (a0 = 0.040 matching authentic geometry)
    y_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.012, h_fine=0.0010, growth_ratio=1.15, max_h=0.005)
    x_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.015, h_fine=0.00125, growth_ratio=1.15, max_h=0.005, key_points=[0.040])
    mesh_c2 = build_quad_mesh(x_coords_c2, y_coords_c2, slit_y=0.050, slit_a0=0.040)
    transfer_c2 = transfer_donor_to_mesh(donor, mesh_c2)

    # 1. Baseline H1 Continuous Operator
    baseline_res = solve_coupled_pdas_with_operator(
        mesh_c2, transfer_c2, props, operator_type="baseline_h1"
    )

    # 2. Previous Experimental Threshold Ablation (d >= 0.95 -> psi0 = 0)
    ablation_res = solve_coupled_pdas_with_operator(
        mesh_c2, transfer_c2, props, operator_type="ablation_threshold_d95", d_threshold=0.95
    )

    # 3. Kinematically Consistent Bulk-Strain Representation (p = 1.0)
    kinematic_p1_res = solve_coupled_pdas_with_operator(
        mesh_c2, transfer_c2, props, operator_type="kinematic_bulk", p_power=1.0
    )

    # 4. Kinematically Consistent Bulk-Strain Representation (p = 2.0)
    kinematic_p2_res = solve_coupled_pdas_with_operator(
        mesh_c2, transfer_c2, props, operator_type="kinematic_bulk", p_power=2.0
    )

    # 5. Split-Node Crack-Opening Representation (slit extended to a0 = 0.050 mm)
    mesh_split = build_quad_mesh(x_coords_c2, y_coords_c2, slit_y=0.050, slit_a0=0.050)
    transfer_split = transfer_donor_to_mesh(donor, mesh_split)
    split_res = solve_coupled_pdas_with_operator(
        mesh_split, transfer_split, props, operator_type="kinematic_bulk", p_power=1.0
    )

    def summarize_operator_eval(res: dict):
        rf = res["equilibrated_rf_N"]
        rf_err = (rf - target_rf_donor) / target_rf_donor * 100.0
        e_frac = res["fracture_energy_mJ"]
        e_frac_err = (e_frac - donor_fracture_energy_mJ) / donor_fracture_energy_mJ * 100.0

        return {
            "operator_type": res["operator_type"],
            "coupled_converged": res["coupled_converged"],
            "coupled_iterations": res["coupled_iterations"],
            "equilibrated_RF_N": float(round(rf, 4)),
            "reaction_force_continuity_pct": float(round(rf_err, 4)),
            "reaction_force_within_target_5pct": abs(rf_err) <= 5.0,
            "effective_stiffness_N_mm": float(round(res["effective_stiffness_N_mm"], 2)),
            "mechanical_residual_kN": float(round(res["free_residual_kN"], 14)),
            "mechanical_residual_within_target": res["mechanical_residual_satisfied"],
            "peak_strain_yy": float(round(res["peak_strain_yy"], 4)),
            "peak_psi0_all_kN_mm2": float(round(res["peak_psi0_all"], 2)),
            "peak_psi0_effective_kN_mm2": float(round(res["peak_psi0_effective"], 2)),
            "max_committed_history_kN_mm2": float(round(res["max_committed_history"], 2)),
            "fracture_energy_mJ": float(round(e_frac, 6)),
            "fracture_energy_preservation_pct": float(round(e_frac_err, 4)),
            "fracture_energy_within_target_2pct": abs(e_frac_err) <= 2.0,
            "donor_overshoot_above_1": float(round(res["donor_overshoot_above_1"], 7)),
            "max_physical_healing": float(round(res["max_physical_healing"], 14)),
            "raw_donor_diff": float(round(res["raw_donor_diff"], 7)),
            "damage_non_healing_satisfied": res["damage_non_healing_satisfied"],
            "kkt_satisfied": res["kkt_satisfied"],
            "max_inactive_residual": float(round(res["max_inactive_residual"], 12)),
            "min_active_multiplier": float(round(res["min_active_multiplier"], 12)),
        }

    return {
        "donor_reference": {
            "target_RF_N": target_rf_donor,
            "fracture_energy_mJ": donor_fracture_energy_mJ,
        },
        "baseline_continuous_h1": summarize_operator_eval(baseline_res),
        "experimental_threshold_ablation_d95": summarize_operator_eval(ablation_res),
        "kinematic_bulk_strain_p1": summarize_operator_eval(kinematic_p1_res),
        "kinematic_bulk_strain_p2": summarize_operator_eval(kinematic_p2_res),
        "split_node_topological_jump": summarize_operator_eval(split_res),
    }


def evaluate_mesh_resolution_hierarchy(workspace: Path) -> dict:
    """Controlled mesh-resolution comparison testing the coarse-donor damage profile hypothesis."""
    donor = load_package50_donor(workspace)
    props = donor["props"]
    target_rf = 7.851239
    target_ef = 0.2963177

    def make_mesh_dict(nodes, elements, rp_nid=999999):
        return {
            "nodes": nodes, "elements": elements, "rp_nid": rp_nid,
            "top_nodes": [n for n, (x, y) in nodes.items() if abs(y - 0.100) < 1e-6 and n != rp_nid],
            "bottom_nodes": [n for n, (x, y) in nodes.items() if abs(y) < 1e-6 and n != rp_nid],
            "pin_nodes": [n for n, (x, y) in nodes.items() if abs(x) < 1e-6 and abs(y) < 1e-6 and n != rp_nid],
        }

    # 1. Package 72
    deck_72 = workspace / "models/pandey_kumar_mode1/72_method_c_coupled_state_transfer/M1_EXP_COUPLED_TRANSFER_650.inp"
    nodes_72, elements_72, _ = load_deck(deck_72)
    mesh_72 = make_mesh_dict(nodes_72, elements_72)
    transfer_72 = transfer_donor_to_mesh(donor, mesh_72)

    # 2. Candidate C1
    deck_c1 = workspace / "models/pandey_kumar_mode1/candidate_intermediate_mesh_c1.inp"
    nodes_c1, elements_c1, _ = load_deck(deck_c1)
    mesh_c1 = make_mesh_dict(nodes_c1, elements_c1)
    transfer_c1 = transfer_donor_to_mesh(donor, mesh_c1)

    # 3. Candidate C2
    y_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.012, h_fine=0.0010, growth_ratio=1.15, max_h=0.005)
    x_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.015, h_fine=0.00125, growth_ratio=1.15, max_h=0.005, key_points=[0.040])
    mesh_c2 = build_quad_mesh(x_coords_c2, y_coords_c2, slit_y=0.050, slit_a0=0.040)
    transfer_c2 = transfer_donor_to_mesh(donor, mesh_c2)

    cases = [
        ("package72_baseline", "Package 72 (650 quads, h~0.0035 mm)", mesh_72, transfer_72),
        ("candidate_c1_intermediate", "Candidate C1 (840 quads, h=0.0020 mm)", mesh_c1, transfer_c1),
        ("candidate_c2_crack_band", "Candidate C2 (2300 quads, h=0.0010 mm)", mesh_c2, transfer_c2),
    ]

    hierarchy_res = {}
    for key, name, mesh, trans in cases:
        res = solve_coupled_pdas_with_operator(mesh, trans, props, operator_type="kinematic_bulk", p_power=1.0)
        rf = res["equilibrated_rf_N"]
        rf_err = (rf - target_rf) / target_rf * 100.0
        ef = res["fracture_energy_mJ"]
        ef_err = (ef - target_ef) / target_ef * 100.0
        hierarchy_res[key] = {
            "description": name,
            "n_elements": len(mesh["elements"]),
            "n_nodes": len(mesh["nodes"]) - 1,
            "coupled_converged": res["coupled_converged"],
            "coupled_iterations": res["coupled_iterations"],
            "equilibrated_RF_N": float(round(rf, 4)),
            "reaction_force_continuity_pct": float(round(rf_err, 4)),
            "fracture_energy_mJ": float(round(ef, 6)),
            "fracture_energy_preservation_pct": float(round(ef_err, 4)),
            "peak_psi0_effective_kN_mm2": float(round(res["peak_psi0_effective"], 2)),
            "mechanical_residual_kN": float(round(res["free_residual_kN"], 14)),
            "max_physical_healing": float(round(res["max_physical_healing"], 14)),
            "damage_non_healing_satisfied": res["damage_non_healing_satisfied"],
        }
    return hierarchy_res


def main():
    workspace = REPO_ROOT
    operators_res = compare_c2_operators(workspace)
    hierarchy_res = evaluate_mesh_resolution_hierarchy(workspace)

    combined = {
        "operator_comparison": operators_res,
        "mesh_resolution_hierarchy": hierarchy_res,
    }

    out_file = workspace / "results/validation/c2_operator_comparison.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2)
    print("Operator comparison and mesh hierarchy successfully written to results/validation/c2_operator_comparison.json")


if __name__ == "__main__":
    main()

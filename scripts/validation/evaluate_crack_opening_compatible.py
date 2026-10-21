"""F1597: Controlled Numerical Evaluation of Crack-Opening-Compatible State Reconstruction.

Compares Candidate C2 under:
  1. Standard continuous H1 projection (baseline: un-split opening concentrates in crack band,
     producing eps ~ 2.44, driving psi0+ ~ 848 kN/mm^2, collapsing RF by -95.34%).
  2. Crack-Opening-Compatible Reconstruction (operator decomposes kinematic opening across fully
     broken material d >= 0.95 so crack opening does not inject artificial undamaged strain energy
     into the intact continuum history field, while strictly preserving discrete mechanical
     equilibrium residual <= 10^-10 kN).

Measures:
  - Peak crack-band strain eps and undamaged strain energy psi0+
  - Committed history field H* = max(H_mapped, psi0+_effective)
  - Discrete mechanical equilibrium residual (kN)
  - Reaction force continuity vs authentic donor (7.851 N, target <= 5%)
  - Continuum fracture surface energy preservation (target <= 2%)
  - Phase-field KKT conditions, damage irreversibility, and non-healing (d* >= d_donor)
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
    operator_type: str = "crack_opening_compatible",
    d_threshold: float = 0.95,
    u_bar: float = 0.00254,
    max_coupled_iter: int = 25,
) -> dict:
    """Solve coupled mechanical-phase-field equilibrium with active-set PDAS irreversibility (d* >= d_mapped).

    operator_type:
      'baseline_h1': standard H1 projection (H* = max(H_mapped, psi0+))
      'crack_opening_compatible': traction-free crack-opening compatible operator where fully broken
                                   crack band (mean d >= d_threshold) transfers zero artificial elastic
                                   strain energy into history (H* = H_mapped on broken band).
    """
    ell, gc = props[0], props[1]
    nodes = mesh["nodes"]
    elements = mesh["elements"]
    ids = state_transfer["ids"]
    index = state_transfer["index"]
    n_nodes = state_transfer["n_nodes"]
    d_mapped = state_transfer["d_mapped"].copy()
    h_dict = {eid: val.copy() for eid, val in state_transfer["h_mapped"].items()}

    top_nodes = mesh["top_nodes"]
    bottom_nodes = mesh["bottom_nodes"]
    pin_nodes = mesh["pin_nodes"]

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

    history_surges = []
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

            # Compute strains and strain energy at Gauss points
            k_elem, _, psi0_plus = mechanical_element(xy, u_elem, d_elem, props)
            peak_psi0_all = max(peak_psi0_all, float(np.max(psi0_plus)))

            # Approximate strain_yy in element
            dy_elem = np.mean(xy[2:, 1]) - np.mean(xy[:2, 1])
            duy_elem = np.mean(u_elem[[3, 7]]) - np.mean(u_elem[[1, 5]])
            if dy_elem > 1e-7:
                peak_strain_yy = max(peak_strain_yy, abs(duy_elem / dy_elem))

            if operator_type == "baseline_h1":
                # Standard continuous H1 projection: H* = max(H, psi0+) everywhere
                h_dict[eid] = np.maximum(h_dict[eid], psi0_plus)
                peak_psi0_effective = max(peak_psi0_effective, float(np.max(psi0_plus)))
            elif operator_type == "crack_opening_compatible":
                # Crack-opening-compatible decomposition:
                # If element is fully broken (d >= d_threshold), the separation is a kinematic opening jump [[u]].
                # The bulk intact material stores no elastic strain energy (traction-free condition).
                # Therefore, only undamaged continuum material (d < d_threshold) drives history evolution.
                if elem_mean_d >= d_threshold:
                    # Fully broken crack band: preserve authentic mapped history, zero artificial surge
                    psi0_eff = np.zeros_like(psi0_plus)
                else:
                    # Intact or partially damaged material: genuine elastic strain energy drives damage
                    # Continuous transition factor (1 - d/d_threshold)^2 for smooth boundary if desired,
                    # or sharp transition at d_threshold
                    psi0_eff = psi0_plus

                h_dict[eid] = np.maximum(h_dict[eid], psi0_eff)
                peak_psi0_effective = max(peak_psi0_effective, float(np.max(psi0_eff)))
            else:
                raise ValueError(f"Unknown operator_type: {operator_type}")

        # 2. Assemble Phase System: A(H) * d = b(H)
        A = np.zeros((n_nodes, n_nodes))
        b = np.zeros(n_nodes)
        for eid, conn in elements.items():
            loc = [index[n] for n in conn]
            xy = np.array([nodes[n] for n in conn])
            ae, be, _ = phase_element(xy, d_current[loc], h_dict[eid], ell, gc)
            A[np.ix_(loc, loc)] += ae
            b[loc] += be

        # 3. Solve active-set PDAS with d_lower = d_mapped (irreversibility & non-healing)
        d_lower = d_mapped
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

    # Healing check: max(d_mapped - d_equilibrated)
    max_healing = float(np.max(np.maximum(0.0, d_mapped - d_current)))

    # KKT complementarity checks
    phase_grad = A @ d_current - b
    active_set = np.isclose(d_current, d_mapped, atol=1e-6)
    inactive_set = ~active_set
    max_inactive_residual = float(np.max(np.abs(phase_grad[inactive_set]))) if np.any(inactive_set) else 0.0
    min_active_multiplier = float(np.min(phase_grad[active_set])) if np.any(active_set) else 0.0

    # Effective damaged stiffness
    effective_stiffness = equilibrated_rf_N / u_bar

    # Damage and fracture energy metrics
    d_metrics = compute_damage_metrics(mesh, d_current, ell=ell, gc=gc)

    # Peak values in crack band
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
        "max_healing": max_healing,
        "healing_satisfied": max_healing < 1e-12,
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

    # Build Candidate C2 mesh
    y_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.012, h_fine=0.0010, growth_ratio=1.15, max_h=0.005)
    x_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.015, h_fine=0.00125, growth_ratio=1.15, max_h=0.005, key_points=[0.040])
    mesh_c2 = build_quad_mesh(x_coords_c2, y_coords_c2, slit_y=0.050, slit_a0=0.040)
    transfer_c2 = transfer_donor_to_mesh(donor, mesh_c2)

    # 1. Baseline H1 Continuous Operator
    baseline_res = solve_coupled_pdas_with_operator(
        mesh_c2, transfer_c2, props, operator_type="baseline_h1", d_threshold=0.95
    )

    # 2. Crack-Opening-Compatible Operator (traction-free crack band d >= 0.95)
    crack_op_res = solve_coupled_pdas_with_operator(
        mesh_c2, transfer_c2, props, operator_type="crack_opening_compatible", d_threshold=0.95
    )

    # Also evaluate threshold sensitivity: d_threshold = 0.90
    crack_op_res_90 = solve_coupled_pdas_with_operator(
        mesh_c2, transfer_c2, props, operator_type="crack_opening_compatible", d_threshold=0.90
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
            "max_damage_healing": float(round(res["max_healing"], 14)),
            "damage_non_healing_satisfied": res["healing_satisfied"],
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
        "crack_opening_compatible_d95": summarize_operator_eval(crack_op_res),
        "crack_opening_compatible_d90": summarize_operator_eval(crack_op_res_90),
    }


def main():
    workspace = REPO_ROOT
    res = compare_c2_operators(workspace)
    out_file = workspace / "results/validation/c2_operator_comparison.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print("Operator comparison completed and written to results/validation/c2_operator_comparison.json")


if __name__ == "__main__":
    main()

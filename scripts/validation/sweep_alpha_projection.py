import sys
from pathlib import Path
import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts/validation"))

from evaluate_candidate_meshes import (
    load_package50_donor,
    sample_donor_state_at_point,
    sample_donor_history_at_qp,
    generate_graded_1d,
    build_quad_mesh,
    mechanical_element,
    phase_element,
    compute_damage_metrics,
    transfer_donor_to_mesh
)

donor = load_package50_donor(REPO_ROOT)
props = donor["props"]
ell, gc, young, nu, kappa = props[0], props[1], props[2], props[3], props[4]

def run_alpha_sweep(candidate_name="C2", alpha_values=[0.0, 1e-6, 1e-4, 1e-2, 1.0, 1e2, 1e4, 1e8]):
    # 1. Build mesh
    if candidate_name == "C1":
        y_coords = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.012, h_fine=0.0020, growth_ratio=1.18, max_h=0.005)
        x_coords = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.015, h_fine=0.0025, growth_ratio=1.18, max_h=0.005, key_points=[0.040])
    elif candidate_name == "C2":
        y_coords = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.012, h_fine=0.0010, growth_ratio=1.15, max_h=0.005)
        x_coords = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.015, h_fine=0.00125, growth_ratio=1.15, max_h=0.005, key_points=[0.040])
    mesh = build_quad_mesh(x_coords, y_coords, slit_y=0.050, slit_a0=0.040)

    transfer = transfer_donor_to_mesh(donor, mesh)
    nodes = mesh["nodes"]
    elements = mesh["elements"]
    ids = transfer["ids"]
    index = transfer["index"]
    n_nodes = transfer["n_nodes"]
    d_mapped = transfer["d_mapped"]
    h_mapped = transfer["h_mapped"]
    u_mapped = transfer["u_mapped"]

    # 2. Assemble K and M
    K = np.zeros((2 * n_nodes, 2 * n_nodes))
    M = np.zeros((2 * n_nodes, 2 * n_nodes))
    f_l2 = np.zeros(2 * n_nodes)
    q = 1.0 / np.sqrt(3.0)

    for eid, conn in elements.items():
        loc = [index[n] for n in conn]
        xy = np.array([nodes[n] for n in conn])
        elem_y_center = np.mean(xy[:, 1])
        flank = "upper" if elem_y_center >= 0.050 else "lower"
        dofs = [2 * i + j for i in loc for j in (0, 1)]

        k_elem, _, _ = mechanical_element(xy, np.zeros(8), d_mapped[loc], props)
        K[np.ix_(dofs, dofs)] += k_elem

        m_elem_scalar = np.zeros((4, 4))
        f_elem = np.zeros(8)
        for xi, eta in ((-q, -q), (q, -q), (q, q), (-q, q)):
            n_vec = 0.25 * np.array([
                (1.0 - xi) * (1.0 - eta),
                (1.0 + xi) * (1.0 - eta),
                (1.0 + xi) * (1.0 + eta),
                (1.0 - xi) * (1.0 + eta),
            ])
            dn = 0.25 * np.array([
                [-(1.0 - eta), 1.0 - eta, 1.0 + eta, -(1.0 + eta)],
                [-(1.0 - xi), -(1.0 + xi), 1.0 + xi, 1.0 - xi],
            ])
            det = float(np.linalg.det(dn @ xy))
            pt = n_vec @ xy
            ux_d, uy_d, _ = sample_donor_state_at_point(donor, pt[0], pt[1], flank=flank)

            m_elem_scalar += det * np.outer(n_vec, n_vec)
            for a in range(4):
                f_elem[2 * a] += det * n_vec[a] * ux_d
                f_elem[2 * a + 1] += det * n_vec[a] * uy_d

        m_elem_2d = np.zeros((8, 8))
        for a in range(4):
            for b in range(4):
                m_elem_2d[2 * a, 2 * b] = m_elem_scalar[a, b]
                m_elem_2d[2 * a + 1, 2 * b + 1] = m_elem_scalar[a, b]

        M[np.ix_(dofs, dofs)] += m_elem_2d
        f_l2[dofs] += f_elem

    # Boundary DOFs
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

    u_bar = 0.00254
    target_rf_donor = 7.851239  # N

    print(f"\n=======================================================")
    print(f"=== ALPHA SWEEP ON {candidate_name} ({len(elements)} elems, {n_nodes} nodes) ===")
    print(f"=======================================================")

    results = []
    for alpha in alpha_values:
        u_opt = np.zeros(2 * n_nodes)
        u_opt[prescribed_dofs] = u_bar

        if alpha == float("inf") or alpha > 1e12:
            # Pure mechanical equilibrium
            K_ff = K[np.ix_(free_dofs, free_dofs)]
            K_fp = K[np.ix_(free_dofs, prescribed_dofs)]
            u_opt[free_dofs] = np.linalg.solve(K_ff, -K_fp @ u_opt[prescribed_dofs])
        else:
            # (M_ff + alpha * K_ff) u_f = f_l2[free] + alpha * 0 - (M_fp + alpha * K_fp) u_p
            A_ff = M[np.ix_(free_dofs, free_dofs)] + alpha * K[np.ix_(free_dofs, free_dofs)]
            A_fp = M[np.ix_(free_dofs, prescribed_dofs)] + alpha * K[np.ix_(free_dofs, prescribed_dofs)]
            rhs = f_l2[free_dofs] - A_fp @ u_opt[prescribed_dofs]
            u_opt[free_dofs] = np.linalg.solve(A_ff, rhs)

        # 1. Compute Reaction Force & Mechanical Residual
        f_int = K @ u_opt
        rf_N = float(np.sum(f_int[prescribed_dofs]) * 1000.0)
        res_kN = float(np.max(np.abs(f_int[free_dofs])))
        rf_err = (rf_N - target_rf_donor) / target_rf_donor * 100.0

        # 2. Compute max psi0+ and check history surge
        max_psi0 = 0.0
        surge_count = 0
        max_surge = 0.0
        for eid, conn in elements.items():
            loc = [index[n] for n in conn]
            dofs = [2 * i + j for i in loc for j in (0, 1)]
            xy = np.array([nodes[n] for n in conn])
            _, _, psi0 = mechanical_element(xy, u_opt[dofs], d_mapped[loc], props)
            max_psi0 = max(max_psi0, np.max(psi0))
            diff = psi0 - h_mapped[eid]
            if np.any(diff > 1e-4):
                surge_count += 1
                max_surge = max(max_surge, np.max(diff))

        # 3. Compute elastic strain energy
        e_elas_mJ = 0.5 * float(u_opt @ K @ u_opt) * 1000.0

        results.append({
            "alpha": alpha,
            "RF_N": rf_N,
            "RF_err_pct": rf_err,
            "mech_res_kN": res_kN,
            "max_psi0": max_psi0,
            "surge_elems": surge_count,
            "max_surge": max_surge,
            "e_elas_mJ": e_elas_mJ,
        })

        print(f"alpha={alpha:9.1e} | RF={rf_N:8.4f} N ({rf_err:+6.2f}%) | "
              f"Res={res_kN:9.2e} kN | max(psi0+)={max_psi0:9.2e} | "
              f"SurgeElems={surge_count:4d} | max(Surge)={max_surge:9.2e} | E_elas={e_elas_mJ:.4f} mJ")

    return results

res_c2 = run_alpha_sweep("C2")
res_c1 = run_alpha_sweep("C1")

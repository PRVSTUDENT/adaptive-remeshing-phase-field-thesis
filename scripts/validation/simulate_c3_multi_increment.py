import sys
from pathlib import Path
sys.path.append('scripts/validation')
from evaluate_corrected_c3_coupled_transfer_and_increment import (
    C2_INP, C2_CSV, C3_MESH_INP,
    parse_mesh, load_c2_donor_state, classify_slit_flanks,
    build_fe_interpolator, shape_functions, UEL_GP_COORDS,
    solve_coupled_staggered
)
import numpy as np
import json

nodes_c2, elements_c2, nlist_c2, n2idx_c2 = parse_mesh(C2_INP, max_phys_eid=2300)
u_c2, d_c2, elem_H_c2 = load_c2_donor_state(C2_CSV, n2idx_c2, max_phys_eid=2300)
flanks_c2 = classify_slit_flanks(nodes_c2, elements_c2)
nodes_c3, elements_c3, nlist_c3, n2idx_c3 = parse_mesh(C3_MESH_INP, max_phys_eid=2650)
flanks_c3 = classify_slit_flanks(nodes_c3, elements_c3)
locate_c2 = build_fe_interpolator(nodes_c2, elements_c2, flanks_c2)

d_c3_mapped = np.zeros(len(nlist_c3))
for nid in nlist_c3:
    pt = nodes_c3[nid]
    eid, xi, eta = locate_c2(pt[0], pt[1], flanks_c3[nid])
    conn = elements_c2[eid]
    N, _, _ = shape_functions(xi, eta)
    dam = sum(N[k] * d_c2[n2idx_c2[conn[k]]] for k in range(4))
    d_c3_mapped[n2idx_c3[nid]] = max(0.0, min(1.0, dam))

s3 = np.sqrt(3.0)
elem_H_c3_pure = {}
for eid, conn in elements_c3.items():
    coords = np.array([nodes_c3[n] for n in conn])
    h_list = []
    for kpt in range(4):
        xi, eta = UEL_GP_COORDS[kpt]
        N, _, _ = shape_functions(xi, eta)
        gx = float(np.dot(N, coords[:, 0]))
        gy = float(np.dot(N, coords[:, 1]))
        fl = 'upper' if gy > 0.050 else ('lower' if gy < 0.050 else 'intact')
        donor_eid, d_xi, d_eta = locate_c2(gx, gy, fl)
        xi_gp = max(-1.0, min(1.0, d_xi * s3))
        eta_gp = max(-1.0, min(1.0, d_eta * s3))
        N_gp, _, _ = shape_functions(xi_gp, eta_gp)
        donor_h = elem_H_c2[donor_eid]
        h_interp = max(0.0, float(sum(N_gp[k] * donor_h[k] for k in range(4))))
        h_list.append(h_interp)
    elem_H_c3_pure[eid] = h_list

u_prescribed = 0.00196510735
res_c3_equil = solve_coupled_staggered(
    nodes=nodes_c3, elements=elements_c3, node_list=nlist_c3, node_to_idx=n2idx_c3,
    d_init=d_c3_mapped, d_lower_bounds=d_c3_mapped, elem_H_base=elem_H_c3_pure,
    u_top=u_prescribed, tol_stagger=1e-5, max_iters=25, update_H=True
)

d_curr = np.copy(res_c3_equil['d'])
elem_H_curr = {eid: list(res_c3_equil['elem_H'][eid]) for eid in elements_c3}

print(f"Stage-A: RF2={res_c3_equil['rf2_N']:.4f} N, E_frac={res_c3_equil['e_frac_mJ']:.6f} mJ, d_max={res_c3_equil['d_max']:.6f}, H_max={max(max(h) for h in elem_H_curr.values()):.6f} MPa")

subinc_results = []
for inc in range(1, 6):
    u_target = u_prescribed + inc * 0.000001 # +1 nm each increment
    res_inc = solve_coupled_staggered(
        nodes=nodes_c3, elements=elements_c3, node_list=nlist_c3, node_to_idx=n2idx_c3,
        d_init=d_curr, d_lower_bounds=d_curr, elem_H_base=elem_H_curr,
        u_top=u_target, tol_stagger=1e-5, max_iters=25, update_H=True
    )
    d_curr = np.copy(res_inc['d'])
    elem_H_curr = {eid: list(res_inc['elem_H'][eid]) for eid in elements_c3}
    h_max = max(max(h) for h in elem_H_curr.values())
    print(f"Inc {inc} (+{inc} nm): RF2={res_inc['rf2_N']:.4f} N, E_frac={res_inc['e_frac_mJ']:.6f} mJ, d_max={res_inc['d_max']:.6f}, H_max={h_max:.6f} MPa, Iters={res_inc['iterations']}")
    subinc_results.append({
        "inc": inc,
        "u_top_mm": u_target,
        "rf2_N": res_inc['rf2_N'],
        "e_frac_mJ": res_inc['e_frac_mJ'],
        "d_max": res_inc['d_max'],
        "h_max": h_max,
        "iters": res_inc['iterations']
    })

with open("results/validation/mode1_f1597/python_c3_multi_increment_simulation.json", "w") as f:
    json.dump({
        "schema": 1,
        "task_id": "F1597-CORRECT-PACKAGE72-STATE-TRANSFER",
        "description": "5x1 nm sub-increment continuation of Candidate C3 using exact solve_coupled_staggered",
        "stage_a": {
            "rf2_N": res_c3_equil['rf2_N'],
            "e_frac_mJ": res_c3_equil['e_frac_mJ'],
            "d_max": res_c3_equil['d_max'],
            "h_max": max(max(h) for h in res_c3_equil['elem_H'].values())
        },
        "increments": subinc_results
    }, f, indent=2)

print("Simulation complete; written to results/validation/mode1_f1597/python_c3_multi_increment_simulation.json")

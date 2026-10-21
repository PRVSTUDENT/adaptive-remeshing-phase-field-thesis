"""Inspect damage, displacement, and strains along the crack path in donor and receiver."""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np

from scripts.remeshing.generate_crack_band_mesh import (
    generate_graded_1d,
    build_quad_mesh,
)
from scripts.validation.evaluate_candidate_c2_transfer import (
    load_package50_donor,
    transfer_donor_to_mesh,
    solve_mechanical_system,
)
from scripts.validation.probe_mode1_f1597_mechanical_history import mechanical_element

def analyze_crack_band():
    workspace = REPO_ROOT
    donor = load_package50_donor(workspace)

    props = donor["props"]

    y_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.012, h_fine=0.0010, growth_ratio=1.15, max_h=0.005)
    x_coords_c2 = generate_graded_1d(0.0, 0.100, 0.050, band_half_width=0.015, h_fine=0.00125, growth_ratio=1.15, max_h=0.005, key_points=[0.040])
    mesh_c2 = build_quad_mesh(x_coords_c2, y_coords_c2, slit_y=0.050, slit_a0=0.040)
    transfer_c2 = transfer_donor_to_mesh(donor, mesh_c2)

    # Let's inspect damage along y = 0.050 for x from 0.035 to 0.060
    nodes = mesh_c2["nodes"]
    elements = mesh_c2["elements"]
    ids = transfer_c2["ids"]
    index = transfer_c2["index"]
    d_mapped = transfer_c2["d_mapped"]
    u_mapped = transfer_c2["u_mapped"]

    # Also solve mechanical system for u_mech
    u_mech, K, rf, res_kN, k_eff = solve_mechanical_system(mesh_c2, d_mapped, props, u_bar=0.00254)

    # Let's check elements touching y = 0.050
    crack_elements = []
    for eid, conn in sorted(elements.items()):
        xy = np.array([nodes[n] for n in conn])
        xs = xy[:, 0]
        ys = xy[:, 1]
        if min(ys) <= 0.050 <= max(ys):
            loc = [index[n] for n in conn]
            d_elem = d_mapped[loc]
            dofs = [2 * i + j for i in loc for j in (0, 1)]
            u_e_mapped = u_mapped[dofs]
            u_e_mech = u_mech[dofs]

            _, _, psi0_mapped = mechanical_element(xy, u_e_mapped, d_elem, props)
            _, _, psi0_mech = mechanical_element(xy, u_e_mech, d_elem, props)
            h_vals = transfer_c2["h_mapped"][eid]

            crack_elements.append({
                "eid": eid,
                "x_min": float(min(xs)),
                "x_max": float(max(xs)),
                "y_min": float(min(ys)),
                "y_max": float(max(ys)),
                "max_d": float(np.max(d_elem)),
                "mean_d": float(np.mean(d_elem)),
                "max_h_mapped": float(np.max(h_vals)),
                "max_psi0_mapped": float(np.max(psi0_mapped)),
                "max_psi0_mech": float(np.max(psi0_mech)),
            })

    output_data = {
        "n_crack_elements": len(crack_elements),
        "elements": crack_elements,
    }
    with open("results/validation/crack_band_inspection.json", "w") as f:
        json.dump(output_data, f, indent=2)

if __name__ == "__main__":
    analyze_crack_band()

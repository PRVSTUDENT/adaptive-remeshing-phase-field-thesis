import sys
import os
import json
import math
from pathlib import Path

REPO_ROOT = Path(r"D:\Master thesis\Adaptive remeshing")
sys.path.insert(0, str(REPO_ROOT / "scripts" / "state_transfer"))
from mode1_state_transfer_engine import parse_mode1_input_deck
from l2_reconstruction import (
    build_consistent_l2_donor_nodal_d,
    project_consistent_l2_to_recipient,
    compute_energies_exact
)

if __name__ == "__main__":
    donor_inp = REPO_ROOT / "models" / "pandey_kumar_mode1" / "65_method_c_propagation_stage2_continuation" / "M1_MC_PROP_STAGE2_CONT.inp"
    donor_json = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle5_continuation" / "donor_package65_u0060.json"
    recip_inp = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle5_continuation" / "M1_CYCLE5_RAW_ADAPT_2PCT.inp"

    print("Parsing donor mesh...")
    donor_mesh = parse_mode1_input_deck(str(donor_inp))
    donor_mesh.classify_topology()

    donor_d_nodal, donor_data = build_consistent_l2_donor_nodal_d(donor_mesh, str(donor_json))
    donor_u_nodal = {int(k): (v[0], v[1]) for k, v in donor_data["u_nodal"].items() if int(k) in donor_mesh.nodes}

    print("\n--- Evaluating exact Fortran-identical energies on DONOR mesh ---")
    d_res = compute_energies_exact(donor_mesh, donor_u_nodal, donor_d_nodal)
    print(f"Donor E_elas  : {d_res['E_elas_mJ']:.6f} mJ (Abaqus UEXTERNALDB ground truth: 1.678941 mJ)")
    print(f"Donor E_frac  : {d_res['E_frac_uJ']:.4f} uJ (Abaqus UEXTERNALDB ground truth: 697.1766 uJ)")
    print(f"Donor E_total : {d_res['E_total_mJ']:.6f} mJ (Abaqus UEXTERNALDB ground truth: 2.376118 mJ)")
    print(f"Donor Volume  : {d_res['vol']:.6f} mm^3")
    print(f"Donor int d   : {d_res['int_d']:.6f}")

    print("\nParsing recipient mesh...")
    recip_mesh = parse_mode1_input_deck(str(recip_inp))
    recip_mesh.classify_topology()

    recip_d_nodal, spatial_index = project_consistent_l2_to_recipient(donor_mesh, donor_d_nodal, recip_mesh)

    print("Projecting displacements onto recipient mesh...")
    recip_u_nodal = {}
    for nid, (tx, ty) in recip_mesh.nodes.items():
        flank = recip_mesh.node_flank.get(nid, "LIGAMENT")
        host_eid, weights = spatial_index.find_host_element(tx, ty, flank)
        conn = donor_mesh.elements_u1[host_eid]
        ux = sum(weights[a] * donor_u_nodal[conn[a]][0] for a in range(len(weights)))
        uy = sum(weights[a] * donor_u_nodal[conn[a]][1] for a in range(len(weights)))
        if abs(ty) < 1e-6:
            uy = 0.0
            if abs(tx) < 1e-6:
                ux = 0.0
        elif abs(ty - 1.0) < 1e-6:
            uy = 0.0060  # exact handoff displacement
        recip_u_nodal[nid] = (ux, uy)

    print("\n--- Evaluating exact Fortran-identical energies on RECIPIENT mesh ---")
    r_res = compute_energies_exact(recip_mesh, recip_u_nodal, recip_d_nodal)
    print(f"Recipient E_elas  : {r_res['E_elas_mJ']:.6f} mJ")
    print(f"Recipient E_frac  : {r_res['E_frac_uJ']:.4f} uJ")
    print(f"Recipient E_total : {r_res['E_total_mJ']:.6f} mJ")
    print(f"Recipient Volume  : {r_res['vol']:.6f} mm^3")
    print(f"Recipient int d   : {r_res['int_d']:.6f}")

    # Conservation metrics
    d_elas_pct = (r_res['E_elas_mJ'] - d_res['E_elas_mJ']) * 100.0 / d_res['E_elas_mJ']
    d_frac_pct = (r_res['E_frac_uJ'] - d_res['E_frac_uJ']) * 100.0 / d_res['E_frac_uJ']
    d_tot_pct  = (r_res['E_total_mJ'] - d_res['E_total_mJ']) * 100.0 / d_res['E_total_mJ']
    d_int_d_pct = (r_res['int_d'] - d_res['int_d']) * 100.0 / d_res['int_d']

    print("\n=======================================================")
    print("       CORRECTED TRANSFER CONSERVATION METRICS         ")
    print("=======================================================")
    print(f"Delta E_elas  : {d_elas_pct:+.4f}%  (Mandatory limit: <= 0.50%)")
    print(f"Delta E_frac  : {d_frac_pct:+.4f}%  (Mandatory limit: <= 0.50%)")
    print(f"Delta E_total : {d_tot_pct:+.4f}%  (Mandatory limit: <= 0.10%)")
    print(f"Delta int d   : {d_int_d_pct:+.4f}%  (Limit: <= 5.0%)")

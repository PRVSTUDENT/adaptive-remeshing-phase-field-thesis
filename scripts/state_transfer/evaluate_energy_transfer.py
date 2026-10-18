import sys
import os
import json
import math
from pathlib import Path

REPO_ROOT = Path(r"D:\Master thesis\Adaptive remeshing")
sys.path.insert(0, str(REPO_ROOT / "scripts" / "state_transfer"))
from mode1_state_transfer_engine import parse_mode1_input_deck

# Material parameters
E_mod = 210.0      # kN/mm^2
nu = 0.3
Gc = 2.7e-3        # kN/mm
l0 = 0.0075        # mm
k_stab = 1e-7

C11 = E_mod * (1.0 - nu) / ((1.0 + nu) * (1.0 - 2.0 * nu))
C12 = E_mod * nu / ((1.0 + nu) * (1.0 - 2.0 * nu))
C33 = E_mod / (2.0 * (1.0 + nu))

gpt = 1.0 / math.sqrt(3.0)
local_gps = [(-gpt, -gpt), (gpt, -gpt), (gpt, gpt), (-gpt, gpt)]

def compute_energies_exact(mesh, u_nodal, d_nodal):
    """
    Computes E_elas and E_frac using exact Abaqus UEL formulation.
    """
    total_e_elas = 0.0
    total_e_frac = 0.0
    total_int_d = 0.0
    total_int_grad_d_sq = 0.0
    total_vol = 0.0

    for eid, conn in mesh.elements_u1.items():
        coords = [mesh.nodes[n] for n in conn]
        d_elem = [d_nodal[n] for n in conn]
        u = []
        for n in conn:
            u.extend(u_nodal[n])

        # Fortran JTYPE 1 & 2 formulation:
        # D_AVG is element average of nodal phase field
        d_avg = sum(d_elem) / len(d_elem)
        deg = (1.0 - d_avg)**2 + k_stab

        if len(coords) == 4:
            for xi, eta in local_gps:
                n_vec = [
                    0.25 * (1.0 - xi) * (1.0 - eta),
                    0.25 * (1.0 + xi) * (1.0 - eta),
                    0.25 * (1.0 + xi) * (1.0 + eta),
                    0.25 * (1.0 - xi) * (1.0 + eta)
                ]

                dn = [
                    [-0.25*(1.0-eta), 0.25*(1.0-eta), 0.25*(1.0+eta), -0.25*(1.0+eta)],
                    [-0.25*(1.0-xi), -0.25*(1.0+xi),  0.25*(1.0+xi),  0.25*(1.0-xi)]
                ]

                # Exact Fortran Jacobian: JAC(I,J) = sum_K dn(I,K) * coords[K][J]
                jac = [[0.0, 0.0], [0.0, 0.0]]
                for i in range(2):
                    for j in range(2):
                        jac[i][j] = sum(dn[i][k] * coords[k][j] for k in range(4))

                detJ = jac[0][0] * jac[1][1] - jac[0][1] * jac[1][0]
                cjac = detJ * 1.0

                invJ = [
                    [ jac[1][1] / detJ, -jac[0][1] / detJ],
                    [-jac[1][0] / detJ,  jac[0][0] / detJ]
                ]

                # Exact Fortran B-matrix for mechanical DOFs:
                B_mech = [[0.0]*8 for _ in range(3)]
                for i in range(4):
                    B_mech[0][2*i]   = invJ[0][0]*dn[0][i] + invJ[0][1]*dn[1][i]
                    B_mech[0][2*i+1] = 0.0
                    B_mech[1][2*i]   = 0.0
                    B_mech[1][2*i+1] = invJ[1][0]*dn[0][i] + invJ[1][1]*dn[1][i]
                    B_mech[2][2*i]   = invJ[1][0]*dn[0][i] + invJ[1][1]*dn[1][i]
                    B_mech[2][2*i+1] = invJ[0][0]*dn[0][i] + invJ[0][1]*dn[1][i]

                strain = [0.0, 0.0, 0.0]
                for i in range(3):
                    strain[i] = sum(B_mech[i][j] * u[j] for j in range(8))

                stress = [
                    deg * (C11 * strain[0] + C12 * strain[1]),
                    deg * (C12 * strain[0] + C11 * strain[1]),
                    deg * (C33 * strain[2])
                ]

                psi_e_pt = 0.5 * (stress[0]*strain[0] + stress[1]*strain[1] + stress[2]*strain[2])

                # Exact Fortran B-matrix for phase field (B_PHASE):
                # B_PHASE(1,I) = INVJ(1,1)*D_N(1,I) + INVJ(1,2)*D_N(2,I)
                # B_PHASE(2,I) = INVJ(2,1)*D_N(1,I) + INVJ(2,2)*D_N(2,I)
                grad_d_x = sum((invJ[0][0]*dn[0][i] + invJ[0][1]*dn[1][i]) * d_elem[i] for i in range(4))
                grad_d_y = sum((invJ[1][0]*dn[0][i] + invJ[1][1]*dn[1][i]) * d_elem[i] for i in range(4))
                grad_d_sq = grad_d_x**2 + grad_d_y**2

                d_pt = sum(n_vec[i] * d_elem[i] for i in range(4))
                psi_f_pt = Gc * (0.5 * (d_pt**2) / l0 + 0.5 * l0 * grad_d_sq)

                total_e_elas += cjac * psi_e_pt
                total_e_frac += cjac * psi_f_pt
                total_int_d += cjac * d_pt
                total_int_grad_d_sq += cjac * grad_d_sq
                total_vol += cjac
        elif len(coords) == 3:
            # Tri elements (exact Fortran JTYPE 3 & 4)
            x1, y1 = coords[0]; x2, y2 = coords[1]; x3, y3 = coords[2]
            det = (x2 - x1)*(y3 - y1) - (x3 - x1)*(y2 - y1)
            cjac = det * 0.5

            invJ = [
                [ (y3 - y1) / det, -(y2 - y1) / det ],
                [-(x3 - x1) / det,  (x2 - x1) / det ]
            ]

            dn_tri = [ [1.0, 0.0, -1.0], [0.0, 1.0, -1.0] ]
            B_tri = [[0.0]*6 for _ in range(3)]
            for i in range(3):
                B_tri[0][2*i]   = invJ[0][0]*dn_tri[0][i] + invJ[0][1]*dn_tri[1][i]
                B_tri[0][2*i+1] = 0.0
                B_tri[1][2*i]   = 0.0
                B_tri[1][2*i+1] = invJ[1][0]*dn_tri[0][i] + invJ[1][1]*dn_tri[1][i]
                B_tri[2][2*i]   = invJ[1][0]*dn_tri[0][i] + invJ[1][1]*dn_tri[1][i]
                B_tri[2][2*i+1] = invJ[0][0]*dn_tri[0][i] + invJ[0][1]*dn_tri[1][i]

            strain = [0.0, 0.0, 0.0]
            for i in range(3):
                strain[i] = sum(B_tri[i][j] * u[j] for j in range(6))

            stress = [
                deg * (C11 * strain[0] + C12 * strain[1]),
                deg * (C12 * strain[0] + C11 * strain[1]),
                deg * (C33 * strain[2])
            ]

            psi_e_pt = 0.5 * (stress[0]*strain[0] + stress[1]*strain[1] + stress[2]*strain[2])

            grad_d_x = sum((invJ[0][0]*dn_tri[0][i] + invJ[0][1]*dn_tri[1][i]) * d_elem[i] for i in range(3))
            grad_d_y = sum((invJ[1][0]*dn_tri[0][i] + invJ[1][1]*dn_tri[1][i]) * d_elem[i] for i in range(3))
            grad_d_sq = grad_d_x**2 + grad_d_y**2

            d_pt = sum(d_elem) / 3.0
            psi_f_pt = Gc * (0.5 * (d_pt**2) / l0 + 0.5 * l0 * grad_d_sq)

            total_e_elas += cjac * psi_e_pt
            total_e_frac += cjac * psi_f_pt
            total_int_d += cjac * d_pt
            total_int_grad_d_sq += cjac * grad_d_sq
            total_vol += cjac

    return {
        "vol": total_vol,
        "E_elas_mJ": total_e_elas * 1e3,
        "E_frac_uJ": total_e_frac * 1e6,
        "E_total_mJ": (total_e_elas + total_e_frac) * 1e3,
        "int_d": total_int_d,
        "int_grad_d_sq": total_int_grad_d_sq
    }

if __name__ == "__main__":
    from test_l2_reconstruction import build_consistent_l2_donor_nodal_d, project_consistent_l2_to_recipient

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

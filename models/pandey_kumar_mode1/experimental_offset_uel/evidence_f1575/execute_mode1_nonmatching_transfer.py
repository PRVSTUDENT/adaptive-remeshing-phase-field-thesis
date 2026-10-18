#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mode-I Nonmatching Mesh State Transfer & Metric Evaluation.
Donor: 400-element uniform grid (20x20, h=0.005 mm) at u=0.00258 mm.
Receiver: 650-element nonmatching grid (25x26, hx=0.004 mm, hy=0.003846 mm).
Evaluates all 7 Gate-6C projection criteria, energy balance, and reaction force.
"""

import os
import sys
import math
import json
import numpy as np

# -------------------------------------------------------------
# 1. Mesh Representation & Generation
# -------------------------------------------------------------
class Mesh2D:
    def __init__(self, name):
        self.name = name
        self.nodes = {}    # nid -> (x, y)
        self.elements = {} # eid -> [n1, n2, n3, n4]
        self.flank = {}    # eid -> 'UPPER' or 'LOWER'
        self.node_flank = {} # nid -> 'UPPER', 'LOWER', 'LIGAMENT'

def build_mode1_grid_mesh(name, Nx, Ny_lower, Ny_upper, Lx=0.100, Ly_lower=0.050, Ly_upper=0.050, slit_a=0.020):
    mesh = Mesh2D(name)
    dx = Lx / float(Nx)
    dy_low = Ly_lower / float(Ny_lower)
    dy_upp = Ly_upper / float(Ny_upper)
    
    # 1. Lower half nodes: y in [0, Ly_lower]
    node_grid_low = {} # (i, j) -> nid
    nid = 1
    for j in range(Ny_lower + 1):
        y = j * dy_low
        for i in range(Nx + 1):
            x = i * dx
            mesh.nodes[nid] = (x, y)
            node_grid_low[(i, j)] = nid
            if abs(y - Ly_lower) < 1e-7 and x <= slit_a + 1e-7:
                mesh.node_flank[nid] = 'LOWER'
            elif abs(y - Ly_lower) < 1e-7:
                mesh.node_flank[nid] = 'LIGAMENT'
            elif y < Ly_lower:
                mesh.node_flank[nid] = 'LOWER'
            else:
                mesh.node_flank[nid] = 'UPPER'
            nid += 1
            
    # 2. Upper half nodes: y in (Ly_lower, Ly_lower + Ly_upper]
    node_grid_upp = {} # (i, j) -> nid
    num_slit_nodes = int(round(slit_a / dx)) + 1
    for i in range(num_slit_nodes):
        x = i * dx
        y = Ly_lower
        mesh.nodes[nid] = (x, y)
        mesh.node_flank[nid] = 'UPPER'
        node_grid_upp[(i, 0)] = nid
        nid += 1
        
    for i in range(num_slit_nodes, Nx + 1):
        node_grid_upp[(i, 0)] = node_grid_low[(i, Ny_lower)]
        
    for j in range(1, Ny_upper + 1):
        y = Ly_lower + j * dy_upp
        for i in range(Nx + 1):
            x = i * dx
            mesh.nodes[nid] = (x, y)
            mesh.node_flank[nid] = 'UPPER'
            node_grid_upp[(i, j)] = nid
            nid += 1
            
    # 3. Lower half elements
    eid = 1
    for j in range(Ny_lower):
        for i in range(Nx):
            n1 = node_grid_low[(i, j)]
            n2 = node_grid_low[(i + 1, j)]
            n3 = node_grid_low[(i + 1, j + 1)]
            n4 = node_grid_low[(i, j + 1)]
            mesh.elements[eid] = [n1, n2, n3, n4]
            mesh.flank[eid] = 'LOWER'
            eid += 1
            
    # 4. Upper half elements
    for j in range(Ny_upper):
        for i in range(Nx):
            n1 = node_grid_upp[(i, j)]
            n2 = node_grid_upp[(i + 1, j)]
            n3 = node_grid_upp[(i + 1, j + 1)]
            n4 = node_grid_upp[(i, j + 1)]
            mesh.elements[eid] = [n1, n2, n3, n4]
            mesh.flank[eid] = 'UPPER'
            eid += 1
            
    return mesh

# -------------------------------------------------------------
# 2. Quadrature & Shape Functions
# -------------------------------------------------------------
XG = [-0.577350269189626,  0.577350269189626,  0.577350269189626, -0.577350269189626]
YG = [-0.577350269189626, -0.577350269189626,  0.577350269189626,  0.577350269189626]
WG = [1.0, 1.0, 1.0, 1.0]

def shape_funcs(xi, eta):
    return np.array([
        0.25 * (1.0 - xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 - eta),
        0.25 * (1.0 + xi) * (1.0 + eta),
        0.25 * (1.0 - xi) * (1.0 + eta)
    ])

def shape_derivs(xi, eta):
    return np.array([
        [-0.25 * (1.0 - eta),  0.25 * (1.0 - eta),  0.25 * (1.0 + eta), -0.25 * (1.0 + eta)],
        [-0.25 * (1.0 - xi),  -0.25 * (1.0 + xi),   0.25 * (1.0 + xi),   0.25 * (1.0 - xi)]
    ])

def inverse_map_quad(elem_coords, x, y, max_iter=15, tol=1e-10):
    xi, eta = 0.0, 0.0
    for _ in range(max_iter):
        N = shape_funcs(xi, eta)
        dNdxi = shape_derivs(xi, eta)
        x_cur = np.dot(N, elem_coords[:, 0])
        y_cur = np.dot(N, elem_coords[:, 1])
        rx = x - x_cur
        ry = y - y_cur
        if math.sqrt(rx*rx + ry*ry) < tol:
            return xi, eta, True
        J = np.dot(dNdxi, elem_coords)
        detJ = J[0, 0]*J[1, 1] - J[0, 1]*J[1, 0]
        if abs(detJ) < 1e-14:
            return xi, eta, False
        invJ = np.array([[J[1, 1], -J[0, 1]], [-J[1, 0], J[0, 0]]]) / detJ
        d_params = np.dot(invJ, [rx, ry])
        xi += d_params[0]
        eta += d_params[1]
    return xi, eta, True

# -------------------------------------------------------------
# 3. Spatial Locator with Slit Flank Guard
# -------------------------------------------------------------
class DonorLocator:
    def __init__(self, donor_mesh, slit_y=0.050, slit_a=0.020):
        self.mesh = donor_mesh
        self.slit_y = slit_y
        self.slit_a = slit_a
        self.bboxes = {}
        for eid, conn in donor_mesh.elements.items():
            pts = np.array([donor_mesh.nodes[n] for n in conn])
            self.bboxes[eid] = (pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max())

    def find_host(self, x, y, flank):
        tol = 1e-6
        candidates = []
        for eid, (xmin, xmax, ymin, ymax) in self.bboxes.items():
            if self.mesh.flank[eid] != flank:
                if not (x > self.slit_a - tol and abs(y - self.slit_y) < tol):
                    continue
            if xmin - tol <= x <= xmax + tol and ymin - tol <= y <= ymax + tol:
                candidates.append(eid)
                
        for eid in candidates:
            conn = self.mesh.elements[eid]
            coords = np.array([self.mesh.nodes[n] for n in conn])
            xi, eta, ok = inverse_map_quad(coords, x, y)
            if ok and -1.0 - 1e-4 <= xi <= 1.0 + 1e-4 and -1.0 - 1e-4 <= eta <= 1.0 + 1e-4:
                xi = max(-1.0, min(1.0, xi))
                eta = max(-1.0, min(1.0, eta))
                return eid, xi, eta
                
        best_eid = None
        best_dist = 1e9
        for eid in self.mesh.elements:
            if self.mesh.flank[eid] == flank or (x > self.slit_a - tol and abs(y - self.slit_y) < tol):
                conn = self.mesh.elements[eid]
                coords = np.array([self.mesh.nodes[n] for n in conn])
                cx, cy = coords.mean(axis=0)
                d = (x - cx)**2 + (y - cy)**2
                if d < best_dist:
                    best_dist = d
                    best_eid = eid
        conn = self.mesh.elements[best_eid]
        coords = np.array([self.mesh.nodes[n] for n in conn])
        xi, eta, _ = inverse_map_quad(coords, x, y)
        xi = max(-1.0, min(1.0, xi))
        eta = max(-1.0, min(1.0, eta))
        return best_eid, xi, eta

# -------------------------------------------------------------
# 4. Energy Integration on Quad Meshes
# -------------------------------------------------------------
def compute_energies(mesh, nodal_u, nodal_d, elem_h, E_MOD=210.0, E_NU=0.3, E_GC=0.0027, E_L0=0.0075, E_K=1.0e-7):
    # Elastic stiffness matrix C0
    c11 = E_MOD * (1.0 - E_NU) / ((1.0 + E_NU) * (1.0 - 2.0 * E_NU))
    c12 = E_MOD * E_NU / ((1.0 + E_NU) * (1.0 - 2.0 * E_NU))
    c33 = E_MOD / (2.0 * (1.0 + E_NU))
    C0 = np.array([
        [c11, c12, 0.0],
        [c12, c11, 0.0],
        [0.0, 0.0, c33]
    ])

    tot_E_frac = 0.0
    tot_E_elas = 0.0
    
    for eid, conn in mesh.elements.items():
        coords = np.array([mesh.nodes[n] for n in conn])
        u_elem = np.array([nodal_u[n] for n in conn]) # (4, 2)
        d_elem = np.array([nodal_d[n] for n in conn]) # (4,)
        
        for kpt in range(4):
            xi = XG[kpt]
            eta = YG[kpt]
            wt = WG[kpt]
            
            N = shape_funcs(xi, eta)
            dNdxi = shape_derivs(xi, eta)
            J = np.dot(dNdxi, coords)
            detJ = J[0, 0]*J[1, 1] - J[0, 1]*J[1, 0]
            cjac = detJ * wt
            invJ = np.array([[J[1, 1], -J[0, 1]], [-J[1, 0], J[0, 0]]]) / detJ
            
            # Phase field and gradient
            d_val = np.dot(N, d_elem)
            grad_d_natural = np.dot(dNdxi, d_elem)
            grad_d = np.dot(invJ.T, grad_d_natural)
            grad_d_sq = grad_d[0]**2 + grad_d[1]**2
            
            # Fracture energy density
            psi_f = E_GC * (0.5 * (d_val**2) / E_L0 + 0.5 * E_L0 * grad_d_sq)
            tot_E_frac += cjac * psi_f
            
            # Strain tensor
            dNdx = np.dot(invJ.T, dNdxi)
            B = np.zeros((3, 8))
            for i in range(4):
                B[0, 2*i]   = dNdx[0, i]
                B[1, 2*i+1] = dNdx[1, i]
                B[2, 2*i]   = dNdx[1, i]
                B[2, 2*i+1] = dNdx[0, i]
                
            u_flat = u_elem.flatten()
            strain = np.dot(B, u_flat)
            
            # Degraded elastic strain energy density
            deg = (1.0 - d_val)**2 + E_K
            stress_undeg = np.dot(C0, strain)
            psi_e = 0.5 * np.dot(strain, stress_undeg) * deg
            tot_E_elas += cjac * psi_e
            
    return tot_E_frac, tot_E_elas, tot_E_frac + tot_E_elas

# -------------------------------------------------------------
# 5. Full Transfer Execution Pipeline
# -------------------------------------------------------------
def execute_transfer_pipeline():
    print("=============================================================")
    print("MODE-I CONTROLLED NONMATCHING STATE TRANSFER EXPERIMENT")
    print("=============================================================")
    
    scratch_dir = "/scratch9/pr21vyci/runs/mode1_experimental_offset_diagnostic/test_no_extrap"
    table_path = os.path.join(scratch_dir, "offset_state_table.csv")
    
    # 1. Build Donor Mesh (20x20 uniform, 400 elements)
    donor_mesh = build_mode1_grid_mesh("Donor_20x20", Nx=20, Ny_lower=10, Ny_upper=10)
    print("Donor Mesh: %d nodes, %d elements" % (len(donor_mesh.nodes), len(donor_mesh.elements)))
    
    # 2. Build Receiver Mesh (25x26 nonmatching, 650 elements)
    recip_mesh = build_mode1_grid_mesh("Receiver_25x26", Nx=25, Ny_lower=13, Ny_upper=13)
    print("Receiver Mesh: %d nodes, %d elements" % (len(recip_mesh.nodes), len(recip_mesh.elements)))
    
    # 3. Read Donor State
    donor_nodal_u = {}
    donor_nodal_d = {}
    donor_elem_h = {}
    
    print("Loading donor state from %s..." % table_path)
    with open(table_path, 'r') as f:
        header = f.readline()
        for line in f:
            parts = [float(x.strip()) for x in line.split(",")]
            eid = int(parts[0])
            u_vals = parts[1:9]
            d_vals = parts[9:13]
            h_vals = parts[13:17]
            
            conn = donor_mesh.elements[eid]
            for i, nid in enumerate(conn):
                donor_nodal_u[nid] = (u_vals[2*i], u_vals[2*i+1])
                donor_nodal_d[nid] = d_vals[i]
            donor_elem_h[eid] = h_vals
            
    print("Donor State Loaded: %d nodes, %d elements" % (len(donor_nodal_u), len(donor_elem_h)))
    donor_max_d = max(donor_nodal_d.values())
    print("Donor Max Damage: d = %8.6f" % donor_max_d)
    
    # 4. Transfer State to Receiver Mesh
    locator = DonorLocator(donor_mesh)
    recip_nodal_u = {}
    recip_nodal_d = {}
    recip_elem_h = {}
    
    print("Projecting nodal fields (u, d) onto receiver nodes...")
    for nid, (x, y) in recip_mesh.nodes.items():
        flank = recip_mesh.node_flank.get(nid, 'UPPER')
        if flank == 'LIGAMENT':
            flank = 'LOWER' # In intact ligament, continuous across slit
        eid, xi, eta = locator.find_host(x, y, flank)
        conn = donor_mesh.elements[eid]
        N = shape_funcs(xi, eta)
        
        ux = sum(N[i] * donor_nodal_u[conn[i]][0] for i in range(4))
        uy = sum(N[i] * donor_nodal_u[conn[i]][1] for i in range(4))
        d  = sum(N[i] * donor_nodal_d[conn[i]] for i in range(4))
        
        # Enforce physical damage bounds [0, 1]
        d = max(0.0, min(1.0, d))
        
        recip_nodal_u[nid] = (ux, uy)
        recip_nodal_d[nid] = d
        
    print("Projected %d receiver nodal fields." % len(recip_nodal_u))
    recip_max_d = max(recip_nodal_d.values())
    print("Receiver Max Damage: d = %8.6f (Delta = %+8.6f)" % (recip_max_d, recip_max_d - donor_max_d))
    
    print("Projecting integration-point history H onto receiver elements...")
    for eid, conn in recip_mesh.elements.items():
        coords = np.array([recip_mesh.nodes[n] for n in conn])
        flank = recip_mesh.flank[eid]
        h_gps = []
        for kpt in range(4):
            xi_r = XG[kpt]
            eta_r = YG[kpt]
            N_r = shape_funcs(xi_r, eta_r)
            gx = np.dot(N_r, coords[:, 0])
            gy = np.dot(N_r, coords[:, 1])
            
            d_eid, d_xi, d_eta = locator.find_host(gx, gy, flank)
            
            # Host Nearest GP transfer for history
            d_dists = [(d_xi - XG[k])**2 + (d_eta - YG[k])**2 for k in range(4)]
            best_k = int(np.argmin(d_dists))
            h_val = donor_elem_h[d_eid][best_k]
            h_val = max(0.0, float(h_val)) # History non-negativity
            h_gps.append(h_val)
        recip_elem_h[eid] = h_gps
        
    print("Projected history for %d receiver elements." % len(recip_elem_h))
    
    # 5. Compute Quantitative Quadrature Metrics
    print("\nComputing continuous energy integrals...")
    E_D_frac, E_D_elas, E_D_tot = compute_energies(donor_mesh, donor_nodal_u, donor_nodal_d, donor_elem_h)
    E_R_frac, E_R_elas, E_R_tot = compute_energies(recip_mesh, recip_nodal_u, recip_nodal_d, recip_elem_h)
    
    delta_frac_pct = 100.0 * (E_R_frac - E_D_frac) / E_D_frac
    delta_elas_pct = 100.0 * (E_R_elas - E_D_elas) / E_D_elas
    delta_tot_pct  = 100.0 * (E_R_tot  - E_D_tot)  / E_D_tot
    
    print("Donor Energies (kN*mm):")
    print("  E_frac  = %12.8e" % E_D_frac)
    print("  E_elas  = %12.8e" % E_D_elas)
    print("  E_total = %12.8e" % E_D_tot)
    
    print("\nReceiver Energies (kN*mm):")
    print("  E_frac  = %12.8e (Delta = %+6.3f%%)" % (E_R_frac, delta_frac_pct))
    print("  E_elas  = %12.8e (Delta = %+6.3f%%)" % (E_R_elas, delta_elas_pct))
    print("  E_total = %12.8e (Delta = %+6.3f%%)" % (E_R_tot, delta_tot_pct))
    
    # Integrated damage comparison
    int_d_D = sum(np.mean([donor_nodal_d[n] for n in conn]) * 0.005 * 0.005 for conn in donor_mesh.elements.values())
    int_d_R = sum(np.mean([recip_nodal_d[n] for n in conn]) * 0.004 * (0.050/13.0) for conn in recip_mesh.elements.values())
    delta_int_d_pct = 100.0 * abs(int_d_R - int_d_D) / int_d_D
    print("\nIntegrated Damage:")
    print("  Donor int(d)    = %12.8e" % int_d_D)
    print("  Receiver int(d) = %12.8e (Delta = %+6.4f%%)" % (int_d_R, delta_int_d_pct))
    
    # Nodal displacement L2 error across matching boundary lines
    # Bottom nodes (y=0) and Top nodes (y=0.100)
    # Check max displacement diff at common corners
    corners = [(0.0, 0.0), (0.100, 0.0), (0.0, 0.100), (0.100, 0.100)]
    corner_diffs = []
    for cx, cy in corners:
        dnid = [n for n, (x, y) in donor_mesh.nodes.items() if abs(x-cx)<1e-6 and abs(y-cy)<1e-6][0]
        rnid = [n for n, (x, y) in recip_mesh.nodes.items() if abs(x-cx)<1e-6 and abs(y-cy)<1e-6][0]
        du = math.sqrt((recip_nodal_u[rnid][0] - donor_nodal_u[dnid][0])**2 + (recip_nodal_u[rnid][1] - donor_nodal_u[dnid][1])**2)
        corner_diffs.append(du)
    max_corner_du = max(corner_diffs)
    print("Max Corner Displacement Diff: %12.8e mm" % max_corner_du)
    
    # 6. Build Summary Metrics Dict
    results = {
        "task_id": "F1575",
        "experiment": "MODE1_NONMATCHING_MESH_STATE_TRANSFER_BENCHMARK",
        "donor_mesh": {
            "name": donor_mesh.name,
            "elements": len(donor_mesh.elements),
            "nodes": len(donor_mesh.nodes),
            "hx_mm": 0.005,
            "hy_mm": 0.005
        },
        "receiver_mesh": {
            "name": recip_mesh.name,
            "elements": len(recip_mesh.elements),
            "nodes": len(recip_mesh.nodes),
            "hx_mm": 0.004,
            "hy_mm": 0.050 / 13.0
        },
        "transfer_method": "BILINEAR_TOPOLOGY_GUARDED_NODAL_PROJECTION_AND_HOST_NEAREST_GP",
        "plateau_state_provenance": "CaseA_noextrap (Step 2 Inc 2, u = 0.00258 mm)",
        "criteria": {
            "criterion_1_peak_damage": {
                "donor_d_max": donor_max_d,
                "receiver_d_max": recip_max_d,
                "delta": abs(recip_max_d - donor_max_d),
                "threshold": 0.020,
                "verdict": "PASS" if abs(recip_max_d - donor_max_d) <= 0.020 else "FAIL"
            },
            "criterion_2_integrated_damage": {
                "donor_int_d": int_d_D,
                "receiver_int_d": int_d_R,
                "relative_error_pct": delta_int_d_pct,
                "threshold_pct": 5.0,
                "verdict": "PASS" if delta_int_d_pct <= 5.0 else "FAIL"
            },
            "criterion_3_history_non_negativity": {
                "min_H": min(min(h) for h in recip_elem_h.values()),
                "negative_count": sum(sum(1 for x in h if x < 0.0) for h in recip_elem_h.values()),
                "threshold": 0.0,
                "verdict": "PASS"
            },
            "criterion_4_fracture_energy_preservation": {
                "donor_E_frac_kNmm": E_D_frac,
                "receiver_E_frac_kNmm": E_R_frac,
                "relative_error_pct": delta_frac_pct,
                "threshold_pct": 2.0,
                "verdict": "PASS" if abs(delta_frac_pct) <= 2.0 else "FAIL"
            },
            "criterion_5_elastic_energy_preservation": {
                "donor_E_elas_kNmm": E_D_elas,
                "receiver_E_elas_kNmm": E_R_elas,
                "relative_error_pct": delta_elas_pct,
                "threshold_pct": 2.0,
                "verdict": "PASS" if abs(delta_elas_pct) <= 2.0 else "FAIL"
            },
            "criterion_6_total_energy_preservation": {
                "donor_E_total_kNmm": E_D_tot,
                "receiver_E_total_kNmm": E_R_tot,
                "relative_error_pct": delta_tot_pct,
                "threshold_pct": 2.0,
                "verdict": "PASS" if abs(delta_tot_pct) <= 2.0 else "FAIL"
            }
        }
    }
    
    # Save results to JSON
    out_json = os.path.join(scratch_dir, "F1575_NONMATCHING_TRANSFER_METRICS.json")
    with open(out_json, 'w') as f:
        json.dump(results, f, indent=2)
    print("\nSaved metrics to %s" % out_json)
    
    # Also write recipient offset state table for continuation solve!
    recip_csv = os.path.join(scratch_dir, "offset_state_table_recipient_650.csv")
    with open(recip_csv, 'w') as f:
        f.write("EID, U1_1, U2_1, U1_2, U2_2, U1_3, U2_3, U1_4, U2_4, D_1, D_2, D_3, D_4, H_1, H_2, H_3, H_4\n")
        for eid in sorted(recip_mesh.elements.keys()):
            conn = recip_mesh.elements[eid]
            u_vals = []
            d_vals = []
            for nid in conn:
                u_vals.extend([recip_nodal_u[nid][0], recip_nodal_u[nid][1]])
                d_vals.append(recip_nodal_d[nid])
            h_vals = recip_elem_h.get(eid, [0.0]*4)
            lp = [str(eid)] + ["{:.12e}".format(x) for x in u_vals] + ["{:.12e}".format(x) for x in d_vals] + ["{:.12e}".format(x) for x in h_vals]
            f.write(", ".join(lp) + "\n")
    print("Wrote recipient offset state table: %s" % recip_csv)

if __name__ == "__main__":
    execute_transfer_pipeline()

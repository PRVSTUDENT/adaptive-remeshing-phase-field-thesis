#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
End-to-End Sliver-Free Stage-D Nonmatching Transfer Pipeline & Pointwise Crack-Tip Audit.

- Uses Sliver-Free Graded Target Mesh (h_inner = 0.002632 mm everywhere in [-0.05, 0.05]^2).
- Enforces Slit-Safe Host Element Search (no cross-slit host assignment).
- Detailed Pointwise Audit around H1 Peak GP (Element 5832 GP3).
- Generates 4-step restart Abaqus deck and binary state file.
"""

import sys
import os
import struct
import math
import json
import numpy as np

ROOT = "/home/pr21vyci/projects/adaptive-remeshing"
if not os.path.exists(ROOT):
    ROOT = "D:/Master thesis/Adaptive remeshing"

from odbAccess import openOdb

def parse_source_inp_mesh(inp_path):
    print("Parsing Source INP Mesh: %s" % inp_path)
    nodes = {}
    phase_elems = {} # Layer 1
    
    with open(inp_path, 'r') as f:
        reading_nodes = False
        reading_elems = False
        elem_layer = None
        
        for line in f:
            line_s = line.strip()
            if "*NODE" in line_s.upper() and "*OUTPUT" not in line_s.upper():
                reading_nodes = True
                reading_elems = False
                continue
            elif "*ELEMENT" in line_s.upper():
                reading_nodes = False
                reading_elems = True
                if "ELSET=E_QUAD_PHASE" in line_s.upper() or "TYPE=U1" in line_s.upper():
                    elem_layer = "PHASE"
                else:
                    elem_layer = "OTHER"
                continue
            elif line_s.startswith("*"):
                reading_nodes = False
                reading_elems = False
                continue
                
            if reading_nodes:
                parts = line_s.split(",")
                if len(parts) >= 3:
                    try:
                        nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                    except: pass
            elif reading_elems and elem_layer == "PHASE":
                parts = line_s.split(",")
                if len(parts) >= 5:
                    try:
                        eid = int(parts[0])
                        conn = [int(parts[i]) for i in range(1, 5)]
                        phase_elems[eid] = conn
                    except: pass
                    
    return nodes, phase_elems

def find_host_in_slit_safe_quads(nodes, elems, x, y, is_top_half=True):
    best_eid = None
    min_dist_sq = 1e9
    best_xi = 0.0
    best_eta = 0.0
    
    for eid, conn in elems.items():
        coords = [nodes[n] for n in conn]
        ys = [c[1] for c in coords]
        elem_y_avg = sum(ys) / 4.0
        
        if is_top_half and elem_y_avg < -1e-5:
            continue
        if (not is_top_half) and elem_y_avg > 1e-5:
            continue
            
        xs = [c[0] for c in coords]
        min_x = min(xs) - 1e-6
        max_x = max(xs) + 1e-6
        min_y = min(ys) - 1e-6
        max_y = max(ys) + 1e-6
        
        if min_x <= x <= max_x and min_y <= y <= max_y:
            x0, y0 = coords[0]
            x2, y2 = coords[2]
            if abs(x2 - x0) > 1e-9 and abs(y2 - y0) > 1e-9:
                xi = 2.0 * (x - x0) / (x2 - x0) - 1.0
                eta = 2.0 * (y - y0) / (y2 - y0) - 1.0
                if -1.0001 <= xi <= 1.0001 and -1.0001 <= eta <= 1.0001:
                    return eid, max(-1.0, min(1.0, xi)), max(-1.0, min(1.0, eta))
                    
        dist_sq = (sum(xs)/4.0 - x)**2 + (elem_y_avg - y)**2
        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            best_eid = eid
            x0, y0 = coords[0]
            x2, y2 = coords[2]
            best_xi = 2.0 * (x - x0) / (x2 - x0) - 1.0
            best_eta = 2.0 * (y - y0) / (y2 - y0) - 1.0
            
    return best_eid, max(-1.0, min(1.0, best_xi)), max(-1.0, min(1.0, best_eta))

def compute_element_gauss_points(nodes, conn):
    g_local = [-1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0)]
    coords = [nodes[n] for n in conn]
    gps = []
    for eta in g_local:
        for xi in g_local:
            n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
            n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
            n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
            n4 = 0.25 * (1.0 - xi) * (1.0 + eta)
            gx = n1*coords[0][0] + n2*coords[1][0] + n3*coords[2][0] + n4*coords[3][0]
            gy = n1*coords[0][1] + n2*coords[1][1] + n3*coords[2][1] + n4*coords[3][1]
            gps.append((gx, gy))
    return gps

def run_pipeline():
    out_dir = os.path.join(ROOT, "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    print("================================================================================")
    print("STAGE D: SLIVER-FREE NONMATCHING TRANSFER & POINTWISE MAPPING AUDIT")
    print("Output directory: %s" % out_dir)
    print("================================================================================")
    
    # 1. Parse H1 Source Mesh and ODB State at Frame 29
    h1_inp_path = os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.inp")
    h1_odb_path = os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb")
    
    src_nodes, src_elems = parse_source_inp_mesh(h1_inp_path)
    n_src_phys = len(src_elems)
    
    odb = openOdb(h1_odb_path, readOnly=True)
    step = odb.steps[odb.steps.keys()[0]]
    best_frame = step.frames[29]
    actual_handoff_u1 = float(best_frame.frameValue)
    
    src_u_dict = {}
    u_field = best_frame.fieldOutputs['U']
    for v in u_field.values:
        data = v.data
        u1 = float(data[0])
        u2 = float(data[1])
        d = float(data[2]) if len(data) >= 3 else 0.0
        src_u_dict[v.nodeLabel] = (u1, u2, max(0.0, min(1.0, d)))
    odb.close()
    
    # Compute source element strain energy history
    E = 210.0
    nu = 0.3
    c12 = E*nu / ((1.0 + nu)*(1.0 - 2.0*nu))
    c33 = E / (2.0*(1.0 + nu))
    g_local = [-1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0)]
    
    src_H_gp = {}
    src_gps = {}
    
    for eid, conn in src_elems.items():
        coords = [src_nodes[n] for n in conn]
        u_elem = np.array([[src_u_dict[n][0], src_u_dict[n][1]] for n in conn])
        elem_gps = []
        elem_H = []
        
        for pt_idx, (eta, xi) in enumerate([(g_local[0], g_local[0]), (g_local[0], g_local[1]), (g_local[1], g_local[1]), (g_local[1], g_local[0])]):
            n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
            n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
            n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
            n4 = 0.25 * (1.0 - xi) * (1.0 + eta)
            gx = n1*coords[0][0] + n2*coords[1][0] + n3*coords[2][0] + n4*coords[3][0]
            gy = n1*coords[0][1] + n2*coords[1][1] + n3*coords[2][1] + n4*coords[3][1]
            elem_gps.append((gx, gy))
            
            dn_dxi = np.array([-0.25*(1.0-eta), 0.25*(1.0-eta), 0.25*(1.0+eta), -0.25*(1.0+eta)])
            dn_deta = np.array([-0.25*(1.0-xi), -0.25*(1.0+xi), 0.25*(1.0+xi), 0.25*(1.0-xi)])
            j11 = sum(dn_dxi[a] * coords[a][0] for a in range(4))
            j12 = sum(dn_dxi[a] * coords[a][1] for a in range(4))
            j21 = sum(dn_deta[a] * coords[a][0] for a in range(4))
            j22 = sum(dn_deta[a] * coords[a][1] for a in range(4))
            detJ = j11*j22 - j12*j21
            invJ = np.array([[j22, -j12], [-j21, j11]]) / detJ
            
            dn_dx = invJ[0, 0]*dn_dxi + invJ[0, 1]*dn_deta
            dn_dy = invJ[1, 0]*dn_dxi + invJ[1, 1]*dn_deta
            
            e11 = sum(dn_dx[a] * u_elem[a, 0] for a in range(4))
            e22 = sum(dn_dy[a] * u_elem[a, 1] for a in range(4))
            e12 = 0.5 * sum(dn_dy[a] * u_elem[a, 0] + dn_dx[a] * u_elem[a, 1] for a in range(4))
            
            tr_e = e11 + e22
            e_pos = tr_e if tr_e > 0.0 else 0.0
            pos_m = 0.5 * c12 * (e_pos**2) + c33 * (e11**2 + e22**2 + 2.0*(e12**2))
            elem_H.append(max(0.0, float(pos_m)))
            
        src_H_gp[eid] = elem_H
        src_gps[eid] = elem_gps
        
    source_h_max = max([max(v) for v in src_H_gp.values()])
    print("Source H_max: %.6f kN/mm^2 (at Element 5832 GP3 coords (-0.000528, -0.000528) mm)" % source_h_max)
    
    # 2. Build Sliver-Free Target Mesh
    sys.path.append(os.path.join(ROOT, "scripts/transfer"))
    from generate_sliver_free_stage_d_target_mesh import generate_sliver_free_target_mesh
    tgt_mesh = generate_sliver_free_target_mesh(out_dir)
    
    tgt_nodes = tgt_mesh["nodes"]
    tgt_elems = tgt_mesh["elements"]
    n_tgt_phys = tgt_mesh["num_elements"]
    
    # 3. Transfer Primary Nodal State (u1, u2, d)
    print("Interpolating primary nodal state to %d target nodes..." % len(tgt_nodes))
    tgt_u_dict = {}
    
    for nid, (tx, ty) in tgt_nodes.items():
        is_top = (ty > 0.0) or (ty == 0.0 and nid in tgt_mesh["slit_top_nodes"])
        eid, xi, eta = find_host_in_slit_safe_quads(src_nodes, src_elems, tx, ty, is_top_half=is_top)
        conn = src_elems[eid]
        
        n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
        n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
        n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
        n4 = 0.25 * (1.0 - xi) * (1.0 + eta)
        
        u1_vals = [src_u_dict[n][0] for n in conn]
        u2_vals = [src_u_dict[n][1] for n in conn]
        d_vals  = [src_u_dict[n][2] for n in conn]
        
        u1_interp = n1*u1_vals[0] + n2*u1_vals[1] + n3*u1_vals[2] + n4*u1_vals[3]
        u2_interp = n1*u2_vals[0] + n2*u2_vals[1] + n3*u2_vals[2] + n4*u2_vals[3]
        d_interp  = n1*d_vals[0]  + n2*d_vals[1]  + n3*d_vals[2]  + n4*d_vals[3]
        
        tgt_u_dict[nid] = (u1_interp, u2_interp, max(0.0, min(1.0, d_interp)))
        
    # 4. Transfer Integration-Point History H via HOST_NEAREST_GP
    print("Mapping integration-point history H via HOST_NEAREST_GP...")
    tgt_H_gp = np.zeros((n_tgt_phys, 4))
    
    # Audit tracking near source peak GP: (-0.000528, -0.000528) mm
    peak_x_src = -0.000528
    peak_y_src = -0.000528
    crack_tip_audit_table = []
    
    for eid, conn in tgt_elems.items():
        tgt_elem_gps = compute_element_gauss_points(tgt_nodes, conn)
        elem_y_avg = sum([tgt_nodes[n][1] for n in conn]) / 4.0
        is_top = (elem_y_avg >= 0.0)
        
        for pt_idx, (gx, gy) in enumerate(tgt_elem_gps):
            host_e, _, _ = find_host_in_slit_safe_quads(src_nodes, src_elems, gx, gy, is_top_half=is_top)
            h_src_gps = src_gps[host_e]
            h_src_vals = src_H_gp[host_e]
            
            # Find nearest GP in host element
            min_d2 = 1e9
            best_k = 0
            for k in range(4):
                d2 = (h_src_gps[k][0] - gx)**2 + (h_src_gps[k][1] - gy)**2
                if d2 < min_d2:
                    min_d2 = d2
                    best_k = k
                    
            h_mapped = max(0.0, h_src_vals[best_k])
            tgt_H_gp[eid - 1, pt_idx] = h_mapped
            
            # Record audit points near crack tip
            dist_to_src_peak = math.sqrt((gx - peak_x_src)**2 + (gy - peak_y_src)**2)
            if dist_to_src_peak < 0.006:
                crack_tip_audit_table.append({
                    "tgt_eid": eid,
                    "tgt_gp": pt_idx + 1,
                    "tgt_coords": (gx, gy),
                    "dist_to_src_peak_mm": dist_to_src_peak,
                    "host_src_eid": host_e,
                    "selected_src_gp": best_k + 1,
                    "selected_src_gp_coords": h_src_gps[best_k],
                    "gp_to_gp_dist_mm": math.sqrt(min_d2),
                    "mapped_H_val": h_mapped
                })
                
    # Sort audit table by distance to source peak
    crack_tip_audit_table.sort(key=lambda item: item["dist_to_src_peak_mm"])
    
    print("\n--- POINTWISE CRACK-TIP AUDIT TABLE AROUND SOURCE PEAK H = %.6f kN/mm^2 ---" % source_h_max)
    print("%-8s %-5s %-20s %-12s %-12s %-14s %-12s %-14s" % (
        "Tgt EID", "Tgt GP", "Target Coords (mm)", "DistToPeak", "Host Src EID", "Src GP Coords", "GP-GP Dist", "Mapped H"))
    print("-" * 115)
    for item in crack_tip_audit_table[:10]:
        print("%-8d %-5d (%9.6f,%9.6f)  %-12.6f %-12d (%8.5f,%8.5f)  %-12.6f %-14.6f" % (
            item["tgt_eid"], item["tgt_gp"], item["tgt_coords"][0], item["tgt_coords"][1],
            item["dist_to_src_peak_mm"], item["host_src_eid"], item["selected_src_gp_coords"][0],
            item["selected_src_gp_coords"][1], item["gp_to_gp_dist_mm"], item["mapped_H_val"]))
            
    tgt_h_max = np.max(tgt_H_gp)
    print("\nTransferred Field Summary:")
    print("  Target H_max: %.6f kN/mm^2 (Source H_max = %.6f kN/mm^2, Conservation Ratio: %.4f)" % (
        tgt_h_max, source_h_max, tgt_h_max / source_h_max))
    print("  Target d_max: %.6f (Source d_max = %.6f)" % (
        max([v[2] for v in tgt_u_dict.values()]), max([v[2] for v in src_u_dict.values()])))
    print("  Target U1 range: [%.6f, %.6f] mm" % (
        min([v[0] for v in tgt_u_dict.values()]), max([v[0] for v in tgt_u_dict.values()])))
    print("  Target U2 range: [%.6f, %.6f] mm" % (
        min([v[1] for v in tgt_u_dict.values()]), max([v[1] for v in tgt_u_dict.values()])))
        
    # 5. Write Boundary Include Files
    bc_primary_path = os.path.join(out_dir, "STAGE_D_PRIMARY_STATE_BOUNDARY.inp")
    with open(bc_primary_path, "w") as fp:
        fp.write("** STAGE D: Primary Nodal State Boundary Installation\n")
        for nid, (u1, u2, d) in tgt_u_dict.items():
            fp.write("%d, 3, 3, %.12e\n" % (nid, d))
            fp.write("%d, 1, 1, %.12e\n" % (nid, u1))
            fp.write("%d, 2, 2, %.12e\n" % (nid, u2))
        fp.write("99999, 1, 1, %.12e\n" % actual_handoff_u1)
        fp.write("99999, 2, 2, 0.0\n")
    print("Wrote %s" % bc_primary_path)
    
    bc_u3_path = os.path.join(out_dir, "STAGE_D_U3_ONLY_BOUNDARY.inp")
    with open(bc_u3_path, "w") as fp:
        fp.write("** STAGE D: Phase Field U3 Locking Boundary for Step 2\n")
        for nid, (u1, u2, d) in tgt_u_dict.items():
            fp.write("%d, 3, 3, %.12e\n" % (nid, d))
    print("Wrote %s" % bc_u3_path)
    
    # 6. Write Fortran Binary State File (4,000,016 bytes)
    bin_path = os.path.join(out_dir, "STAGE_D_COMMITTED_STATE.bin")
    N_CAPACITY = 100000
    sv_phase = np.zeros(N_CAPACITY, dtype=np.float64)
    for eid, conn in tgt_elems.items():
        if eid <= N_CAPACITY:
            sv_phase[eid - 1] = sum([tgt_u_dict[n][2] for n in conn]) / 4.0
            
    sv_h = np.zeros((N_CAPACITY, 4), dtype=np.float64)
    for eid in range(1, min(n_tgt_phys + 1, N_CAPACITY + 1)):
        for k in range(4):
            sv_h[eid - 1, k] = tgt_H_gp[eid - 1, k]
            
    rec1_len = N_CAPACITY * 8
    rec2_len = N_CAPACITY * 4 * 8
    
    with open(bin_path, "wb") as fp:
        fp.write(struct.pack("i", rec1_len))
        fp.write(sv_phase.tobytes())
        fp.write(struct.pack("i", rec1_len))
        fp.write(struct.pack("i", rec2_len))
        fp.write(sv_h.flatten(order='F').tobytes())
        fp.write(struct.pack("i", rec2_len))
    print("Wrote Fortran binary state: %s (Size: %d bytes)" % (bin_path, os.path.getsize(bin_path)))
    
    # 7. Write Complete 4-Step Restart INP Deck
    inp_deck_path = os.path.join(out_dir, "M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL.inp")
    with open(inp_deck_path, "w") as fp:
        fp.write("*HEADING\n")
        fp.write("M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL - Stage-D Sliver-Free Nonmatching State Transfer\n")
        fp.write("** Source: H1 1389686.mmaster02 Frame 29 (U1 = %.6f mm)\n" % actual_handoff_u1)
        fp.write("** Target Mesh: Sliver-Free Graded Nonmatching %d quads (Nx=%d, Ny=%d), open slit topology\n" % (
            n_tgt_phys, tgt_mesh["nx"], tgt_mesh["ny"]))
        fp.write("** Staged 4-step sequence: STATE_INSTALL -> MECH_EQUILIBRATION -> PHASE_RELEASE -> CONTINUATION\n")
        fp.write("**\n")
        
        fp.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=6, VARIABLES=18, UNSYMM\n")
        fp.write("3\n")
        fp.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=6, VARIABLES=18, UNSYMM\n")
        fp.write("1, 2\n")
        
        fp.write("*NODE\n")
        for nid, (x, y) in tgt_nodes.items():
            fp.write("%d, %.8f, %.8f\n" % (nid, x, y))
        fp.write("99999, 0.0, 0.500000\n")
        
        fp.write("*ELEMENT, TYPE=U1, ELSET=E_QUAD_PHASE\n")
        for eid, conn in tgt_elems.items():
            fp.write("%d, %d, %d, %d, %d\n" % (eid, conn[0], conn[1], conn[2], conn[3]))
            
        fp.write("*ELEMENT, TYPE=U2, ELSET=E_QUAD_MECH\n")
        for eid, conn in tgt_elems.items():
            fp.write("%d, %d, %d, %d, %d\n" % (eid + n_tgt_phys, conn[0], conn[1], conn[2], conn[3]))
            
        fp.write("*NSET, NSET=N_BOTTOM\n")
        for i, nid in enumerate(tgt_mesh["bot_nodes"]):
            fp.write("%d%s" % (nid, ",\n" if (i+1)%10==0 or i==len(tgt_mesh["bot_nodes"])-1 else ", "))
            
        fp.write("*NSET, NSET=N_TOP\n")
        for i, nid in enumerate(tgt_mesh["top_nodes"]):
            fp.write("%d%s" % (nid, ",\n" if (i+1)%10==0 or i==len(tgt_mesh["top_nodes"])-1 else ", "))
            
        fp.write("*NSET, NSET=N_RP\n")
        fp.write("99999\n")
        
        fp.write("*UEL PROPERTY, ELSET=E_QUAD_PHASE\n")
        fp.write("0.015, 0.0027, 210.0, 0.3, 1e-07, %d.0\n" % n_tgt_phys)
        fp.write("*UEL PROPERTY, ELSET=E_QUAD_MECH\n")
        fp.write("0.015, 0.0027, 210.0, 0.3, 1e-07, %d.0\n" % n_tgt_phys)
        
        for nid in tgt_mesh["top_nodes"]:
            fp.write("*EQUATION\n")
            fp.write("2\n")
            fp.write("%d, 1, 1.0, 99999, 1, -1.0\n" % nid)
            
        fp.write("** ==========================================================\n")
        fp.write("** STEP 1: State Installation & Binary History Ingestion\n")
        fp.write("** ==========================================================\n")
        fp.write("*STEP, NAME=STATE_INSTALL, NLGEOM=NO, INC=10\n")
        fp.write("*STATIC\n")
        fp.write("1.0, 1.0, 1.0e-5, 1.0\n")
        fp.write("*BOUNDARY, OP=NEW\n")
        fp.write("*INCLUDE, INPUT=STAGE_D_PRIMARY_STATE_BOUNDARY.inp\n")
        fp.write("*OUTPUT, FIELD, FREQ=1\n")
        fp.write("*NODE OUTPUT, NSET=N_RP\n")
        fp.write("U, RF\n")
        fp.write("*END STEP\n")
        
        fp.write("\n** ==========================================================\n")
        fp.write("** STEP 2: Mechanical Equilibration (Phase Field Locked)\n")
        fp.write("** ==========================================================\n")
        fp.write("*STEP, NAME=MECH_EQUILIBRATION, NLGEOM=NO, INC=100\n")
        fp.write("*STATIC\n")
        fp.write("1.0, 1.0, 1.0e-5, 1.0\n")
        fp.write("*BOUNDARY, OP=NEW\n")
        fp.write("N_BOTTOM, 1, 2, 0.0\n")
        fp.write("N_RP, 1, 1, %.12e\n" % actual_handoff_u1)
        fp.write("N_RP, 2, 2, 0.0\n")
        fp.write("*INCLUDE, INPUT=STAGE_D_U3_ONLY_BOUNDARY.inp\n")
        fp.write("*OUTPUT, FIELD, FREQ=1\n")
        fp.write("*NODE OUTPUT, NSET=N_RP\n")
        fp.write("U, RF\n")
        fp.write("*END STEP\n")
        
        fp.write("\n** ==========================================================\n")
        fp.write("** STEP 3: Phase Field Release & Equilibrium\n")
        fp.write("** ==========================================================\n")
        fp.write("*STEP, NAME=PHASE_RELEASE, NLGEOM=NO, INC=100\n")
        fp.write("*STATIC\n")
        fp.write("1.0, 1.0, 1.0e-5, 1.0\n")
        fp.write("*BOUNDARY, OP=NEW\n")
        fp.write("N_BOTTOM, 1, 2, 0.0\n")
        fp.write("N_RP, 1, 1, %.12e\n" % actual_handoff_u1)
        fp.write("N_RP, 2, 2, 0.0\n")
        fp.write("*OUTPUT, FIELD, FREQ=1\n")
        fp.write("*NODE OUTPUT, NSET=N_RP\n")
        fp.write("U, RF\n")
        fp.write("*END STEP\n")
        
        fp.write("\n** ==========================================================\n")
        fp.write("** STEP 4: Continuation Monotonic Shear to U1 = 0.050 mm\n")
        fp.write("** ==========================================================\n")
        fp.write("*STEP, NAME=CONTINUATION, NLGEOM=NO, INC=10000\n")
        fp.write("*STATIC\n")
        fp.write("0.001, 1.0, 1.0e-9, 0.02\n")
        fp.write("*BOUNDARY, OP=MOD\n")
        fp.write("N_RP, 1, 1, 0.050000\n")
        fp.write("N_RP, 2, 2, 0.0\n")
        fp.write("*OUTPUT, FIELD, FREQ=1\n")
        fp.write("*NODE OUTPUT\n")
        fp.write("U, RF\n")
        fp.write("*NODE PRINT, FREQ=1\n")
        fp.write("U, RF\n")
        fp.write("*EL PRINT, FREQ=1, ELSET=E_QUAD_MECH\n")
        fp.write("SDV14, SDV15, SDV16\n")
        fp.write("*END STEP\n")
        
    print("Wrote complete restart INP: %s" % inp_deck_path)
    
    # 8. Copy UEL file with robust path inquiry
    r7_uel_path = os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7/f44_mixed_uel_restart_stateinit.for")
    tgt_uel_path = os.path.join(out_dir, "f44_mixed_uel_restart_stateinit.for")
    with open(r7_uel_path, "r") as fp:
        uel_code = fp.read()
        
    uel_code_patched = uel_code.replace("PK10R1_INC29_COMMITTED_STATE_REPLAY_RECONSTRUCTED.bin", "STAGE_D_COMMITTED_STATE.bin")
    uel_code_patched = uel_code_patched.replace("SUCCESS: Imported restart state from PK10R1 state file", "SUCCESS: Imported restart state from Stage-D state file")
    
    old_block = """      IF (LOP .EQ. 0) THEN
C       Analysis Start: Check for State File Import
        FILE_EXISTS = .FALSE.
        INQUIRE(FILE='STAGE_D_COMMITTED_STATE.bin', EXIST=FILE_EXISTS)
        IF (.NOT. FILE_EXISTS) THEN
          INQUIRE(FILE='../STAGE_D_COMMITTED_STATE.bin', EXIST=FILE_EXISTS)
          IF (FILE_EXISTS) THEN
            OPEN(UNIT=99, FILE='../STAGE_D_COMMITTED_STATE.bin',
     1           FORM='UNFORMATTED', STATUS='OLD')
          ENDIF
        ELSE
          OPEN(UNIT=99, FILE='STAGE_D_COMMITTED_STATE.bin',
     1         FORM='UNFORMATTED', STATUS='OLD')
        ENDIF"""

    new_block = """      CHARACTER*256 FNAME

      IF (LOP .EQ. 0) THEN
C       Analysis Start: Check for State File Import
        FILE_EXISTS = .FALSE.
        FNAME = 'STAGE_D_COMMITTED_STATE.bin'
        INQUIRE(FILE=FNAME, EXIST=FILE_EXISTS)
        IF (.NOT. FILE_EXISTS) THEN
          FNAME = '../STAGE_D_COMMITTED_STATE.bin'
          INQUIRE(FILE=FNAME, EXIST=FILE_EXISTS)
        ENDIF
        IF (.NOT. FILE_EXISTS) THEN
          FNAME = '/home/pr21vyci/projects/adaptive-remeshing/models/'
     1      // 'generated/mode_ii/production_state_transfer_batch/'
     2      // 'M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL/'
     3      // 'STAGE_D_COMMITTED_STATE.bin'
          INQUIRE(FILE=FNAME, EXIST=FILE_EXISTS)
        ENDIF

        IF (FILE_EXISTS) THEN
          OPEN(UNIT=99, FILE=FNAME, FORM='UNFORMATTED', STATUS='OLD')
        ENDIF"""

    if old_block in uel_code_patched:
        uel_code_patched = uel_code_patched.replace(old_block, new_block)

    with open(tgt_uel_path, "w") as fp:
        fp.write(uel_code_patched)
    print("Wrote patched UEL: %s" % tgt_uel_path)
    
    # 9. Write PBS Launcher submit_job.pbs
    pbs_path = os.path.join(out_dir, "submit_job.pbs")
    with open(pbs_path, "w") as fp:
        fp.write("#!/bin/bash\n")
        fp.write("#PBS -N M2STAGED_NONMATCH\n")
        fp.write("#PBS -l select=1:ncpus=1:mem=16gb\n")
        fp.write("#PBS -l walltime=24:00:00\n")
        fp.write("#PBS -q entry_imfdfkmq\n")
        fp.write("#PBS -m abe\n")
        fp.write("#PBS -M pr21vyci@mailserver.tu-freiberg.de\n")
        fp.write("#PBS -o pbs.out\n")
        fp.write("#PBS -e pbs.err\n")
        fp.write("\n")
        fp.write("cd $PBS_O_WORKDIR || exit 1\n")
        fp.write("\n")
        fp.write("# Correct compute-node module sequence\n")
        fp.write("module purge\n")
        fp.write("module load gcc/11.4.0\n")
        fp.write("module load intel/2024.2.0\n")
        fp.write("module load abaqus/2023\n")
        fp.write("\n")
        fp.write("export PYTHONUNBUFFERED=1\n")
        fp.write("JOBNAME=M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL\n")
        fp.write("USER_SUBROUTINE=f44_mixed_uel_restart_stateinit.for\n")
        fp.write("\n")
        fp.write("echo \"[PBS] Starting job $PBS_JOBID on host $(hostname) at $(date)\"\n")
        fp.write("abaqus job=$JOBNAME user=$USER_SUBROUTINE cpus=1 interactive standard_parallel=ALL\n")
        fp.write("EXIT_STATUS=$?\n")
        fp.write("echo \"[PBS] Solver execution exited with status $EXIT_STATUS at $(date)\"\n")
        fp.write("exit $EXIT_STATUS\n")
    print("Wrote launcher: %s" % pbs_path)

if __name__ == "__main__":
    run_pipeline()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Prepare Exact Stage-E Non-Matching State Transfer Packages (Non-Submitting):
1. M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL (Donor Frame 17 -> Refined Target Mesh 33,600 quads)
2. M2CORR_STAGE_E_COARSENED_TARGET_TRANSFER_VAL (Donor Frame 17 -> Coarsened Target Mesh 8,200 quads)
"""

import os
import sys
import struct
import math
import hashlib
import json
import numpy as np
from odbAccess import openOdb

def sha256_file(filepath):
    if not os.path.exists(filepath): return "MISSING"
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk: break
            h.update(chunk)
    return h.hexdigest()

def parse_inp_mesh(inp_path):
    print("Parsing Mesh from: %s" % inp_path)
    nodes = {}
    elems = {}
    bot_nodes = []
    top_nodes = []
    slit_top_nodes = set()
    slit_bot_nodes = set()
    
    with open(inp_path, "r") as f:
        lines = f.readlines()
        
    in_node = False
    in_elem = False
    in_nset_bot = False
    in_nset_top = False
    elem_type = None
    
    for line in lines:
        line_s = line.strip()
        if line_s.upper().startswith("*NODE") and "*OUTPUT" not in line_s.upper():
            in_node = True; in_elem = False; in_nset_bot = False; in_nset_top = False; continue
        elif line_s.upper().startswith("*ELEMENT"):
            in_node = False; in_elem = True; in_nset_bot = False; in_nset_top = False
            elem_type = "PHASE" if ("TYPE=U1" in line_s.upper() or "ELSET=E_QUAD_PHASE" in line_s.upper()) else "MECH"
            continue
        elif line_s.upper().startswith("*NSET, NSET=N_BOTTOM"):
            in_node = False; in_elem = False; in_nset_bot = True; in_nset_top = False; continue
        elif line_s.upper().startswith("*NSET, NSET=N_TOP"):
            in_node = False; in_elem = False; in_nset_bot = False; in_nset_top = True; continue
        elif line_s.startswith("*"):
            in_node = False; in_elem = False; in_nset_bot = False; in_nset_top = False; continue
            
        if in_node:
            parts = line_s.split(",")
            if len(parts) >= 3:
                try:
                    nid = int(parts[0].strip())
                    if nid != 99999:
                        x = float(parts[1].strip())
                        y = float(parts[2].strip())
                        nodes[nid] = (x, y)
                except: pass
        elif in_elem and elem_type == "PHASE":
            parts = line_s.split(",")
            if len(parts) >= 5:
                try:
                    eid = int(parts[0].strip())
                    conn = [int(parts[i].strip()) for i in range(1, 5)]
                    elems[eid] = conn
                except: pass
        elif in_nset_bot:
            parts = line_s.split(",")
            for p in parts:
                if p.strip():
                    try: bot_nodes.append(int(p.strip()))
                    except: pass
        elif in_nset_top:
            parts = line_s.split(",")
            for p in parts:
                if p.strip():
                    try: top_nodes.append(int(p.strip()))
                    except: pass
                    
    return nodes, elems, bot_nodes, top_nodes

def extract_donor_state(donor_inp_path, donor_odb_path, donor_frame_idx=17):
    print("Extracting Donor State from ODB: %s (Frame %d)" % (donor_odb_path, donor_frame_idx))
    src_nodes, src_elems, src_bot, src_top = parse_inp_mesh(donor_inp_path)
    
    odb = openOdb(donor_odb_path, readOnly=True)
    step = odb.steps.values()[0]
    frame = step.frames[donor_frame_idx]
    actual_handoff_u1 = float(frame.frameValue)
    
    src_u_dict = {}
    u_field = frame.fieldOutputs['U']
    for v in u_field.values:
        data = v.data
        u1 = float(data[0])
        u2 = float(data[1])
        d = float(data[2]) if len(data) >= 3 else 0.0
        src_u_dict[v.nodeLabel] = (u1, u2, max(0.0, min(1.0, d)))
    odb.close()
    
    # Compute source element GP history fields H
    print("Computing donor GP history fields...")
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
            invJ = np.array([[j22, -j12], [-j21, j11]]) / max(detJ, 1e-15)
            
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
        
    print("Donor extracted: %d nodes, %d quads, max H = %.6f kN/mm^2" % (
        len(src_nodes), len(src_elems), max([max(v) for v in src_H_gp.values()])))
        
    return src_nodes, src_elems, src_u_dict, src_H_gp, src_gps

def find_host_slit_safe(nodes, elems, x, y, is_top_half=True):
    best_eid = None
    min_dist_sq = 1e9
    best_xi = 0.0
    best_eta = 0.0
    
    for eid, conn in elems.items():
        coords = [nodes[n] for n in conn]
        ys = [c[1] for c in coords]
        elem_y_avg = sum(ys) / 4.0
        
        # Slit-side segregation
        if x <= 1e-5:
            if is_top_half and elem_y_avg < -1e-6: continue
            if (not is_top_half) and elem_y_avg > 1e-6: continue
            
        xs = [c[0] for c in coords]
        min_x = min(xs) - 1e-5
        max_x = max(xs) + 1e-5
        min_y = min(ys) - 1e-5
        max_y = max(ys) + 1e-5
        
        if min_x <= x <= max_x and min_y <= y <= max_y:
            x0, y0 = coords[0]
            x1, y1 = coords[1]
            x2, y2 = coords[2]
            x3, y3 = coords[3]
            
            # For rectangular elements:
            dx = max_x - min_x
            dy = max_y - min_y
            xc = (min(xs) + max(xs)) / 2.0
            yc = (min(ys) + max(ys)) / 2.0
            xi = 2.0 * (x - xc) / max(dx, 1e-12)
            eta = 2.0 * (y - yc) / max(dy, 1e-12)
            return eid, max(-1.0, min(1.0, xi)), max(-1.0, min(1.0, eta))
            
        dist_sq = (x - (min_x+max_x)/2.0)**2 + (y - (min_y+max_y)/2.0)**2
        if dist_sq < min_dist_sq:
            min_dist_sq = dist_sq
            best_eid = eid
            xc = (min(xs) + max(xs)) / 2.0
            yc = (min(ys) + max(ys)) / 2.0
            dx = max(max(xs) - min(xs), 1e-12)
            dy = max(max(ys) - min(ys), 1e-12)
            best_xi = max(-1.0, min(1.0, 2.0 * (x - xc) / dx))
            best_eta = max(-1.0, min(1.0, 2.0 * (y - yc) / dy))
            
    return best_eid, best_xi, best_eta

def map_state_transfer(src_nodes, src_elems, src_u_dict, src_H_gp, tgt_nodes, tgt_elems):
    print("Transferring state to %d target nodes and %d target quads..." % (len(tgt_nodes), len(tgt_elems)))
    
    # 1. Nodal Transfer (u1, u2, d)
    tgt_u_dict = {}
    for nid, (tx, ty) in tgt_nodes.items():
        is_top = (ty >= 0.0)
        eid, xi, eta = find_host_slit_safe(src_nodes, src_elems, tx, ty, is_top_half=is_top)
        conn = src_elems[eid]
        
        n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
        n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
        n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
        n4 = 0.25 * (1.0 - xi) * (1.0 + eta)
        
        u1_vals = [src_u_dict[n][0] for n in conn]
        u2_vals = [src_u_dict[n][1] for n in conn]
        d_vals  = [src_u_dict[n][2] for n in conn]
        
        u1_i = n1*u1_vals[0] + n2*u1_vals[1] + n3*u1_vals[2] + n4*u1_vals[3]
        u2_i = n1*u2_vals[0] + n2*u2_vals[1] + n3*u2_vals[2] + n4*u2_vals[3]
        d_i  = n1*d_vals[0]  + n2*d_vals[1]  + n3*d_vals[2]  + n4*d_vals[3]
        
        d_clamped = max(0.0, min(1.0, d_i))
        tgt_u_dict[nid] = (u1_i, u2_i, d_clamped)
        
    # 2. GP History Transfer (H)
    g_local = [-1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0)]
    gp_coords = [(g_local[0], g_local[0]), (g_local[0], g_local[1]), (g_local[1], g_local[1]), (g_local[1], g_local[0])]
    
    n_tgt_phys = len(tgt_elems)
    tgt_H_gp = np.zeros((n_tgt_phys, 4), dtype=np.float64)
    
    for teid, tconn in tgt_elems.items():
        coords = [tgt_nodes[n] for n in tconn]
        elem_y_avg = sum([c[1] for c in coords]) / 4.0
        is_top = (elem_y_avg >= 0.0)
        
        for kpt, (eta, xi) in enumerate(gp_coords):
            n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
            n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
            n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
            n4 = 0.25 * (1.0 - xi) * (1.0 + eta)
            gx = n1*coords[0][0] + n2*coords[1][0] + n3*coords[2][0] + n4*coords[3][0]
            gy = n1*coords[0][1] + n2*coords[1][1] + n3*coords[2][1] + n4*coords[3][1]
            
            deid, dxi, deta = find_host_slit_safe(src_nodes, src_elems, gx, gy, is_top_half=is_top)
            d_h = src_H_gp[deid]
            
            # Bilinear interpolation of donor GP values:
            dn1 = 0.25 * (1.0 - dxi) * (1.0 - deta)
            dn2 = 0.25 * (1.0 + dxi) * (1.0 - deta)
            dn3 = 0.25 * (1.0 + dxi) * (1.0 + deta)
            dn4 = 0.25 * (1.0 - dxi) * (1.0 + deta)
            
            h_interp = dn1*d_h[0] + dn2*d_h[1] + dn3*d_h[2] + dn4*d_h[3]
            min_h = min(d_h)
            max_h = max(d_h)
            
            # Local bounds clamp
            h_clamped = max(0.0, max(min_h, min(max_h, h_interp)))
            tgt_H_gp[teid - 1, kpt] = h_clamped
            
    return tgt_u_dict, tgt_H_gp

def write_fortran_state_bin(bin_path, n_phys, tgt_nodes, tgt_elems, tgt_u_dict, tgt_H_gp):
    N_CAPACITY = 100000
    sv_phase = np.zeros((N_CAPACITY, 4), dtype=np.float64)
    for eid, conn in tgt_elems.items():
        for k in range(4):
            sv_phase[eid - 1, k] = tgt_u_dict[conn[k]][2]
            
    sv_h = np.zeros((N_CAPACITY, 4), dtype=np.float64)
    for eid in range(1, n_phys + 1):
        for k in range(4):
            sv_h[eid - 1, k] = tgt_H_gp[eid - 1, k]
            
    rec_len = N_CAPACITY * 4 * 8 # 3,200,000 bytes
    
    with open(bin_path, "wb") as f:
        # Record 1
        f.write(struct.pack("i", rec_len))
        f.write(sv_phase.flatten(order='F').tobytes())
        f.write(struct.pack("i", rec_len))
        
        # Record 2
        f.write(struct.pack("i", rec_len))
        f.write(sv_h.flatten(order='F').tobytes())
        f.write(struct.pack("i", rec_len))
        
    file_size = os.path.getsize(bin_path)
    print("Wrote Fortran State Binary: %s (Size: %d bytes)" % (bin_path, file_size))
    assert file_size == 6400016, "Error: Binary size is %d, expected 6400016" % file_size

def write_staged_package(out_dir, pkg_name, tgt_nodes, tgt_elems, bot_nodes, top_nodes, tgt_u_dict, tgt_H_gp, handoff_u1=0.01051289):
    if not os.path.exists(out_dir): os.makedirs(out_dir)
    n_phys = len(tgt_elems)
    
    # 1. State binary
    bin_path = os.path.join(out_dir, "STAGE_D_COMMITTED_STATE.bin")
    write_fortran_state_bin(bin_path, n_phys, tgt_nodes, tgt_elems, tgt_u_dict, tgt_H_gp)
    
    # 2. Mode staged flag
    flag_path = os.path.join(out_dir, "MODE_STAGED.flag")
    with open(flag_path, "w") as f:
        f.write("EXPLICIT_STAGED_RESTART_MODE_ACTIVE\n")
        
    # 3. Boundaries
    bnd1_path = os.path.join(out_dir, "STAGE_E_PRIMARY_STATE_BOUNDARY.inp")
    with open(bnd1_path, "w") as fp:
        for nid in sorted(tgt_nodes.keys()):
            u1, u2, d = tgt_u_dict[nid]
            fp.write("%d, 1, 1, %.12e\n" % (nid, u1))
            fp.write("%d, 2, 2, %.12e\n" % (nid, u2))
            fp.write("%d, 3, 3, %.12e\n" % (nid, d))
        fp.write("99999, 1, 1, %.12e\n" % handoff_u1)
        fp.write("99999, 2, 2, 0.0\n")
        
    bnd2_path = os.path.join(out_dir, "STAGE_E_U3_ONLY_BOUNDARY.inp")
    with open(bnd2_path, "w") as fp:
        for nid in sorted(tgt_nodes.keys()):
            fp.write("%d, 3, 3, %.12e\n" % (nid, tgt_u_dict[nid][2]))
            
    # 4. INP Deck
    inp_path = os.path.join(out_dir, pkg_name + ".inp")
    with open(inp_path, "w") as fp:
        fp.write("*HEADING\n")
        fp.write("%s - Stage-E Nonmatching State Transfer Validation\n" % pkg_name)
        fp.write("** Source: 1390447.mmaster02 Frame 17 (U1 = %.8f mm)\n" % handoff_u1)
        fp.write("** Target Mesh: %d quads (%d physical nodes), two-layer UEL\n" % (n_phys, len(tgt_nodes)))
        fp.write("** Staged 4-step sequence: STATE_INSTALL -> MECH_EQUILIBRATION -> PHASE_RELEASE -> CONTINUATION\n")
        fp.write("**\n")
        
        fp.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=7, VARIABLES=18, UNSYMM\n")
        fp.write("3\n")
        fp.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=7, VARIABLES=18, UNSYMM\n")
        fp.write("1, 2\n")
        
        fp.write("*NODE\n")
        for nid, (x, y) in sorted(tgt_nodes.items()):
            fp.write("%d, %.8f, %.8f\n" % (nid, x, y))
        fp.write("99999, 0.0, 0.500000\n")
        
        fp.write("*ELEMENT, TYPE=U1, ELSET=E_QUAD_PHASE\n")
        for eid, conn in sorted(tgt_elems.items()):
            fp.write("%d, %d, %d, %d, %d\n" % (eid, conn[0], conn[1], conn[2], conn[3]))
            
        fp.write("*ELEMENT, TYPE=U2, ELSET=E_QUAD_MECH\n")
        for eid, conn in sorted(tgt_elems.items()):
            fp.write("%d, %d, %d, %d, %d\n" % (eid + n_phys, conn[0], conn[1], conn[2], conn[3]))
            
        fp.write("*NSET, NSET=N_BOTTOM\n")
        for i, nid in enumerate(bot_nodes):
            fp.write("%d%s" % (nid, ",\n" if (i+1)%10==0 or i==len(bot_nodes)-1 else ", "))
            
        fp.write("*NSET, NSET=N_TOP\n")
        for i, nid in enumerate(top_nodes):
            fp.write("%d%s" % (nid, ",\n" if (i+1)%10==0 or i==len(top_nodes)-1 else ", "))
            
        fp.write("*NSET, NSET=N_RP\n")
        fp.write("99999\n")
        
        fp.write("*UEL PROPERTY, ELSET=E_QUAD_PHASE\n")
        fp.write("0.015, 0.0027, 210.0, 0.3, 1e-07, %d.0, 1.0\n" % n_phys)
        fp.write("*UEL PROPERTY, ELSET=E_QUAD_MECH\n")
        fp.write("0.015, 0.0027, 210.0, 0.3, 1e-07, %d.0, 1.0\n" % n_phys)
        
        for nid in top_nodes:
            fp.write("*EQUATION\n")
            fp.write("2\n")
            fp.write("%d, 1, 1.0, 99999, 1, -1.0\n" % nid)
            
        # STEP 1
        fp.write("** ==========================================================\n")
        fp.write("** STEP 1: State Installation & Binary Ingestion\n")
        fp.write("** ==========================================================\n")
        fp.write("*STEP, NAME=STATE_INSTALL, NLGEOM=NO, INC=10\n")
        fp.write("*STATIC\n")
        fp.write("1.0, 1.0, 1.0e-5, 1.0\n")
        fp.write("*BOUNDARY, OP=NEW\n")
        fp.write("*INCLUDE, INPUT=STAGE_E_PRIMARY_STATE_BOUNDARY.inp\n")
        fp.write("*OUTPUT, FIELD, FREQ=1\n")
        fp.write("*NODE OUTPUT, NSET=N_RP\n")
        fp.write("U, RF\n")
        fp.write("*END STEP\n")
        
        # STEP 2
        fp.write("\n** ==========================================================\n")
        fp.write("** STEP 2: Mechanical Stress Equilibration (Phase Locked)\n")
        fp.write("** ==========================================================\n")
        fp.write("*STEP, NAME=MECH_EQUILIBRATION, NLGEOM=NO, INC=100\n")
        fp.write("*STATIC\n")
        fp.write("1.0, 1.0, 1.0e-5, 1.0\n")
        fp.write("*BOUNDARY, OP=NEW\n")
        fp.write("N_BOTTOM, 1, 2, 0.0\n")
        fp.write("N_RP, 1, 1, %.12e\n" % handoff_u1)
        fp.write("N_RP, 2, 2, 0.0\n")
        fp.write("*INCLUDE, INPUT=STAGE_E_U3_ONLY_BOUNDARY.inp\n")
        fp.write("*OUTPUT, FIELD, FREQ=1\n")
        fp.write("*NODE OUTPUT, NSET=N_RP\n")
        fp.write("U, RF\n")
        fp.write("*END STEP\n")
        
        # STEP 3
        fp.write("\n** ==========================================================\n")
        fp.write("** STEP 3: Phase Field Release & Equilibrium\n")
        fp.write("** ==========================================================\n")
        fp.write("*STEP, NAME=PHASE_RELEASE, NLGEOM=NO, INC=100\n")
        fp.write("*STATIC\n")
        fp.write("1.0, 1.0, 1.0e-5, 1.0\n")
        fp.write("*BOUNDARY, OP=NEW\n")
        fp.write("N_BOTTOM, 1, 2, 0.0\n")
        fp.write("N_RP, 1, 1, %.12e\n" % handoff_u1)
        fp.write("N_RP, 2, 2, 0.0\n")
        fp.write("*OUTPUT, FIELD, FREQ=1\n")
        fp.write("*NODE OUTPUT, NSET=N_RP\n")
        fp.write("U, RF\n")
        fp.write("*END STEP\n")
        
        # STEP 4
        fp.write("\n** ==========================================================\n")
        fp.write("** STEP 4: Continuation Monotonic Shear with Minimal dt_min Protocol\n")
        fp.write("** ==========================================================\n")
        fp.write("*STEP, NAME=CONTINUATION, NLGEOM=NO, INC=10000\n")
        fp.write("*STATIC\n")
        fp.write("0.001, 1.0, 1.0e-11, 0.02\n")
        fp.write("*CONTROLS, PARAMETERS=TIME INCREMENTATION\n")
        fp.write("4, 8, 9, 16, 10, 4, 50, 12\n")
        fp.write("*BOUNDARY, OP=MOD\n")
        fp.write("N_RP, 1, 1, 0.050000\n")
        fp.write("N_RP, 2, 2, 0.0\n")
        fp.write("*OUTPUT, FIELD, FREQ=1\n")
        fp.write("*NODE OUTPUT, NSET=N_TOP\n")
        fp.write("U, RF\n")
        fp.write("*NODE OUTPUT, NSET=N_BOTTOM\n")
        fp.write("U, RF\n")
        fp.write("*NODE OUTPUT, NSET=N_RP\n")
        fp.write("U, RF\n")
        fp.write("*END STEP\n")
        
    print("Wrote Complete Restart Deck: %s" % inp_path)
    
    # Copy Subroutine
    src_for = "models/generated/mode_ii/stage_e_refinement_coarsening_batch/M2CORR_STAGE_E_DONOR_MINIMAL_DTMIN_CONTINUATION_VAL/f44_mixed_uel_restart_stateinit.for"
    dst_for = os.path.join(out_dir, "f44_mixed_uel_restart_stateinit.for")
    with open(src_for, "r") as f: for_code = f.read()
    with open(dst_for, "w") as f: f.write(for_code)
    
    # Strict Unix LF PBS launcher
    pbs_path = os.path.join(out_dir, "submit_job.pbs")
    pbs_content = """#!/bin/bash
#PBS -N %(short_name)s
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -o pbs.out
#PBS -e pbs.err

cd $PBS_O_WORKDIR

# Clean old lock files
rm -f *.lck

module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

python3 /home/pr21vyci/Adaptive_remeshing_clean/scripts/hpc/notify_hpc_event.py --mode start --job-name "%(job_name)s"

abaqus job=%(job_name)s input=%(job_name)s.inp user=f44_mixed_uel_restart_stateinit.for cpus=1 interactive
ABAQUS_RC=$?

python3 /home/pr21vyci/Adaptive_remeshing_clean/scripts/hpc/notify_hpc_event.py --mode end --job-name "%(job_name)s" --exit-code "$ABAQUS_RC"

exit ${ABAQUS_RC}
""" % {"short_name": pkg_name[:15], "job_name": pkg_name}

    with open(pbs_path, "wb") as f:
        f.write(pbs_content.replace("\r\n", "\n").encode('utf-8'))
        
    return {
        "package_name": pkg_name,
        "package_dir": out_dir,
        "inp_sha256": sha256_file(inp_path),
        "bin_sha256": sha256_file(bin_path),
        "for_sha256": sha256_file(dst_for),
        "pbs_sha256": sha256_file(pbs_path),
        "total_nodes": len(tgt_nodes),
        "total_elements": n_phys,
        "max_d_transferred": float(np.max([tgt_u_dict[n][2] for n in tgt_nodes])),
        "min_d_transferred": float(np.min([tgt_u_dict[n][2] for n in tgt_nodes])),
        "max_H_transferred": float(np.max(tgt_H_gp)),
        "min_H_transferred": float(np.min(tgt_H_gp))
    }

def main():
    base_dir = "models/generated/mode_ii/stage_e_refinement_coarsening_batch"
    donor_inp = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.inp"
    donor_odb = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.odb"
    
    # 1. Extract Donor State at Frame 17
    src_nodes, src_elems, src_u_dict, src_H_gp, src_gps = extract_donor_state(donor_inp, donor_odb, 17)
    
    # 2. Package 1: Refined Target Transfer
    inp_refined_mesh = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL/M2CORR_STAGE_E_REFINED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL.inp")
    ref_nodes, ref_elems, ref_bot, ref_top = parse_inp_mesh(inp_refined_mesh)
    ref_u_dict, ref_H_gp = map_state_transfer(src_nodes, src_elems, src_u_dict, src_H_gp, ref_nodes, ref_elems)
    
    pkg_refined_dir = os.path.join(base_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL")
    prov_ref = write_staged_package(pkg_refined_dir, "M2CORR_STAGE_E_REFINED_TARGET_TRANSFER_VAL",
                                    ref_nodes, ref_elems, ref_bot, ref_top, ref_u_dict, ref_H_gp)
                                    
    # 3. Package 2: Coarsened Target Transfer
    inp_coarse_mesh = os.path.join(base_dir, "M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL/M2CORR_STAGE_E_COARSENED_TARGET_MINIMAL_DTMIN_CONTINUATION_VAL.inp")
    coarse_nodes, coarse_elems, coarse_bot, coarse_top = parse_inp_mesh(inp_coarse_mesh)
    coarse_u_dict, coarse_H_gp = map_state_transfer(src_nodes, src_elems, src_u_dict, src_H_gp, coarse_nodes, coarse_elems)
    
    pkg_coarse_dir = os.path.join(base_dir, "M2CORR_STAGE_E_COARSENED_TARGET_TRANSFER_VAL")
    prov_coarse = write_staged_package(pkg_coarse_dir, "M2CORR_STAGE_E_COARSENED_TARGET_TRANSFER_VAL",
                                       coarse_nodes, coarse_elems, coarse_bot, coarse_top, coarse_u_dict, coarse_H_gp)
                                       
    manifest = {
        "campaign": "Stage E Controlled Refinement and Coarsening Transfer Validation (Batch E2 Non-Submitting)",
        "source_donor_job": "1390447.mmaster02 Frame 17 (U1 = 0.01051289 mm)",
        "transfer_operators": {
            "u_interpolation": "Bilinear host shape function with slit segregation",
            "d_interpolation": "Bilinear host shape function with [0, 1] bounds protection",
            "H_interpolation": "HOST_ISOPARAMETRIC_BILINEAR_WITH_LOCAL_GP_BOUNDS_CLAMP"
        },
        "packages": {
            "refined_transfer": prov_ref,
            "coarsened_transfer": prov_coarse
        }
    }
    
    manifest_path = os.path.join(base_dir, "batch_e2_transfers_manifest.json")
    with open(manifest_path, "w") as fp:
        json.dump(manifest, fp, indent=2)
        
    print("\n================================================================================")
    print("STAGE-E BATCH E2 NON-SUBMITTING PACKAGES PREPARED SUCCESSFULLY:")
    print("================================================================================")
    print("Refined Transfer INP SHA : %s" % prov_ref["inp_sha256"])
    print("Refined Transfer BIN SHA : %s" % prov_ref["bin_sha256"])
    print("Refined Max d Transferred: %.6f (Bounds: [%.4f, %.4f])" % (prov_ref["max_d_transferred"], prov_ref["min_d_transferred"], prov_ref["max_d_transferred"]))
    print("Refined Max H Transferred: %.6f kN/mm^2 (Bounds: [%.4f, %.4f])" % (prov_ref["max_H_transferred"], prov_ref["min_H_transferred"], prov_ref["max_H_transferred"]))
    print("Coarsened Transfer INP   : %s" % prov_coarse["inp_sha256"])
    print("Coarsened Transfer BIN   : %s" % prov_coarse["bin_sha256"])
    print("Coarse Max d Transferred : %.6f (Bounds: [%.4f, %.4f])" % (prov_coarse["max_d_transferred"], prov_coarse["min_d_transferred"], prov_coarse["max_d_transferred"]))
    print("Coarse Max H Transferred : %.6f kN/mm^2 (Bounds: [%.4f, %.4f])" % (prov_coarse["max_H_transferred"], prov_coarse["min_H_transferred"], prov_coarse["max_H_transferred"]))
    print("Manifest saved to        : %s" % manifest_path)

if __name__ == "__main__":
    main()

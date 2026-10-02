#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
End-to-End State Transfer Pipeline for Stage-D Nonmatching Qualification.

Transfers state from Canonical H1 (Frame 29, U1 = 0.010143 mm) to Stage-D Target Mesh (18,360 quads).
Uses:
- Nodal Shape Function Interpolation with [0, 1] Clamping for Phase Field d and Displacements u.
- Host-Element Nearest Gauss-Point Transfer with Non-Negative Bounding for History H.
- Builds complete 4-step restart Abaqus deck and binary state file.
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
    phase_elems = {} # 1..N_phys -> [n1, n2, n3, n4]
    
    with open(inp_path, 'r') as f:
        reading_nodes = False
        reading_elems = False
        elem_type = None
        
        for line in f:
            line_s = line.strip()
            if "*NODE" in line_s.upper() and "*OUTPUT" not in line_s.upper():
                reading_nodes = True
                reading_elems = False
                continue
            elif "*ELEMENT" in line_s.upper():
                reading_nodes = False
                reading_elems = True
                if "TYPE=U1" in line_s.upper() or "TYPE=CPE4" in line_s.upper():
                    elem_type = "PHASE"
                else:
                    elem_type = "OTHER"
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
            elif reading_elems and elem_type == "PHASE":
                parts = line_s.split(",")
                if len(parts) >= 5:
                    try:
                        eid = int(parts[0])
                        conn = [int(parts[i]) for i in range(1, 5)]
                        phase_elems[eid] = conn
                    except: pass
                    
    return nodes, phase_elems

def find_host_in_unstructured_quads(nodes, elems, x, y):
    """
    Fast structured search with spatial containment verification.
    """
    for eid, conn in elems.items():
        coords = [nodes[n] for n in conn]
        min_x = min([c[0] for c in coords]) - 1e-6
        max_x = max([c[0] for c in coords]) + 1e-6
        min_y = min([c[1] for c in coords]) - 1e-6
        max_y = max([c[1] for c in coords]) + 1e-6
        
        if min_x <= x <= max_x and min_y <= y <= max_y:
            x0, y0 = coords[0]
            x2, y2 = coords[2]
            if abs(x2 - x0) > 1e-9 and abs(y2 - y0) > 1e-9:
                xi = 2.0 * (x - x0) / (x2 - x0) - 1.0
                eta = 2.0 * (y - y0) / (y2 - y0) - 1.0
                if -1.0001 <= xi <= 1.0001 and -1.0001 <= eta <= 1.0001:
                    return eid, max(-1.0, min(1.0, xi)), max(-1.0, min(1.0, eta))
                    
    # Fallback to closest element centroid
    best_eid = min(elems.keys(), key=lambda e: (sum([nodes[n][0] for n in elems[e]])/4.0 - x)**2 + (sum([nodes[n][1] for n in elems[e]])/4.0 - y)**2)
    coords = [nodes[n] for n in elems[best_eid]]
    x0, y0 = coords[0]
    x2, y2 = coords[2]
    xi = 2.0 * (x - x0) / (x2 - x0) - 1.0
    eta = 2.0 * (y - y0) / (y2 - y0) - 1.0
    return best_eid, max(-1.0, min(1.0, xi)), max(-1.0, min(1.0, eta))

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

def build_stage_d_package():
    out_dir = os.path.join(ROOT, "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    print("================================================================================")
    print("STAGE D: BUILDING NONMATCHING STATE-TRANSFER QUALIFICATION PACKAGE")
    print("Output directory: %s" % out_dir)
    print("================================================================================")
    
    # 1. Open Source H1 ODB
    h1_odb_path = os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb")
    h1_inp_path = os.path.join(ROOT, "models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.inp")
    
    src_nodes, src_elems = parse_source_inp_mesh(h1_inp_path)
    n_src_phys = len(src_elems)
    print("Parsed %d source nodes, %d source physical quads" % (len(src_nodes), n_src_phys))
    
    odb = openOdb(h1_odb_path, readOnly=True)
    step = odb.steps[odb.steps.keys()[0]]
    
    # Frame 29 (U1 = 0.010143 mm)
    target_u1 = 0.0101433
    best_f_idx = 29
    for i, f in enumerate(step.frames):
        if abs(float(f.frameValue) - target_u1) < 1e-5:
            best_f_idx = i
            break
            
    best_frame = step.frames[best_f_idx]
    actual_handoff_u1 = float(best_frame.frameValue)
    print("Source handoff state: Frame %d, U1 = %.6f mm" % (best_f_idx, actual_handoff_u1))
    
    # Extract source nodal U and d
    src_u_dict = {}
    u_field = best_frame.fieldOutputs['U']
    for v in u_field.values:
        data = v.data
        u1 = float(data[0])
        u2 = float(data[1])
        d = float(data[2]) if len(data) >= 3 else 0.0
        src_u_dict[v.nodeLabel] = (u1, u2, max(0.0, min(1.0, d)))
        
    odb.close()
    
    # Precompute source element strain energy history at all 4 Gauss points
    print("Computing source element Gauss-point history fields...")
    E = 210.0
    nu = 0.3
    c12 = E*nu / ((1.0 + nu)*(1.0 - 2.0*nu))
    c33 = E / (2.0*(1.0 + nu))
    g_local = [-1.0/math.sqrt(3.0), 1.0/math.sqrt(3.0)]
    
    src_H_gp = {} # eid -> list of 4 H values
    src_gps = {}  # eid -> list of 4 (gx, gy)
    
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
        
    print("Source H_max: %.6f kN/mm^2" % max([max(v) for v in src_H_gp.values()]))
    
    # 2. Build Stage D Target Mesh (Nx = 135, Ny = 136, N_phys = 18360)
    sys.path.append(os.path.join(ROOT, "scripts/transfer"))
    from generate_stage_d_target_mesh import generate_nonmatching_stage_d_mesh
    tgt_mesh = generate_nonmatching_stage_d_mesh(out_dir)
    
    tgt_nodes = tgt_mesh["nodes"]
    tgt_elems = tgt_mesh["elements"]
    n_tgt_phys = tgt_mesh["num_elements"]
    
    # 3. Transfer Primary Nodal State (u1, u2, d)
    print("Interpolating primary nodal state to %d target nodes..." % len(tgt_nodes))
    tgt_u_dict = {}
    
    for nid, (tx, ty) in tgt_nodes.items():
        eid, xi, eta = find_host_in_unstructured_quads(src_nodes, src_elems, tx, ty)
        conn = src_elems[eid]
        
        n1 = 0.25 * (1.0 - xi) * (1.0 - eta)
        n2 = 0.25 * (1.0 + xi) * (1.0 - eta)
        n3 = 0.25 * (1.0 + xi) * (1.0 + eta)
        n4 = 0.25 * (1.0 - xi) * (1.0 + eta)
        
        u1_vals = [src_u_dict[n][0] for n in conn if n in src_u_dict]
        u2_vals = [src_u_dict[n][1] for n in conn if n in src_u_dict]
        d_vals  = [src_u_dict[n][2] for n in conn if n in src_u_dict]
        
        u1_interp = n1*u1_vals[0] + n2*u1_vals[1] + n3*u1_vals[2] + n4*u1_vals[3]
        u2_interp = n1*u2_vals[0] + n2*u2_vals[1] + n3*u2_vals[2] + n4*u2_vals[3]
        d_interp  = n1*d_vals[0]  + n2*d_vals[1]  + n3*d_vals[2]  + n4*d_vals[3]
        
        tgt_u_dict[nid] = (u1_interp, u2_interp, max(0.0, min(1.0, d_interp)))
        
    print("Transferred Nodal Fields:")
    u1_t = [v[0] for v in tgt_u_dict.values()]
    u2_t = [v[1] for v in tgt_u_dict.values()]
    d_t  = [v[2] for v in tgt_u_dict.values()]
    print("  Target U1 range: [%.6f, %.6f] mm" % (min(u1_t), max(u1_t)))
    print("  Target U2 range: [%.6f, %.6f] mm" % (min(u2_t), max(u2_t)))
    print("  Target  d range: [%.6f, %.6f]" % (min(d_t), max(d_t)))
    
    # 4. Transfer Integration-Point History H via HOST_NEAREST_GP
    print("Mapping integration-point history H to %d target elements via HOST_NEAREST_GP..." % n_tgt_phys)
    tgt_H_gp = np.zeros((n_tgt_phys, 4))
    
    for eid, conn in tgt_elems.items():
        coords = [tgt_nodes[n] for n in conn]
        tgt_gps = compute_element_gauss_points(tgt_nodes, conn)
        
        for pt_idx, (gx, gy) in enumerate(tgt_gps):
            host_e, _, _ = find_host_in_unstructured_quads(src_nodes, src_elems, gx, gy)
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
                    
            tgt_H_gp[eid - 1, pt_idx] = max(0.0, h_src_vals[best_k])
            
    print("Target H_max at Gauss points: %.6f kN/mm^2" % np.max(tgt_H_gp))
    
    # 5. Write Boundary Include Files:
    # A. PRIMARY_STATE_BOUNDARY (Displacements DOFs 1,2 and Phase DOF 3)
    bc_primary_path = os.path.join(out_dir, "STAGE_D_PRIMARY_STATE_BOUNDARY.inp")
    with open(bc_primary_path, "w") as fp:
        fp.write("** STAGE D: Primary Nodal State Boundary Installation\n")
        fp.write("** U1, U2 for Displacement Nodes (Layer 2) & U3 for Phase Nodes (Layer 1)\n")
        for nid, (u1, u2, d) in tgt_u_dict.items():
            # Phase node (Layer 1): DOF 3
            fp.write("%d, 3, 3, %.12e\n" % (nid, d))
            # Displacement node (Layer 2): DOFs 1, 2
            fp.write("%d, 1, 1, %.12e\n" % (nid, u1))
            fp.write("%d, 2, 2, %.12e\n" % (nid, u2))
        # RP node
        fp.write("99999, 1, 1, %.12e\n" % actual_handoff_u1)
        fp.write("99999, 2, 2, 0.0\n")
    print("Wrote %s" % bc_primary_path)
    
    # B. U3_ONLY_BOUNDARY (Phase field locked during Mech Equilibration)
    bc_u3_path = os.path.join(out_dir, "STAGE_D_U3_ONLY_BOUNDARY.inp")
    with open(bc_u3_path, "w") as fp:
        fp.write("** STAGE D: Phase Field U3 Locking Boundary for Step 2\n")
        for nid, (u1, u2, d) in tgt_u_dict.items():
            fp.write("%d, 3, 3, %.12e\n" % (nid, d))
    print("Wrote %s" % bc_u3_path)
    
    # 6. Write Binary State History File in Fortran Sequential Format (STAGE_D_COMMITTED_STATE.bin, 4,000,016 bytes)
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
            
    rec1_len = N_CAPACITY * 8 # 800,000 bytes
    rec2_len = N_CAPACITY * 4 * 8 # 3,200,000 bytes
    
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
        fp.write("M2CORR_STAGE_D_NONMATCHING_TRANSFER_VAL - Stage-D Pure Nonmatching State Transfer Qualification\n")
        fp.write("** Source: H1 1389686.mmaster02 Frame 29 (U1 = %.6f mm)\n" % actual_handoff_u1)
        fp.write("** Target Mesh: Nonmatching %d quads (Nx=%d, Ny=%d), open slit topology\n" % (
            n_tgt_phys, tgt_mesh["nx"], tgt_mesh["ny"]))
        fp.write("** Staged 4-step sequence: STATE_INSTALL -> MECH_EQUILIBRATION -> PHASE_RELEASE -> CONTINUATION\n")
        fp.write("**\n")
        
        # User Element definitions:
        fp.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=6, VARIABLES=18, UNSYMM\n")
        fp.write("3\n")
        fp.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=6, VARIABLES=18, UNSYMM\n")
        fp.write("1, 2\n")
        
        # Node section
        fp.write("*NODE\n")
        for nid, (x, y) in tgt_nodes.items():
            fp.write("%d, %.8f, %.8f\n" % (nid, x, y))
        fp.write("99999, 0.0, 0.500000\n")
        
        # Element Layer 1 (Phase quads 1..N_phys)
        fp.write("*ELEMENT, TYPE=U1, ELSET=E_QUAD_PHASE\n")
        for eid, conn in tgt_elems.items():
            fp.write("%d, %d, %d, %d, %d\n" % (eid, conn[0], conn[1], conn[2], conn[3]))
            
        # Element Layer 2 (Mechanical quads N_phys+1..2*N_phys)
        fp.write("*ELEMENT, TYPE=U2, ELSET=E_QUAD_MECH\n")
        for eid, conn in tgt_elems.items():
            fp.write("%d, %d, %d, %d, %d\n" % (eid + n_tgt_phys, conn[0], conn[1], conn[2], conn[3]))
            
        # Node sets
        fp.write("*NSET, NSET=N_BOTTOM\n")
        for i, nid in enumerate(tgt_mesh["bot_nodes"]):
            fp.write("%d%s" % (nid, ",\n" if (i+1)%10==0 or i==len(tgt_mesh["bot_nodes"])-1 else ", "))
            
        fp.write("*NSET, NSET=N_TOP\n")
        for i, nid in enumerate(tgt_mesh["top_nodes"]):
            fp.write("%d%s" % (nid, ",\n" if (i+1)%10==0 or i==len(tgt_mesh["top_nodes"])-1 else ", "))
            
        fp.write("*NSET, NSET=N_RP\n")
        fp.write("99999\n")
        
        # UEL Properties
        fp.write("*UEL PROPERTY, ELSET=E_QUAD_PHASE\n")
        fp.write("0.015, 0.0027, 210.0, 0.3, 1e-07, %d.0\n" % n_tgt_phys)
        fp.write("*UEL PROPERTY, ELSET=E_QUAD_MECH\n")
        fp.write("0.015, 0.0027, 210.0, 0.3, 1e-07, %d.0\n" % n_tgt_phys)
        
        # Rigid Top Edge Equations: individual ties
        for nid in tgt_mesh["top_nodes"]:
            fp.write("*EQUATION\n")
            fp.write("2\n")
            fp.write("%d, 1, 1.0, 99999, 1, -1.0\n" % nid)
            
        # STEP 1: State Installation
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
        
        # STEP 2: Mechanical Equilibration
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
        
        # STEP 3: Phase Field Release
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
        
        # STEP 4: Continuation Loading to U1 = 0.050 mm
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
        fp.write("*NODE OUTPUT, NSET=N_TOP\n")
        fp.write("U, RF\n")
        fp.write("*NODE OUTPUT, NSET=N_BOTTOM\n")
        fp.write("U, RF\n")
        fp.write("*NODE OUTPUT, NSET=N_RP\n")
        fp.write("U, RF\n")
        fp.write("*NODE PRINT, FREQ=1\n")
        fp.write("U, RF\n")
        fp.write("*EL PRINT, FREQ=1, ELSET=E_QUAD_MECH\n")
        fp.write("SDV14, SDV15, SDV16\n")
        fp.write("*END STEP\n")
        
    print("Wrote complete restart INP: %s" % inp_deck_path)
    
    # 8. Copy UEL file and write submit_job.pbs
    r7_uel_path = os.path.join(ROOT, "models/generated/mode_ii/production_control_batch/M2CORR_PK10R1_SAMEMESH_RESTART_VALIDATION_R7/f44_mixed_uel_restart_stateinit.for")
    tgt_uel_path = os.path.join(out_dir, "f44_mixed_uel_restart_stateinit.for")
    with open(r7_uel_path, "r") as fp:
        uel_code = fp.read()
        
    # Replace hardcoded binary filename with STAGE_D_COMMITTED_STATE.bin
    uel_code_patched = uel_code.replace("PK10R1_INC29_COMMITTED_STATE_REPLAY_RECONSTRUCTED.bin", "STAGE_D_COMMITTED_STATE.bin")
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
        fp.write("#PBS -M pruthviraj.chavda@mailbox.tu-freiberg.de\n")
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
    build_stage_d_package()

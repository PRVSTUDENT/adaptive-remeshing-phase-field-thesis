#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate Same-Target-Mesh Identity Staged Restart Package:
M2CORR_STAGE_D_SAME_TARGET_IDENTITY_RESTART_VAL
Sourced from Frame 17 of 1390447.mmaster02 (U1 = 0.01051289 mm)
Matching exact 1-difference staged restart architecture of 1390279.mmaster02
"""

import os
import sys
import struct
import numpy as np
from odbAccess import openOdb

def generate_package():
    odb_path = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.odb"
    src_inp = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL.inp"
    out_dir = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_SAME_TARGET_IDENTITY_RESTART_VAL"
    
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    print("================================================================================")
    print("EXTRACTING SOURCE STATE FROM 1390447 (FRAME 17)")
    print("================================================================================")
    
    odb = openOdb(odb_path, readOnly=True)
    step = odb.steps['ShearStep']
    frame = step.frames[17]
    
    step_time = float(frame.frameValue)
    inc_num = frame.incrementNumber
    print("Source Step: %s | Frame: 17 | Inc: %d | Time: %.7f" % (step.name, inc_num, step_time))

    # Read nodes and connectivity from source INP
    nodes = {} # node_id -> (x, y)
    elements = {} # elem_id -> [n1, n2, n3, n4]
    
    with open(src_inp, 'r') as fp:
        lines = fp.readlines()

    mode = None
    for line in lines:
        line_s = line.strip()
        if line_s.startswith('*'):
            if line_s.startswith('*NODE') and not line_s.startswith('*NODE OUTPUT') and not line_s.startswith('*NODE FILE') and not line_s.startswith('*NODE PRINT'):
                mode = 'NODE'
            elif line_s.startswith('*ELEMENT, TYPE=U1') or line_s.startswith('*ELEMENT, TYPE=U2'):
                mode = 'ELEM'
            elif line_s.startswith('*ELEMENT, TYPE=CPS4'):
                mode = 'VIS_ELEM'
            else:
                mode = None
            continue
        
        if mode == 'NODE':
            if line_s and not line_s.startswith('*'):
                parts = [p.strip() for p in line_s.split(',')]
                try:
                    nid = int(parts[0])
                    if nid < 99999: # Only physical mesh nodes
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
                except ValueError:
                    pass
        elif mode == 'ELEM':
            if line_s and not line_s.startswith('*'):
                parts = [p.strip() for p in line_s.split(',')]
                try:
                    eid = int(parts[0])
                    if eid <= 8836:
                        conn = [int(p) for p in parts[1:5]]
                        elements[eid] = conn
                except ValueError:
                    pass

    print("Read %d physical nodes and %d physical elements from source INP" % (len(nodes), len(elements)))

    # Read nodal displacements and damage from ODB
    nodal_u1 = {}
    nodal_u2 = {}
    nodal_d = {}

    u_field = frame.fieldOutputs['U']
    for v in u_field.values:
        nid = v.nodeLabel
        nodal_u1[nid] = float(v.data[0])
        nodal_u2[nid] = float(v.data[1])
        if len(v.data) >= 3:
            nodal_d[nid] = float(v.data[2])
        else:
            nodal_d[nid] = 0.0

    odb.close()

    rp_u1 = nodal_u1.get(99999, step_time * 0.050)
    print("Handoff RP U1: %.7f mm (Total prescribed = 0.050 mm)" % rp_u1)
    print("Max nodal damage d_max: %.7f" % max(nodal_d.values()))

    # Compute exact 4-GP H for each element
    E_MOD = 210.0
    E_NU = 0.3
    C11_0 = E_MOD * (1.0 - E_NU) / ((1.0 + E_NU) * (1.0 - 2.0 * E_NU))
    C12_0 = E_MOD * E_NU / ((1.0 + E_NU) * (1.0 - 2.0 * E_NU))
    C33_0 = E_MOD / (2.0 * (1.0 + E_NU))

    xg4 = [-0.577350269189626, 0.577350269189626, 0.577350269189626, -0.577350269189626]
    yg4 = [-0.577350269189626, -0.577350269189626, 0.577350269189626, 0.577350269189626]

    elem_h = {} # elem_id -> [h1, h2, h3, h4]
    elem_d = {} # elem_id -> [d1, d2, d3, d4]

    for eid, conn in elements.items():
        c_x = [nodes[n][0] for n in conn]
        c_y = [nodes[n][1] for n in conn]
        
        u_elem = []
        for n in conn:
            u_elem.extend([nodal_u1.get(n, 0.0), nodal_u2.get(n, 0.0)])
        u_elem = np.array(u_elem)

        d_elem = [nodal_d.get(n, 0.0) for n in conn]
        elem_d[eid] = d_elem

        h_vals = []
        for kpt in range(4):
            xi = xg4[kpt]
            eta = yg4[kpt]

            dn_dxi = np.array([
                -0.25 * (1.0 - eta),
                 0.25 * (1.0 - eta),
                 0.25 * (1.0 + eta),
                -0.25 * (1.0 + eta)
            ])
            dn_deta = np.array([
                -0.25 * (1.0 - xi),
                -0.25 * (1.0 + xi),
                 0.25 * (1.0 + xi),
                 0.25 * (1.0 - xi)
            ])

            j11 = np.sum(dn_dxi * c_x)
            j12 = np.sum(dn_dxi * c_y)
            j21 = np.sum(dn_deta * c_x)
            j22 = np.sum(dn_deta * c_y)

            detj = j11 * j22 - j12 * j21
            invj11 =  j22 / detj
            invj12 = -j12 / detj
            invj21 = -j21 / detj
            invj22 =  j11 / detj

            B = np.zeros((3, 8))
            for i in range(4):
                B[0, 2*i]   = invj11 * dn_dxi[i] + invj12 * dn_deta[i]
                B[1, 2*i+1] = invj21 * dn_dxi[i] + invj22 * dn_deta[i]
                B[2, 2*i]   = invj21 * dn_dxi[i] + invj22 * dn_deta[i]
                B[2, 2*i+1] = invj11 * dn_dxi[i] + invj12 * dn_deta[i]

            strain = B.dot(u_elem)
            e11 = strain[0]
            e22 = strain[1]
            e12 = 0.5 * strain[2]
            tr_e = e11 + e22
            e_pos = max(tr_e, 0.0)

            pos_m = 0.5 * C12_0 * (e_pos**2) + C33_0 * (e11**2 + e22**2 + 2.0 * (e12**2))
            h_vals.append(pos_m)

        elem_h[eid] = h_vals

    max_h = max(max(h) for h in elem_h.values())
    print("Max GP strain history H_max: %.7f MPa" % (max_h * 1000.0))

    # Write STAGE_D_COMMITTED_STATE.bin (Fortran unformatted sequential binary)
    bin_path = os.path.join(out_dir, "STAGE_D_COMMITTED_STATE.bin")
    
    n_capacity = 100000
    phase_arr = np.zeros((n_capacity, 4), dtype=np.float64, order='F')
    h_arr = np.zeros((n_capacity, 4), dtype=np.float64, order='F')

    for eid in range(1, 8837):
        for k in range(4):
            phase_arr[eid-1, k] = elem_d[eid][k]
            h_arr[eid-1, k] = elem_h[eid][k]

    record1_bytes = phase_arr.tobytes(order='F')
    record2_bytes = h_arr.tobytes(order='F')
    rec_len = len(record1_bytes) # 3,200,000 bytes

    with open(bin_path, 'wb') as fp:
        # Record 1
        fp.write(struct.pack('i', rec_len))
        fp.write(record1_bytes)
        fp.write(struct.pack('i', rec_len))
        # Record 2
        fp.write(struct.pack('i', rec_len))
        fp.write(record2_bytes)
        fp.write(struct.pack('i', rec_len))

    print("Created binary state file: %s (%d bytes)" % (bin_path, os.path.getsize(bin_path)))

    # Node sets
    bot_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - (-0.5)) < 1e-6]
    top_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 0.5) < 1e-6]
    left_nodes = [nid for nid, (x, y) in nodes.items() if abs(x - (-0.5)) < 1e-6]
    right_nodes = [nid for nid, (x, y) in nodes.items() if abs(x - 0.5) < 1e-6]

    # Write STAGE_D_PRIMARY_STATE_BOUNDARY.inp (Exactly matching 1390279 layout)
    bnd_primary_path = os.path.join(out_dir, "STAGE_D_PRIMARY_STATE_BOUNDARY.inp")
    with open(bnd_primary_path, 'w') as fp:
        fp.write("** STAGE D: Primary Nodal State Boundary Installation (Identity Transfer)\n")
        for nid in sorted(nodes.keys()):
            fp.write("%d, 3, 3, %.12e\n" % (nid, nodal_d.get(nid, 0.0)))
            if nid not in top_nodes and nid not in bot_nodes:
                fp.write("%d, 1, 1, %.12e\n" % (nid, nodal_u1.get(nid, 0.0)))
                fp.write("%d, 2, 2, %.12e\n" % (nid, nodal_u2.get(nid, 0.0)))
            elif nid in bot_nodes:
                fp.write("%d, 1, 1, 0.000000000000e+00\n" % nid)
                fp.write("%d, 2, 2, 0.000000000000e+00\n" % nid)
            elif nid in top_nodes:
                fp.write("%d, 2, 2, %.12e\n" % (nid, nodal_u2.get(nid, 0.0)))
        # RP Boundary
        fp.write("99999, 1, 1, %.12e\n" % rp_u1)
        fp.write("99999, 2, 2, 0.000000000000e+00\n")
    print("Created %s" % bnd_primary_path)

    # Write STAGE_D_U3_ONLY_BOUNDARY.inp
    bnd_u3_path = os.path.join(out_dir, "STAGE_D_U3_ONLY_BOUNDARY.inp")
    with open(bnd_u3_path, 'w') as fp:
        fp.write("** STAGE D: Phase Field U3 Locking Boundary for Step 2 (Identity Transfer)\n")
        for nid in sorted(nodes.keys()):
            fp.write("%d, 3, 3, %.12e\n" % (nid, nodal_d.get(nid, 0.0)))
    print("Created %s" % bnd_u3_path)

    # Create MODE_STAGED.flag
    with open(os.path.join(out_dir, "MODE_STAGED.flag"), 'w') as fp:
        fp.write("EXPLICIT_MODE = 1 (STAGED_TRANSFER_RESTART)\n")

    # Generate the 4-step Staged Restart INP
    inp_name = "M2CORR_STAGE_D_SAME_TARGET_IDENTITY_RESTART_VAL.inp"
    inp_path = os.path.join(out_dir, inp_name)
    
    generate_staged_inp(inp_path, nodes, elements, bot_nodes, top_nodes, left_nodes, right_nodes, rp_u1)
    print("Generated staged restart INP: %s" % inp_path)

    # Copy UEL file
    src_uel = "models/generated/mode_ii/production_state_transfer_batch/M2CORR_STAGE_D_CONTINUOUS_TARGET_CONTROL_VAL/f44_mixed_uel_restart_stateinit.for"
    dst_uel = os.path.join(out_dir, "f44_mixed_uel_restart_stateinit.for")
    with open(src_uel, 'r') as fp_in, open(dst_uel, 'w') as fp_out:
        fp_out.write(fp_in.read())
    print("Copied UEL subroutine to: %s" % dst_uel)

    # Generate submit_job.pbs
    pbs_path = os.path.join(out_dir, "submit_job.pbs")
    generate_pbs(pbs_path, "M2CORR_STAGE_D_SAME_TARGET_IDENTITY_RESTART_VAL")
    print("Generated PBS script: %s" % pbs_path)

def generate_staged_inp(inp_path, nodes, elements, bot_nodes, top_nodes, left_nodes, right_nodes, rp_u1_handoff):
    with open(inp_path, 'w') as fp:
        fp.write("*HEADING\n")
        fp.write("M2CORR_STAGE_D_SAME_TARGET_IDENTITY_RESTART_VAL - Same-Target-Mesh Identity Staged Restart\n")
        fp.write("** Target Mesh: Exact Stage-D Sliver-Free Graded Nonmatching 8836 quads (Nx=94, Ny=94)\n")
        fp.write("** Handoff Displacement U1 = %.7f mm (Exact Frame 17 of 1390447.mmaster02)\n" % rp_u1_handoff)
        fp.write("** Staged Sequence: STATE_INSTALL -> MECH_EQUILIBRATION -> PHASE_RELEASE -> CONTINUATION\n")
        fp.write("** Explicit Execution Mode: PROPS(7) = 1.0 (Staged Transfer Restart)\n")
        fp.write("**\n")
        fp.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=7, VARIABLES=18, UNSYMM\n")
        fp.write("3\n")
        fp.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, I PROPERTIES=0, PROPERTIES=7, VARIABLES=18, UNSYMM\n")
        fp.write("1, 2\n")
        fp.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            fp.write("%d, %.8f, %.8f\n" % (nid, nodes[nid][0], nodes[nid][1]))
        fp.write("99999, 0.00000000, 0.00000000\n")

        # Elements
        fp.write("*ELEMENT, TYPE=U1, ELSET=E_QUAD_PHASE\n")
        for eid in sorted(elements.keys()):
            c = elements[eid]
            fp.write("%d, %d, %d, %d, %d\n" % (eid, c[0], c[1], c[2], c[3]))

        fp.write("*ELEMENT, TYPE=U2, ELSET=E_QUAD_MECH\n")
        for eid in sorted(elements.keys()):
            c = elements[eid]
            fp.write("%d, %d, %d, %d, %d\n" % (eid + 8836, c[0], c[1], c[2], c[3]))

        # Node sets
        fp.write("*NSET, NSET=N_BOTTOM\n")
        write_set(fp, bot_nodes)
        fp.write("*NSET, NSET=N_TOP\n")
        write_set(fp, top_nodes)
        fp.write("*NSET, NSET=N_LEFT\n")
        write_set(fp, left_nodes)
        fp.write("*NSET, NSET=N_RIGHT\n")
        write_set(fp, right_nodes)
        fp.write("*NSET, NSET=N_RP\n99999\n")
        fp.write("*NSET, NSET=N_ALL_PHYS\n")
        write_set(fp, sorted(nodes.keys()))

        # Properties (Mode 1: Staged Transfer Restart)
        fp.write("*UEL PROPERTY, ELSET=E_QUAD_PHASE\n")
        fp.write("0.015, 0.0027, 210.0, 0.3, 1e-07, 8836.0, 1.0\n")
        fp.write("*UEL PROPERTY, ELSET=E_QUAD_MECH\n")
        fp.write("0.015, 0.0027, 210.0, 0.3, 1e-07, 8836.0, 1.0\n")

        # Equations (Top surface coupled to RP, exactly matching 1390279)
        for nid in top_nodes:
            fp.write("*EQUATION\n")
            fp.write("2\n")
            fp.write("%d, 1, 1.0, 99999, 1, -1.0\n" % nid)

        # ----------------------------------------------------------------------
        # STEP 1: STATE_INSTALL (Install Transferred Fields)
        # ----------------------------------------------------------------------
        fp.write("** ==========================================================\n")
        fp.write("** STEP 1: State Installation & Binary History Ingestion\n")
        fp.write("** ==========================================================\n")
        fp.write("*STEP, NAME=STATE_INSTALL, NLGEOM=NO, INC=10\n")
        fp.write("*STATIC\n")
        fp.write("1.0, 1.0, 1.0e-5, 1.0\n")
        fp.write("*BOUNDARY, OP=NEW\n")
        fp.write("*INCLUDE, INPUT=STAGE_D_PRIMARY_STATE_BOUNDARY.inp\n")
        fp.write("*OUTPUT, FIELD, FREQ=1\n")
        fp.write("*NODE OUTPUT\nU, RF\n")
        fp.write("*END STEP\n")

        # ----------------------------------------------------------------------
        # STEP 2: MECH_EQUILIBRATION (Equilibrate Displacements with Clamped d)
        # ----------------------------------------------------------------------
        fp.write("** ==========================================================\n")
        fp.write("** STEP 2: Mechanical Equilibration (Phase Field Locked)\n")
        fp.write("** ==========================================================\n")
        fp.write("*STEP, NAME=MECH_EQUILIBRATION, NLGEOM=NO, INC=100\n")
        fp.write("*STATIC\n")
        fp.write("1.0, 1.0, 1.0e-5, 1.0\n")
        fp.write("*BOUNDARY, OP=NEW\n")
        fp.write("N_BOTTOM, 1, 2, 0.0\n")
        fp.write("N_RP, 1, 1, %.12e\n" % rp_u1_handoff)
        fp.write("N_RP, 2, 2, 0.0\n")
        fp.write("*INCLUDE, INPUT=STAGE_D_U3_ONLY_BOUNDARY.inp\n")
        fp.write("*OUTPUT, FIELD, FREQ=1\n")
        fp.write("*NODE OUTPUT\nU, RF\n")
        fp.write("*END STEP\n")

        # ----------------------------------------------------------------------
        # STEP 3: PHASE_RELEASE (Release Phase Clamping)
        # ----------------------------------------------------------------------
        fp.write("** ==========================================================\n")
        fp.write("** STEP 3: Phase Field Release & Equilibrium\n")
        fp.write("** ==========================================================\n")
        fp.write("*STEP, NAME=PHASE_RELEASE, NLGEOM=NO, INC=100\n")
        fp.write("*STATIC\n")
        fp.write("1.0, 1.0, 1.0e-5, 1.0\n")
        fp.write("*BOUNDARY, OP=NEW\n")
        fp.write("N_BOTTOM, 1, 2, 0.0\n")
        fp.write("N_RP, 1, 1, %.12e\n" % rp_u1_handoff)
        fp.write("N_RP, 2, 2, 0.0\n")
        fp.write("*OUTPUT, FIELD, FREQ=1\n")
        fp.write("*NODE OUTPUT\nU, RF\n")
        fp.write("*END STEP\n")

        # ----------------------------------------------------------------------
        # STEP 4: CONTINUATION (Monotonic shear from U1_handoff to 0.050 mm)
        # ----------------------------------------------------------------------
        fp.write("** ==========================================================\n")
        fp.write("** STEP 4: Continuation Monotonic Shear to U1 = 0.050 mm\n")
        fp.write("** ==========================================================\n")
        fp.write("*STEP, NAME=CONTINUATION, NLGEOM=NO, INC=10000\n")
        fp.write("*STATIC\n")
        fp.write("0.001, 1.0, 1.0e-9, 0.02\n")
        fp.write("*BOUNDARY, OP=MOD\n")
        fp.write("N_RP, 1, 1, 0.050000\n")
        fp.write("N_RP, 2, 2, 0.0\n")
        fp.write("*OUTPUT, FIELD, FREQ=1\n")
        fp.write("*NODE OUTPUT\nU, RF\n")
        fp.write("*NODE PRINT, FREQ=1\nU, RF\n")
        fp.write("*EL PRINT, FREQ=1, ELSET=E_QUAD_MECH\n")
        fp.write("SDV14, SDV15, SDV16\n")
        fp.write("*END STEP\n")

def write_set(fp, node_list):
    for i in range(0, len(node_list), 10):
        chunk = node_list[i:i+10]
        fp.write(", ".join(str(n) for n in chunk) + "\n")

def generate_pbs(pbs_path, job_name):
    content = """#!/bin/bash
#PBS -N %s
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -o pbs.out
#PBS -e pbs.err

cd $PBS_O_WORKDIR

module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

echo "Job started on $(hostname) at $(date)"

abaqus job=%s input=%s.inp user=f44_mixed_uel_restart_stateinit.for cpus=1 interactive

echo "Job finished at $(date) with exit code $?"
""" % ("M2_STAGE_D_ID_RST", job_name, job_name)
    with open(pbs_path, 'w') as fp:
        fp.write(content)

if __name__ == "__main__":
    generate_package()

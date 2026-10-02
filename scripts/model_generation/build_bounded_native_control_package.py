#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Build M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL package.
Extracts Frame 29 state from native H1 ODB (1389686) on H1 canonical mesh (12064 quads),
generates INP with 4-stage sequence, generates binary state file with node-indexed phase,
and sets up PBS launcher for dual-job campaign.
"""

import os
import sys
import struct
from odbAccess import openOdb

def build_package():
    h1_odb_path = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.odb"
    h1_base_inp = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_verification_batch/M2CORR_H1_FREEU2_FULL_U050/M2CORR_H1_FREEU2_FULL_U050.inp"
    
    out_dir = "/home/pr21vyci/projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch/M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
    
    print("================================================================================")
    print("BUILDING NATIVE BOUNDED CONTROL PACKAGE: M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL")
    print("================================================================================")
    
    odb = openOdb(h1_odb_path, readOnly=True)
    step = odb.steps['ShearStep']
    frame29 = step.frames[29]
    
    print("Extracting Frame 29 state (Time = %.6f, U1 = 0.0101433 mm)..." % frame29.frameValue)
    
    u_field = frame29.fieldOutputs['U']
    sdv_field = frame29.fieldOutputs['SDV'] if 'SDV' in frame29.fieldOutputs else None
    
    # 1. Read nodal displacements & phase
    # Nodal U: u1, u2, u3 (d)
    nodal_state = {}
    for v in u_field.values:
        nid = v.nodeLabel
        u1 = v.data[0]
        u2 = v.data[1]
        u3 = v.data[2] if len(v.data) >= 3 else 0.0
        nodal_state[nid] = (u1, u2, u3)
        
    print("Extracted %d nodal states. Max d = %.6f" % (len(nodal_state), max(v[2] for v in nodal_state.values())))
    
    # 2. Write STAGE_D_PRIMARY_STATE_BOUNDARY.inp for H1 mesh
    primary_bc_path = os.path.join(out_dir, "STAGE_D_PRIMARY_STATE_BOUNDARY.inp")
    u3_bc_path = os.path.join(out_dir, "STAGE_D_U3_ONLY_BOUNDARY.inp")
    
    with open(primary_bc_path, "w") as fp_prim, open(u3_bc_path, "w") as fp_u3:
        fp_prim.write("** Primary State Initial Boundary Conditions for H1 Mesh\n")
        fp_u3.write("** U3-Only Phase Boundary Conditions for H1 Mesh\n")
        for nid in sorted(nodal_state.keys()):
            if nid == 12384: # Reference Point node
                continue
            u1, u2, u3 = nodal_state[nid]
            fp_prim.write("%d, 1, 1, %.12e\n" % (nid, u1))
            fp_prim.write("%d, 2, 2, %.12e\n" % (nid, u2))
            fp_prim.write("%d, 3, 3, %.12e\n" % (nid, u3))
            fp_u3.write("%d, 3, 3, %.12e\n" % (nid, u3))
            
    print("Written primary and U3 boundary files.")

    # 3. Read H1 mesh connectivity from base INP
    phase_elem_conn = {}
    with open(h1_base_inp, "r") as fp:
        lines = fp.readlines()
        
    reading_conn = False
    for line in lines:
        l = line.strip()
        if l.startswith("*ELEMENT") and "TYPE=U1" in l:
            reading_conn = True
            continue
        elif l.startswith("*ELEMENT") or l.startswith("*"):
            reading_conn = False
            
        if reading_conn and l and not l.startswith("**"):
            parts = [int(p.strip()) for p in l.split(",")]
            eid = parts[0]
            nodes = parts[1:5]
            phase_elem_conn[eid] = nodes
            
    print("Read %d phase elements from base INP." % len(phase_elem_conn))

    # 4. Extract GP history H from ODB
    # In H1 ODB, SDV13/SDV16 is H
    # If not in ODB, compute from strains or extract from SDV
    gp_H = {}
    if 'SDV_SDV16' in frame29.fieldOutputs:
        f_sdv = frame29.fieldOutputs['SDV_SDV16']
        for v in f_sdv.values:
            eid = v.elementLabel
            if eid not in gp_H:
                gp_H[eid] = [0.0]*4
            # integration point
            ip = v.integrationPoint - 1
            if 0 <= ip < 4:
                gp_H[eid][ip] = v.data
    elif 'SDV16' in frame29.fieldOutputs:
        f_sdv = frame29.fieldOutputs['SDV16']
        for v in f_sdv.values:
            eid = v.elementLabel
            if eid not in gp_H:
                gp_H[eid] = [0.0]*4
            ip = v.integrationPoint - 1
            if 0 <= ip < 4:
                gp_H[eid][ip] = v.data

    # 5. Generate STAGE_D_COMMITTED_STATE.bin
    # Record 1: SV_ELEM_NODAL_PHASE(100000, 4)
    # Record 2: SV_H_COMMITTED(100000, 4)
    bin_path = os.path.join(out_dir, "STAGE_D_COMMITTED_STATE.bin")
    elem_nodal_phase = [[0.0]*4 for _ in range(100000)]
    elem_h_committed = [[0.0]*4 for _ in range(100000)]
    
    for eid, nodes in phase_elem_conn.items():
        if eid <= 100000:
            for loc_i, nid in enumerate(nodes):
                elem_nodal_phase[eid-1][loc_i] = nodal_state.get(nid, (0, 0, 0))[2]
            if eid in gp_H:
                for k in range(4):
                    elem_h_committed[eid-1][k] = gp_H[eid][k]

    with open(bin_path, "wb") as fp:
        # Record 1 (Fortran unformatted: 4-byte header + 400000 doubles + 4-byte footer)
        rec1_bytes = struct.pack("=400000d", *[elem_nodal_phase[e][k] for e in range(100000) for k in range(4)])
        rec1_len = len(rec1_bytes)
        fp.write(struct.pack("=i", rec1_len))
        fp.write(rec1_bytes)
        fp.write(struct.pack("=i", rec1_len))
        
        # Record 2
        rec2_bytes = struct.pack("=400000d", *[elem_h_committed[e][k] for e in range(100000) for k in range(4)])
        rec2_len = len(rec2_bytes)
        fp.write(struct.pack("=i", rec2_len))
        fp.write(rec2_bytes)
        fp.write(struct.pack("=i", rec2_len))
        
    print("Generated binary state file: %s (Size: %d bytes)" % (bin_path, os.path.getsize(bin_path)))

    # 6. Build INP for H1 Native Control
    inp_path = os.path.join(out_dir, "M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL.inp")
    with open(h1_base_inp, "r") as fp_in, open(inp_path, "w") as fp_out:
        for line in fp_in:
            if line.strip().upper().startswith("*STEP"):
                break
            fp_out.write(line)
            
        # Append 4-step sequence
        steps_text = """** ==========================================================
** STEP 1: State Install (Nodal Displacement & Phase Bound)
** ==========================================================
*STEP, NAME=STATE_INSTALL, NLGEOM=NO, INC=100
*STATIC
1.0, 1.0, 1.0e-5, 1.0
*BOUNDARY, OP=NEW
*INCLUDE, INPUT=STAGE_D_PRIMARY_STATE_BOUNDARY.inp
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT
U, RF
*END STEP

** ==========================================================
** STEP 2: Mechanical Equilibration (Phase Field Locked)
** ==========================================================
*STEP, NAME=MECH_EQUILIBRATION, NLGEOM=NO, INC=100
*STATIC
1.0, 1.0, 1.0e-5, 1.0
*BOUNDARY, OP=NEW
bottom_nodes, 1, 2, 0.0
RP, 1, 1, 1.014330051839e-02
RP, 2, 2, 0.0
*INCLUDE, INPUT=STAGE_D_U3_ONLY_BOUNDARY.inp
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT
U, RF
*END STEP

** ==========================================================
** STEP 3: Phase Field Release & Equilibrium
** ==========================================================
*STEP, NAME=PHASE_RELEASE, NLGEOM=NO, INC=100
*STATIC
1.0, 1.0, 1.0e-5, 1.0
*BOUNDARY, OP=NEW
bottom_nodes, 1, 2, 0.0
RP, 1, 1, 1.014330051839e-02
RP, 2, 2, 0.0
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT
U, RF
*END STEP

** ==========================================================
** STEP 4: Continuation Monotonic Shear to U1 = 0.050 mm
** ==========================================================
*STEP, NAME=CONTINUATION, NLGEOM=NO, INC=10000
*STATIC
0.001, 1.0, 1.0e-9, 0.02
*BOUNDARY, OP=MOD
RP, 1, 1, 0.050000
RP, 2, 2, 0.0
*OUTPUT, FIELD, FREQ=1
*NODE OUTPUT
U, RF
*END STEP
"""
        fp_out.write(steps_text)
        
    print("Generated native control INP: %s" % inp_path)
    
    # 7. Write PBS launcher for Native Control
    pbs_path = os.path.join(out_dir, "submit_job.pbs")
    pbs_content = """#PBS -N M2NATIVE_CTRL
#PBS -l select=1:ncpus=1:mem=16gb
#PBS -l walltime=24:00:00
#PBS -q entry_imfdfkmq
#PBS -m abe
#PBS -M pr21vyci@mailserver.tu-freiberg.de
#PBS -o pbs.out
#PBS -e pbs.err

cd $PBS_O_WORKDIR

source /etc/profile
module purge
module load gcc/11.4.0
module load intel/2024.2.0
module load abaqus/2023

echo "[PBS] Starting job $PBS_JOBID on host $(hostname) at $(date)"

abaqus job=M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL user=f44_mixed_uel_restart_stateinit.for cpus=1 interactive
SOLVER_STATUS=$?

echo "[PBS] Solver execution exited with status $SOLVER_STATUS at $(date)"
exit $SOLVER_STATUS
"""
    with open(pbs_path, "w") as fp:
        fp.write(pbs_content)
        
    odb.close()
    print("M2CORR_H1_BOUNDED_NATIVE_CONTROL_VAL package build complete.")

if __name__ == "__main__":
    build_package()

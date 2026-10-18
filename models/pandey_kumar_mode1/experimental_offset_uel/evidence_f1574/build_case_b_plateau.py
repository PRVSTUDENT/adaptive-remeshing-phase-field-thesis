"""
Test Cracked State Reconstruction on the Stable Propagation Plateau (Step 2, Inc 2, u = 0.00258 mm)
"""

from odbAccess import openOdb
import sys
import os
import json

scratch_dir = "/scratch9/pr21vyci/runs/mode1_experimental_offset_diagnostic"
dat_path = os.path.join(scratch_dir, "CaseA_cracked_solve.dat")
odb_path = os.path.join(scratch_dir, "CaseA_cracked_solve.odb")
inp_case_a = os.path.join(scratch_dir, "CaseA_cracked.inp")
csv_plateau = os.path.join(scratch_dir, "offset_state_table_plateau.csv")
csv_out = os.path.join(scratch_dir, "offset_state_table.csv")
inp_plateau = os.path.join(scratch_dir, "CaseB_plateau.inp")

print("=== 1. Extracting Plateau State from Case A (u = 0.00258 mm, Step 2 Inc 2) ===")

with open(dat_path, 'r') as f:
    text = f.read()

tables = text.split("THE FOLLOWING TABLE IS PRINTED FOR ALL NODES")
table5 = tables[5] # Table 5 is Step 2 Inc 2 (u = 0.00258 mm)

nodal_u = {}
for line in table5.splitlines():
    line = line.strip()
    if not line or "Abaqus" in line or "Date" in line or "Time" in line or "PAGE" in line or "Page" in line:
        continue
    if line.startswith("MAXIMUM"):
        break
    if line.startswith("NODE") or line.startswith("MINIMUM") or line.startswith("AT NODE"):
        continue
    parts = line.split()
    if len(parts) >= 4:
        try:
            nid = int(parts[0])
            if 1 <= nid <= 450:
                u1 = float(parts[1])
                u2 = float(parts[2])
                d  = float(parts[3])
                nodal_u[nid] = (u1, u2, d)
        except ValueError:
            pass

print("Extracted nodal U for %d nodes at u = 0.00258 mm" % len(nodal_u))
max_d = max(nodal_u[n][2] for n in nodal_u)
max_d_nid = max(nodal_u.keys(), key=lambda n: nodal_u[n][2])
print("Max damage d = %f at node %d" % (max_d, max_d_nid))

# Extract SDV2 from Step 2 Frame 2
odb = openOdb(odb_path, readOnly=True)
s2 = odb.steps['Step-2']
f2_2 = s2.frames[2] # Frame 2 is Step 2 Inc 2

elem_H = {}
for val in f2_2.fieldOutputs['SDV2'].values:
    eid = val.elementLabel
    phys_eid = eid - 800
    if 1 <= phys_eid <= 400:
        if phys_eid not in elem_H:
            elem_H[phys_eid] = []
        elem_H[phys_eid].append(float(val.data))

odb.close()
print("Extracted history H for %d elements." % len(elem_H))

# Read mesh connectivity
elem_nodes = {}
with open(inp_case_a, 'r') as f:
    in_phase = False
    for line in f:
        ls = line.strip()
        if ls.startswith("*Element, type=U1"):
            in_phase = True
            continue
        elif ls.startswith("*Element, type=U2"):
            in_phase = False
            break
        if in_phase and ls and not ls.startswith("*"):
            p = [int(x.strip()) for x in ls.split(",")]
            elem_nodes[p[0]] = p[1:5]

# Write offset table
for pth in [csv_plateau, csv_out]:
    with open(pth, 'w') as f:
        f.write("EID, U1_1, U2_1, U1_2, U2_2, U1_3, U2_3, U1_4, U2_4, D_1, D_2, D_3, D_4, H_1, H_2, H_3, H_4\n")
        for eid in sorted(elem_nodes.keys()):
            conn = elem_nodes[eid]
            u_vals = []
            d_vals = []
            for nid in conn:
                u_vals.extend([nodal_u[nid][0], nodal_u[nid][1]])
                d_vals.append(nodal_u[nid][2])
            h_vals = elem_H.get(eid, [0.0]*4)
            if len(h_vals) < 4:
                h_vals = (h_vals + [0.0]*4)[:4]
            lp = [str(eid)] + ["{:.12e}".format(x) for x in u_vals] + ["{:.12e}".format(x) for x in d_vals] + ["{:.12e}".format(x) for x in h_vals]
            f.write(", ".join(lp) + "\n")

print("Wrote offset table for plateau checkpoint.")

# Build CaseB_plateau.inp
with open(inp_case_a, 'r') as f:
    deck = f.read()

prefix = deck.split("** STEP 1: Monotonic Loading")[0]

steps = """** ==========================================================
** STEP 1: Zero-Increment State Reconstruction (Delta u = 0.0 mm)
** Evaluates cracked equilibrium at stable plateau (u = 0.00258 mm)
** ==========================================================
*Step, name=Step-1, nlgeom=NO, inc=10
*Static
1.0, 1.0, 1.0E-6, 1.0
*Boundary
N_BOTTOM, 2, 2, 0.0
N_PIN, 1, 1, 0.0
N_TOP, 1, 1, 0.0
N_RP, 2, 2, 0.0
*Output, field, frequency=1
*Node Output, nset=N_RP
U, RF
*Node Output
U, RF
*Element Output, elset=umatelem
SDV, S, E
*Output, history, frequency=1
*Energy Output
ALLSE, ALLIE, ALLWK, ALLFD, ALLCD, ALLVD, ALLPD, ALLAE, ETOTAL
*Node Output, nset=N_RP
U2, RF2
*Node Print, freq=1, nset=N_RP
U2, RF2
*Node Print, freq=1
U
*End Step
** ==========================================================
** STEP 2: Forward Continuation Advance (Delta u = 0.00012 mm, 3 incs to u = 0.00270 mm)
** ==========================================================
*Step, name=Step-2, nlgeom=NO, inc=100
*Static
0.333333333333, 1.0, 1.0E-6, 0.333333333333
*Boundary
N_RP, 2, 2, 0.00012
*Output, field, frequency=1
*Node Output, nset=N_RP
U, RF
*Node Output
U, RF
*Element Output, elset=umatelem
SDV, S, E
*Output, history, frequency=1
*Energy Output
ALLSE, ALLIE, ALLWK, ALLFD, ALLCD, ALLVD, ALLPD, ALLAE, ETOTAL
*Node Output, nset=N_RP
U2, RF2
*Node Print, freq=1, nset=N_RP
U2, RF2
*Node Print, freq=1
U
*End Step
"""

with open(inp_plateau, 'w') as f:
    f.write(prefix + steps)

# Also write to CaseB_cracked.inp so run_case_b_cracked_solve.sh runs it
with open(os.path.join(scratch_dir, "CaseB_cracked.inp"), 'w') as f:
    f.write(prefix + steps)

print("Generated CaseB_plateau.inp and updated CaseB_cracked.inp")

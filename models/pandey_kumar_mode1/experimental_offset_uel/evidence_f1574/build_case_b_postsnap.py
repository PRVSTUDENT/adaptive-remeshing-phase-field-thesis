"""
Build Case B Post-Snap Continuation Model from Authentic Case A Solved State (Step 2, Inc 1, u = 0.00254 mm)
"""

from odbAccess import openOdb
import sys
import os
import json
import numpy as np

scratch_dir = "/scratch9/pr21vyci/runs/mode1_experimental_offset_diagnostic"
dat_path = os.path.join(scratch_dir, "CaseA_cracked_solve.dat")
odb_path = os.path.join(scratch_dir, "CaseA_cracked_solve.odb")
inp_case_a = os.path.join(scratch_dir, "CaseA_cracked.inp")
csv_out_versioned = os.path.join(scratch_dir, "offset_state_table_postsnap.csv")
csv_out = os.path.join(scratch_dir, "offset_state_table.csv")
inp_case_b = os.path.join(scratch_dir, "CaseB_cracked.inp")

print("=== 1. Extracting Authentic Post-Snap State from Case A (u = 0.00254 mm) ===")

# 1. Parse nodal displacements and damage from .dat file (Table 4 is Step 2 Inc 1)
with open(dat_path, 'r') as f:
    text = f.read()

tables = text.split("THE FOLLOWING TABLE IS PRINTED FOR ALL NODES")
print("Found %d total node tables in dat" % (len(tables)-1))
table4 = tables[4] # Table 4 is Step 2, inc 1 (u = 0.00254 mm)

nodal_u = {} # nid -> (u1, u2, d)
for line in table4.splitlines():
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

print("Extracted nodal U for %d physical nodes." % len(nodal_u))
max_d = max(nodal_u[n][2] for n in nodal_u)
max_d_nid = max(nodal_u.keys(), key=lambda n: nodal_u[n][2])
print("Max extracted nodal damage d_0 = %f at node %d" % (max_d, max_d_nid))
print("Node 1: U1 = %e, U2 = %e, U3 = %f" % (nodal_u[1][0], nodal_u[1][1], nodal_u[1][2]))

# 2. Extract Gauss-point history H from ODB at Step 2 Frame 1
odb = openOdb(odb_path, readOnly=True)
s2 = odb.steps['Step-2']
f2_1 = s2.frames[1] # Frame 1 is Step 2 Inc 1 (u = 0.00254 mm)

elem_H = {} # phys_eid (1..400) -> [H_gp1, H_gp2, H_gp3, H_gp4]
for val in f2_1.fieldOutputs['SDV2'].values:
    eid = val.elementLabel
    phys_eid = eid - 800
    if 1 <= phys_eid <= 400:
        if phys_eid not in elem_H:
            elem_H[phys_eid] = []
        elem_H[phys_eid].append(float(val.data))

odb.close()
print("Extracted history H for %d elements." % len(elem_H))
max_H = max(max(h) for h in elem_H.values())
print("Max extracted Gauss-point history H_0 = %f MPa" % max_H)

# 3. Read mesh connectivity from CaseA_cracked.inp
elem_nodes = {} # phys_eid -> [n1, n2, n3, n4]
with open(inp_case_a, 'r') as f:
    in_phase_elems = False
    for line in f:
        line = line.strip()
        if line.startswith("*Element, type=U1"):
            in_phase_elems = True
            continue
        elif line.startswith("*Element, type=U2"):
            in_phase_elems = False
            break
        if in_phase_elems and line and not line.startswith("*"):
            parts = [int(p.strip()) for p in line.split(",")]
            eid = parts[0]
            elem_nodes[eid] = parts[1:5]

print("Read connectivity for %d physical elements." % len(elem_nodes))

# 4. Write offset_state_table_postsnap.csv and offset_state_table.csv
for target_csv in [csv_out_versioned, csv_out]:
    with open(target_csv, 'w') as f:
        f.write("EID, U1_1, U2_1, U1_2, U2_2, U1_3, U2_3, U1_4, U2_4, D_1, D_2, D_3, D_4, H_1, H_2, H_3, H_4\n")
        for eid in sorted(elem_nodes.keys()):
            conn = elem_nodes[eid]
            u_vals = []
            d_vals = []
            for nid in conn:
                u_vals.extend([nodal_u[nid][0], nodal_u[nid][1]])
                d_vals.append(nodal_u[nid][2])
                
            h_vals = elem_H.get(eid, [0.0, 0.0, 0.0, 0.0])
            if len(h_vals) < 4:
                h_vals = (h_vals + [0.0]*4)[:4]
                
            line_parts = [str(eid)] + ["{:.12e}".format(x) for x in u_vals] + ["{:.12e}".format(x) for x in d_vals] + ["{:.12e}".format(x) for x in h_vals]
            f.write(", ".join(line_parts) + "\n")

print("SUCCESS: Wrote offset_state_table.csv for %d elements." % len(elem_nodes))

# 5. Assemble Residuals to evaluate coupled equilibrium before solve
print("\n=== 2. Assembling Initial Residuals at Post-Snap Offset State ===")
# Load mesh coordinates
mesh_coords = {}
with open(inp_case_a, 'r') as f:
    in_nodes = False
    for line in f:
        ls = line.strip()
        if ls.upper().startswith('*NODE'):
            in_nodes = True
            continue
        elif ls.startswith('*'):
            in_nodes = False
            continue
        if in_nodes and ls:
            p = [x.strip() for x in ls.split(',')]
            if len(p) >= 3:
                mesh_coords[int(p[0])] = np.array([float(p[1]), float(p[2])])

E_L0 = 0.0075
E_GC = 0.0027
E_MOD = 210.0
E_NU = 0.3
E_K = 1.0e-7

xg = [-0.577350269189626, 0.577350269189626, 0.577350269189626, -0.577350269189626]
yg = [-0.577350269189626, -0.577350269189626, 0.577350269189626, 0.577350269189626]

R_phase = np.zeros(len(mesh_coords) + 1)
R_mech_x = np.zeros(len(mesh_coords) + 1)
R_mech_y = np.zeros(len(mesh_coords) + 1)

for eid in sorted(elem_nodes.keys()):
    conn = elem_nodes[eid]
    elem_xy = np.array([mesh_coords[n] for n in conn])
    
    d_tot = np.array([nodal_u[n][2] for n in conn])
    u_off = np.array([[nodal_u[n][0], nodal_u[n][1]] for n in conn])
    u_flat = u_off.flatten()
    h_table = elem_H.get(eid, [0.0, 0.0, 0.0, 0.0])
    d_avg = 0.25 * sum(d_tot)
    deg = (1.0 - d_avg)**2 + E_K
    
    amatrx_p = np.zeros((4,4))
    rhs_p = np.zeros(4)
    f_int_m = np.zeros(8)
    
    c11_0 = E_MOD*(1.0 - E_NU)/((1.0 + E_NU)*(1.0 - 2.0*E_NU))
    c12_0 = E_MOD*E_NU/((1.0 + E_NU)*(1.0 - 2.0*E_NU))
    c22_0 = c11_0
    c33_0 = E_MOD/(2.0*(1.0 + E_NU))
    
    c11_m = c11_0 * deg
    c12_m = c12_0 * deg
    c22_m = c22_0 * deg
    c33_m = c33_0 * deg
    D_elas = np.array([
        [c11_m, c12_m, 0.0],
        [c12_m, c22_m, 0.0],
        [0.0,   0.0,   c33_m]
    ])
    
    for kpt in range(4):
        xi, eta = xg[kpt], yg[kpt]
        n_vec = np.array([
            0.25*(1-xi)*(1-eta),
            0.25*(1+xi)*(1-eta),
            0.25*(1+xi)*(1+eta),
            0.25*(1-xi)*(1+eta)
        ])
        dn_xi  = np.array([-0.25*(1-eta),  0.25*(1-eta), 0.25*(1+eta), -0.25*(1+eta)])
        dn_eta = np.array([-0.25*(1-xi),  -0.25*(1+xi),  0.25*(1+xi),   0.25*(1-xi)])
        
        J = np.zeros((2,2))
        for i in range(4):
            J[0,0] += dn_xi[i]  * elem_xy[i,0]
            J[0,1] += dn_xi[i]  * elem_xy[i,1]
            J[1,0] += dn_eta[i] * elem_xy[i,0]
            J[1,1] += dn_eta[i] * elem_xy[i,1]
            
        detJ = J[0,0]*J[1,1] - J[0,1]*J[1,0]
        cjac = detJ * 1.0
        invJ = np.linalg.inv(J)
        
        b_p = np.zeros((2, 4))
        for i in range(4):
            b_p[0,i] = invJ[0,0]*dn_xi[i] + invJ[0,1]*dn_eta[i]
            b_p[1,i] = invJ[1,0]*dn_xi[i] + invJ[1,1]*dn_eta[i]
            
        hist = h_table[kpt]
        for i in range(4):
            for j in range(4):
                bdb = b_p[0,i]*b_p[0,j] + b_p[1,i]*b_p[1,j]
                amatrx_p[i,j] += cjac * ((E_GC*E_L0)*bdb + (E_GC/E_L0 + 2.0*hist)*n_vec[i]*n_vec[j])
            rhs_p[i] += cjac * 2.0 * hist * n_vec[i]
            
        B_m = np.zeros((3, 8))
        for i in range(4):
            B_m[0, 2*i]   = b_p[0,i]
            B_m[1, 2*i+1] = b_p[1,i]
            B_m[2, 2*i]   = b_p[1,i]
            B_m[2, 2*i+1] = b_p[0,i]
            
        strain = B_m.dot(u_flat)
        stress = D_elas.dot(strain)
        for i in range(8):
            for j in range(3):
                f_int_m[i] += cjac * B_m[j,i] * stress[j]
                
    for i in range(4):
        for j in range(4):
            rhs_p[i] -= amatrx_p[i,j] * d_tot[j]
            
    for i, n in enumerate(conn):
        R_phase[n] += rhs_p[i]
        R_mech_x[n] -= f_int_m[2*i]
        R_mech_y[n] -= f_int_m[2*i+1]

max_r_p = max(abs(R_phase[1:451]))
max_r_p_nid = int(np.argmax(abs(R_phase[1:451])) + 1)
print("Max |R_phase| = %e kN (= %f N) at node %d" % (max_r_p, max_r_p*1000.0, max_r_p_nid))

fixed_nodes = set(range(1, 22)) | set(range(430, 451))
internal_nodes = [n for n in range(1, 451) if n not in fixed_nodes]
max_r_mx = max(abs(R_mech_x[internal_nodes]))
max_r_my = max(abs(R_mech_y[internal_nodes]))
print("Max internal |R_mech_x| = %e kN (= %f N)" % (max_r_mx, max_r_mx*1000.0))
print("Max internal |R_mech_y| = %e kN (= %f N)" % (max_r_my, max_r_my*1000.0))

# 6. Generate CaseB_cracked.inp
print("\n=== 3. Generating CaseB_cracked.inp ===")
with open(inp_case_a, 'r') as f:
    deck_content = f.read()

prefix = deck_content.split("** STEP 1: Monotonic Loading")[0]

case_b_steps = """** ==========================================================
** STEP 1: Zero-Increment State Reconstruction (Delta u = 0.0 mm)
** Evaluates exact cracked equilibrium under kinematic offset at u = 0.00254 mm
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
** STEP 2: Forward Continuation Advance (Delta u = 0.00016 mm, 4 incs of 0.00004 mm)
** Continues propagation from u = 0.00254 mm to u = 0.00270 mm
** ==========================================================
*Step, name=Step-2, nlgeom=NO, inc=100
*Static
0.25, 1.0, 1.0E-6, 0.25
*Boundary
N_RP, 2, 2, 0.00016
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

with open(inp_case_b, 'w') as f:
    f.write(prefix + case_b_steps)

print("SUCCESS: Generated CaseB_cracked.inp for post-snap continuation.")

summary = {
    "reference_state": "Step-2 Frame 1 (inc 1, u = 0.00254 mm)",
    "max_nodal_damage": max_d,
    "max_nodal_damage_node": max_d_nid,
    "max_history_H0_MPa": max_H,
    "max_residual_phase_kN": float(max_r_p),
    "max_residual_phase_N": float(max_r_p * 1000.0),
    "max_residual_phase_node": max_r_p_nid,
    "max_residual_mech_x_kN": float(max_r_mx),
    "max_residual_mech_x_N": float(max_r_mx * 1000.0),
    "max_residual_mech_y_kN": float(max_r_my),
    "max_residual_mech_y_N": float(max_r_my * 1000.0),
    "continuation_step2_delta_u_mm": 0.00016,
    "continuation_step2_target_u_mm": 0.00270,
    "continuation_step2_incs": 4
}

with open(os.path.join(scratch_dir, "postsnap_initialization_summary.json"), 'w') as f:
    json.dump(summary, f, indent=2)

print("Saved postsnap_initialization_summary.json")

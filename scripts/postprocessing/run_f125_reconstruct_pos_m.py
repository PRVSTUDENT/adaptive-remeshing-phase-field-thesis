#!/usr/bin/env python3
"""
F125DIAG POS_M vs H Reconstruction & Consistency Auditor for R2R13 and Continuous PK10R1
Task ID: F125DIAG-M2-R2R13-TERMINAL-HISTORY-ENERGY-CONSISTENCY-AND-CALL-ORDER1
"""

import sys
import os
import json
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SSH_KEY = "C:/Users/pruth/.ssh/tu_freiberg_codex"
SSH_HOST = "pr21vyci@mlogin01.hrz.tu-freiberg.de"

REMOTE_SCRIPT = """#!/usr/bin/env python3
import sys
import os
import re
import json
import math

BASE_STATE   = "projects/adaptive-remeshing/models/generated/mode_ii/production_state_transfer_batch"
BASE_CONTROL = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch"

def parse_inp_mesh(inp_path):
    nodes = {}
    elements = {} # eid -> (type, [n1, n2, ...])
    
    in_node = False
    in_elem = False
    elem_type = None
    
    with open(inp_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("**"):
                continue
            if line_str.upper().startswith("*NODE"):
                in_node = True
                in_elem = False
                continue
            if line_str.upper().startswith("*ELEMENT"):
                in_node = False
                in_elem = True
                m = re.search(r"TYPE\s*=\s*([A-Za-z0-9]+)", line_str, re.IGNORECASE)
                if m:
                    elem_type = m.group(1).upper()
                else:
                    elem_type = "UNKNOWN"
                continue
            if line_str.startswith("*"):
                in_node = False
                in_elem = False
                continue
                
            if in_node:
                tokens = [t.strip() for t in line_str.split(",")]
                if len(tokens) >= 3 and tokens[0].isdigit():
                    nid = int(tokens[0])
                    x = float(tokens[1])
                    y = float(tokens[2])
                    nodes[nid] = (x, y)
            elif in_elem:
                tokens = [t.strip() for t in line_str.split(",")]
                if len(tokens) >= 4 and tokens[0].isdigit():
                    eid = int(tokens[0])
                    nl = [int(t) for t in tokens[1:] if t.isdigit()]
                    elements[eid] = (elem_type, nl)
                    
    return nodes, elements

def parse_dat(dat_path):
    nodes_u = {}
    elem_sdvs = {}
    
    in_node = False
    in_el = False
    
    with open(dat_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "THE FOLLOWING TABLE IS PRINTED FOR ALL NODES" in line:
                in_node = True
                in_el = False
                continue
            if "THE FOLLOWING TABLE IS PRINTED AT THE INTEGRATION POINTS" in line:
                in_el = True
                in_node = False
                continue
            if in_node:
                if line.startswith("1") or "JOB TIME SUMMARY" in line or "ANALYSIS SUMMARY" in line or "STEP " in line or "THE FOLLOWING TABLE" in line:
                    in_node = False
                    continue
                tokens = line.strip().split()
                if len(tokens) >= 3 and tokens[0].isdigit():
                    try:
                        nid = int(tokens[0])
                        u1 = float(tokens[1])
                        u2 = float(tokens[2])
                        nodes_u[nid] = (u1, u2)
                    except Exception:
                        pass
            if in_el:
                if line.startswith("1") or "JOB TIME SUMMARY" in line or "ANALYSIS SUMMARY" in line or "STEP " in line or "THE FOLLOWING TABLE" in line:
                    in_el = False
                    continue
                tokens = line.strip().split()
                if len(tokens) >= 5 and tokens[0].isdigit() and tokens[1].isdigit():
                    try:
                        eid = int(tokens[0])
                        pt  = int(tokens[1])
                        sdv14 = float(tokens[2])
                        sdv15 = float(tokens[3])
                        sdv16 = float(tokens[4])
                        elem_sdvs[(eid, pt)] = (sdv14, sdv15, sdv16)
                    except Exception:
                        pass
                        
    return nodes_u, elem_sdvs

def compute_pos_m_for_mesh(nodes, elements, nodes_u, elem_sdvs, n_phys=9612):
    # Material constants
    E_MOD = 210.0
    E_NU  = 0.3
    C11 = E_MOD*(1.0 - E_NU)/((1.0 + E_NU)*(1.0 - 2.0*E_NU))
    C12 = E_MOD*E_NU/((1.0 + E_NU)*(1.0 - 2.0*E_NU))
    C33 = E_MOD/(2.0*(1.0 + E_NU))
    
    pos_m_list = []
    h_list = []
    diff_list = []
    
    # Gauss points for Quad 4 (2x2)
    xg4 = [-0.577350269189626, 0.577350269189626, 0.577350269189626, -0.577350269189626]
    yg4 = [-0.577350269189626, -0.577350269189626, 0.577350269189626, 0.577350269189626]
    
    # Gauss points for Tri 3 (1 point)
    xg3 = [1.0/3.0]
    yg3 = [1.0/3.0]

    count_gt = 0
    max_diff = 0.0
    sum_diff_sq = 0.0
    sum_h_sq = 0.0
    
    tol = 1.0e-4
    
    for mech_eid in range(n_phys + 1, 2*n_phys + 1):
        if mech_eid not in elements:
            continue
        etype, conn = elements[mech_eid]
        phys_idx = mech_eid - n_phys
        
        # Get nodal coords and displacements
        coords = [nodes[n] for n in conn]
        u_vals = [nodes_u.get(n, (0.0, 0.0)) for n in conn]
        
        if etype in ["U2", "CPE4"]:
            # Quad 4
            num_pts = 4
            for pt in range(1, 5):
                xi = xg4[pt-1]
                eta = yg4[pt-1]
                
                # Shape function derivatives
                dn = [
                    [-0.25*(1.0-eta), 0.25*(1.0-eta), 0.25*(1.0+eta), -0.25*(1.0+eta)],
                    [-0.25*(1.0-xi), -0.25*(1.0+xi), 0.25*(1.0+xi), 0.25*(1.0-xi)]
                ]
                
                # Jacobian
                j11 = sum(dn[0][k]*coords[k][0] for k in range(4))
                j12 = sum(dn[0][k]*coords[k][1] for k in range(4))
                j21 = sum(dn[1][k]*coords[k][0] for k in range(4))
                j22 = sum(dn[1][k]*coords[k][1] for k in range(4))
                detj = j11*j22 - j12*j21
                
                invj = [[j22/detj, -j12/detj], [-j21/detj, j11/detj]]
                
                # B matrix
                b = [[0.0]*8 for _ in range(3)]
                for i in range(4):
                    b[0][2*i]   = invj[0][0]*dn[0][i] + invj[0][1]*dn[1][i]
                    b[1][2*i+1] = invj[1][0]*dn[0][i] + invj[1][1]*dn[1][i]
                    b[2][2*i]   = invj[1][0]*dn[0][i] + invj[1][1]*dn[1][i]
                    b[2][2*i+1] = invj[0][0]*dn[0][i] + invj[0][1]*dn[1][i]
                    
                u_vec = []
                for u1, u2 in u_vals:
                    u_vec.extend([u1, u2])
                    
                e11 = sum(b[0][k]*u_vec[k] for k in range(8))
                e22 = sum(b[1][k]*u_vec[k] for k in range(8))
                e12 = 0.5 * sum(b[2][k]*u_vec[k] for k in range(8))
                
                tr_e = e11 + e22
                e_pos = max(0.0, tr_e)
                pos_m = 0.5*C12*(e_pos**2) + C33*(e11**2 + e22**2 + 2.0*(e12**2))
                
                # Stored H from DAT (for point 1) or manifest
                sdv_data = elem_sdvs.get((mech_eid, pt), elem_sdvs.get((mech_eid, 1), (0.0, 1.0, 0.0)))
                h_stored = sdv_data[2]
                
                pos_m_list.append(pos_m)
                h_list.append(h_stored)
                diff = pos_m - h_stored
                diff_list.append(diff)
                
                if diff > tol:
                    count_gt += 1
                if diff > max_diff:
                    max_diff = diff
                    
                sum_diff_sq += diff**2
                sum_h_sq += h_stored**2

        elif etype in ["U4", "CPE3"]:
            # Tri 3
            pass # Handle tris if present

    pos_m_min = min(pos_m_list) if pos_m_list else 0.0
    pos_m_max = max(pos_m_list) if pos_m_list else 0.0
    pos_m_mean = sum(pos_m_list)/len(pos_m_list) if pos_m_list else 0.0
    
    h_min = min(h_list) if h_list else 0.0
    h_max = max(h_list) if h_list else 0.0
    h_mean = sum(h_list)/len(h_list) if h_list else 0.0
    
    total_ips = len(pos_m_list)
    frac_gt = float(count_gt)/total_ips if total_ips > 0 else 0.0
    rel_l2 = math.sqrt(sum_diff_sq) / max(math.sqrt(sum_h_sq), 1e-12)
    
    return {
        "terminal_IP_count": total_ips,
        "POS_M_min": pos_m_min,
        "POS_M_max": pos_m_max,
        "POS_M_mean": pos_m_mean,
        "H_min": h_min,
        "H_max": h_max,
        "H_mean": h_mean,
        "count_POS_M_gt_H_plus_tolerance": count_gt,
        "fraction_POS_M_gt_H": frac_gt,
        "max_POS_M_minus_H": max_diff,
        "relative_L2_POS_M_vs_H": rel_l2
    }

def main():
    r13_inp = os.path.join(BASE_STATE, "M2STATE_FRACFIX_RESTART2R13", "M2STATE_FRACFIX_RESTART2R13.inp")
    r13_dat = os.path.join(BASE_STATE, "M2STATE_FRACFIX_RESTART2R13", "M2STATE_FRACFIX_RESTART2R13.dat")
    
    cont_inp = os.path.join(BASE_CONTROL, "PK10R1_CONTINUOUS_U050", "PK10R1_CONTINUOUS_U050.inp")
    cont_dat = os.path.join(BASE_CONTROL, "PK10R1_CONTINUOUS_U050", "PK10R1_CONTINUOUS_U050.dat")
    
    nodes_r13, elems_r13 = parse_inp_mesh(r13_inp)
    u_r13, sdvs_r13 = parse_dat(r13_dat)
    r13_res = compute_pos_m_for_mesh(nodes_r13, elems_r13, u_r13, sdvs_r13)
    
    nodes_cont, elems_cont = parse_inp_mesh(cont_inp)
    u_cont, sdvs_cont = parse_dat(cont_dat)
    cont_res = compute_pos_m_for_mesh(nodes_cont, elems_cont, u_cont, sdvs_cont)
    
    out = {
        "r13_audit": r13_res,
        "continuous_audit": cont_res
    }
    print(json.dumps(out))

if __name__ == "__main__":
    main()
"""

def main():
    remote_path = "projects/adaptive-remeshing/models/generated/mode_ii/production_control_batch/f125_reconstruct.py"
    upload_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"cat << 'EOF' > {remote_path}\n{REMOTE_SCRIPT}\nEOF"]
    subprocess.run(upload_cmd, check=True)

    run_cmd = ["ssh", "-i", SSH_KEY, SSH_HOST, f"python3 {remote_path}"]
    res = subprocess.run(run_cmd, capture_output=True, text=True, timeout=120)
    print(res.stdout)

if __name__ == "__main__":
    main()

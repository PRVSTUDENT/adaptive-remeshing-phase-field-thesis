# -*- coding: utf-8 -*-
"""
execute_f1692_sec43_recovery.py
===============================
Task F1692: Auxiliary Stress Recovery for Pandey-Kumar Section 4.3 Benchmark.
1. Reads physical coarse mesh (3,923 elements, 4,039 nodes)
2. Loads damage field d from converged staggered solve (f1692_damaged_elements.json)
3. Generates two auxiliary recovery models:
   - Case A: Intact linear-elastic recovery (Method A pre-analysis control at uy=1.46 mm)
   - Case B: Degraded-stiffness recovery (Method A multi-frame/terminal state with E_deg = g(d)*E0)
4. Solves both locally with Abaqus/Standard (0 PBS)
5. Exports authentic MISESERI, MISESAVG, and EVOL fields.
"""

from __future__ import print_function
import os
import sys
import json
import math
import subprocess

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MODEL_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "192_pk_sec43_staggered_job1")
PHYS_INP = os.path.join(MODEL_DIR, "PK_SEC43_STAGGERED_PHYS.inp")
DAMAGED_JSON = os.path.join(MODEL_DIR, "f1692_damaged_elements.json")

def parse_mesh():
    nodes = []
    quads = []
    tris = []
    
    in_node = False
    in_elem = False
    elem_type = ""
    
    with open(PHYS_INP, "r") as f:
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("**"):
                continue
            if line_str.startswith("*"):
                u = line_str.upper()
                if u.startswith("*NODE"):
                    in_node = True
                    in_elem = False
                elif u.startswith("*ELEMENT"):
                    in_node = False
                    in_elem = True
                    elem_type = "CPE4" if "CPE4" in u else ("CPE3" if "CPE3" in u else "")
                else:
                    in_node = False
                    in_elem = False
                continue
                
            if in_node:
                parts = [p.strip() for p in line_str.split(",")]
                if len(parts) >= 3:
                    nodes.append((int(parts[0]), float(parts[1]), float(parts[2])))
            elif in_elem:
                parts = [int(p.strip()) for p in line_str.split(",")]
                eid = parts[0]
                conn = parts[1:]
                if len(conn) == 4 or elem_type == "CPE4":
                    quads.append((eid, conn))
                elif len(conn) == 3 or elem_type == "CPE3":
                    tris.append((eid, conn))
                    
    print("Parsed %d nodes, %d quads, %d tris." % (len(nodes), len(quads), len(tris)))
    return nodes, quads, tris

def identify_boundary_nodes(nodes):
    lower_nodes = []
    upper_nodes = []
    central_nodes = []
    
    for nid, x, y in nodes:
        d_lower = math.hypot(x - 20.0, y - 20.0)
        d_upper = math.hypot(x - 20.0, y - 100.0)
        d_central = math.hypot(x - 36.5, y - 51.0)
        
        if abs(d_lower - 5.0) <= 0.08:
            lower_nodes.append(nid)
        if abs(d_upper - 5.0) <= 0.08:
            upper_nodes.append(nid)
        if abs(d_central - 10.0) <= 0.08:
            central_nodes.append(nid)
            
    print("Boundary nodes: lower=%d, upper=%d, central=%d" % (
        len(lower_nodes), len(upper_nodes), len(central_nodes)
    ))
    return lower_nodes, upper_nodes, central_nodes

def build_deck(out_path, nodes, quads, tris, lower_nodes, upper_nodes, damaged_dict=None):
    rp_nid = 999999
    E0 = 210.0  # GPa = kN/mm^2
    nu = 0.3
    k_res = 1e-6
    
    with open(out_path, "w") as f:
        f.write("*HEADING\n")
        f.write("Task F1692 Auxiliary Stress Recovery for Pandey-Kumar Sec 4.3\n")
        
        # Nodes
        f.write("*NODE\n")
        for nid, x, y in nodes:
            f.write("%d, %.7f, %.7f\n" % (nid, x, y))
        f.write("%d, 20.0000000, 100.0000000\n" % rp_nid)
        
        # Elements
        if quads:
            f.write("*ELEMENT, TYPE=CPE4, ELSET=QUADS\n")
            for eid, conn in quads:
                f.write("%d, %s\n" % (eid, ", ".join(str(c) for c in conn)))
        if tris:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=TRIS\n")
            for eid, conn in tris:
                f.write("%d, %s\n" % (eid, ", ".join(str(c) for c in conn)))
                
        f.write("*ELSET, ELSET=All_elem\nQUADS\nTRIS\n")
        
        # Node sets
        def write_nset(name, nids):
            f.write("*NSET, NSET=%s\n" % name)
            for i in range(0, len(nids), 16):
                f.write(", ".join(str(nid) for nid in nids[i:i+16]) + "\n")
                
        write_nset("N_LOWER_HOLE", lower_nodes)
        write_nset("N_UPPER_HOLE", upper_nodes)
        f.write("*NSET, NSET=N_RP\n%d\n" % rp_nid)
        
        def write_elset(name, eids):
            f.write("*ELSET, ELSET=%s\n" % name)
            for i in range(0, len(eids), 16):
                f.write(", ".join(str(eid) for eid in eids[i:i+16]) + "\n")
                
        # Material assignment
        if damaged_dict is None:
            # Homogeneous linear elastic
            f.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=STEEL\n1.0\n")
            f.write("*MATERIAL, NAME=STEEL\n")
            f.write("*ELASTIC, TYPE=ISOTROPIC\n%.4f, %.4f\n" % (E0, nu))
        else:
            # Discrete degraded stiffness bins (20 bins)
            all_eids = [eid for eid, _ in quads] + [eid for eid, _ in tris]
            n_phys = len(all_eids)
            bins = {i: [] for i in range(20)}
            
            for eid in all_eids:
                d = damaged_dict.get(eid, 0.0)
                # g(d) = (1-d)^2 + k_res
                g_d = (1.0 - d)**2 + k_res
                bin_idx = min(19, int(g_d * 20.0))
                bins[bin_idx].append(eid)
                
            for b_idx, eids in bins.items():
                if not eids:
                    continue
                mat_name = "MAT_BIN_%d" % b_idx
                elset_name = "ELSET_BIN_%d" % b_idx
                write_elset(elset_name, eids)
                f.write("*SOLID SECTION, ELSET=%s, MATERIAL=%s\n1.0\n" % (elset_name, mat_name))
                f.write("*MATERIAL, NAME=%s\n" % mat_name)
                # Mean degraded modulus in bin
                g_mid = (b_idx + 0.5) / 20.0
                E_deg = max(1e-4, g_mid * E0)
                f.write("*ELASTIC, TYPE=ISOTROPIC\n%.6e, %.4f\n" % (E_deg, nu))
                
        # Tie upper hole to RP in DOF 2
        f.write("** Tie upper hole to RP\n")
        for nid in upper_nodes:
            f.write("*EQUATION\n2\n%d, 2, 1.0, %d, 2, -1.0\n" % (nid, rp_nid))
            
        # Step
        f.write("*STEP, NAME=RECOVERY_STEP, NLGEOM=NO\n")
        f.write("*STATIC\n1.0, 1.0, 1.0, 1.0\n")
        f.write("*BOUNDARY\n")
        f.write("N_LOWER_HOLE, 1, 2, 0.0\n")
        f.write("N_UPPER_HOLE, 1, 1, 0.0\n")
        f.write("N_RP, 2, 2, 1.46\n") # uy = 1.46 mm matching paper
        
        # Field Outputs
        f.write("*OUTPUT, FIELD\n")
        f.write("*ELEMENT OUTPUT, ELSET=All_elem\n")
        f.write("MISESERI, MISESAVG, EVOL, S, E\n")
        f.write("*NODE OUTPUT\nU, RF\n")
        f.write("*END STEP\n")
        
    print("Wrote deck: %s" % out_path)

def solve_deck(inp_path, job_name):
    cmd = "abaqus job=" + job_name + " input=" + inp_path + " interactive ask_delete=OFF"
    print("Solving %s..." % job_name)
    subprocess.check_call(cmd, shell=True, cwd=MODEL_DIR)
    print("Job %s finished successfully." % job_name)

def main():
    nodes, quads, tris = parse_mesh()
    lower_nodes, upper_nodes, central_nodes = identify_boundary_nodes(nodes)
    
    # 1. Linear Elastic Pre-Analysis Deck
    elas_inp = os.path.join(MODEL_DIR, "PK_SEC43_STAGGERED_RECOVERY_ELAS.inp")
    build_deck(elas_inp, nodes, quads, tris, lower_nodes, upper_nodes, damaged_dict=None)
    solve_deck(elas_inp, "PK_SEC43_STAGGERED_RECOVERY_ELAS")
    
    # 2. Degraded-Stiffness Recovery Deck
    if os.path.exists(DAMAGED_JSON):
        with open(DAMAGED_JSON, "r") as f:
            d_data = json.load(f)
        n_phys = len(quads) + len(tris)
        damaged_dict = {}
        for item in d_data.get("damaged_elements", []):
            raw_eid = item["element"]
            phys_eid = ((raw_eid - 1) % n_phys) + 1
            damaged_dict[phys_eid] = item["damage"]
            
        deg_inp = os.path.join(MODEL_DIR, "PK_SEC43_STAGGERED_RECOVERY_DEG.inp")
        build_deck(deg_inp, nodes, quads, tris, lower_nodes, upper_nodes, damaged_dict=damaged_dict)
        solve_deck(deg_inp, "PK_SEC43_STAGGERED_RECOVERY_DEG")
        
    print("All recovery solves complete.")
    return 0

if __name__ == "__main__":
    main()

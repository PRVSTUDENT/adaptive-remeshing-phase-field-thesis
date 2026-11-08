#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
execute_f1688_sec43_recovery.py

Task F1688: Method A auxiliary linear-elastic stress recovery on Pandey-Kumar Section 4.3
rectangular notched plate with a hole (65 x 120 mm).
Runs local Abaqus/Standard solve (0 PBS) on physical coarse mesh (3,923 elements).
Outputs authentic MISESERI and MISESAVG field outputs.
"""

import os
import sys
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
model_dir = REPO_ROOT / "models" / "pandey_kumar_mode1" / "188_pk_sec43_hole_plate"
phys_inp = model_dir / "PK_SEC43_COARSE_PHYS.inp"
recovery_inp = model_dir / "PK_SEC43_COARSE_RECOVERY.inp"
job_name = "PK_SEC43_COARSE_RECOVERY"

def build_recovery_deck():
    print(f"Reading physical mesh: {phys_inp}")
    with open(phys_inp, "r") as f:
        lines = f.readlines()

    # Extract nodes and elements
    nodes = []
    quad_elems = []
    tri_elems = []
    
    in_node = False
    in_elem = False
    elem_type = ""
    
    for line in lines:
        s = line.strip()
        if not s or s.startswith("**"):
            continue
        if s.startswith("*"):
            su = s.upper()
            if su.startswith("*NODE"):
                in_node = True
                in_elem = False
            elif su.startswith("*ELEMENT"):
                in_node = False
                in_elem = True
                if "TYPE=CPE4" in su:
                    elem_type = "CPE4"
                elif "TYPE=CPE3" in su:
                    elem_type = "CPE3"
                else:
                    elem_type = ""
            else:
                in_node = False
                in_elem = False
            continue
            
        if in_node:
            parts = [p.strip() for p in s.split(",")]
            if len(parts) >= 3:
                nid = int(parts[0])
                x = float(parts[1])
                y = float(parts[2])
                nodes.append((nid, x, y))
        elif in_elem:
            parts = [p.strip() for p in s.split(",")]
            eid = int(parts[0])
            conn = [int(p) for p in parts[1:]]
            if elem_type == "CPE4" or len(conn) == 4:
                quad_elems.append((eid, conn))
            elif elem_type == "CPE3" or len(conn) == 3:
                tri_elems.append((eid, conn))

    print(f"Extracted {len(nodes)} nodes, {len(quad_elems)} quads, {len(tri_elems)} tris.")

    # Find boundary nodes:
    # Lower hole: center (20, 20), R=5
    # Upper hole: center (20, 100), R=5
    # Central hole: center (36.5, 51), R=10
    lower_nodes = []
    upper_nodes = []
    central_nodes = []
    
    for nid, x, y in nodes:
        d_lower = ((x - 20.0)**2 + (y - 20.0)**2)**0.5
        d_upper = ((x - 20.0)**2 + (y - 100.0)**2)**0.5
        d_central = ((x - 36.5)**2 + (y - 51.0)**2)**0.5
        
        if abs(d_lower - 5.0) <= 0.05:
            lower_nodes.append(nid)
        if abs(d_upper - 5.0) <= 0.05:
            upper_nodes.append(nid)
        if abs(d_central - 10.0) <= 0.05:
            central_nodes.append(nid)
            
    print(f"Identified boundary nodes: lower={len(lower_nodes)}, upper={len(upper_nodes)}, central={len(central_nodes)}")

    # Write recovery input deck
    with open(recovery_inp, "w") as f:
        f.write("*HEADING\n")
        f.write("Task F1688 Method A Pandey-Kumar Section 4.3 Auxiliary Stress Recovery\n")
        f.write("** Native Abaqus Linear-Elastic Continuum Model for MISESERI Recovery\n")
        f.write("** Dimensions: 65 x 120 mm, Notch: 10 x 0.4 mm, Holes: R=5, R=5, R=10\n")
        
        # Nodes
        f.write("*NODE\n")
        for nid, x, y in nodes:
            f.write(f"{nid}, {x:.7f}, {y:.7f}\n")
        # Reference point node
        rp_nid = 999999
        f.write(f"{rp_nid}, 20.0000000, 100.0000000\n")
        
        # Elements
        if quad_elems:
            f.write("*ELEMENT, TYPE=CPE4, ELSET=QUADS\n")
            for eid, conn in quad_elems:
                f.write(f"{eid}, {', '.join(str(c) for c in conn)}\n")
        if tri_elems:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=TRIS\n")
            for eid, conn in tri_elems:
                f.write(f"{eid}, {', '.join(str(c) for c in conn)}\n")
                
        f.write("*ELSET, ELSET=All_elem\n")
        f.write("QUADS\nTRIS\n")
        
        # Node sets
        def write_nset(name, nids):
            f.write(f"*NSET, NSET={name}\n")
            for i in range(0, len(nids), 16):
                f.write(", ".join(str(nid) for nid in nids[i:i+16]) + "\n")

        write_nset("N_LOWER_HOLE", lower_nodes)
        write_nset("N_UPPER_HOLE", upper_nodes)
        write_nset("N_CENTRAL_HOLE", central_nodes)
        f.write(f"*NSET, NSET=N_RP\n{rp_nid}\n")
        
        # Solid Section
        f.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=STEEL\n1.0\n")
        f.write("*MATERIAL, NAME=STEEL\n")
        f.write("*ELASTIC, TYPE=ISOTROPIC\n")
        f.write("210.0, 0.30\n") # E = 210 kN/mm^2 = 210 GPa, nu = 0.3
        
        # Equation constraints: tie upper hole DOF 2 to RP
        f.write("** Tie upper hole nodes to RP in DOF 2\n")
        for nid in upper_nodes:
            f.write("*EQUATION\n2\n")
            f.write(f"{nid}, 2, 1.0, {rp_nid}, 2, -1.0\n")
            
        # Step: Single linear elastic step
        # Target displacement: u_y = 1.0 mm (or 1.46 mm)
        f.write("*STEP, NAME=RECOVERY_STEP, NLGEOM=NO\n")
        f.write("*STATIC\n")
        f.write("1.0, 1.0, 1.0, 1.0\n")
        f.write("*BOUNDARY\n")
        f.write("N_LOWER_HOLE, 1, 2, 0.0\n")
        f.write("N_UPPER_HOLE, 1, 1, 0.0\n")
        f.write(f"N_RP, 2, 2, 1.46\n") # 1.46 mm matching paper Fig. 16 point u_s4
        
        f.write("*OUTPUT, FIELD\n")
        f.write("*ELEMENT OUTPUT, ELSET=All_elem\n")
        f.write("MISESERI, MISESAVG, S, E, EVOL\n")
        f.write("*NODE OUTPUT, NSET=N_RP\n")
        f.write("U, RF\n")
        f.write("*END STEP\n")

    print(f"Wrote recovery input deck: {recovery_inp}")

def run_local_abaqus():
    cwd = str(model_dir)
    cmd = ["cmd", "/c", "abaqus", f"job={job_name}", "interactive"]
    print(f"Executing local Abaqus solve in: {cwd}")
    print(f"Command: {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    print("Abaqus return code:", res.returncode)
    if res.stdout:
        print("Stdout tail:\n", "\n".join(res.stdout.splitlines()[-15:]))
    if res.stderr:
        print("Stderr:\n", res.stderr)
    if res.returncode != 0:
        raise RuntimeError("Abaqus recovery solve failed.")

if __name__ == "__main__":
    build_recovery_deck()
    run_local_abaqus()

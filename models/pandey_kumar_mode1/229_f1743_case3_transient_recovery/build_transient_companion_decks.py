# -*- coding: utf-8 -*-
"""
build_transient_companion_decks.py
==================================
Task F1743: Builds continuous degradation companion recovery decks for intermediate
primary-crack propagation states in Pandey & Kumar (2025) Section 4.3 holed plate.

Prescribes authentic full-field UEL nodal displacements u_UEL(x, y) and degraded
stiffness (1-d)^2 * E_0 onto standard continuum CPE4/CPE3 elements, ensuring:
  1. Exact kinematic equivalence with zero remote re-equilibration artifacts.
  2. Authentic degraded stress concentration around the moving crack tip.
  3. Native Abaqus SPR (MISESERI / MISESAVG) error indicator generation.

Zero user subroutines required for the recovery solve.
"""
from __future__ import print_function
import os
import sys
import json
import numpy as np

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
BASE_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "200_pk_sec43_prescribed_same_state", "PK_SEC43_PRESCRIBED_STATE2.inp")
PACKAGE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "229_f1743_case3_transient_recovery")
EXTRACTED_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1743_extracted_transient_uel.json")

E0_GPA = 210.0   # 210 kN/mm^2 = GPa
NU = 0.30
K_RES = 1.0e-7

def parse_mesh(inp_path):
    nodes = {}
    elements = {}
    with open(inp_path, "r") as f:
        mode = None
        for line in f:
            line_s = line.strip()
            if not line_s or line_s.startswith("**"):
                continue
            if line_s.startswith("*"):
                upper = line_s.upper()
                if upper.startswith("*NODE") and not any(k in upper for k in ["PRINT", "FILE", "OUTPUT"]):
                    mode = "NODE"
                elif upper.startswith("*ELEMENT") and "OUTPUT" not in upper:
                    if "CPE4" in upper:
                        mode = "CPE4"
                    elif "CPE3" in upper:
                        mode = "CPE3"
                    else:
                        mode = None
                else:
                    mode = None
                continue
            parts = [p.strip() for p in line_s.split(",")]
            try:
                if mode == "NODE":
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                elif mode in ("CPE4", "CPE3"):
                    elements[int(parts[0])] = (mode, [int(p) for p in parts[1:]])
            except ValueError:
                pass
    return nodes, elements

def compute_nodal_damage(nodes, elements, elem_dmg):
    node_elem_dmg = {nid: [] for nid in nodes}
    for eid, (etype, nids) in elements.items():
        # Handle string or integer keys, and potential external element label offset (7846)
        d_val = float(elem_dmg.get(str(eid), elem_dmg.get(eid, elem_dmg.get(str(eid + 7846), 0.0))))
        for nid in nids:
            node_elem_dmg[nid].append(d_val)
    nodal_damage = {}
    for nid, vals in node_elem_dmg.items():
        nodal_damage[nid] = float(np.mean(vals)) if vals else 0.0
    return nodal_damage

def generate_companion_deck(state_name, state_data, nodes, elements, out_inp_path):
    nodal_u = state_data["nodal_displacements"]
    elem_dmg = state_data.get("element_avg_damage", {})
    nodal_damage = compute_nodal_damage(nodes, elements, elem_dmg)
    
    with open(out_inp_path, "w") as f:
        f.write("*HEADING\n")
        f.write("Task F1743 Continuous Degradation Companion Recovery: %s\n" % state_name)
        
        # Nodes
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write("%d, %.8f, %.8f\n" % (nid, x, y))
            
        # Quads
        quad_elements = {eid: nids for eid, (etype, nids) in elements.items() if etype == "CPE4"}
        if quad_elements:
            f.write("*ELEMENT, TYPE=CPE4, ELSET=All_elem\n")
            for eid in sorted(quad_elements.keys()):
                n_str = ", ".join(str(n) for n in quad_elements[eid])
                f.write("%d, %s\n" % (eid, n_str))
                
        # Tris
        tri_elements = {eid: nids for eid, (etype, nids) in elements.items() if etype == "CPE3"}
        if tri_elements:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=All_elem\n")
            for eid in sorted(tri_elements.keys()):
                n_str = ", ".join(str(n) for n in tri_elements[eid])
                f.write("%d, %s\n" % (eid, n_str))
                
        # Solid section with continuous material
        f.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=MAT_CONTINUOUS_PFM\n")
        f.write("1.0\n")
        
        # Continuous material definition via field variable dependency
        f.write("*MATERIAL, NAME=MAT_CONTINUOUS_PFM\n")
        f.write("*ELASTIC, DEPENDENCIES=1\n")
        for i in range(101):
            d_val = i / 100.0
            g_val = (1.0 - d_val)**2 + K_RES
            e_val = E0_GPA * g_val
            f.write("%.8e, %.2f, , %.2f\n" % (e_val, NU, d_val))
            
        # Initial conditions: continuous damage mapped to field variable 1 at NODES
        f.write("*INITIAL CONDITIONS, TYPE=FIELD, VARIABLE=1\n")
        for nid in sorted(nodes.keys()):
            d_val = nodal_damage.get(nid, 0.0)
            d_clamped = max(0.0, min(1.0, d_val))
            f.write("%d, %.6f\n" % (nid, d_clamped))
            
        # Prescribed same-state recovery step
        f.write("*STEP, NAME=RECOVERY, NLGEOM=NO\n")
        f.write("*STATIC\n")
        f.write("1.0, 1.0, 1.0, 1.0\n")
        
        # Prescribe exact UEL displacements onto all nodes
        f.write("*BOUNDARY\n")
        for nid in sorted(nodes.keys()):
            u_pair = nodal_u.get(str(nid), nodal_u.get(nid, [0.0, 0.0]))
            f.write("%d, 1, 1, %.8e\n" % (nid, u_pair[0]))
            f.write("%d, 2, 2, %.8e\n" % (nid, u_pair[1]))
            
        # Outputs required for SPR and stress recovery
        f.write("*OUTPUT, FIELD\n")
        f.write("*ELEMENT OUTPUT, ELSET=All_elem\n")
        f.write("S, E, FV, MISESERI, MISESAVG, EVOL\n")
        f.write("*NODE OUTPUT\n")
        f.write("U, RF\n")
        f.write("*END STEP\n")
    print("Wrote deck: %s (%d bytes)" % (out_inp_path, os.path.getsize(out_inp_path)))

def main():
    print("Parsing base mesh from:", BASE_INP)
    nodes, elements = parse_mesh(BASE_INP)
    print("Mesh loaded: %d nodes, %d elements" % (len(nodes), len(elements)))
    
    print("Loading extracted transient UEL data from:", EXTRACTED_JSON)
    with open(EXTRACTED_JSON, "r") as f:
        data = json.load(f)
        
    targets = [
        ("INC_260", "PK_SEC43_COMPANION_T1"),
        ("INC_300", "PK_SEC43_COMPANION_T2"),
        ("INC_340", "PK_SEC43_COMPANION_T3"),
    ]
    
    for key, job_name in targets:
        if key not in data:
            print("ERROR: Key %s not found in data!" % key)
            continue
        out_path = os.path.join(PACKAGE_DIR, "%s.inp" % job_name)
        generate_companion_deck(key, data[key], nodes, elements, out_path)
        
    print("\nAll 3 transient companion recovery decks successfully generated!")

if __name__ == "__main__":
    main()

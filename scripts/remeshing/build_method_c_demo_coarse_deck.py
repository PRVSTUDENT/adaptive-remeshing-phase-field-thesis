# -*- coding: utf-8 -*-
"""
scripts/remeshing/build_method_c_demo_coarse_deck.py
===================================================
Task: METHOD-C-PHASE1-DEMO-AND-LOOP-SKELETON
Builds the authentic 3-layer Method A / Method C coupled production deck
PK_METHOD_C_DEMO_COARSE_JOB1.inp from PK_METHOD_C_DEMO_COARSE_PHYS.inp.
"""

from __future__ import print_function
import os
import sys
import json
import hashlib

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "289_method_c_demo_case")
PHYS_INP = os.path.join(CASE_DIR, "PK_METHOD_C_DEMO_COARSE_PHYS.inp")
COUPLED_INP = os.path.join(CASE_DIR, "PK_METHOD_C_DEMO_COARSE_JOB1.inp")
RECEIPT_JSON = os.path.join(CASE_DIR, "PK_METHOD_C_DEMO_COARSE_RECEIPT.json")

def compute_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            h.update(chunk)
    return h.hexdigest().upper()

def compute_body_sha256(path):
    h = hashlib.sha256()
    with open(path, "r") as f:
        for line in f:
            stripped = line.strip()
            if not stripped.startswith("**"):
                h.update((stripped + "\n").encode("utf-8"))
    return h.hexdigest().upper()

def build_demo_deck():
    nodes = {}
    quad_elems = {}
    tri_elems = {}

    in_nodes = False
    in_elements = False
    elem_type = None

    with open(PHYS_INP, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                in_nodes = False
                in_elements = False
                u = l.upper()
                if u.startswith("*NODE"):
                    in_nodes = True
                elif u.startswith("*ELEMENT"):
                    in_elements = True
                    if "CPE4" in u or "CPS4" in u or "QUAD" in u:
                        elem_type = "QUAD"
                    elif "CPE3" in u or "CPS3" in u or "TRI" in u:
                        elem_type = "TRI"
                    else:
                        elem_type = "UNKNOWN"
                continue

            parts = [p.strip() for p in l.split(",") if p.strip()]
            if in_nodes and len(parts) >= 3:
                try:
                    nid = int(parts[0])
                    nodes[nid] = (float(parts[1]), float(parts[2]))
                except ValueError:
                    pass
            elif in_elements and len(parts) >= 4:
                try:
                    int_parts = [int(p) for p in parts]
                    eid = int_parts[0]
                    conn = int_parts[1:]
                    if elem_type == "QUAD" or len(conn) == 4:
                        quad_elems[eid] = tuple(conn[:4])
                    else:
                        tri_elems[eid] = tuple(conn[:3])
                except ValueError:
                    pass

    num_quads = len(quad_elems)
    num_tris = len(tri_elems)
    num_phys = num_quads + num_tris
    num_nodes = len(nodes)

    print("Parsed Physical Mesh: %d nodes, %d elements (%d quads, %d tris)" % (
        num_nodes, num_phys, num_quads, num_tris
    ))

    # Boundary node sets
    tol = 1e-4
    bottom_nodes = sorted([nid for nid, (x, y) in nodes.items() if abs(y - 0.0) < tol])
    top_nodes = sorted([nid for nid, (x, y) in nodes.items() if abs(y - 1.0) < tol])
    pin_candidates = [nid for nid in bottom_nodes if abs(nodes[nid][0] - 0.0) < tol]
    pin_node = min(pin_candidates) if pin_candidates else bottom_nodes[0]
    rp_nid = 999999

    print("Boundary sets: %d bottom nodes, %d top nodes, pin node %d" % (
        len(bottom_nodes), len(top_nodes), pin_node
    ))

    # Renumber physical elements 1 .. num_phys deterministically
    new_quads = {}
    new_tris = {}
    new_eid = 1
    for old_eid in sorted(quad_elems.keys()):
        new_quads[new_eid] = quad_elems[old_eid]
        new_eid += 1
    for old_eid in sorted(tri_elems.keys()):
        new_tris[new_eid] = tri_elems[old_eid]
        new_eid += 1

    disp_offset = num_phys
    umat_offset = 2 * num_phys

    with open(COUPLED_INP, "w") as out:
        out.write("** ==========================================================\n")
        out.write("** METHOD C DEMONSTRATION BENCHMARK COARSE PHASE-FIELD MODEL\n")
        out.write("** Physical elements: %d (Quads: %d, Tris: %d), Nodes: %d\n" % (
            num_phys, num_quads, num_tris, num_nodes
        ))
        out.write("** Layered elements: %d, Total nodes: %d\n" % (
            3 * num_phys, num_nodes + 1
        ))
        out.write("** Direct UEL-UMAT stress coupling via COMMON /CB_F1720_STRESS/\n")
        out.write("** ==========================================================\n")
        out.write("*HEADING\n")
        out.write("Method C Demo Case Coarse Simulation with Direct UEL-UMAT Coupling\n")

        # UEL declarations
        out.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
        out.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
        if num_tris > 0:
            out.write("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
            out.write("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")

        # Nodes
        out.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            out.write("%d, %.9e, %.9e\n" % (nid, x, y))
        out.write("%d, %.9e, %.9e\n" % (rp_nid, 0.5, 1.0))

        # Layer 1: Phase field (DOF 3)
        if new_quads:
            out.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD\n")
            for eid in sorted(new_quads.keys()):
                out.write("%d, %s\n" % (eid, ", ".join(str(n) for n in new_quads[eid])))
        if new_tris:
            out.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI\n")
            for eid in sorted(new_tris.keys()):
                out.write("%d, %s\n" % (eid, ", ".join(str(n) for n in new_tris[eid])))

        # Layer 2: Displacement (DOF 1, 2)
        if new_quads:
            out.write("*ELEMENT, TYPE=U2, ELSET=DISP_QUAD\n")
            for eid in sorted(new_quads.keys()):
                out.write("%d, %s\n" % (eid + disp_offset, ", ".join(str(n) for n in new_quads[eid])))
        if new_tris:
            out.write("*ELEMENT, TYPE=U4, ELSET=DISP_TRI\n")
            for eid in sorted(new_tris.keys()):
                out.write("%d, %s\n" % (eid + disp_offset, ", ".join(str(n) for n in new_tris[eid])))

        # Layer 3: Visualizer CPE4/CPE3 companion elements
        if new_quads:
            out.write("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS\n")
            for eid in sorted(new_quads.keys()):
                out.write("%d, %s\n" % (eid + umat_offset, ", ".join(str(n) for n in new_quads[eid])))
        if new_tris:
            out.write("*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS\n")
            for eid in sorted(new_tris.keys()):
                out.write("%d, %s\n" % (eid + umat_offset, ", ".join(str(n) for n in new_tris[eid])))

        # Sets
        out.write("*ELSET, ELSET=PHASE_ELEM\nPHASE_QUAD\n")
        if new_tris:
            out.write("PHASE_TRI\n")
        out.write("*ELSET, ELSET=MECH_ELEM\nDISP_QUAD\n")
        if new_tris:
            out.write("DISP_TRI\n")
        out.write("*ELSET, ELSET=All_elem\nUMAT_QUADS\n")
        if new_tris:
            out.write("UMAT_TRIS\n")
        out.write("*ELSET, ELSET=umatelem\nAll_elem\n")

        # Node sets (wrapped at 16 entries per line)
        def write_nset(name, nlist):
            out.write("*NSET, NSET=%s\n" % name)
            for i in range(0, len(nlist), 16):
                chunk = nlist[i:i+16]
                out.write(", ".join(str(n) for n in chunk) + "\n")

        write_nset("N_BOTTOM", bottom_nodes)
        write_nset("N_TOP", top_nodes)
        out.write("*NSET, NSET=N_PIN\n%d\n" % pin_node)
        out.write("*NSET, NSET=N_RP\n%d\n" % rp_nid)

        # Properties
        num_phys_f = float(num_phys)
        l0 = 0.007500
        gc = 0.002700
        e_mod = 210.00
        nu = 0.30
        k_res = 1.0e-07
        out.write("*UEL PROPERTY, ELSET=PHASE_ELEM\n")
        out.write("%.6f, %.6f, %.2f, %.2f, %.1e, %.1f\n" % (l0, gc, e_mod, nu, k_res, num_phys_f))
        out.write("*UEL PROPERTY, ELSET=MECH_ELEM\n")
        out.write("%.6f, %.6f, %.2f, %.2f, %.1e, %.1f\n" % (l0, gc, e_mod, nu, k_res, num_phys_f))

        out.write("*SOLID SECTION, ELSET=umatelem, MATERIAL=UMAT_MAT\n1.0\n")
        out.write("*MATERIAL, NAME=UMAT_MAT\n")
        out.write("*USER MATERIAL, CONSTANTS=4\n")
        out.write("%.2f, %.2f, %.1f, 1.0\n" % (e_mod, nu, num_phys_f))
        out.write("*DEPVAR\n20\n")

        # Rigid tie equations: top nodes tied to RP in DOF 2
        out.write("** ----------------------------------------------------------\n")
        out.write("** EQUATIONS (Rigid top tensile pull tied to RP in DOF 2)\n")
        out.write("** ----------------------------------------------------------\n")
        for nid in top_nodes:
            out.write("*EQUATION\n2\n")
            out.write("%d, 2, 1.0, %d, 2, -1.0\n" % (nid, rp_nid))

        # Step 1: Precritical loading to uy = 0.0050 mm
        out.write("** ----------------------------------------------------------\n")
        out.write("** STEP 1: Linear elastic loading to u_y = 0.0050 mm (50 incs)\n")
        out.write("** ----------------------------------------------------------\n")
        out.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=1000\n")
        out.write("*STATIC\n0.02, 1.0, 1.0E-07, 0.02\n")
        out.write("*BOUNDARY\n")
        out.write("N_BOTTOM, 2, 2, 0.0\n")
        out.write("N_PIN, 1, 1, 0.0\n")
        out.write("N_RP, 1, 1, 0.0\n")
        out.write("N_RP, 2, 2, 0.0050\n")
        out.write("*OUTPUT, FIELD, FREQUENCY=5\n")
        out.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        out.write("*NODE OUTPUT, NSET=N_BOTTOM\nRF\n")
        out.write("*NODE OUTPUT\nU\n")
        out.write("*ELEMENT OUTPUT, ELSET=umatelem\nS, MISESERI, MISESAVG, EVOL, SDV\n")
        out.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        out.write("*END STEP\n")

        # Step 2: Fracture localization regime to u_y = 0.0100 mm (partitioned into 5 increments)
        out.write("** ----------------------------------------------------------\n")
        out.write("** STEP 2: Progressive localization to u_y = 0.0100 mm\n")
        out.write("** ----------------------------------------------------------\n")
        out.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=5000\n")
        out.write("*STATIC\n0.002, 1.0, 1.0E-08, 0.005\n")
        out.write("*BOUNDARY\n")
        out.write("N_RP, 2, 2, 0.0100\n")
        out.write("*OUTPUT, FIELD, FREQUENCY=2\n")
        out.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        out.write("*NODE OUTPUT, NSET=N_BOTTOM\nRF\n")
        out.write("*NODE OUTPUT\nU\n")
        out.write("*ELEMENT OUTPUT, ELSET=umatelem\nS, MISESERI, MISESAVG, EVOL, SDV\n")
        out.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        out.write("*END STEP\n")

    phys_sha = compute_sha256(PHYS_INP)
    coupled_sha = compute_sha256(COUPLED_INP)
    coupled_body_sha = compute_body_sha256(COUPLED_INP)

    receipt = {
        "benchmark": "METHOD_C_DEMO_PLATE_ON_AXIS_HOLE",
        "geometry": {
            "plate_width_mm": 1.0,
            "plate_height_mm": 1.0,
            "notch_length_mm": 0.5,
            "notch_y_mm": 0.5,
            "hole_center_mm": [0.75, 0.50],
            "hole_radius_mm": 0.10,
            "inter_ligament_mm": 0.15,
            "rear_ligament_mm": 0.15
        },
        "mesh_statistics": {
            "physical_elements": num_phys,
            "quad_elements": num_quads,
            "tri_elements": num_tris,
            "quad_fraction_pct": round(100.0 * num_quads / num_phys, 2),
            "physical_nodes": num_nodes,
            "layered_elements": 3 * num_phys,
            "total_nodes_with_rp": num_nodes + 1
        },
        "material": {
            "E_GPa": 210.0,
            "nu": 0.30,
            "Gc_kN_per_mm": 0.0027,
            "l0_mm": 0.0075,
            "k_residual": 1.0e-07
        },
        "loading": {
            "step1_u2_mm": 0.0050,
            "step2_u2_mm": 0.0100,
            "step2_increments": 5
        },
        "artifacts": {
            "physical_inp": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_COARSE_PHYS.inp",
            "physical_inp_sha256": phys_sha,
            "coupled_inp": "models/pandey_kumar_mode1/289_method_c_demo_case/PK_METHOD_C_DEMO_COARSE_JOB1.inp",
            "coupled_inp_sha256": coupled_sha,
            "coupled_inp_body_sha256": coupled_body_sha
        }
    }

    with open(RECEIPT_JSON, "w") as f:
        json.dump(receipt, f, indent=2)

    print("\nSUCCESS: Built 3-layer Method C demo coarse deck!")
    print("  Coupled deck: %s" % COUPLED_INP)
    print("  Coupled SHA:  %s" % coupled_sha)
    print("  Body SHA:     %s" % coupled_body_sha)
    print("  Receipt:      %s" % RECEIPT_JSON)

if __name__ == "__main__":
    build_demo_deck()

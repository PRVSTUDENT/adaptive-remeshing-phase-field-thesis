# -*- coding: utf-8 -*-
"""
scripts/remeshing/build_method_c_case3_coarse_deck.py
===================================================
Task: METHOD-C-CASE3-ADAPTATION-PACKAGE
Builds the authentic 3-layer Method C coupled production deck
PK_METHOD_C_CASE3_COARSE_JOB1.inp from PK_METHOD_C_CASE3_COARSE_PHYS.inp.

Benchmark: Pandey & Kumar (2025) Section 4.3 Rectangular Notched Plate with Hole and Pins
- Dimensions: 65 x 120 mm plate, notch a = 10 mm at y = 70 mm, slit opening = 0.2 mm
- Central hole: (36.5, 51.0) mm, r = 10.0 mm
- Pin holes: Lower (20.0, 20.0) mm, r = 5.0 mm; Upper (20.0, 100.0) mm, r = 5.0 mm
- Material: E = 210.0 GPa, nu = 0.30, l0 = 0.285 mm, Gc = 0.00228 kN/mm, k = 1.0e-7
- Loading: PIN_HOLE_PULL (Lower hole encastre, Upper hole tied in DOF 2 to RP node 999999)
- Step 1: Pre-critical loading to u2 = 0.05 mm (50 increments, delta_u = 0.001 mm)
- Initial conditions: TYPE=SOLUTION only, strictly no TYPE=DISPLACEMENT
"""

from __future__ import print_function
import os
import sys
import math
import json
import hashlib

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
CASE_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3")
PHYS_INP = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_COARSE_PHYS.inp")
COUPLED_INP = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_COARSE_JOB1.inp")
RECEIPT_JSON = os.path.join(CASE_DIR, "PK_METHOD_C_CASE3_COARSE_RECEIPT.json")

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

def write_wrapped_nset(f, nset_name, node_list, max_per_line=16):
    f.write("*NSET, NSET=%s\n" % nset_name)
    sorted_nodes = sorted(node_list)
    for i in range(0, len(sorted_nodes), max_per_line):
        chunk = sorted_nodes[i:i + max_per_line]
        f.write(", ".join(str(n) for n in chunk) + "\n")

def build_case3_coarse_deck():
    nodes = {}
    quad_elems = {}
    tri_elems = {}

    in_nodes = False
    in_elements = False
    elem_type = None

    print("[Case 3 Build] Parsing physical mesh: %s" % PHYS_INP)
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

    print("  Parsed: %d nodes, %d elements (%d quads, %d tris)" % (
        num_nodes, num_phys, num_quads, num_tris
    ))

    # Boundary sets: Pin holes (R=5.0 mm at (20, 20) and (20, 100))
    low_hole_nodes = [nid for nid, (x, y) in nodes.items() if abs(math.hypot(x - 20.0, y - 20.0) - 5.0) < 0.05]
    upp_hole_nodes = [nid for nid, (x, y) in nodes.items() if abs(math.hypot(x - 20.0, y - 100.0) - 5.0) < 0.05]
    central_hole_nodes = [nid for nid, (x, y) in nodes.items() if abs(math.hypot(x - 36.5, y - 51.0) - 10.0) < 0.05]

    print("  Boundary sets: Lower hole: %d nodes, Upper hole: %d nodes, Central hole: %d nodes" % (
        len(low_hole_nodes), len(upp_hole_nodes), len(central_hole_nodes)
    ))

    rp_nid = 999999
    offset_disp = num_phys
    offset_vis = 2 * num_phys

    # Case 3 parameters
    l0 = 0.2850
    Gc = 0.002280
    E_GPa = 210.0
    nu = 0.30
    k_res = 1.0e-07
    step1_u2 = 0.050
    step2_u2 = 0.4125

    with open(COUPLED_INP, "w") as out:
        out.write("** ==========================================================\n")
        out.write("** METHOD C CASE 3 PRODUCTION DECK: PK_METHOD_C_CASE3_COARSE_JOB1\n")
        out.write("** Benchmark: Pandey & Kumar (2025) Section 4.3 Rectangular Notched Plate with Hole and Pins\n")
        out.write("** Physical Mesh: %d elements (%d quads, %d tris), %d nodes\n" % (num_phys, num_quads, num_tris, num_nodes))
        out.write("** Layered Elements: 3 x %d = %d total elements\n" % (num_phys, 3 * num_phys))
        out.write("** Subroutine: f42_mixed_uel.for (CE8D5EDC...)\n")
        out.write("** Initial Conditions: TYPE=SOLUTION only (strictly no TYPE=DISPLACEMENT)\n")
        out.write("** ==========================================================\n")
        out.write("*HEADING\nMethod C Case 3: Pandey-Kumar Sec 4.3 Notched Plate with Pins Job-1 Coarse\n")
        out.write("*PREPRINT, ECHO=NO, MODEL=NO, HISTORY=NO\n\n")

        # Nodes
        out.write("** ----------------------------------------------------------\n")
        out.write("** NODES\n")
        out.write("** ----------------------------------------------------------\n")
        out.write("*NODE, NSET=ALLNODES\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            out.write("%d, %.12g, %.12g\n" % (nid, x, y))
        out.write("%d, 20.0, 100.0\n" % rp_nid)

        # Layer 1: Phase field UEL (DOF 3)
        out.write("** ----------------------------------------------------------\n")
        out.write("** LAYER 1: Phase-Field User Elements (DOF 3)\n")
        out.write("** ----------------------------------------------------------\n")
        if quad_elems:
            out.write("*USER ELEMENT, NODES=4, TYPE=U1, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n3\n")
            out.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                c = quad_elems[eid]
                out.write("%d, %s\n" % (eid, ", ".join(str(n) for n in c)))
        if tri_elems:
            out.write("*USER ELEMENT, NODES=3, TYPE=U3, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n3\n")
            out.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI\n")
            for eid in sorted(tri_elems.keys()):
                c = tri_elems[eid]
                out.write("%d, %s\n" % (eid, ", ".join(str(n) for n in c)))

        # Layer 2: Mechanical displacement UEL (DOF 1, 2)
        out.write("** ----------------------------------------------------------\n")
        out.write("** LAYER 2: Mechanical Displacement User Elements (DOF 1, 2)\n")
        out.write("** ----------------------------------------------------------\n")
        if quad_elems:
            out.write("*USER ELEMENT, NODES=4, TYPE=U2, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n1, 2\n")
            out.write("*ELEMENT, TYPE=U2, ELSET=DISP_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                c = quad_elems[eid]
                out.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in c)))
        if tri_elems:
            out.write("*USER ELEMENT, NODES=3, TYPE=U4, PROPERTIES=6, COORDINATES=2, VARIABLES=18, UNSYMM\n1, 2\n")
            out.write("*ELEMENT, TYPE=U4, ELSET=DISP_TRI\n")
            for eid in sorted(tri_elems.keys()):
                c = tri_elems[eid]
                out.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in c)))

        # Layer 3: Companion visualizer elements
        out.write("** ----------------------------------------------------------\n")
        out.write("** LAYER 3: Companion Visualizer Elements (CPE4 / CPE3)\n")
        out.write("** ----------------------------------------------------------\n")
        if quad_elems:
            out.write("*ELEMENT, TYPE=CPE4, ELSET=umatelem_quad\n")
            for eid in sorted(quad_elems.keys()):
                c = quad_elems[eid]
                out.write("%d, %s\n" % (eid + offset_vis, ", ".join(str(n) for n in c)))
        if tri_elems:
            out.write("*ELEMENT, TYPE=CPE3, ELSET=umatelem_tri\n")
            for eid in sorted(tri_elems.keys()):
                c = tri_elems[eid]
                out.write("%d, %s\n" % (eid + offset_vis, ", ".join(str(n) for n in c)))

        # Element sets
        out.write("*ELSET, ELSET=All_elem\n")
        if quad_elems and tri_elems:
            out.write("umatelem_quad, umatelem_tri\n")
        elif quad_elems:
            out.write("umatelem_quad\n")
        else:
            out.write("umatelem_tri\n")
        out.write("*ELSET, ELSET=umatelem\nAll_elem\n")

        # Boundary Node sets
        out.write("** ----------------------------------------------------------\n")
        out.write("** BOUNDARY NODE SETS\n")
        out.write("** ----------------------------------------------------------\n")
        write_wrapped_nset(out, "N_LOWER_HOLE", low_hole_nodes)
        write_wrapped_nset(out, "N_UPPER_HOLE", upp_hole_nodes)
        out.write("*NSET, NSET=N_RP\n%d\n" % rp_nid)

        # UEL Properties
        num_phys_f = float(num_phys)
        if quad_elems:
            out.write("*UEL PROPERTY, ELSET=PHASE_QUAD\n")
            out.write("%.4f, %.6f, %.1f, %.2f, %.1e, %.1f\n" % (l0, Gc, E_GPa, nu, k_res, num_phys_f))
            out.write("*UEL PROPERTY, ELSET=DISP_QUAD\n")
            out.write("%.4f, %.6f, %.1f, %.2f, %.1e, %.1f\n" % (l0, Gc, E_GPa, nu, k_res, num_phys_f))
        if tri_elems:
            out.write("*UEL PROPERTY, ELSET=PHASE_TRI\n")
            out.write("%.4f, %.6f, %.1f, %.2f, %.1e, %.1f\n" % (l0, Gc, E_GPa, nu, k_res, num_phys_f))
            out.write("*UEL PROPERTY, ELSET=DISP_TRI\n")
            out.write("%.4f, %.6f, %.1f, %.2f, %.1e, %.1f\n" % (l0, Gc, E_GPa, nu, k_res, num_phys_f))

        # Companion Solid Section & User Material
        out.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=DUMMY_MAT\n1.0\n")
        out.write("*MATERIAL, NAME=DUMMY_MAT\n")
        out.write("*USER MATERIAL, CONSTANTS=3\n")
        out.write("%.1f, %.2f, %.1f\n" % (E_GPa, nu, num_phys_f))
        out.write("*DEPVAR\n20\n")

        # Initial Conditions: TYPE=SOLUTION only (strictly no TYPE=DISPLACEMENT)
        out.write("** ----------------------------------------------------------\n")
        out.write("** INITIAL CONDITIONS: TYPE=SOLUTION only (Abaqus/Standard static)\n")
        out.write("** Zero initial history variables for virgin coarse solve\n")
        out.write("** ----------------------------------------------------------\n")
        out.write("*INITIAL CONDITIONS, TYPE=SOLUTION\n")
        out.write("umatelem, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0\n")
        out.write("0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0\n")
        out.write("0.0, 0.0, 0.0, 0.0\n")

        # Kinematic Coupling Equations: Upper pin hole tied to RP in DOF 2
        out.write("** ----------------------------------------------------------\n")
        out.write("** EQUATIONS (Rigid tensile pull of upper hole pin tied to RP in DOF 2)\n")
        out.write("** ----------------------------------------------------------\n")
        for nid in sorted(upp_hole_nodes):
            out.write("*EQUATION\n2\n")
            out.write("%d, 2, 1.0, %d, 2, -1.0\n" % (nid, rp_nid))

        # STEP 1: Linear Loading to u2 = 0.05 mm (50 incs, delta_u = 0.001 mm)
        out.write("** ----------------------------------------------------------\n")
        out.write("** STEP 1: Pre-critical linear elastic loading to u2 = %.4f mm\n" % step1_u2)
        out.write("** ----------------------------------------------------------\n")
        out.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=1000\n")
        out.write("*STATIC\n0.02, 1.0, 1.0E-07, 0.02\n")
        out.write("*BOUNDARY\n")
        out.write("N_LOWER_HOLE, 1, 2, 0.0\n")
        out.write("N_UPPER_HOLE, 1, 1, 0.0\n")
        out.write("N_RP, 1, 1, 0.0\n")
        out.write("N_RP, 2, 2, %.4f\n" % step1_u2)
        out.write("*OUTPUT, FIELD, FREQUENCY=5\n")
        out.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        out.write("*NODE OUTPUT, NSET=N_LOWER_HOLE\nRF\n")
        out.write("*NODE OUTPUT\nU\n")
        out.write("*ELEMENT OUTPUT, ELSET=umatelem\nS, MISESERI, MISESAVG, EVOL, SDV\n")
        out.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        out.write("*END STEP\n")

        # STEP 2: Forward crack propagation across ligament toward central hole (u2 = 0.050 mm -> 0.4125 mm)
        out.write("** ----------------------------------------------------------\n")
        out.write("** STEP 2: Forward crack propagation to u2 = %.4f mm\n" % step2_u2)
        out.write("** ----------------------------------------------------------\n")
        out.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=5000\n")
        out.write("*STATIC\n0.002, 1.0, 1.0E-08, 0.005\n")
        out.write("*BOUNDARY\n")
        out.write("N_RP, 2, 2, %.4f\n" % step2_u2)
        out.write("*OUTPUT, FIELD, FREQUENCY=2\n")
        out.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        out.write("*NODE OUTPUT, NSET=N_LOWER_HOLE\nRF\n")
        out.write("*NODE OUTPUT\nU\n")
        out.write("*ELEMENT OUTPUT, ELSET=umatelem\nS, MISESERI, MISESAVG, EVOL, SDV\n")
        out.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        out.write("*END STEP\n")

    phys_sha = compute_sha256(PHYS_INP)
    coupled_sha = compute_sha256(COUPLED_INP)
    coupled_body_sha = compute_body_sha256(COUPLED_INP)

    receipt = {
        "benchmark": "Pandey & Kumar (2025) Section 4.3 Rectangular Notched Plate with Hole and Pins",
        "case_id": "method_c_case3",
        "geometry": {
            "plate_width_mm": 65.0,
            "plate_height_mm": 120.0,
            "notch_length_mm": 10.0,
            "notch_y_mm": 70.0,
            "notch_slit_opening_mm": 0.20,
            "central_hole": {"x_mm": 36.5, "y_mm": 51.0, "r_mm": 10.0},
            "lower_pin_hole": {"x_mm": 20.0, "y_mm": 20.0, "r_mm": 5.0},
            "upper_pin_hole": {"x_mm": 20.0, "y_mm": 100.0, "r_mm": 5.0}
        },
        "mesh_statistics": {
            "physical_elements": num_phys,
            "quad_elements": num_quads,
            "tri_elements": num_tris,
            "quad_fraction_pct": round(100.0 * num_quads / num_phys, 2),
            "physical_nodes": num_nodes,
            "layered_elements": 3 * num_phys,
            "total_nodes_with_rp": num_nodes + 1,
            "rp_node_id": rp_nid
        },
        "material": {
            "E_GPa": E_GPa,
            "nu": nu,
            "Gc_kN_per_mm": Gc,
            "l0_mm": l0,
            "k_residual": k_res,
            "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        },
        "loading": {
            "loading_type": "PIN_HOLE_PULL",
            "step1_u2_mm": step1_u2,
            "step2_u2_mm": step2_u2,
            "lower_hole_nodes_count": len(low_hole_nodes),
            "upper_hole_nodes_count": len(upp_hole_nodes),
            "initial_conditions_protocol": "TYPE=SOLUTION only (strictly no TYPE=DISPLACEMENT)"
        },
        "artifacts": {
            "physical_inp": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_COARSE_PHYS.inp",
            "physical_inp_sha256": phys_sha,
            "coupled_inp": "models/pandey_kumar_mode1/290_method_c_case3/PK_METHOD_C_CASE3_COARSE_JOB1.inp",
            "coupled_inp_sha256": coupled_sha,
            "coupled_inp_body_sha256": coupled_body_sha
        }
    }

    with open(RECEIPT_JSON, "w") as f:
        json.dump(receipt, f, indent=2)

    print("\nSUCCESS: Built 3-layer Method C Case 3 coarse deck!")
    print("  Coupled deck: %s" % COUPLED_INP)
    print("  Coupled SHA:  %s" % coupled_sha)
    print("  Body SHA:     %s" % coupled_body_sha)
    print("  Receipt:      %s" % RECEIPT_JSON)
    return receipt

if __name__ == "__main__":
    build_case3_coarse_deck()

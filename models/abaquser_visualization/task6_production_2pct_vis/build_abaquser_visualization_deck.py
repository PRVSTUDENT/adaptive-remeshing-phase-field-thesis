import os
import sys
import hashlib

def compute_sha256(filepath):
    if not os.path.exists(filepath):
        return ""
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def build_vis_deck(phys_inp_path, target_inp_path, error_target_str="2.0%"):
    nodes = {}
    quad_elems = {}
    tri_elems = {}

    with open(phys_inp_path, 'r') as f:
        section = None
        for line in f:
            line_str = line.strip()
            if not line_str or line_str.startswith("**"):
                continue
            if line_str.startswith("*"):
                upline = line_str.upper()
                if upline.startswith("*NODE"):
                    section = "NODE"
                elif upline.startswith("*ELEMENT"):
                    if "CPS4" in upline or "CPE4" in upline or "QUAD" in upline or "TYPE=U1" in upline or "TYPE=U2" in upline:
                        section = "QUAD"
                    elif "CPS3" in upline or "CPE3" in upline or "TRI" in upline or "TYPE=U3" in upline or "TYPE=U4" in upline:
                        section = "TRI"
                    else:
                        section = "QUAD"
                else:
                    section = None
                continue

            if section == "NODE":
                parts = [p.strip() for p in line_str.split(',')]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
                    except ValueError:
                        pass
            elif section == "QUAD":
                parts = [p.strip() for p in line_str.split(',')]
                if len(parts) >= 5:
                    try:
                        eid = int(parts[0])
                        n1, n2, n3, n4 = int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])
                        quad_elems[eid] = (n1, n2, n3, n4)
                    except ValueError:
                        pass
            elif section == "TRI":
                parts = [p.strip() for p in line_str.split(',')]
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        n1, n2, n3 = int(parts[1]), int(parts[2]), int(parts[3])
                        tri_elems[eid] = (n1, n2, n3)
                    except ValueError:
                        pass

    num_phys_nodes = len(nodes)
    num_phys_quads = len(quad_elems)
    num_phys_tris = len(tri_elems)
    num_phys_elems = num_phys_quads + num_phys_tris

    print("Loaded %s: %d nodes, %d elements (%d quads, %d tris)" %
          (error_target_str, num_phys_nodes, num_phys_elems, num_phys_quads, num_phys_tris))

    # Identify boundary nodes
    bottom_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 0.0) < 1e-4]
    top_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 1.0) < 1e-4]
    pin_candidates = [nid for nid in bottom_nodes if abs(nodes[nid][0] - 0.0) < 1e-4]
    pin_node = min(pin_candidates) if pin_candidates else bottom_nodes[0]
    rp_nid = 999999

    print("Boundary Nodes: Bottom=%d, Top=%d, Pin Node=%d, RP Node=%d" %
          (len(bottom_nodes), len(top_nodes), pin_node, rp_nid))

    with open(target_inp_path, 'w') as f:
        f.write("*HEADING\n")
        f.write("Pandey & Kumar (2025) Mode-I %s ABAQUSER Visualization Production Solve (Sharp Slit)\n" % error_target_str)
        f.write("** Physical Elements: %d (%d quads, %d tris), Nodes: %d\n" %
                (num_phys_elems, num_phys_quads, num_phys_tris, num_phys_nodes))
        f.write("** Parameters: E=210.0 kN/mm^2, nu=0.3, l0=0.0075 mm, Gc=0.0027 kN/mm, k=1.0e-7\n")
        f.write("** ----------------------------------------------------------\n")

        # User Element Interfaces (Clean 6-Slot Property ABI)
        f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
        f.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
        if num_phys_tris > 0:
            f.write("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
            f.write("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")

        # Nodes
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write("%d, %.10e, %.10e\n" % (nid, x, y))
        f.write("%d, 0.5, 1.0\n" % rp_nid)

        # Layer 1: Phase-field UEL (1..N_phys)
        if quad_elems:
            f.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in quad_elems[eid])))
        if tri_elems:
            f.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI\n")
            for eid in sorted(tri_elems.keys()):
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in tri_elems[eid])))

        # Layer 2: Displacement UEL (N_phys+1..2*N_phys)
        offset_disp = num_phys_elems
        if quad_elems:
            f.write("*ELEMENT, TYPE=U2, ELSET=DISP_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                f.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in quad_elems[eid])))
        if tri_elems:
            f.write("*ELEMENT, TYPE=U4, ELSET=DISP_TRI\n")
            for eid in sorted(tri_elems.keys()):
                f.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in tri_elems[eid])))

        # Layer 3: Companion UMAT Facsimile (2*N_phys+1..3*N_phys)
        offset_umat = 2 * num_phys_elems
        if quad_elems:
            f.write("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS\n")
            for eid in sorted(quad_elems.keys()):
                f.write("%d, %s\n" % (eid + offset_umat, ", ".join(str(n) for n in quad_elems[eid])))
        if tri_elems:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS\n")
            for eid in sorted(tri_elems.keys()):
                f.write("%d, %s\n" % (eid + offset_umat, ", ".join(str(n) for n in tri_elems[eid])))

        # Sets
        f.write("*ELSET, ELSET=All_elem\nUMAT_QUADS\n")
        if tri_elems:
            f.write("UMAT_TRIS\n")
        f.write("*ELSET, ELSET=umatelem\nAll_elem\n")

        def write_nset(file_handle, set_name, node_list):
            file_handle.write("*NSET, NSET=" + set_name + "\n")
            chunk_size = 10
            for i in range(0, len(node_list), chunk_size):
                chunk = node_list[i:i + chunk_size]
                file_handle.write(", ".join(str(n) for n in chunk) + "\n")

        write_nset(f, "N_BOTTOM", bottom_nodes)
        write_nset(f, "N_PIN", [pin_node])
        write_nset(f, "N_TOP", top_nodes)
        write_nset(f, "N_RP", [rp_nid])

        # UEL Properties: l0, Gc, E, nu, k, N_phys
        f.write("*UEL PROPERTY, ELSET=PHASE_QUAD\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.\n" % num_phys_elems)
        f.write("*UEL PROPERTY, ELSET=DISP_QUAD\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.\n" % num_phys_elems)
        if tri_elems:
            f.write("*UEL PROPERTY, ELSET=PHASE_TRI\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.\n" % num_phys_elems)
            f.write("*UEL PROPERTY, ELSET=DISP_TRI\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.\n" % num_phys_elems)

        # Companion UMAT Material Section with CONSTANTS=3 for ABAQUSER State Mapping
        f.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=DUMMY_MAT\n1.0\n")
        f.write("*MATERIAL, NAME=DUMMY_MAT\n*USER MATERIAL, CONSTANTS=3\n210.0, 0.3, %d.\n*DEPVAR\n18\n" % num_phys_elems)

        # Coupling Equations (Rigid top pull tied to RP)
        f.write("** EQUATIONS (Rigid top tensile pull tied to RP)\n")
        for tn in sorted(top_nodes):
            f.write("*EQUATION\n2\n%d, 2, 1.0, %d, 2, -1.0\n" % (tn, rp_nid))

        # Step 1: Monotonic loading to u = 0.0050 mm (2000 increments)
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 1: Monotonic Tensile Loading to u = 0.0050 mm (2000 increments)\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=6000\n")
        f.write("*STATIC\n5.0E-4, 1.0, 1.0E-9, 5.0E-4\n")
        f.write("*BOUNDARY\nN_BOTTOM, 2, 2, 0.0\nN_PIN, 1, 1, 0.0\nN_TOP, 1, 1, 0.0\nN_RP, 2, 2, 0.0050\n")
        f.write("*RESTART, WRITE, FREQUENCY=0\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*NODE OUTPUT\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV, S, E\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

        # Step 2: Fracture propagation to u = 0.0100 mm (5000 increments)
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 2: Fracture Propagation to u = 0.0100 mm (5000 increments)\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=10000\n")
        f.write("*STATIC\n2.0E-4, 1.0, 1.0E-14, 2.0E-4\n")
        f.write("*BOUNDARY\nN_RP, 2, 2, 0.0100\n")
        f.write("*RESTART, WRITE, FREQUENCY=0\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*NODE OUTPUT\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV, S, E\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

    sha256 = compute_sha256(target_inp_path)
    print("Wrote %s (SHA-256: %s)" % (target_inp_path, sha256))
    return {
        "num_nodes": num_phys_nodes,
        "num_elements": num_phys_elems,
        "num_quads": num_phys_quads,
        "num_tris": num_phys_tris,
        "sha256": sha256
    }

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        p_phys = sys.argv[1]
        p_out = sys.argv[2]
        err_str = sys.argv[3] if len(sys.argv) >= 4 else "2.0%"
        build_vis_deck(p_phys, p_out, err_str)
    else:
        print("Usage: python build_abaquser_visualization_deck.py <phys_inp> <out_inp> [error_target_str]")

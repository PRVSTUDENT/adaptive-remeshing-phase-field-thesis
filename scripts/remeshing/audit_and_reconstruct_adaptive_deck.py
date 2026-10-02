#!/usr/bin/env python3
import sys
import os
import math
import json
import hashlib

def main():
    raw_inp_path = r"C:\Users\pruth\.gemini\antigravity-cli\brain\7ab04046-3e47-424c-a416-7a68bfbe7f70\ModeII_Adaptive_Raw.inp"
    out_uel_path = r"C:\Users\pruth\.gemini\antigravity-cli\brain\7ab04046-3e47-424c-a416-7a68bfbe7f70\ModeII_adaptive_candidate.inp"
    
    print("Reading raw adaptive mesh deck:", raw_inp_path)
    
    nodes = {}
    quad_elems = {}
    tri_elems = {}
    
    in_nodes = False
    in_elements = False
    elem_type = None
    
    with open(raw_inp_path, "r", errors="ignore") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            lu = l.upper()
            if lu.startswith("*NODE") and not ("OUTPUT" in lu or "PRINT" in lu):
                in_nodes = True
                in_elements = False
                continue
            elif lu.startswith("*ELEMENT"):
                in_elements = True
                in_nodes = False
                if "CPS4" in lu or "CPE4" in lu or "QUAD" in lu or "S4" in lu or "CAX4" in lu:
                    elem_type = "QUAD"
                elif "CPS3" in lu or "CPE3" in lu or "TRI" in lu or "S3" in lu or "CAX3" in lu:
                    elem_type = "TRI"
                else:
                    elem_type = "QUAD"
                continue
            elif l.startswith("*"):
                in_nodes = False
                in_elements = False
                continue
                
            if in_nodes:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
                    except ValueError:
                        pass
            elif in_elements:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 4:
                    try:
                        int_parts = [int(p) for p in parts]
                        eid = int_parts[0]
                        conn = int_parts[1:]
                        if len(conn) == 4 or elem_type == "QUAD":
                            quad_elems[eid] = tuple(conn[:4])
                        else:
                            tri_elems[eid] = tuple(conn[:3])
                    except ValueError:
                        pass

    n_nodes = len(nodes)
    n_quads = len(quad_elems)
    n_tris = len(tri_elems)
    n_phys = n_quads + n_tris
    
    print("Parsed mesh:")
    print("  Total underlying finite elements (N_PHYS): %d" % n_phys)
    print("  Quads (CPS4): %d" % n_quads)
    print("  Triangles (CPS3): %d" % n_tris)
    print("  Nodes: %d" % n_nodes)
    
    # Compute element sizes h = sqrt(Area)
    l0 = 0.015 # mm
    quad_areas = []
    tri_areas = []
    
    all_h = []
    crack_zone_h = [] # x in [0.0, 0.5], y in [-0.25, 0.05]
    
    for eid, (n1, n2, n3, n4) in quad_elems.items():
        x1, y1 = nodes[n1]
        x2, y2 = nodes[n2]
        x3, y3 = nodes[n3]
        x4, y4 = nodes[n4]
        # Shoelace formula
        area = 0.5 * abs(x1*y2 - x2*y1 + x2*y3 - x3*y2 + x3*y4 - x4*y3 + x4*y1 - x1*y4)
        quad_areas.append(area)
        h = math.sqrt(area)
        all_h.append(h)
        cx = 0.25 * (x1 + x2 + x3 + x4)
        cy = 0.25 * (y1 + y2 + y3 + y4)
        if 0.0 <= cx <= 0.5 and -0.25 <= cy <= 0.05:
            crack_zone_h.append(h)
            
    for eid, (n1, n2, n3) in tri_elems.items():
        x1, y1 = nodes[n1]
        x2, y2 = nodes[n2]
        x3, y3 = nodes[n3]
        area = 0.5 * abs(x1*y2 - x2*y1 + x2*y3 - x3*y2 + x3*y1 - x1*y3)
        tri_areas.append(area)
        h = math.sqrt(2.0 * area) # or sqrt(4*area/sqrt(3))
        all_h.append(h)
        cx = (x1 + x2 + x3) / 3.0
        cy = (y1 + y2 + y3) / 3.0
        if 0.0 <= cx <= 0.5 and -0.25 <= cy <= 0.05:
            crack_zone_h.append(h)
            
    print("\n--- Mesh Resolution Statistics ---")
    print("Global h range:      [%.6f, %.6f] mm" % (min(all_h), max(all_h)))
    print("Global mean h:       %.6f mm" % (sum(all_h) / len(all_h)))
    all_h_sorted = sorted(all_h)
    median_h = all_h_sorted[len(all_h_sorted)//2]
    print("Global median h:     %.6f mm" % median_h)
    print("Global mean h/l0:    %.4f (l0 = %.4f mm)" % (sum(all_h)/(len(all_h)*l0), l0))
    print("Global median h/l0:  %.4f" % (median_h / l0))
    
    if crack_zone_h:
        cz_sorted = sorted(crack_zone_h)
        print("Crack zone elements: %d" % len(crack_zone_h))
        print("Crack zone h range:  [%.6f, %.6f] mm" % (min(crack_zone_h), max(crack_zone_h)))
        print("Crack zone mean h:   %.6f mm" % (sum(crack_zone_h) / len(crack_zone_h)))
        print("Crack zone median h: %.6f mm" % cz_sorted[len(cz_sorted)//2])
        print("Crack zone mean h/l0:%.4f" % (sum(crack_zone_h) / (len(crack_zone_h)*l0)))
        print("Crack zone median h/l0: %.4f" % (cz_sorted[len(cz_sorted)//2] / l0))

    # Identify Boundary Nodes
    tol = 1.0e-5
    bottom_nodes = sorted([nid for nid, (x, y) in nodes.items() if abs(y - (-0.5)) < tol])
    top_nodes = sorted([nid for nid, (x, y) in nodes.items() if abs(y - 0.5) < tol])
    left_nodes = sorted([nid for nid, (x, y) in nodes.items() if abs(x - (-0.5)) < tol])
    right_nodes = sorted([nid for nid, (x, y) in nodes.items() if abs(x - 0.5) < tol])
    
    print("\nBoundary Node Sets:")
    print("  Bottom nodes (y = -0.5 mm): %d" % len(bottom_nodes))
    print("  Top nodes (y = +0.5 mm):    %d" % len(top_nodes))
    print("  Left nodes (x = -0.5 mm):   %d" % len(left_nodes))
    print("  Right nodes (x = +0.5 mm):  %d" % len(right_nodes))
    
    # Reconstruct 3-layer UEL Deck
    rp_id = max(nodes.keys()) + 1
    rp_coords = (0.0, 0.6) # RP for top displacement coupling
    
    # Layer 1: Phase UEL (U1 for quads, U3 for tris) -> IDs 1 to N_PHYS
    # Layer 2: Mechanical UEL (U2 for quads, U4 for tris) -> IDs N_PHYS+1 to 2*N_PHYS
    # Layer 3: Companion UMAT (CPE4 for quads, CPE3 for tris) -> IDs 2*N_PHYS+1 to 3*N_PHYS
    # Total Abaqus Element Objects = 3 * N_PHYS
    
    all_sorted_eids = sorted(list(quad_elems.keys()) + list(tri_elems.keys()))
    # Map raw eids to compact 1..N_PHYS
    eid_map = {raw_eid: i+1 for i, raw_eid in enumerate(all_sorted_eids)}
    
    with open(out_uel_path, "w") as f:
        f.write("*Heading\n")
        f.write("Pandey & Kumar (2025) Mode-II Literature-Faithful Adaptive Refined PFM Model\n")
        f.write("** ------------------------------------------------------------------------\n")
        f.write("** Underlying Finite Elements: %d (%d quads, %d tris)\n" % (n_phys, n_quads, n_tris))
        f.write("** Total Abaqus Element Objects: %d (3 co-located layers x %d)\n" % (3 * n_phys, n_phys))
        f.write("** Unified 6-Slot Property ABI: 0.015, 0.0027, 210.0, 0.3, 1.0e-7, %d.0\n" % n_phys)
        f.write("** ------------------------------------------------------------------------\n")
        f.write("*Preprint, echo=NO, model=NO, history=NO, contact=NO\n")
        
        # User Element Declarations
        # Quad Phase: TYPE=U1 (DOF 3)
        f.write("*USER ELEMENT, NODES=4, TYPE=U1, PROPERTIES=6, COORDINATES=2, VARIABLES=18\n3\n")
        # Quad Mech: TYPE=U2 (DOFs 1, 2)
        f.write("*USER ELEMENT, NODES=4, TYPE=U2, PROPERTIES=6, COORDINATES=2, VARIABLES=18\n1, 2\n")
        if n_tris > 0:
            # Tri Phase: TYPE=U3 (DOF 3)
            f.write("*USER ELEMENT, NODES=3, TYPE=U3, PROPERTIES=6, COORDINATES=2, VARIABLES=18\n3\n")
            # Tri Mech: TYPE=U4 (DOFs 1, 2)
            f.write("*USER ELEMENT, NODES=3, TYPE=U4, PROPERTIES=6, COORDINATES=2, VARIABLES=18\n1, 2\n")
            
        # Nodes
        f.write("*Node\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write("%8d, %15.8e, %15.8e\n" % (nid, x, y))
        f.write("%8d, %15.8e, %15.8e\n" % (rp_id, rp_coords[0], rp_coords[1]))
        
        # Layer 1: Phase Elements (1 .. N_PHYS)
        if n_quads > 0:
            f.write("*Element, type=U1, elset=PHASE_QUAD\n")
            for raw_eid in sorted(quad_elems.keys()):
                uid = eid_map[raw_eid]
                conn = quad_elems[raw_eid]
                f.write("%8d, %8d, %8d, %8d, %8d\n" % (uid, conn[0], conn[1], conn[2], conn[3]))
        if n_tris > 0:
            f.write("*Element, type=U3, elset=PHASE_TRI\n")
            for raw_eid in sorted(tri_elems.keys()):
                uid = eid_map[raw_eid]
                conn = tri_elems[raw_eid]
                f.write("%8d, %8d, %8d, %8d\n" % (uid, conn[0], conn[1], conn[2]))
                
        # Layer 2: Mechanical Elements (N_PHYS+1 .. 2*N_PHYS)
        offset_mech = n_phys
        if n_quads > 0:
            f.write("*Element, type=U2, elset=DISP_QUAD\n")
            for raw_eid in sorted(quad_elems.keys()):
                uid = eid_map[raw_eid] + offset_mech
                conn = quad_elems[raw_eid]
                f.write("%8d, %8d, %8d, %8d, %8d\n" % (uid, conn[0], conn[1], conn[2], conn[3]))
        if n_tris > 0:
            f.write("*Element, type=U4, elset=DISP_TRI\n")
            for raw_eid in sorted(tri_elems.keys()):
                uid = eid_map[raw_eid] + offset_mech
                conn = tri_elems[raw_eid]
                f.write("%8d, %8d, %8d, %8d\n" % (uid, conn[0], conn[1], conn[2]))
                
        # Layer 3: Companion UMAT Elements (2*N_PHYS+1 .. 3*N_PHYS)
        offset_umat = 2 * n_phys
        if n_quads > 0:
            f.write("*Element, type=CPE4, elset=UMAT_QUAD\n")
            for raw_eid in sorted(quad_elems.keys()):
                uid = eid_map[raw_eid] + offset_umat
                conn = quad_elems[raw_eid]
                f.write("%8d, %8d, %8d, %8d, %8d\n" % (uid, conn[0], conn[1], conn[2], conn[3]))
        if n_tris > 0:
            f.write("*Element, type=CPE3, elset=UMAT_TRI\n")
            for raw_eid in sorted(tri_elems.keys()):
                uid = eid_map[raw_eid] + offset_umat
                conn = tri_elems[raw_eid]
                f.write("%8d, %8d, %8d, %8d\n" % (uid, conn[0], conn[1], conn[2]))

        # Elsets
        f.write("*Elset, elset=All_elem\n")
        f.write("UMAT_QUAD\n")
        if n_tris > 0:
            f.write("UMAT_TRI\n")
            
        f.write("*Elset, elset=All_phase\n")
        f.write("PHASE_QUAD\n")
        if n_tris > 0:
            f.write("PHASE_TRI\n")
            
        f.write("*Elset, elset=All_disp\n")
        f.write("DISP_QUAD\n")
        if n_tris > 0:
            f.write("DISP_TRI\n")

        # Nsets
        f.write("*Nset, nset=RP\n%d\n" % rp_id)
        
        f.write("*Nset, nset=bottom_nodes\n")
        for i in range(0, len(bottom_nodes), 16):
            chunk = bottom_nodes[i:i+16]
            f.write(", ".join(str(n) for n in chunk) + "\n")
            
        f.write("*Nset, nset=top_nodes\n")
        for i in range(0, len(top_nodes), 16):
            chunk = top_nodes[i:i+16]
            f.write(", ".join(str(n) for n in chunk) + "\n")

        # UEL Properties (6-slot ABI)
        # PROPS: l0=0.015, Gc=0.0027, E=210.0, nu=0.3, k=1e-7, N_PHYS
        f.write("*UEL Property, elset=PHASE_QUAD\n")
        f.write(" 1.500000e-02, 2.700000e-03, 2.100000e+02, 3.000000e-01, 1.000000e-07, %d.0\n" % n_phys)
        f.write("*UEL Property, elset=DISP_QUAD\n")
        f.write(" 1.500000e-02, 2.700000e-03, 2.100000e+02, 3.000000e-01, 1.000000e-07, %d.0\n" % n_phys)
        if n_tris > 0:
            f.write("*UEL Property, elset=PHASE_TRI\n")
            f.write(" 1.500000e-02, 2.700000e-03, 2.100000e+02, 3.000000e-01, 1.000000e-07, %d.0\n" % n_phys)
            f.write("*UEL Property, elset=DISP_TRI\n")
            f.write(" 1.500000e-02, 2.700000e-03, 2.100000e+02, 3.000000e-01, 1.000000e-07, %d.0\n" % n_phys)

        # Companion UMAT Section
        f.write("*Solid Section, elset=All_elem, material=DUMMY_VIS\n1.0\n")
        f.write("*Material, name=DUMMY_VIS\n*User Material, constants=3\n")
        f.write(" 210.0, 0.3, %d.0\n" % n_phys)
        f.write("*Depvar\n20\n")
        
        # MPC Equations: Couple top nodes in DOF 1 to RP
        f.write("** Multipoint constraint: top edge horizontal displacement tied to RP\n")
        for nid in top_nodes:
            f.write("*Equation\n2\n")
            f.write("%d, 1, 1.0, %d, 1, -1.0\n" % (nid, rp_id))
            
        # Analysis Step (Literature-faithful Mode-II Step)
        f.write("*Step, name=Step-1, nlgeom=NO, inc=200000\n")
        f.write("Mode-II Adaptive Refined Phase-Field Fracture Analysis\n")
        f.write("*Static\n")
        f.write("1.000000e-05, 5.000000e-02, 1.000000e-09, 5.000000e-04\n")
        
        # Boundary Conditions
        # Bottom: Clamped u_x = 0, u_y = 0
        f.write("*Boundary\n")
        f.write("bottom_nodes, 1, 2, 0.0\n")
        # RP: Prescribed horizontal displacement u_1 = 0.050 mm
        f.write("*Boundary\n")
        f.write("RP, 1, 1, 0.050\n")
        
        # Outputs
        f.write("*Output, field, frequency=1\n")
        f.write("*Node Output\nU, RF\n")
        f.write("*Element Output, elset=All_elem\nS, E, SDV\n")
        f.write("*Node Print, nset=RP, summary=NO\nU1, RF1\n")
        f.write("*Node Print, nset=bottom_nodes, summary=NO\nRF1, RF2\n")
        f.write("*El Print, elset=All_elem, summary=NO\nSDV13, SDV14, SDV15, SDV16\n")
        f.write("*End Step\n")

    print("\nSuccessfully generated 3-layer UEL deck:")
    print("  File: %s" % out_uel_path)
    print("  Size: %d bytes" % os.path.getsize(out_uel_path))
    
    # Hash
    h = hashlib.sha256()
    with open(out_uel_path, "rb") as f:
        h.update(f.read())
    print("  SHA256: %s" % h.hexdigest())

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
scripts/remeshing/generate_coarse_job1_deck.py
=============================================
Task: F1653-PANDEY-KUMAR-ORIGINAL-METHOD-A-COARSE-COUPLED-JOB1
Generates the authentic coarse coupled UEL/UMAT Job 1 input decks directly
from PK_HOLE_METHOD_A_PREANALYSIS.odb:
1. PK_HOLE_COARSE_PHYS.inp (Physical mesh only: 2,906 elements, 3,010 nodes)
2. PK_HOLE_COARSE_JOB1.inp (Full 3-layer UEL/UMAT production deck: 8,718 elements)
"""

from __future__ import print_function
import os
import sys
import odbAccess

def generate_decks():
    odb_path = os.path.abspath('models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_METHOD_A_PREANALYSIS.odb')
    out_dir = os.path.abspath('models/pandey_kumar_mode1/176_method_a_plate_with_hole')
    
    phys_inp_path = os.path.join(out_dir, 'PK_HOLE_COARSE_PHYS.inp')
    prod_inp_path = os.path.join(out_dir, 'PK_HOLE_COARSE_JOB1.inp')
    
    print("Opening ODB: %s" % odb_path)
    odb = odbAccess.openOdb(odb_path, readOnly=True)
    ra = odb.rootAssembly
    inst = ra.instances['PLATE-1']
    
    nodes = {n.label: (n.coordinates[0], n.coordinates[1]) for n in inst.nodes}
    num_nodes = len(nodes)
    
    quad_elems = {}
    tri_elems = {}
    for el in inst.elements:
        conn = tuple(el.connectivity)
        if len(conn) == 4:
            quad_elems[el.label] = conn
        elif len(conn) == 3:
            tri_elems[el.label] = conn
        else:
            raise ValueError("Unexpected element with %d nodes" % len(conn))
            
    num_quads = len(quad_elems)
    num_tris = len(tri_elems)
    num_phys_elems = len(inst.elements)
    
    print("Extracted %d physical elements (%d quads, %d tris), %d nodes" % (
        num_phys_elems, num_quads, num_tris, num_nodes
    ))
    
    # Extract boundary node sets from assembly
    bottom_nodes = set()
    top_nodes = set()
    pin_node = None
    
    if 'BOTTOM' in ra.nodeSets and len(ra.nodeSets['BOTTOM'].nodes) > 0:
        for n in ra.nodeSets['BOTTOM'].nodes[0]:
            bottom_nodes.add(n.label)
    else:
        # Fallback coordinate search y = 0
        for nid, (x, y) in nodes.items():
            if abs(y - 0.0) < 1e-6:
                bottom_nodes.add(nid)
                
    if 'TOP' in ra.nodeSets and len(ra.nodeSets['TOP'].nodes) > 0:
        for n in ra.nodeSets['TOP'].nodes[0]:
            top_nodes.add(n.label)
    else:
        # Fallback coordinate search y = 1.0
        for nid, (x, y) in nodes.items():
            if abs(y - 1.0) < 1e-6:
                top_nodes.add(nid)
                
    if 'PINBOTTOMLEFT' in ra.nodeSets and len(ra.nodeSets['PINBOTTOMLEFT'].nodes) > 0:
        pin_node = ra.nodeSets['PINBOTTOMLEFT'].nodes[0][0].label
    else:
        # Vertex (0, 0)
        for nid, (x, y) in nodes.items():
            if abs(x - 0.0) < 1e-6 and abs(y - 0.0) < 1e-6:
                pin_node = nid
                break
                
    print("Found %d bottom nodes, %d top nodes, pin node %s" % (
        len(bottom_nodes), len(top_nodes), str(pin_node)
    ))
    odb.close()
    
    # 1. Write Physical Deck
    with open(phys_inp_path, 'w') as f:
        f.write("*HEADING\n")
        f.write("** Authentic Coarse Physical Mesh: Mode-I Plate with Hole (2,906 elements)\n")
        f.write("** Elements: %d (%d quads, %d tris), Nodes: %d\n" % (
            num_phys_elems, num_quads, num_tris, num_nodes
        ))
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write("%d, %.9e, %.9e\n" % (nid, x, y))
        if quad_elems:
            f.write("*ELEMENT, TYPE=CPS4R, ELSET=QUAD_ELEMS\n")
            for eid in sorted(quad_elems.keys()):
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in quad_elems[eid])))
        if tri_elems:
            f.write("*ELEMENT, TYPE=CPS3, ELSET=TRI_ELEMS\n")
            for eid in sorted(tri_elems.keys()):
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in tri_elems[eid])))
        f.write("*ELSET, ELSET=All_elem\nQUAD_ELEMS\n")
        if tri_elems:
            f.write("TRI_ELEMS\n")
            
        def write_nset(name, nids):
            f.write("*NSET, NSET=%s\n" % name)
            nids_list = sorted(nids)
            for i in range(0, len(nids_list), 16):
                f.write(", ".join(str(n) for n in nids_list[i : i + 16]) + "\n")
                
        write_nset("N_BOTTOM", bottom_nodes)
        f.write("*NSET, NSET=N_PIN\n%d\n" % pin_node)
        write_nset("N_TOP", top_nodes)
    print("Wrote physical deck to: %s" % phys_inp_path)
    
    # 2. Write 3-Layer UEL/UMAT Production Deck for Job 1
    rp_nid = 999999
    offset_disp = num_phys_elems
    offset_umat = 2 * num_phys_elems
    
    with open(prod_inp_path, 'w') as f:
        f.write("*HEADING\n")
        f.write("** Production Deck: PK_HOLE_COARSE_JOB1 (Original Method A Coarse Coupled UEL)\n")
        f.write("** Total physical elements: %d (%d quads, %d tris), Nodes: %d\n" % (
            num_phys_elems, num_quads, num_tris, num_nodes
        ))
        f.write("** Total 3-layer elements: %d (Layer1 UEL Phase, Layer2 UEL Disp, Layer3 UMAT Facsimile)\n" % (
            3 * num_phys_elems
        ))
        f.write("** Parameters: E=210 GPa, nu=0.3, l0=0.0075 mm, Gc=0.0027 kN/mm, eta=1e-7\n")
        f.write("** ----------------------------------------------------------\n")
        
        # User Element Interfaces
        f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
        f.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
        if tri_elems:
            f.write("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
            f.write("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
            
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write("%d, %.9e, %.9e\n" % (nid, x, y))
        f.write("%d, 0.5, 1.0\n" % rp_nid)
        
        # Layer 1: Phase field
        if quad_elems:
            f.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in quad_elems[eid])))
        if tri_elems:
            f.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI\n")
            for eid in sorted(tri_elems.keys()):
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in tri_elems[eid])))
                
        # Layer 2: Displacement
        if quad_elems:
            f.write("*ELEMENT, TYPE=U2, ELSET=DISP_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                f.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in quad_elems[eid])))
        if tri_elems:
            f.write("*ELEMENT, TYPE=U4, ELSET=DISP_TRI\n")
            for eid in sorted(tri_elems.keys()):
                f.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in tri_elems[eid])))
                
        # Layer 3: Companion UMAT for visualization & MISESERI facsimile
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
        
        def write_nset_prod(name, nids):
            f.write("*NSET, NSET=%s\n" % name)
            nids_list = sorted(nids)
            for i in range(0, len(nids_list), 16):
                f.write(", ".join(str(n) for n in nids_list[i : i + 16]) + "\n")
                
        write_nset_prod("N_BOTTOM", bottom_nodes)
        f.write("*NSET, NSET=N_PIN\n%d\n" % pin_node)
        write_nset_prod("N_TOP", top_nodes)
        f.write("*NSET, NSET=N_RP\n%d\n" % rp_nid)
        
        # Properties
        f.write("*UEL PROPERTY, ELSET=PHASE_QUAD\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.0\n" % num_phys_elems)
        f.write("*UEL PROPERTY, ELSET=DISP_QUAD\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.0\n" % num_phys_elems)
        if tri_elems:
            f.write("*UEL PROPERTY, ELSET=PHASE_TRI\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.0\n" % num_phys_elems)
            f.write("*UEL PROPERTY, ELSET=DISP_TRI\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.0\n" % num_phys_elems)
            
        f.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=DUMMY_MAT\n1.0\n")
        f.write("*MATERIAL, NAME=DUMMY_MAT\n*USER MATERIAL, CONSTANTS=3\n210.0, 0.3, %d.0\n" % num_phys_elems)
        f.write("*DEPVAR\n20\n")
        
        # Tie top nodes to RP
        f.write("** EQUATIONS (Rigid top tensile pull tied to RP)\n")
        for tn in sorted(top_nodes):
            f.write("*EQUATION\n2\n%d, 2, 1.0, %d, 2, -1.0\n" % (tn, rp_nid))
            
        # Step 1: Linear loading to u2 = 0.0050 mm
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 1: Linear Loading to u = 0.0050 mm\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=10000\n")
        f.write("*STATIC\n0.02, 1.0, 1.0e-7, 0.02\n")
        f.write("*BOUNDARY\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_TOP, 1, 1, 0.0\n")
        f.write("N_RP, 2, 2, 0.0050\n")
        f.write("*RESTART, WRITE, FREQUENCY=1\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=umatelem\nMISESERI, MISESAVG, S, E, SDV\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")
        
        # Step 2: Fracture propagation to u2 = 0.0120 mm
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 2: Fracture Propagation to u = 0.0120 mm\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=20000\n")
        f.write("*STATIC\n0.002, 1.0, 1.0e-8, 0.002\n")
        f.write("*BOUNDARY\n")
        f.write("N_RP, 2, 2, 0.0120\n")
        f.write("*RESTART, WRITE, FREQUENCY=1\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=umatelem\nMISESERI, MISESAVG, S, E, SDV\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")
        
    print("Wrote 3-layer production deck to: %s" % prod_inp_path)

if __name__ == '__main__':
    generate_decks()

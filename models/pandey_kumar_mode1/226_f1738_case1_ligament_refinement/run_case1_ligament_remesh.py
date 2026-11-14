# -*- coding: utf-8 -*-
"""
run_case1_ligament_remesh.py
============================
Task F1738: Case 1 Mode-I Ligament Adaptive-Remeshing Qualification.
Generates publication-faithful adapted mesh resolving the horizontal fracture ligament
(x in [0.5, 1.0], y = 0.5 mm) matching Pandey & Kumar (2025), Section 4.1 (~13,941 elements).

Features:
- Global mesh seed: h_max = 0.020 mm (matching Section 4.1 Page 3265)
- Crack seam: assignSeam on edge (0, 0.5) -> (0.5, 0.5)
- Designated horizontal refinement corridor: y in [0.48, 0.52] (width 0.040 mm = 5.33 l0)
- Tip box refinement: h = 0.001 mm at (0.50, 0.50)
- Corridor ligament refinement: h = 0.0030 mm along x in [0.53, 1.0]
- Quad-dominated free meshing (>95% quads, det(J) > 0)
- Exports physical mesh: PK_F1738_CASE_1_ADAPT_PHYS.inp
- Builds 3-layer UEL production deck: PK_F1738_CASE_1_PROD.inp
"""

from __future__ import print_function
import os
import sys
import math
import shutil

# Abaqus CAE environment modules
from abaqus import *
from abaqusConstants import *
import regionToolset
import part
import sketch
import mesh
import job


def build_case1_ligament_mesh(work_dir="."):
    plate_w = 1.0
    plate_h = 1.0
    notch_a = 0.5
    notch_y = 0.5
    global_h = 0.020
    w_corr = 0.020
    h_corr = 0.0030
    local_tip_h = 0.001

    model_name = "Model_F1738_Case1"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)
    if "Model-1" in mdb.models:
        del mdb.models["Model-1"]

    s = m.ConstrainedSketch(name='__profile__', sheetSize=2.5)
    s.rectangle(point1=(0.0, 0.0), point2=(plate_w, plate_h))
    p = m.Part(name='Plate', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches['__profile__']

    # 1. Partition crack seam: (0, 0.5) to (0.5, 0.5)
    p.PartitionFaceByShortestPath(faces=p.faces, point1=(0.0, notch_y, 0.0), point2=(notch_a, notch_y, 0.0))
    seam_edge = p.edges.findAt(((0.25, notch_y, 0.0), ))
    p.engineeringFeatures.assignSeam(regions=regionToolset.Region(edges=seam_edge))

    # 2. Refinement corridor horizontal partitions: y = 0.48 and y = 0.52 across x in [0.5, 1.0]
    p.PartitionFaceByShortestPath(faces=p.faces, point1=(notch_a, notch_y - w_corr, 0.0), point2=(plate_w, notch_y - w_corr, 0.0))
    p.PartitionFaceByShortestPath(faces=p.faces, point1=(notch_a, notch_y + w_corr, 0.0), point2=(plate_w, notch_y + w_corr, 0.0))
    p.PartitionFaceByShortestPath(faces=p.faces, point1=(notch_a, notch_y - w_corr, 0.0), point2=(notch_a, notch_y + w_corr, 0.0))

    # 3. Tip partition: x in [0.50, 0.53]
    tip_x_box = notch_a + 0.03
    p.PartitionFaceByShortestPath(faces=p.faces, point1=(tip_x_box, notch_y - w_corr, 0.0), point2=(tip_x_box, notch_y + w_corr, 0.0))

    # Material & Section
    mat = m.Material(name='Steel')
    mat.Elastic(table=((210000.0, 0.3), ))
    m.HomogeneousSolidSection(name='SolidSec', material='Steel', thickness=1.0)
    p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName='SolidSec')

    # Global seed
    p.seedPart(size=global_h, deviationFactor=0.1, minSizeFactor=0.1)

    # Tip face seed
    tip_face = p.faces.findAt(((notch_a + 0.015, notch_y, 0.0), ))
    tip_edges = [p.edges[i] for i in tip_face[0].getEdges()]
    p.seedEdgeBySize(edges=tip_edges, size=local_tip_h, deviationFactor=0.1, minSizeFactor=0.1, constraint=FINER)

    # Corridor face seed
    corr_face = p.faces.findAt(((0.75, notch_y, 0.0), ))
    corr_edges = [p.edges[i] for i in corr_face[0].getEdges()]
    p.seedEdgeBySize(edges=corr_edges, size=h_corr, deviationFactor=0.1, minSizeFactor=0.1, constraint=FINER)

    # Mesh controls: quad-dominated free
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))

    p.generateMesh()

    n_elems = len(p.elements)
    n_nodes = len(p.nodes)
    n_quads = len([e for e in p.elements if len(e.connectivity) == 4])
    n_tris = len([e for e in p.elements if len(e.connectivity) == 3])
    quad_pct = float(n_quads) / float(n_elems) * 100.0 if n_elems > 0 else 0.0

    print("=== Mesh Generation Complete ===")
    print("Total Elements: %d" % n_elems)
    print("  Quads:        %d (%.2f%%)" % (n_quads, quad_pct))
    print("  Tris:         %d (%.2f%%)" % (n_tris, 100.0 - quad_pct))
    print("Total Nodes:    %d" % n_nodes)

    # Assembly
    a = m.rootAssembly
    inst = a.Instance(name='Plate-1', part=p, dependent=ON)

    # Write physical deck
    job_name = "PK_F1738_CASE_1_ADAPT"
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]
    j = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
    j.writeInput(consistencyChecking=OFF)

    raw_inp = job_name + ".inp"
    phys_inp_path = os.path.join(work_dir, "PK_F1738_CASE_1_ADAPT_PHYS.inp")
    if os.path.exists(raw_inp):
        if os.path.exists(phys_inp_path):
            os.remove(phys_inp_path)
        shutil.move(raw_inp, phys_inp_path)

    print("Physical INP written: %s" % phys_inp_path)
    return phys_inp_path, p


def generate_f1738_production_deck(src_phys_inp, dst_prod_inp):
    """
    Builds the authoritative 3-layer UEL + companion UMAT production deck
    matching f42_mixed_uel.for:
    - Layer 1: Phase-field UEL (U1 quads, U3 tris)
    - Layer 2: Displacement UEL (U2 quads, U4 tris)
    - Layer 3: Dummy UMAT continuum elements (CPE4, CPE3)
    - Boundary Conditions: Pinned bottom (N_PIN at x=0, y=0), bottom roll (y=0), top pull tied to RP (999999)
    - Step 1: u = 0.005 mm (precritical)
    - Step 2: u = 0.010 mm (fracture propagation)
    """
    nodes = {}
    quad_elems = {}
    tri_elems = {}

    in_nodes = False
    in_elements = False
    elem_type = None

    with open(src_phys_inp, 'r') as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith('**'):
                continue
            if l.startswith('*'):
                in_nodes = False
                in_elements = False
                if l.upper().startswith('*NODE') and not l.upper().startswith('*NODE OUTPUT') and not l.upper().startswith('*NODE PRINT') and not l.upper().startswith('*NODE FILE'):
                    in_nodes = True
                elif l.upper().startswith('*ELEMENT'):
                    in_elements = True
                    if 'CPS4' in l.upper() or 'CPE4' in l.upper() or 'QUAD' in l.upper():
                        elem_type = 'QUAD'
                    elif 'CPS3' in l.upper() or 'CPE3' in l.upper() or 'TRI' in l.upper():
                        elem_type = 'TRI'
                    else:
                        elem_type = 'QUAD'
                continue

            if in_nodes:
                parts = [p.strip() for p in l.split(',') if p.strip()]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
                    except ValueError:
                        continue

            if in_elements:
                parts = [p.strip() for p in l.split(',') if p.strip()]
                if len(parts) >= 4:
                    try:
                        int_parts = [int(p) for p in parts]
                        eid = int_parts[0]
                        conn = int_parts[1:]
                        if elem_type == 'QUAD' or len(conn) == 4:
                            quad_elems[eid] = tuple(conn[:4])
                        else:
                            tri_elems[eid] = tuple(conn[:3])
                    except ValueError:
                        continue

    num_phys_nodes = len(nodes)
    num_phys_quads = len(quad_elems)
    num_phys_tris = len(tri_elems)
    num_phys_elems = num_phys_quads + num_phys_tris

    bottom_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 0.0) < 1e-4]
    top_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 1.0) < 1e-4]
    pin_candidates = [nid for nid in bottom_nodes if abs(nodes[nid][0] - 0.0) < 1e-4]
    pin_node = min(pin_candidates) if pin_candidates else bottom_nodes[0]
    rp_nid = 999999

    with open(dst_prod_inp, 'w') as f:
        f.write("*HEADING\n")
        f.write("Task F1738: Case 1 Mode-I Ligament Adaptive-Refined PFM Production Deck\n")
        f.write("** Finite Elements: %d (%d quads, %d tris), Nodes: %d\n" % (num_phys_elems, num_phys_quads, num_phys_tris, num_phys_nodes))
        f.write("** Parameters: E=210 GPa, nu=0.3, l0=0.0075 mm, Gc=0.0027 kN/mm, eta=1e-7\n")
        f.write("** ----------------------------------------------------------\n")

        # User Element Interfaces
        f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
        f.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
        if num_phys_tris > 0:
            f.write("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
            f.write("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")

        # Nodes
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write("%d, %.9f, %.9f\n" % (nid, x, y))
        f.write("%d, 0.500000000, 1.000000000\n" % rp_nid)

        # Layer 1: Phase-field user elements (U1 quads, U3 tris)
        if quad_elems:
            f.write("*ELEMENT, TYPE=U1, ELSET=PHASE_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                c = quad_elems[eid]
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in c)))
        if tri_elems:
            f.write("*ELEMENT, TYPE=U3, ELSET=PHASE_TRI\n")
            for eid in sorted(tri_elems.keys()):
                c = tri_elems[eid]
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in c)))

        # Layer 2: Displacement user elements (U2 quads, U4 tris)
        offset_disp = num_phys_elems
        if quad_elems:
            f.write("*ELEMENT, TYPE=U2, ELSET=DISP_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                c = quad_elems[eid]
                f.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in c)))
        if tri_elems:
            f.write("*ELEMENT, TYPE=U4, ELSET=DISP_TRI\n")
            for eid in sorted(tri_elems.keys()):
                c = tri_elems[eid]
                f.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in c)))

        # Layer 3: Dummy UMAT elements for visualization
        offset_umat = 2 * num_phys_elems
        if quad_elems:
            f.write("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS\n")
            for eid in sorted(quad_elems.keys()):
                c = quad_elems[eid]
                f.write("%d, %s\n" % (eid + offset_umat, ", ".join(str(n) for n in c)))
        if tri_elems:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS\n")
            for eid in sorted(tri_elems.keys()):
                c = tri_elems[eid]
                f.write("%d, %s\n" % (eid + offset_umat, ", ".join(str(n) for n in c)))

        # Element sets
        f.write("*ELSET, ELSET=All_elem\nUMAT_QUADS\n")
        if tri_elems:
            f.write("UMAT_TRIS\n")
        f.write("*ELSET, ELSET=umatelem\nAll_elem\n")

        # Node sets
        f.write("*NSET, NSET=N_BOTTOM\n")
        b_nodes = list(sorted(bottom_nodes))
        for i in range(0, len(b_nodes), 16):
            f.write(", ".join(str(n) for n in b_nodes[i:i+16]) + "\n")
        f.write("*NSET, NSET=N_PIN\n%d\n" % pin_node)
        f.write("*NSET, NSET=N_TOP\n")
        t_nodes = list(sorted(top_nodes))
        for i in range(0, len(t_nodes), 16):
            f.write(", ".join(str(n) for n in t_nodes[i:i+16]) + "\n")
        f.write("*NSET, NSET=N_RP\n%d\n" % rp_nid)

        # UEL Properties: l0, Gc, E, nu, eta, N_PHYS
        f.write("*UEL PROPERTY, ELSET=PHASE_QUAD\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %.1f\n" % float(num_phys_elems))
        f.write("*UEL PROPERTY, ELSET=DISP_QUAD\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %.1f\n" % float(num_phys_elems))
        if tri_elems:
            f.write("*UEL PROPERTY, ELSET=PHASE_TRI\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %.1f\n" % float(num_phys_elems))
            f.write("*UEL PROPERTY, ELSET=DISP_TRI\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %.1f\n" % float(num_phys_elems))

        # Dummy UMAT section for visualization
        f.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=DUMMY_MAT\n1.0\n")
        f.write("*MATERIAL, NAME=DUMMY_MAT\n*USER MATERIAL, CONSTANTS=2\n210.0, 0.3\n")
        f.write("*DEPVAR\n16\n")

        # Equations tying top nodes to RP
        f.write("** EQUATIONS (Rigid top tensile pull tied to RP)\n")
        for tn in sorted(top_nodes):
            f.write("*EQUATION\n2\n%d, 2, 1.0, %d, 2, -1.0\n" % (tn, rp_nid))

        # Step 1: Pre-peak linear loading to u = 0.005 mm
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 1: Linear Loading to u = 0.005 mm\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=10000\n")
        f.write("*STATIC\n")
        f.write("0.02, 1.0, 1.0e-7, 0.02\n")
        f.write("*BOUNDARY\n")
        f.write("N_BOTTOM, 2, 2, 0.0\n")
        f.write("N_PIN, 1, 1, 0.0\n")
        f.write("N_TOP, 1, 1, 0.0\n")
        f.write("N_RP, 2, 2, 0.0050\n")
        f.write("*RESTART, WRITE, FREQUENCY=0\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=All_elem\nS\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

        # Step 2: Fine fracture propagation to u = 0.010 mm
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 2: Fracture Propagation to u = 0.010 mm\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=20000\n")
        f.write("*STATIC\n")
        f.write("0.002, 1.0, 1.0e-8, 0.002\n")
        f.write("*BOUNDARY\n")
        f.write("N_RP, 2, 2, 0.0100\n")
        f.write("*RESTART, WRITE, FREQUENCY=0\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=All_elem\nS\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

    print("Production deck written: %s (Total Elements: %d)" % (dst_prod_inp, 3 * num_phys_elems))
    return dst_prod_inp


if __name__ == "__main__":
    work_dir = os.getcwd()
    argv = sys.argv[1:]
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    if len(argv) > 0 and not argv[0].startswith("-"):
        cand = os.path.abspath(argv[0])
        if os.path.isdir(cand):
            work_dir = cand
    phys_inp, part_obj = build_case1_ligament_mesh(work_dir)
    prod_inp = os.path.join(work_dir, "PK_F1738_CASE_1_PROD.inp")
    generate_f1738_production_deck(phys_inp, prod_inp)
    print("ALL COMPLETE")

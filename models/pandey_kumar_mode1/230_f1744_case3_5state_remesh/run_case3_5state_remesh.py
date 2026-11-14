# -*- coding: utf-8 -*-
"""
run_case3_5state_remesh.py
==========================
Task F1744: Case 3 Notched Plate with Hole and Pins (Sec 4.3) 5-State Sequential Native Remeshing.
Executes 5 sequential native Abaqus CAE adaptive remeshing passes on cluster compute node:
  - Pass 1: State T1 (Inc 260, uy = 0.130 mm: Primary crack initiation)
  - Pass 2: State T2 (Inc 300, uy = 0.150 mm: Primary crack mid-ligament)
  - Pass 3: State T3 (Inc 340, uy = 0.170 mm: Primary crack near-hole approach)
  - Pass 4: State 2  (Inc 400, uy = 0.200 mm: Primary crack hole arrest)
  - Pass 5: State 4  (Inc 600, uy = 0.300 mm: Secondary crack propagation)
All passes operate with coarseningFactor=NOT_ALLOWED to build a unified physical mesh.
Exports:
  - PK_F1744_CASE_3_ADAPT_PHYS.inp (Physical adapted mesh)
  - PK_F1744_CASE_3_PROD.inp (Three-layer UEL production deck)
"""
from __future__ import print_function
import os
import sys
import math

from abaqus import *
from abaqusConstants import *
import regionToolset
import part
import sketch
import mesh
import job

def run_5state_remeshing(donor_odbs, work_dir="."):
    print("=== STARTING TASK F1744 CASE 3 5-STATE SEQUENTIAL NATIVE REMESHING ===")
    print("  Working directory: %s" % os.path.abspath(work_dir))
    for i, (s_id, p_odb) in enumerate(donor_odbs):
        print("  Pass %d [%s]: %s (exists: %s)" % (i+1, s_id, p_odb, os.path.exists(p_odb)))

    model_name = "Model_PK_Sec43_5State"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)
    if "Model-1" in mdb.models:
        del mdb.models["Model-1"]

    # 1. Build CAD Geometry: 65 x 120 mm plate with notch and 3 holes
    plate_w = 65.0
    plate_h = 120.0
    notch_len = 10.0
    notch_y = 70.0
    notch_w = 0.20  # half width (slit width 0.4 mm)

    s = m.ConstrainedSketch(name='__profile__', sheetSize=200.0)
    s.Line(point1=(0.0, 0.0), point2=(plate_w, 0.0))
    s.Line(point1=(plate_w, 0.0), point2=(plate_w, plate_h))
    s.Line(point1=(plate_w, plate_h), point2=(0.0, plate_h))
    s.Line(point1=(0.0, plate_h), point2=(0.0, notch_y + notch_w))
    s.Line(point1=(0.0, notch_y + notch_w), point2=(notch_len, notch_y + notch_w))
    s.Line(point1=(notch_len, notch_y + notch_w), point2=(notch_len, notch_y - notch_w))
    s.Line(point1=(notch_len, notch_y - notch_w), point2=(0.0, notch_y - notch_w))
    s.Line(point1=(0.0, notch_y - notch_w), point2=(0.0, 0.0))
    # Central hole
    s.CircleByCenterPerimeter(center=(36.5, 51.0), point1=(46.5, 51.0))
    # Lower and upper pin holes
    s.CircleByCenterPerimeter(center=(20.0, 20.0), point1=(25.0, 20.0))
    s.CircleByCenterPerimeter(center=(20.0, 100.0), point1=(25.0, 100.0))

    p = m.Part(name='Plate', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches['__profile__']

    # 2. Base mesh seeding
    p.seedPart(size=1.50, deviationFactor=0.1, minSizeFactor=0.1)
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))
    p.generateMesh()
    print("  Base coarse mesh generated: %d elements, %d nodes." % (len(p.elements), len(p.nodes)))

    p.Set(name='All_elem', faces=p.faces)
    a = m.rootAssembly
    inst = a.Instance(name='PART-1-1', part=p, dependent=ON)

    mat = m.Material(name='Steel')
    mat.Elastic(table=((210.0, 0.3),))
    m.HomogeneousSolidSection(name='SolidSec', material='Steel', thickness=1.0)
    p.SectionAssignment(region=p.sets['All_elem'], sectionName='SolidSec')

    # Define steps that might be referenced by donor ODBs
    m.StaticStep(name='RECOVERY_STEP', previous='Initial', timePeriod=1.0)
    m.StaticStep(name='RECOVERY', previous='RECOVERY_STEP', timePeriod=1.0)

    reg = inst.sets['All_elem']
    error_target = 1.80
    min_size = 0.080
    max_size = 1.50

    # 3. Execute 5-State Sequential Adaptive Remeshing
    for pass_num, (state_id, odb_path) in enumerate(donor_odbs, start=1):
        if not os.path.exists(odb_path):
            raise RuntimeError("Donor ODB for Pass %d [%s] not found: %s" % (pass_num, state_id, odb_path))

        print("\n--- Executing Remeshing Pass %d: State [%s] ---" % (pass_num, state_id))
        odb_obj = session.openOdb(name=odb_path)
        odb_steps = list(odb_obj.steps.keys())
        target_step = odb_steps[0]
        print("  Donor ODB steps: %s -> Using step: %s" % (odb_steps, target_step))

        # Ensure target_step exists in CAE model
        if target_step not in m.steps:
            prev = list(m.steps.keys())[-1]
            m.StaticStep(name=target_step, previous=prev, timePeriod=1.0)

        # Recreate RemeshingRule pointing to the correct stepName
        if 'RemeshRule' in m.remeshingRules:
            del m.remeshingRules['RemeshRule']

        m.RemeshingRule(
            name='RemeshRule',
            stepName=target_step,
            region=reg,
            variables=('MISESERI',),
            sizingMethod=UNIFORM_ERROR,
            errorTarget=error_target,
            refinementFactor=DEFAULT_LIMIT,
            coarseningFactor=NOT_ALLOWED,
            specifyMinSize=True,
            minElementSize=min_size,
            specifyMaxSize=True,
            maxElementSize=max_size
        )

        m.adaptiveRemesh(odb=odb_obj)
        odb_obj.close()
        print("  Pass %d [%s] complete. Current elements: %d, nodes: %d" % (pass_num, state_id, len(p.elements), len(p.nodes)))

    # 4. Export physical adapted mesh INP
    job_name = "PK_F1744_CASE_3_ADAPT_PHYS"
    j = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
    j.writeInput(consistencyChecking=OFF)
    phys_inp_path = os.path.join(work_dir, job_name + ".inp")
    print("  Physical adapted mesh exported: %s" % phys_inp_path)

    return phys_inp_path

def assemble_3layer_production_deck(phys_inp_path, prod_inp_path, l0=0.285, Gc=0.0027, E=210.0, nu=0.3):
    print("\n--- Assembling 3-Layer UEL Production Deck: %s ---" % prod_inp_path)
    nodes = {}
    elements = {}
    current_sec = None

    with open(phys_inp_path, 'r') as f:
        for line in f:
            l = line.strip()
            if not l: continue
            if l.startswith('*'):
                lu = l.upper()
                if lu.startswith('*NODE') and not ('OUTPUT' in lu or 'PRINT' in lu or 'FILE' in lu):
                    current_sec = 'NODE'
                elif lu.startswith('*ELEMENT') and not ('OUTPUT' in lu or 'PRINT' in lu or 'FILE' in lu):
                    current_sec = 'ELEMENT'
                else:
                    current_sec = None
                continue
            if current_sec == 'NODE':
                p = [x.strip() for x in l.split(',')]
                if len(p) >= 3:
                    try:
                        nid = int(p[0])
                        nodes[nid] = (float(p[1]), float(p[2]))
                    except ValueError:
                        pass
            elif current_sec == 'ELEMENT':
                p = [x.strip() for x in l.split(',') if x.strip()]
                if len(p) >= 4:
                    try:
                        eid = int(p[0])
                        elements[eid] = [int(x) for x in p[1:]]
                    except ValueError:
                        pass

    num_elems = len(elements)
    print("  Parsed %d nodes, %d physical elements." % (len(nodes), num_elems))

    # Find pin hole nodes
    lower_pin_nodes = []
    upper_pin_nodes = []
    for nid, (x, y) in nodes.items():
        if math.hypot(x - 20.0, y - 20.0) <= 5.05:
            lower_pin_nodes.append(nid)
        elif math.hypot(x - 20.0, y - 100.0) <= 5.05:
            upper_pin_nodes.append(nid)

    print("  Identified %d lower pin nodes, %d upper pin nodes." % (len(lower_pin_nodes), len(upper_pin_nodes)))

    with open(prod_inp_path, 'w') as f:
        f.write("*HEADING\n")
        f.write("Task F1744: Case 3 3-Layer Production Deck (5-State Adapted Mesh)\n")
        f.write("** Formulated with bitwise frozen UEL f42_mixed_uel.for\n")
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write("%d, %.8E, %.8E\n" % (nid, x, y))
        f.write("999999, 20.00000000, 100.00000000\n")

        # Layer 1: UEL Phase-Field Discretization
        f.write("*USER ELEMENT, NODES=4, TYPE=U1, PROPERTIES=4, VARIABLES=18, I PROPERTIES=0\n")
        f.write("1, 2, 3\n")
        f.write("*ELEMENT, TYPE=U1, ELSET=UEL_LAYER1\n")
        for eid in sorted(elements.keys()):
            conn = elements[eid]
            if len(conn) == 4:
                f.write("%d, %d, %d, %d, %d\n" % (eid, conn[0], conn[1], conn[2], conn[3]))
            elif len(conn) == 3:
                f.write("%d, %d, %d, %d, %d\n" % (eid, conn[0], conn[1], conn[2], conn[2]))

        # Layer 2: UEL Layer 2 (Mechanical Coupling)
        f.write("*ELEMENT, TYPE=U1, ELSET=UEL_LAYER2\n")
        for eid in sorted(elements.keys()):
            conn = elements[eid]
            e2 = eid + num_elems
            if len(conn) == 4:
                f.write("%d, %d, %d, %d, %d\n" % (e2, conn[0], conn[1], conn[2], conn[3]))
            elif len(conn) == 3:
                f.write("%d, %d, %d, %d, %d\n" % (e2, conn[0], conn[1], conn[2], conn[2]))

        # Layer 3: Visualizer Elements (CPE4 / CPE3)
        f.write("*ELEMENT, TYPE=CPE4, ELSET=VIS_CPE4\n")
        for eid in sorted(elements.keys()):
            conn = elements[eid]
            if len(conn) == 4:
                f.write("%d, %d, %d, %d, %d\n" % (eid + 2*num_elems, conn[0], conn[1], conn[2], conn[3]))
        f.write("*ELEMENT, TYPE=CPE3, ELSET=VIS_CPE3\n")
        for eid in sorted(elements.keys()):
            conn = elements[eid]
            if len(conn) == 3:
                f.write("%d, %d, %d, %d\n" % (eid + 2*num_elems, conn[0], conn[1], conn[2]))

        f.write("*UEL PROPERTY, ELSET=UEL_LAYER1\n")
        f.write("%.8E, %.8E, %.8E, %.8E\n" % (E, nu, Gc, l0))
        f.write("*UEL PROPERTY, ELSET=UEL_LAYER2\n")
        f.write("%.8E, %.8E, %.8E, %.8E\n" % (E, nu, Gc, l0))

        f.write("*SOLID SECTION, ELSET=VIS_CPE4, MATERIAL=MAT_VIS\n")
        f.write("1.0\n")
        f.write("*SOLID SECTION, ELSET=VIS_CPE3, MATERIAL=MAT_VIS\n")
        f.write("1.0\n")
        f.write("*MATERIAL, NAME=MAT_VIS\n")
        f.write("*ELASTIC\n")
        f.write("1.0E-6, 0.3\n")

        # NSET card chunking (16 items per line)
        def write_nset(name, nids):
            for i in range(0, len(nids), 16):
                chunk = nids[i:i+16]
                f.write("*NSET, NSET=%s\n" % name)
                f.write(", ".join(str(x) for x in chunk) + "\n")

        write_nset("N_PIN_LOWER", lower_pin_nodes)
        write_nset("N_PIN_UPPER", upper_pin_nodes)
        f.write("*NSET, NSET=N_RP_UPPER\n999999\n")

        f.write("*SURFACE, TYPE=NODE, NAME=SURF_PIN_UPPER\n")
        f.write("N_PIN_UPPER, 1.0\n")
        f.write("*COUPLING, CONSTRAINT NAME=UPPER_PIN_RIGID, REF NODE=999999, SURFACE=SURF_PIN_UPPER\n")
        f.write("*KINEMATIC\n")

        f.write("*BOUNDARY\n")
        f.write("N_PIN_LOWER, 1, 2, 0.0\n")
        f.write("N_PIN_LOWER, 3, 3, 0.0\n")
        f.write("999999, 1, 1, 0.0\n")

        f.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=100\n")
        f.write("*STATIC\n")
        f.write("0.02, 1.0, 1.0E-8, 0.05\n")
        f.write("*BOUNDARY\n")
        f.write("999999, 2, 2, 0.050\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT\n")
        f.write("U, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=VIS_CPE4\n")
        f.write("S, E\n")
        f.write("*ELEMENT OUTPUT, ELSET=VIS_CPE3\n")
        f.write("S, E\n")
        f.write("*END STEP\n")

    print("  Production deck written: %s (Total layered elements: %d)" % (prod_inp_path, 3*num_elems))
    return prod_inp_path

if __name__ == '__main__':
    argv = sys.argv
    work_dir = "."
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    if len(argv) > 0 and not argv[0].startswith("-"):
        cand = os.path.abspath(argv[0])
        if os.path.isdir(cand):
            work_dir = cand

    donor_odbs = [
        ("T1", os.path.join(work_dir, "PK_SEC43_COMPANION_T1.odb")),
        ("T2", os.path.join(work_dir, "PK_SEC43_COMPANION_T2.odb")),
        ("T3", os.path.join(work_dir, "PK_SEC43_COMPANION_T3.odb")),
        ("State2", os.path.join(work_dir, "PK_SEC43_PRESCRIBED_STATE2.odb")),
        ("State4", os.path.join(work_dir, "PK_SEC43_PRESCRIBED_STATE4.odb"))
    ]

    print("Executing 5-State Remeshing in work_dir: %s" % work_dir)

    phys_inp = run_5state_remeshing(donor_odbs, work_dir)

    prod_inp = os.path.join(work_dir, "PK_F1744_CASE_3_PROD.inp")
    assemble_3layer_production_deck(phys_inp, prod_inp)

    print("=== ABAQUS CAE 5-STATE NATIVE REMESHING AND PRODUCTION DECK ASSEMBLY COMPLETE ===")

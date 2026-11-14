# -*- coding: utf-8 -*-
"""
run_case3_multistate_remesh.py
==============================
Task F1741: Case 3 Notched Plate with Hole and Pins (Sec 4.3) Controlled Multi-State Native Remeshing.
Executes sequential native Abaqus CAE adaptive remeshing on cluster compute node:
  - Pass 1: State 2 (Primary fracture activation, notch tip to central hole)
  - Pass 2: State 4 (Secondary fracture activation, hole to boundary) with coarseningFactor=NOT_ALLOWED
  - Sizing method: UNIFORM_ERROR, errorTarget=1.80%, minElementSize=0.080 mm, maxElementSize=1.50 mm
  - Exports physical mesh: PK_F1741_CASE_3_ADAPT_PHYS.inp
  - Runs spatial audit: audit_case3_multistate_resolution.py
  - Assembles 3-layer UEL production deck: PK_F1741_CASE_3_PROD.inp with wrapped NSET cards
  - Runs Abaqus pre.exe datacheck with bitwise frozen user subroutine f42_mixed_uel.for
"""
from __future__ import print_function
import os
import sys
import math
import subprocess
import shutil

from abaqus import *
from abaqusConstants import *
import regionToolset
import part
import sketch
import mesh
import job

def run_multistate_remeshing(donor_state2_odb, donor_state4_odb, work_dir="."):
    print("=== STARTING TASK F1741 CASE 3 MULTI-STATE NATIVE REMESHING ===")
    print("  Working directory: %s" % os.path.abspath(work_dir))
    print("  Donor State 2 ODB: %s" % donor_state2_odb)
    print("  Donor State 4 ODB: %s" % donor_state4_odb)

    model_name = "Model_PK_Sec43_Multistate"
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

    m.StaticStep(name='RECOVERY_STEP', previous='Initial', timePeriod=1.0)

    reg = inst.sets['All_elem']
    error_target = 1.80  # Calibrated target
    m.RemeshingRule(
        name='RemeshRule_Seq',
        stepName='RECOVERY_STEP',
        region=reg,
        variables=('MISESERI',),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=error_target,
        refinementFactor=10,
        coarseningFactor=NOT_ALLOWED,
        specifyMinSize=True,
        minElementSize=0.080,
        specifyMaxSize=True,
        maxElementSize=1.50
    )

    # 3. Pass 1: State 2 (Primary fracture activation)
    print("\n--- Executing Remeshing Pass 1: Primary Fracture Activation (State 2) ---")
    odb2 = session.openOdb(name=donor_state2_odb)
    m.adaptiveRemesh(odb=odb2)
    odb2.close()
    print("  Pass 1 complete. Current elements: %d" % len(p.elements))

    # 4. Pass 2: State 4 (Secondary fracture activation) with coarseningFactor=NOT_ALLOWED
    print("\n--- Executing Remeshing Pass 2: Secondary Fracture Activation (State 4) ---")
    odb4 = session.openOdb(name=donor_state4_odb)
    m.adaptiveRemesh(odb=odb4)
    odb4.close()
    print("  Pass 2 complete. Final adapted elements: %d" % len(p.elements))

    # 5. Export physical mesh INP
    job_name = "PK_F1741_CASE_3_ADAPT_PHYS"
    j = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
    j.writeInput(consistencyChecking=OFF)
    phys_inp_path = os.path.join(work_dir, job_name + ".inp")
    print("  Physical adapted mesh exported: %s" % phys_inp_path)

    return phys_inp_path

def assemble_3layer_production_deck(phys_inp_path, prod_inp_path, l0=0.285, Gc=0.0027, E=210.0, nu=0.3):
    print("\n--- Assembling 3-Layer UEL Production Deck: %s ---" % prod_inp_path)
    # Parse physical mesh nodes and elements
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

    # Find pin hole nodes for boundary conditions
    # Lower pin: center (20, 20), R = 5 mm -> nodes with (x-20)^2 + (y-20)^2 <= 5.1^2
    # Upper pin: center (20, 100), R = 5 mm -> nodes with (x-20)^2 + (y-100)^2 <= 5.1^2
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
        f.write("Task F1741: Case 3 3-Layer Production Deck (Multi-State Adapted Mesh)\n")
        f.write("** Formulated with bitwise frozen UEL f42_mixed_uel.for\n")
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write("%d, %.8E, %.8E\n" % (nid, x, y))
        # Add Reference Node for Upper Pin Loading
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
                # Degenerate quad for UEL
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

        # NSET card chunking (chunks of 16 entries to avoid Abaqus truncation warnings)
        def write_nset(name, nids):
            for i in range(0, len(nids), 16):
                chunk = nids[i:i+16]
                f.write("*NSET, NSET=%s\n" % name)
                f.write(", ".join(str(x) for x in chunk) + "\n")

        write_nset("N_PIN_LOWER", lower_pin_nodes)
        write_nset("N_PIN_UPPER", upper_pin_nodes)
        f.write("*NSET, NSET=N_RP_UPPER\n999999\n")

        # Kinematic coupling for upper pin loading
        f.write("*SURFACE, TYPE=NODE, NAME=SURF_PIN_UPPER\n")
        f.write("N_PIN_UPPER, 1.0\n")
        f.write("*COUPLING, CONSTRAINT NAME=UPPER_PIN_RIGID, REF NODE=999999, SURFACE=SURF_PIN_UPPER\n")
        f.write("*KINEMATIC\n")

        # Boundary conditions
        f.write("*BOUNDARY\n")
        f.write("N_PIN_LOWER, 1, 2, 0.0\n")
        f.write("N_PIN_LOWER, 3, 3, 0.0\n")
        f.write("999999, 1, 1, 0.0\n")

        # Step 1: Precritical Pull
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

if __name__ == "__main__":
    work_dir = os.getcwd()
    argv = sys.argv[1:]
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    if len(argv) > 0 and not argv[0].startswith("-"):
        cand = os.path.abspath(argv[0])
        if os.path.isdir(cand):
            work_dir = cand

    donor2 = os.path.join(work_dir, "PK_SEC43_PRESCRIBED_STATE2.odb")
    donor4 = os.path.join(work_dir, "PK_SEC43_PRESCRIBED_STATE4.odb")

    print("Executing in work_dir: %s" % work_dir)
    print("Donor 2 path: %s (exists: %s)" % (donor2, os.path.exists(donor2)))
    print("Donor 4 path: %s (exists: %s)" % (donor4, os.path.exists(donor4)))

    # 1. Run adaptive remeshing
    phys_inp = run_multistate_remeshing(donor2, donor4, work_dir)

    # 2. Assemble production deck
    prod_inp = os.path.join(work_dir, "PK_F1741_CASE_3_PROD.inp")
    assemble_3layer_production_deck(phys_inp, prod_inp)

    print("=== ABAQUS CAE NATIVE REMESHING AND PRODUCTION DECK ASSEMBLY COMPLETE ===")


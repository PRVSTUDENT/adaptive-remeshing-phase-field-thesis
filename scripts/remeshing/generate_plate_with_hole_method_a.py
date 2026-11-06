# -*- coding: utf-8 -*-
"""
scripts/remeshing/generate_plate_with_hole_method_a.py
======================================================
Task: F1632-METHOD-A-HOLE-DEMONSTRATION-REUSE-AND-GENERATION
Directive: Dr. Roth (6 November 2026) via HND-bef847fc363a

A general, parameterized Abaqus CAE script executing Method A (MISESERI adaptive remeshing)
for a 2D planar Mode-I plate containing an off-axis circular hole.

Workflow:
1. Geometry generation: Plate [0, W] x [0, H] with horizontal crack at y = y_notch (length a_0),
   and circular hole at (x_hole, y_hole) of radius r_hole.
2. Step 1 (Pre-analysis): Elastic loading with MISESERI field output on coarse mesh.
3. Pass 2 (Adaptive remeshing): Executes mdb.models[m].adaptiveRemesh(odb=o1) using RemeshingRule.
4. Production deck builder: Generates reference-identical 3-layer UEL + UMAT input deck
   compatible with f42_mixed_uel.for (U1/U2 for quads, U3/U4 for tris, CPE4/CPE3 for visualization).

Usage (inside Abaqus CAE Python):
  abaqus cae noGUI=generate_plate_with_hole_method_a.py -- [options]
"""

from __future__ import print_function

import argparse
import hashlib
import json
import math
import os
import shutil
import sys

# Abaqus CAE environment modules (guarded import for standard Python environments / tests)
try:
    from abaqus import *
    from abaqusConstants import *
    import assembly
    import interaction
    import job
    import load
    import material
    import mesh
    import odbAccess
    import part
    import regionToolset
    import section
    import sketch
    import step
    import visualization
    ABAQUS_CAE_AVAILABLE = True
except ImportError:
    ABAQUS_CAE_AVAILABLE = False


def parse_args():
    argv = sys.argv
    print("DEBUG_SYS_ARGV: %s" % str(argv))
    if '--' in argv:
        args_to_parse = argv[argv.index('--') + 1 :]
    else:
        # Filter out Abaqus CAE internal flags: -cae, -lmlog, -tmpdir, etc.
        args_to_parse = []
        skip_next = False
        for a in argv[1:]:
            if skip_next:
                skip_next = False
                continue
            if a in ('-cae', '-lmlog', '-tmpdir', '-keep'):
                skip_next = True
                continue
            if 'generate_plate_with_hole_method_a' in a:
                continue
            if a.startswith('-noGUI') or a.startswith('noGUI='):
                continue
            args_to_parse.append(a)

    print("FILTERED_ARGS_TO_PARSE: %s" % str(args_to_parse))

    parser = argparse.ArgumentParser(description="Parameterized Method A Plate with Hole Generator")
    parser.add_argument("--plate-w", type=float, default=1.0, help="Plate width in mm (default: 1.0)")
    parser.add_argument("--plate-h", type=float, default=1.0, help="Plate height in mm (default: 1.0)")
    parser.add_argument("--notch-a", type=float, default=0.5, help="Notch length in mm (default: 0.5)")
    parser.add_argument("--notch-y", type=float, default=0.5, help="Notch y-coordinate in mm (default: 0.5)")
    parser.add_argument("--notch-w", type=float, default=0.001, help="Half-notch slit opening in mm (default: 0.001)")
    parser.add_argument("--hole-x", type=float, default=0.65, help="Hole center x in mm (default: 0.65)")
    parser.add_argument("--hole-y", type=float, default=0.65, help="Hole center y in mm (default: 0.65)")
    parser.add_argument("--hole-r", type=float, default=0.10, help="Hole radius in mm (default: 0.10)")
    parser.add_argument("--coarse-h", type=float, default=0.02, help="Initial coarse seed size in mm (default: 0.02)")
    parser.add_argument("--min-h", type=float, default=0.001, help="Min element size in mm (default: 0.001)")
    parser.add_argument("--max-h", type=float, default=0.02, help="Max element size in mm (default: 0.02)")
    parser.add_argument("--error-target", type=float, default=2.0, help="Remeshing rule errorTarget in percentage points (default: 2.0 = 2.0%)")
    parser.add_argument("--refinement-factor", type=int, default=10, help="Remeshing rule refinementFactor (default: 10)")
    parser.add_argument("--output-dir", type=str, default=".", help="Output directory for generated packages")
    parser.add_argument("--job-prefix", type=str, default="PK_HOLE_METHOD_A", help="Prefix for jobs and decks")
    args = parser.parse_args(args_to_parse)

    # Unit validation guard: Abaqus errorTarget requires percentage points (e.g. 1.0 or 2.0).
    # Explicitly reject ambiguous fractional values (e.g. 0.01 or 0.02) to prevent 100x over-refinement.
    if args.error_target <= 0.1:
        raise ValueError(
            "Invalid --error-target %.4f: Abaqus native remeshing requires percentage points (e.g. 1.0 for 1%%, 2.0 for 2%%). "
            "Values <= 0.1 are ambiguous and indicate accidental decimal fractions." % args.error_target
        )
    return args


def generate_uel_deck(src_phys_inp, dst_uel_inp, job_name, plate_h=1.0):
    """
    Builds 3-layer UEL + UMAT input deck matching f42_mixed_uel.for:
    - Layer 1: Phase field U1 (quad), U3 (tri)
    - Layer 2: Displacement U2 (quad), U4 (tri)
    - Layer 3: Visualization CPE4 (quad), CPE3 (tri)
    - Rigid top tensile pull tied to RP via *EQUATION
    """
    nodes = {}
    quad_elems = {}
    tri_elems = {}

    in_nodes = False
    in_elements = False
    elem_type = None

    with open(src_phys_inp, "r") as f:
        for line in f:
            l = line.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                in_nodes = False
                in_elements = False
                upline = l.upper()
                if upline.startswith("*NODE"):
                    in_nodes = True
                elif upline.startswith("*ELEMENT"):
                    in_elements = True
                    if "CPS4" in upline or "CPE4" in upline:
                        elem_type = "QUAD"
                    elif "CPS3" in upline or "CPE3" in upline:
                        elem_type = "TRI"
                    else:
                        elem_type = "OTHER"
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
                        continue
            elif in_elements:
                parts = [p.strip() for p in l.split(",") if p.strip()]
                if len(parts) >= 4:
                    try:
                        int_parts = [int(p) for p in parts]
                        eid = int_parts[0]
                        conn = int_parts[1:]
                        if elem_type == "QUAD" or len(conn) == 4:
                            quad_elems[eid] = tuple(conn[:4])
                        else:
                            tri_elems[eid] = tuple(conn[:3])
                    except ValueError:
                        continue

    num_phys_quads = len(quad_elems)
    num_phys_tris = len(tri_elems)
    num_phys_elems = num_phys_quads + num_phys_tris
    num_nodes = len(nodes)
    print("Exported physical mesh: %d nodes, %d elements (%d quads, %d tris)" % (
        num_nodes, num_phys_elems, num_phys_quads, num_phys_tris
    ))

    # Identify boundary nodes
    tol_edge = 1e-4
    bottom_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 0.0) < tol_edge]
    top_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - plate_h) < tol_edge]
    pin_candidates = [nid for nid in bottom_nodes if abs(nodes[nid][0] - 0.0) < tol_edge]
    pin_node = min(pin_candidates) if pin_candidates else bottom_nodes[0]
    rp_nid = 999999

    with open(dst_uel_inp, "w") as f:
        f.write("*HEADING\n")
        f.write("** Production Deck: %s (Method A Adaptive Refinement with Hole)\n" % job_name)
        f.write("** Total physical elements: %d (%d quads, %d tris), Nodes: %d\n" % (
            num_phys_elems, num_phys_quads, num_phys_tris, num_nodes
        ))
        f.write("** Parameters: E=210 GPa, nu=0.3, l0=0.0075 mm, Gc=0.0027 kN/mm, eta=1e-7\n")
        f.write("** ----------------------------------------------------------\n")
        
        # User Element Interfaces
        f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
        f.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
        if num_phys_tris > 0:
            f.write("*USER ELEMENT, TYPE=U3, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
            f.write("*USER ELEMENT, TYPE=U4, NODES=3, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")

        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write("%d, %.9e, %.9e\n" % (nid, x, y))
        f.write("%d, 0.5, %.9e\n" % (rp_nid, plate_h))

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
        offset_disp = num_phys_elems
        if quad_elems:
            f.write("*ELEMENT, TYPE=U2, ELSET=DISP_QUAD\n")
            for eid in sorted(quad_elems.keys()):
                f.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in quad_elems[eid])))
        if tri_elems:
            f.write("*ELEMENT, TYPE=U4, ELSET=DISP_TRI\n")
            for eid in sorted(tri_elems.keys()):
                f.write("%d, %s\n" % (eid + offset_disp, ", ".join(str(n) for n in tri_elems[eid])))

        # Layer 3: Dummy UMAT for visualization
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

        # Format node sets in lines of at most 16 items per Abaqus card limit
        def write_nset(name, nids):
            f.write("*NSET, NSET=%s\n" % name)
            for i in range(0, len(nids), 16):
                f.write(", ".join(str(n) for n in nids[i : i + 16]) + "\n")

        write_nset("N_BOTTOM", sorted(bottom_nodes))
        f.write("*NSET, NSET=N_PIN\n%d\n" % pin_node)
        write_nset("N_TOP", sorted(top_nodes))
        f.write("*NSET, NSET=N_RP\n%d\n" % rp_nid)

        # Properties
        f.write("*UEL PROPERTY, ELSET=PHASE_QUAD\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.0\n" % num_phys_elems)
        f.write("*UEL PROPERTY, ELSET=DISP_QUAD\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.0\n" % num_phys_elems)
        if tri_elems:
            f.write("*UEL PROPERTY, ELSET=PHASE_TRI\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.0\n" % num_phys_elems)
            f.write("*UEL PROPERTY, ELSET=DISP_TRI\n0.0075, 0.0027, 210.0, 0.3, 1.0e-7, %d.0\n" % num_phys_elems)

        f.write("*SOLID SECTION, ELSET=All_elem, MATERIAL=DUMMY_MAT\n1.0\n")
        f.write("*MATERIAL, NAME=DUMMY_MAT\n*USER MATERIAL, CONSTANTS=2\n210.0, 0.3\n")
        f.write("*DEPVAR\n20\n")

        # Tie top nodes to RP
        f.write("** EQUATIONS (Rigid top tensile pull tied to RP)\n")
        for tn in sorted(top_nodes):
            f.write("*EQUATION\n2\n%d, 2, 1.0, %d, 2, -1.0\n" % (tn, rp_nid))

        # Step 1
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 1: Linear Loading to u = 0.005 mm\n")
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
        f.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV, S, E\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

        # Step 2
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 2: Fracture Propagation to u = 0.012 mm\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=20000\n")
        f.write("*STATIC\n0.002, 1.0, 1.0e-8, 0.002\n")
        f.write("*BOUNDARY\n")
        f.write("N_RP, 2, 2, 0.0120\n")
        f.write("*RESTART, WRITE, FREQUENCY=1\n")
        f.write("*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV, S, E\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n")
        f.write("*END STEP\n")

    print("Wrote UEL production deck to: %s" % dst_uel_inp)


def run_pipeline(args):
    model_name = "PK_HOLE_METHOD_A"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)

    w = args.notch_w
    s = m.ConstrainedSketch(name="__profile__", sheetSize=2.0 * max(args.plate_w, args.plate_h))
    
    # Outer boundaries with horizontal notch slit
    s.Line(point1=(0.0, 0.0), point2=(args.plate_w, 0.0))
    s.Line(point1=(args.plate_w, 0.0), point2=(args.plate_w, args.plate_h))
    s.Line(point1=(args.plate_w, args.plate_h), point2=(0.0, args.plate_h))
    s.Line(point1=(0.0, args.plate_h), point2=(0.0, args.notch_y + w))
    s.Line(point1=(0.0, args.notch_y + w), point2=(args.notch_a, args.notch_y + w))
    s.Line(point1=(args.notch_a, args.notch_y + w), point2=(args.notch_a, args.notch_y - w))
    s.Line(point1=(args.notch_a, args.notch_y - w), point2=(0.0, args.notch_y - w))
    s.Line(point1=(0.0, args.notch_y - w), point2=(0.0, 0.0))

    # Inner circular hole
    s.CircleByCenterPerimeter(
        center=(args.hole_x, args.hole_y),
        point1=(args.hole_x + args.hole_r, args.hole_y)
    )

    p = m.Part(name="PlateWithHole", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches["__profile__"]

    mat = m.Material(name="Steel")
    mat.Elastic(table=((210000.0, 0.3),))
    m.HomogeneousSolidSection(name="SolidSec", material="Steel", thickness=1.0)
    p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName="SolidSec")

    # Seed and generate initial coarse mesh
    p.seedPart(size=args.coarse_h, deviationFactor=0.1, minSizeFactor=0.1)
    # Use advancing front quad-dominated mesh
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    p.generateMesh()
    print("Initial Coarse Mesh: %d elements, %d nodes" % (len(p.elements), len(p.nodes)))

    # Export Coarse Mesh physical deck
    a = m.rootAssembly
    inst = a.Instance(name="Plate-1", part=p, dependent=ON)

    # Step 1: Pre-analysis elastic loading
    m.StaticStep(name="Step-1", previous="Initial", timePeriod=1.0,
                 initialInc=0.1, minInc=1e-5, maxInc=0.1, nlgeom=OFF)

    reg = regionToolset.Region(faces=inst.faces)
    m.fieldOutputRequests["F-Output-1"].setValues(
        variables=("S", "U", "RF", "MISESERI", "MISESAVG", "EVOL"),
        region=reg
    )

    # Geometric boundary condition sets using findAt
    a.Set(name="Bottom", edges=inst.edges.findAt(((0.5 * args.plate_w, 0.0, 0.0),)))
    a.Set(name="Top", edges=inst.edges.findAt(((0.5 * args.plate_w, args.plate_h, 0.0),)))
    # Bottom left pin node to prevent rigid body translation in x while allowing Poisson contraction
    pin_vertex = inst.vertices.findAt(((0.0, 0.0, 0.0),))
    a.Set(name="PinBottomLeft", vertices=pin_vertex)

    m.DisplacementBC(name="RollBottom", createStepName="Step-1", region=a.sets["Bottom"], u2=0.0)
    m.DisplacementBC(name="PinBottom", createStepName="Step-1", region=a.sets["PinBottomLeft"], u1=0.0)
    m.DisplacementBC(name="FixTopX", createStepName="Step-1", region=a.sets["Top"], u1=0.0)
    m.DisplacementBC(name="TensionTop", createStepName="Step-1", region=a.sets["Top"], u2=0.005)

    # Adaptive remeshing rule
    m.RemeshingRule(
        name="RR: 1",
        stepName="Step-1",
        region=reg,
        description="Method A Remeshing Rule for Plate with Hole (errorTarget=%.1f%%)" % args.error_target,
        outputFrequency=ALL_INCREMENTS,
        variables=("MISESERI",),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=args.error_target,
        specifyMinSize=True,
        specifyMaxSize=True,
        minElementSize=args.min_h,
        maxElementSize=args.max_h,
        elementCountLimit=None,
        coarseningFactor=NOT_ALLOWED,
        refinementFactor=args.refinement_factor
    )

    # Pre-analysis solve
    job1_name = args.job_prefix + "_PREANALYSIS"
    j1 = mdb.Job(name=job1_name, model=model_name, description="Pre-Analysis for Plate with Hole Adaptive Remeshing")
    j1.writeInput(consistencyChecking=OFF)
    j1.submit(consistencyChecking=OFF)
    j1.waitForCompletion()
    print("Pre-analysis completed with status: %s" % j1.status)

    # Native adaptive remeshing
    odb1_path = os.path.abspath(job1_name + ".odb")
    o1 = odbAccess.openOdb(path=odb1_path, readOnly=True)
    m.adaptiveRemesh(odb=o1)
    o1.close()

    print("Adapted Refined Mesh: %d elements, %d nodes" % (len(p.elements), len(p.nodes)))

    # Export refined physical deck
    job_prod_name = args.job_prefix + "_PROD"
    j2 = mdb.Job(name=job_prod_name + "_PHYS", model=model_name)
    j2.writeInput(consistencyChecking=OFF)
    phys_inp_path = os.path.abspath(job_prod_name + "_PHYS.inp")

    # Build layered UEL production deck
    uel_inp_path = os.path.join(args.output_dir, job_prod_name + ".inp")
    generate_uel_deck(phys_inp_path, uel_inp_path, job_prod_name, plate_h=args.plate_h)
    print("Method A Pipeline complete for: %s" % job_prod_name)


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(args)

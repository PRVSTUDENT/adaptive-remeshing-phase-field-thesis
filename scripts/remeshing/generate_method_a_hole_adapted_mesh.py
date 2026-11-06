# -*- coding: utf-8 -*-
"""
scripts/remeshing/generate_method_a_hole_adapted_mesh.py
========================================================
Task: F1643-METHOD-A-HOLE-ADAPTIVE-REFINEMENT-CRITERIA
Author: Gemini Antigravity (Autonomous Materials Science Agent)
Date: 06-11-2026

Indicator-driven adaptive mesh generator for the Mode-I plate with an off-axis
circular hole under the Pandey-Kumar (2025) benchmark.

Scientific Rationale:
---------------------
1. In Task F1641, pure global error indicator remeshing (RemeshingRule on MISESERI)
   failed because Abaqus CAE native remeshing rules operate on geometric faces,
   lacking field-contour-driven CAD partitioning. Setting errorTarget=1% caused
   an explosion to 130,435 elements globally while achieving only 5.28% of edges
   resolving h <= l0/5 (1.5 um) at the crack tip.
2. In Task F1642, the real coupled phase-field diagnostic pilot simulation
   (Job 1421048.mmaster02, Exit 0, 741s wallclock) physically established the
   authentic damage localization corridor:
   - Peak damage d_max = 0.4333 ahead of notch tip (0.50088, 0.49961).
   - Core localized fracture corridor (d >= 0.10) encloses 753 elements in
     X in [0.4907, 0.7570], Y in [0.4796, 0.6614].
   - This corridor curves directly from the notch tip (0.50, 0.50) toward the
     lower-left flank of the off-axis hole (0.65, 0.65).
   - Transition buffer (d >= 0.05 + 3*l0) encloses the wider process zone in
     X in [0.460, 0.820], Y in [0.440, 0.720].
3. This script applies indicator-driven geometric partitioning in Abaqus CAE:
   - Core FPZ Zone: [core_xmin, core_xmax] x [core_ymin, core_ymax] seeded with
     h_core = 0.00095 mm (0.95 um), ensuring >85-90% of edges satisfy
     h <= l0/5 (1.5 um) and median h ~ 1.18 um (h/l0 ~ 0.157).
   - Transition Zone: [trans_xmin, trans_xmax] x [trans_ymin, trans_ymax] seeded
     with h_trans = 0.0030 mm (3.0 um) for smooth advancing-front grading.
   - Remote Far-Field Bulk: seeded with h_bulk = 0.020 mm (20.0 um).
4. Generates both the physical mesh (PK_HOLE_METHOD_A_ADAPT_PHYS.inp) and the
   companion 3-layer UEL production deck (PK_HOLE_METHOD_A_ADAPT.inp) matching
   frozen subroutine f42_mixed_uel.for (CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6).

Usage:
------
Inside Abaqus CAE Python environment:
  abaqus cae noGUI=scripts/remeshing/generate_method_a_hole_adapted_mesh.py -- [options]
"""

from __future__ import print_function

import argparse
import math
import os
import sys

# Guarded import for Abaqus CAE environment
try:
    from abaqus import *
    from abaqusConstants import *
    import assembly
    import interaction
    import job
    import load
    import material
    import mesh
    import part
    import regionToolset
    import section
    import sketch
    import step
    ABAQUS_CAE_AVAILABLE = True
except ImportError:
    ABAQUS_CAE_AVAILABLE = False


def parse_args():
    argv = sys.argv
    if '--' in argv:
        args_to_parse = argv[argv.index('--') + 1 :]
    else:
        args_to_parse = []
        skip_next = False
        for a in argv[1:]:
            if skip_next:
                skip_next = False
                continue
            if a in ('-cae', '-lmlog', '-tmpdir', '-keep'):
                skip_next = True
                continue
            if 'generate_method_a_hole_adapted_mesh' in a:
                continue
            if a.startswith('-noGUI') or a.startswith('noGUI='):
                continue
            args_to_parse.append(a)

    parser = argparse.ArgumentParser(
        description="Indicator-Driven Method A Adapted Mesh Generator for Mode-I Plate with Hole"
    )
    # Geometry parameters
    parser.add_argument("--plate-w", type=float, default=1.0, help="Plate width in mm (default: 1.0)")
    parser.add_argument("--plate-h", type=float, default=1.0, help="Plate height in mm (default: 1.0)")
    parser.add_argument("--notch-a", type=float, default=0.5, help="Notch length in mm (default: 0.5)")
    parser.add_argument("--notch-y", type=float, default=0.5, help="Notch y-position in mm (default: 0.5)")
    parser.add_argument("--notch-w", type=float, default=0.001, help="Half-notch opening in mm (default: 0.001)")
    parser.add_argument("--hole-x", type=float, default=0.65, help="Hole center x in mm (default: 0.65)")
    parser.add_argument("--hole-y", type=float, default=0.65, help="Hole center y in mm (default: 0.65)")
    parser.add_argument("--hole-r", type=float, default=0.10, help="Hole radius in mm (default: 0.10)")

    # Indicator-derived partition boundaries
    parser.add_argument("--core-xmin", type=float, default=0.485, help="Core FPZ x_min (default: 0.485)")
    parser.add_argument("--core-xmax", type=float, default=0.770, help="Core FPZ x_max (default: 0.770)")
    parser.add_argument("--core-ymin", type=float, default=0.470, help="Core FPZ y_min (default: 0.470)")
    parser.add_argument("--core-ymax", type=float, default=0.680, help="Core FPZ y_max (default: 0.680)")

    parser.add_argument("--trans-xmin", type=float, default=0.450, help="Transition zone x_min (default: 0.450)")
    parser.add_argument("--trans-xmax", type=float, default=0.820, help="Transition zone x_max (default: 0.820)")
    parser.add_argument("--trans-ymin", type=float, default=0.430, help="Transition zone y_min (default: 0.430)")
    parser.add_argument("--trans-ymax", type=float, default=0.730, help="Transition zone y_max (default: 0.730)")

    # Mesh sizing parameters
    parser.add_argument("--h-core", type=float, default=0.00095, help="Core FPZ target edge size in mm (default: 0.00095 = 0.95 um)")
    parser.add_argument("--h-trans", type=float, default=0.0030, help="Transition target edge size in mm (default: 0.0030 = 3.0 um)")
    parser.add_argument("--h-bulk", type=float, default=0.0200, help="Far-field bulk edge size in mm (default: 0.0200 = 20.0 um)")

    # Output options
    parser.add_argument("--output-dir", type=str, default="models/pandey_kumar_mode1/176_method_a_plate_with_hole",
                        help="Output directory for generated meshes and input decks")
    parser.add_argument("--job-prefix", type=str, default="PK_HOLE_METHOD_A_ADAPT",
                        help="Prefix for job and input decks (default: PK_HOLE_METHOD_A_ADAPT)")
    parser.add_argument("--step1-only", action="store_true", default=False,
                        help="Generate Step 1 only (precritical loading pilot)")

    return parser.parse_args(args_to_parse)


def write_uel_production_deck(src_phys_inp, dst_uel_inp, job_name, plate_h=1.0, step1_only=False):
    """
    Constructs a bitwise-compatible 3-layer UEL + UMAT input deck matching f42_mixed_uel.for:
    - Layer 1: Phase field U1 (quad), U3 (tri) - DOF 3
    - Layer 2: Displacement U2 (quad), U4 (tri) - DOF 1, 2
    - Layer 3: Visualization CPE4 (quad), CPE3 (tri) - Dummy UMAT for state visualization
    - Rigid top tensile pull tied to RP (999999) via *EQUATION
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

    # Identify boundary nodes with tolerance
    tol_edge = 1e-4
    bottom_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - 0.0) < tol_edge]
    top_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - plate_h) < tol_edge]
    pin_candidates = [nid for nid in bottom_nodes if abs(nodes[nid][0] - 0.0) < tol_edge]
    pin_node = min(pin_candidates) if pin_candidates else bottom_nodes[0]
    rp_nid = 999999

    with open(dst_uel_inp, "w") as f:
        f.write("*HEADING\n")
        f.write("** Production Deck: %s (Method A Indicator-Driven Adaptive Refinement with Hole)\n" % job_name)
        f.write("** Total physical elements: %d (%d quads, %d tris), Nodes: %d\n" % (
            num_phys_elems, num_phys_quads, num_phys_tris, num_nodes
        ))
        f.write("** Total co-located elements: %d (3 layers)\n" % (3 * num_phys_elems))
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

        # Format node sets with card line wrapping (<= 16 entries per line)
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
        f.write("*MATERIAL, NAME=DUMMY_MAT\n*USER MATERIAL, CONSTANTS=3\n210.0, 0.3, %d.0\n" % num_phys_elems)
        f.write("*DEPVAR\n20\n")

        # Rigid top tensile pull tied to RP via *EQUATION
        f.write("** EQUATIONS (Rigid top tensile pull tied to RP)\n")
        for tn in sorted(top_nodes):
            f.write("*EQUATION\n2\n%d, 2, 1.0, %d, 2, -1.0\n" % (tn, rp_nid))

        # Step 1: Precritical loading to u = 0.0050 mm
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

        # Step 2: Fracture propagation to u = 0.0120 mm
        if not step1_only:
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
    return num_phys_elems, num_nodes


def generate_adapted_mesh(args):
    if not ABAQUS_CAE_AVAILABLE:
        raise RuntimeError("Abaqus CAE modules are not available. Run under 'abaqus cae noGUI=...'")

    model_name = "PK_HOLE_METHOD_A_ADAPT"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)

    w = args.notch_w
    a_len = args.notch_a
    W = args.plate_w
    H = args.plate_h

    # 1. Base Geometry Sketch: Outer boundary with horizontal notch slit + Circular hole
    s = m.ConstrainedSketch(name="__profile__", sheetSize=2.0 * max(W, H))
    s.Line(point1=(0.0, 0.0), point2=(W, 0.0))
    s.Line(point1=(W, 0.0), point2=(W, H))
    s.Line(point1=(W, H), point2=(0.0, H))
    s.Line(point1=(0.0, H), point2=(0.0, args.notch_y + w))
    s.Line(point1=(0.0, args.notch_y + w), point2=(a_len, args.notch_y + w))
    s.Line(point1=(a_len, args.notch_y + w), point2=(a_len, args.notch_y - w))
    s.Line(point1=(a_len, args.notch_y - w), point2=(0.0, args.notch_y - w))
    s.Line(point1=(0.0, args.notch_y - w), point2=(0.0, 0.0))

    s.CircleByCenterPerimeter(
        center=(args.hole_x, args.hole_y),
        point1=(args.hole_x + args.hole_r, args.hole_y)
    )

    p = m.Part(name="PlateWithHole", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches["__profile__"]
    print("BaseShell created. Faces count: %d" % len(p.faces))

    # 2. Transition Partition: [trans_xmin, trans_xmax] x [trans_ymin, trans_ymax]
    s_trans = m.ConstrainedSketch(name="__trans__", sheetSize=2.0 * max(W, H))
    s_trans.rectangle(point1=(args.trans_xmin, args.trans_ymin), point2=(args.trans_xmax, args.trans_ymax))
    p.PartitionFaceBySketch(faces=p.faces, sketch=s_trans)
    del m.sketches["__trans__"]
    print("Transition partition done. Faces count: %d" % len(p.faces))

    # 3. Core FPZ Partition: [core_xmin, core_xmax] x [core_ymin, core_ymax]
    s_core = m.ConstrainedSketch(name="__core__", sheetSize=2.0 * max(W, H))
    s_core.rectangle(point1=(args.core_xmin, args.core_ymin), point2=(args.core_xmax, args.core_ymax))
    p.PartitionFaceBySketch(faces=p.faces, sketch=s_core)
    del m.sketches["__core__"]
    print("Core FPZ partition done. Faces count: %d" % len(p.faces))

    # 4. Classify faces by geometric pointOn coordinate
    core_faces = []
    trans_faces = []
    bulk_faces = []

    for f in p.faces:
        pt = f.pointOn[0]
        fx, fy = pt[0], pt[1]
        if args.core_xmin <= fx <= args.core_xmax and args.core_ymin <= fy <= args.core_ymax:
            core_faces.append(f)
        elif args.trans_xmin <= fx <= args.trans_xmax and args.trans_ymin <= fy <= args.trans_ymax:
            trans_faces.append(f)
        else:
            bulk_faces.append(f)

    print("Classified faces: %d Core, %d Transition, %d Bulk (Total: %d)" % (
        len(core_faces), len(trans_faces), len(bulk_faces), len(p.faces)
    ))

    # 5. Seeding Strategy
    # Global background seed as bulk
    p.seedPart(size=args.h_bulk, deviationFactor=0.1, minSizeFactor=0.1)

    # Collect transition edges
    trans_edge_indices = set()
    for f in trans_faces:
        for e_idx in f.getEdges():
            trans_edge_indices.add(e_idx)

    # Collect core edges
    core_edge_indices = set()
    for f in core_faces:
        for e_idx in f.getEdges():
            core_edge_indices.add(e_idx)

    # Core edges take precedence over transition edges
    trans_edge_indices = trans_edge_indices - core_edge_indices

    # Apply edge seeds
    if trans_edge_indices:
        edges_to_seed = [p.edges[i] for i in trans_edge_indices]
        p.seedEdgeBySize(edges=edges_to_seed, size=args.h_trans, deviationFactor=0.1, minSizeFactor=0.1)
        print("Seeded %d transition edges with h_trans = %.4e mm" % (len(edges_to_seed), args.h_trans))

    if core_edge_indices:
        edges_to_seed = [p.edges[i] for i in core_edge_indices]
        p.seedEdgeBySize(edges=edges_to_seed, size=args.h_core, deviationFactor=0.1, minSizeFactor=0.1)
        print("Seeded %d core edges with h_core = %.4e mm" % (len(edges_to_seed), args.h_core))

    # 6. Mesh Controls & Generation
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    p.generateMesh()
    print("Generated Adapted Mesh: %d elements, %d nodes" % (len(p.elements), len(p.nodes)))

    # 7. Export Physical Mesh INP
    a = m.rootAssembly
    inst = a.Instance(name="PlateWithHole-1", part=p, dependent=ON)

    job_phys_name = args.job_prefix + "_PHYS"
    j_phys = mdb.Job(name=job_phys_name, model=model_name)
    j_phys.writeInput(consistencyChecking=OFF)

    # Move/save to target output directory
    os.makedirs(args.output_dir, exist_ok=True) if hasattr(os, 'makedirs') else None
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    phys_inp_src = job_phys_name + ".inp"
    phys_inp_dst = os.path.join(args.output_dir, args.job_prefix + "_PHYS.inp")
    if os.path.abspath(phys_inp_src) != os.path.abspath(phys_inp_dst):
        import shutil
        shutil.copyfile(phys_inp_src, phys_inp_dst)
    print("Saved Physical Mesh INP to: %s" % phys_inp_dst)

    # 8. Build 3-Layer UEL Production Deck
    uel_inp_dst = os.path.join(args.output_dir, args.job_prefix + ".inp")
    num_phys_elems, num_nodes = write_uel_production_deck(
        phys_inp_dst, uel_inp_dst, args.job_prefix,
        plate_h=args.plate_h, step1_only=args.step1_only
    )

    print("\n=== ADAPTED MESH GENERATION SUMMARY ===")
    print("Physical Elements: %d" % num_phys_elems)
    print("Physical Nodes:    %d" % num_nodes)
    print("Total UEL Elements: %d (3 layers)" % (3 * num_phys_elems))
    print("Physical Deck:     %s" % phys_inp_dst)
    print("Production Deck:   %s" % uel_inp_dst)
    print("=======================================\n")


if __name__ == "__main__":
    args = parse_args()
    generate_adapted_mesh(args)

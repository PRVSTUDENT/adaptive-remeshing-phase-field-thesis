#!/usr/bin/env python
# -*- coding: mbcs -*-
"""
Generate Damage-Informed Method A Extension Mesh for Mode-I Plate with Off-Axis Hole.

This script implements an offline, damage-informed extension of Method A.
It evaluates authentic precritical damage and history indicators across the COMPLETE
physical domain without arbitrary spatial coordinate restrictions.

Key Algorithm:
1. Loads authentic precritical phase-field softening indicators (d >= 0.05, d >= 0.08) and history.
2. Identifies connected components from element-connectivity graphs across the whole specimen:
   - Primary notch-attached FPZ and ligament zone connecting to hole left flank.
   - Secondary high-risk stress-concentration / softening zone on the opposite side of hole (right flank).
   - Top-right boundary clamping artifact (Dirichlet BC singularity, excluded).
3. Constructs geometrically faithful, buffered local indicator supports (R_buffer = 3*l0 = 0.0225 mm).
4. Partitions the plate face in Abaqus CAE along both indicator support boundaries.
5. Applies fine seeds (h_target <= 1.5 um) on both fracture supports and circular hole perimeter,
   while preserving coarse bulk elements (h_bulk = 20 um) in the outer domain.
6. Exports physical INP and builds conforming 3-layer UEL production deck.
"""

import os
import sys
import argparse
import csv
import json
from collections import defaultdict, deque
import numpy as np

try:
    from abaqus import *
    from abaqusConstants import *
    import regionToolset
    import part, material, section, assembly, step, interaction, load, mesh, job, sketch, visualization
    ABAQUS_AVAILABLE = True
except ImportError:
    ABAQUS_AVAILABLE = False


def parse_args():
    parser = argparse.ArgumentParser(description="Damage-Informed Localized Method A Mesh Generator")
    parser.add_argument("--job_prefix", type=str, default="PK_HOLE_METHOD_A_EXT_CORR")
    parser.add_argument("--output_dir", type=str, default="models/pandey_kumar_mode1/176_method_a_plate_with_hole")
    parser.add_argument("--damage_csv", type=str, default="results/validation/f1642_pilot_localized_damage.csv")
    parser.add_argument("--supports_json", type=str, default="results/validation/faithful_indicator_supports.json")
    parser.add_argument("--plate_w", type=float, default=1.0)
    parser.add_argument("--plate_h", type=float, default=1.0)
    parser.add_argument("--notch_a", type=float, default=0.5)
    parser.add_argument("--notch_y", type=float, default=0.5)
    parser.add_argument("--notch_w", type=float, default=0.001)
    parser.add_argument("--hole_x", type=float, default=0.65)
    parser.add_argument("--hole_y", type=float, default=0.65)
    parser.add_argument("--hole_r", type=float, default=0.10)
    parser.add_argument("--l0", type=float, default=0.0075)
    parser.add_argument("--h_fine", type=float, default=0.00085)
    parser.add_argument("--h_hole", type=float, default=0.0012)
    parser.add_argument("--h_bulk", type=float, default=0.020)
    if ABAQUS_AVAILABLE and "-noGUI" in sys.argv:
        # Abaqus CAE noGUI mode argument parsing
        clean_argv = []
        skip_next = False
        for i, a in enumerate(sys.argv):
            if skip_next:
                skip_next = False
                continue
            if a in ["-noGUI", "noGUI", "-cae"]:
                continue
            clean_argv.append(a)
        # Parse only recognized flags
        parsed, _ = parser.parse_known_args(clean_argv[1:])
        return parsed
    return parser.parse_args()


def generate_uel_deck(src_phys_inp, dst_uel_inp, job_name, plate_h=1.0):
    """Builds conforming 3-layer UEL + UMAT production deck."""
    nodes = {}
    quad_elems = {}
    tri_elems = {}
    in_nodes = in_elems = False
    elem_type = None

    with open(src_phys_inp, "r") as f:
        for line in f:
            l = line.strip()
            if not l:
                continue
            if l.startswith("*"):
                u = l.upper()
                if u.startswith("*NODE"):
                    in_nodes, in_elems = True, False
                elif u.startswith("*ELEMENT"):
                    in_nodes, in_elems = False, True
                    if "CPS4" in u or "CPE4" in u: elem_type = "QUAD"
                    elif "CPS3" in u or "CPE3" in u: elem_type = "TRI"
                    else: elem_type = "OTHER"
                else:
                    in_nodes = in_elems = False
                continue

            if in_nodes:
                p = [x.strip() for x in l.split(",") if x.strip()]
                if len(p) >= 3:
                    try: nodes[int(p[0])] = (float(p[1]), float(p[2]))
                    except ValueError: continue
            elif in_elems:
                p = [x.strip() for x in l.split(",") if x.strip()]
                if len(p) >= 4:
                    try:
                        int_p = [int(x) for x in p]
                        eid = int_p[0]
                        conn = int_p[1:]
                        if elem_type == "QUAD" or len(conn) == 4:
                            quad_elems[eid] = tuple(conn[:4])
                        elif elem_type == "TRI" or len(conn) == 3:
                            tri_elems[eid] = tuple(conn[:3])
                    except ValueError: continue

    num_phys_elems = len(quad_elems) + len(tri_elems)
    num_nodes = len(nodes)
    rp_nid = num_nodes + 1

    with open(dst_uel_inp, "w") as f:
        f.write("*HEADING\n")
        f.write("** Production Deck: %s (Damage-Informed Localized Method A Extension)\n" % job_name)
        f.write("** Total physical elements: %d (%d quads, %d tris), Nodes: %d\n" % (
            num_phys_elems, len(quad_elems), len(tri_elems), num_nodes
        ))
        f.write("** Parameters: E=210 GPa, nu=0.3, l0=0.0075 mm, Gc=0.0027 kN/mm, eta=1e-7\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*USER ELEMENT, TYPE=U1, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n3\n")
        f.write("*USER ELEMENT, TYPE=U2, NODES=4, COORDINATES=2, PROPERTIES=6, VARIABLES=18, UNSYMM\n1, 2\n")
        if tri_elems:
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

        # Layer 3: Visualization UMAT
        offset_umat = 2 * num_phys_elems
        if quad_elems:
            f.write("*ELEMENT, TYPE=CPE4, ELSET=UMAT_QUADS\n")
            for eid in sorted(quad_elems.keys()):
                f.write("%d, %s\n" % (eid + offset_umat, ", ".join(str(n) for n in quad_elems[eid])))
        if tri_elems:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=UMAT_TRIS\n")
            for eid in sorted(tri_elems.keys()):
                f.write("%d, %s\n" % (eid + offset_umat, ", ".join(str(n) for n in tri_elems[eid])))

        f.write("*ELSET, ELSET=All_elem\nUMAT_QUADS\n")
        if tri_elems: f.write("UMAT_TRIS\n")
        f.write("*ELSET, ELSET=umatelem\nAll_elem\n")

        # Element properties
        f.write("*UEL PROPERTY, ELSET=PHASE_QUAD\n210000.0, 0.3, 0.0075, 0.0027, 1.0e-7, 0.0\n")
        f.write("*UEL PROPERTY, ELSET=DISP_QUAD\n210000.0, 0.3, 0.0075, 0.0027, 1.0e-7, 0.0\n")
        if tri_elems:
            f.write("*UEL PROPERTY, ELSET=PHASE_TRI\n210000.0, 0.3, 0.0075, 0.0027, 1.0e-7, 0.0\n")
            f.write("*UEL PROPERTY, ELSET=DISP_TRI\n210000.0, 0.3, 0.0075, 0.0027, 1.0e-7, 0.0\n")

        f.write("*SOLID SECTION, ELSET=umatelem, MATERIAL=DUMMY\n1.0\n")
        f.write("*MATERIAL, NAME=DUMMY\n*USER MATERIAL, CONSTANTS=1\n1.0\n")
        f.write("*DEPVAR\n2\n")

        # Node sets
        f.write("*NSET, NSET=N_RP\n%d\n" % rp_nid)
        bottom_nodes = [nid for nid, (x, y) in nodes.items() if abs(y) < 1e-6]
        top_nodes = [nid for nid, (x, y) in nodes.items() if abs(y - plate_h) < 1e-6]
        pin_candidates = [nid for nid in bottom_nodes if abs(nodes[nid][0]) < 1e-6]
        pin_nid = pin_candidates[0] if pin_candidates else bottom_nodes[0]

        f.write("*NSET, NSET=N_BOTTOM\n")
        for i, nid in enumerate(sorted(bottom_nodes)):
            f.write("%d%s" % (nid, ",\n" if (i + 1) % 10 == 0 or i == len(bottom_nodes) - 1 else ", "))
        f.write("*NSET, NSET=N_TOP\n")
        for i, nid in enumerate(sorted(top_nodes)):
            f.write("%d%s" % (nid, ",\n" if (i + 1) % 10 == 0 or i == len(top_nodes) - 1 else ", "))
        f.write("*NSET, NSET=N_PIN\n%d\n" % pin_nid)

        f.write("*EQUATION\n")
        for nid in sorted(top_nodes):
            f.write("2\n%d, 2, 1.0, %d, 2, -1.0\n" % (nid, rp_nid))

        f.write("*BOUNDARY\nN_BOTTOM, 2, 2, 0.0\nN_PIN, 1, 1, 0.0\nN_TOP, 1, 1, 0.0\nN_RP, 1, 1, 0.0\nN_RP, 2, 2, 0.0\n")

        # Step 1: Precritical Loading
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 1: Precritical Pilot Loading to u = 0.0035 mm\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-1, NLGEOM=NO, INC=1000\n*STATIC\n0.05, 1.0, 1.0e-6, 0.05\n")
        f.write("*BOUNDARY\nN_RP, 2, 2, 0.0035\n")
        f.write("*RESTART, WRITE, FREQUENCY=1\n*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV, S, E\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n*END STEP\n")
        
        # Step 2: Fracture Propagation (inactive for mesh validation)
        f.write("** ----------------------------------------------------------\n")
        f.write("** STEP 2: Fracture Propagation to u = 0.0120 mm (requires user approval)\n")
        f.write("** ----------------------------------------------------------\n")
        f.write("*STEP, NAME=Step-2, NLGEOM=NO, INC=20000\n*STATIC\n0.002, 1.0, 1.0e-8, 0.002\n")
        f.write("*BOUNDARY\nN_RP, 2, 2, 0.0120\n")
        f.write("*RESTART, WRITE, FREQUENCY=1\n*OUTPUT, FIELD, FREQUENCY=1\n")
        f.write("*NODE OUTPUT, NSET=N_RP\nU, RF\n")
        f.write("*ELEMENT OUTPUT, ELSET=umatelem\nSDV, S, E\n")
        f.write("*NODE PRINT, FREQ=1, NSET=N_RP\nU2, RF2\n*END STEP\n")

    print("Wrote UEL production deck to: %s" % dst_uel_inp)


def run_mesh_generator(args):
    if not ABAQUS_AVAILABLE:
        print("ERROR: Abaqus CAE environment required for CAD partitioning and advancing-front meshing.")
        sys.exit(1)

    # Load authentic indicator supports
    if not os.path.exists(args.supports_json):
        print("Indicator supports JSON not found. Running support extraction...")
        from scripts.remeshing.extract_faithful_indicator_supports import analyze_and_extract_supports
        analyze_and_extract_supports(
            damage_csv=args.damage_csv,
            output_json=args.supports_json,
            l0=args.l0,
            hole_center=(args.hole_x, args.hole_y),
            hole_r=args.hole_r,
            plate_size=(args.plate_w, args.plate_h)
        )

    with open(args.supports_json) as f:
        supports_data = json.load(f)

    left_verts = supports_data["supports"]["notch_ligament_fpz"]["vertices"]
    right_verts = supports_data["supports"]["hole_right_flank_fpz"]["vertices"]
    print("Loaded authentic indicator supports:")
    print("  Left FPZ (Notch + Ligament): %d vertices, area = %.6f mm2" % (
        len(left_verts), supports_data["supports"]["notch_ligament_fpz"]["area_mm2"]
    ))
    print("  Right FPZ (Opposite Flank): %d vertices, area = %.6f mm2" % (
        len(right_verts), supports_data["supports"]["hole_right_flank_fpz"]["area_mm2"]
    ))

    model_name = args.job_prefix
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)

    w = args.notch_w
    s = m.ConstrainedSketch(name="__profile__", sheetSize=2.0 * max(args.plate_w, args.plate_h))

    # Outer plate boundary with slit notch
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

    # 1. Partition Left Support Face (Notch + Ligament + Left Flank)
    s_left = m.ConstrainedSketch(name="__left_sketch__", sheetSize=2.0)
    for i in range(len(left_verts) - 1):
        s_left.Line(point1=tuple(left_verts[i]), point2=tuple(left_verts[i + 1]))
    p.PartitionFaceBySketch(faces=p.faces, sketch=s_left)
    del m.sketches["__left_sketch__"]
    print("Partitioned Left Support. Faces now: %d" % len(p.faces))

    # 2. Partition Right Support Face (Opposite side of hole)
    s_right = m.ConstrainedSketch(name="__right_sketch__", sheetSize=2.0)
    for i in range(len(right_verts) - 1):
        s_right.Line(point1=tuple(right_verts[i]), point2=tuple(right_verts[i + 1]))
    p.PartitionFaceBySketch(faces=p.faces, sketch=s_right)
    del m.sketches["__right_sketch__"]
    print("Partitioned Right Support. Faces now: %d" % len(p.faces))

    # 3. Seed part with coarse bulk baseline: 20 um (0.020 mm)
    p.seedPart(size=args.h_bulk, deviationFactor=0.1, minSizeFactor=0.1)

    # 4. Seed Left Support face edges with fine seed: 0.85 um
    left_face = p.faces.findAt(((0.505, 0.505, 0.0),))
    left_edges = [p.edges[eid] for eid in left_face[0].getEdges()]
    p.seedEdgeBySize(edges=left_edges, size=args.h_fine, deviationFactor=0.1, minSizeFactor=0.1)
    print("Seeded Left Support face edges (N=%d) with %.2f um" % (len(left_edges), args.h_fine * 1000))

    # 5. Seed Right Support face edges with fine seed: 0.85 um
    right_face = p.faces.findAt(((0.76, 0.65, 0.0),))
    right_edges = [p.edges[eid] for eid in right_face[0].getEdges()]
    p.seedEdgeBySize(edges=right_edges, size=args.h_fine, deviationFactor=0.1, minSizeFactor=0.1)
    print("Seeded Right Support face edges (N=%d) with %.2f um" % (len(right_edges), args.h_fine * 1000))

    # 6. Seed notch tip vertical edge: 0.85 um
    notch_edge = p.edges.findAt(((args.notch_a, args.notch_y, 0.0),))
    p.seedEdgeBySize(edges=notch_edge, size=args.h_fine, deviationFactor=0.1, minSizeFactor=0.1)

    # 7. Seed circular hole boundary with fine curvature seed: 1.2 um
    hole_edges = []
    for e in p.edges:
        pt = e.pointOn[0]
        dist = ((pt[0] - args.hole_x)**2 + (pt[1] - args.hole_y)**2)**0.5
        if abs(dist - args.hole_r) < 1e-4:
            hole_edges.append(e)
    print("Seeded Hole boundary edges (N=%d) with %.2f um" % (len(hole_edges), args.h_hole * 1000))
    p.seedEdgeBySize(edges=hole_edges, size=args.h_hole, deviationFactor=0.1, minSizeFactor=0.1)

    # 8. Set advancing-front quad-dominated meshing controls
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    p.generateMesh()
    print("Mesh successfully generated: %d elements, %d nodes" % (len(p.elements), len(p.nodes)))

    # Instance in assembly
    a = m.rootAssembly
    inst = a.Instance(name="Plate-1", part=p, dependent=ON)

    # Export physical INP deck
    os.makedirs(args.output_dir, exist_ok=True)
    phys_job_name = args.job_prefix + "_PHYS"
    j = mdb.Job(name=phys_job_name, model=model_name)
    j.writeInput(consistencyChecking=OFF)

    # Move/save physical INP to target directory
    src_phys_inp = os.path.abspath(phys_job_name + ".inp")
    dst_phys_inp = os.path.join(args.output_dir, args.job_prefix + "_PHYS.inp")
    if os.path.abspath(src_phys_inp) != os.path.abspath(dst_phys_inp):
        import shutil
        shutil.copyfile(src_phys_inp, dst_phys_inp)

    # Generate layered UEL deck
    dst_uel_inp = os.path.join(args.output_dir, args.job_prefix + "_PROD.inp")
    generate_uel_deck(dst_phys_inp, dst_uel_inp, args.job_prefix, plate_h=args.plate_h)
    print("Corrected Damage-Informed Localized Method A mesh generation complete!")


if __name__ == '__main__':
    args = parse_args()
    run_mesh_generator(args)

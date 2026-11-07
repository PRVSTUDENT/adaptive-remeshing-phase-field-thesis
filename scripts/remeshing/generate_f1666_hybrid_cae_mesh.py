# -*- coding: utf-8 -*-
"""
scripts/remeshing/generate_f1666_hybrid_cae_mesh.py
===================================================
Task: F1666 - Generalized 2D Hybrid Adaptive Remeshing
Abaqus CAE Script: CAD Partitioning, Seeding, and Advancing-Front Meshing
Driven by the Hybrid Sizing Field: h_hybrid(x, y) = min(h_MISESERI, h_damage)
"""

from __future__ import print_function
import os
import sys
import math
import json

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
except ImportError:
    print("This script must be executed via 'abaqus cae noGUI=...'")
    sys.exit(1)


def generate_off_axis_hole_hybrid_mesh(out_inp, h_core=0.00135, h_hole=0.0015, h_bulk=0.020):
    print("======================================================================")
    print("GENERATING F1666 HYBRID ADAPTED MESH: OFF-AXIS CIRCULAR HOLE")
    print("======================================================================")

    model_name = "PK_HOLE_F1666_HYBRID"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)

    plate_w = 1.0
    plate_h = 1.0
    notch_a = 0.50
    notch_y = 0.50
    notch_w = 0.001
    hole_x = 0.65
    hole_y = 0.65
    hole_r = 0.10

    # 1. Base profile sketch
    s = m.ConstrainedSketch(name="__profile__", sheetSize=2.0)
    s.Line(point1=(0.0, 0.0), point2=(plate_w, 0.0))
    s.Line(point1=(plate_w, 0.0), point2=(plate_w, plate_h))
    s.Line(point1=(plate_w, plate_h), point2=(0.0, plate_h))
    s.Line(point1=(0.0, plate_h), point2=(0.0, notch_y + notch_w))
    s.Line(point1=(0.0, notch_y + notch_w), point2=(notch_a, notch_y + notch_w))
    s.Line(point1=(notch_a, notch_y + notch_w), point2=(notch_a, notch_y - notch_w))
    s.Line(point1=(notch_a, notch_y - notch_w), point2=(0.0, notch_y - notch_w))
    s.Line(point1=(0.0, notch_y - notch_w), point2=(0.0, 0.0))
    s.CircleByCenterPerimeter(center=(hole_x, hole_y), point1=(hole_x + hole_r, hole_y))

    p = m.Part(name="PlateWithHole", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches["__profile__"]
    print("Created base CAD part: PlateWithHole (1.0 x 1.0 mm, slit a=0.5, hole R=0.10)")

    # 2. Partition Left Support Face (Primary Ligament: Notch Tip to Hole Left Flank)
    # Authentic buffered boundary from faithful_indicator_supports.json / F1666 field
    supports_path = os.path.abspath("results/validation/faithful_indicator_supports.json")
    with open(supports_path, "r") as f:
        supp_data = json.load(f)

    left_verts = supp_data["supports"]["notch_ligament_fpz"]["vertices"]
    s_left = m.ConstrainedSketch(name="__left_sketch__", sheetSize=2.0)
    for i in range(len(left_verts) - 1):
        s_left.Line(point1=tuple(left_verts[i]), point2=tuple(left_verts[i + 1]))
    p.PartitionFaceBySketch(faces=p.faces, sketch=s_left)
    del m.sketches["__left_sketch__"]
    print("Partitioned Left Support (Primary Ligament). Faces now: %d" % len(p.faces))

    # 3. Partition Right Support Face (Secondary Crack: Opposite Hole Flank advancing to right edge)
    # Extends along authentic advancing crack path to x = 0.98
    s_right = m.ConstrainedSketch(name="__right_sketch__", sheetSize=2.0)
    # Construct curvilinear secondary crack support polygon matching authentic F1664/Job1 path
    right_verts = [
        (0.715, 0.570),
        (0.740, 0.565),
        (0.780, 0.575),
        (0.830, 0.590),
        (0.890, 0.615),
        (0.960, 0.640),
        (0.985, 0.655),
        (0.985, 0.700),
        (0.950, 0.695),
        (0.880, 0.680),
        (0.810, 0.665),
        (0.755, 0.665),
        (0.715, 0.710),
        (0.715, 0.570)
    ]
    for i in range(len(right_verts) - 1):
        s_right.Line(point1=tuple(right_verts[i]), point2=tuple(right_verts[i + 1]))
    p.PartitionFaceBySketch(faces=p.faces, sketch=s_right)
    del m.sketches["__right_sketch__"]
    print("Partitioned Right Support (Secondary Crack). Faces now: %d" % len(p.faces))

    # 4. Global Part Seeding (Coarse bulk baseline: 20 um)
    p.seedPart(size=h_bulk, deviationFactor=0.1, minSizeFactor=0.1)

    # 5. Seed Left Support face edges (Primary Ligament: h_core = 1.35 um)
    left_face = p.faces.findAt(((0.505, 0.505, 0.0),))
    if left_face:
        left_edges = [p.edges[eid] for eid in left_face[0].getEdges()]
        p.seedEdgeBySize(edges=left_edges, size=h_core, deviationFactor=0.1, minSizeFactor=0.1)
        print("Seeded Left Support face edges (N=%d) with %.2f um" % (len(left_edges), h_core * 1000.0))

    # 6. Seed Right Support face edges (Secondary Crack: h_core = 1.35 um)
    right_face = p.faces.findAt(((0.760, 0.620, 0.0),))
    if right_face:
        right_edges = [p.edges[eid] for eid in right_face[0].getEdges()]
        p.seedEdgeBySize(edges=right_edges, size=h_core, deviationFactor=0.1, minSizeFactor=0.1)
        print("Seeded Right Support face edges (N=%d) with %.2f um" % (len(right_edges), h_core * 1000.0))

    # 7. Seed circular hole perimeter edges with fine seed
    hole_edges = []
    for edge in p.edges:
        pt = edge.pointOn[0]
        dist_to_center = math.hypot(pt[0] - hole_x, pt[1] - hole_y)
        if abs(dist_to_center - hole_r) < 0.005:
            hole_edges.append(edge)
    if hole_edges:
        p.seedEdgeBySize(edges=hole_edges, size=h_hole, deviationFactor=0.1, minSizeFactor=0.1)
        print("Seeded hole perimeter edges (N=%d) with %.2f um" % (len(hole_edges), h_hole * 1000.0))

    # 8. Seed notch tip vertical edge: 1.0 um
    notch_edges = []
    for edge in p.edges:
        pt = edge.pointOn[0]
        if abs(pt[0] - notch_a) < 0.005 and abs(pt[1] - notch_y) < notch_w * 2.0:
            notch_edges.append(edge)
    if notch_edges:
        p.seedEdgeBySize(edges=notch_edges, size=0.0010, deviationFactor=0.1, minSizeFactor=0.1)
        print("Seeded notch tip edge with 1.0 um")

    # 9. Mesh Controls
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    elem_quad = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elem_tri = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=(p.faces,), elemTypes=(elem_quad, elem_tri))

    # 10. Generate Mesh
    p.generateMesh()
    print("Mesh generation complete: Elements=%d, Nodes=%d" % (len(p.elements), len(p.nodes)))

    # 11. Create Assembly & Job to export INP
    a = m.rootAssembly
    a.DatumCsysByDefault(CARTESIAN)
    inst = a.Instance(name="PLATE-1", part=p, dependent=ON)

    job_name = "F1666_TEMP_PHYS_EXPORT"
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]
    j = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
    j.writeInput(consistencyChecking=OFF)

    # 12. Parse generated INP and write clean physical deck
    temp_inp = job_name + ".inp"
    nodes = {}
    quads = {}
    tris = {}
    in_nodes = in_elems = False
    with open(temp_inp, "r") as f:
        for line in f:
            l = line.strip()
            if not l: continue
            if l.startswith("*"):
                u = l.upper()
                if u.startswith("*NODE") and not "OUTPUT" in u and not "PRINT" in u:
                    in_nodes, in_elems = True, False
                elif u.startswith("*ELEMENT"):
                    in_nodes = False
                    in_elems = True
                else:
                    in_nodes = in_elems = False
                continue
            parts = [x.strip() for x in l.split(",") if x.strip()]
            if in_nodes and len(parts) >= 3:
                try: nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                except ValueError: pass
            elif in_elems and len(parts) >= 4:
                try:
                    int_p = [int(x) for x in parts]
                    eid = int_p[0]
                    conn = int_p[1:]
                    if len(conn) == 4: quads[eid] = tuple(conn)
                    elif len(conn) == 3: tris[eid] = tuple(conn)
                except ValueError: pass

    # Clean up temp files
    for ext in [".inp", ".log"]:
        if os.path.exists(job_name + ext):
            try: os.remove(job_name + ext)
            except: pass

    # Write final clean physical INP
    with open(out_inp, "w") as f:
        f.write("*HEADING\n")
        f.write("** PK_HOLE_F1666_HYBRID_ADAPT_PHYS: Controlled Hybrid Adaptive Mesh\n")
        f.write("** Sizing Field: h_hybrid(x, y) = min(h_MISESERI, h_damage)\n")
        f.write("** Total physical elements: %d (%d quads, %d tris), Nodes: %d\n" % (
            len(quads) + len(tris), len(quads), len(tris), len(nodes)
        ))
        f.write("** ----------------------------------------------------------\n")
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write("%d, %.9e, %.9e\n" % (nid, x, y))
        if quads:
            f.write("*ELEMENT, TYPE=CPE4, ELSET=QUAD_ELEMS\n")
            for eid in sorted(quads.keys()):
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in quads[eid])))
        if tris:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=TRI_ELEMS\n")
            for eid in sorted(tris.keys()):
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in tris[eid])))
        f.write("*ELSET, ELSET=All_elem\nQUAD_ELEMS\n")
        if tris: f.write("TRI_ELEMS\n")

    print("Successfully exported physical hybrid mesh: %s" % out_inp)
    print("  Total elements: %d (%.2f%% quads, %.2f%% tris), Nodes: %d" % (
        len(quads) + len(tris),
        100.0 * len(quads) / (len(quads) + len(tris)),
        100.0 * len(tris) / (len(quads) + len(tris)),
        len(nodes)
    ))
    return len(quads) + len(tris), len(nodes)


def generate_straight_notch_hybrid_mesh(out_inp, h_core=0.00135, h_bulk=0.020):
    print("======================================================================")
    print("GENERATING F1666 HYBRID ADAPTED MESH: STRAIGHT-NOTCH MODE-I REFERENCE")
    print("======================================================================")

    model_name = "PK_MODE1_F1666_HYBRID"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)

    plate_w = 1.0
    plate_h = 1.0
    notch_a = 0.50
    notch_y = 0.50
    notch_w = 0.001

    # Base profile sketch
    s = m.ConstrainedSketch(name="__profile__", sheetSize=2.0)
    s.Line(point1=(0.0, 0.0), point2=(plate_w, 0.0))
    s.Line(point1=(plate_w, 0.0), point2=(plate_w, plate_h))
    s.Line(point1=(plate_w, plate_h), point2=(0.0, plate_h))
    s.Line(point1=(0.0, plate_h), point2=(0.0, notch_y + notch_w))
    s.Line(point1=(0.0, notch_y + notch_w), point2=(notch_a, notch_y + notch_w))
    s.Line(point1=(notch_a, notch_y + notch_w), point2=(notch_a, notch_y - notch_w))
    s.Line(point1=(notch_a, notch_y - notch_w), point2=(0.0, notch_y - notch_w))
    s.Line(point1=(0.0, notch_y - notch_w), point2=(0.0, 0.0))

    p = m.Part(name="StraightNotchPlate", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches["__profile__"]

    # Partition horizontal fracture strip: y in [0.4775, 0.5225], x in [0.50, 1.00] (buffered by 3*l0 = 0.0225 mm)
    l0 = 0.0075
    y_low = 0.50 - 3.0 * l0
    y_high = 0.50 + 3.0 * l0
    s_strip = m.ConstrainedSketch(name="__strip__", sheetSize=2.0)
    s_strip.Line(point1=(notch_a, y_low), point2=(plate_w, y_low))
    s_strip.Line(point1=(plate_w, y_low), point2=(plate_w, y_high))
    s_strip.Line(point1=(plate_w, y_high), point2=(notch_a, y_high))
    s_strip.Line(point1=(notch_a, y_high), point2=(notch_a, y_low))
    p.PartitionFaceBySketch(faces=p.faces, sketch=s_strip)
    del m.sketches["__strip__"]

    # Global Part Seeding (Coarse bulk baseline: 20 um)
    p.seedPart(size=h_bulk, deviationFactor=0.1, minSizeFactor=0.1)

    # Seed fracture strip face edges with fine seed (h_core = 1.35 um)
    strip_face = p.faces.findAt(((0.75, 0.50, 0.0),))
    if strip_face:
        strip_edges = [p.edges[eid] for eid in strip_face[0].getEdges()]
        p.seedEdgeBySize(edges=strip_edges, size=h_core, deviationFactor=0.1, minSizeFactor=0.1)
        print("Seeded Straight Notch fracture strip edges (N=%d) with %.2f um" % (len(strip_edges), h_core * 1000.0))

    # Seed notch tip vertical edge: 1.0 um
    notch_edges = []
    for edge in p.edges:
        pt = edge.pointOn[0]
        if abs(pt[0] - notch_a) < 0.005 and abs(pt[1] - notch_y) < notch_w * 2.0:
            notch_edges.append(edge)
    if notch_edges:
        p.seedEdgeBySize(edges=notch_edges, size=0.0010, deviationFactor=0.1, minSizeFactor=0.1)

    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    elem_quad = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elem_tri = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=(p.faces,), elemTypes=(elem_quad, elem_tri))
    p.generateMesh()

    a = m.rootAssembly
    a.DatumCsysByDefault(CARTESIAN)
    inst = a.Instance(name="PLATE-1", part=p, dependent=ON)

    job_name = "F1666_STR_TEMP_EXPORT"
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]
    j = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
    j.writeInput(consistencyChecking=OFF)

    temp_inp = job_name + ".inp"
    nodes = {}
    quads = {}
    tris = {}
    in_nodes = in_elems = False
    with open(temp_inp, "r") as f:
        for line in f:
            l = line.strip()
            if not l: continue
            if l.startswith("*"):
                u = l.upper()
                if u.startswith("*NODE") and not "OUTPUT" in u and not "PRINT" in u:
                    in_nodes, in_elems = True, False
                elif u.startswith("*ELEMENT"):
                    in_nodes = False
                    in_elems = True
                else:
                    in_nodes = in_elems = False
                continue
            parts = [x.strip() for x in l.split(",") if x.strip()]
            if in_nodes and len(parts) >= 3:
                try: nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                except ValueError: pass
            elif in_elems and len(parts) >= 4:
                try:
                    int_p = [int(x) for x in parts]
                    eid = int_p[0]
                    conn = int_p[1:]
                    if len(conn) == 4: quads[eid] = tuple(conn)
                    elif len(conn) == 3: tris[eid] = tuple(conn)
                except ValueError: pass

    for ext in [".inp", ".log"]:
        if os.path.exists(job_name + ext):
            try: os.remove(job_name + ext)
            except: pass

    with open(out_inp, "w") as f:
        f.write("*HEADING\n")
        f.write("** PK_MODE1_F1666_HYBRID_ADAPT_PHYS: Straight Notch Hybrid Adapted Mesh\n")
        f.write("** Sizing Field: h_hybrid(x, y) = min(h_MISESERI, h_damage)\n")
        f.write("** Total physical elements: %d (%d quads, %d tris), Nodes: %d\n" % (
            len(quads) + len(tris), len(quads), len(tris), len(nodes)
        ))
        f.write("** ----------------------------------------------------------\n")
        f.write("*NODE\n")
        for nid in sorted(nodes.keys()):
            x, y = nodes[nid]
            f.write("%d, %.9e, %.9e\n" % (nid, x, y))
        if quads:
            f.write("*ELEMENT, TYPE=CPE4, ELSET=QUAD_ELEMS\n")
            for eid in sorted(quads.keys()):
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in quads[eid])))
        if tris:
            f.write("*ELEMENT, TYPE=CPE3, ELSET=TRI_ELEMS\n")
            for eid in sorted(tris.keys()):
                f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in tris[eid])))
        f.write("*ELSET, ELSET=All_elem\nQUAD_ELEMS\n")
        if tris: f.write("TRI_ELEMS\n")

    print("Successfully exported straight notch hybrid mesh: %s" % out_inp)
    print("  Total elements: %d (%.2f%% quads, %.2f%% tris), Nodes: %d" % (
        len(quads) + len(tris),
        100.0 * len(quads) / (len(quads) + len(tris)),
        100.0 * len(tris) / (len(quads) + len(tris)),
        len(nodes)
    ))
    return len(quads) + len(tris), len(nodes)


def main():
    hole_out = os.path.abspath("models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1666_HYBRID_ADAPT_PHYS.inp")
    str_out = os.path.abspath("models/pandey_kumar_mode1/01_standard_pfm_reference/PK_MODE1_F1666_HYBRID_ADAPT_PHYS.inp")

    if not (os.path.exists(hole_out) and os.path.getsize(hole_out) > 500000):
        generate_off_axis_hole_hybrid_mesh(hole_out, h_core=0.00135, h_hole=0.0015, h_bulk=0.020)
    else:
        print("PK_HOLE_F1666_HYBRID_ADAPT_PHYS.inp already exists (%d bytes). Skipping hole mesh generation." % os.path.getsize(hole_out))

    generate_straight_notch_hybrid_mesh(str_out, h_core=0.00135, h_bulk=0.020)

if __name__ == "__main__":
    main()

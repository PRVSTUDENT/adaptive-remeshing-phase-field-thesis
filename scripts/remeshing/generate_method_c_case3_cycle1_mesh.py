# -*- coding: utf-8 -*-
"""
scripts/remeshing/generate_method_c_case3_cycle1_mesh.py
=======================================================
Task: METHOD-C-CASE3-CYCLE1-REFINEMENT-PACKAGE
Generates the Method C Case 3 Cycle-1 adapted physical mesh (Abaqus CAE script):
- Benchmark: Pandey & Kumar (2025) Section 4.3 Rectangular Notched Plate with Hole and Pins
- Domain: 65.0 x 120.0 mm Mode-I rectangular plate with pin holes and central void
- Notch: Horizontal edge notch at y = 70.0 mm, length a = 10.0 mm, slit half-opening w = 0.2 mm
- Central void: Circular hole at (36.5, 51.0) mm, radius r = 10.0 mm
- Pin holes: Lower pin at (20.0, 20.0) mm, r = 5.0 mm; Upper pin at (20.0, 100.0) mm, r = 5.0 mm
- Refinement zone: Partition around notch root and advancing crack process zone:
    x in [8.5, 22.0] mm, y in [63.0, 77.0] mm
- Refined seed: h_ref = 0.140 mm (resolving l0 = 0.285 mm with h <= l0 / 2 = 0.1425 mm)
- Global background seed: h_bg = 2.00 mm (CPE4/CPE3 quad-dominated free mesh)
"""

from __future__ import print_function
import os
import sys
import math

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
framework_dir = os.path.join(REPO_ROOT, "scripts", "remeshing")
if framework_dir not in sys.path:
    sys.path.insert(0, framework_dir)

from abaqus import mdb
from abaqusConstants import *
import regionToolset
import part
import sketch
import mesh

OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "290_method_c_case3")
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

PHYS_INP = os.path.join(OUT_DIR, "PK_METHOD_C_CASE3_CYCLE1_PHYS.inp")

# 1. Model & Sketch
model_name = "METHOD_C_CASE3_CYCLE1"
if model_name in mdb.models:
    del mdb.models[model_name]
m = mdb.Model(name=model_name)

plate_w = 65.0
plate_h = 120.0
notch_a = 10.0
notch_y = 70.0
notch_w = 0.20  # half-width = 0.2 mm
central_hole_x = 36.5
central_hole_y = 51.0
central_hole_r = 10.0
lower_pin_x = 20.0
lower_pin_y = 20.0
lower_pin_r = 5.0
upper_pin_x = 20.0
upper_pin_y = 100.0
upper_pin_r = 5.0

h_bg = 2.00
h_ref = 0.140  # resolves l0/2 = 0.1425 mm

s = m.ConstrainedSketch(name="__profile__", sheetSize=250.0)

# Outer polygon with notch slit
outer_pts = [
    (0.0, 0.0),
    (plate_w, 0.0),
    (plate_w, plate_h),
    (0.0, plate_h),
    (0.0, notch_y + notch_w),
    (notch_a, notch_y + notch_w),
    (notch_a, notch_y - notch_w),
    (0.0, notch_y - notch_w)
]
for i in range(len(outer_pts)):
    s.Line(point1=outer_pts[i], point2=outer_pts[(i + 1) % len(outer_pts)])

# Holes
s.CircleByCenterPerimeter(center=(central_hole_x, central_hole_y), point1=(central_hole_x + central_hole_r, central_hole_y))
s.CircleByCenterPerimeter(center=(lower_pin_x, lower_pin_y), point1=(lower_pin_x + lower_pin_r, lower_pin_y))
s.CircleByCenterPerimeter(center=(upper_pin_x, upper_pin_y), point1=(upper_pin_x + upper_pin_r, upper_pin_y))

p = m.Part(name="Case3PlateCycle1Refined", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
p.BaseShell(sketch=s)
del m.sketches["__profile__"]

# 2. Partition Face for refined crack process zone
# Partition box: x in [8.5, 22.0], y in [63.0, 77.0]
# This encloses the blunt notch root at x = 10.0, y in [69.8, 70.2] and the forward process zone
x_ref_min = 8.5
x_ref_max = 22.0
y_ref_min = 63.0
y_ref_max = 77.0

sp = m.ConstrainedSketch(name="__partition__", sheetSize=250.0)
sp.rectangle(point1=(x_ref_min, y_ref_min), point2=(x_ref_max, y_ref_max))

p.PartitionFaceBySketch(faces=p.faces, sketch=sp)
del m.sketches["__partition__"]

# 3. Material & Section
mat = m.Material(name="Steel")
mat.Elastic(table=((210000.0, 0.3),))
m.HomogeneousSolidSection(name="SolidSec", material="Steel", thickness=1.0)
p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName="SolidSec")

# 4. Seeding: Background seed, then fine seed on refinement zone
p.seedPart(size=h_bg, deviationFactor=0.05, minSizeFactor=0.02)

# Identify faces in refinement zone
ref_faces = []
for f in p.faces:
    pt = f.pointOn[0]
    if (x_ref_min - 1e-3 <= pt[0] <= x_ref_max + 1e-3) and (y_ref_min - 1e-3 <= pt[1] <= y_ref_max + 1e-3):
        ref_faces.append(f)

print("Found %d face(s) in refinement zone" % len(ref_faces))

# Identify edges of refinement faces to seed with h_ref
ref_edges = []
edge_indices_seen = set()
for f in ref_faces:
    for e_idx in f.getEdges():
        if e_idx not in edge_indices_seen:
            edge_indices_seen.add(e_idx)
            ref_edges.append(p.edges[e_idx])

# Also identify blunt notch root edges
notch_edges = []
tol = 1e-3
for edge in p.edges:
    pt = edge.pointOn[0]
    if pt[0] <= notch_a + tol and (notch_y - notch_w - tol) <= pt[1] <= (notch_y + notch_w + tol):
        notch_edges.append(edge)

# Seed refinement edges
if ref_edges:
    p.seedEdgeBySize(edges=ref_edges, size=h_ref, deviationFactor=0.05, minSizeFactor=0.02, constraint=FINER)

# Seed notch root edges to ensure smooth quad layers across root
root_seed = min(h_ref, (2.0 * notch_w) / 4.0)
for se in notch_edges:
    try:
        p.seedEdgeBySize(edges=(se,), size=root_seed, deviationFactor=0.05, minSizeFactor=0.02, constraint=FREE)
    except Exception:
        pass

p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))
p.generateMesh()

# 5. Assembly & Job to generate INP
a = m.rootAssembly
inst = a.Instance(name="PART-1-1", part=p, dependent=ON)
job_name = "PK_METHOD_C_CASE3_CYCLE1_PHYS_TEMP"
if job_name in mdb.jobs:
    del mdb.jobs[job_name]
job = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
job.writeInput(consistencyChecking=OFF)

# 6. Clean and write standalone physical mesh
src_inp = job_name + ".inp"
if not os.path.exists(src_inp) and os.path.exists(os.path.join(REPO_ROOT, src_inp)):
    src_inp = os.path.join(REPO_ROOT, src_inp)

nodes = {}
quads = {}
tris = {}
in_nodes = False
in_elements = False
elem_type = None

with open(src_inp, "r") as f:
    for line in f:
        l = line.strip()
        if not l or l.startswith("**"):
            continue
        if l.startswith("*"):
            in_nodes = False
            in_elements = False
            u = l.upper()
            if u.startswith("*NODE"):
                in_nodes = True
            elif u.startswith("*ELEMENT"):
                in_elements = True
                if "CPE4" in u or "CPS4" in u or "QUAD" in u:
                    elem_type = "QUAD"
                elif "CPE3" in u or "CPS3" in u or "TRI" in u:
                    elem_type = "TRI"
                else:
                    elem_type = "UNKNOWN"
            continue

        parts_l = [pt.strip() for pt in l.split(",") if pt.strip()]
        if in_nodes and len(parts_l) >= 3:
            try:
                nid = int(parts_l[0])
                nodes[nid] = (float(parts_l[1]), float(parts_l[2]))
            except ValueError:
                pass
        elif in_elements and len(parts_l) >= 4:
            try:
                int_parts = [int(pt) for pt in parts_l]
                eid = int_parts[0]
                conn = int_parts[1:]
                if elem_type == "QUAD" or len(conn) == 4:
                    quads[eid] = tuple(conn[:4])
                else:
                    tris[eid] = tuple(conn[:3])
            except ValueError:
                pass

# Renumber deterministically: 1..num_quads for quads, num_quads+1..num_total for tris
renumbered_quads = {}
renumbered_tris = {}
new_eid = 1
for old_eid in sorted(quads.keys()):
    renumbered_quads[new_eid] = quads[old_eid]
    new_eid += 1
for old_eid in sorted(tris.keys()):
    renumbered_tris[new_eid] = tris[old_eid]
    new_eid += 1

total_elems = len(renumbered_quads) + len(renumbered_tris)
quad_pct = 100.0 * len(renumbered_quads) / total_elems if total_elems > 0 else 0.0

with open(PHYS_INP, "w") as f:
    f.write("** ==========================================================\n")
    f.write("** METHOD C CASE 3 PHYSICAL CYCLE-1 ADAPTED MESH (65x120 mm Plate)\n")
    f.write("** Benchmark: Pandey & Kumar (2025) Section 4.3\n")
    f.write("** Refinement: h_ref = %.3f mm (l0 = %.3f mm, l0/2 = %.4f mm)\n" % (h_ref, 0.285, 0.1425))
    f.write("** Physical elements: %d (Quads: %d [%.2f%%], Tris: %d), Nodes: %d\n" % (
        total_elems, len(renumbered_quads), quad_pct, len(renumbered_tris), len(nodes)
    ))
    f.write("** ==========================================================\n")
    f.write("*HEADING\n")
    f.write("Method C Case 3 Cycle-1 Adapted Physical Mesh\n")
    f.write("*NODE\n")
    for nid in sorted(nodes.keys()):
        x, y = nodes[nid]
        f.write("%d, %.9e, %.9e\n" % (nid, x, y))
    if renumbered_quads:
        f.write("*ELEMENT, TYPE=CPE4, ELSET=ALL_ELEM\n")
        for eid in sorted(renumbered_quads.keys()):
            f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in renumbered_quads[eid])))
    if renumbered_tris:
        f.write("*ELEMENT, TYPE=CPE3, ELSET=ALL_ELEM\n")
        for eid in sorted(renumbered_tris.keys()):
            f.write("%d, %s\n" % (eid, ", ".join(str(n) for n in renumbered_tris[eid])))

# Clean up temp files
if os.path.exists(src_inp):
    try:
        os.remove(src_inp)
    except Exception:
        pass

print("\nSUCCESS: Generated Case 3 Cycle-1 physical adapted mesh!")
print("  Elements: %d (%d quads [%.2f%%], %d tris)" % (total_elems, len(renumbered_quads), quad_pct, len(renumbered_tris)))
print("  Nodes:    %d" % len(nodes))
print("  Output:   %s" % PHYS_INP)

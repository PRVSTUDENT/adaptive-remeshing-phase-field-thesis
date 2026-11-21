# -*- coding: utf-8 -*-
"""
scripts/remeshing/generate_method_c_case3_cycle3_mesh.py
=======================================================
Task: METHOD-C-CASE3-CYCLE3-REFINEMENT-PACKAGE
Generates the Method C Case 3 Cycle-3 adapted physical mesh (Abaqus CAE script):
- Benchmark: Pandey & Kumar (2025) Section 4.3 Rectangular Notched Plate with Hole and Pins
- Domain: 65.0 x 120.0 mm Mode-I rectangular plate with pin holes and central void
- Notch: Horizontal edge notch at y = 70.0 mm, length a = 10.0 mm, slit half-opening w = 0.2 mm
- Central void: Circular hole at (36.5, 51.0) mm, radius r = 10.0 mm
- Pin holes: Lower pin at (20.0, 20.0) mm, r = 5.0 mm; Upper pin at (20.0, 100.0) mm, r = 5.0 mm
- Extended refinement zone: Partition covering notch wake, crack tip (d>=0.95 tip x=12.5215 mm),
  and forward crack corridor to the central hole perimeter at x = 26.5 mm and beyond along
  the crack trajectory toward hole center at (36.5, 51.0) mm:
    x in [8.5, 37.0] mm, y in [48.0, 77.0] mm
- Refined seed: h_ref = 0.140 mm (resolving l0 = 0.285 mm with h <= l0 / 2 = 0.1425 mm)
- Global background seed: h_bg = 2.00 mm (CPE4/CPE3 quad-dominated free mesh)
"""

from __future__ import print_function
import os
import sys
import math

from abaqus import mdb
from abaqusConstants import *
import regionToolset
import part
import sketch
import mesh

print("Generating candidate Case 3 Cycle 3 physical mesh...")
model_name = "METHOD_C_CASE3_CYCLE3"
if model_name in mdb.models:
    del mdb.models[model_name]
m = mdb.Model(name=model_name)

plate_w = 65.0
plate_h = 120.0
notch_a = 10.0
notch_y = 70.0
notch_w = 0.20
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

s.CircleByCenterPerimeter(center=(central_hole_x, central_hole_y), point1=(central_hole_x + central_hole_r, central_hole_y))
s.CircleByCenterPerimeter(center=(lower_pin_x, lower_pin_y), point1=(lower_pin_x + lower_pin_r, lower_pin_y))
s.CircleByCenterPerimeter(center=(upper_pin_x, upper_pin_y), point1=(upper_pin_x + upper_pin_r, upper_pin_y))

p = m.Part(name="Case3PlateCycle3Refined", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
p.BaseShell(sketch=s)
del m.sketches["__profile__"]

# Refinement partition: extends to x=37.0 (past central hole perimeter x=26.5 and center x=36.5), y in [48.0, 77.0]
x_ref_min = 8.5
x_ref_max = 37.0
y_ref_min = 48.0
y_ref_max = 77.0

sp = m.ConstrainedSketch(name="__partition__", sheetSize=250.0)
sp.rectangle(point1=(x_ref_min, y_ref_min), point2=(x_ref_max, y_ref_max))

p.PartitionFaceBySketch(faces=p.faces, sketch=sp)
del m.sketches["__partition__"]

# Material & Section
mat = m.Material(name="Steel")
mat.Elastic(table=((210000.0, 0.3),))
m.HomogeneousSolidSection(name="SolidSec", material="Steel", thickness=1.0)
p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName="SolidSec")

# Seeding
p.seedPart(size=h_bg, deviationFactor=0.05, minSizeFactor=0.02)

ref_faces = []
for f in p.faces:
    pt = f.pointOn[0]
    if (x_ref_min - 1e-3 <= pt[0] <= x_ref_max + 1e-3) and (y_ref_min - 1e-3 <= pt[1] <= y_ref_max + 1e-3):
        ref_faces.append(f)

print("Found %d face(s) in refinement zone" % len(ref_faces))

ref_edges = []
edge_indices_seen = set()
for f in ref_faces:
    for e_idx in f.getEdges():
        if e_idx not in edge_indices_seen:
            edge_indices_seen.add(e_idx)
            ref_edges.append(p.edges[e_idx])

notch_edges = []
tol = 1e-3
for edge in p.edges:
    pt = edge.pointOn[0]
    if pt[0] <= notch_a + tol and (notch_y - notch_w - tol) <= pt[1] <= (notch_y + notch_w + tol):
        notch_edges.append(edge)

if ref_edges:
    p.seedEdgeBySize(edges=ref_edges, size=h_ref, deviationFactor=0.05, minSizeFactor=0.02, constraint=FINER)

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

print("Generating mesh...")
p.generateMesh()

print("Mesh generated: %d nodes, %d elements" % (len(p.nodes), len(p.elements)))

# Assembly & Job to generate INP
a = m.rootAssembly
inst = a.Instance(name="PART-1-1", part=p, dependent=ON)
job_name = "PK_METHOD_C_CASE3_CYCLE3_PHYS_TEMP"
if job_name in mdb.jobs:
    del mdb.jobs[job_name]
job = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
job.writeInput(consistencyChecking=OFF)

src_inp = job_name + ".inp"
out_phys_inp = "PK_METHOD_C_CASE3_CYCLE3_PHYS.inp"

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
        if in_nodes:
            parts = [p.strip() for p in l.split(",") if p.strip()]
            if len(parts) >= 3:
                nid = int(parts[0])
                nodes[nid] = (float(parts[1]), float(parts[2]))
        elif in_elements:
            parts = [p.strip() for p in l.split(",") if p.strip()]
            if len(parts) >= 4:
                eid = int(parts[0])
                nids = [int(p) for p in parts[1:]]
                if elem_type == "QUAD" or len(nids) == 4:
                    quads[eid] = nids
                else:
                    tris[eid] = nids

print("Read %d nodes, %d quads, %d tris from temp INP" % (len(nodes), len(quads), len(tris)))
total_elements = len(quads) + len(tris)
quad_pct = 100.0 * float(len(quads)) / float(total_elements) if total_elements > 0 else 0.0
print("Total elements: %d (Quad fraction: %.2f%%)" % (total_elements, quad_pct))

# Re-index nodes and elements consecutively
node_map = {}
new_nodes = {}
for idx, (old_nid, coord) in enumerate(sorted(nodes.items(), key=lambda x: x[0]), start=1):
    node_map[old_nid] = idx
    new_nodes[idx] = coord

new_elements = {}
for idx, (old_eid, nids) in enumerate(sorted(quads.items(), key=lambda x: x[0]), start=1):
    new_elements[idx] = ("CPE4", [node_map[n] for n in nids])

start_tri = len(new_elements) + 1
for idx, (old_eid, nids) in enumerate(sorted(tris.items(), key=lambda x: x[0]), start=start_tri):
    new_elements[idx] = ("CPE3", [node_map[n] for n in nids])

with open(out_phys_inp, "w") as f:
    f.write("** ============================================================\n")
    f.write("** Method C Case 3 Cycle-3 Physical Mesh\n")
    f.write("** Benchmark: Pandey & Kumar (2025) Section 4.3 Plate with Hole\n")
    f.write("** Corridor: x in [%.1f, %.1f], y in [%.1f, %.1f]\n" % (x_ref_min, x_ref_max, y_ref_min, y_ref_max))
    f.write("** Sizing: h_ref = %.3f mm, h_bg = %.3f mm\n" % (h_ref, h_bg))
    f.write("** Statistics: %d nodes, %d elements (%d quads, %d tris, %.2f%% quad)\n" % (
        len(new_nodes), len(new_elements), len(quads), len(tris), quad_pct
    ))
    f.write("** ============================================================\n")
    f.write("*NODE\n")
    for nid in range(1, len(new_nodes) + 1):
        f.write("%d, %.8e, %.8e\n" % (nid, new_nodes[nid][0], new_nodes[nid][1]))

    f.write("*ELEMENT, TYPE=CPE4, ELSET=E_QUAD\n")
    for eid in range(1, len(quads) + 1):
        c = new_elements[eid][1]
        f.write("%d, %d, %d, %d, %d\n" % (eid, c[0], c[1], c[2], c[3]))

    if tris:
        f.write("*ELEMENT, TYPE=CPE3, ELSET=E_TRI\n")
        for eid in range(len(quads) + 1, len(new_elements) + 1):
            c = new_elements[eid][1]
            f.write("%d, %d, %d, %d\n" % (eid, c[0], c[1], c[2]))

    f.write("*ELSET, ELSET=ALL_ELEMENTS\n")
    f.write("E_QUAD,\n")
    if tris:
        f.write("E_TRI,\n")

print("Successfully written standalone physical mesh: %s" % out_phys_inp)

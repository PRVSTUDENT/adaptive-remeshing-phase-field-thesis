# -*- coding: utf-8 -*-
"""
scripts/remeshing/generate_method_c_demo_refined_mesh.py
=======================================================
Task: METHOD-C-PHASE2-TRANSFER-REEQUILIBRATION
Generates the Method C demonstration benchmark refined receiver physical mesh (Abaqus CAE script):
- Domain: 1.0 x 1.0 mm Mode-I square plate
- Notch: Horizontal edge notch at y = 0.5 mm, from x = 0.0 to x = 0.5 mm (a = 0.5 mm)
- Void: Symmetrical circular hole centered on crack line at (0.75, 0.50) mm, r = 0.10 mm
- Refinement zone: Crack tip process zone (x in [0.42, 0.65], y in [0.42, 0.58])
- Refined seed: h_ref = 0.0035 mm (resolving l0 = 0.0075 mm with h <= l0 / 2)
- Global background seed: h_bg = 0.020 mm (CPE4/CPE3 quad-dominated free mesh)
"""

from abaqus import *
from abaqusConstants import *
import regionToolset
import part
import sketch
import mesh
import os
import sys

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "289_method_c_demo_case")
if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

PHYS_INP = os.path.join(OUT_DIR, "PK_METHOD_C_DEMO_REFINED_STEP1_PHYS.inp")

# 1. Model & Sketch
model_name = "METHOD_C_DEMO_REFINED"
if model_name in mdb.models:
    del mdb.models[model_name]
m = mdb.Model(name=model_name)

plate_w = 1.0
plate_h = 1.0
notch_a = 0.5
notch_y = 0.5
notch_w = 0.001
hole_x = 0.75
hole_y = 0.50
hole_r = 0.10
h_bg = 0.020
h_ref = 0.0035

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

p = m.Part(name="DemoPlateWithHoleRefined", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
p.BaseShell(sketch=s)
del m.sketches["__profile__"]

# 2. Partition Face to create refined process zone
# Box around crack tip and ligament: x in [0.42, 0.65], y in [0.42, 0.58]
x_ref_min = 0.42
x_ref_max = 0.65
y_ref_min = 0.42
y_ref_max = 0.58

sp = m.ConstrainedSketch(name="__partition__", sheetSize=2.0)
sp.rectangle(point1=(x_ref_min, y_ref_min), point2=(x_ref_max, y_ref_max))

p.PartitionFaceBySketch(faces=p.faces, sketch=sp)
del m.sketches["__partition__"]

# 3. Material & Section (for physical mesh export)
mat = m.Material(name="Steel")
mat.Elastic(table=((210000.0, 0.3),))
m.HomogeneousSolidSection(name="SolidSec", material="Steel", thickness=1.0)
p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName="SolidSec")

# 4. Seeding: global background seed, then local fine seed on process zone faces
p.seedPart(size=h_bg, deviationFactor=0.1, minSizeFactor=0.1)

# Identify faces inside the refinement box
ref_faces = []
for f in p.faces:
    pt = f.pointOn[0]
    if (x_ref_min - 1e-4 <= pt[0] <= x_ref_max + 1e-4) and (y_ref_min - 1e-4 <= pt[1] <= y_ref_max + 1e-4):
        ref_faces.append(f)

print("Found %d face(s) in refinement zone" % len(ref_faces))
if ref_faces:
    # Seed edges of the refinement zone with fine size
    ref_edges = []
    for f in ref_faces:
        for e in f.getEdges():
            ref_edges.append(p.edges[e])
    p.seedEdgeBySize(edges=ref_edges, size=h_ref, deviationFactor=0.1, minSizeFactor=0.1, constraint=FINER)

p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))
p.generateMesh()

# 5. Assembly & Job to generate INP
a = m.rootAssembly
inst = a.Instance(name="PART-1-1", part=p, dependent=ON)
job = mdb.Job(name="PK_METHOD_C_DEMO_REFINED_STEP1_PHYS", model=model_name, type=ANALYSIS)
job.writeInput(consistencyChecking=OFF)

# Move generated job input deck to OUT_DIR/PK_METHOD_C_DEMO_REFINED_STEP1_PHYS.inp
src_inp = "PK_METHOD_C_DEMO_REFINED_STEP1_PHYS.inp"
if os.path.exists(src_inp):
    if os.path.exists(PHYS_INP):
        os.remove(PHYS_INP)
    os.rename(src_inp, PHYS_INP)

num_quads = sum([1 for e in p.elements if len(e.connectivity) == 4])
num_tris = sum([1 for e in p.elements if len(e.connectivity) == 3])
num_elems = len(p.elements)
num_nodes = len(p.nodes)

print("GENERATED REFINED PHYSICAL MESH:")
print("  Elements: %d (%d quads [%.2f%%], %d tris)" % (
    num_elems, num_quads, 100.0 * num_quads / num_elems, num_tris
))
print("  Nodes:    %d" % num_nodes)
print("  Output:   %s" % PHYS_INP)

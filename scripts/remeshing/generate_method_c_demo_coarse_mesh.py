# -*- coding: utf-8 -*-
"""
scripts/remeshing/generate_method_c_demo_coarse_mesh.py
======================================================
Task: METHOD-C-PHASE1-DEMO-AND-LOOP-SKELETON
Generates the Method C demonstration benchmark physical mesh (Abaqus CAE script):
- Domain: 1.0 x 1.0 mm Mode-I square plate
- Notch: Horizontal edge notch at y = 0.5 mm, from x = 0.0 to x = 0.5 mm (a = 0.5 mm)
- Void: Symmetrical circular hole centered on crack line at (0.75, 0.50) mm, r = 0.10 mm
- Ligaments: Inter-feature ligament = 0.15 mm (x in [0.5, 0.65]), rear ligament = 0.15 mm (x in [0.85, 1.0])
- Global coarse seed: h0 = 0.020 mm (CPE4/CPE3 quad-dominated free mesh)
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

PHYS_INP = os.path.join(OUT_DIR, "PK_METHOD_C_DEMO_COARSE_PHYS.inp")

# 1. Model & Sketch
model_name = "METHOD_C_DEMO_COARSE"
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
coarse_h = 0.020

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

p = m.Part(name="DemoPlateWithHole", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
p.BaseShell(sketch=s)
del m.sketches["__profile__"]

# 2. Material & Section (for physical mesh export)
mat = m.Material(name="Steel")
mat.Elastic(table=((210000.0, 0.3),))
m.HomogeneousSolidSection(name="SolidSec", material="Steel", thickness=1.0)
p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName="SolidSec")

# 3. Seeding & Meshing
p.seedPart(size=coarse_h, deviationFactor=0.1, minSizeFactor=0.1)
p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))
p.generateMesh()

# 4. Assembly & Job to generate INP
a = m.rootAssembly
inst = a.Instance(name="PART-1-1", part=p, dependent=ON)
job = mdb.Job(name="PK_METHOD_C_DEMO_COARSE_PHYS", model=model_name, type=ANALYSIS)
job.writeInput(consistencyChecking=OFF)

# Move generated job input deck to OUT_DIR/PK_METHOD_C_DEMO_COARSE_PHYS.inp
src_inp = "PK_METHOD_C_DEMO_COARSE_PHYS.inp"
if os.path.exists(src_inp):
    if os.path.exists(PHYS_INP):
        os.remove(PHYS_INP)
    os.rename(src_inp, PHYS_INP)

num_quads = sum([1 for e in p.elements if len(e.connectivity) == 4])
num_tris = sum([1 for e in p.elements if len(e.connectivity) == 3])
num_elems = len(p.elements)
num_nodes = len(p.nodes)

print("GENERATED PHYSICAL MESH:")
print("  Elements: %d (%d quads [%.2f%%], %d tris)" % (
    num_elems, num_quads, 100.0 * num_quads / num_elems, num_tris
))
print("  Nodes:    %d" % num_nodes)
print("  Output:   %s" % PHYS_INP)

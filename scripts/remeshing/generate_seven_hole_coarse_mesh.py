# -*- coding: utf-8 -*-
"""
scripts/remeshing/generate_seven_hole_coarse_mesh.py
===================================================
Generates the Seven-Hole Plate geometry and coarse physical mesh
(global seed 0.020 mm) using Abaqus CAE, matching Pandey & Kumar (2025) Section 4.6.
"""

from abaqus import *
from abaqusConstants import *
import regionToolset
import mesh
import os
import sys

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study")

if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

# 1. Create Model
model_name = "SevenHole_Coarse"
if model_name in mdb.models:
    del mdb.models[model_name]
m = mdb.Model(name=model_name)

# 2. Sketch outer 1.0 x 1.0 mm plate
s = m.ConstrainedSketch(name='__profile__', sheetSize=2.0)
s.Line(point1=(0.0, 0.0), point2=(1.0, 0.0))
s.Line(point1=(1.0, 0.0), point2=(1.0, 1.0))
s.Line(point1=(1.0, 1.0), point2=(0.0, 1.0))
s.Line(point1=(0.0, 1.0), point2=(0.0, 0.0))

# 3. Add 7 circular holes from Table 6 of Pandey & Kumar (2025)
# h1: (0.15, 0.40), r=0.10
s.CircleByCenterPerimeter(center=(0.15, 0.40), point1=(0.25, 0.40))
# h2: (0.50, 0.55), r=0.10
s.CircleByCenterPerimeter(center=(0.50, 0.55), point1=(0.60, 0.55))
# h3: (0.85, 0.50), r=0.10
s.CircleByCenterPerimeter(center=(0.85, 0.50), point1=(0.95, 0.50))
# h4: (0.30, 0.60), r=0.05
s.CircleByCenterPerimeter(center=(0.30, 0.60), point1=(0.35, 0.60))
# h5: (0.70, 0.60), r=0.05
s.CircleByCenterPerimeter(center=(0.70, 0.60), point1=(0.75, 0.60))
# h6: (0.40, 0.35), r=0.05
s.CircleByCenterPerimeter(center=(0.40, 0.35), point1=(0.45, 0.35))
# h7: (0.65, 0.35), r=0.05
s.CircleByCenterPerimeter(center=(0.65, 0.35), point1=(0.70, 0.35))

# 4. Create Part
p = m.Part(name='SevenHolePlate', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
p.BaseShell(sketch=s)
del m.sketches['__profile__']

# 5. Material & Section
mat = m.Material(name='Steel')
mat.Elastic(table=((210000.0, 0.3), ))
m.HomogeneousSolidSection(name='SolidSec', material='Steel', thickness=1.0)
p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName='SolidSec')

# 6. Mesh Controls & Seeding (0.020 mm coarse seed)
seed_size = 0.020
p.seedPart(size=seed_size, deviationFactor=0.1, minSizeFactor=0.1)
p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))
p.generateMesh()

# 7. Assembly & Sets
a = m.rootAssembly
inst = a.Instance(name='PART-1-1', part=p, dependent=ON)
p.Set(name='ALL_ELEM', faces=p.faces)
a.Set(name='ALL_ELEM', faces=inst.faces)

# Boundary edge sets
tol = 1e-4
bot_edges = inst.edges.findAt(((0.5, 0.0, 0.0),))
top_edges = inst.edges.findAt(((0.5, 1.0, 0.0),))
a.Set(name='BOTTOM_EDGE', edges=bot_edges)
a.Set(name='TOP_EDGE', edges=top_edges)

# Write physical mesh INP
phys_inp_path = os.path.join(OUT_DIR, "PK_F1726_SEVEN_HOLE_COARSE_PHYS.inp")
job_phys = mdb.Job(name='PK_F1726_SEVEN_HOLE_COARSE_PHYS', model=m, type=ANALYSIS)
job_phys.writeInput(consistencyChecking=OFF)

# Move generated inp from current working dir to OUT_DIR if needed
cwd_inp = "PK_F1726_SEVEN_HOLE_COARSE_PHYS.inp"
if os.path.exists(cwd_inp) and os.path.abspath(cwd_inp) != os.path.abspath(phys_inp_path):
    if os.path.exists(phys_inp_path):
        os.remove(phys_inp_path)
    os.rename(cwd_inp, phys_inp_path)

print("SUCCESS: Generated Seven-Hole coarse physical mesh at %s" % phys_inp_path)
n_quads = len([e for e in p.elements if len(e.connectivity) == 4])
n_tris = len([e for e in p.elements if len(e.connectivity) == 3])
print("Elements: %d (Quads: %d, Tris: %d), Nodes: %d" % (
    len(p.elements), n_quads, n_tris, len(p.nodes)
))

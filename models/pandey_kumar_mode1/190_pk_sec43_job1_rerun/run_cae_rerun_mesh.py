# -*- coding: mbcs -*-
from abaqus import *
from abaqusConstants import *
import mesh
import os

model_name = 'PK_SEC43_RERUN'
if model_name in mdb.models:
    del mdb.models[model_name]
m = mdb.Model(name=model_name)

# 1. Sketch profile with outer boundary, notch, and 3 holes
s = m.ConstrainedSketch(name='__profile__', sheetSize=300.0)

# Outer boundary and notch
s.Line(point1=(0.0, 0.0), point2=(65.0, 0.0))
s.Line(point1=(65.0, 0.0), point2=(65.0, 120.0))
s.Line(point1=(65.0, 120.0), point2=(0.0, 120.0))
s.Line(point1=(0.0, 120.0), point2=(0.0, 70.2))
s.Line(point1=(0.0, 70.2), point2=(10.0, 70.2))
s.Line(point1=(10.0, 70.2), point2=(10.0, 69.8))
s.Line(point1=(10.0, 69.8), point2=(0.0, 69.8))
s.Line(point1=(0.0, 69.8), point2=(0.0, 0.0))

# 3 Holes:
# Central eccentric void (Circle 1): center (36.5, 51.0), R = 10.0 mm
s.CircleByCenterPerimeter(center=(36.5, 51.0), point1=(46.5, 51.0))

# Lower pinned hole (Circle 2): center (20.0, 20.0), R = 5.0 mm
s.CircleByCenterPerimeter(center=(20.0, 20.0), point1=(25.0, 20.0))

# Upper loading hole (Circle 3): center (20.0, 100.0), R = 5.0 mm
s.CircleByCenterPerimeter(center=(20.0, 100.0), point1=(25.0, 100.0))

# 2. Create 2D Planar Part
p = m.Part(name='PlateWithHoles', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
p.BaseShell(sketch=s)
del m.sketches['__profile__']

# 3. Mesh controls and seeding (Option 2: Finer Coarse Mesh h = 0.60 mm)
p.seedPart(size=0.6, deviationFactor=0.1, minSizeFactor=0.1)
p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)

# Set element type to CPE4 / CPE3 (plane strain)
elem_type_quad = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
elem_type_tri = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
p.setElementType(regions=(p.faces,), elemTypes=(elem_type_quad, elem_type_tri))

# 4. Generate Mesh
p.generateMesh()

print('Mesh generation complete:')
print('Total Elements:', len(p.elements))
print('Total Nodes:', len(p.nodes))

# 5. Create Assembly and Job to export physical INP
a = m.rootAssembly
a.DatumCsysByDefault(CARTESIAN)
inst = a.Instance(name='PlateWithHoles-1', part=p, dependent=ON)

job = mdb.Job(name='PK_SEC43_RERUN_PHYS', model=model_name, type=ANALYSIS)
job.writeInput(consistencyChecking=OFF)
print('Wrote PK_SEC43_RERUN_PHYS.inp successfully.')

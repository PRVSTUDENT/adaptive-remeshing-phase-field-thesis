# -*- coding: utf-8 -*-
"""
test_five_hole_cad.py
Test CAD sketching and mesh generation for Pandey & Kumar (2025) Section 4.5 Five-Hole plate.
"""
from __future__ import print_function
import os
import sys

from abaqus import *
from abaqusConstants import *
import regionToolset
import part
import material
import section
import assembly
import step
import interaction
import load
import mesh
import job
import sketch

def test_cad():
    model_name = "PK_FIVE_HOLE_TEST"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)

    s = m.ConstrainedSketch(name='__profile__', sheetSize=2.0)

    # Outer boundary trace (counterclockwise)
    # Bottom edge: (0, 0) to (1, 0)
    s.Line(point1=(0.0, 0.0), point2=(1.0, 0.0))

    # Right edge lower segment: (1, 0) to (1, 0.375)
    s.Line(point1=(1.0, 0.0), point2=(1.0, 0.375))

    # Hole h5 arc (semi-circle curving into domain to x=0.925):
    # start: (1.0, 0.375), point on arc: (0.925, 0.45), end: (1.0, 0.525)
    s.Arc3Points(point1=(1.0, 0.375), point2=(1.0, 0.525), point3=(0.925, 0.45))

    # Right edge upper segment: (1, 0.525) to (1, 1)
    s.Line(point1=(1.0, 0.525), point2=(1.0, 1.0))

    # Top edge: (1, 1) to (0, 1)
    s.Line(point1=(1.0, 1.0), point2=(0.0, 1.0))

    # Left edge upper segment: (0, 1) to (0, 0.60)
    s.Line(point1=(0.0, 1.0), point2=(0.0, 0.60))

    # Hole h1 arc (semi-circle curving into domain to x=0.10):
    # start: (0.0, 0.60), point on arc: (0.10, 0.50), end: (0.0, 0.40)
    s.Arc3Points(point1=(0.0, 0.60), point2=(0.0, 0.40), point3=(0.10, 0.50))

    # Left edge lower segment: (0, 0.40) to (0, 0)
    s.Line(point1=(0.0, 0.40), point2=(0.0, 0.0))

    # Three interior circular holes
    # h2: centre (0.35, 0.45), radius 0.10
    s.CircleByCenterPerimeter(center=(0.35, 0.45), point1=(0.45, 0.45))

    # h3: centre (0.60, 0.55), radius 0.05
    s.CircleByCenterPerimeter(center=(0.60, 0.55), point1=(0.65, 0.55))

    # h4: centre (0.75, 0.50), radius 0.075
    s.CircleByCenterPerimeter(center=(0.75, 0.50), point1=(0.825, 0.50))

    # Create part
    p = m.Part(name='FiveHolePlate', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches['__profile__']

    # Material
    mat = m.Material(name='Steel')
    mat.Elastic(table=((210000.0, 0.3), ))
    m.HomogeneousSolidSection(name='SolidSec', material='Steel', thickness=1.0)
    p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName='SolidSec')

    # Seed with coarse size h = 0.02 mm
    coarse_h = 0.02
    p.seedPart(size=coarse_h, deviationFactor=0.1, minSizeFactor=0.1)
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))
    p.generateMesh()

    n_nodes = len(p.nodes)
    n_elems = len(p.elements)
    print("SUCCESS: Generated mesh with %d elements and %d nodes!" % (n_elems, n_nodes))

if __name__ == "__main__":
    test_cad()

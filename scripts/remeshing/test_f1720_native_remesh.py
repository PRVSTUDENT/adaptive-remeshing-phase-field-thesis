# -*- coding: utf-8 -*-
"""
Quick test of native adaptiveRemesh() directly on PK_F1720_COARSE_COUPLED.odb.
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
import mesh
import job
import sketch


REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
COUPLED_ODB = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "213_f1720_coarse_coupled", "PK_F1720_COARSE_COUPLED.odb")

def test_remesh():
    m = mdb.Model(name='TEST_REMESH')
    
    # Build CAD
    s = m.ConstrainedSketch(name='__profile__', sheetSize=2.0)
    s.Line(point1=(0.0, 0.0), point2=(1.0, 0.0))
    s.Line(point1=(1.0, 0.0), point2=(1.0, 0.375))
    s.Arc3Points(point1=(1.0, 0.375), point2=(1.0, 0.525), point3=(0.925, 0.450))
    s.Line(point1=(1.0, 0.525), point2=(1.0, 1.0))
    s.Line(point1=(1.0, 1.0), point2=(0.0, 1.0))
    s.Line(point1=(0.0, 1.0), point2=(0.0, 0.60))
    s.Arc3Points(point1=(0.0, 0.600), point2=(0.0, 0.400), point3=(0.100, 0.500))
    s.Line(point1=(0.0, 0.400), point2=(0.0, 0.0))

    s.CircleByCenterPerimeter(center=(0.35, 0.45), point1=(0.45, 0.45))
    s.CircleByCenterPerimeter(center=(0.60, 0.55), point1=(0.65, 0.55))
    s.CircleByCenterPerimeter(center=(0.75, 0.50), point1=(0.825, 0.50))

    p = m.Part(name='FiveHolePlate', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches['__profile__']

    mat = m.Material(name='Steel')
    mat.Elastic(table=((210000.0, 0.3), ))
    m.HomogeneousSolidSection(name='SolidSec', material='Steel', thickness=1.0)
    p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName='SolidSec')

    p.seedPart(size=0.02, deviationFactor=0.1, minSizeFactor=0.1)
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))
    p.generateMesh()

    p.Set(name='ALL_ELEM', faces=p.faces)
    a = m.rootAssembly
    inst = a.Instance(name='PART-1-1', part=p, dependent=ON)
    a.Set(name='ALL_ELEM', faces=inst.faces)

    m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0)

    reg_all = inst.sets['ALL_ELEM']
    m.RemeshingRule(
        name='RR_TEST',
        stepName='Step-1',
        region=reg_all,
        variables=('MISESERI',),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=3.05,
        specifyMinSize=True,
        specifyMaxSize=True,
        minElementSize=0.001,
        maxElementSize=0.020,
        elementCountLimit=None,
        coarseningFactor=NOT_ALLOWED,
        refinementFactor=10
    )

    print("Opening ODB: %s" % COUPLED_ODB)
    odb_donor = session.openOdb(name=COUPLED_ODB)
    print("Calling m.adaptiveRemesh(odb=odb_donor)...")
    try:
        m.adaptiveRemesh(odb=odb_donor)
        print("SUCCESS! Remeshed elements: %d, nodes: %d" % (len(p.elements), len(p.nodes)))
    except Exception as e:
        print("EXCEPTION in adaptiveRemesh: %s" % str(e))
    finally:
        odb_donor.close()

if __name__ == "__main__":
    test_remesh()

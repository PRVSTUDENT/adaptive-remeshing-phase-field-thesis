# -*- coding: utf-8 -*-
"""
calibrate_five_hole_target.py
Find the exact errorTarget that matches the published 12,944 elements
for the Five-Hole benchmark (Pandey & Kumar 2025 Section 4.5).
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
import odbAccess

def build_base_model(model_name):
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)

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

    coarse_h = 0.02
    p.seedPart(size=coarse_h, deviationFactor=0.1, minSizeFactor=0.1)
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))
    p.generateMesh()

    a = m.rootAssembly
    inst = a.Instance(name='FiveHolePlate-1', part=p, dependent=ON)

    m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0, nlgeom=OFF)
    reg_all = regionToolset.Region(faces=inst.faces)
    a.Set(name='All_elem', faces=inst.faces)

    m.RemeshingRule(
        name='RR: 1',
        stepName='Step-1',
        region=reg_all,
        description='Five-Hole Remeshing Rule',
        outputFrequency=LAST_INCREMENT,
        variables=('MISESERI', ),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=1.85,
        specifyMinSize=True,
        specifyMaxSize=True,
        minElementSize=0.001,
        maxElementSize=0.020,
        elementCountLimit=None,
        coarseningFactor=NOT_ALLOWED,
        refinementFactor=10
    )
    return m

def calibrate():
    work_dir = os.path.abspath(os.path.dirname(__file__)) if '__file__' in globals() else os.getcwd()
    os.chdir(work_dir)
    odb_path = os.path.abspath("PK_F1714_JOB1_COARSE.odb")
    
    targets = [2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0]
    
    for err in targets:
        mname = "CALIB_ERR_%d" % int(round(err * 10))
        m = build_base_model(mname)
        m.remeshingRules['RR: 1'].setValues(errorTarget=err)
        
        o = odbAccess.openOdb(path=odb_path, readOnly=True)
        m.adaptiveRemesh(odb=o)
        o.close()
        
        p = m.parts['FiveHolePlate']
        n_elems = len(p.elements)
        n_nodes = len(p.nodes)
        diff_pct = 100.0 * (n_elems - 12944) / 12944.0
        print("RESULT: errorTarget = %.1f%% -> %d elements, %d nodes (parity: %+.2f%%)" % (
            err, n_elems, n_nodes, diff_pct
        ))

if __name__ == "__main__":
    calibrate()

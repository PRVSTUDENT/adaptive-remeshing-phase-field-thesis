# -*- coding: utf-8 -*-
from __future__ import print_function
import sys
import os
import math
import json
import hashlib

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
import visualization
import odbAccess

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def main():
    work_dir = os.getcwd()
    model_name = "ModeII_Native_Model"
    preanalysis_odb_path = "ModeII_MISESERI_preanalysis.odb"
    
    print("=== STARTING MODE-II NATIVE ADAPTIVE REMESHING (errorTarget=5.0) ===")
    print("Work directory:", work_dir)
    print("Pre-analysis ODB:", preanalysis_odb_path)
    
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)
    
    w = 0.0005 # 0.5 um slit half-width
    
    # 1. Geometric Sketch matching Part-1 of ModeII_MISESERI_preanalysis
    s = m.ConstrainedSketch(name='__profile__', sheetSize=2.0)
    s.Line(point1=(-0.5, -0.5), point2=(0.5, -0.5))
    s.Line(point1=(0.5, -0.5), point2=(0.5, 0.5))
    s.Line(point1=(0.5, 0.5), point2=(-0.5, 0.5))
    s.Line(point1=(-0.5, 0.5), point2=(-0.5, w))
    s.Line(point1=(-0.5, w), point2=(0.0, w))
    s.Line(point1=(0.0, w), point2=(0.0, -w))
    s.Line(point1=(0.0, -w), point2=(-0.5, -w))
    s.Line(point1=(-0.5, -w), point2=(-0.5, -0.5))
    
    p = m.Part(name='Part-1', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches['__profile__']
    
    # Material & Section (Plane Strain CPE4/CPE3)
    mat = m.Material(name='Elastic_Matrix')
    mat.Elastic(table=((210.0, 0.3), ))
    m.HomogeneousSolidSection(name='SolidSec', material='Elastic_Matrix', thickness=1.0)
    
    # Part set All_elem
    p.Set(name='All_elem', faces=p.faces)
    p.SectionAssignment(region=p.sets['All_elem'], sectionName='SolidSec')
    
    # Seed Part with coarse size h = 0.02 mm
    p.seedPart(size=0.02, deviationFactor=0.1, minSizeFactor=0.1)
    
    # Element controls: allow CPE4 quads and CPE3 triangles
    elemTypeQuad = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elemTypeTri = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=p.sets['All_elem'], elemTypes=(elemTypeQuad, elemTypeTri))
    p.generateMesh()
    
    coarse_nodes = len(p.nodes)
    coarse_elems = len(p.elements)
    print("Geometric Part-1 Coarse Mesh: %d elements, %d nodes" % (coarse_elems, coarse_nodes))
    
    # Root Assembly & Instance named Part-1-1
    a = m.rootAssembly
    inst = a.Instance(name='Part-1-1', part=p, dependent=ON)
    
    # Step for RemeshingRule
    m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0, initialInc=0.1, minInc=1e-5, maxInc=0.1, nlgeom=OFF)
    
    # Remeshing Rule matching Pandey & Kumar (2025) on inst.sets['All_elem']
    reg = inst.sets['All_elem']
    m.fieldOutputRequests['F-Output-1'].setValues(
        variables=('S', 'U', 'RF', 'MISESERI', 'MISESAVG', 'EVOL'),
        region=reg
    )
    
    # Boundary Conditions
    bottom_edges = inst.edges.findAt(((0.0, -0.5, 0.0), ))
    a.Set(name='bottom', edges=bottom_edges)
    m.DisplacementBC(name='FixBottom', createStepName='Step-1', region=a.sets['bottom'], u1=0.0, u2=0.0)
    
    top_edges = inst.edges.findAt(((0.0, 0.5, 0.0), ))
    a.Set(name='top', edges=top_edges)
    m.DisplacementBC(name='ShearTop', createStepName='Step-1', region=a.sets['top'], u1=0.001)
    
    m.RemeshingRule(
        name='ModeII_RR',
        stepName='Step-1',
        region=reg,
        description='Publication-adopted Mode-II Remeshing Rule from Pandey & Kumar (2025)',
        outputFrequency=ALL_INCREMENTS,
        variables=('MISESERI', ),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=5.0,
        specifyMinSize=True,
        specifyMaxSize=True,
        minElementSize=0.003,
        maxElementSize=0.020,
        elementCountLimit=None,
        coarseningFactor=NOT_ALLOWED,
        refinementFactor=10
    )
    print("Created RemeshingRule 'ModeII_RR' with errorTarget=5.0, refinementFactor=10, minElementSize=0.003, maxElementSize=0.020")
    
    # Open pre-analysis ODB and execute adaptiveRemesh
    print("Opening pre-analysis ODB: %s" % preanalysis_odb_path)
    o1 = odbAccess.openOdb(path=preanalysis_odb_path, readOnly=True)
    
    print("Calling m.adaptiveRemesh(odb=o1)...")
    m.adaptiveRemesh(odb=o1)
    o1.close()
    print("adaptiveRemesh executed successfully!")
    
    refined_nodes = len(p.nodes)
    refined_elems = len(p.elements)
    print("Refined Mesh Generated: %d elements, %d nodes" % (refined_elems, refined_nodes))
    
    # Export raw refined input deck
    raw_job_name = "ModeII_Adaptive_Raw"
    j_raw = mdb.Job(name=raw_job_name, model=model_name, description='Raw Native Refined Mode-II Model errorTarget=5.0')
    j_raw.writeInput(consistencyChecking=OFF)
    raw_inp = raw_job_name + ".inp"
    print("Wrote raw refined deck: %s (size: %d bytes)" % (raw_inp, os.path.getsize(raw_inp)))

if __name__ == "__main__":
    main()

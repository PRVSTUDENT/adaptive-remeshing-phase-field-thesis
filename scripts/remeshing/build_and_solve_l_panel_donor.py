# -*- coding: utf-8 -*-
"""
scripts/remeshing/build_and_solve_l_panel_donor.py
==================================================
Builds the initial coarse mesh and runs a local linear-elastic Abaqus/Standard
solve to generate an authentic native donor ODB with native stress recovery error
(MISESERI / MISESAVG) for the unfamiliar L-shaped panel benchmark.
"""

from __future__ import print_function
import os
import subprocess
import shutil

from abaqus import mdb, session
from abaqusConstants import *
import regionToolset
import mesh

def build_coarse_l_panel():
    out_dir = r"models\pandey_kumar_mode1\276_f1846_generalized_framework\l_panel"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    job_name = "PK_F1846_LPANEL_COARSE"
    model_name = "Model_LPanel_Coarse"

    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)
    if "Model-1" in mdb.models:
        del mdb.models["Model-1"]

    # 1. Sketch L-shaped polygon: [(0,0), (100,0), (100,50), (50,50), (50,100), (0,100)]
    s = m.ConstrainedSketch(name='__profile__', sheetSize=250.0)
    pts = [
        (0.0, 0.0),
        (100.0, 0.0),
        (100.0, 50.0),
        (50.0, 50.0),
        (50.0, 100.0),
        (0.0, 100.0)
    ]
    for i in range(len(pts)):
        s.Line(point1=pts[i], point2=pts[(i+1)%len(pts)])

    p = m.Part(name='PART-1', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches['__profile__']

    # 2. Material & Section
    mat = m.Material(name='Steel')
    mat.Elastic(table=((210000.0, 0.3), ))
    m.HomogeneousSolidSection(name='SolidSec', material='Steel', thickness=1.0)
    p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName='SolidSec')

    # 3. Coarse mesh: seed size 5.0 mm
    p.seedPart(size=5.0, deviationFactor=0.1, minSizeFactor=0.1)
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))
    p.generateMesh()

    p.Set(name='ALL_ELEM', faces=p.faces)
    a = m.rootAssembly
    inst = a.Instance(name='PART-1-1', part=p, dependent=ON)
    a.Set(name='ALL_ELEM', faces=inst.faces)

    # 4. Step
    m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0)

    # 5. Boundary conditions
    bottom_edges = inst.edges.findAt(((50.0, 0.0, 0.0), ))
    m.DisplacementBC(name='BC_Bottom', createStepName='Step-1',
                     region=regionToolset.Region(edges=bottom_edges),
                     u1=0.0, u2=0.0)

    top_edges = inst.edges.findAt(((25.0, 100.0, 0.0), ))
    m.DisplacementBC(name='BC_Top', createStepName='Step-1',
                     region=regionToolset.Region(edges=top_edges),
                     u1=0.0, u2=0.1)

    # 6. Write base input file
    j = mdb.Job(name=job_name, model=m.name, type=ANALYSIS)
    j.writeInput(consistencyChecking=OFF)

    raw_inp = job_name + ".inp"
    target_inp = os.path.join(out_dir, job_name + ".inp")

    # Read written INP and ensure *ELEMENT OUTPUT includes MISESERI, MISESAVG, EVOL
    lines = []
    with open(raw_inp, "r") as f:
        for line in f:
            lines.append(line)

    # Insert element output request if not present
    new_lines = []
    in_step = False
    output_added = False
    for line in lines:
        upline = line.upper().strip()
        if upline.startswith("*STEP"):
            in_step = True
        if upline.startswith("*END STEP") and not output_added:
            new_lines.append("*OUTPUT, FIELD\n")
            new_lines.append("*ELEMENT OUTPUT\n")
            new_lines.append("MISESERI, MISESAVG, EVOL, S, E\n")
            new_lines.append("*NODE OUTPUT\n")
            new_lines.append("U, RF\n")
            output_added = True
        new_lines.append(line)

    with open(target_inp, "w") as f:
        f.writelines(new_lines)

    if os.path.exists(raw_inp):
        os.remove(raw_inp)

    print("Successfully built coarse L-panel input deck: %s" % target_inp)
    return target_inp

if __name__ == '__main__':
    build_coarse_l_panel()

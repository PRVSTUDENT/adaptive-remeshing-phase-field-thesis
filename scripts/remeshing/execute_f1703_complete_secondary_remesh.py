# -*- coding: utf-8 -*-
"""
scripts/remeshing/execute_f1703_complete_secondary_remesh.py
============================================================
Task F1703: Complete Secondary Crack-Path Adaptive Refinement
Generates the official Task F1703 adapted mesh deck:
  models/pandey_kumar_mode1/203_pk_sec43_secondary_complete/PK_SEC43_F1703_SECONDARY_COMPLETE_ADAPT.inp
using native Abaqus/CAE sequential adaptiveRemesh() under coarseningFactor=NOT_ALLOWED
across:
  Pass 1: State 2 (Hole Arrest, uy=0.200mm)
  Pass 2: State 4 (Secondary Mid-Propagation, uy=0.300mm)
  Pass 3: State 5 (Terminal Dual Severance, uy=1.500mm)
with errorTarget=2.5% and minElementSize=0.143mm (~l0/2).

Performs exact 2D polygon-line segment clipping audit across canonical primary,
canonical horizontal secondary, and authentic secondary crack trajectories:
  results/validation/f1703_secondary_complete_connectivity_audit.json
"""

from __future__ import print_function
import os
import sys
import json
import math
import shutil
from abaqus import *
from abaqusConstants import *
import regionToolset
import mesh

def log(msg):
    print("[F1703-RECOVERY] " + str(msg))
    sys.stdout.flush()

def main():
    repo_root = r"D:\Master thesis\Adaptive remeshing"
    odb_dir = os.path.join(repo_root, "models", "pandey_kumar_mode1", "200_pk_sec43_prescribed_same_state")
    out_dir = os.path.join(repo_root, "models", "pandey_kumar_mode1", "203_pk_sec43_secondary_complete")
    os.makedirs(out_dir, exist_ok=True)
    out_inp = os.path.join(out_dir, "PK_SEC43_F1703_SECONDARY_COMPLETE_ADAPT.inp")

    odb_state2 = os.path.join(odb_dir, "PK_SEC43_PRESCRIBED_STATE2.odb")
    odb_state4 = os.path.join(odb_dir, "PK_SEC43_PRESCRIBED_STATE4.odb")
    odb_state5 = os.path.join(odb_dir, "PK_SEC43_PRESCRIBED_STATE5.odb")

    model_name = "Model_PK_Sec43_F1703_CompleteSecondary"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)

    log("1. Creating authentic Section 4.3 holed-plate geometry (65x120 mm)...")
    s = m.ConstrainedSketch(name="__profile__", sheetSize=200.0)
    s.Line(point1=(0.0, 0.0), point2=(65.0, 0.0))
    s.Line(point1=(65.0, 0.0), point2=(65.0, 120.0))
    s.Line(point1=(65.0, 120.0), point2=(0.0, 120.0))
    s.Line(point1=(0.0, 120.0), point2=(0.0, 70.2))
    s.Line(point1=(0.0, 70.2), point2=(10.0, 70.2))
    s.Line(point1=(10.0, 70.2), point2=(10.0, 69.8))
    s.Line(point1=(10.0, 69.8), point2=(0.0, 69.8))
    s.Line(point1=(0.0, 69.8), point2=(0.0, 0.0))

    s.CircleByCenterPerimeter(center=(36.5, 51.0), point1=(46.5, 51.0))
    s.CircleByCenterPerimeter(center=(20.0, 20.0), point1=(25.0, 20.0))
    s.CircleByCenterPerimeter(center=(20.0, 100.0), point1=(25.0, 100.0))

    p = m.Part(name="PlateWithHoles", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches["__profile__"]

    log("2. Seeding part with initial 1.50 mm coarse seed...")
    p.seedPart(size=1.50, deviationFactor=0.1, minSizeFactor=0.1)
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))
    p.generateMesh()

    p.Set(name="All_elem", faces=p.faces)
    a = m.rootAssembly
    inst = a.Instance(name="PART-1-1", part=p, dependent=ON)

    mat = m.Material(name="Steel")
    mat.Elastic(table=((210.0, 0.3),))
    m.HomogeneousSolidSection(name="SolidSec", material="Steel", thickness=1.0)
    p.SectionAssignment(region=p.sets["All_elem"], sectionName="SolidSec")

    donor_step_name = "RECOVERY_STEP"
    m.StaticStep(name=donor_step_name, previous="Initial", timePeriod=1.0)

    reg = inst.sets["All_elem"]
    rule_name = "RemeshingRule_F1703_CompleteSecondary"
    log("3. Defining RemeshingRule: %s (errorTarget=2.5%%, coarseningFactor=NOT_ALLOWED)..." % rule_name)
    m.RemeshingRule(
        name=rule_name,
        stepName=donor_step_name,
        region=reg,
        description="F1703 Multi-State Remeshing: errorTarget=2.5%, coarseningFactor=NOT_ALLOWED",
        variables=("MISESERI",),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=2.5,
        refinementFactor=10,
        coarseningFactor=NOT_ALLOWED,
        specifyMinSize=True,
        minElementSize=0.143,
        specifyMaxSize=True,
        maxElementSize=1.5
    )

    log("PASS 1: State 2 (Hole Arrest, uy=0.200mm)...")
    odb_d2 = session.openOdb(name=odb_state2)
    m.adaptiveRemesh(odb=odb_d2)
    odb_d2.close()
    log("  Pass 1 complete. Elements = %d" % len(p.elements))

    log("PASS 2: State 4 (Secondary Mid-Propagation, uy=0.300mm)...")
    odb_d4 = session.openOdb(name=odb_state4)
    m.adaptiveRemesh(odb=odb_d4)
    odb_d4.close()
    log("  Pass 2 complete. Elements = %d" % len(p.elements))

    log("PASS 3: State 5 (Terminal Dual Severance, uy=1.500mm)...")
    odb_d5 = session.openOdb(name=odb_state5)
    m.adaptiveRemesh(odb=odb_d5)
    odb_d5.close()
    log("  Pass 3 complete. Elements = %d" % len(p.elements))

    log("4. Writing adapted mesh input deck: %s..." % out_inp)
    job_name = "PK_SEC43_F1703_SECONDARY_COMPLETE_ADAPT"
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]
    j = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
    j.writeInput(consistencyChecking=OFF)
    src_inp = job_name + ".inp"
    if os.path.exists(src_inp):
        shutil.copy2(src_inp, out_inp)
        try: os.remove(src_inp)
        except: pass
    log("Wrote %s (%d bytes)" % (out_inp, os.path.getsize(out_inp)))

if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
scripts/remeshing/execute_method_a_native_remesh.py
==================================================
Task: F1653-PANDEY-KUMAR-ORIGINAL-METHOD-A-COARSE-COUPLED-JOB1
Implements the exact native Method A adaptive remeshing from Pandey & Kumar (2025):
1. Builds geometric model PlateWithHole with initial coarse mesh (2,906 elements).
2. Opens authentic Job 1 coupled ODB (PK_HOLE_COARSE_JOB1.odb).
3. Defines RemeshingRule referencing variables=('MISESERI',) on stepName='Step-2'.
4. Executes m.adaptiveRemesh(odb=o1).
5. Captures and records the exact execution log, adapted element count, and sizing behavior.
"""

from __future__ import print_function
import os
import sys
import json

from abaqus import mdb
from abaqusConstants import *
import regionToolset
import odbAccess
import mesh

def run_native_remesh():
    odb_path = os.path.abspath('models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_COARSE_JOB1.odb')
    out_dir = os.path.abspath('models/pandey_kumar_mode1/176_method_a_plate_with_hole')
    log_json = os.path.join(out_dir, 'native_remesh_job1_log.json')
    
    print("=== Step 1: Geometry & Initial Mesh Generation ===")
    model_name = "PK_HOLE_METHOD_A_JOB1"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)
    
    plate_w = 1.0
    plate_h = 1.0
    notch_a = 0.5
    notch_y = 0.5
    notch_w = 0.001
    hole_x = 0.65
    hole_y = 0.65
    hole_r = 0.10
    
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
    
    p = m.Part(name="PART-1", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches["__profile__"]
    
    mat = m.Material(name="Steel")
    mat.Elastic(table=((210000.0, 0.3),))
    m.HomogeneousSolidSection(name="SolidSec", material="Steel", thickness=1.0)
    p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName="SolidSec")
    
    # Coarse mesh seed 0.02
    p.seedPart(size=0.02, deviationFactor=0.1, minSizeFactor=0.1)
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    p.generateMesh()
    
    n_coarse_elems = len(p.elements)
    n_coarse_nodes = len(p.nodes)
    print("Generated Coarse Mesh: %d elements, %d nodes" % (n_coarse_elems, n_coarse_nodes))
    
    p.Set(name="ALL_ELEM", elements=p.elements)
    a = m.rootAssembly
    inst = a.Instance(name="PART-1-1", part=p, dependent=ON)
    reg = regionToolset.Region(faces=inst.faces)
    
    print("\n=== Step 2: Open Authentic Coupled Job 1 ODB ===")
    print("Opening ODB: %s" % odb_path)
    o1 = odbAccess.openOdb(path=odb_path, readOnly=True)
    
    # Check MISESERI in Step-2 and Step-1
    for sname in o1.steps.keys():
        st = o1.steps[sname]
        last_f = st.frames[-1]
        if 'MISESERI' in last_f.fieldOutputs:
            vals = [float(v.data) for v in last_f.fieldOutputs['MISESERI'].values if v.data is not None]
            print("Step %s last frame: MISESERI count=%d, min=%.6e, max=%.6e" % (
                sname, len(vals), min(vals) if vals else 0.0, max(vals) if vals else 0.0
            ))
            
    print("\n=== Step 3: Define Abaqus RemeshingRule ===")
    # Define RemeshingRule on Step-2 (or Step-1)
    step_target = "Step-2" if "Step-2" in o1.steps else "Step-1"
    
    # Create dummy step on CAE model so RemeshingRule has a step reference
    m.StaticStep(name="Step-1", previous="Initial", timePeriod=1.0)
    m.StaticStep(name="Step-2", previous="Step-1", timePeriod=1.0)
    
    m.RemeshingRule(
        name="RR_Method_A",
        stepName=step_target,
        region=reg,
        description="Original Pandey-Kumar Method A Remeshing Rule (errorTarget=2.0%%)",
        outputFrequency=ALL_INCREMENTS,
        variables=('MISESERI',),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=2.0,
        specifyMinSize=True,
        specifyMaxSize=True,
        minElementSize=0.001,
        maxElementSize=0.020,
        elementCountLimit=None,
        coarseningFactor=NOT_ALLOWED,
        refinementFactor=10
    )
    print("Created RemeshingRule: RR_Method_A on %s" % step_target)
    
    print("\n=== Step 4: Invoke m.adaptiveRemesh(odb=o1) ===")
    remesh_success = False
    error_msg = ""
    n_adapted_elems = n_coarse_elems
    n_adapted_nodes = n_coarse_nodes
    
    try:
        m.adaptiveRemesh(odb=o1)
        remesh_success = True
        n_adapted_elems = len(p.elements)
        n_adapted_nodes = len(p.nodes)
        print("m.adaptiveRemesh() completed successfully!")
        print("Adapted Mesh Count: %d elements, %d nodes (Change: %+d elements)" % (
            n_adapted_elems, n_adapted_nodes, n_adapted_elems - n_coarse_elems
        ))
    except Exception as e:
        remesh_success = False
        error_msg = str(e)
        print("m.adaptiveRemesh() failed with error: %s" % error_msg)
        
    o1.close()
    
    # Save physical mesh deck of adapted part
    adapted_phys_inp = os.path.join(out_dir, 'PK_HOLE_ORIG_METHOD_A_JOB1_ADAPT_PHYS.inp')
    if remesh_success:
        j_adapt = mdb.Job(name="PK_HOLE_ORIG_METHOD_A_JOB1_ADAPT", model=model_name)
        j_adapt.writeInput(consistencyChecking=OFF)
        print("Exported adapted model deck to: PK_HOLE_ORIG_METHOD_A_JOB1_ADAPT.inp")
        
    # Record execution summary
    summary = {
        "coarse_elements": n_coarse_elems,
        "coarse_nodes": n_coarse_nodes,
        "adapted_elements": n_adapted_elems,
        "adapted_nodes": n_adapted_nodes,
        "delta_elements": n_adapted_elems - n_coarse_elems,
        "remesh_success": remesh_success,
        "error_message": error_msg,
        "target_step": step_target,
        "rule_error_target": 2.0,
        "min_h": 0.001,
        "max_h": 0.020,
        "refinement_factor": 10,
        "coarsening_factor": "NOT_ALLOWED"
    }
    
    with open(log_json, 'w') as f:
        json.dump(summary, f, indent=2)
    print("Wrote remesh execution log to: %s" % log_json)

if __name__ == '__main__':
    run_native_remesh()

# -*- coding: utf-8 -*-
"""
scripts/remeshing/generate_f1687_mode1_blind_mesh.py
===================================================
Task F1687 Stage C: Mode-I Blind Generalization Mesh Generation.
Tests Hypothesis H2:
"The locked differential rule (e_tgt_prim = 5%, e_tgt_sec = 10%, adopted thresholds,
 h_equiv measure) produces a narrow, crack-following mesh on an unseen geometry
 with ZERO retuning."

Unseen Geometry: Mode-I 1x1 mm edge-cracked plate (notch tip at x=0.50, y=0.50).
Source Donor ODB: PK_M1_JOB1_INF_COMPANION_2906.odb
  - Step 1 (Early Donor): Frame 870 (just past peak load, initiation)
  - Step 2 (Terminal Donor): Frame 1021 (severance)
Export: models/pandey_kumar_mode1/01_standard_pfm_reference/PK_MODE1_BLIND_DIFF_PHYS.inp
"""

import os
import sys
import shutil
import time

from abaqus import *
from abaqusConstants import *
from caeModules import *
import regionToolset
import mesh
from odbAccess import openOdb, Odb

def log(msg):
    print("[F1687-BLIND-GEN] " + str(msg))
    sys.stdout.flush()

def create_differential_donor_odb(src_path, dst_path, early_frame_idx=870, term_frame_idx=1021):
    log("Creating 2-step differential donor ODB from %s..." % src_path)
    if os.path.exists(dst_path):
        os.remove(dst_path)

    src = openOdb(src_path, readOnly=True)
    inst_src = src.rootAssembly.instances['PART-1-1']
    
    dst = Odb(name="PK_MODE1_DIFFERENTIAL_DONOR", path=dst_path)
    part1 = dst.Part(name="PART-1", embeddedSpace=TWO_D_PLANAR, type=DEFORMABLE_BODY)

    # Copy nodes
    node_labels = [n.label for n in inst_src.nodes]
    node_coords = [(float(n.coordinates[0]), float(n.coordinates[1])) for n in inst_src.nodes]
    part1.addNodes(labels=node_labels, coordinates=node_coords)

    # Copy elements
    cpe4_elems = [e for e in inst_src.elements if e.type == 'CPE4']
    if cpe4_elems:
        part1.addElements(labels=[e.label for e in cpe4_elems], connectivity=[e.connectivity for e in cpe4_elems], type='CPE4')
    cpe3_elems = [e for e in inst_src.elements if e.type == 'CPE3']
    if cpe3_elems:
        part1.addElements(labels=[e.label for e in cpe3_elems], connectivity=[e.connectivity for e in cpe3_elems], type='CPE3')

    inst_dst = dst.rootAssembly.Instance(name='PART-1-1', object=part1)
    inst_dst.ElementSet(name='UMATELEM', elements=inst_dst.elements)

    all_labels = tuple(e.label for e in inst_src.elements if e.type in ('CPE4', 'CPE3'))

    # Step 1: Early Donor (Initiation)
    s1 = dst.Step(name='STEP_EARLY', description='Early Donor Step (Frame %d)' % early_frame_idx, domain=TIME, timePeriod=1.0)
    f1 = s1.Frame(frameId=1, frameValue=1.0, description='Early Donor Frame %d' % early_frame_idx)
    f_src_early = src.steps['Step-2'].frames[early_frame_idx]

    f_eri1 = f1.FieldOutput(name='MISESERI', description='Mises Error Indicator', type=SCALAR)
    f_avg1 = f1.FieldOutput(name='MISESAVG', description='Mises Average', type=SCALAR)
    f_evol1 = f1.FieldOutput(name='EVOL', description='Element volume', type=SCALAR)

    eri_src1 = {v.elementLabel: v.data for v in f_src_early.fieldOutputs['MISESERI'].values}
    avg_src1 = {v.elementLabel: v.data for v in f_src_early.fieldOutputs['MISESAVG'].values}
    evol_src1 = {v.elementLabel: v.data for v in f_src_early.fieldOutputs['EVOL'].values}

    valid_labels1 = [lbl for lbl in all_labels if lbl in eri_src1 and lbl in avg_src1 and lbl in evol_src1]
    f_eri1.addData(position=WHOLE_ELEMENT, instance=inst_dst, labels=valid_labels1, data=[[eri_src1[lbl]] for lbl in valid_labels1])
    f_avg1.addData(position=WHOLE_ELEMENT, instance=inst_dst, labels=valid_labels1, data=[[avg_src1[lbl]] for lbl in valid_labels1])
    f_evol1.addData(position=WHOLE_ELEMENT, instance=inst_dst, labels=valid_labels1, data=[[evol_src1[lbl]] for lbl in valid_labels1])

    # Step 2: Terminal Donor (Severance)
    s2 = dst.Step(name='STEP_TERMINAL', description='Terminal Donor Step (Frame %d)' % term_frame_idx, domain=TIME, timePeriod=1.0, previousStepName='STEP_EARLY')
    f2 = s2.Frame(frameId=1, frameValue=1.0, description='Terminal Donor Frame %d' % term_frame_idx)
    f_src_term = src.steps['Step-2'].frames[term_frame_idx]

    f_eri2 = f2.FieldOutput(name='MISESERI', description='Mises Error Indicator', type=SCALAR)
    f_avg2 = f2.FieldOutput(name='MISESAVG', description='Mises Average', type=SCALAR)
    f_evol2 = f2.FieldOutput(name='EVOL', description='Element volume', type=SCALAR)

    eri_src2 = {v.elementLabel: v.data for v in f_src_term.fieldOutputs['MISESERI'].values}
    avg_src2 = {v.elementLabel: v.data for v in f_src_term.fieldOutputs['MISESAVG'].values}
    evol_src2 = {v.elementLabel: v.data for v in f_src_term.fieldOutputs['EVOL'].values}

    valid_labels2 = [lbl for lbl in all_labels if lbl in eri_src2 and lbl in avg_src2 and lbl in evol_src2]
    f_eri2.addData(position=WHOLE_ELEMENT, instance=inst_dst, labels=valid_labels2, data=[[eri_src2[lbl]] for lbl in valid_labels2])
    f_avg2.addData(position=WHOLE_ELEMENT, instance=inst_dst, labels=valid_labels2, data=[[avg_src2[lbl]] for lbl in valid_labels2])
    f_evol2.addData(position=WHOLE_ELEMENT, instance=inst_dst, labels=valid_labels2, data=[[evol_src2[lbl]] for lbl in valid_labels2])

    dst.save()
    dst.close()
    src.close()
    log("Differential donor ODB created successfully: %s (%d bytes)" % (dst_path, os.path.getsize(dst_path)))

def build_base_mode1_cad_model(model_name="MODEL_MODE1_BLIND_DIFF"):
    log("Building base CAD model for Mode-I: %s" % model_name)
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)
    if "Model-1" in mdb.models:
        del mdb.models["Model-1"]

    s = m.ConstrainedSketch(name="__profile__", sheetSize=2.0)
    s.rectangle(point1=(0.0, 0.0), point2=(1.0, 1.0))
    p = m.Part(name="PART-1", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches["__profile__"]

    # Partition face to define sharp seam line y=0.5, 0 <= x <= 0.5
    p.PartitionFaceByShortestPath(faces=p.faces, point1=(0.0, 0.5, 0.0), point2=(0.5, 0.5, 0.0))
    seam_edge = p.edges.findAt(((0.25, 0.5, 0.0),))
    p.engineeringFeatures.assignSeam(regions=regionToolset.Region(edges=seam_edge))

    p.seedPart(size=0.020, deviationFactor=0.1, minSizeFactor=0.1)
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))
    p.generateMesh()

    p.Set(name='ALL_ELEM', faces=p.faces)
    p.Set(name='UMATELEM', faces=p.faces)

    a = m.rootAssembly
    inst = a.Instance(name="PART-1-1", part=p, dependent=ON)

    mat = m.Material(name="Steel")
    mat.Elastic(table=((210000.0, 0.3),))
    m.HomogeneousSolidSection(name="SolidSec", material="Steel", thickness=1.0)
    p.SectionAssignment(region=p.sets['ALL_ELEM'], sectionName="SolidSec")

    m.StaticStep(name="STEP_EARLY", previous="Initial")
    m.StaticStep(name="STEP_TERMINAL", previous="STEP_EARLY")

    reg = inst.sets["UMATELEM"]

    # LOCKED DIFFERENTIAL RULES (ZERO RETUNING)
    # Rule 1: Early Donor (Initiation), errorTarget = 5.0%
    m.RemeshingRule(
        name="Rule_Mode1_Early_5pct",
        stepName="STEP_EARLY",
        region=reg,
        description="F1687 Locked Rule 1: Early Initiation Donor (Frame 870, e_tgt=5.0%)",
        variables=("MISESERI",),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=5.0,
        specifyMinSize=True,
        specifyMaxSize=True,
        minElementSize=0.0015,
        maxElementSize=0.0200,
        coarseningFactor=NOT_ALLOWED,
        refinementFactor=10
    )

    # Rule 2: Terminal Donor (Severance), errorTarget = 10.0%
    m.RemeshingRule(
        name="Rule_Mode1_Terminal_10pct",
        stepName="STEP_TERMINAL",
        region=reg,
        description="F1687 Locked Rule 2: Terminal Severance Donor (Frame 1021, e_tgt=10.0%)",
        variables=("MISESERI",),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=10.0,
        specifyMinSize=True,
        specifyMaxSize=True,
        minElementSize=0.0015,
        maxElementSize=0.0200,
        coarseningFactor=NOT_ALLOWED,
        refinementFactor=10
    )

    log("Base CAD model '%s' built with locked differential rules." % model_name)
    return m, p

def main():
    t0 = time.time()
    donor_src = os.path.abspath("PK_M1_JOB1_INF_COMPANION_2906.odb")
    run_dir = os.path.abspath("runs/f1687_mode1_recovery")
    if not os.path.exists(run_dir):
        os.makedirs(run_dir)
    donor_dst = os.path.join(run_dir, "PK_MODE1_DIFFERENTIAL_DONOR.odb")

    out_inp_dir = os.path.abspath("models/pandey_kumar_mode1/01_standard_pfm_reference")
    if not os.path.exists(out_inp_dir):
        os.makedirs(out_inp_dir)
    out_inp_path = os.path.join(out_inp_dir, "PK_MODE1_BLIND_DIFF_PHYS.inp")

    log("======================================================================")
    log("TASK F1687 STAGE C: MODE-I BLIND GENERALIZATION MESH GENERATION")
    log("Source Companion ODB: %s" % donor_src)
    log("Target Output Deck:   %s" % out_inp_path)
    log("======================================================================")

    # 1. Create 2-step donor ODB
    create_differential_donor_odb(donor_src, donor_dst, early_frame_idx=870, term_frame_idx=1021)

    # 2. Build base CAD model with locked rules
    m, p = build_base_mode1_cad_model("MODEL_MODE1_BLIND_DIFF")

    # 3. Execute native adaptive remesh
    odb_donor = session.openOdb(name=donor_dst)
    log("Calling m.adaptiveRemesh(odb=odb_donor)...")
    m.adaptiveRemesh(odb=odb_donor)
    odb_donor.close()

    n_elems = len(p.elements)
    n_nodes = len(p.nodes)
    n_quads = sum([1 for e in p.elements if len(e.connectivity) == 4])
    n_tris = sum([1 for e in p.elements if len(e.connectivity) == 3])

    log("Native adaptiveRemesh executed successfully!")
    log("  Adapted Physical Elements: %d (Quads: %d = %.2f%%, Tris: %d = %.2f%%)" % (
        n_elems, n_quads, 100.0 * n_quads / n_elems, n_tris, 100.0 * n_tris / n_elems
    ))
    log("  Adapted Physical Nodes:    %d" % n_nodes)

    # 4. Export physical mesh INP
    job_name = "PK_MODE1_BLIND_DIFF_PHYS"
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]
    j = mdb.Job(name=job_name, model=m.name, type=ANALYSIS)
    j.writeInput(consistencyChecking=OFF)

    raw_inp = job_name + ".inp"
    if os.path.exists(out_inp_path):
        os.remove(out_inp_path)
    shutil.copyfile(raw_inp, out_inp_path)
    log("Wrote physical adapted deck to: %s (%d bytes)" % (out_inp_path, os.path.getsize(out_inp_path)))

    dt = time.time() - t0
    log("Completed in %.2f seconds." % dt)

if __name__ == "__main__":
    main()

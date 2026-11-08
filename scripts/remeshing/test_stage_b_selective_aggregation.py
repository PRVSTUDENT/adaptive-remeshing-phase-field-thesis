"""
scripts/remeshing/test_stage_b_selective_aggregation.py
========================================================
Task F1686 - Stage B & C: Selective Error Aggregation Parameter Investigation.
Evaluates Differential Multi-Target Aggregation:
- Rule 1 (Candidate C, Frame 150): errorTarget = 5.0% (Primary crack & notch tip)
- Rule 2 (Terminal Baseline, Frame 337): errorTarget varied across [5.0%, 10.0%, 15.0%, 20.0%, 25.0%, 30.0%, 40.0%, 50.0%]
Driven by authentic recovery database:
  runs/f1684_multistep_recovery/PK_HOLE_MULTISTEP_RECOVERY.odb

Compatible with Abaqus/CAE Python 2.7.
"""
from abaqus import *
from abaqusConstants import *
import regionToolset
import part
import mesh
import job
import step
import load
import odbAccess
import os
import sys
import shutil
import math

def log(msg):
    print(msg)
    sys.stdout.flush()

def build_base_cad_model(model_name):
    m = mdb.Model(name=model_name)
    if "Model-1" in mdb.models:
        del mdb.models["Model-1"]

    plate_w = 1.0; plate_h = 1.0; notch_a = 0.5; notch_y = 0.5; notch_w = 0.001
    hole_x = 0.65; hole_y = 0.65; hole_r = 0.10

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

    p = m.Part(name="PlateWithHole", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches["__profile__"]

    p.seedPart(size=0.020, deviationFactor=0.1, minSizeFactor=0.1)
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))
    p.generateMesh()

    a = m.rootAssembly
    inst = a.Instance(name="Plate-1", part=p, dependent=ON)
    a.Set(name="All_elem", faces=inst.faces)

    mat = m.Material(name="Steel")
    mat.Elastic(table=((210000.0, 0.3),))
    m.HomogeneousSolidSection(name="SolidSec", material="Steel", thickness=1.0)
    p.SectionAssignment(region=(p.faces,), sectionName="SolidSec")

    m.StaticStep(name="RECOVERY_C", previous="Initial")
    m.StaticStep(name="RECOVERY_TERMINAL", previous="RECOVERY_C")

    return m

def main():
    repo_root = os.path.abspath(".")
    odb_path = os.path.join(repo_root, "runs", "f1684_multistep_recovery", "PK_HOLE_MULTISTEP_RECOVERY.odb")
    cand_dir = os.path.join(repo_root, "models", "pandey_kumar_mode1", "176_method_a_plate_with_hole", "candidates")
    if not os.path.exists(cand_dir):
        os.makedirs(cand_dir)

    log("=" * 80)
    log("TASK F1686: STAGE B & C - SELECTIVE ERROR AGGREGATION MESH GENERATION")
    log("Recovery ODB: %s" % odb_path)
    log("Candidates output directory: %s" % cand_dir)
    log("=" * 80)

    if not os.path.exists(odb_path):
        raise RuntimeError("Multi-step recovery ODB not found: %s" % odb_path)

    odb = session.openOdb(name=odb_path)

    test_targets = [5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 40.0, 50.0]
    results = []

    for e_sec in test_targets:
        model_name = "MODEL_SEL_E%02d" % int(e_sec)
        log("\n>>> Generating Candidate: Rule 1 e_tgt=5.0%%, Rule 2 e_tgt=%.1f%% (Model: %s) <<<" % (e_sec, model_name))
        Mdb()
        m = build_base_cad_model(model_name)
        p = m.parts["PlateWithHole"]
        reg = m.rootAssembly.sets["All_elem"]

        # Rule 1: Candidate C (Frame 150) - 5.0% target
        m.RemeshingRule(
            name="Rule_CandC_5pct",
            stepName="RECOVERY_C",
            region=reg,
            description="Candidate C Primary Fracture Rule (e_tgt=5.0%)",
            outputFrequency=ALL_INCREMENTS,
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

        # Rule 2: Terminal Baseline (Frame 337) - e_sec target
        m.RemeshingRule(
            name="Rule_Terminal_Selective",
            stepName="RECOVERY_TERMINAL",
            region=reg,
            description="Terminal Baseline Secondary Ligament Rule (e_tgt=%.1f%%)" % e_sec,
            outputFrequency=ALL_INCREMENTS,
            variables=("MISESERI",),
            sizingMethod=UNIFORM_ERROR,
            errorTarget=e_sec,
            specifyMinSize=True,
            specifyMaxSize=True,
            minElementSize=0.0015,
            maxElementSize=0.0200,
            coarseningFactor=NOT_ALLOWED,
            refinementFactor=10
        )

        m.adaptiveRemesh(odb=odb)

        n_elems = len(p.elements)
        n_nodes = len(p.nodes)
        n_quads = sum([1 for el in p.elements if len(el.connectivity) == 4])
        n_tris = sum([1 for el in p.elements if len(el.connectivity) == 3])

        log("  Generated: %d elements (%d quads, %d tris), %d nodes." % (n_elems, n_quads, n_tris, n_nodes))

        # Write input deck
        job_name = "PK_HOLE_SEL_E%02d_PHYS" % int(e_sec)
        j = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
        j.writeInput(consistencyChecking=OFF)

        dest_inp = os.path.join(cand_dir, "%s.inp" % job_name)
        shutil.copyfile("%s.inp" % job_name, dest_inp)
        log("  Saved to: %s" % dest_inp)

        results.append({
            "target_sec_pct": e_sec,
            "job_name": job_name,
            "inp_path": dest_inp,
            "n_elements": n_elems,
            "n_nodes": n_nodes,
            "quads": n_quads,
            "tris": n_tris
        })

    odb.close()

    # Save summary
    sum_json = os.path.join(repo_root, "results", "validation", "f1686_stage_b_candidates_summary.json")
    import json
    with open(sum_json, 'w') as f:
        json.dump(results, f, indent=2)

    log("\n" + "=" * 80)
    log("STAGE B/C GENERATION COMPLETE: %d candidate meshes generated." % len(results))
    log("Saved summary to: %s" % sum_json)
    log("=" * 80)

if __name__ == '__main__':
    main()

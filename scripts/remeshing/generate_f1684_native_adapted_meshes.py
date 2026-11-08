"""
scripts/remeshing/generate_f1684_native_adapted_meshes.py
=========================================================
Task F1684: Generation of Native Abaqus Adapted Meshes
- Mesh 1 (Control B): Candidate C Rule alone (errorTarget = 5.0%, min = 1.5 um, max = 20 um)
- Mesh 2 (Experiment C): Combined Multi-Step (Rule_C + Rule_Terminal, both errorTarget = 5.0%)
Driven by authentic multi-step recovery ODB:
  runs/f1684_multistep_recovery/PK_HOLE_MULTISTEP_RECOVERY.odb
Exports:
  models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1684_CAND_C_ADAPT_PHYS.inp
  models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1684_COMBINED_ADAPT_PHYS.inp
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

    # Define both steps to match ODB
    m.StaticStep(name="RECOVERY_C", previous="Initial")
    m.StaticStep(name="RECOVERY_TERMINAL", previous="RECOVERY_C")

    log("Base CAD model '%s' built: %d elements, %d nodes." % (model_name, len(p.elements), len(p.nodes)))
    return m

def main():
    odb_path = os.path.abspath("runs/f1684_multistep_recovery/PK_HOLE_MULTISTEP_RECOVERY.odb")
    dest_dir = os.path.abspath("models/pandey_kumar_mode1/176_method_a_plate_with_hole")
    os.makedirs(dest_dir, exist_ok=True)

    log("======================================================================")
    log("TASK F1684: NATIVE ADAPTED MESH GENERATION (CANDIDATE C vs COMBINED)")
    log("Recovery ODB: %s" % odb_path)
    log("Target Directory: %s" % dest_dir)
    log("======================================================================")

    if not os.path.exists(odb_path):
        raise RuntimeError("Multi-step recovery ODB not found: %s" % odb_path)

    odb = session.openOdb(name=odb_path)

    # --------------------------------------------------------------------------
    # 1. GENERATE MESH 1 (CONTROL B — CANDIDATE C ALONE)
    # --------------------------------------------------------------------------
    log("\n--- 1. Generating Mesh 1 (Control B: Candidate C Alone, errorTarget=5.0%) ---")
    Mdb()
    m_c = build_base_cad_model("PK_HOLE_F1684_CAND_C")
    p_c = m_c.parts["PlateWithHole"]
    reg_c = m_c.rootAssembly.sets["All_elem"]

    m_c.RemeshingRule(
        name="Rule_CandC_5pct",
        stepName="RECOVERY_C",
        region=reg_c,
        description="F1684 Control B: Candidate C alone (Frame 150, errorTarget=5.0%)",
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

    log("Invoking adaptiveRemesh for Candidate C alone...")
    m_c.adaptiveRemesh(odb=odb)
    n_elems_c = len(p_c.elements)
    n_nodes_c = len(p_c.nodes)
    n_quads_c = sum([1 for e in p_c.elements if len(e.connectivity) == 4])
    n_tris_c = sum([1 for e in p_c.elements if len(e.connectivity) == 3])
    log("SUCCESS: Mesh 1 (Control B) Adapted!")
    log("  Total Elements: %d (Quads: %d = %.2f%%, Tris: %d = %.2f%%)" % (
        n_elems_c, n_quads_c, 100.0 * n_quads_c / n_elems_c, n_tris_c, 100.0 * n_tris_c / n_elems_c
    ))
    log("  Total Nodes:    %d" % n_nodes_c)

    job_c_name = "PK_HOLE_F1684_CAND_C_ADAPT_PHYS"
    j_c = mdb.Job(name=job_c_name, model="PK_HOLE_F1684_CAND_C", type=ANALYSIS)
    j_c.writeInput(consistencyChecking=OFF)
    dest_c_inp = os.path.join(dest_dir, f"{job_c_name}.inp")
    shutil.copyfile(f"{job_c_name}.inp", dest_c_inp)
    log("Wrote Mesh 1 to: %s (%d bytes)" % (dest_c_inp, os.path.getsize(dest_c_inp)))

    # --------------------------------------------------------------------------
    # 2. GENERATE MESH 2 (EXPERIMENT C — COMBINED MULTI-STEP)
    # --------------------------------------------------------------------------
    log("\n--- 2. Generating Mesh 2 (Experiment C: Combined Multi-Step, errorTarget=5.0%) ---")
    Mdb()
    m_comb = build_base_cad_model("PK_HOLE_F1684_COMBINED")
    p_comb = m_comb.parts["PlateWithHole"]
    reg_comb = m_comb.rootAssembly.sets["All_elem"]

    m_comb.RemeshingRule(
        name="Rule_CandC_5pct",
        stepName="RECOVERY_C",
        region=reg_comb,
        description="F1684 Candidate C Primary Fracture Rule (Frame 150, errorTarget=5.0%)",
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

    m_comb.RemeshingRule(
        name="Rule_Terminal_5pct",
        stepName="RECOVERY_TERMINAL",
        region=reg_comb,
        description="F1684 Terminal Baseline Secondary Ligament Rule (Frame 337, errorTarget=5.0%)",
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

    log("Invoking adaptiveRemesh for Combined Multi-Step...")
    m_comb.adaptiveRemesh(odb=odb)
    n_elems_comb = len(p_comb.elements)
    n_nodes_comb = len(p_comb.nodes)
    n_quads_comb = sum([1 for e in p_comb.elements if len(e.connectivity) == 4])
    n_tris_comb = sum([1 for e in p_comb.elements if len(e.connectivity) == 3])
    log("SUCCESS: Mesh 2 (Experiment C) Adapted!")
    log("  Total Elements: %d (Quads: %d = %.2f%%, Tris: %d = %.2f%%)" % (
        n_elems_comb, n_quads_comb, 100.0 * n_quads_comb / n_elems_comb, n_tris_comb, 100.0 * n_tris_comb / n_elems_comb
    ))
    log("  Total Nodes:    %d" % n_nodes_comb)

    job_comb_name = "PK_HOLE_F1684_COMBINED_ADAPT_PHYS"
    j_comb = mdb.Job(name=job_comb_name, model="PK_HOLE_F1684_COMBINED", type=ANALYSIS)
    j_comb.writeInput(consistencyChecking=OFF)
    dest_comb_inp = os.path.join(dest_dir, f"{job_comb_name}.inp")
    shutil.copyfile(f"{job_comb_name}.inp", dest_comb_inp)
    log("Wrote Mesh 2 to: %s (%d bytes)" % (dest_comb_inp, os.path.getsize(dest_comb_inp)))

    odb.close()
    log("\n======================================================================")
    log("BOTH NATIVE ADAPTED MESHES GENERATED & ARCHIVED SUCCESSFULLY!")
    log("======================================================================")

if __name__ == "__main__":
    main()

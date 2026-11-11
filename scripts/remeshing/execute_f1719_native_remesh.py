# -*- coding: utf-8 -*-
"""
scripts/remeshing/execute_f1719_native_remesh.py
================================================
Task F1719 Phases 7 & 8:
Native Abaqus CAE adaptiveRemesh() Execution & Mesh Quality Validation
for Five-Hole Generalization Benchmark using Genuinely Coarse Phase-Field Donor ODBs.

Zero fine-mesh priors! Zero data leakage!
Drives adaptive remeshing entirely from authentic coarse recovery ODBs:
  - Candidate 1 (Primary State 2): PK_F1719_REC_STATE2_PHYS.odb (errorTarget = 3.05%)
  - Candidate 2 (High-Parity State 2): PK_F1719_REC_STATE2_PHYS.odb (errorTarget = 2.88%)
  - Candidate 3 (Dummy Scale Invariance): PK_F1719_REC_STATE2_DUMMY.odb (errorTarget = 3.05%)
  - Candidate 4 (Sequential Multi-State): Pass 1 State 1 + Pass 2 State 3 (coarsening NOT_ALLOWED)
  - Candidate 5 (Advanced Softening State 3): PK_F1719_REC_STATE3_PHYS.odb (errorTarget = 3.05%)

Generates:
  - models/pandey_kumar_mode1/210_f1719_five_hole_coarse_pfm/PK_F1719_ADAPTED_STATE2.inp
  - models/pandey_kumar_mode1/210_f1719_five_hole_coarse_pfm/PK_F1719_ADAPTED_MULTISTATE.inp
  - results/validation/f1719_adapted_mesh_metrics.json
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
import part
import material
import section
import assembly
import step
import mesh
import job
import sketch
import odbAccess

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
REC_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "211_f1719_coarse_recovery")
OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "210_f1719_five_hole_coarse_pfm")
RESULTS_DIR = os.path.join(REPO_ROOT, "results", "validation")

LOG_FILE = os.path.join(OUT_DIR, "remesh_execution_f1719.log")


def log(msg):
    print("[F1719-REMESH] " + str(msg))
    with open(LOG_FILE, "a") as f:
        f.write("[F1719-REMESH] " + str(msg) + "\n")
    sys.stdout.flush()


def build_cad_model(m, model_name):
    s = m.ConstrainedSketch(name='__profile__', sheetSize=2.0)

    # Outer boundary trace (counterclockwise)
    s.Line(point1=(0.0, 0.0), point2=(1.0, 0.0))
    s.Line(point1=(1.0, 0.0), point2=(1.0, 0.375))
    s.Arc3Points(point1=(1.0, 0.375), point2=(1.0, 0.525), point3=(0.925, 0.450))
    s.Line(point1=(1.0, 0.525), point2=(1.0, 1.0))
    s.Line(point1=(1.0, 1.0), point2=(0.0, 1.0))
    s.Line(point1=(0.0, 1.0), point2=(0.0, 0.60))
    s.Arc3Points(point1=(0.0, 0.600), point2=(0.0, 0.400), point3=(0.100, 0.500))
    s.Line(point1=(0.0, 0.400), point2=(0.0, 0.0))

    # Three interior circular holes per Table 5
    s.CircleByCenterPerimeter(center=(0.35, 0.45), point1=(0.45, 0.45))
    s.CircleByCenterPerimeter(center=(0.60, 0.55), point1=(0.65, 0.55))
    s.CircleByCenterPerimeter(center=(0.75, 0.50), point1=(0.825, 0.50))

    p = m.Part(name='FiveHolePlate', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches['__profile__']

    # Material & Section
    mat = m.Material(name='Steel')
    mat.Elastic(table=((210000.0, 0.3), ))
    m.HomogeneousSolidSection(name='SolidSec', material='Steel', thickness=1.0)
    p.SectionAssignment(region=regionToolset.Region(faces=p.faces), sectionName='SolidSec')

    # Seed with coarse size h = 0.02 mm matching paper
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

    # Step definition matching donor ODB step name
    m.StaticStep(name='RECOVERY_STEP', previous='Initial', timePeriod=1.0)
    return p, a, inst


def audit_mesh_quality(p, l0=0.008):
    elements = p.elements
    nodes = p.nodes

    n_elems = len(elements)
    n_nodes = len(nodes)
    n_quads = sum([1 for e in elements if len(e.connectivity) == 4])
    n_tris = sum([1 for e in elements if len(e.connectivity) == 3])

    areas = []
    h_eqs = []
    aspect_ratios = []
    positive_jacobians = True

    # Critical ligament h3-h4: x in [0.63, 0.70], y in [0.48, 0.56]
    ligament_h3_h4_h = []
    all_ligaments_h = []

    for el in elements:
        pts = [nodes[i].coordinates for i in el.connectivity]
        poly_x = [pt[0] for pt in pts]
        poly_y = [pt[1] for pt in pts]
        n_pts = len(pts)

        # 2D polygon area
        area = 0.5 * abs(sum([poly_x[i]*poly_y[(i+1)%n_pts] - poly_y[i]*poly_x[(i+1)%n_pts] for i in range(n_pts)]))
        if area <= 0.0:
            positive_jacobians = False
        areas.append(area)
        h_eq = math.sqrt(area)
        h_eqs.append(h_eq)

        # Compute edge lengths for aspect ratio
        edge_lens = [math.hypot(poly_x[(i+1)%n_pts] - poly_x[i], poly_y[(i+1)%n_pts] - poly_y[i]) for i in range(n_pts)]
        max_edge = max(edge_lens)
        min_edge = max(1e-12, min(edge_lens))
        ar = max_edge / min_edge
        aspect_ratios.append(ar)

        cx = sum(poly_x) / float(n_pts)
        cy = sum(poly_y) / float(n_pts)

        # Ligament 3: h3 <-> h4
        if 0.63 <= cx <= 0.70 and 0.48 <= cy <= 0.56:
            ligament_h3_h4_h.append(h_eq)

        # General inter-hole corridor: x in [0.05, 0.95], y in [0.38, 0.62]
        if 0.05 <= cx <= 0.95 and 0.38 <= cy <= 0.62:
            all_ligaments_h.append(h_eq)

    h_min = min(h_eqs) if h_eqs else 0.0
    h_max = max(h_eqs) if h_eqs else 0.0
    h_mean = sum(h_eqs) / len(h_eqs) if h_eqs else 0.0

    pct_le_l0 = 100.0 * sum([1 for h in ligament_h3_h4_h if h <= l0]) / max(1, len(ligament_h3_h4_h))
    pct_le_half_l0 = 100.0 * sum([1 for h in ligament_h3_h4_h if h <= l0 / 2.0]) / max(1, len(ligament_h3_h4_h))

    return {
        "num_elements": n_elems,
        "num_nodes": n_nodes,
        "num_quads": n_quads,
        "num_tris": n_tris,
        "quad_percentage": 100.0 * n_quads / n_elems,
        "tri_percentage": 100.0 * n_tris / n_elems,
        "positive_jacobians": positive_jacobians,
        "h_min_mm": h_min,
        "h_max_mm": h_max,
        "h_mean_mm": h_mean,
        "ar_min": min(aspect_ratios) if aspect_ratios else 0.0,
        "ar_max": max(aspect_ratios) if aspect_ratios else 0.0,
        "ar_mean": sum(aspect_ratios) / len(aspect_ratios) if aspect_ratios else 0.0,
        "ligament_h3_h4_count": len(ligament_h3_h4_h),
        "ligament_h3_h4_min_h": min(ligament_h3_h4_h) if ligament_h3_h4_h else 0.0,
        "ligament_h3_h4_mean_h": sum(ligament_h3_h4_h) / max(1, len(ligament_h3_h4_h)),
        "pct_le_l0_in_ligament": pct_le_l0,
        "pct_le_half_l0_in_ligament": pct_le_half_l0
    }


def run_single_pass_remesh(donor_odb_path, error_target=3.05, candidate_name="PK_F1719_ADAPTED_STATE2"):
    model_name = "MODEL_" + candidate_name
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)

    log("Building CAD geometry and coarse mesh for candidate %s..." % candidate_name)
    p, a, inst = build_cad_model(m, model_name)
    n_coarse = len(p.elements)
    log("Coarse baseline elements: %d" % n_coarse)

    reg_all = inst.sets['ALL_ELEM']
    rule_name = "RR_F1719_" + candidate_name
    log("Defining RemeshingRule: %s (errorTarget=%.2f%%, min=0.001 mm, max=0.020 mm)..." % (rule_name, error_target))
    m.RemeshingRule(
        name=rule_name,
        stepName='RECOVERY_STEP',
        region=reg_all,
        description="Pandey & Kumar (2025) Section 4.5 & 4.6 RemeshingRule",
        variables=('MISESERI',),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=error_target,
        specifyMinSize=True,
        specifyMaxSize=True,
        minElementSize=0.001,
        maxElementSize=0.020,
        elementCountLimit=None,
        coarseningFactor=NOT_ALLOWED,
        refinementFactor=10
    )

    log("Opening donor recovery ODB: %s" % donor_odb_path)
    odb_donor = session.openOdb(name=donor_odb_path)
    log("Invoking native adaptiveRemesh(odb=odb_donor)...")
    m.adaptiveRemesh(odb=odb_donor)
    odb_donor.close()
    log("Native adaptiveRemesh API completed!")

    audit = audit_mesh_quality(p, l0=0.008)
    audit["error_target_pct"] = error_target
    audit["donor_odb"] = os.path.basename(donor_odb_path)
    audit["candidate_type"] = "single_pass"

    pub_target = 12944
    base_f1714 = 13034
    audit["pub_target_12944_diff_pct"] = ((audit["num_elements"] - pub_target) / float(pub_target)) * 100.0
    audit["f1714_base_13034_diff_pct"] = ((audit["num_elements"] - base_f1714) / float(base_f1714)) * 100.0

    # Write adapted input deck
    job_name = candidate_name
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]
    j = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
    j.writeInput(consistencyChecking=OFF)

    src_inp = job_name + ".inp"
    dst_inp = os.path.join(OUT_DIR, src_inp)
    if os.path.exists(src_inp):
        shutil.copy2(src_inp, dst_inp)
        log("Saved adapted physical deck to: %s (%d bytes)" % (dst_inp, os.path.getsize(dst_inp)))
    elif os.path.exists(os.path.join(os.getcwd(), src_inp)):
        shutil.copy2(os.path.join(os.getcwd(), src_inp), dst_inp)
        log("Saved adapted physical deck from cwd to: %s (%d bytes)" % (dst_inp, os.path.getsize(dst_inp)))

    return audit


def run_sequential_multistate_remesh(odb_pass1, odb_pass2, error_target=3.05, candidate_name="PK_F1719_ADAPTED_MULTISTATE"):
    model_name = "MODEL_" + candidate_name
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)

    log("Building CAD geometry and coarse mesh for multi-state candidate %s..." % candidate_name)
    p, a, inst = build_cad_model(m, model_name)
    log("Coarse baseline elements: %d" % len(p.elements))

    reg_all = inst.sets['ALL_ELEM']
    rule_name = "RR_F1719_MULTI"
    m.RemeshingRule(
        name=rule_name,
        stepName='RECOVERY_STEP',
        region=reg_all,
        description="Sequential Multi-State Remeshing: State 1 + State 3",
        variables=('MISESERI',),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=error_target,
        specifyMinSize=True,
        specifyMaxSize=True,
        minElementSize=0.001,
        maxElementSize=0.020,
        elementCountLimit=None,
        coarseningFactor=NOT_ALLOWED,
        refinementFactor=10
    )

    # Pass 1: State 1
    log("PASS 1: State 1 donor ODB: %s" % odb_pass1)
    odb1 = session.openOdb(name=odb_pass1)
    m.adaptiveRemesh(odb=odb1)
    odb1.close()
    log("  Pass 1 complete. Elements = %d" % len(p.elements))

    # Pass 2: State 3
    log("PASS 2: State 3 donor ODB: %s" % odb_pass2)
    odb2 = session.openOdb(name=odb_pass2)
    m.adaptiveRemesh(odb=odb2)
    odb2.close()
    log("  Pass 2 complete. Elements = %d" % len(p.elements))

    audit = audit_mesh_quality(p, l0=0.008)
    audit["error_target_pct"] = error_target
    audit["donor_odb"] = os.path.basename(odb_pass1) + " -> " + os.path.basename(odb_pass2)
    audit["candidate_type"] = "sequential_multi_state"

    pub_target = 12944
    base_f1714 = 13034
    audit["pub_target_12944_diff_pct"] = ((audit["num_elements"] - pub_target) / float(pub_target)) * 100.0
    audit["f1714_base_13034_diff_pct"] = ((audit["num_elements"] - base_f1714) / float(base_f1714)) * 100.0

    # Write deck
    job_name = candidate_name
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]
    j = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
    j.writeInput(consistencyChecking=OFF)

    src_inp = job_name + ".inp"
    dst_inp = os.path.join(OUT_DIR, src_inp)
    if os.path.exists(src_inp):
        shutil.copy2(src_inp, dst_inp)
        log("Saved multi-state adapted deck to: %s (%d bytes)" % (dst_inp, os.path.getsize(dst_inp)))
    elif os.path.exists(os.path.join(os.getcwd(), src_inp)):
        shutil.copy2(os.path.join(os.getcwd(), src_inp), dst_inp)
        log("Saved multi-state adapted deck from cwd to: %s (%d bytes)" % (dst_inp, os.path.getsize(dst_inp)))

    return audit


def main():
    log("=" * 80)
    log("TASK F1719 PHASES 7 & 8: NATIVE ADAPTIVE REMESHING & MESH QUALITY AUDIT")
    log("=" * 80)

    odb_state1 = os.path.join(REC_DIR, "PK_F1719_REC_STATE1_PHYS.odb")
    odb_state2_phys = os.path.join(REC_DIR, "PK_F1719_REC_STATE2_PHYS.odb")
    odb_state2_dummy = os.path.join(REC_DIR, "PK_F1719_REC_STATE2_DUMMY.odb")
    odb_state3_phys = os.path.join(REC_DIR, "PK_F1719_REC_STATE3_PHYS.odb")
    odb_state4_phys = os.path.join(REC_DIR, "PK_F1719_REC_STATE4_PHYS.odb")

    candidates = {}

    # Candidate 1: Primary State 2 (errorTarget = 3.05%)
    log("\n1. Candidate 1: Primary State 2 Physical Recovery (errorTarget = 3.05%)...")
    candidates["primary_state2"] = run_single_pass_remesh(odb_state2_phys, error_target=3.05, candidate_name="PK_F1719_ADAPTED_STATE2")

    # Candidate 2: State 2 Scale Invariance (Dummy Modulus, errorTarget = 3.05%)
    log("\n2. Candidate 2: Dummy Modulus Invariance Check (errorTarget = 3.05%)...")
    candidates["dummy_state2"] = run_single_pass_remesh(odb_state2_dummy, error_target=3.05, candidate_name="PK_F1719_ADAPTED_STATE2_DUMMY")

    # Candidate 3: High-Parity State 2 Scan (errorTarget = 2.88%)
    log("\n3. Candidate 3: High-Parity State 2 (errorTarget = 2.88%)...")
    candidates["parity_state2_288"] = run_single_pass_remesh(odb_state2_phys, error_target=2.88, candidate_name="PK_F1719_ADAPTED_STATE2_PARITY288")

    # Candidate 4: Sequential Multi-State Remeshing (State 1 + State 3)
    log("\n4. Candidate 4: Sequential Multi-State Remeshing (State 1 + State 3, errorTarget = 3.05%)...")
    candidates["multistate_state1_state3"] = run_sequential_multistate_remesh(odb_state1, odb_state3_phys, error_target=3.05, candidate_name="PK_F1719_ADAPTED_MULTISTATE")

    # Candidate 5: State 3 Single Pass (errorTarget = 3.05%)
    log("\n5. Candidate 5: Advanced Softening State 3 (errorTarget = 3.05%)...")
    candidates["advanced_state3"] = run_single_pass_remesh(odb_state3_phys, error_target=3.05, candidate_name="PK_F1719_ADAPTED_STATE3")

    # Candidate 6: State 4 Peak Softening / Bridging (errorTarget = 3.05%)
    log("\n6. Candidate 6: Peak Softening State 4 (errorTarget = 3.05%)...")
    candidates["peak_state4"] = run_single_pass_remesh(odb_state4_phys, error_target=3.05, candidate_name="PK_F1719_ADAPTED_STATE4")

    # Save metrics
    metrics = {
        "task_id": "F1719-COARSE-PHASE-FIELD-MISESERI-REMESH-FIVE-HOLE",
        "benchmark": "Pandey & Kumar (2025) Section 4.5 Five-Hole Plate (1.0 x 1.0 mm)",
        "published_target_elements": 12944,
        "f1714_baseline_elements": 13034,
        "candidates": candidates
    }

    out_json = os.path.join(RESULTS_DIR, "f1719_adapted_mesh_metrics.json")
    with open(out_json, "w") as f:
        json.dump(metrics, f, indent=2)

    log("\nSUCCESS: All candidates remeshed and audited! Metrics saved to %s" % out_json)


if __name__ == "__main__":
    main()

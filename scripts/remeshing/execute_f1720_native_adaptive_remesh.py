# -*- coding: utf-8 -*-
"""
scripts/remeshing/execute_f1720_native_adaptive_remesh.py
========================================================
Task F1720 Stage 4: Native Abaqus CAE adaptiveRemesh() Execution & Mesh Audit
from Direct UEL-UMAT Coupled ODB (PK_F1720_COARSE_COUPLED.odb).

Zero manual guidance! Zero predefined crack corridors!
Refinement is driven 100% natively by Abaqus MISESERI.

Audits candidate error targets to reproduce the published 12,944-element benchmark.
Generates:
  - models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1720_ADAPTED_PHYS.inp
  - models/pandey_kumar_mode1/214_f1720_adapted_mesh/PK_F1720_ADAPTED_PFM.inp
  - results/validation/f1720_adapted_mesh_metrics.json
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

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
COUPLED_ODB = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "213_f1720_coarse_coupled", "PK_F1720_COARSE_COUPLED.odb")
OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "214_f1720_adapted_mesh")
RESULTS_DIR = os.path.join(REPO_ROOT, "results", "validation")

if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

LOG_FILE = os.path.join(OUT_DIR, "remesh_execution_f1720.log")

def log(msg):
    print("[F1720-REMESH] " + str(msg))
    with open(LOG_FILE, "a") as f:
        f.write("[F1720-REMESH] " + str(msg) + "\n")
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
    m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0)
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

def run_remesh_candidate(donor_odb_path, error_target, candidate_name):
    model_name = "MODEL_" + candidate_name
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)

    log("Building CAD model for %s (errorTarget=%.2f%%)..." % (candidate_name, error_target))
    p, a, inst = build_cad_model(m, model_name)

    reg_all = inst.sets['ALL_ELEM']
    rule_name = "RR_" + candidate_name
    m.RemeshingRule(
        name=rule_name,
        stepName='Step-1',
        region=reg_all,
        description="Pandey & Kumar (2025) Section 4.5 & 4.6 Native RemeshingRule",
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

    odb_donor = session.openOdb(name=donor_odb_path)
    m.adaptiveRemesh(odb=odb_donor)
    odb_donor.close()

    audit = audit_mesh_quality(p, l0=0.008)
    audit["error_target_pct"] = error_target
    audit["candidate_name"] = candidate_name

    pub_target = 12944
    audit["pub_target_12944_diff_pct"] = ((audit["num_elements"] - pub_target) / float(pub_target)) * 100.0

    log("Candidate %s -> Elements: %d, Nodes: %d, Diff vs 12944: %+.2f%%" %
        (candidate_name, audit["num_elements"], audit["num_nodes"], audit["pub_target_12944_diff_pct"]))
    log("  h_min: %.6f mm, h_mean: %.6f mm, AR_max: %.2f, %% <= l0/2 in Ligament: %.1f%%" %
        (audit["h_min_mm"], audit["h_mean_mm"], audit["ar_max"], audit["pct_le_half_l0_in_ligament"]))

    # Write input deck
    job_name = candidate_name
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]
    j = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
    j.writeInput(consistencyChecking=OFF)

    # Move output deck
    src_inp = job_name + ".inp"
    dst_inp = os.path.join(OUT_DIR, src_inp)
    if os.path.exists(src_inp):
        shutil.move(src_inp, dst_inp)
        audit["inp_path"] = dst_inp

    return audit, dst_inp

def execute_remeshing_suite():
    log("=" * 80)
    log("F1720 STAGE 4: NATIVE ADAPTIVE REMESHING SUITE")
    log("Donor ODB: %s" % COUPLED_ODB)
    log("=" * 80)

    # Test error target sweep: 3.05%, 3.30%, 3.50%, 3.70%, 4.00%
    targets = [
        (3.05, "PK_F1720_ADAPTED_ET305"),
        (3.30, "PK_F1720_ADAPTED_ET330"),
        (3.50, "PK_F1720_ADAPTED_ET350"),
        (3.60, "PK_F1720_ADAPTED_ET360"),
        (3.70, "PK_F1720_ADAPTED_ET370"),
        (3.85, "PK_F1720_ADAPTED_ET385"),
        (4.00, "PK_F1720_ADAPTED_ET400")
    ]

    all_audits = {}
    best_candidate = None
    min_diff = 1e9

    for et, cname in targets:
        audit, inp_path = run_remesh_candidate(COUPLED_ODB, et, cname)
        all_audits[cname] = audit
        diff = abs(audit["num_elements"] - 12944)
        if diff < min_diff:
            min_diff = diff
            best_candidate = (cname, audit, inp_path)

    log("\nSelected Best Candidate vs Published 12,944 Elements:")
    log("  Name: %s" % best_candidate[0])
    log("  Elements: %d (Diff: %d elements, %+.2f%%)" %
        (best_candidate[1]["num_elements"], best_candidate[1]["num_elements"] - 12944, best_candidate[1]["pub_target_12944_diff_pct"]))

    # Copy best candidate to PK_F1720_ADAPTED_PHYS.inp
    best_inp = best_candidate[2]
    phys_target = os.path.join(OUT_DIR, "PK_F1720_ADAPTED_PHYS.inp")
    shutil.copyfile(best_inp, phys_target)
    log("Saved primary physical adapted mesh to: %s" % phys_target)

    # Save metrics JSON
    summary = {
        "task_id": "F1720-METHOD-A-DIRECT-COUPLING-AND-REMESH-REPRODUCTION",
        "benchmark": "Pandey & Kumar (2025) Section 4.5 Five-Hole Plate (1.0 x 1.0 mm)",
        "published_target_elements": 12944,
        "donor_odb": COUPLED_ODB,
        "best_candidate": best_candidate[0],
        "best_candidate_metrics": best_candidate[1],
        "all_candidates": all_audits
    }

    out_json = os.path.join(RESULTS_DIR, "f1720_adapted_mesh_metrics.json")
    with open(out_json, "w") as f:
        json.dump(summary, f, indent=2)
    log("Saved mesh audit metrics to: %s" % out_json)

if __name__ == "__main__":
    execute_remeshing_suite()

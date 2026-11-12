# -*- coding: utf-8 -*-
"""
scripts/remeshing/test_f1723_remesh_parameters.py
================================================
Systematic exploration of native Abaqus adaptive remeshing parameters for Task F1723.
Investigates:
  1. outputFrequency (LAST_INCREMENT vs ALL_INCREMENTS)
  2. Step choice (Step-1 vs Step-2)
  3. errorTarget sweep (1.0% to 3.5%)
  4. Base seed size / maxElementSize (0.020, 0.025, 0.030)
Evaluates refinement in ALL FOUR ligaments:
  Lig 1 (h1 <-> h2), Lig 2 (h2 <-> h3), Lig 3 (h3 <-> h4), Lig 4 (h4 <-> h5)
and checks for excessive bulk spreading.
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
OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "215_f1723_adapted_mesh_study")

if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

def build_cad_model(m, model_name, seed_size, max_size):
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

    p.seedPart(size=seed_size, deviationFactor=0.1, minSizeFactor=0.1)
    p.setMeshControls(regions=p.faces, elemShape=QUAD_DOMINATED, technique=FREE)
    elem_cpe4 = mesh.ElemType(elemCode=CPE4, elemLibrary=STANDARD)
    elem_cpe3 = mesh.ElemType(elemCode=CPE3, elemLibrary=STANDARD)
    p.setElementType(regions=(p.faces,), elemTypes=(elem_cpe4, elem_cpe3))
    p.generateMesh()

    p.Set(name='ALL_ELEM', faces=p.faces)

    a = m.rootAssembly
    inst = a.Instance(name='PART-1-1', part=p, dependent=ON)
    a.Set(name='ALL_ELEM', faces=inst.faces)

    # Define steps matching donor ODB
    m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0)
    m.StaticStep(name='Step-2', previous='Step-1', timePeriod=1.0)
    return p, a, inst

def audit_mesh_detailed(p, l0=0.008):
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

    lig1_h = []
    lig2_h = []
    lig3_h = []
    lig4_h = []
    bulk_h = []

    for el in elements:
        pts = [nodes[i].coordinates for i in el.connectivity]
        poly_x = [pt[0] for pt in pts]
        poly_y = [pt[1] for pt in pts]
        n_pts = len(pts)

        area = 0.5 * abs(sum([poly_x[i]*poly_y[(i+1)%n_pts] - poly_y[i]*poly_x[(i+1)%n_pts] for i in range(n_pts)]))
        if area <= 0.0:
            positive_jacobians = False
        areas.append(area)
        h_eq = math.sqrt(area)
        h_eqs.append(h_eq)

        edge_lens = [math.hypot(poly_x[(i+1)%n_pts] - poly_x[i], poly_y[(i+1)%n_pts] - poly_y[i]) for i in range(n_pts)]
        max_edge = max(edge_lens)
        min_edge = max(1e-12, min(edge_lens))
        ar = max_edge / min_edge
        aspect_ratios.append(ar)

        cx = sum(poly_x) / float(n_pts)
        cy = sum(poly_y) / float(n_pts)

        # Four inter-hole ligaments:
        if 0.08 <= cx <= 0.27 and 0.40 <= cy <= 0.56:
            lig1_h.append(h_eq)
        elif 0.42 <= cx <= 0.57 and 0.42 <= cy <= 0.58:
            lig2_h.append(h_eq)
        elif 0.63 <= cx <= 0.70 and 0.48 <= cy <= 0.56:
            lig3_h.append(h_eq)
        elif 0.80 <= cx <= 0.95 and 0.42 <= cy <= 0.54:
            lig4_h.append(h_eq)
        else:
            bulk_h.append(h_eq)

    def stats(arr):
        if not arr:
            return {"count": 0, "min_h": 0.0, "mean_h": 0.0, "max_h": 0.0, "pct_le_l0": 0.0, "pct_le_half_l0": 0.0}
        return {
            "count": len(arr),
            "min_h": min(arr),
            "mean_h": sum(arr) / len(arr),
            "max_h": max(arr),
            "pct_le_l0": 100.0 * len([h for h in arr if h <= l0]) / float(len(arr)),
            "pct_le_half_l0": 100.0 * len([h for h in arr if h <= l0 / 2.0]) / float(len(arr))
        }

    return {
        "num_elements": n_elems,
        "num_nodes": n_nodes,
        "num_quads": n_quads,
        "num_tris": n_tris,
        "quad_percentage": 100.0 * n_quads / n_elems,
        "positive_jacobians": positive_jacobians,
        "ar_max": max(aspect_ratios) if aspect_ratios else 0.0,
        "ar_mean": sum(aspect_ratios) / len(aspect_ratios) if aspect_ratios else 0.0,
        "global_h": stats(h_eqs),
        "lig1_h1_h2": stats(lig1_h),
        "lig2_h2_h3": stats(lig2_h),
        "lig3_h3_h4": stats(lig3_h),
        "lig4_h4_h5": stats(lig4_h),
        "bulk": stats(bulk_h)
    }

def run_test_case(case_name, donor_odb, step_name, out_freq, err_tgt, seed_size, max_size, min_size=0.001):
    model_name = "M_" + case_name
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)

    p, a, inst = build_cad_model(m, model_name, seed_size, max_size)
    reg_all = inst.sets['ALL_ELEM']

    m.RemeshingRule(
        name="RR_" + case_name,
        stepName=step_name,
        region=reg_all,
        description="F1723 Test RemeshingRule",
        variables=('MISESERI',),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=err_tgt,
        specifyMinSize=True,
        specifyMaxSize=True,
        minElementSize=min_size,
        maxElementSize=max_size,
        elementCountLimit=None,
        coarseningFactor=NOT_ALLOWED,
        refinementFactor=10,
        outputFrequency=out_freq
    )

    odb_donor = session.openOdb(name=donor_odb)
    m.adaptiveRemesh(odb=odb_donor)
    odb_donor.close()

    res = audit_mesh_detailed(p)
    res["case_name"] = case_name
    res["step_name"] = step_name
    res["out_freq"] = "ALL_INCREMENTS" if out_freq == ALL_INCREMENTS else "LAST_INCREMENT"
    res["err_tgt"] = err_tgt
    res["seed_size"] = seed_size
    res["max_size"] = max_size
    res["min_size"] = min_size
    pub_target = 12944
    res["diff_vs_pub_pct"] = ((res["num_elements"] - pub_target) / float(pub_target)) * 100.0

    print("CASE: %-22s | Els: %5d (%+5.1f%%) | Lig1: %3d (%.1f%% <= l0) | Lig2: %3d (%.1f%% <= l0) | Lig3: %3d (%.1f%% <= l0/2) | Bulk: %5d (mean h=%.4f)" %
          (case_name, res["num_elements"], res["diff_vs_pub_pct"],
           res["lig1_h1_h2"]["count"], res["lig1_h1_h2"]["pct_le_l0"],
           res["lig2_h2_h3"]["count"], res["lig2_h2_h3"]["pct_le_l0"],
           res["lig3_h3_h4"]["count"], res["lig3_h3_h4"]["pct_le_half_l0"],
           res["bulk"]["count"], res["bulk"]["mean_h"]))

    return res

print("=" * 100)
print("F1723 PARAMETER EXPLORATION SUITE")
print("=" * 100)

cases = [
    # 1. Baseline F1720 configuration (Step-1, LAST_INCREMENT, seed=0.02, max=0.02, err=3.5%)
    ("BASE_S1_LAST_E35", COUPLED_ODB, 'Step-1', LAST_INCREMENT, 3.50, 0.020, 0.020),
    # 2. Lower error targets with LAST_INCREMENT (seed=0.02, max=0.02)
    ("S1_LAST_E25", COUPLED_ODB, 'Step-1', LAST_INCREMENT, 2.50, 0.020, 0.020),
    ("S1_LAST_E20", COUPLED_ODB, 'Step-1', LAST_INCREMENT, 2.00, 0.020, 0.020),
    ("S1_LAST_E15", COUPLED_ODB, 'Step-1', LAST_INCREMENT, 1.50, 0.020, 0.020),
    # 3. ALL_INCREMENTS per Listing 1 of published paper (Step-1)
    ("S1_ALL_E35", COUPLED_ODB, 'Step-1', ALL_INCREMENTS, 3.50, 0.020, 0.020),
    ("S1_ALL_E25", COUPLED_ODB, 'Step-1', ALL_INCREMENTS, 2.50, 0.020, 0.020),
    ("S1_ALL_E20", COUPLED_ODB, 'Step-1', ALL_INCREMENTS, 2.00, 0.020, 0.020),
    ("S1_ALL_E15", COUPLED_ODB, 'Step-1', ALL_INCREMENTS, 1.50, 0.020, 0.020),
    # 4. Step-2 (fracture propagation step)
    ("S2_LAST_E35", COUPLED_ODB, 'Step-2', LAST_INCREMENT, 3.50, 0.020, 0.020),
    ("S2_LAST_E25", COUPLED_ODB, 'Step-2', LAST_INCREMENT, 2.50, 0.020, 0.020),
    ("S2_ALL_E35", COUPLED_ODB, 'Step-2', ALL_INCREMENTS, 3.50, 0.020, 0.020),
    ("S2_ALL_E25", COUPLED_ODB, 'Step-2', ALL_INCREMENTS, 2.50, 0.020, 0.020),
    # 5. Base seed = 0.025 mm / 0.030 mm with lower errorTarget
    ("S1_ALL_SEED25_E20", COUPLED_ODB, 'Step-1', ALL_INCREMENTS, 2.00, 0.025, 0.025),
    ("S1_ALL_SEED25_E15", COUPLED_ODB, 'Step-1', ALL_INCREMENTS, 1.50, 0.025, 0.025),
    ("S1_ALL_SEED30_E15", COUPLED_ODB, 'Step-1', ALL_INCREMENTS, 1.50, 0.030, 0.030),
    ("S1_ALL_SEED30_E10", COUPLED_ODB, 'Step-1', ALL_INCREMENTS, 1.00, 0.030, 0.030),
]

results = []
out_json = os.path.join(OUT_DIR, "f1723_parameter_exploration_results.json")

for c in cases:
    try:
        r = run_test_case(c[0], c[1], c[2], c[3], c[4], c[5], c[6])
        results.append(r)
        with open(out_json, "w") as f:
            json.dump(results, f, indent=2)
    except Exception as e:
        print("ERROR running case %s: %s" % (c[0], str(e)))

print("\nResults saved to: %s" % out_json)

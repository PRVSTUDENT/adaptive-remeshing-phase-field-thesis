# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_seven_hole_parity_search.py
================================================
Searches higher error targets (4.5% to 6.5%) with and without coarsening
to identify the exact error target matching Pandey & Kumar's 15,714-element benchmark.
"""

from abaqus import *
from abaqusConstants import *
import regionToolset
import mesh
import os
import math
import json

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
STUDY_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study")
COARSE_ODB = os.path.join(STUDY_DIR, "PK_F1726_SEVEN_HOLE_COARSE.odb")
OUT_JSON = os.path.join(STUDY_DIR, "f1726_parity_search_results.json")
LOG_PATH = os.path.join(STUDY_DIR, "f1726_parity_search_log.txt")

log_f = open(LOG_PATH, "w")

def log(msg):
    log_f.write(str(msg) + "\n")
    log_f.flush()
    print(msg)

log("Starting Seven-Hole Parity Search...")
odb_donor = session.openOdb(COARSE_ODB)

def build_cad_model(m, seed_size):
    s = m.ConstrainedSketch(name='__profile__', sheetSize=2.0)
    s.Line(point1=(0.0, 0.0), point2=(1.0, 0.0))
    s.Line(point1=(1.0, 0.0), point2=(1.0, 1.0))
    s.Line(point1=(1.0, 1.0), point2=(0.0, 1.0))
    s.Line(point1=(0.0, 1.0), point2=(0.0, 0.0))

    s.CircleByCenterPerimeter(center=(0.15, 0.40), point1=(0.25, 0.40))
    s.CircleByCenterPerimeter(center=(0.50, 0.55), point1=(0.60, 0.55))
    s.CircleByCenterPerimeter(center=(0.85, 0.50), point1=(0.95, 0.50))
    s.CircleByCenterPerimeter(center=(0.30, 0.60), point1=(0.35, 0.60))
    s.CircleByCenterPerimeter(center=(0.70, 0.60), point1=(0.75, 0.60))
    s.CircleByCenterPerimeter(center=(0.40, 0.35), point1=(0.45, 0.35))
    s.CircleByCenterPerimeter(center=(0.65, 0.35), point1=(0.70, 0.35))

    p = m.Part(name='SevenHolePlate', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches['__profile__']

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

    m.StaticStep(name='Step-1', previous='Initial', timePeriod=1.0)
    m.StaticStep(name='Step-2', previous='Step-1', timePeriod=1.0)
    return p, a, inst

def dist_to_segments(px, py, segs):
    min_d = 1e9
    for (x1, y1), (x2, y2) in segs:
        dx, dy = x2 - x1, y2 - y1
        l2 = dx*dx + dy*dy
        t = max(0.0, min(1.0, ((px - x1)*dx + (py - y1)*dy) / l2)) if l2 > 0 else 0.0
        d = math.hypot(px - (x1 + t*dx), py - (y1 + t*dy))
        if d < min_d:
            min_d = d
    return min_d

def audit_mesh_detailed(p, l0=0.008):
    elements = p.elements
    nodes = p.nodes

    n_elems = len(elements)
    n_nodes = len(nodes)
    n_quads = len([e for e in elements if len(e.connectivity) == 4])
    n_tris = len([e for e in elements if len(e.connectivity) == 3])

    areas = []
    h_eqs = []
    aspect_ratios = []
    positive_jacobians = True

    upper_segments = [
        ((0.15, 0.40), (0.30, 0.60)),
        ((0.30, 0.60), (0.50, 0.55)),
        ((0.50, 0.55), (0.70, 0.60)),
        ((0.70, 0.60), (0.85, 0.50))
    ]

    upper_h = []
    lower_h6_h = []
    lower_h7_h = []
    bulk_h = []

    for el in elements:
        pts = [nodes[i].coordinates for i in el.connectivity]
        px = [pt[0] for pt in pts]
        py = [pt[1] for pt in pts]
        n_pts = len(pts)

        area = 0.5 * abs(sum([px[i]*py[(i+1)%n_pts] - py[i]*px[(i+1)%n_pts] for i in range(n_pts)]))
        if area <= 0.0:
            positive_jacobians = False
        areas.append(area)

        h_eq = math.sqrt(area) * 1000.0
        h_eqs.append(h_eq)

        edges = [math.hypot(px[(i+1)%n_pts] - px[i], py[(i+1)%n_pts] - py[i]) for i in range(n_pts)]
        ar = max(edges) / max(min(edges), 1e-12)
        aspect_ratios.append(ar)

        cx = sum(px) / float(n_pts)
        cy = sum(py) / float(n_pts)

        d_upper = dist_to_segments(cx, cy, upper_segments)
        d_h6 = math.hypot(cx - 0.40, cy - 0.35) - 0.05
        d_h7 = math.hypot(cx - 0.65, cy - 0.35) - 0.05

        if d_upper <= 0.040:
            upper_h.append(h_eq)
        elif abs(d_h6) <= 0.040:
            lower_h6_h.append(h_eq)
        elif abs(d_h7) <= 0.040:
            lower_h7_h.append(h_eq)
        else:
            bulk_h.append(h_eq)

    def stats(arr):
        if not arr:
            return {"count": 0, "min": 0.0, "mean": 0.0, "median": 0.0, "max": 0.0, "le_l0": 0, "pct_le_l0": 0.0}
        s = sorted(arr)
        n = len(s)
        le_l0 = len([v for v in s if v <= l0 * 1000.0])
        return {
            "count": n,
            "min": round(s[0], 2),
            "mean": round(sum(s)/float(n), 2),
            "median": round(s[n//2], 2),
            "max": round(s[-1], 2),
            "le_l0": le_l0,
            "pct_le_l0": round(100.0 * le_l0 / float(n), 1)
        }

    return {
        "num_elements": n_elems,
        "num_nodes": n_nodes,
        "num_quads": n_quads,
        "num_tris": n_tris,
        "quad_percentage": round(100.0 * n_quads / float(n_elems), 2),
        "positive_jacobians": positive_jacobians,
        "ar_max": round(max(aspect_ratios), 3) if aspect_ratios else 0.0,
        "ar_mean": round(sum(aspect_ratios) / float(len(aspect_ratios)), 3) if aspect_ratios else 0.0,
        "global_h": stats(h_eqs),
        "upper_corridor": stats(upper_h),
        "lower_h6": stats(lower_h6_h),
        "lower_h7": stats(lower_h7_h),
        "bulk": stats(bulk_h)
    }

def run_case(case_name, step_name, sizing_method, err_tgt, coarsening_fac, seed_size, max_size, min_size=0.001):
    model_name = "M_" + case_name
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)
    p, a, inst = build_cad_model(m, seed_size)
    reg_all = inst.sets['ALL_ELEM']

    rule_kwargs = {
        "name": "RR_" + case_name,
        "stepName": step_name,
        "region": reg_all,
        "variables": ('MISESERI',),
        "sizingMethod": sizing_method,
        "specifyMinSize": True,
        "minElementSize": min_size,
        "specifyMaxSize": True,
        "maxElementSize": max_size,
        "coarseningFactor": coarsening_fac,
        "refinementFactor": 10,
        "outputFrequency": ALL_INCREMENTS
    }

    if sizing_method == UNIFORM_ERROR:
        rule_kwargs["errorTarget"] = err_tgt

    m.RemeshingRule(**rule_kwargs)
    m.adaptiveRemesh(odb=odb_donor)
    metrics = audit_mesh_detailed(p)

    job_name = case_name
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]
    j = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
    j.writeInput(consistencyChecking=OFF)

    src_inp = job_name + ".inp"
    dst_inp = os.path.join(STUDY_DIR, src_inp)
    if os.path.exists(src_inp) and src_inp != dst_inp:
        if os.path.exists(dst_inp):
            os.remove(dst_inp)
        os.rename(src_inp, dst_inp)

    parity = round(100.0 * (metrics['num_elements'] - 15714) / 15714.0, 2)
    log("Case %s: %d elems (Parity: %+0.2f%% vs 15,714, %0.2f%% quads) | Upper=%d (mean=%0.2f um, %0.1f%% <= l0) | LowerH6=%d (mean=%0.2f um) | Bulk=%d (mean=%0.2f um)" % (
        case_name, metrics['num_elements'], parity, metrics['quad_percentage'],
        metrics['upper_corridor']['count'], metrics['upper_corridor']['mean'], metrics['upper_corridor']['pct_le_l0'],
        metrics['lower_h6']['count'], metrics['lower_h6']['mean'],
        metrics['bulk']['count'], metrics['bulk']['mean']
    ))
    metrics["parity_pct"] = parity
    metrics["case_name"] = case_name
    return metrics

parity_cases = [
    # Search range 4.5% to 6.5% on Step 2
    ("F1726_S2_ET450", "Step-2", UNIFORM_ERROR, 4.50, NOT_ALLOWED, 0.020, 0.030),
    ("F1726_S2_ET500", "Step-2", UNIFORM_ERROR, 5.00, NOT_ALLOWED, 0.020, 0.030),
    ("F1726_S2_ET550", "Step-2", UNIFORM_ERROR, 5.50, NOT_ALLOWED, 0.020, 0.030),
    ("F1726_S2_ET575", "Step-2", UNIFORM_ERROR, 5.75, NOT_ALLOWED, 0.020, 0.030),
    ("F1726_S2_ET600", "Step-2", UNIFORM_ERROR, 6.00, NOT_ALLOWED, 0.020, 0.030),
    ("F1726_S2_ET625", "Step-2", UNIFORM_ERROR, 6.25, NOT_ALLOWED, 0.020, 0.030),
    ("F1726_S2_ET650", "Step-2", UNIFORM_ERROR, 6.50, NOT_ALLOWED, 0.020, 0.030),

    # With Coarsening
    ("F1726_S2_COARSEN_ET450", "Step-2", UNIFORM_ERROR, 4.50, DEFAULT_LIMIT, 0.020, 0.030),
    ("F1726_S2_COARSEN_ET500", "Step-2", UNIFORM_ERROR, 5.00, DEFAULT_LIMIT, 0.020, 0.030),
    ("F1726_S2_COARSEN_ET550", "Step-2", UNIFORM_ERROR, 5.50, DEFAULT_LIMIT, 0.020, 0.030),
    ("F1726_S2_COARSEN_ET575", "Step-2", UNIFORM_ERROR, 5.75, DEFAULT_LIMIT, 0.020, 0.030),
    ("F1726_S2_COARSEN_ET600", "Step-2", UNIFORM_ERROR, 6.00, DEFAULT_LIMIT, 0.020, 0.030),
]

parity_results = {}
for cargs in parity_cases:
    try:
        res = run_case(*cargs)
        parity_results[cargs[0]] = res
    except Exception as e:
        log("ERROR running case %s: %s" % (cargs[0], str(e)))

with open(OUT_JSON, "w") as jf:
    json.dump(parity_results, jf, indent=2)

log("\n=== PARITY SEARCH COMPLETE ===")
log("Saved quantitative results to: " + OUT_JSON)
log_f.close()

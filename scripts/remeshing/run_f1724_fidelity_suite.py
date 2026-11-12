from abaqus import *
from abaqusConstants import *
import regionToolset
import mesh
import os
import math
import json
import numpy as np

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
COUPLED_ODB = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "213_f1720_coarse_coupled", "PK_F1720_COARSE_COUPLED.odb")
OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "216_f1724_fidelity_study")

if not os.path.exists(OUT_DIR):
    os.makedirs(OUT_DIR)

out_log = os.path.join(OUT_DIR, "f1724_fidelity_suite_log.txt")
log_f = open(out_log, "w")

def log(msg):
    log_f.write(str(msg) + "\n")
    log_f.flush()
    print(msg)

def build_cad_model(m, seed_size):
    s = m.ConstrainedSketch(name='__profile__', sheetSize=2.0)
    s.Line(point1=(0.0, 0.0), point2=(1.0, 0.0))
    s.Line(point1=(1.0, 0.0), point2=(1.0, 0.375))
    s.Arc3Points(point1=(1.0, 0.375), point2=(1.0, 0.525), point3=(0.925, 0.450))
    s.Line(point1=(1.0, 0.525), point2=(1.0, 1.0))
    s.Line(point1=(1.0, 1.0), point2=(0.0, 1.0))
    s.Line(point1=(0.0, 1.0), point2=(0.0, 0.60))
    s.Arc3Points(point1=(0.0, 0.600), point2=(0.0, 0.400), point3=(0.100, 0.500))
    s.Line(point1=(0.0, 0.400), point2=(0.0, 0.0))

    s.CircleByCenterPerimeter(center=(0.35, 0.45), point1=(0.45, 0.45))
    s.CircleByCenterPerimeter(center=(0.60, 0.55), point1=(0.65, 0.55))
    s.CircleByCenterPerimeter(center=(0.75, 0.50), point1=(0.825, 0.50))

    p = m.Part(name='FiveHolePlate', dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
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
        px = [pt[0] for pt in pts]
        py = [pt[1] for pt in pts]
        n_pts = len(pts)

        area = 0.5 * abs(sum([px[i]*py[(i+1)%n_pts] - py[i]*px[(i+1)%n_pts] for i in range(n_pts)]))
        if area <= 0.0:
            positive_jacobians = False
        areas.append(area)
        h_eq = math.sqrt(area)
        h_eqs.append(h_eq * 1000.0) # um

        edge_lens = [math.hypot(px[(i+1)%n_pts] - px[i], py[(i+1)%n_pts] - py[i]) for i in range(n_pts)]
        max_edge = max(edge_lens)
        min_edge = max(1e-12, min(edge_lens))
        ar = max_edge / min_edge
        aspect_ratios.append(ar)

        cx = sum(px) / float(n_pts)
        cy = sum(py) / float(n_pts)

        if 0.08 <= cx <= 0.27 and 0.40 <= cy <= 0.56:
            lig1_h.append(h_eq * 1000.0)
        elif 0.42 <= cx <= 0.57 and 0.42 <= cy <= 0.58:
            lig2_h.append(h_eq * 1000.0)
        elif 0.63 <= cx <= 0.69 and 0.48 <= cy <= 0.56:
            lig3_h.append(h_eq * 1000.0)
        elif 0.81 <= cx <= 0.94 and 0.40 <= cy <= 0.55:
            lig4_h.append(h_eq * 1000.0)
        elif cy > 0.70 or cy < 0.30:
            bulk_h.append(h_eq * 1000.0)

    def stats(arr):
        if not arr:
            return {"min": 0.0, "max": 0.0, "mean": 0.0, "median": 0.0, "std": 0.0, "frac_le_l0": 0.0, "frac_le_half_l0": 0.0, "count": 0}
        s_arr = sorted(arr)
        n = len(arr)
        mean_v = sum(arr) / float(n)
        med_v = s_arr[n // 2]
        std_v = math.sqrt(sum([(x - mean_v)**2 for x in arr]) / float(n))
        f_l0 = sum([1 for x in arr if x <= (l0 * 1000.0)]) / float(n)
        f_hl0 = sum([1 for x in arr if x <= (l0 * 500.0)]) / float(n)
        return {
            "min": round(min(arr), 3),
            "max": round(max(arr), 3),
            "mean": round(mean_v, 3),
            "median": round(med_v, 3),
            "std": round(std_v, 3),
            "frac_le_l0": round(f_l0, 4),
            "frac_le_half_l0": round(f_hl0, 4),
            "count": n
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
        "lig1_h1_h2": stats(lig1_h),
        "lig2_h2_h3": stats(lig2_h),
        "lig3_h3_h4": stats(lig3_h),
        "lig4_h4_h5": stats(lig4_h),
        "bulk": stats(bulk_h)
    }

def run_case(case_name, step_name, sizing_method, err_tgt, max_err_tgt, min_err_tgt, coarsening_fac, seed_size, max_size, min_size=0.001):
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
    elif sizing_method == MINIMUM_MAXIMUM:
        rule_kwargs["maxSolutionErrorTarget"] = max_err_tgt
        rule_kwargs["minSolutionErrorTarget"] = min_err_tgt

    m.RemeshingRule(**rule_kwargs)
    m.adaptiveRemesh(odb=odb_donor)
    metrics = audit_mesh_detailed(p)

    job_name = case_name
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]
    j = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
    j.writeInput(consistencyChecking=OFF)

    src_inp = job_name + ".inp"
    dst_inp = os.path.join(OUT_DIR, src_inp)
    if os.path.exists(src_inp) and src_inp != dst_inp:
        if os.path.exists(dst_inp):
            os.remove(dst_inp)
        os.rename(src_inp, dst_inp)

    log(f"Case {case_name}: {metrics['num_elements']} elems ({metrics['quad_percentage']}% quads), Lig1={metrics['lig1_h1_h2']['count']} elems, Lig2={metrics['lig2_h2_h3']['count']} elems, Bulk mean_h={metrics['bulk']['mean']} um")
    return metrics

cases_to_run = [
    # 1. Exact Method A: Uniform Error on Step-2 with fine sweeps around target
    ("F1724_EXACT_S2_ET330", "Step-2", UNIFORM_ERROR, 3.30, None, None, NOT_ALLOWED, 0.020, 0.020),
    ("F1724_EXACT_S2_ET335", "Step-2", UNIFORM_ERROR, 3.35, None, None, NOT_ALLOWED, 0.020, 0.020),
    ("F1724_EXACT_S2_ET340", "Step-2", UNIFORM_ERROR, 3.40, None, None, NOT_ALLOWED, 0.020, 0.020),
    ("F1724_EXACT_S2_ET345", "Step-2", UNIFORM_ERROR, 3.45, None, None, NOT_ALLOWED, 0.020, 0.020),
    ("F1724_EXACT_S2_ET350", "Step-2", UNIFORM_ERROR, 3.50, None, None, NOT_ALLOWED, 0.020, 0.020),

    # 2. Maximum Size Sensitivity (Resolving the 0.02 vs 0.03 mm reported global size)
    ("F1724_MAXSIZE_025_ET340", "Step-2", UNIFORM_ERROR, 3.40, None, None, NOT_ALLOWED, 0.025, 0.025),
    ("F1724_MAXSIZE_030_ET340", "Step-2", UNIFORM_ERROR, 3.40, None, None, NOT_ALLOWED, 0.030, 0.030),
    ("F1724_MAXSIZE_030_ET280", "Step-2", UNIFORM_ERROR, 2.80, None, None, NOT_ALLOWED, 0.030, 0.030),
    ("F1724_MAXSIZE_030_ET250", "Step-2", UNIFORM_ERROR, 2.50, None, None, NOT_ALLOWED, 0.030, 0.030),

    # 3. Controlled Diagnostic: Coarsening in low-error bulk regions
    ("F1724_COARSEN_DEF_ET340", "Step-2", UNIFORM_ERROR, 3.40, None, None, DEFAULT_LIMIT, 0.020, 0.030),
    ("F1724_COARSEN_DEF_ET300", "Step-2", UNIFORM_ERROR, 3.00, None, None, DEFAULT_LIMIT, 0.020, 0.030),

    # 4. Controlled Diagnostic: MINIMUM_MAXIMUM sizing (Threshold-based)
    ("F1724_MINMAX_TGT_4_1",  "Step-2", MINIMUM_MAXIMUM, None, 4.0, 1.0, NOT_ALLOWED, 0.020, 0.020),
    ("F1724_MINMAX_TGT_5_2",  "Step-2", MINIMUM_MAXIMUM, None, 5.0, 2.0, NOT_ALLOWED, 0.020, 0.020),
    ("F1724_MINMAX_TGT_6_2",  "Step-2", MINIMUM_MAXIMUM, None, 6.0, 2.0, NOT_ALLOWED, 0.020, 0.020),
]

log("Opening coarse coupled donor ODB...")
odb_donor = session.openOdb(name=COUPLED_ODB)

all_results = {}
for c in cases_to_run:
    c_name, s_name, method, e_tgt, max_e, min_e, c_fac, s_size, m_size = c
    res = run_case(c_name, s_name, method, e_tgt, max_e, min_e, c_fac, s_size, m_size)
    all_results[c_name] = {
        "config": {
            "case_name": c_name,
            "step_name": s_name,
            "sizing_method": str(method),
            "err_tgt": e_tgt,
            "max_err_tgt": max_e,
            "min_err_tgt": min_e,
            "coarsening_factor": str(c_fac),
            "seed_size": s_size,
            "max_size": m_size
        },
        "metrics": res
    }

odb_donor.close()

# Save JSON results
json_path = os.path.join(OUT_DIR, "f1724_fidelity_suite_results.json")
with open(json_path, "w") as jf:
    json.dump(all_results, jf, indent=2)

log(f"All {len(cases_to_run)} cases executed and results saved to {json_path}!")
log_f.close()

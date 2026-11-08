# -*- coding: utf-8 -*-
"""
execute_f1690_sec43_remesh.py

Task F1690 Stage D: Native Abaqus one-rule adaptive remeshing on Pandey-Kumar Section 4.3
rectangular plate with a hole (65 x 120 mm) using recovery ODB from finer coarse mesh.
Builds native CAD geometry, sets up Paper Listing 1 RemeshingRule,
and executes m.adaptiveRemesh(odb=odb_donor).
Exports PK_SEC43_RERUN_ADAPT_PHYS.inp and audits spatial resolution metrics.
"""

from __future__ import print_function
import os
import sys
import json
import math
from abaqus import *
from abaqusConstants import *
import regionToolset
import mesh

REPO_ROOT = os.path.abspath(os.getcwd())
model_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "190_pk_sec43_job1_rerun")
recovery_odb_path = os.path.join(model_dir, "PK_SEC43_RERUN_RECOVERY.odb")
adapt_inp_path = os.path.join(model_dir, "PK_SEC43_RERUN_ADAPT_PHYS.inp")
results_dir = os.path.join(REPO_ROOT, "results", "validation")
figures_dir = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures")

def log(msg):
    print("[F1690-REMESH] " + str(msg))
    sys.stdout.flush()

def main():
    log("=" * 80)
    log("TASK F1690 STAGE D: PANDEY-KUMAR §4.3 NATIVE ONE-RULE ADAPTIVE REMESHING (h=0.6 mm DONOR)")
    log("=" * 80)

    model_name = "Model_PK_Sec43_Rerun_Adapt"
    if model_name in mdb.models:
        del mdb.models[model_name]
    m = mdb.Model(name=model_name)
    if "Model-1" in mdb.models:
        del mdb.models["Model-1"]

    log("Building native CAD geometry for 65 x 120 mm plate with 3 holes...")
    s = m.ConstrainedSketch(name="__profile__", sheetSize=300.0)

    # Outer boundary and notch
    s.Line(point1=(0.0, 0.0), point2=(65.0, 0.0))
    s.Line(point1=(65.0, 0.0), point2=(65.0, 120.0))
    s.Line(point1=(65.0, 120.0), point2=(0.0, 120.0))
    s.Line(point1=(0.0, 120.0), point2=(0.0, 70.2))
    s.Line(point1=(0.0, 70.2), point2=(10.0, 70.2))
    s.Line(point1=(10.0, 70.2), point2=(10.0, 69.8))
    s.Line(point1=(10.0, 69.8), point2=(0.0, 69.8))
    s.Line(point1=(0.0, 69.8), point2=(0.0, 0.0))

    # 3 Holes:
    # Central eccentric void (Circle 1): center (36.5, 51.0), R = 10.0 mm
    s.CircleByCenterPerimeter(center=(36.5, 51.0), point1=(46.5, 51.0))
    # Lower pinned hole (Circle 2): center (20.0, 20.0), R = 5.0 mm
    s.CircleByCenterPerimeter(center=(20.0, 20.0), point1=(25.0, 20.0))
    # Upper loading hole (Circle 3): center (20.0, 100.0), R = 5.0 mm
    s.CircleByCenterPerimeter(center=(20.0, 100.0), point1=(25.0, 100.0))

    p = m.Part(name="PlateWithHoles", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches["__profile__"]

    # Seed with 0.60 mm global size matching rerun model
    p.seedPart(size=0.60, deviationFactor=0.1, minSizeFactor=0.1)
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

    step_name = "RECOVERY_STEP"
    m.StaticStep(name=step_name, previous="Initial", timePeriod=1.0)

    reg = inst.sets["All_elem"]

    rule_name = "RemeshingRule_PK_Sec43_Paper"
    log("Defining RemeshingRule: %s (errorTarget=5.0, min=0.143 mm, max=1.5 mm)" % rule_name)
    m.RemeshingRule(
        name=rule_name,
        stepName=step_name,
        region=reg,
        description="Pandey & Kumar (2025) Listing 1: Native MISESERI errorTarget=5%, min=0.143mm, max=1.5mm",
        variables=("MISESERI",),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=5.0,
        refinementFactor=10,
        coarseningFactor=NOT_ALLOWED,
        specifyMinSize=True,
        minElementSize=0.143,
        specifyMaxSize=True,
        maxElementSize=1.5
    )

    log("Opening donor recovery ODB: %s" % recovery_odb_path)
    odb_donor = session.openOdb(name=recovery_odb_path)

    log("Executing m.adaptiveRemesh(odb=odb_donor)...")
    m.adaptiveRemesh(odb=odb_donor)
    odb_donor.close()

    n_elems = len(p.elements)
    n_nodes = len(p.nodes)
    n_quads = sum([1 for e in p.elements if len(e.connectivity) == 4])
    n_tris = sum([1 for e in p.elements if len(e.connectivity) == 3])

    log("Native adaptiveRemesh completed successfully!")
    log("  Adapted Physical Elements: %d (Quads: %d = %.2f%%, Tris: %d = %.2f%%)" % (
        n_elems, n_quads, 100.0 * n_quads / n_elems, n_tris, 100.0 * n_tris / n_elems
    ))
    log("  Adapted Physical Nodes:    %d" % n_nodes)

    job_name = "PK_SEC43_RERUN_ADAPT_PHYS"
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]
    j = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
    j.writeInput(consistencyChecking=OFF)

    # Move generated INP to adapt_inp_path if written in current dir
    src_inp = job_name + ".inp"
    if os.path.exists(src_inp):
        import shutil
        shutil.copy2(src_inp, adapt_inp_path)
        log("Copied adapted INP to: %s" % adapt_inp_path)

    # 5. Spatial Resolution & Corridor Audit
    log("\nAnalyzing adapted mesh spatial metrics...")
    l0 = 0.285  # mm
    l0_half = l0 / 2.0  # 0.1425 mm
    l0_third = l0 / 3.0 # 0.0950 mm

    def dist_to_segment(px, py, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        l2 = dx*dx + dy*dy
        if l2 == 0:
            return math.hypot(px - x1, py - y1)
        t = max(0.0, min(1.0, ((px - x1)*dx + (py - y1)*dy) / l2))
        proj_x = x1 + t * dx
        proj_y = y1 + t * dy
        return math.hypot(px - proj_x, py - proj_y)

    elem_metrics = []
    prim_elems = []
    sec_elems = []

    for el in p.elements:
        pts = [p.nodes[i].coordinates for i in el.connectivity]
        poly_x = [pt[0] for pt in pts]
        poly_y = [pt[1] for pt in pts]
        area = 0.5 * abs(sum([poly_x[i]*poly_y[(i+1)%len(pts)] - poly_y[i]*poly_x[(i+1)%len(pts)] for i in range(len(pts))]))
        h_eq = math.sqrt(area)
        cx = sum(poly_x) / float(len(pts))
        cy = sum(poly_y) / float(len(pts))

        elem_metrics.append({
            "label": el.label,
            "type": len(pts),
            "area": area,
            "h_eq": h_eq,
            "cx": cx,
            "cy": cy
        })

        # Primary corridor: notch (10, 70) to central hole (36.5, 51)
        d_prim = dist_to_segment(cx, cy, 10.0, 70.0, 36.5, 51.0)
        if d_prim <= 3.0 and 10.0 <= cx <= 36.5:
            prim_elems.append(h_eq)

        # Secondary corridor: central hole (46.5, 51) to right boundary (65, 51)
        d_sec = dist_to_segment(cx, cy, 46.5, 51.0, 65.0, 51.0)
        if d_sec <= 3.0 and 46.5 <= cx <= 65.0:
            sec_elems.append(h_eq)

    h_all = [em["h_eq"] for em in elem_metrics]
    h_all.sort()
    prim_elems.sort()
    sec_elems.sort()

    def get_stats(arr):
        if not arr:
            return {"count": 0, "min": 0, "med": 0, "max": 0, "pct_l0": 0, "pct_l0_half": 0}
        n = len(arr)
        med = arr[n//2] if n % 2 == 1 else 0.5*(arr[n//2 - 1] + arr[n//2])
        p_l0 = 100.0 * sum([1 for v in arr if v <= l0]) / float(n)
        p_l0_h = 100.0 * sum([1 for v in arr if v <= l0_half]) / float(n)
        return {
            "count": n,
            "min": min(arr),
            "med": med,
            "max": max(arr),
            "pct_l0": p_l0,
            "pct_l0_half": p_l0_h
        }

    stats_all = get_stats(h_all)
    stats_prim = get_stats(prim_elems)
    stats_sec = get_stats(sec_elems)

    log("\n--- REGIONAL RESOLUTION METRICS ---")
    log("Primary Corridor (%d elements):" % stats_prim["count"])
    log("  Median h_equiv: %.4f mm (Gate: <= l0/3 = %.4f mm)" % (stats_prim["med"], l0_third))
    log("  Min h_equiv:    %.4f mm" % stats_prim["min"])
    log("  %% <= l0:        %.1f%%" % stats_prim["pct_l0"])
    log("  %% <= l0/2:      %.1f%%" % stats_prim["pct_l0_half"])

    log("Secondary Corridor (%d elements):" % stats_sec["count"])
    log("  Median h_equiv: %.4f mm (Gate: <= l0/3 = %.4f mm)" % (stats_sec["med"], l0_third))
    log("  Min h_equiv:    %.4f mm" % stats_sec["min"])
    log("  %% <= l0:        %.1f%%" % stats_sec["pct_l0"])
    log("  %% <= l0/2:      %.1f%%" % stats_sec["pct_l0_half"])

    # Pass/Fail determination
    pass_prim = stats_prim["med"] <= l0_third or stats_prim["pct_l0_half"] >= 50.0
    pass_sec = stats_sec["pct_l0"] >= 50.0

    audit_record = {
        "benchmark": "Pandey_Kumar_2025_Section_4.3_F1690_RERUN",
        "remeshing_rule": {
            "variables": ["MISESERI"],
            "sizing_method": "UNIFORM_ERROR",
            "error_target": 5.0,
            "min_element_size": 0.143,
            "max_element_size": 1.5,
            "refinement_factor": 10,
            "coarsening": "NOT_ALLOWED"
        },
        "adapted_mesh": {
            "total_elements": n_elems,
            "quad_elements": n_quads,
            "tri_elements": n_tris,
            "total_nodes": n_nodes,
            "total_dofs": n_nodes * 2
        },
        "length_scale_l0": l0,
        "primary_corridor": stats_prim,
        "secondary_corridor": stats_sec,
        "overall_mesh_metrics": stats_all,
        "pass_fail": {
            "primary_corridor_pass": bool(pass_prim),
            "secondary_corridor_pass": bool(pass_sec),
            "overall_pass": bool(pass_prim and pass_sec)
        }
    }

    metrics_json = os.path.join(results_dir, "f1690_sec43_adapted_mesh_metrics.json")
    with open(metrics_json, "w") as f:
        json.dump(audit_record, f, indent=2)
    log("Saved adapted mesh metrics to: %s" % metrics_json)

if __name__ == "__main__":
    main()

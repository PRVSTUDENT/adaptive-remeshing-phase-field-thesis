# -*- coding: utf-8 -*-
"""
execute_f1694_sec43_midprop_remesh.py
=====================================
Task F1694 Stage 3: Native Abaqus one-rule adaptive remeshing on Pandey-Kumar
Section 4.3 benchmark using Donor (b): Secondary Mid-Propagation recovery
(PK_SEC43_STAGGERED_RECOVERY_SEC_MIDPROP.odb at uy = 0.300 mm).

Builds native CAD geometry, seeds with 1.50 mm coarse size, defines Listing 1
RemeshingRule (errorTarget=5.0%, min=0.143 mm, max=1.5 mm), and executes
m.adaptiveRemesh(odb=odb_donor).

Exports PK_SEC43_STAGGERED_ADAPT_BEST_DONOR.inp and outputs
f1694_sec43_adapted_mesh_best_donor_metrics.json.
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
import mesh

def log(msg):
    print("[F1694-BEST-DONOR-REMESH] " + str(msg))
    sys.stdout.flush()

def main():
    log("=" * 80)
    log("TASK F1694 STAGE 3: ADAPTIVE REMESHING FROM BEST DONOR (SEC_MIDPROP, uy=0.300mm)")
    log("=" * 80)

    repo_root = os.path.abspath(os.getcwd())
    model_dir = os.path.join(repo_root, "models", "pandey_kumar_mode1", "192_pk_sec43_staggered_job1")
    odb_path = os.path.join(model_dir, "PK_SEC43_STAGGERED_RECOVERY_SEC_MIDPROP.odb")

    if not os.path.exists(odb_path):
        raise IOError("Donor ODB not found at: %s" % odb_path)

    log("Using donor ODB: %s" % odb_path)

    donor_step_name = "RECOVERY_STEP"

    model_name = "Model_PK_Sec43_BestDonor_Adapt"
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
    # Central eccentric void: center (36.5, 51.0), R = 10.0 mm
    s.CircleByCenterPerimeter(center=(36.5, 51.0), point1=(46.5, 51.0))
    # Lower pinned hole: center (20.0, 20.0), R = 5.0 mm
    s.CircleByCenterPerimeter(center=(20.0, 20.0), point1=(25.0, 20.0))
    # Upper loading hole: center (20.0, 100.0), R = 5.0 mm
    s.CircleByCenterPerimeter(center=(20.0, 100.0), point1=(25.0, 100.0))

    p = m.Part(name="PlateWithHoles", dimensionality=TWO_D_PLANAR, type=DEFORMABLE_BODY)
    p.BaseShell(sketch=s)
    del m.sketches["__profile__"]

    # Seed with 1.50 mm coarse global size matching paper
    log("Seeding part with 1.50 mm global size...")
    p.seedPart(size=1.50, deviationFactor=0.1, minSizeFactor=0.1)
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

    # Step definition matching ODB step name
    m.StaticStep(name=donor_step_name, previous="Initial", timePeriod=1.0)

    reg = inst.sets["All_elem"]

    rule_name = "RemeshingRule_PK_Sec43_Listing1"
    log("Defining RemeshingRule: %s (errorTarget=5.0, min=0.143 mm, max=1.5 mm)" % rule_name)
    m.RemeshingRule(
        name=rule_name,
        stepName=donor_step_name,
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

    log("Opening donor ODB for adaptiveRemesh: %s" % odb_path)
    odb_donor = session.openOdb(name=odb_path)

    log("Executing m.adaptiveRemesh(odb=odb_donor)...")
    m.adaptiveRemesh(odb=odb_donor)
    odb_donor.close()

    n_elems = len(p.elements)
    n_nodes = len(p.nodes)
    n_quads = sum([1 for e in p.elements if len(e.connectivity) == 4])
    n_tris = sum([1 for e in p.elements if len(e.connectivity) == 3])
    total_dofs = n_nodes * 2

    log("Native adaptiveRemesh completed successfully!")
    log("  Adapted Physical Elements: %d (Quads: %d = %.2f%%, Tris: %d = %.2f%%)" % (
        n_elems, n_quads, 100.0 * n_quads / n_elems, n_tris, 100.0 * n_tris / n_elems
    ))
    log("  Adapted Physical Nodes:    %d (Total DOFs: %d)" % (n_nodes, total_dofs))

    # Write adapted input deck
    job_name = "PK_SEC43_STAGGERED_ADAPT_BEST_DONOR"
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]
    j = mdb.Job(name=job_name, model=model_name, type=ANALYSIS)
    j.writeInput(consistencyChecking=OFF)

    src_inp = job_name + ".inp"
    if os.path.exists(src_inp):
        shutil.copy2(src_inp, os.path.join(model_dir, src_inp))
        log("Copied adapted INP to: %s" % os.path.join(model_dir, src_inp))

    # Spatial Resolution & Corridor Audit
    log("\nAnalyzing adapted mesh spatial metrics...")
    l0 = 0.285  # mm
    l0_half = l0 / 2.0   # 0.1425 mm
    l0_third = l0 / 3.0  # 0.0950 mm

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

        # Primary corridor: centerline from notch tip (10.0, 70.0) to central hole (26.5, 51.0)
        d_prim = dist_to_segment(cx, cy, 10.0, 70.0, 26.5, 51.0)
        if d_prim <= 2.0 * l0:
            prim_elems.append(h_eq)

        # Secondary corridor: centerline from central hole (46.5, 51.0) to right boundary (65.0, 51.0)
        d_sec = dist_to_segment(cx, cy, 46.5, 51.0, 65.0, 51.0)
        if d_sec <= 2.0 * l0:
            sec_elems.append(h_eq)

    def stats(vals):
        if not vals:
            return {"count": 0, "min": 0.0, "med": 0.0, "pct_l0_half": 0.0, "pct_l0_third": 0.0}
        s_vals = sorted(vals)
        n = len(s_vals)
        med = s_vals[n//2] if n % 2 == 1 else 0.5 * (s_vals[n//2 - 1] + s_vals[n//2])
        p_half = 100.0 * sum([1 for v in s_vals if v <= l0_half]) / float(n)
        p_third = 100.0 * sum([1 for v in s_vals if v <= l0_third]) / float(n)
        return {
            "count": n,
            "min": round(min(s_vals), 4),
            "med": round(med, 4),
            "pct_l0_half": round(p_half, 2),
            "pct_l0_third": round(p_third, 2)
        }

    prim_stats = stats(prim_elems)
    sec_stats = stats(sec_elems)

    fine_elems = [e for e in elem_metrics if e["h_eq"] <= l0_half]
    total_area = sum([e["area"] for e in elem_metrics])
    fine_area = sum([e["area"] for e in fine_elems])

    in_corridor_fine = []
    for e in fine_elems:
        cx, cy = e["cx"], e["cy"]
        d_prim = dist_to_segment(cx, cy, 10.0, 70.0, 26.5, 51.0)
        d_sec = dist_to_segment(cx, cy, 46.5, 51.0, 65.0, 51.0)
        if d_prim <= 2.0 * l0 or d_sec <= 2.0 * l0:
            in_corridor_fine.append(e)

    in_corridor_area = sum([e["area"] for e in in_corridor_fine])
    waste_area = fine_area - in_corridor_area
    rel_waste = 100.0 * waste_area / fine_area if fine_area > 0 else 0.0

    transverse_dists = []
    for e in fine_elems:
        cx, cy = e["cx"], e["cy"]
        d_prim = dist_to_segment(cx, cy, 10.0, 70.0, 26.5, 51.0)
        d_sec = dist_to_segment(cx, cy, 46.5, 51.0, 65.0, 51.0)
        transverse_dists.append(min(d_prim, d_sec))

    if transverse_dists:
        transverse_dists.sort()
        idx_90 = int(0.90 * len(transverse_dists))
        w_90 = 2.0 * transverse_dists[min(idx_90, len(transverse_dists)-1)]
    else:
        w_90 = 0.0

    log("Corridor Resolution Audit:")
    log("  Primary corridor elements:   %d" % prim_stats["count"])
    log("    h_min: %.4f mm, h_med: %.4f mm, pct <= l0/2: %.2f%%, pct <= l0/3: %.2f%%" % (
        prim_stats["min"], prim_stats["med"], prim_stats["pct_l0_half"], prim_stats["pct_l0_third"]
    ))
    log("  Secondary corridor elements: %d" % sec_stats["count"])
    log("    h_min: %.4f mm, h_med: %.4f mm, pct <= l0/2: %.2f%%, pct <= l0/3: %.2f%%" % (
        sec_stats["min"], sec_stats["med"], sec_stats["pct_l0_half"], sec_stats["pct_l0_third"]
    ))
    log("  Transverse width W_90%%:      %.4f mm" % w_90)
    log("  Relative waste area:         %.2f%%" % rel_waste)

    metrics_out = {
        "task_id": "F1694-PK-SEC43-MISESERI-FIELDS-AND-MULTI-DONOR-REMESH",
        "donor_case": "Donor (b): Secondary Mid-Propagation (uy = 0.300 mm)",
        "adapted_mesh_inp": job_name + ".inp",
        "donor_odb": odb_path,
        "donor_step": donor_step_name,
        "elements_total": n_elems,
        "elements_quads": n_quads,
        "elements_tris": n_tris,
        "pct_quads": round(100.0 * n_quads / n_elems, 2),
        "pct_tris": round(100.0 * n_tris / n_elems, 2),
        "nodes_total": n_nodes,
        "total_dofs": total_dofs,
        "l0_mm": l0,
        "l0_half_mm": l0_half,
        "l0_third_mm": l0_third,
        "primary_corridor": prim_stats,
        "secondary_corridor": sec_stats,
        "w_90_mm": round(w_90, 4),
        "fine_area_mm2": round(fine_area, 4),
        "waste_area_mm2": round(waste_area, 4),
        "relative_waste_pct": round(rel_waste, 2),
        "paper_comparison": {
            "paper_figure_16b": "Dual-branch refined mesh from notch to hole and hole to right boundary",
            "paper_element_count": "Pandey & Kumar (2025) do not report an adapted element count for Section 4.3",
            "primary_refined": prim_stats["pct_l0_half"] > 0,
            "secondary_refined": sec_stats["pct_l0_half"] > 0
        }
    }

    out_json = "f1694_sec43_adapted_mesh_best_donor_metrics.json"
    dest_paths = [
        os.path.join(repo_root, "results", "validation", out_json),
        os.path.join(model_dir, out_json)
    ]
    for dp in dest_paths:
        with open(dp, "w") as fp:
            json.dump(metrics_out, fp, indent=2)
        log("Saved copy to: %s" % dp)

    log("Saved adapted mesh metrics to: %s" % out_json)
    return 0

if __name__ == "__main__":
    main()

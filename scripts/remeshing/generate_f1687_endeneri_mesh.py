"""
scripts/remeshing/generate_f1687_endeneri_mesh.py
=================================================
Task F1687 Stage B: ENDENERI Terminal-Frame Control Mesh Generation & Audit.
Uses authentic PK_HOLE_MULTISTEP_RECOVERY.odb, step RECOVERY_TERMINAL (Frame 337).
Rule: Single native RemeshingRule with variables=('ENDENERI',), errorTarget=5.0%.
Measures metrics using exact canonical h_equiv pipeline against crack centerlines.
"""

import os
import sys
import math
import json
import numpy as np

from abaqus import *
from abaqusConstants import *
from caeModules import *

def log(msg):
    print(f"[F1687-ENDENERI] {msg}")

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

def export_inp(model, inp_path):
    job_name = "TEMP_F1687_ENDENERI_JOB"
    if job_name in mdb.jobs:
        del mdb.jobs[job_name]
    j = mdb.Job(name=job_name, model=model.name, type=ANALYSIS)
    j.writeInput(consistencyChecking=OFF)
    raw_inp = f"{job_name}.inp"
    if os.path.exists(inp_path):
        os.remove(inp_path)
    os.rename(raw_inp, inp_path)
    log(f"Exported INP to {inp_path}")

def compute_jacobian_and_aspect(pts):
    # Shoelace Area
    n = len(pts)
    area = 0.0
    for i in range(n):
        j = (i + 1) % n
        area += pts[i][0] * pts[j][1] - pts[j][0] * pts[i][1]
    area = 0.5 * abs(area)

    # Edge lengths
    edges = []
    for i in range(n):
        j = (i + 1) % n
        edges.append(math.hypot(pts[j][0] - pts[i][0], pts[j][1] - pts[i][1]))
    max_edge = max(edges)
    min_edge = min(edges)
    aspect_ratio = (max_edge / min_edge) if min_edge > 0 else 100.0

    # Scaled Jacobian
    if n == 4:
        corner_jacs = []
        for i in range(4):
            p_prev = pts[(i - 1) % 4]
            p_curr = pts[i]
            p_next = pts[(i + 1) % 4]
            v1 = (p_next[0] - p_curr[0], p_next[1] - p_curr[1])
            v2 = (p_prev[0] - p_curr[0], p_prev[1] - p_curr[1])
            cross = v1[0] * v2[1] - v1[1] * v2[0]
            l1 = math.hypot(v1[0], v1[1])
            l2 = math.hypot(v2[0], v2[1])
            if l1 * l2 > 0:
                corner_jacs.append(abs(cross) / (l1 * l2))
            else:
                corner_jacs.append(0.0)
        scaled_jac = min(corner_jacs)
    elif n == 3:
        p0, p1, p2 = pts
        v1 = (p1[0] - p0[0], p1[1] - p0[1])
        v2 = (p2[0] - p0[0], p2[1] - p0[1])
        cross = abs(v1[0] * v2[1] - v1[1] * v2[0])
        l1 = math.hypot(v1[0], v1[1])
        l2 = math.hypot(v2[0], v2[1])
        scaled_jac = (cross / (l1 * l2)) if (l1 * l2 > 0) else 0.0
    else:
        scaled_jac = 1.0

    return area, max_edge, scaled_jac, aspect_ratio

def compute_point_to_polyline_dist(px, py, polyline):
    min_dist = float("inf")
    for i in range(len(polyline) - 1):
        x1, y1 = polyline[i]
        x2, y2 = polyline[i+1]
        dx = x2 - x1
        dy = y2 - y1
        l2 = dx*dx + dy*dy
        if l2 == 0.0:
            d = math.hypot(px - x1, py - y1)
        else:
            t = max(0.0, min(1.0, ((px - x1)*dx + (py - y1)*dy) / l2))
            proj_x = x1 + t * dx
            proj_y = y1 + t * dy
            d = math.hypot(px - proj_x, py - proj_y)
        if d < min_dist:
            min_dist = d
    return min_dist

def main():
    odb_path = os.path.abspath("runs/f1684_multistep_recovery/PK_HOLE_MULTISTEP_RECOVERY.odb")
    cand_dir = os.path.abspath("models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidates")
    os.makedirs(cand_dir, exist_ok=True)
    inp_path = os.path.join(cand_dir, "PK_HOLE_ENDENERI_TERM_PHYS.inp")

    centerline_path = "results/validation/f1684_crack_path_centerlines.json"
    with open(centerline_path, "r") as fp:
        cl_data = json.load(fp)
    primary_cl = cl_data["primary"]["points"]
    secondary_cl = cl_data["secondary"]["points"]

    log("Opening ODB: %s" % odb_path)
    odb = session.openOdb(name=odb_path)

    log("Building base CAD model...")
    model_name = "Model_Endeneri_5pct"
    m = build_base_cad_model(model_name)
    p = m.parts["PlateWithHole"]
    reg = m.rootAssembly.sets["All_elem"]

    log("Defining RemeshingRule on RECOVERY_TERMINAL with ENDENERI errorTarget=5.0%...")
    m.RemeshingRule(
        name="Rule_Endeneri_5pct",
        stepName="RECOVERY_TERMINAL",
        region=reg,
        description="F1687 Stage B: Terminal Frame ENDENERI Control (errorTarget=5.0%)",
        outputFrequency=ALL_INCREMENTS,
        variables=("ENDENERI",),
        sizingMethod=UNIFORM_ERROR,
        errorTarget=5.0,
        specifyMinSize=True,
        specifyMaxSize=True,
        minElementSize=0.0015,
        maxElementSize=0.0200,
        coarseningFactor=NOT_ALLOWED,
        refinementFactor=10
    )

    log("Calling adaptiveRemesh...")
    m.adaptiveRemesh(odb=odb)
    n_elems = len(p.elements)
    n_nodes = len(p.nodes)
    n_quads = sum([1 for e in p.elements if len(e.connectivity) == 4])
    n_tris = sum([1 for e in p.elements if len(e.connectivity) == 3])
    log(f"Remeshing complete: {n_elems} elements ({n_quads} quads, {n_tris} tris), {n_nodes} nodes.")

    export_inp(m, inp_path)

    # --------------------------------------------------------------------------
    # Audit Metrics under Canonical h_equiv
    # --------------------------------------------------------------------------
    log("Auditing adapted mesh metrics under canonical h_equiv...")
    nodes = {n.label: (n.coordinates[0], n.coordinates[1]) for n in p.nodes}
    
    centroids = []
    areas = []
    h_equivs = []
    h_edges = []
    scaled_jacs = []
    aspect_ratios = []

    for e in p.elements:
        pts = [nodes[nid] for nid in e.connectivity]
        cx = sum([pt[0] for pt in pts]) / float(len(pts))
        cy = sum([pt[1] for pt in pts]) / float(len(pts))
        centroids.append((cx, cy))

        area, max_edge, s_jac, asp = compute_jacobian_and_aspect(pts)
        areas.append(area)
        h_equivs.append(math.sqrt(area) * 1000.0) # um
        h_edges.append(max_edge * 1000.0) # um
        scaled_jacs.append(s_jac)
        aspect_ratios.append(asp)

    cents = np.array(centroids)
    h_equivs = np.array(h_equivs)
    h_edges = np.array(h_edges)
    areas = np.array(areas)
    scaled_jacs = np.array(scaled_jacs)
    aspect_ratios = np.array(aspect_ratios)

    total_area_mm2 = float(np.sum(areas))

    # Crack path distances (um)
    d_prim_um = np.array([compute_point_to_polyline_dist(c[0], c[1], primary_cl) * 1000.0 for c in cents])
    d_sec_um = np.array([compute_point_to_polyline_dist(c[0], c[1], secondary_cl) * 1000.0 for c in cents])
    d_min_um = np.minimum(d_prim_um, d_sec_um)

    l0_um = 7.50
    h_half_l0_um = 3.75
    h_third_l0_um = 2.50

    is_fine = h_equivs <= h_half_l0_um
    n_fine = int(np.sum(is_fine))

    in_prim_15 = d_prim_um <= 15.0
    in_sec_15 = d_sec_um <= 15.0
    in_any_15 = d_min_um <= 15.0

    fine_out_corridor = is_fine & (~in_any_15)
    waste_area_mm2 = float(np.sum(areas[fine_out_corridor]))
    total_fine_area_mm2 = float(np.sum(areas[is_fine]))
    waste_pct_rel = (waste_area_mm2 / total_fine_area_mm2 * 100.0) if total_fine_area_mm2 > 0 else 0.0
    waste_pct_domain = (waste_area_mm2 / total_area_mm2 * 100.0)

    # Transverse widths
    if n_fine > 0:
        fine_dists = d_min_um[is_fine]
        w50 = float(np.percentile(fine_dists, 50.0))
        w90 = float(np.percentile(fine_dists, 90.0))
    else:
        w50, w90 = 0.0, 0.0

    # Primary corridor (dist <= 15 um)
    h_prim_eq = h_equivs[in_prim_15]
    prim_n = len(h_prim_eq)
    prim_med_eq = float(np.median(h_prim_eq)) if prim_n > 0 else 0.0
    prim_pct_half_eq = float(np.sum(h_prim_eq <= h_half_l0_um) / float(prim_n) * 100.0) if prim_n > 0 else 0.0
    prim_pct_third_eq = float(np.sum(h_prim_eq <= h_third_l0_um) / float(prim_n) * 100.0) if prim_n > 0 else 0.0
    prim_pct_l0_eq = float(np.sum(h_prim_eq <= l0_um) / float(prim_n) * 100.0) if prim_n > 0 else 0.0
    prim_max_eq = float(np.max(h_prim_eq)) if prim_n > 0 else 0.0
    prim_min_eq = float(np.min(h_prim_eq)) if prim_n > 0 else 0.0

    # Secondary corridor (dist <= 15 um)
    h_sec_eq = h_equivs[in_sec_15]
    sec_n = len(h_sec_eq)
    sec_med_eq = float(np.median(h_sec_eq)) if sec_n > 0 else 0.0
    sec_pct_half_eq = float(np.sum(h_sec_eq <= h_half_l0_um) / float(sec_n) * 100.0) if sec_n > 0 else 0.0
    sec_pct_third_eq = float(np.sum(h_sec_eq <= h_third_l0_um) / float(sec_n) * 100.0) if sec_n > 0 else 0.0
    sec_pct_l0_eq = float(np.sum(h_sec_eq <= l0_um) / float(sec_n) * 100.0) if sec_n > 0 else 0.0
    sec_max_eq = float(np.max(h_sec_eq)) if sec_n > 0 else 0.0
    sec_min_eq = float(np.min(h_sec_eq)) if sec_n > 0 else 0.0

    # Criteria evaluation
    crit1_prim = (prim_med_eq <= h_third_l0_um) and (prim_pct_half_eq >= 75.0)
    crit2_sec = (sec_med_eq <= h_third_l0_um) and (sec_pct_half_eq >= 80.0)
    crit3_scale = (prim_max_eq <= l0_um) and (sec_max_eq <= l0_um)
    crit4_selectivity = (w90 <= 50.0) and (waste_pct_rel <= 70.0)
    overall_pass = crit1_prim and crit2_sec and crit3_scale and crit4_selectivity

    min_jac = float(np.min(scaled_jacs))
    max_asp = float(np.max(aspect_ratios))

    summary = {
        "candidate_name": "PK_HOLE_ENDENERI_TERM_PHYS",
        "description": "Terminal Frame ENDENERI Control (Frame 337, errorTarget=5.0%)",
        "total_elements": n_elems,
        "n_quads": n_quads,
        "n_tris": n_tris,
        "total_nodes": n_nodes,
        "total_dofs": 3 * n_nodes,
        "total_area_mm2": total_area_mm2,
        "min_scaled_jacobian": min_jac,
        "max_aspect_ratio": max_asp,
        "n_fine_elements": n_fine,
        "fine_area_mm2": total_fine_area_mm2,
        "waste_area_mm2": waste_area_mm2,
        "waste_pct_rel": waste_pct_rel,
        "waste_pct_domain": waste_pct_domain,
        "w50_um": w50,
        "w90_um": w90,
        "primary_corridor": {
            "n_elements": prim_n,
            "min_h_equiv_um": prim_min_eq,
            "med_h_equiv_um": prim_med_eq,
            "max_h_equiv_um": prim_max_eq,
            "pct_le_half_l0": prim_pct_half_eq,
            "pct_le_third_l0": prim_pct_third_eq,
            "pct_le_l0": prim_pct_l0_eq,
            "criterion_pass": crit1_prim
        },
        "secondary_corridor": {
            "n_elements": sec_n,
            "min_h_equiv_um": sec_min_eq,
            "med_h_equiv_um": sec_med_eq,
            "max_h_equiv_um": sec_max_eq,
            "pct_le_half_l0": sec_pct_half_eq,
            "pct_le_third_l0": sec_pct_third_eq,
            "pct_le_l0": sec_pct_l0_eq,
            "criterion_pass": crit2_sec
        },
        "criterion_3_scale_enclosure": crit3_scale,
        "criterion_4_selectivity": crit4_selectivity,
        "overall_pass": overall_pass,
        "h1_hypothesis_verdict": "PASS" if overall_pass else "FALSIFIED"
    }

    out_json = "results/validation/f1687_endeneri_candidate_audit.json"
    with open(out_json, "w") as fp:
        json.dump(summary, fp, indent=2)
    log(f"Audit saved to {out_json}")

    csv_path = "results/validation/f1687_endeneri_candidate_summary.csv"
    with open(csv_path, "w") as fp:
        fp.write("candidate,n_elems,dofs,waste_mm2,waste_rel_pct,w50_um,w90_um,prim_h_med_um,prim_pct_half,sec_h_med_um,sec_pct_half,min_jac,max_asp,crit1,crit2,crit3,crit4,overall_pass,h1_verdict\n")
        fp.write(f"PK_HOLE_ENDENERI_TERM_PHYS,{n_elems},{3*n_nodes},{waste_area_mm2:.6f},{waste_pct_rel:.2f},{w50:.2f},{w90:.2f},{prim_med_eq:.3f},{prim_pct_half_eq:.1f},{sec_med_eq:.3f},{sec_pct_half_eq:.1f},{min_jac:.4f},{max_asp:.2f},{crit1_prim},{crit2_sec},{crit3_scale},{crit4_selectivity},{overall_pass},{summary['h1_hypothesis_verdict']}\n")
    log(f"Summary CSV saved to {csv_path}")

    print("\n" + "=" * 90)
    print("STAGE B: ENDENERI TERMINAL-FRAME CONTROL RESULTS")
    print("=" * 90)
    print(f"Total Physical Elements: {n_elems} ({n_quads} quads, {n_tris} tris)")
    print(f"Total DOFs:              {3 * n_nodes}")
    print(f"Refinement Widths:       W50 = {w50:.2f} um, W90 = {w90:.2f} um")
    print(f"Fine-Element Waste:      Area = {waste_area_mm2:.6f} mm2, Relative Waste = {waste_pct_rel:.2f}%")
    print(f"Primary Corridor:        n = {prim_n}, median = {prim_med_eq:.3f} um, % <= l0/2 = {prim_pct_half_eq:.1f}%, max = {prim_max_eq:.3f} um (Crit 1: {crit1_prim})")
    print(f"Secondary Corridor:      n = {sec_n}, median = {sec_med_eq:.3f} um, % <= l0/2 = {sec_pct_half_eq:.1f}%, max = {sec_max_eq:.3f} um (Crit 2: {crit2_sec})")
    print(f"Scale Enclosure (Crit 3): {crit3_scale}")
    print(f"Selectivity Gate (Crit 4): {crit4_selectivity}")
    print(f"OVERALL PASS:            {overall_pass}")
    print(f"H1 HYPOTHESIS VERDICT:   {summary['h1_hypothesis_verdict']}")
    print("=" * 90)

if __name__ == "__main__":
    main()

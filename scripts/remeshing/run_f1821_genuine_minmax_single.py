# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1821_genuine_minmax_single.py
===================================================
Executes a single benchmark case under genuine Abaqus MINIMUM_MAXIMUM sizing
using the enhanced reusable_2d_adaptive_framework.py (SHA-256: 0578156E...).
Outputs:
  - Adapted physical mesh: PK_F1821_MINMAX_<CID>_ADAPT_PHYS.inp
  - Mesh quality audit and scientific resolution gates
  - Machine receipt: f1821_receipt_<cid>.json
"""
from __future__ import print_function
import os
import sys
import json
import math
import hashlib
import shutil
import time

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
framework_dir = os.path.join(REPO_ROOT, "scripts", "remeshing")
if framework_dir not in sys.path:
    sys.path.insert(0, framework_dir)

from reusable_2d_adaptive_framework import (
    AdaptiveConfig,
    AbaqusNativeRemeshingEngine,
    MeshQualityAuditEngine,
    get_geometry_adapter,
    py_sum
)


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()


def compute_body_sha256(inp_path):
    h = hashlib.sha256()
    with open(inp_path, "r") as f:
        for line in f:
            if line.startswith("**"):
                continue
            h.update(line.strip().encode("utf-8"))
            h.update(b"\n")
    return h.hexdigest().upper()


def to_repo_rel(path):
    if not path:
        return ""
    rel = os.path.relpath(path, REPO_ROOT)
    return rel.replace("\\", "/")


def point_to_segment_dist(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1
    l2 = dx*dx + dy*dy
    if l2 == 0:
        return math.sqrt((px - x1)**2 + (py - y1)**2)
    t = max(0.0, min(1.0, ((px - x1)*dx + (py - y1)*dy) / l2))
    proj_x = x1 + t * dx
    proj_y = y1 + t * dy
    return math.sqrt((px - proj_x)**2 + (py - proj_y)**2)


def point_to_polyline_dist(px, py, segments):
    return min(point_to_segment_dist(px, py, s[0][0], s[0][1], s[1][0], s[1][1]) for s in segments)


def run_minmax_case(cid, out_dir, max_err=1.0, min_err=5.0, bias=7):
    cases_meta = {
        "case_1": {
            "name": "Case 1: Mode-I Edge-Cracked Plate",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1812_case1_native_miseseri.json"),
            "donor_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "case1", "PK_CASE1_MULTISTATE_RECOVERY.odb"),
            "expected_donor_sha": "0A25CDFE64344BE9DF7C651802F46EBF3D6F85C445689BBD28DBA64157758117",
            "l0_mm": 0.0075,
            "segments": [((0.5, 0.5), (1.0, 0.5))]
        },
        "case_2": {
            "name": "Case 2: Mode-I Plate with Off-Axis Hole",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case2_native_miseseri.json"),
            "donor_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case2", "PK_HOLE_MULTISTATE_RECOVERY.odb"),
            "expected_donor_sha": "87E100CB40BD35B8844E29D4A5961BB7A3EC527AE0B2A5E1D807174903654EAD",
            "l0_mm": 0.0075,
            "segments": [((0.50, 0.50), (0.55, 0.55)), ((0.75, 0.55), (1.00, 0.65))]
        },
        "case_3": {
            "name": "Case 3: Notched Plate with Pins and Central Hole",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case3_native_miseseri.json"),
            "donor_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "259_f1809_multistate_recovery", "case3", "SEC43_MULTISTATE_RECOVERY.odb"),
            "expected_donor_sha": "C67C0DEE132B31B53FDF7C2DF4C1D232AD92D42E9AFB29F5CD8313C269CF9780",
            "l0_mm": 0.285,
            "segments": [((30.0, 60.0), (50.0, 60.0)), ((70.0, 60.0), (120.0, 60.0))]
        },
        "case_5": {
            "name": "Case 5: Square Plate with Seven Holes",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case5_native_miseseri.json"),
            "donor_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_COARSE.odb"),
            "expected_donor_sha": "CB673713FDE31593AE452A21BC05BFFC140BCCCE71F1D43D601EE17B43802B0E",
            "l0_mm": 0.0080,
            "segments": [
                ((0.0, 0.40), (0.15, 0.40)),
                ((0.15, 0.40), (0.30, 0.60)),
                ((0.30, 0.60), (0.50, 0.55)),
                ((0.50, 0.55), (0.70, 0.60)),
                ((0.70, 0.60), (0.85, 0.50))
            ]
        }
    }

    meta = cases_meta[cid]
    cname = meta["name"]
    cfg_file = meta["config_path"]
    donor_p = meta["donor_path"]
    exp_donor_sha = meta["expected_donor_sha"]
    l0 = meta["l0_mm"]
    segments = meta["segments"]

    print("\n" + "=" * 80)
    print("TASK F1821 GENUINE MINIMUM_MAXIMUM SIZING: %s (%s)" % (cid.upper(), cname))
    print("  Executing RemeshingRule with sizingMethod=MINIMUM_MAXIMUM")
    print("  max_solution_error_target = %.1f%%, min_solution_error_target = %.1f%%, mesh_bias = %d" % (max_err, min_err, bias))
    print("  Output dir: %s" % out_dir)
    print("=" * 80)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    actual_donor_sha = compute_sha256(donor_p)
    if actual_donor_sha != exp_donor_sha:
        raise RuntimeError("Donor hash mismatch! Expected: %s, Actual: %s" % (exp_donor_sha, actual_donor_sha))

    with open(cfg_file, "r") as f:
        cfg_data = json.load(f)

    # Configure genuine MINIMUM_MAXIMUM sizing parameters
    rr = cfg_data.get("remeshing_rule", cfg_data.get("remeshing", {}))
    rr["sizing_method"] = "MINIMUM_MAXIMUM"
    rr["max_solution_error_target"] = max_err
    rr["min_solution_error_target"] = min_err
    rr["mesh_bias"] = bias
    cfg_data["remeshing_rule"] = rr

    cfg = AdaptiveConfig(cfg_data)
    adapter = get_geometry_adapter(cfg)

    job_name = "PK_F1821_MINMAX_" + cid.upper()
    phys_inp = AbaqusNativeRemeshingEngine.execute_native_remesh(
        cfg, donor_p, out_dir, output_job_name=job_name + "_PHYS"
    )

    target_phys_inp = os.path.join(out_dir, job_name + "_ADAPT_PHYS.inp")
    if phys_inp != target_phys_inp:
        if os.path.exists(target_phys_inp):
            os.remove(target_phys_inp)
        shutil.copyfile(phys_inp, target_phys_inp)
        phys_inp = target_phys_inp

    # Audit mesh quality
    audit = MeshQualityAuditEngine.evaluate_mesh(phys_inp, l0_mm=l0, adapter=adapter)
    phys_sha = compute_sha256(phys_inp)
    phys_body_sha = compute_body_sha256(phys_inp)
    phys_size = os.path.getsize(phys_inp)

    total_el = audit["total_elements"]
    quad_el = audit["quad_count"]
    tri_el = audit["tri_count"]
    quad_pct = audit["quad_fraction_pct"]
    min_j = audit["min_det_j"]
    max_ar = audit["max_aspect_ratio"]
    coarsening_ratio = audit.get("refinement_ratio_far_to_core", 1.0)
    total_nodes = audit["total_nodes"]
    nominal_field_dofs = total_nodes * 3

    # Compute width metric
    nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(phys_inp)
    fine_elements = []
    for eid, conn in list(quads.items()) + list(tris.items()):
        pts = [nodes[nid] for nid in conn]
        cx = py_sum(p[0] for p in pts) / len(pts)
        cy = py_sum(p[1] for p in pts) / len(pts)
        n = len(pts)
        area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
        h = math.sqrt(area)
        if h <= l0 / 2.0 + 1e-9:
            d = point_to_polyline_dist(cx, cy, segments)
            fine_elements.append((cx, cy, h, d))

    n_fine = len(fine_elements)
    n_2l0 = py_sum(1 for e in fine_elements if e[3] <= 2.0 * l0 + 1e-9)
    n_3l0 = py_sum(1 for e in fine_elements if e[3] <= 3.0 * l0 + 1e-9)
    n_5l0 = py_sum(1 for e in fine_elements if e[3] <= 5.0 * l0 + 1e-9)
    f_2l0 = (float(n_2l0) / n_fine * 100.0) if n_fine > 0 else 0.0
    f_3l0 = (float(n_3l0) / n_fine * 100.0) if n_fine > 0 else 0.0
    f_5l0 = (float(n_5l0) / n_fine * 100.0) if n_fine > 0 else 0.0

    # Scientific gate evaluation
    scientific_gate_name = "NONE"
    scientific_gate_val = 0.0
    scientific_gate_status = "FAIL"

    if cid == "case_1":
        scientific_gate_name = "SCIENTIFIC_GATE_FULL_LIGAMENT"
        lig_elems = []
        for eid, conn in list(quads.items()) + list(tris.items()):
            pts = [nodes[nid] for nid in conn]
            cx = py_sum(p[0] for p in pts) / len(pts)
            cy = py_sum(p[1] for p in pts) / len(pts)
            if 0.50 <= cx <= 1.00 and 0.48 <= cy <= 0.52:
                n = len(pts)
                area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
                h = math.sqrt(area)
                lig_elems.append(h)
        n_lig = len(lig_elems)
        n_lig_half = py_sum(1 for h in lig_elems if h <= l0 / 2.0 + 1e-9)
        scientific_gate_val = (float(n_lig_half) / n_lig * 100.0) if n_lig > 0 else 0.0
        scientific_gate_status = "PASS" if scientific_gate_val >= 95.0 else "FAIL"

    elif cid == "case_2":
        scientific_gate_name = "SCIENTIFIC_GATE_OUTER_DISTAL"
        outer_elems = []
        for eid, conn in list(quads.items()) + list(tris.items()):
            pts = [nodes[nid] for nid in conn]
            cx = py_sum(p[0] for p in pts) / len(pts)
            cy = py_sum(p[1] for p in pts) / len(pts)
            if 0.90 <= cx <= 1.00 and 0.55 <= cy <= 0.75:
                n = len(pts)
                area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
                h = math.sqrt(area)
                outer_elems.append(h)
        n_outer = len(outer_elems)
        n_outer_half = py_sum(1 for h in outer_elems if h <= l0 / 2.0 + 1e-9)
        scientific_gate_val = (float(n_outer_half) / n_outer * 100.0) if n_outer > 0 else 0.0
        scientific_gate_status = "PASS" if scientific_gate_val >= 50.0 else "FAIL"

    elif cid == "case_3":
        scientific_gate_name = "SCIENTIFIC_GATE_SECONDARY_CORRIDOR"
        sec_elems = []
        for eid, conn in list(quads.items()) + list(tris.items()):
            pts = [nodes[nid] for nid in conn]
            cx = py_sum(p[0] for p in pts) / len(pts)
            cy = py_sum(p[1] for p in pts) / len(pts)
            if 36.5 <= cx <= 65.0 and 45.0 <= cy <= 65.0:
                n = len(pts)
                area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
                h = math.sqrt(area)
                sec_elems.append(h)
        n_sec = len(sec_elems)
        n_sec_l0 = py_sum(1 for h in sec_elems if h <= l0 + 1e-9)
        scientific_gate_val = (float(n_sec_l0) / n_sec * 100.0) if n_sec > 0 else 0.0
        scientific_gate_status = "PASS" if scientific_gate_val >= 90.0 else "FAIL"

    elif cid == "case_5":
        scientific_gate_name = "SCIENTIFIC_GATE_INTER_HOLE"
        inter_elems = []
        for eid, conn in list(quads.items()) + list(tris.items()):
            pts = [nodes[nid] for nid in conn]
            cx = py_sum(p[0] for p in pts) / len(pts)
            cy = py_sum(p[1] for p in pts) / len(pts)
            if 0.15 <= cx <= 0.85 and 0.45 <= cy <= 0.65:
                n = len(pts)
                area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
                h = math.sqrt(area)
                inter_elems.append(h)
        n_inter = len(inter_elems)
        n_inter_l0 = py_sum(1 for h in inter_elems if h <= l0 + 1e-9)
        scientific_gate_val = (float(n_inter_l0) / n_inter * 100.0) if n_inter > 0 else 0.0
        scientific_gate_status = "PASS" if scientific_gate_val >= 90.0 else "FAIL"

    # Quality gates
    gate_01 = "PASS" if audit["non_positive_jacobians"] == 0 else "FAIL"
    gate_02 = "PASS" if quad_pct >= 90.0 else "FAIL"
    gate_03 = "PASS" if max_ar <= 4.0 else "FAIL"
    gate_04 = "PASS" if (audit["min_corner_angle_deg"] >= 20.0 and audit["max_corner_angle_deg"] <= 160.0) else "FAIL"
    gate_05 = "PASS" if scientific_gate_status == "PASS" else "FAIL"
    gate_06 = "PASS" if coarsening_ratio >= 2.0 else "FAIL"
    el_budget = 80000 if cid in ("case_2", "case_3") else 30000
    gate_07 = "PASS" if total_el <= el_budget else "FAIL"

    res = {
        "case_id": cid,
        "name": cname,
        "sizing_method": "MINIMUM_MAXIMUM",
        "eta_max_pct": max_err,
        "eta_min_pct": min_err,
        "mesh_bias": bias,
        "physical_mesh_path": to_repo_rel(phys_inp),
        "physical_mesh_sha256": phys_sha,
        "physical_mesh_body_sha256": phys_body_sha,
        "physical_mesh_size_bytes": phys_size,
        "total_elements": total_el,
        "quad_elements": quad_el,
        "tri_elements": tri_el,
        "quad_fraction_pct": quad_pct,
        "total_nodes": total_nodes,
        "nominal_field_dofs": nominal_field_dofs,
        "min_det_j": min_j,
        "max_aspect_ratio": max_ar,
        "min_corner_angle_deg": audit["min_corner_angle_deg"],
        "max_corner_angle_deg": audit["max_corner_angle_deg"],
        "coarsening_ratio": coarsening_ratio,
        "scientific_gate_name": scientific_gate_name,
        "scientific_gate_value": scientific_gate_val,
        "scientific_gate_status": scientific_gate_status,
        "gates": {
            "GATE_01_JACOBIAN": gate_01,
            "GATE_02_QUAD_FRACTION": gate_02,
            "GATE_03_ASPECT_RATIO": gate_03,
            "GATE_04_CORNER_ANGLES": gate_04,
            "GATE_05_SCIENTIFIC_RESOLUTION": gate_05,
            "GATE_06_FAR_FIELD_COARSENING": gate_06,
            "GATE_07_ELEMENT_BUDGET": gate_07
        },
        "width_metrics": {
            "fine_elements_count": n_fine,
            "fine_elements_pct_of_total": (100.0 * n_fine / total_el) if total_el > 0 else 0.0,
            "within_2l0_count": n_2l0,
            "pct_within_2l0": f_2l0,
            "within_3l0_count": n_3l0,
            "pct_within_3l0": f_3l0,
            "within_5l0_count": n_5l0,
            "pct_within_5l0": f_5l0
        }
    }

    print("  Total Elements: %d (Quads: %d = %.2f%%, Tris: %d)" % (
        res["total_elements"], res["quad_elements"], res["quad_fraction_pct"], res["tri_elements"]
    ))
    print("  Min det(J): %.2e, Max AR: %.2f" % (res["min_det_j"], res["max_aspect_ratio"]))
    print("  Gate 06 Coarsening: %.2fx (Gate: %s)" % (coarsening_ratio, gate_06))
    print("  Scientific Gate (%s): %.2f%% (Gate: %s)" % (
        scientific_gate_name, scientific_gate_val, scientific_gate_status
    ))
    print("  Width metrics (h <= l0/2): Total fine = %d" % n_fine)
    print("    Within 2*l0: %d (%.2f%%)" % (n_2l0, f_2l0))
    print("    Within 3*l0: %d (%.2f%%)" % (n_3l0, f_3l0))
    print("    Within 5*l0: %d (%.2f%%)" % (n_5l0, f_5l0))

    receipt_path = os.path.join(out_dir, "f1821_receipt_" + cid + ".json")
    with open(receipt_path, "w") as f:
        json.dump(res, f, indent=2)

    return res


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: abaqus cae noGUI=run_f1821_genuine_minmax_single.py -- <cid> <out_dir> [max_err] [min_err] [bias]")
        sys.exit(1)
    cid = sys.argv[-2]
    out_dir = sys.argv[-1]
    run_minmax_case(cid, out_dir)

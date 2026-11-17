# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1834_single_target.py
============================================
Task F1834: Universal Framework Early-State Blowup Guard Remeshing Runner.
Executes a single benchmark case at a specified error target and donor path within
a fresh, isolated Abaqus CAE session:
- Loads benchmark configuration
- Overrides error_target to the specified value
- Executes native Abaqus adaptiveRemesh() via reusable_2d_adaptive_framework.py
- Generates target physical mesh .inp
- Performs complete finite element quality audit
- Computes case-specific critical metrics (full ligament bins, outer ligament, dual corridors)
- Computes refinement-band extent (width metric) and unnecessary fine-region area
- Writes audit receipt JSON using repo-relative paths
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


def run_target(cid, error_target, out_dir, job_name, custom_donor_path=None):
    t_remesh_start = time.time()
    cases_meta = {
        "case_1": {
            "name": "Case 1: Mode-I Edge-Cracked Plate (Method A.2 State-Consistent Multi-State)",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1812_case1_native_miseseri.json"),
            "l0_mm": 0.0075,
        },
        "case_2": {
            "name": "Case 2: Plate with an Off-Axis Hole (Method A.2 State-Consistent Multi-State)",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case2_native_miseseri.json"),
            "l0_mm": 0.0075,
        },
        "case_3": {
            "name": "Case 3: Notched Plate with Hole and Pins (Method A.2 State-Consistent Multi-State)",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case3_native_miseseri.json"),
            "l0_mm": 0.285,
        },
        "case_5": {
            "name": "Case 5: Plate with Seven Holes (Table 6 Parity)",
            "config_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case5_native_miseseri.json"),
            "l0_mm": 0.0080,
        }
    }

    if cid not in cases_meta:
        raise ValueError("Unknown case ID: %s" % cid)

    meta = cases_meta[cid]
    cname = meta["name"]
    cfg_file = meta["config_path"]
    donor_p = custom_donor_path
    l0 = meta["l0_mm"]

    print("=" * 80)
    print("RUNNING %s AT ERROR TARGET %.2f%%" % (cname.upper(), error_target))
    print("Output directory: %s" % out_dir)
    print("Job name:         %s" % job_name)
    print("Donor path:       %s" % donor_p)
    print("=" * 80)

    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    if not os.path.exists(donor_p):
        raise RuntimeError("Donor file does not exist: %s" % donor_p)
    actual_donor_sha = compute_sha256(donor_p)
    print("Donor ODB verified: %s (SHA: %s)" % (os.path.basename(donor_p), actual_donor_sha))

    # Load configuration
    with open(cfg_file, "r") as f:
        cfg_data = json.load(f)
    cfg = AdaptiveConfig(cfg_data)
    cfg.error_target = float(error_target)
    adapter = get_geometry_adapter(cfg)

    phys_inp = AbaqusNativeRemeshingEngine.execute_native_remesh(
        cfg, donor_p, out_dir, output_job_name=job_name + "_PHYS"
    )
    print("Generated physical mesh: %s" % phys_inp)

    target_phys_inp = os.path.join(out_dir, job_name + "_ADAPT_PHYS.inp")
    if phys_inp != target_phys_inp:
        if os.path.exists(target_phys_inp):
            os.remove(target_phys_inp)
        shutil.copyfile(phys_inp, target_phys_inp)
        phys_inp = target_phys_inp

    # Audit mesh
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

    print("  [AUDIT] Elements: %d (Quads: %d, Tris: %d, Quad %%: %.2f%%)" % (total_el, quad_el, tri_el, quad_pct))
    print("  [AUDIT] Min signed det(J): %g, Max AR: %.3f, Coarsening: %.2fx" % (min_j, max_ar, coarsening_ratio))

    crit_metrics = {}
    nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(phys_inp)

    scientific_gate = "UNKNOWN"
    scientific_gate_name = "NONE"

    # Compute element areas and centers for all elements
    elem_areas = {}
    elem_centers = {}
    elem_h = {}
    total_mesh_area = 0.0
    total_fine_area = 0.0  # h <= l0
    for eid, conn in list(quads.items()) + list(tris.items()):
        pts = [nodes[nid] for nid in conn]
        cx = py_sum(p[0] for p in pts) / len(pts)
        cy = py_sum(p[1] for p in pts) / len(pts)
        n = len(pts)
        area = 0.5 * abs(py_sum(pts[i][0] * pts[(i+1)%n][1] - pts[(i+1)%n][0] * pts[i][1] for i in range(n)))
        h = math.sqrt(area)
        elem_areas[eid] = area
        elem_centers[eid] = (cx, cy)
        elem_h[eid] = h
        total_mesh_area += area
        if h <= l0 + 1e-9:
            total_fine_area += area

    band_metrics = {
        "total_mesh_area_mm2": round(total_mesh_area, 6),
        "total_fine_area_mm2": round(total_fine_area, 6),
        "total_fine_elements": py_sum(1 for h in elem_h.values() if h <= l0 + 1e-9),
    }

    if cid == "case_1":
        scientific_gate_name = "SCIENTIFIC_GATE_FULL_LIGAMENT"
        lig_elems = []
        outer_elems = []
        bin_elems = {
            "bin_1": [], # 0.50 - 0.55
            "bin_2": [], # 0.55 - 0.60
            "bin_3": [], # 0.60 - 0.70
            "bin_4": [], # 0.70 - 0.80
            "bin_5": [], # 0.80 - 0.90
            "bin_6": []  # 0.90 - 1.00
        }
        corridor_fine_area = 0.0
        y_fine_in_ligament = []
        for eid, (cx, cy) in elem_centers.items():
            h = elem_h[eid]
            area = elem_areas[eid]
            if 0.50 <= cx <= 1.00 and 0.48 <= cy <= 0.52:
                lig_elems.append(h)
                if h <= l0 + 1e-9:
                    corridor_fine_area += area
                    y_fine_in_ligament.append(cy)
                if cx < 0.55:
                    bin_elems["bin_1"].append(h)
                elif cx < 0.60:
                    bin_elems["bin_2"].append(h)
                elif cx < 0.70:
                    bin_elems["bin_3"].append(h)
                elif cx < 0.80:
                    bin_elems["bin_4"].append(h)
                elif cx < 0.90:
                    bin_elems["bin_5"].append(h)
                    outer_elems.append(h)
                else:
                    bin_elems["bin_6"].append(h)
                    outer_elems.append(h)

        n_lig = len(lig_elems)
        pct_lig_l0 = (float(py_sum(1 for h in lig_elems if h <= l0 + 1e-9)) / n_lig * 100.0) if n_lig > 0 else 0.0
        pct_lig_l0_half = (float(py_sum(1 for h in lig_elems if h <= l0 / 2.0 + 1e-9)) / n_lig * 100.0) if n_lig > 0 else 0.0

        n_outer = len(outer_elems)
        pct_outer_l0_half = (float(py_sum(1 for h in outer_elems if h <= l0 / 2.0 + 1e-9)) / n_outer * 100.0) if n_outer > 0 else 0.0

        bins_audit = {}
        for b_name in sorted(bin_elems.keys()):
            b_list = bin_elems[b_name]
            nb = len(b_list)
            nb_l0 = py_sum(1 for h in b_list if h <= l0 + 1e-9)
            nb_half = py_sum(1 for h in b_list if h <= l0 / 2.0 + 1e-9)
            pct_b_l0 = (float(nb_l0) / nb * 100.0) if nb > 0 else 0.0
            pct_b_half = (float(nb_half) / nb * 100.0) if nb > 0 else 0.0
            min_h_b = min(b_list) * 1000.0 if nb > 0 else 0.0
            bins_audit[b_name] = {
                "count": nb,
                "pct_le_l0": pct_b_l0,
                "pct_le_l0_half": pct_b_half,
                "min_h_um": min_h_b
            }

        scientific_gate = "PASS" if (pct_lig_l0 >= 99.9 and pct_lig_l0_half >= 90.0) else "FAIL"
        unnecessary_fine_area = max(0.0, total_fine_area - corridor_fine_area)
        band_width_mm = corridor_fine_area / 0.50 if corridor_fine_area > 0 else 0.0

        band_metrics.update({
            "corridor_fine_area_mm2": round(corridor_fine_area, 6),
            "unnecessary_fine_area_mm2": round(unnecessary_fine_area, 6),
            "unnecessary_fine_fraction_pct": round(unnecessary_fine_area / total_fine_area * 100.0 if total_fine_area > 0 else 0.0, 2),
            "band_width_mm": round(band_width_mm, 6)
        })

        crit_metrics = {
            "ligament_elements": n_lig,
            "ligament_pct_le_l0": pct_lig_l0,
            "ligament_pct_le_l0_half": pct_lig_l0_half,
            "outer_ligament_count": n_outer,
            "outer_ligament_pct_le_l0_half": pct_outer_l0_half,
            "bins": bins_audit
        }
        print("  [CRITICAL] Full Ligament: %d, %%<=l0: %.2f%%, %%<=l0/2: %.2f%%, Outer %%<=l0/2: %.2f%% (Gate: %s)" % (
            n_lig, pct_lig_l0, pct_lig_l0_half, pct_outer_l0_half, scientific_gate
        ))
        print("  [BAND] Corridor Fine Area: %.4f mm^2, Unnecessary Fine Area: %.4f mm^2 (%.1f%%), Band Width: %.4f mm" % (
            corridor_fine_area, unnecessary_fine_area, band_metrics["unnecessary_fine_fraction_pct"], band_width_mm
        ))

    elif cid == "case_2":
        scientific_gate_name = "SCIENTIFIC_GATE_OUTER_DISTAL"
        distal_elems = []
        bin_elems = {1: [], 2: [], 3: [], 4: [], 5: []}
        distal_fine_area = 0.0
        pre_hole_fine_area = 0.0
        for eid, (cx, cy) in elem_centers.items():
            h = elem_h[eid]
            area = elem_areas[eid]
            if 0.75 <= cx <= 1.00 and 0.55 <= cy <= 0.75:
                distal_elems.append(h)
                if h <= l0 + 1e-9:
                    distal_fine_area += area
                if cx < 0.80:
                    bin_elems[1].append(h)
                elif cx < 0.85:
                    bin_elems[2].append(h)
                elif cx < 0.90:
                    bin_elems[3].append(h)
                elif cx < 0.95:
                    bin_elems[4].append(h)
                else:
                    bin_elems[5].append(h)
            elif 0.0 <= cx <= 0.55 and 0.48 <= cy <= 0.52:
                if h <= l0 + 1e-9:
                    pre_hole_fine_area += area

        n_dist = len(distal_elems)
        n_dist_l0 = py_sum(1 for h in distal_elems if h <= l0 + 1e-9)
        n_dist_l0_half = py_sum(1 for h in distal_elems if h <= l0 / 2.0 + 1e-9)
        pct_dist_l0 = (float(n_dist_l0) / n_dist * 100.0) if n_dist > 0 else 0.0
        pct_dist_l0_half = (float(n_dist_l0_half) / n_dist * 100.0) if n_dist > 0 else 0.0

        bins_audit = {}
        for b_idx in range(1, 6):
            b_list = bin_elems[b_idx]
            nb = len(b_list)
            nb_half = py_sum(1 for h in b_list if h <= l0 / 2.0 + 1e-9)
            pct_b_half = (float(nb_half) / nb * 100.0) if nb > 0 else 0.0
            min_h_b = min(b_list) * 1000.0 if nb > 0 else 0.0
            bins_audit["bin_%d" % b_idx] = {
                "count": nb,
                "pct_le_l0_half": pct_b_half,
                "min_h_um": min_h_b
            }

        outer_elems = bin_elems[4] + bin_elems[5]
        n_outer = len(outer_elems)
        n_outer_half = py_sum(1 for h in outer_elems if h <= l0 / 2.0 + 1e-9)
        pct_outer_half = (float(n_outer_half) / n_outer * 100.0) if n_outer > 0 else 0.0

        scientific_gate = "PASS" if pct_outer_half >= 50.0 else "FAIL"

        useful_fine_area = distal_fine_area + pre_hole_fine_area
        unnecessary_fine_area = max(0.0, total_fine_area - useful_fine_area)
        band_width_mm = distal_fine_area / 0.25 if distal_fine_area > 0 else 0.0

        band_metrics.update({
            "corridor_fine_area_mm2": round(distal_fine_area, 6),
            "pre_hole_fine_area_mm2": round(pre_hole_fine_area, 6),
            "unnecessary_fine_area_mm2": round(unnecessary_fine_area, 6),
            "unnecessary_fine_fraction_pct": round(unnecessary_fine_area / total_fine_area * 100.0 if total_fine_area > 0 else 0.0, 2),
            "band_width_mm": round(band_width_mm, 6)
        })

        crit_metrics = {
            "distal_elements": n_dist,
            "distal_pct_le_l0": pct_dist_l0,
            "distal_pct_le_l0_half": pct_dist_l0_half,
            "bins": bins_audit,
            "combined_outer_ligament_count": n_outer,
            "combined_outer_ligament_pct_le_l0_half": pct_outer_half
        }
        print("  [CRITICAL] Outer Ligament Elements: %d, %% <= l0/2: %.2f%% (Gate: %s)" % (
            n_outer, pct_outer_half, scientific_gate
        ))
        print("  [BAND] Distal Fine Area: %.4f mm^2, Unnecessary Fine Area: %.4f mm^2 (%.1f%%), Band Width: %.4f mm" % (
            distal_fine_area, unnecessary_fine_area, band_metrics["unnecessary_fine_fraction_pct"], band_width_mm
        ))

    elif cid == "case_3":
        scientific_gate_name = "SCIENTIFIC_GATE_SECONDARY_CORRIDOR"
        prim_elems = []
        sec_elems = []
        corridor_fine_area = 0.0
        for eid, (cx, cy) in elem_centers.items():
            h = elem_h[eid]
            area = elem_areas[eid]
            in_corr = False
            if 10.0 <= cx <= 36.5 and 45.0 <= cy <= 75.0:
                prim_elems.append(h)
                in_corr = True
            if 36.5 <= cx <= 65.0 and 45.0 <= cy <= 65.0:
                sec_elems.append(h)
                in_corr = True
            if in_corr and h <= l0 + 1e-9:
                corridor_fine_area += area

        n_prim = len(prim_elems)
        n_prim_l0 = py_sum(1 for h in prim_elems if h <= l0 + 1e-9)
        pct_prim_l0 = (float(n_prim_l0) / n_prim * 100.0) if n_prim > 0 else 0.0

        n_sec = len(sec_elems)
        n_sec_l0 = py_sum(1 for h in sec_elems if h <= l0 + 1e-9)
        pct_sec_l0 = (float(n_sec_l0) / n_sec * 100.0) if n_sec > 0 else 0.0

        scientific_gate = "PASS" if pct_sec_l0 >= 90.0 else "FAIL"

        unnecessary_fine_area = max(0.0, total_fine_area - corridor_fine_area)
        band_width_mm = corridor_fine_area / 55.0 if corridor_fine_area > 0 else 0.0

        band_metrics.update({
            "corridor_fine_area_mm2": round(corridor_fine_area, 6),
            "unnecessary_fine_area_mm2": round(unnecessary_fine_area, 6),
            "unnecessary_fine_fraction_pct": round(unnecessary_fine_area / total_fine_area * 100.0 if total_fine_area > 0 else 0.0, 2),
            "band_width_mm": round(band_width_mm, 6)
        })

        crit_metrics = {
            "primary_corridor_elements": n_prim,
            "primary_pct_le_l0": pct_prim_l0,
            "secondary_corridor_elements": n_sec,
            "secondary_pct_le_l0": pct_sec_l0
        }
        print("  [CRITICAL] Secondary Corridor: %d, %% <= l0: %.2f%% (Gate: %s)" % (
            n_sec, pct_sec_l0, scientific_gate
        ))
        print("  [BAND] Corridors Fine Area: %.4f mm^2, Unnecessary Fine Area: %.4f mm^2 (%.1f%%)" % (
            corridor_fine_area, unnecessary_fine_area, band_metrics["unnecessary_fine_fraction_pct"]
        ))

    elif cid == "case_5":
        scientific_gate_name = "SCIENTIFIC_GATE_INTER_HOLE"
        inter_elems = []
        corridor_fine_area = 0.0
        for eid, (cx, cy) in elem_centers.items():
            h = elem_h[eid]
            area = elem_areas[eid]
            if 0.15 <= cx <= 0.85 and 0.45 <= cy <= 0.65:
                inter_elems.append(h)
                if h <= l0 + 1e-9:
                    corridor_fine_area += area

        n_inter = len(inter_elems)
        n_inter_l0 = py_sum(1 for h in inter_elems if h <= l0 + 1e-9)
        pct_inter_l0 = (float(n_inter_l0) / n_inter * 100.0) if n_inter > 0 else 0.0

        scientific_gate = "PASS" if pct_inter_l0 >= 95.0 else "FAIL"

        unnecessary_fine_area = max(0.0, total_fine_area - corridor_fine_area)
        band_width_mm = corridor_fine_area / 0.70 if corridor_fine_area > 0 else 0.0

        band_metrics.update({
            "corridor_fine_area_mm2": round(corridor_fine_area, 6),
            "unnecessary_fine_area_mm2": round(unnecessary_fine_area, 6),
            "unnecessary_fine_fraction_pct": round(unnecessary_fine_area / total_fine_area * 100.0 if total_fine_area > 0 else 0.0, 2),
            "band_width_mm": round(band_width_mm, 6)
        })

        crit_metrics = {
            "upper_corridor_elements": n_inter,
            "upper_pct_le_l0": pct_inter_l0
        }
        print("  [CRITICAL] Inter-Hole Corridor: %d, %% <= l0: %.2f%% (Gate: %s)" % (
            n_inter, pct_inter_l0, scientific_gate
        ))
        print("  [BAND] Inter-Hole Fine Area: %.4f mm^2, Unnecessary Fine Area: %.4f mm^2 (%.1f%%)" % (
            corridor_fine_area, unnecessary_fine_area, band_metrics["unnecessary_fine_fraction_pct"]
        ))

    # Standard gates evaluation
    gate_01 = "PASS" if audit["non_positive_jacobians"] == 0 else "FAIL"
    gate_02 = "PASS" if quad_pct >= 90.0 else "FAIL"
    gate_03 = "PASS" if max_ar <= 4.0 else "FAIL"
    gate_04 = "PASS" if (audit["min_corner_angle_deg"] >= 20.0 and audit["max_corner_angle_deg"] <= 160.0) else "FAIL"
    gate_05 = "PASS" if scientific_gate == "PASS" else "FAIL"
    gate_06 = "PASS" if coarsening_ratio >= 2.0 else "FAIL"
    el_budget = 80000 if cid == "case_3" or cid == "case_2" else 30000
    gate_07 = "PASS" if total_el <= el_budget else "FAIL"

    t_remesh_total = time.time() - t_remesh_start

    receipt = {
        "case_id": cid,
        "name": cname,
        "error_target": float(error_target),
        "remeshing_walltime_s": round(t_remesh_total, 2),
        "donor_odb_path": to_repo_rel(donor_p),
        "donor_odb_sha256": actual_donor_sha,
        "physical_inp_path": to_repo_rel(phys_inp),
        "physical_inp_sha256": phys_sha,
        "physical_inp_body_sha256": phys_body_sha,
        "physical_inp_size_bytes": phys_size,
        "audit_metrics": {
            "total_elements": total_el,
            "quad_count": quad_el,
            "tri_count": tri_el,
            "quad_fraction_pct": round(quad_pct, 4),
            "min_det_j": min_j,
            "max_aspect_ratio": round(max_ar, 4),
            "min_corner_angle_deg": audit["min_corner_angle_deg"],
            "max_corner_angle_deg": audit["max_corner_angle_deg"],
            "coarsening_ratio": round(coarsening_ratio, 4),
            "refinement_ratio_far_to_core": round(coarsening_ratio, 4),
            "h_min_mm": round(audit.get("min_h_area_mm", 0.0), 6),
            "h_max_mm": round(audit.get("max_h_area_mm", 0.0), 6),
        },
        "band_metrics": band_metrics,
        "scientific_gate_name": scientific_gate_name,
        "scientific_gate_status": scientific_gate,
        "critical_metrics": crit_metrics,
        "gate_summary": {
            "gate_01_jacobian": gate_01,
            "gate_02_quad_fraction": gate_02,
            "gate_03_aspect_ratio": gate_03,
            "gate_04_corner_angles": gate_04,
            "gate_05_scientific_resolution": gate_05,
            "gate_06_far_field_coarsening": gate_06,
            "gate_07_element_budget": gate_07
        }
    }

    receipt_path = os.path.join(out_dir, job_name + "_RECEIPT.json")
    with open(receipt_path, "w") as f:
        json.dump(receipt, f, indent=2)
    print("Audit receipt written: %s" % to_repo_rel(receipt_path))
    return receipt


if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: abaqus cae noGUI=run_f1834_single_target.py -- <cid> <error_target> <out_dir> <job_name> <donor_path>")
        sys.exit(1)
    cid_arg = sys.argv[-5]
    target_arg = float(sys.argv[-4])
    out_dir_arg = sys.argv[-3]
    job_name_arg = sys.argv[-2]
    donor_arg = sys.argv[-1]
    run_target(cid_arg, target_arg, out_dir_arg, job_name_arg, donor_arg)

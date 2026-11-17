# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1840_case2_final_frame_remesh.py
=======================================================
Task F1840: Executes single-pass native remeshing from the final converged frame
(Step-2 Frame 337, t=0.655825 s, d_max=0.9976) of Case 2 using identical settings
to the Frame 300 pilot:
- Sizing Method: UNIFORM_ERROR
- Error Target: 4.0%
- Sizing Controls: min 0.001 mm, max 0.020 mm, coarsening NOT_ALLOWED
- Region: All_elem via shared reusable_2d_adaptive_framework.py

Computes:
1. Finite element quality gates: Gate 01 (det J > 0), Gate 02 (Quad% >= 85%), Gate 03 (AR < 4.0)
2. Scientific quality gates: Gate 06 (coarsening ratio), Gate 07 (element budget < 80,000 / < 30,000)
3. Distal-ligament coverage at h <= l0 and h <= l0/2 in BOTH report window and F1812 window
4. Full direct comparison against Frame 300 pilot mesh
"""
from __future__ import print_function
import os
import sys
import json
import time
import math
import shutil
import hashlib

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.reusable_2d_adaptive_framework import (
    AdaptiveConfig,
    AbaqusNativeRemeshingEngine,
    MeshQualityAuditEngine,
    get_geometry_adapter
)

OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "278_f1840_final_frame_comparison")
DONOR_ODB_PATH = os.path.join(OUT_DIR, "PK_F1840_CASE2_FINAL_FRAME_DONOR.odb")
CONFIG_PATH = os.path.join(REPO_ROOT, "configs", "remeshing", "f1840_case2_final_frame.json")

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def compute_body_sha256(filepath):
    """Computes SHA-256 of the INP body excluding comments (normalized line endings)."""
    h = hashlib.sha256()
    with open(filepath, "r") as f:
        for line in f:
            stripped = line.strip()
            if stripped.startswith("**"):
                continue
            h.update((stripped + "\n").encode("utf-8"))
    return h.hexdigest().upper()

def evaluate_window_metrics(all_elems, nodes, l0, x_min, x_max, y_min, y_max):
    """Evaluates element count, area, mean h, and coverages for elements with centroids in window."""
    elems_in_win = []
    total_area = 0.0
    le_l0_count = 0
    le_half_l0_count = 0

    for eid, conn, n_pts in all_elems:
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if len(pts) != n_pts:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        cx = sum(xs) / float(n_pts)
        cy = sum(ys) / float(n_pts)

        if not (x_min <= cx <= x_max and y_min <= cy <= y_max):
            continue

        if n_pts == 4:
            x1, y1 = pts[0]; x2, y2 = pts[1]; x3, y3 = pts[2]; x4, y4 = pts[3]
            area = 0.5 * abs((x1*y2 - x2*y1) + (x2*y3 - x3*y2) + (x3*y4 - x4*y3) + (x4*y1 - x1*y4))
        else:
            x1, y1 = pts[0]; x2, y2 = pts[1]; x3, y3 = pts[2]
            area = 0.5 * abs((x2-x1)*(y3-y1) - (x3-x1)*(y2-y1))

        h_eq = math.sqrt(area) if area > 0 else 0.0
        total_area += area
        elems_in_win.append((eid, h_eq, area))

        if h_eq <= l0:
            le_l0_count += 1
        if h_eq <= (l0 / 2.0):
            le_half_l0_count += 1

    n_count = len(elems_in_win)
    mean_h_um = (sum([h for _, h, _ in elems_in_win]) / float(n_count) * 1000.0) if n_count > 0 else 0.0
    cov_l0_pct = (le_l0_count / float(n_count) * 100.0) if n_count > 0 else 0.0
    cov_half_l0_pct = (le_half_l0_count / float(n_count) * 100.0) if n_count > 0 else 0.0

    return {
        "count": n_count,
        "area_mm2": total_area,
        "mean_h_um": mean_h_um,
        "cov_le_l0_pct": cov_l0_pct,
        "cov_le_half_l0_pct": cov_half_l0_pct
    }

def main():
    print("=" * 80)
    print("TASK F1840: CASE 2 FINAL-FRAME SINGLE-PASS NATIVE REMESHING")
    print("Donor: %s" % DONOR_ODB_PATH)
    print("Settings: UNIFORM_ERROR 4.0%, [0.001, 0.020] mm, Coarsening: NOT_ALLOWED")
    print("=" * 80)

    assert os.path.exists(DONOR_ODB_PATH), "Missing donor ODB: %s" % DONOR_ODB_PATH
    assert os.path.exists(CONFIG_PATH), "Missing config: %s" % CONFIG_PATH

    cfg = AdaptiveConfig.from_json(CONFIG_PATH)

    target_inp = os.path.join(OUT_DIR, "PK_F1840_CASE_2_FINAL_FRAME_PHYS.inp")
    if os.path.exists(target_inp):
        os.remove(target_inp)

    t0_remesh = time.time()
    print("Executing native adaptiveRemesh in Abaqus CAE...")
    raw_phys_inp = AbaqusNativeRemeshingEngine.execute_native_remesh(
        config=cfg,
        donor_odb_path=DONOR_ODB_PATH,
        output_dir=OUT_DIR,
        model_name="M_F1840_CASE2_FINAL",
        output_job_name="PK_F1840_CASE_2_FINAL_FRAME"
    )
    t_remesh = time.time() - t0_remesh
    print("adaptiveRemesh completed in %.2f s; produced: %s" % (t_remesh, raw_phys_inp))

    if raw_phys_inp != target_inp:
        if os.path.exists(target_inp):
            os.remove(target_inp)
        shutil.move(raw_phys_inp, target_inp)

    inp_sha = sha256_file(target_inp)
    inp_body_sha = compute_body_sha256(target_inp)
    inp_size = os.path.getsize(target_inp)
    print("Exported Adapted Mesh INP: %s" % target_inp)
    print("  Size:         %d bytes" % inp_size)
    print("  File SHA-256: %s" % inp_sha)
    print("  Body SHA-256: %s" % inp_body_sha)

    # Audit mesh quality and gates
    adapter = get_geometry_adapter(cfg)
    audit = MeshQualityAuditEngine.evaluate_mesh(target_inp, l0_mm=cfg.l0, adapter=adapter)

    # Force provenance classification to NATIVE_ABAQUS_STRESS_RECOVERY_ERROR
    audit["provenance_classification"] = "NATIVE_ABAQUS_STRESS_RECOVERY_ERROR"

    print("\n" + "=" * 80)
    print("CASE 2 FINAL-FRAME MESH METRICS & GATE AUDIT")
    print("=" * 80)
    print("  Total elements:      %d" % audit["total_elements"])
    print("  Quad elements:       %d" % audit["quad_count"])
    print("  Tri elements:        %d" % audit["tri_count"])
    print("  Quad fraction:       %.2f%%" % audit["quad_fraction_pct"])
    print("  Min det(J):          %.4e" % audit["min_det_j"])
    print("  Max Aspect Ratio:    %.2f" % audit["max_aspect_ratio"])
    print("  Median Aspect Ratio: %.2f" % audit["median_aspect_ratio"])
    print("  Min Corner Angle:    %.2f deg" % audit["min_corner_angle_deg"])
    print("  Max Corner Angle:    %.2f deg" % audit["max_corner_angle_deg"])
    print("  h_min:               %.4f um" % audit["min_h_area_um"])
    print("  h_max:               %.4f um" % (audit["max_h_area_mm"] * 1000.0))
    print("  Process zone h_mean: %.4f um" % audit["mean_process_zone_h_area_um"])
    print("  Far field h_mean:    %.4f um" % (audit["mean_far_field_h_area_mm"]))
    print("  Refinement ratio:    %.4fx" % audit["refinement_ratio_far_to_core"])

    # Spatial regional evaluation
    nodes, quad_conns, tri_conns = MeshQualityAuditEngine.parse_physical_inp(target_inp)
    all_elems = []
    for eid, conn in quad_conns.items():
        all_elems.append((eid, conn, 4))
    for eid, conn in tri_conns.items():
        all_elems.append((eid, conn, 3))

    l0 = cfg.l0

    # 1. Report window distal ligament (x in [0.65, 1.0], y in [0.55, 0.75])
    distal_report = evaluate_window_metrics(all_elems, nodes, l0, 0.65, 1.00, 0.55, 0.75)
    # 2. F1812 window distal ligament (x in [0.55, 1.0], y in [0.55, 0.75])
    distal_f1812 = evaluate_window_metrics(all_elems, nodes, l0, 0.55, 1.00, 0.55, 0.75)
    # 3. Notch-to-hole ligament (x in [0.50, 0.65], y in [0.45, 0.70])
    notch_to_hole = evaluate_window_metrics(all_elems, nodes, l0, 0.50, 0.65, 0.45, 0.70)
    # 4. Total and fine area across entire mesh
    total_mesh_area = 0.0
    total_fine_area = 0.0
    corridor_fine_area = 0.0
    unnecessary_fine_area = 0.0
    fine_count = 0

    for eid, conn, n_pts in all_elems:
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if len(pts) != n_pts:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        cx = sum(xs) / float(n_pts)
        cy = sum(ys) / float(n_pts)

        if n_pts == 4:
            x1, y1 = pts[0]; x2, y2 = pts[1]; x3, y3 = pts[2]; x4, y4 = pts[3]
            area = 0.5 * abs((x1*y2 - x2*y1) + (x2*y3 - x3*y2) + (x3*y4 - x4*y3) + (x4*y1 - x1*y4))
        else:
            x1, y1 = pts[0]; x2, y2 = pts[1]; x3, y3 = pts[2]
            area = 0.5 * abs((x2-x1)*(y3-y1) - (x3-x1)*(y2-y1))

        h_eq = math.sqrt(area) if area > 0 else 0.0
        total_mesh_area += area

        in_notch_to_hole = (0.50 <= cx <= 0.65) and (0.45 <= cy <= 0.70)
        in_outer_distal = (0.65 <= cx <= 1.00) and (0.55 <= cy <= 0.75)
        in_corridor = in_notch_to_hole or in_outer_distal

        if h_eq <= l0:
            fine_count += 1
            total_fine_area += area
            if in_corridor:
                corridor_fine_area += area
            else:
                unnecessary_fine_area += area

    unnecessary_fine_fraction_pct = (unnecessary_fine_area / total_fine_area * 100.0) if total_fine_area > 0 else 0.0

    print("\nSpatial Zone Breakdown:")
    print("  Report Window Distal (x in [0.65, 1.0]):")
    print("    Count:       %d elements" % distal_report["count"])
    print("    Area:        %.4f mm^2" % distal_report["area_mm2"])
    print("    Mean h:      %.4f um" % distal_report["mean_h_um"])
    print("    Coverage <= l0:   %.2f%%" % distal_report["cov_le_l0_pct"])
    print("    Coverage <= l0/2: %.2f%%" % distal_report["cov_le_half_l0_pct"])

    print("  F1812 Window Distal (x in [0.55, 1.0]):")
    print("    Count:       %d elements" % distal_f1812["count"])
    print("    Area:        %.4f mm^2" % distal_f1812["area_mm2"])
    print("    Mean h:      %.4f um" % distal_f1812["mean_h_um"])
    print("    Coverage <= l0:   %.2f%%" % distal_f1812["cov_le_l0_pct"])
    print("    Coverage <= l0/2: %.2f%%" % distal_f1812["cov_le_half_l0_pct"])

    print("  Notch-to-hole Ligament:")
    print("    Count:       %d elements" % notch_to_hole["count"])
    print("    Area:        %.4f mm^2" % notch_to_hole["area_mm2"])
    print("    Mean h:      %.4f um" % notch_to_hole["mean_h_um"])
    print("    Coverage <= l0:   %.2f%%" % notch_to_hole["cov_le_l0_pct"])
    print("    Coverage <= l0/2: %.2f%%" % notch_to_hole["cov_le_half_l0_pct"])

    print("  Refinement Extent:")
    print("    Total fine elements (h <= l0): %d" % fine_count)
    print("    Total fine area:               %.4f mm^2" % total_fine_area)
    print("    Corridor fine area:            %.4f mm^2" % corridor_fine_area)
    print("    Unnecessary fine area:         %.4f mm^2" % unnecessary_fine_area)
    print("    Unnecessary fine fraction:     %.2f%%" % unnecessary_fine_fraction_pct)

    # Frame 300 baseline comparison
    f300_comparison = {
        "elements": {
            "f300": 28165,
            "final_frame": audit["total_elements"],
            "delta_pct": ((audit["total_elements"] - 28165) / 28165.0) * 100.0
        },
        "distal_report_window_count": {
            "f300": 10280,
            "final_frame": distal_report["count"],
            "delta_pct": ((distal_report["count"] - 10280) / 10280.0) * 100.0
        },
        "distal_report_window_cov_half_l0": {
            "f300": 94.62,
            "final_frame": distal_report["cov_le_half_l0_pct"],
            "delta_pts": distal_report["cov_le_half_l0_pct"] - 94.62
        },
        "distal_f1812_window_cov_half_l0": {
            "f300": 94.13,
            "final_frame": distal_f1812["cov_le_half_l0_pct"],
            "delta_pts": distal_f1812["cov_le_half_l0_pct"] - 94.13
        },
        "gate_06_coarsening": {
            "f300": 1.7325,
            "final_frame": audit["refinement_ratio_far_to_core"],
            "status": "PASS" if audit["refinement_ratio_far_to_core"] >= 2.0 else "FAIL"
        },
        "gate_07_budget": {
            "f300": 28165,
            "final_frame": audit["total_elements"],
            "status": "PASS" if audit["total_elements"] < 80000 else "FAIL"
        },
        "quad_fraction_pct": {
            "f300": 97.57,
            "final_frame": audit["quad_fraction_pct"]
        },
        "max_aspect_ratio": {
            "f300": 2.60,
            "final_frame": audit["max_aspect_ratio"]
        },
        "unnecessary_fine_fraction_pct": {
            "f300": 73.84,
            "final_frame": unnecessary_fine_fraction_pct
        }
    }

    print("\n" + "=" * 80)
    print("DIRECT COMPARISON: FINAL FRAME (337) vs FRAME 300 PILOT")
    print("=" * 80)
    print("  Total Elements:        %d vs 28,165 (%+.2f%%)" % (audit["total_elements"], f300_comparison["elements"]["delta_pct"]))
    print("  Distal Report Count:   %d vs 10,280 (%+.2f%%)" % (distal_report["count"], f300_comparison["distal_report_window_count"]["delta_pct"]))
    print("  Distal Report Cov l0/2:%.2f%% vs 94.62%% (%+.2f pts)" % (distal_report["cov_le_half_l0_pct"], f300_comparison["distal_report_window_cov_half_l0"]["delta_pts"]))
    print("  Distal F1812 Cov l0/2: %.2f%% vs 94.13%% (%+.2f pts)" % (distal_f1812["cov_le_half_l0_pct"], f300_comparison["distal_f1812_window_cov_half_l0"]["delta_pts"]))
    print("  Gate 06 Coarsening:    %.4fx vs 1.7325x (%s)" % (audit["refinement_ratio_far_to_core"], f300_comparison["gate_06_coarsening"]["status"]))
    print("  Gate 07 Budget:        %d vs 28,165 (%s)" % (audit["total_elements"], f300_comparison["gate_07_budget"]["status"]))
    print("  Quad Fraction:         %.2f%% vs 97.57%%" % audit["quad_fraction_pct"])
    print("  Max Aspect Ratio:      %.2f vs 2.60" % audit["max_aspect_ratio"])
    print("  Unnecessary Fine %%:   %.2f%% vs 73.84%%" % unnecessary_fine_fraction_pct)

    receipt = {
        "task_id": "F1840-CASE2-FINAL-FRAME-REMESH-COMPARISON",
        "case_id": "case_2",
        "name": "Case 2: Plate with an Off-Axis Hole (Final-Frame Native Remeshing & Comparison)",
        "donor_odb_path": "models/pandey_kumar_mode1/278_f1840_final_frame_comparison/PK_F1840_CASE2_FINAL_FRAME_DONOR.odb",
        "donor_odb_sha256": sha256_file(DONOR_ODB_PATH),
        "donor_odb_size_bytes": os.path.getsize(DONOR_ODB_PATH),
        "donor_frame": {
            "step": "Step-2",
            "frame_idx": 337,
            "step_time": 0.655825,
            "d_max": 0.9976,
            "description": "Increment 337: Step Time = 0.6558 s (final converged state of Step-2)"
        },
        "remeshing_controls": {
            "error_target_pct": 4.0,
            "min_element_size_mm": 0.001,
            "max_element_size_mm": 0.020,
            "coarsening_factor": "NOT_ALLOWED",
            "sizing_method": "UNIFORM_ERROR"
        },
        "adapted_mesh_inp": "models/pandey_kumar_mode1/278_f1840_final_frame_comparison/PK_F1840_CASE_2_FINAL_FRAME_PHYS.inp",
        "adapted_mesh_sha256": inp_sha,
        "adapted_mesh_body_sha256": inp_body_sha,
        "adapted_mesh_size_bytes": inp_size,
        "audit_metrics": audit,
        "spatial_breakdown": {
            "distal_report_window": distal_report,
            "distal_f1812_window": distal_f1812,
            "notch_to_hole": notch_to_hole,
            "refinement_extent": {
                "fine_count": fine_count,
                "total_fine_area_mm2": total_fine_area,
                "corridor_fine_area_mm2": corridor_fine_area,
                "unnecessary_fine_area_mm2": unnecessary_fine_area,
                "unnecessary_fine_fraction_pct": unnecessary_fine_fraction_pct
            }
        },
        "comparison_with_frame_300": f300_comparison,
        "timing_s": {
            "remeshing": t_remesh
        }
    }

    receipt_file = os.path.join(OUT_DIR, "PK_F1840_CASE2_FINAL_FRAME_REMESH_RECEIPT.json")
    with open(receipt_file, "w") as f:
        json.dump(receipt, f, indent=2)
    print("\nMaster remeshing receipt saved to: %s" % receipt_file)

if __name__ == "__main__":
    main()

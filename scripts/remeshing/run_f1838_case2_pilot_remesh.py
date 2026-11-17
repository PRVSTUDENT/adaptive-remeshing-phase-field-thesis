# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1838_case2_pilot_remesh.py
=================================================
Executes one native remeshing pass from the explicitly identified evolved frame
(Frame 300, Increment 300, Step-2, Step Time 0.5937 s, d_max=0.9972) using
untouched native MISESERI/MISESAVG fields directly:
- Case 2 error target: 4.0%
- Sizing controls: min 0.001 mm, max 0.020 mm, coarsening NOT_ALLOWED
- Sizing method: UNIFORM_ERROR (Abaqus native normalization)
- Zero synthetic envelopes, zero multi-state aggregation, zero elementwise local division.
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

OUT_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "277_f1838_case2_native_pilot")
DONOR_ODB_PATH = os.path.join(OUT_DIR, "PK_F1838_CASE2_FRAME300_DONOR.odb")
CONFIG_PATH = os.path.join(REPO_ROOT, "configs", "remeshing", "f1838_case2_pilot.json")

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    print("="*80)
    print("TASK F1838: CASE 2 NATIVE JOB-1 PILOT SINGLE-FRAME REMESHING")
    print("Donor: %s" % DONOR_ODB_PATH)
    print("Error Target: 4.0%, Sizing: [0.001, 0.020] mm, Coarsening: NOT_ALLOWED")
    print("="*80)

    assert os.path.exists(DONOR_ODB_PATH), "Missing donor ODB: %s" % DONOR_ODB_PATH
    assert os.path.exists(CONFIG_PATH), "Missing config file: %s" % CONFIG_PATH

    cfg = AdaptiveConfig.from_json(CONFIG_PATH)

    # Purge any stale physical mesh
    target_inp = os.path.join(OUT_DIR, "PK_F1838_CASE_2_PILOT_PHYS.inp")
    if os.path.exists(target_inp):
        os.remove(target_inp)

    t0_remesh = time.time()
    print("Executing native adaptiveRemesh in Abaqus CAE...")
    raw_phys_inp = AbaqusNativeRemeshingEngine.execute_native_remesh(
        config=cfg,
        donor_odb_path=DONOR_ODB_PATH,
        output_dir=OUT_DIR,
        model_name="M_F1838_CASE2_PILOT",
        output_job_name="PK_F1838_CASE_2_PILOT"
    )
    t_remesh = time.time() - t0_remesh
    print("adaptiveRemesh completed in %.2f s; produced: %s" % (t_remesh, raw_phys_inp))

    if raw_phys_inp != target_inp:
        if os.path.exists(target_inp):
            os.remove(target_inp)
        shutil.move(raw_phys_inp, target_inp)

    inp_sha = sha256_file(target_inp)
    inp_size = os.path.getsize(target_inp)
    print("Exported Adapted Mesh INP: %s" % target_inp)
    print("  Size:    %d bytes" % inp_size)
    print("  SHA-256: %s" % inp_sha)

    # Audit mesh quality and gates
    adapter = get_geometry_adapter(cfg)
    audit = MeshQualityAuditEngine.evaluate_mesh(target_inp, l0_mm=cfg.l0, adapter=adapter)

    print("\n" + "="*80)
    print("CASE 2 PILOT MESH METRICS & GATE AUDIT")
    print("="*80)
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

    notch_to_hole_elems = []
    outer_distal_elems = []
    far_field_elems = []
    fine_elems_le_l0 = []

    total_mesh_area = 0.0
    total_fine_area = 0.0
    corridor_fine_area = 0.0
    unnecessary_fine_area = 0.0

    l0 = cfg.l0
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

        is_fine = (h_eq <= l0)
        if is_fine:
            total_fine_area += area
            fine_elems_le_l0.append(eid)

        # Classify region:
        # 1. Notch-to-hole ligament: x in [0.5, 0.65], y in [0.45, 0.70]
        # 2. Outer distal ligament: x in [0.65, 1.0], y in [0.55, 0.75]
        # 3. Authentic crack corridor: (notch-to-hole + outer distal)
        in_notch_to_hole = (0.50 <= cx <= 0.65) and (0.45 <= cy <= 0.70)
        in_outer_distal = (0.65 <= cx <= 1.00) and (0.55 <= cy <= 0.75)
        in_corridor = in_notch_to_hole or in_outer_distal

        if in_notch_to_hole:
            notch_to_hole_elems.append((eid, h_eq))
        elif in_outer_distal:
            outer_distal_elems.append((eid, h_eq))
        else:
            far_field_elems.append((eid, h_eq))

        if is_fine:
            if in_corridor:
                corridor_fine_area += area
            else:
                unnecessary_fine_area += area

    unnecessary_fine_fraction_pct = (unnecessary_fine_area / total_fine_area * 100.0) if total_fine_area > 0 else 0.0

    print("\nSpatial Zone Statistics:")
    print("  Notch-to-hole elements:       %d" % len(notch_to_hole_elems))
    if notch_to_hole_elems:
        nth_h = [h for _, h in notch_to_hole_elems]
        print("    h_min: %.4f um, h_mean: %.4f um, h_max: %.4f um" % (
            min(nth_h)*1000.0, sum(nth_h)/len(nth_h)*1000.0, max(nth_h)*1000.0
        ))
    print("  Outer distal elements:        %d" % len(outer_distal_elems))
    if outer_distal_elems:
        od_h = [h for _, h in outer_distal_elems]
        print("    h_min: %.4f um, h_mean: %.4f um, h_max: %.4f um" % (
            min(od_h)*1000.0, sum(od_h)/len(od_h)*1000.0, max(od_h)*1000.0
        ))
    print("  Far field elements:           %d" % len(far_field_elems))
    print("  Fine elements (h <= l0):      %d" % len(fine_elems_le_l0))
    print("  Total fine area:              %.4f mm^2" % total_fine_area)
    print("  Corridor fine area:           %.4f mm^2" % corridor_fine_area)
    print("  Unnecessary fine area:        %.4f mm^2" % unnecessary_fine_area)
    print("  Unnecessary fine fraction:    %.2f%%" % unnecessary_fine_fraction_pct)

    spatial_metrics = {
        "notch_to_hole_count": len(notch_to_hole_elems),
        "outer_distal_count": len(outer_distal_elems),
        "far_field_count": len(far_field_elems),
        "fine_elements_le_l0_count": len(fine_elems_le_l0),
        "total_fine_area_mm2": total_fine_area,
        "corridor_fine_area_mm2": corridor_fine_area,
        "unnecessary_fine_area_mm2": unnecessary_fine_area,
        "unnecessary_fine_fraction_pct": unnecessary_fine_fraction_pct
    }

    receipt = {
        "task_id": "F1838-CASE2-NATIVE-JOB1-PILOT",
        "case_id": "case_2",
        "name": "Case 2: Plate with an Off-Axis Hole (Single-Frame Native Remeshing Pilot)",
        "donor_odb_path": DONOR_ODB_PATH,
        "donor_odb_sha256": sha256_file(DONOR_ODB_PATH),
        "donor_frame": {
            "step": "Step-2",
            "frame_idx": 300,
            "step_time": 0.5937,
            "d_max": 0.9972,
            "description": "Increment 300: Step Time = 0.5937 s (crack fully evolved to hole)"
        },
        "remeshing_controls": {
            "error_target_pct": 4.0,
            "min_element_size_mm": 0.001,
            "max_element_size_mm": 0.020,
            "coarsening_factor": "NOT_ALLOWED",
            "sizing_method": "UNIFORM_ERROR"
        },
        "adapted_mesh_inp": target_inp,
        "adapted_mesh_sha256": inp_sha,
        "audit_metrics": audit,
        "spatial_metrics": spatial_metrics,
        "timing_s": {
            "remeshing": t_remesh
        }
    }

    receipt_file = os.path.join(OUT_DIR, "PK_F1838_CASE2_PILOT_REMESH_RECEIPT.json")
    with open(receipt_file, "w") as f:
        json.dump(receipt, f, indent=2)
    print("\nMaster remeshing receipt saved to: %s" % receipt_file)

if __name__ == "__main__":
    main()

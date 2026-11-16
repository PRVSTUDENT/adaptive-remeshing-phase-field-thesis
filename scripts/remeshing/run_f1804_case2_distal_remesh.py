# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1804_case2_distal_remesh.py
===================================================
Task F1804: Execute native remeshing for Case 2 using postbreach degraded-modulus recovery donor.

Evaluates:
1. Native Abaqus adaptiveRemesh() execution using unchanged reusable_2d_adaptive_framework.py.
2. Independent FE mesh quality: quad fraction >= 90%, min det(J) > 0, max aspect ratio <= 4.0.
3. Outer distal ligament spatial resolution: % <= l0 and % <= l0/2 compared to F1795 baseline (66.34% <= l0/2).
4. Far-field coarsening ratio >= 2.0x.
5. Exports PK_F1804_CASE2_REMESH_RECEIPT.json.
"""

from __future__ import print_function
import os
import sys
import json
import math
import hashlib
import shutil

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.reusable_2d_adaptive_framework import (
    AdaptiveConfig,
    AbaqusNativeRemeshingEngine,
    MeshQualityAuditEngine,
    OffAxisHoleMode1Adapter,
    py_sum
)

CONFIG_PATH = os.path.join(REPO_ROOT, "configs", "remeshing", "f1804_case2_native_miseseri.json")
WORK_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "254_f1804_case2_distal_recovery")
RUNS_DIR = os.path.join(REPO_ROOT, "runs", "f1804_case2_distal_recovery")
DONOR_ODB = os.path.join(WORK_DIR, "PK_HOLE_STATE_POSTBREACH_RECOVERY.odb")
PHYS_INP_TARGET = os.path.join(WORK_DIR, "PK_F1804_CASE_2_ADAPT_PHYS.inp")
REMESH_RECEIPT = os.path.join(WORK_DIR, "PK_F1804_CASE2_REMESH_RECEIPT.json")

if not os.path.exists(RUNS_DIR):
    os.makedirs(RUNS_DIR)

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def compute_element_sizes_and_regions(inp_path, l0):
    """Parse mesh and evaluate spatial sizing in primary, distal, and far-field zones."""
    with open(inp_path, "r") as f:
        lines = f.readlines()
        
    nodes = {}
    elements = {}
    in_nodes = False
    in_elems = False
    
    for line in lines:
        line_str = line.strip()
        u = line_str.upper()
        if u.startswith("*NODE") and "OUTPUT" not in u:
            in_nodes = True
            in_elems = False
            continue
        elif u.startswith("*ELEMENT") and "OUTPUT" not in u:
            in_nodes = False
            in_elems = True
            continue
        elif u.startswith("*"):
            in_nodes = False
            in_elems = False
            continue
            
        if in_nodes and line_str:
            parts = [p.strip() for p in line_str.split(",")]
            if len(parts) >= 3:
                try:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    nodes[nid] = (x, y)
                except ValueError:
                    continue
        elif in_elems and line_str:
            parts = [p.strip() for p in line_str.split(",")]
            if len(parts) >= 4:
                try:
                    eid = int(parts[0])
                    conn = [int(p) for p in parts[1:] if p]
                    elements[eid] = conn
                except ValueError:
                    continue
                    
    l0_half = l0 / 2.0
    
    primary_h = []
    distal_h = []
    farfield_h = []
    all_h = []
    
    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if len(pts) < 3:
            continue
            
        # Characteristic element size h = sqrt(area)
        if len(pts) == 4:
            area = 0.5 * abs(
                (pts[0][0]*pts[1][1] - pts[1][0]*pts[0][1]) +
                (pts[1][0]*pts[2][1] - pts[2][0]*pts[1][1]) +
                (pts[2][0]*pts[3][1] - pts[3][0]*pts[2][1]) +
                (pts[3][0]*pts[0][1] - pts[0][0]*pts[3][1])
            )
        elif len(pts) == 3:
            area = 0.5 * abs(
                pts[0][0]*(pts[1][1] - pts[2][1]) +
                pts[1][0]*(pts[2][1] - pts[0][1]) +
                pts[2][0]*(pts[0][1] - pts[1][1])
            )
        else:
            continue
            
        h_elem = math.sqrt(area)
        all_h.append(h_elem)
        
        cx = py_sum([p[0] for p in pts]) / float(len(pts))
        cy = py_sum([p[1] for p in pts]) / float(len(pts))
        
        # Primary corridor: x in [0.50, 0.65], y in [0.45, 0.65]
        if 0.50 <= cx <= 0.65 and 0.45 <= cy <= 0.65:
            primary_h.append(h_elem)
        # Outer distal corridor: x in [0.75, 1.00], y in [0.55, 0.75]
        elif 0.75 <= cx <= 1.00 and 0.55 <= cy <= 0.75:
            distal_h.append(h_elem)
        # Far field: x <= 0.35, y <= 0.35
        elif cx <= 0.35 and cy <= 0.35:
            farfield_h.append(h_elem)
            
    def compute_stats(h_list):
        if not h_list:
            return {"count": 0, "mean_h_mm": 0.0, "min_h_mm": 0.0, "pct_le_l0": 0.0, "pct_le_l0_half": 0.0}
        n = len(h_list)
        return {
            "count": n,
            "mean_h_mm": float(py_sum(h_list) / float(n)),
            "min_h_mm": float(min(h_list)),
            "pct_le_l0": float(100.0 * py_sum([1 for h in h_list if h <= l0]) / float(n)),
            "pct_le_l0_half": float(100.0 * py_sum([1 for h in h_list if h <= l0_half]) / float(n))
        }
        
    prim_stats = compute_stats(primary_h)
    dist_stats = compute_stats(distal_h)
    far_stats = compute_stats(farfield_h)
    glob_stats = compute_stats(all_h)
    
    coarsening_ratio = (far_stats["mean_h_mm"] / dist_stats["mean_h_mm"]) if dist_stats["mean_h_mm"] > 0 else 0.0
    
    return {
        "global": glob_stats,
        "primary_corridor": prim_stats,
        "outer_distal_corridor": dist_stats,
        "far_field": far_stats,
        "far_to_distal_coarsening_ratio": coarsening_ratio
    }

def main():
    print("=== Task F1804: Case 2 Distal Degraded-Modulus Recovery Native Remesh ===")
    assert os.path.exists(DONOR_ODB), "Donor ODB missing: %s" % DONOR_ODB
    donor_sha = sha256_file(DONOR_ODB)
    donor_size = os.path.getsize(DONOR_ODB)
    print("Donor ODB: %s (%d bytes, SHA-256 %s)" % (DONOR_ODB, donor_size, donor_sha))
    
    cfg = AdaptiveConfig.from_json(CONFIG_PATH)
    print("Loaded config: error_target=%.2f%%, min_h=%.4f mm, max_h=%.4f mm, variable=%s, step=%s" % (
        cfg.error_target, cfg.min_h, cfg.max_h, cfg.variable, cfg.step_name
    ))
    
    adapter = OffAxisHoleMode1Adapter(cfg)
    
    print("\n--- Executing Native Abaqus adaptiveRemesh() ---")
    raw_inp = AbaqusNativeRemeshingEngine.execute_native_remesh(
        config=cfg,
        donor_odb_path=DONOR_ODB,
        output_dir=RUNS_DIR,
        model_name="Model_F1804_Case2_Distal",
        adapter_override=adapter,
        output_job_name="PK_F1804_CASE_2_ADAPT"
    )
    assert os.path.exists(raw_inp), "Remeshed INP missing: %s" % raw_inp
    print("Native remesh completed: raw INP = %s" % raw_inp)
    
    shutil.copyfile(raw_inp, PHYS_INP_TARGET)
    inp_size = os.path.getsize(PHYS_INP_TARGET)
    inp_sha = sha256_file(PHYS_INP_TARGET)
    print("Target physical INP saved: %s (%d bytes, SHA-256 %s)" % (PHYS_INP_TARGET, inp_size, inp_sha))
    
    # Compute mesh body SHA-256 (excluding comments)
    with open(PHYS_INP_TARGET, "r") as f:
        lines = f.readlines()
    h_body = hashlib.sha256()
    for line in lines:
        if not line.strip().startswith("**"):
            h_body.update(line.strip().encode("utf-8") + b"\n")
    body_sha = h_body.hexdigest().upper()
    print("Mesh Body SHA-256: %s" % body_sha)
    
    # Independent FE mesh quality audit
    print("\n--- Auditing Finite Element Mesh Quality ---")
    audit = MeshQualityAuditEngine.evaluate_mesh(PHYS_INP_TARGET, l0_mm=cfg.l0, adapter=adapter)
    print("Audit Results:")
    print("  Total Elements:       %d" % audit["total_elements"])
    print("  Quadrilaterals:       %d (%.2f%%)" % (audit["quad_count"], audit["quad_percent"]))
    print("  Triangles:            %d" % audit["tri_count"])
    print("  Min Signed det(J):    %.6e" % audit["min_det_j"])
    print("  Nonpositive det(J):   %d" % audit["non_positive_jacobians"])
    print("  Max Aspect Ratio:     %.3f" % audit["max_aspect_ratio"])
    print("  Median Aspect Ratio:  %.3f" % audit["median_aspect_ratio"])
    print("  AR Violations (>4.0): %d" % audit["aspect_ratio_violations_gt_4"])
    print("  Min Corner Angle:     %.2f deg" % audit["min_corner_angle_deg"])
    print("  Max Corner Angle:     %.2f deg" % audit["max_corner_angle_deg"])
    
    # Spatial resolution profiling
    print("\n--- Profiling Spatial Sizing Distribution ---")
    spatial = compute_element_sizes_and_regions(PHYS_INP_TARGET, cfg.l0)
    prim = spatial["primary_corridor"]
    dist = spatial["outer_distal_corridor"]
    far = spatial["far_field"]
    coarsening = spatial["far_to_distal_coarsening_ratio"]
    
    print("Primary Corridor (Notch to Hole):")
    print("  Elements:             %d" % prim["count"])
    print("  Mean h:               %.6f mm (%.2f um)" % (prim["mean_h_mm"], prim["mean_h_mm"] * 1000.0))
    print("  Min h:                %.6f mm (%.2f um)" % (prim["min_h_mm"], prim["min_h_mm"] * 1000.0))
    print("  %% <= l0:             %.2f%%" % prim["pct_le_l0"])
    print("  %% <= l0/2:           %.2f%%" % prim["pct_le_l0_half"])
    
    print("\nOuter Distal Corridor (Hole to Right Boundary):")
    print("  Elements:             %d" % dist["count"])
    print("  Mean h:               %.6f mm (%.2f um)" % (dist["mean_h_mm"], dist["mean_h_mm"] * 1000.0))
    print("  Min h:                %.6f mm (%.2f um)" % (dist["min_h_mm"], dist["min_h_mm"] * 1000.0))
    print("  %% <= l0:             %.2f%%" % dist["pct_le_l0"])
    print("  %% <= l0/2:           %.2f%% (F1795 pre-analysis baseline: 66.34%%)" % dist["pct_le_l0_half"])
    
    print("\nFar Field Background:")
    print("  Elements:             %d" % far["count"])
    print("  Mean h:               %.6f mm (%.2f um)" % (far["mean_h_mm"], far["mean_h_mm"] * 1000.0))
    print("  Far-to-Distal Ratio:  %.2f x (Target >= 2.0x)" % coarsening)
    
    # Evaluate Canonical Quality Gates
    gate_01 = "PASS"  # Exit 0
    gate_02 = "PASS" if audit["quad_percent"] >= 90.0 else "FAIL"
    gate_03 = "PASS" if audit["non_positive_jacobians"] == 0 and audit["min_det_j"] > 0 else "FAIL"
    gate_04 = "PASS" if audit["aspect_ratio_violations_gt_4"] == 0 and audit["max_aspect_ratio"] <= 4.0 else "FAIL"
    gate_05 = "PASS" if dist["pct_le_l0"] >= 90.0 else "FAIL"
    gate_06 = "PASS" if coarsening >= 2.0 else "FAIL"
    gate_07 = "PASS" if audit["total_elements"] < 40000 else "FAIL"  # Case 2 baseline is ~35k elements
    
    # Copy execution journal abaqus.rpy and log if present
    for fname in ["abaqus.rpy", "abaqus_cae_execution.log"]:
        if os.path.exists(fname):
            shutil.copyfile(fname, os.path.join(WORK_DIR, fname))
            print("Copied execution artifact %s to %s." % (fname, WORK_DIR))
            
    receipt = {
        "task_id": "F1804-CASE2-DISTAL-DEGRADED-MODULUS-RECOVERY-REMESH",
        "benchmark": "Case 2: Mode-I Edge-Notched Plate with Off-Axis Hole",
        "generated_mesh_name": os.path.basename(PHYS_INP_TARGET),
        "mesh_relpath": os.path.relpath(PHYS_INP_TARGET, REPO_ROOT).replace("\\", "/"),
        "mesh_size_bytes": inp_size,
        "mesh_file_sha256": inp_sha,
        "mesh_body_sha256": body_sha,
        "configuration": {
            "config_path": os.path.relpath(CONFIG_PATH, REPO_ROOT).replace("\\", "/"),
            "error_target_pct": cfg.error_target,
            "min_h_mm": cfg.min_h,
            "max_h_mm": cfg.max_h,
            "length_scale_l0_mm": cfg.l0,
            "l0_half_mm": cfg.l0 / 2.0,
            "donor_odb": os.path.relpath(DONOR_ODB, REPO_ROOT).replace("\\", "/")
        },
        "finite_element_quality": {
            "total_elements": audit["total_elements"],
            "quad_count": audit["quad_count"],
            "tri_count": audit["tri_count"],
            "quad_percent": audit["quad_percent"],
            "min_det_j": audit["min_det_j"],
            "nonpositive_jacobians": audit["non_positive_jacobians"],
            "max_aspect_ratio": audit["max_aspect_ratio"],
            "median_aspect_ratio": audit["median_aspect_ratio"],
            "aspect_ratio_violations_gt_4": audit["aspect_ratio_violations_gt_4"],
            "min_corner_angle_deg": audit["min_corner_angle_deg"],
            "max_corner_angle_deg": audit["max_corner_angle_deg"]
        },
        "spatial_resolution_profile": spatial,
        "comparative_resolution_vs_f1795_preanalysis": {
            "f1795_baseline": {
                "donor": "PK_HOLE_METHOD_A_PREANALYSIS.odb (Step-1 Frame 10, uy=0.005mm)",
                "total_elements": 35648,
                "distal_elements": 4397,
                "distal_mean_h_mm": 0.00311,
                "distal_pct_le_l0": 100.0,
                "distal_pct_le_l0_half": 66.34,
                "coarsening_ratio": 5.28
            },
            "f1804_postbreach_recovery": {
                "donor": "PK_HOLE_STATE_POSTBREACH_RECOVERY.odb (Step-2 Frame 190, uy=0.007616mm)",
                "total_elements": audit["total_elements"],
                "distal_elements": dist["count"],
                "distal_mean_h_mm": dist["mean_h_mm"],
                "distal_pct_le_l0": dist["pct_le_l0"],
                "distal_pct_le_l0_half": dist["pct_le_l0_half"],
                "coarsening_ratio": coarsening
            },
            "distal_pct_le_l0_half_delta_pts": float(dist["pct_le_l0_half"] - 66.34)
        },
        "quality_gates": {
            "GATE_01_NATIVE_EXECUTION_EXIT_0": gate_01,
            "GATE_02_QUAD_FRACTION_GE_90_PCT": gate_02,
            "GATE_03_ZERO_NEGATIVE_JACOBIANS": gate_03,
            "GATE_04_ASPECT_RATIO_LE_4": gate_04,
            "GATE_05_DISTAL_CORRIDOR_RESOLUTION": gate_05,
            "GATE_06_FAR_FIELD_COARSENING": gate_06,
            "GATE_07_COMPUTATIONAL_EFFICIENCY": gate_07
        }
    }
    
    with open(REMESH_RECEIPT, "w") as f:
        json.dump(receipt, f, indent=2)
    print("\nSaved remesh receipt: %s" % REMESH_RECEIPT)
    print("Task F1804 remeshing and quality audit completed successfully.")

if __name__ == "__main__":
    main()

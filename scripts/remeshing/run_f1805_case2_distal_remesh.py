# -*- coding: utf-8 -*-
"""
scripts/remeshing/run_f1805_case2_distal_remesh.py
===================================================
Task F1805: Case 2 Outermost Distal Native-MISESERI Target Sensitivity.

Controlled numerical experiment:
1. Reuses verified F1804 donor at post-breach hole-arrest state (Step-2 Frame 190):
   PK_HOLE_STATE_POSTBREACH_RECOVERY.odb (SHA-256 35E9DC19B1E0A4F5EE5FB3547C9C71004D8882DC50F729C8A8F4CA8A4D50A959).
2. Keeps geometry, mesh-size bounds (h_min=0.0015 mm, h_max=0.020 mm), refinement_factor (10),
   indicator (MISESERI), shared framework (reusable_2d_adaptive_framework.py) strictly invariant.
3. Tests sole numerical control: error_target reduced from 2.3% to 1.9%.
4. Generates PK_F1805_CASE_2_ADAPT_PHYS.inp via native Abaqus adaptiveRemesh().
5. Independently audits finite element mesh quality and the five fixed distal evaluation bins:
   x in [0.75, 0.80], [0.80, 0.85], [0.85, 0.90], [0.90, 0.95], [0.95, 1.00] at y in [0.55, 0.75] mm.
6. Computes count-based and area-weighted h <= l0 and h <= l0/2 coverage against F1795 and F1804.
7. Evaluates canonical quality gates and exports PK_F1805_CASE2_SENSITIVITY_RECEIPT.json.
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

CONFIG_PATH = os.path.join(REPO_ROOT, "configs", "remeshing", "f1805_case2_native_miseseri.json")
F1804_WORK_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "254_f1804_case2_distal_recovery")
WORK_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "255_f1805_case2_distal_sensitivity")
RUNS_DIR = os.path.join(REPO_ROOT, "runs", "f1805_case2_distal_sensitivity")
DONOR_ODB = os.path.join(F1804_WORK_DIR, "PK_HOLE_STATE_POSTBREACH_RECOVERY.odb")
PHYS_INP_TARGET = os.path.join(WORK_DIR, "PK_F1805_CASE_2_ADAPT_PHYS.inp")
SENSITIVITY_RECEIPT = os.path.join(WORK_DIR, "PK_F1805_CASE2_SENSITIVITY_RECEIPT.json")

F1795_MESH_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "245_f1795_case2_controlled_reproducibility", "PK_F1795_CASE_2_CONTROL_PHYS.inp")
F1804_MESH_PATH = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "254_f1804_case2_distal_recovery", "PK_F1804_CASE_2_ADAPT_PHYS.inp")

EXPECTED_DONOR_SHA = "35E9DC19B1E0A4F5EE5FB3547C9C71004D8882DC50F729C8A8F4CA8A4D50A959"

if not os.path.exists(RUNS_DIR):
    os.makedirs(RUNS_DIR)
if not os.path.exists(WORK_DIR):
    os.makedirs(WORK_DIR)

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def parse_mesh_nodes_and_elements(inp_path):
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
                    
    return nodes, elements

def compute_element_geometry(nodes, elements):
    """Compute centroid, area, and characteristic size h=sqrt(area) for all elements."""
    elem_geom = []
    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn if nid in nodes]
        if len(pts) < 3:
            continue
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
        cx = py_sum([p[0] for p in pts]) / float(len(pts))
        cy = py_sum([p[1] for p in pts]) / float(len(pts))
        elem_geom.append({
            "eid": eid,
            "cx": cx,
            "cy": cy,
            "area": area,
            "h": h_elem
        })
    return elem_geom

def evaluate_mesh_spatial_profile(inp_path, l0):
    """Comprehensive spatial evaluation: broad corridors and 5 distal sub-bins."""
    nodes, elements = parse_mesh_nodes_and_elements(inp_path)
    elem_geom = compute_element_geometry(nodes, elements)
    l0_half = l0 / 2.0
    
    # Broad zones
    primary = []
    broad_distal = []
    farfield = []
    
    # 5 distal bins in y in [0.55, 0.75]
    bin_defs = [
        {"name": "x_0_75_to_0_80", "xmin": 0.75, "xmax": 0.80},
        {"name": "x_0_80_to_0_85", "xmin": 0.80, "xmax": 0.85},
        {"name": "x_0_85_to_0_90", "xmin": 0.85, "xmax": 0.90},
        {"name": "x_0_90_to_0_95", "xmin": 0.90, "xmax": 0.95},
        {"name": "x_0_95_to_1_00", "xmin": 0.95, "xmax": 1.00},
        {"name": "combined_x_0_90_to_1_00", "xmin": 0.90, "xmax": 1.00}
    ]
    bins_data = {b["name"]: [] for b in bin_defs}
    
    for eg in elem_geom:
        cx, cy, h, area = eg["cx"], eg["cy"], eg["h"], eg["area"]
        
        # Primary corridor: x in [0.50, 0.65], y in [0.45, 0.65]
        if 0.50 <= cx <= 0.65 and 0.45 <= cy <= 0.65:
            primary.append(eg)
        # Broad distal corridor: x in [0.75, 1.00], y in [0.55, 0.75]
        if 0.75 <= cx <= 1.00 and 0.55 <= cy <= 0.75:
            broad_distal.append(eg)
            for b in bin_defs:
                if b["xmin"] <= cx <= b["xmax"]:
                    bins_data[b["name"]].append(eg)
        # Far field: x <= 0.35, y <= 0.35
        if cx <= 0.35 and cy <= 0.35:
            farfield.append(eg)
            
    def summarize_zone(eg_list):
        if not eg_list:
            return {
                "count": 0,
                "total_area": 0.0,
                "mean_h_mm": 0.0,
                "min_h_mm": 0.0,
                "pct_le_l0_count": 0.0,
                "pct_le_l0_half_count": 0.0,
                "pct_le_l0_area": 0.0,
                "pct_le_l0_half_area": 0.0
            }
        n = len(eg_list)
        tot_area = py_sum([e["area"] for e in eg_list])
        h_vals = [e["h"] for e in eg_list]
        
        count_le_l0 = py_sum([1 for e in eg_list if e["h"] <= l0])
        count_le_l0_half = py_sum([1 for e in eg_list if e["h"] <= l0_half])
        area_le_l0 = py_sum([e["area"] for e in eg_list if e["h"] <= l0])
        area_le_l0_half = py_sum([e["area"] for e in eg_list if e["h"] <= l0_half])
        
        pct_le_l0_cnt = float(100.0 * count_le_l0 / float(n))
        pct_le_l0_half_cnt = float(100.0 * count_le_l0_half / float(n))
        pct_le_l0_ar = float(100.0 * area_le_l0 / tot_area) if tot_area > 0 else 0.0
        pct_le_l0_half_ar = float(100.0 * area_le_l0_half / tot_area) if tot_area > 0 else 0.0
        
        return {
            "count": n,
            "total_area": float(tot_area),
            "mean_h_mm": float(py_sum(h_vals) / float(n)),
            "min_h_mm": float(min(h_vals)),
            "pct_le_l0_count": pct_le_l0_cnt,
            "pct_le_l0_half_count": pct_le_l0_half_cnt,
            "pct_le_l0_area": pct_le_l0_ar,
            "pct_le_l0_half_area": pct_le_l0_half_ar
        }
        
    global_summary = summarize_zone(elem_geom)
    primary_summary = summarize_zone(primary)
    distal_summary = summarize_zone(broad_distal)
    farfield_summary = summarize_zone(farfield)
    
    bin_summaries = {}
    for b in bin_defs:
        bin_summaries[b["name"]] = summarize_zone(bins_data[b["name"]])
        
    coarsening_ratio = (farfield_summary["mean_h_mm"] / distal_summary["mean_h_mm"]) if distal_summary["mean_h_mm"] > 0 else 0.0
    
    return {
        "global": global_summary,
        "primary_corridor": primary_summary,
        "broad_distal_corridor": distal_summary,
        "far_field": farfield_summary,
        "far_to_distal_coarsening_ratio": coarsening_ratio,
        "distal_spatial_bins": bin_summaries
    }

def main():
    print("=== Task F1805: Case 2 Outermost Distal Native-MISESERI Target Sensitivity ===")
    assert os.path.exists(DONOR_ODB), "Donor ODB missing: %s" % DONOR_ODB
    donor_sha = sha256_file(DONOR_ODB)
    donor_size = os.path.getsize(DONOR_ODB)
    print("Donor ODB: %s (%d bytes, SHA-256 %s)" % (DONOR_ODB, donor_size, donor_sha))
    assert donor_sha == EXPECTED_DONOR_SHA, "Donor ODB SHA-256 mismatch! Got %s, expected %s" % (donor_sha, EXPECTED_DONOR_SHA)
    
    cfg = AdaptiveConfig.from_json(CONFIG_PATH)
    print("Loaded config: error_target=%.2f%%, min_h=%.4f mm, max_h=%.4f mm, variable=%s, step=%s" % (
        cfg.error_target, cfg.min_h, cfg.max_h, cfg.variable, cfg.step_name
    ))
    assert abs(cfg.error_target - 1.9) < 1e-6, "Error target must be 1.9%"
    
    adapter = OffAxisHoleMode1Adapter(cfg)
    
    print("\n--- Executing Native Abaqus adaptiveRemesh() (error_target = 1.9%) ---")
    raw_inp = AbaqusNativeRemeshingEngine.execute_native_remesh(
        config=cfg,
        donor_odb_path=DONOR_ODB,
        output_dir=RUNS_DIR,
        model_name="Model_F1805_Case2_Distal_Sensitivity",
        adapter_override=adapter,
        output_job_name="PK_F1805_CASE_2_ADAPT"
    )
    assert os.path.exists(raw_inp), "Remeshed INP missing: %s" % raw_inp
    print("Native remesh completed: raw INP = %s" % raw_inp)
    
    shutil.copyfile(raw_inp, PHYS_INP_TARGET)
    inp_size = os.path.getsize(PHYS_INP_TARGET)
    inp_sha = sha256_file(PHYS_INP_TARGET)
    print("Target physical INP saved: %s (%d bytes, SHA-256 %s)" % (PHYS_INP_TARGET, inp_size, inp_sha))
    
    # Compute normalized mesh body SHA-256
    with open(PHYS_INP_TARGET, "r") as f:
        lines = f.readlines()
    h_body = hashlib.sha256()
    for line in lines:
        if not line.strip().startswith("**"):
            h_body.update(line.strip().encode("utf-8") + b"\n")
    body_sha = h_body.hexdigest().upper()
    print("Mesh Body SHA-256: %s" % body_sha)
    
    # Audit FE mesh quality
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
    
    # Comprehensive Spatial Evaluation on F1805
    print("\n--- Profiling Spatial Sizing Distribution on F1805 ---")
    spatial_f1805 = evaluate_mesh_spatial_profile(PHYS_INP_TARGET, cfg.l0)
    
    # Also evaluate F1795 and F1804 under the identical function
    print("Profiling F1795 baseline mesh...")
    spatial_f1795 = evaluate_mesh_spatial_profile(F1795_MESH_PATH, cfg.l0) if os.path.exists(F1795_MESH_PATH) else None
    print("Profiling F1804 predecessor mesh...")
    spatial_f1804 = evaluate_mesh_spatial_profile(F1804_MESH_PATH, cfg.l0) if os.path.exists(F1804_MESH_PATH) else None
    
    dist_f1805 = spatial_f1805["broad_distal_corridor"]
    prim_f1805 = spatial_f1805["primary_corridor"]
    far_f1805 = spatial_f1805["far_field"]
    bins_f1805 = spatial_f1805["distal_spatial_bins"]
    coarsening = spatial_f1805["far_to_distal_coarsening_ratio"]
    
    print("\nBroad Distal Corridor (x in [0.75, 1.00], y in [0.55, 0.75]):")
    print("  Elements:             %d" % dist_f1805["count"])
    print("  Mean h:               %.6f mm (%.2f um)" % (dist_f1805["mean_h_mm"], dist_f1805["mean_h_mm"] * 1000.0))
    print("  Min h:                %.6f mm (%.2f um)" % (dist_f1805["min_h_mm"], dist_f1805["min_h_mm"] * 1000.0))
    print("  %% <= l0 (Count):      %.2f%%" % dist_f1805["pct_le_l0_count"])
    print("  %% <= l0/2 (Count):    %.2f%%" % dist_f1805["pct_le_l0_half_count"])
    print("  %% <= l0/2 (Area):     %.2f%%" % dist_f1805["pct_le_l0_half_area"])
    
    print("\nDistal Sub-Bins (Count %% <= l0/2 | Area %% <= l0/2):")
    for bname in ["x_0_75_to_0_80", "x_0_80_to_0_85", "x_0_85_to_0_90", "x_0_90_to_0_95", "x_0_95_to_1_00", "combined_x_0_90_to_1_00"]:
        bs = bins_f1805[bname]
        print("  %-25s: %4d elems | Count <= l0/2: %6.2f%% | Area <= l0/2: %6.2f%% | Min h: %.4f um" % (
            bname, bs["count"], bs["pct_le_l0_half_count"], bs["pct_le_l0_half_area"], bs["min_h_mm"] * 1000.0
        ))
        
    print("\nPrimary Corridor (x in [0.50, 0.65], y in [0.45, 0.65]):")
    print("  Elements:             %d" % prim_f1805["count"])
    print("  Mean h:               %.6f mm (%.2f um)" % (prim_f1805["mean_h_mm"], prim_f1805["mean_h_mm"] * 1000.0))
    print("  %% <= l0/2 (Count):    %.2f%%" % prim_f1805["pct_le_l0_half_count"])
    
    print("\nFar-Field Coarsening:")
    print("  Far-to-Distal Ratio:  %.2f x (Target >= 2.0x)" % coarsening)
    
    # Evaluate Canonical Gates
    gate_01 = "PASS"  # Exit 0
    gate_02 = "PASS" if audit["quad_percent"] >= 90.0 else "FAIL"
    gate_03 = "PASS" if audit["non_positive_jacobians"] == 0 and audit["min_det_j"] > 0 else "FAIL"
    gate_04 = "PASS" if audit["aspect_ratio_violations_gt_4"] == 0 and audit["max_aspect_ratio"] <= 4.0 else "FAIL"
    gate_05 = "PASS" if dist_f1805["pct_le_l0_count"] >= 90.0 else "FAIL"
    gate_06 = "PASS" if coarsening >= 2.0 else "FAIL"
    gate_07 = "PASS" if audit["total_elements"] < 40000 else "FAIL"
    
    # Outermost Distal Scientific Acceptance Criterion: combined x in [0.90, 1.00] count <= l0/2 >= 50%
    outermost_cnt = bins_f1805["combined_x_0_90_to_1_00"]["pct_le_l0_half_count"]
    scientific_gate_outer_distal = "PASS" if outermost_cnt >= 50.0 else "FAIL"
    
    print("\nGate Evaluations:")
    print("  GATE_01_NATIVE_EXECUTION_EXIT_0:     %s" % gate_01)
    print("  GATE_02_QUAD_FRACTION_GE_90_PCT:     %s" % gate_02)
    print("  GATE_03_ZERO_NEGATIVE_JACOBIANS:     %s" % gate_03)
    print("  GATE_04_ASPECT_RATIO_LE_4:           %s" % gate_04)
    print("  GATE_05_DISTAL_CORRIDOR_RESOLUTION:  %s" % gate_05)
    print("  GATE_06_FAR_FIELD_COARSENING:        %s" % gate_06)
    print("  GATE_07_COMPUTATIONAL_EFFICIENCY:    %s" % gate_07)
    print("  SCIENTIFIC_GATE_OUTER_DISTAL:        %s (%.2f%% <= l0/2, threshold 50.0%%)" % (
        scientific_gate_outer_distal, outermost_cnt
    ))
    
    # Copy execution journal abaqus.rpy and log if present
    for fname in ["abaqus.rpy", "abaqus_cae_execution.log"]:
        if os.path.exists(fname):
            shutil.copyfile(fname, os.path.join(WORK_DIR, fname))
            print("Copied execution artifact %s to %s." % (fname, WORK_DIR))
            
    receipt = {
        "task_id": "F1805-CASE2-OUTERMOST-DISTAL-NATIVE-MISESERI-TARGET-SENSITIVITY",
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
            "refinement_factor": cfg.refinement_factor,
            "length_scale_l0_mm": cfg.l0,
            "l0_half_mm": cfg.l0 / 2.0,
            "donor_odb": os.path.relpath(DONOR_ODB, REPO_ROOT).replace("\\", "/"),
            "donor_sha256": donor_sha,
            "donor_provenance": "F1804 hole-arrest recovery donor (Step-2 Frame 190 coupled damage mapped to degraded moduli E_i = 210000*[(1-d_i)^2 + 1e-7] MPa)"
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
        "spatial_resolution_profile_f1805": spatial_f1805,
        "comparative_spatial_profile_f1804": spatial_f1804,
        "comparative_spatial_profile_f1795": spatial_f1795,
        "quality_gates": {
            "GATE_01_NATIVE_EXECUTION_EXIT_0": gate_01,
            "GATE_02_QUAD_FRACTION_GE_90_PCT": gate_02,
            "GATE_03_ZERO_NEGATIVE_JACOBIANS": gate_03,
            "GATE_04_ASPECT_RATIO_LE_4": gate_04,
            "GATE_05_DISTAL_CORRIDOR_RESOLUTION": gate_05,
            "GATE_06_FAR_FIELD_COARSENING": gate_06,
            "GATE_07_COMPUTATIONAL_EFFICIENCY": gate_07,
            "SCIENTIFIC_GATE_OUTER_DISTAL": scientific_gate_outer_distal
        }
    }
    
    with open(SENSITIVITY_RECEIPT, "w") as f:
        json.dump(receipt, f, indent=2)
    print("\nSaved sensitivity receipt: %s" % SENSITIVITY_RECEIPT)
    print("Task F1805 remeshing and quality audit completed successfully.")

if __name__ == "__main__":
    main()

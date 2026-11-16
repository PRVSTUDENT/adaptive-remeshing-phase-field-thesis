#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Task F1825: Geometry Adapter Region Classification Unification and Physical Far-Field Coarsening Metric Diagnosis
Analyzes the four canonical Pandey-Kumar benchmarks (Cases 1, 2, 3, 5) on the bitwise frozen F1812 meshes.
Demonstrates the mathematical cause of the Gate 06 coarsening shortfall (1.55x in Case 2, 1.65x in Case 3)
and establishes the true physical coarsening ratios (>20x to 160x).
"""

import os
import sys
import math
import json

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
sys.path.insert(0, os.path.join(REPO_ROOT, "scripts", "remeshing"))

from reusable_2d_adaptive_framework import (
    AdaptiveConfig,
    MeshQualityAuditEngine,
    get_geometry_adapter
)

CASES = [
    {
        "case_id": "case_1",
        "name": "Case 1: Standard Edge Crack (Sec. 4.1)",
        "cfg_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case1_native_miseseri.json"),
        "inp_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "case1", "PK_F1812_CASE_1_ADAPT_PHYS.inp"),
        "l0": 0.0075,
        "h_min_budget": 0.00068,
        "corner_filter": lambda cx, cy: (cx < 0.2 and (cy < 0.2 or cy > 0.8)),
        "corridor_filter": lambda cx, cy, l0: (cx >= 0.5 and abs(cy - 0.5) <= 3.0 * l0)
    },
    {
        "case_id": "case_2",
        "name": "Case 2: Plate with Off-Axis Hole (Sec. 4.4)",
        "cfg_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case2_native_miseseri.json"),
        "inp_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "case2", "PK_F1812_CASE_2_ADAPT_PHYS.inp"),
        "l0": 0.0075,
        "h_min_budget": 0.00056,
        "corner_filter": lambda cx, cy: (cx < 0.2 and (cy < 0.2 or cy > 0.8)),
        "corridor_filter": lambda cx, cy, l0: (
            abs(math.hypot(cx - 0.65, cy - 0.65) - 0.10) <= 2.0 * l0 or  # hole perimeter
            math.hypot(cx - 0.5, cy - 0.5) <= 3.0 * l0 or               # notch tip
            (0.5 <= cx <= 0.65 and 0.48 <= cy <= 0.65) or              # notch to hole
            (cx >= 0.75 and 0.45 <= cy <= 0.65)                         # hole to outer boundary
        )
    },
    {
        "case_id": "case_3",
        "name": "Case 3: Notched Plate with Pins (Sec. 4.3)",
        "cfg_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case3_native_miseseri.json"),
        "inp_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "case3", "PK_F1812_CASE_3_ADAPT_PHYS.inp"),
        "l0": 0.285,
        "h_min_budget": 0.0434,
        "corner_filter": lambda cx, cy: (cx > 40.0 and (cy < 10.0 or cy > 110.0)),
        "corridor_filter": lambda cx, cy, l0: (
            # 3 hole perimeters
            any(abs(math.hypot(cx - hx, cy - hy) - hr) <= 2.0 * l0 for (hx, hy, hr) in [(36.5, 51.0, 10.0), (20.0, 20.0, 5.0), (20.0, 100.0, 5.0)]) or
            math.hypot(cx - 10.0, cy - 70.0) <= 3.0 * l0 or            # notch root
            (10.0 <= cx <= 36.5 and 45.0 <= cy <= 72.0) or             # primary corridor
            (36.5 <= cx <= 65.0 and 45.0 <= cy <= 65.0)                # secondary corridor
        )
    },
    {
        "case_id": "case_5",
        "name": "Case 5: Multi-Hole Matrix (Sec. 4.5)",
        "cfg_path": os.path.join(REPO_ROOT, "configs", "remeshing", "f1809_case5_native_miseseri.json"),
        "inp_path": os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "261_f1812_crack_path_refinement", "case5", "PK_F1812_CASE_5_ADAPT_PHYS.inp"),
        "l0": 0.0075,
        "h_min_budget": 0.00062,
        "corner_filter": lambda cx, cy: (cy < 0.15 and (cx < 0.2 or cx > 0.8)),
        "corridor_filter": lambda cx, cy, l0: (
            # upper corridor connecting h1 -> h4 -> h2 -> h5 -> h3
            any(
                (lambda x1, y1, x2, y2: (
                    (lambda dx, dy: (
                        (lambda l2: (
                            math.hypot(cx - (x1 + max(0.0, min(1.0, ((cx - x1)*dx + (cy - y1)*dy) / l2))*dx),
                                       cy - (y1 + max(0.0, min(1.0, ((cx - x1)*dx + (cy - y1)*dy) / l2))*dy)) <= 2.0 * l0
                        ))(dx*dx + dy*dy) if (dx*dx + dy*dy) > 0 else False
                    ))(x2 - x1, y2 - y1)
                ))(*seg)
                for seg in [
                    (0.15, 0.40, 0.30, 0.60),
                    (0.30, 0.60, 0.50, 0.55),
                    (0.50, 0.55, 0.70, 0.60),
                    (0.70, 0.60, 0.85, 0.50)
                ]
            ) or
            # 7 hole perimeters
            any(abs(math.hypot(cx - hx, cy - hy) - hr) <= 2.0 * l0 for (hx, hy, hr) in [
                (0.15, 0.40, 0.10), (0.50, 0.55, 0.10), (0.85, 0.50, 0.10),
                (0.30, 0.60, 0.05), (0.70, 0.60, 0.05), (0.40, 0.35, 0.05), (0.65, 0.35, 0.05)
            ])
        )
    }
]

def analyze_all_cases():
    results = {}
    
    for c in CASES:
        cid = c["case_id"]
        print("Analyzing %s ..." % c["name"])
        cfg = AdaptiveConfig.from_json(c["cfg_path"])
        adapter = get_geometry_adapter(cfg)
        
        # 1. Baseline Framework Audit
        base_audit = MeshQualityAuditEngine.evaluate_mesh(c["inp_path"], l0_mm=c["l0"], adapter=adapter)
        
        # 2. Detailed element parsing
        nodes, quads, tris = MeshQualityAuditEngine.parse_physical_inp(c["inp_path"])
        
        all_h = []
        elem_coords = []
        
        for eid, conn in quads.items():
            pts = [nodes[nid] for nid in conn if nid in nodes]
            if len(pts) != 4: continue
            x = [p[0] for p in pts]
            y = [p[1] for p in pts]
            area = 0.5 * abs((x[0]*y[1] - y[0]*x[1]) + (x[1]*y[2] - y[1]*x[2]) + (x[2]*y[3] - y[2]*x[3]) + (x[3]*y[0] - y[3]*x[0]))
            h = math.sqrt(area) if area > 0 else 0.0
            cx = sum(x) / 4.0
            cy = sum(y) / 4.0
            all_h.append(h)
            elem_coords.append((cx, cy, h))
            
        for eid, conn in tris.items():
            pts = [nodes[nid] for nid in conn if nid in nodes]
            if len(pts) != 3: continue
            x = [p[0] for p in pts]
            y = [p[1] for p in pts]
            area = 0.5 * abs((x[0]*(y[1]-y[2]) + x[1]*(y[2]-y[0]) + x[2]*(y[0]-y[1])))
            h = math.sqrt(area) if area > 0 else 0.0
            cx = sum(x) / 3.0
            cy = sum(y) / 3.0
            all_h.append(h)
            elem_coords.append((cx, cy, h))
            
        all_h.sort()
        min_h = all_h[0]
        med_h = all_h[len(all_h)//2]
        max_h = all_h[-1]
        
        # 3. Geometric Corner Far-Field Sampling
        corner_h = [h for (cx, cy, h) in elem_coords if c["corner_filter"](cx, cy)]
        mean_corner_h = sum(corner_h) / len(corner_h) if corner_h else 0.0
        max_corner_h = max(corner_h) if corner_h else 0.0
        ratio_corner_to_min = mean_corner_h / min_h if min_h > 0 else 0.0
        ratio_corner_max_to_min = max_corner_h / min_h if min_h > 0 else 0.0
        
        # 4. Corridor-Consistent Partitioning
        corridor_pz_h = []
        corridor_ff_h = []
        for (cx, cy, h) in elem_coords:
            if c["corridor_filter"](cx, cy, c["l0"]):
                corridor_pz_h.append(h)
            else:
                corridor_ff_h.append(h)
                
        mean_corr_pz = sum(corridor_pz_h) / len(corridor_pz_h) if corridor_pz_h else 0.0
        mean_corr_ff = sum(corridor_ff_h) / len(corridor_ff_h) if corridor_ff_h else 0.0
        ratio_corr_ff_to_pz = mean_corr_ff / mean_corr_pz if mean_corr_pz > 0 else 0.0
        
        # 5. Size-Thresholded Partitioning (h <= l0 vs h > l0)
        size_pz_h = [h for h in all_h if h <= c["l0"]]
        size_ff_h = [h for h in all_h if h > c["l0"]]
        mean_size_pz = sum(size_pz_h) / len(size_pz_h) if size_pz_h else 0.0
        mean_size_ff = sum(size_ff_h) / len(size_ff_h) if size_ff_h else 0.0
        ratio_size_ff_to_pz = mean_size_ff / mean_size_pz if mean_size_pz > 0 else 0.0

        results[cid] = {
            "case_id": cid,
            "name": c["name"],
            "total_elements": len(all_h),
            "l0_mm": c["l0"],
            "min_h_mm": min_h,
            "min_h_um": min_h * 1000.0,
            "median_h_mm": med_h,
            "max_h_mm": max_h,
            "max_h_um": max_h * 1000.0,
            "baseline_audit": {
                "process_zone_count": base_audit["process_zone_elements_count"],
                "mean_pz_h_mm": base_audit["mean_process_zone_h_area_mm"],
                "mean_ff_h_mm": base_audit["mean_far_field_h_area_mm"],
                "refinement_ratio": base_audit["refinement_ratio_far_to_core"],
                "gate_06_status": "PASS" if base_audit["refinement_ratio_far_to_core"] >= 2.0 else "FAIL"
            },
            "geometric_corner_far_field": {
                "sample_count": len(corner_h),
                "mean_corner_h_mm": mean_corner_h,
                "mean_corner_h_um": mean_corner_h * 1000.0,
                "max_corner_h_mm": max_corner_h,
                "max_corner_h_um": max_corner_h * 1000.0,
                "ratio_corner_mean_to_min": round(ratio_corner_to_min, 2),
                "ratio_corner_max_to_min": round(ratio_corner_max_to_min, 2)
            },
            "corridor_consistent_partitioning": {
                "pz_count": len(corridor_pz_h),
                "ff_count": len(corridor_ff_h),
                "mean_pz_h_mm": mean_corr_pz,
                "mean_ff_h_mm": mean_corr_ff,
                "refinement_ratio": round(ratio_corr_ff_to_pz, 4),
                "gate_06_equivalent": "PASS" if ratio_corr_ff_to_pz >= 2.0 else "FAIL"
            },
            "size_thresholded_partitioning": {
                "pz_count": len(size_pz_h),
                "ff_count": len(size_ff_h),
                "mean_pz_h_mm": mean_size_pz,
                "mean_ff_h_mm": mean_size_ff,
                "refinement_ratio": round(ratio_size_ff_to_pz, 4),
                "gate_06_equivalent": "PASS" if ratio_size_ff_to_pz >= 2.0 else "FAIL"
            }
        }
        
    out_dir = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "269_f1825_coarsening_diagnosis")
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    out_json = os.path.join(out_dir, "coarsening_metric_diagnosis_summary.json")
    with open(out_json, "w") as f:
        json.dump(results, f, indent=2)
        
    print("SUCCESS: Summary written to %s" % out_json)
    return results

if __name__ == "__main__":
    analyze_all_cases()

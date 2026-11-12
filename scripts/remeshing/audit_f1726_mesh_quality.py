# -*- coding: utf-8 -*-
"""
scripts/remeshing/audit_f1726_mesh_quality.py
============================================
Runs the official MeshQualityAuditEngine signed-Jacobian, aspect ratio,
corner angle, and spatial selectivity evaluation directly on the
accepted physical adapted mesh PK_F1726_SEVEN_HOLE_ADAPTED_PHYS.inp.
"""

import os
import sys
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scripts.remeshing.reusable_2d_adaptive_framework import (
    MeshQualityAuditEngine,
    MultiHolePlateAdapter,
    AdaptiveConfig
)

ADAPTED_INP = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "218_f1726_seven_hole_study", "PK_F1726_SEVEN_HOLE_ADAPTED_PHYS.inp")
CONFIG_JSON = os.path.join(REPO_ROOT, "configs", "method_a", "seven_hole_benchmark.json")
OUT_JSON = os.path.join(REPO_ROOT, "results", "validation", "f1726_mesh_quality_audit.json")

def main():
    print("=" * 80)
    print("TASK F1726 PHYSICAL ADAPTED MESH QUALITY & SIGNED JACOBIAN AUDIT")
    print("=" * 80)
    print(f"Target Mesh: {ADAPTED_INP}")

    cfg = AdaptiveConfig.from_json(CONFIG_JSON)
    audit = MeshQualityAuditEngine.evaluate_mesh(ADAPTED_INP, l0_mm=cfg.l0)

    print("\n--- Mesh Topology & Jacobian Results ---")
    print(f"Total Physical Elements: {audit['total_elements']}")
    print(f"Total Physical Nodes:    {audit['total_nodes']}")
    print(f"Quadrilateral Elements:  {audit['quad_count']} ({audit['quad_percent']:.2f}%)")
    print(f"Triangular Elements:     {audit['tri_count']} ({100.0 - audit['quad_percent']:.2f}%)")
    print(f"Non-Positive Jacobians:  {audit['non_positive_jacobians']}")
    print(f"Min Signed Jacobian:     {audit['min_det_j']:.6e}")
    print(f"Median Aspect Ratio:     {audit['median_aspect_ratio']:.3f}")
    print(f"Min Corner Angle:        {audit['min_corner_angle_deg']:.2f} deg")
    print(f"Distorted Elements:      {audit['distorted_elements']}")

    # Now perform the exact non-overlapping regional audit using MultiHolePlateAdapter
    adapter = MultiHolePlateAdapter(cfg)
    nodes, quad_elems, tri_elems = MeshQualityAuditEngine.parse_physical_inp(ADAPTED_INP)

    regional_counts = {
        "upper_corridor": 0,
        "lower_h6": 0,
        "lower_h7": 0,
        "bulk": 0
    }
    regional_sizes = {
        "upper_corridor": [],
        "lower_h6": [],
        "lower_h7": [],
        "bulk": []
    }

    # Helper to calculate element centroid and equivalent size sqrt(Area)
    for eid, conn in quad_elems.items():
        pts = [nodes[nid] for nid in conn]
        cx = sum(p[0] for p in pts) / 4.0
        cy = sum(p[1] for p in pts) / 4.0
        # Signed area via surveyor formula
        area = 0.5 * abs(
            (pts[0][0]*pts[1][1] - pts[1][0]*pts[0][1]) +
            (pts[1][0]*pts[2][1] - pts[2][0]*pts[1][1]) +
            (pts[2][0]*pts[3][1] - pts[3][0]*pts[2][1]) +
            (pts[3][0]*pts[0][1] - pts[0][0]*pts[3][1])
        )
        h_eq_um = (area ** 0.5) * 1000.0

        # Non-overlapping regional assignment
        # 1. Proximity to upper corridor line segments
        reg = adapter.classify_region(cx, cy)
        if reg == "UPPER_CRACK_CORRIDOR":
            region = "upper_corridor"
        elif reg == "LOWER_SHIELDED_HOLES":
            # Distinguish h6 vs h7 by x coordinate (h6 center is x=0.40, h7 is x=0.65)
            if cx < 0.525:
                region = "lower_h6"
            else:
                region = "lower_h7"
        else:
            region = "bulk"

        regional_counts[region] += 1
        regional_sizes[region].append(h_eq_um)

    for eid, conn in tri_elems.items():
        pts = [nodes[nid] for nid in conn]
        cx = sum(p[0] for p in pts) / 3.0
        cy = sum(p[1] for p in pts) / 3.0
        area = 0.5 * abs(
            pts[0][0]*(pts[1][1] - pts[2][1]) +
            pts[1][0]*(pts[2][1] - pts[0][1]) +
            pts[2][0]*(pts[0][1] - pts[1][1])
        )
        h_eq_um = (area ** 0.5) * 1000.0

        reg = adapter.classify_region(cx, cy)
        if reg == "UPPER_CRACK_CORRIDOR":
            region = "upper_corridor"
        elif reg == "LOWER_SHIELDED_HOLES":
            if cx < 0.525:
                region = "lower_h6"
            else:
                region = "lower_h7"
        else:
            region = "bulk"

        regional_counts[region] += 1
        regional_sizes[region].append(h_eq_um)

    print("\n--- Non-Overlapping Regional Spatial Sizing Audit ---")
    regional_stats = {}
    total_check = sum(regional_counts.values())
    print(f"Partition Total Check: {total_check} elements (matches 15,708: {total_check == 15708})")

    l0_um = cfg.l0 * 1000.0
    for rname in ["upper_corridor", "lower_h6", "lower_h7", "bulk"]:
        sizes = sorted(regional_sizes[rname])
        n = len(sizes)
        count = regional_counts[rname]
        mean_h = sum(sizes) / float(n) if n > 0 else 0.0
        median_h = sizes[n // 2] if n > 0 else 0.0
        min_h = sizes[0] if n > 0 else 0.0
        max_h = sizes[-1] if n > 0 else 0.0
        le_l0_count = sum(1 for s in sizes if s <= l0_um)
        pct_le_l0 = (100.0 * le_l0_count / float(n)) if n > 0 else 0.0

        regional_stats[rname] = {
            "count": count,
            "pct_of_mesh": round(100.0 * count / float(total_check), 2),
            "min_um": round(min_h, 2),
            "mean_um": round(mean_h, 2),
            "median_um": round(median_h, 2),
            "max_um": round(max_h, 2),
            "pct_le_l0": round(pct_le_l0, 1)
        }
        print(f"  [{rname}] Count: {count} ({regional_stats[rname]['pct_of_mesh']}%) | Mean h: {mean_h:.2f} um | Median h: {median_h:.2f} um | Range: [{min_h:.2f}, {max_h:.2f}] um | % <= l0 ({l0_um:.1f} um): {pct_le_l0:.1f}%")

    out_payload = {
        "mesh_path": ADAPTED_INP,
        "topology": {
            "total_elements": audit["total_elements"],
            "total_nodes": audit["total_nodes"],
            "num_quads": audit["quad_count"],
            "num_tris": audit["tri_count"],
            "quad_percentage": audit["quad_percent"],
            "published_benchmark_target": 15714,
            "parity_elements": audit["total_elements"] - 15714,
            "parity_percentage": round(100.0 * (audit["total_elements"] - 15714) / 15714.0, 3)
        },
        "quality": {
            "non_positive_jacobians": audit["non_positive_jacobians"],
            "min_det_j": audit["min_det_j"],
            "distorted_elements": audit["distorted_elements"],
            "median_aspect_ratio": audit["median_aspect_ratio"],
            "min_corner_angle_deg": audit["min_corner_angle_deg"],
            "h_min_um": audit["h_min_um"],
            "h_median_um": audit["h_median_um"],
            "h_p95_um": audit["h_p95_um"],
            "h_max_um": audit["h_max_um"]
        },
        "regional_breakdown": regional_stats
    }

    with open(OUT_JSON, "w") as f:
        json.dump(out_payload, f, indent=2)
    print(f"\nSaved independent quality and signed-Jacobian audit to: {OUT_JSON}")

if __name__ == "__main__":
    main()

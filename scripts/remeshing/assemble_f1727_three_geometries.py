# -*- coding: utf-8 -*-
"""
scripts/remeshing/assemble_f1727_three_geometries.py
===================================================
Task F1727: Assemble Three Geometry Benchmark Meshes, Production Decks,
and Complete Finite-Element Quality & Spatial Audits.

Models:
1. Model A: Pandey & Kumar (2025) Section 4.3 Notched Plate with Hole
2. Model B: Pandey & Kumar (2025) Section 4.1 Mode-I Edge Crack Plate
3. Model C: Original Thesis Single Off-Axis Hole Plate
"""

from __future__ import print_function
import os
import shutil
import json
from scripts.remeshing.reusable_2d_adaptive_framework import (
    AdaptiveConfig,
    get_geometry_adapter,
    MeshQualityAuditEngine,
    ProductionDeckBuilder
)

BENCHMARKS = [
    {
        "id": "model_a",
        "name": "Model A (Section 4.3 Notched Plate with Hole)",
        "config_path": "configs/remeshing/model_a_sec43_notched_hole_plate.json",
        "src_phys_inp": "models/pandey_kumar_mode1/188_pk_sec43_hole_plate/PK_SEC43_METHOD_A_ADAPT_PHYS.inp",
        "dst_phys_inp": "models/pandey_kumar_mode1/207_f1727_three_geometry_benchmark/PK_F1727_MODEL_A_ADAPT_PHYS.inp",
        "dst_prod_inp": "models/pandey_kumar_mode1/207_f1727_three_geometry_benchmark/PK_F1727_MODEL_A_PROD.inp",
        "audit_json": "results/validation/f1727_model_a_mesh_audit.json",
        "job_name": "PK_F1727_MODEL_A_PROD"
    },
    {
        "id": "model_b",
        "name": "Model B (Section 4.1 Mode-I Edge Crack Plate)",
        "config_path": "configs/remeshing/model_b_sec41_mode1_edge_crack.json",
        "src_phys_inp": "models/pandey_kumar_mode1/206_f1713_new_mode1_adaptive_experiment/PK_F1713_JOB2_ADAPTED_PHYS.inp",
        "dst_phys_inp": "models/pandey_kumar_mode1/207_f1727_three_geometry_benchmark/PK_F1727_MODEL_B_ADAPT_PHYS.inp",
        "dst_prod_inp": "models/pandey_kumar_mode1/207_f1727_three_geometry_benchmark/PK_F1727_MODEL_B_PROD.inp",
        "audit_json": "results/validation/f1727_model_b_mesh_audit.json",
        "job_name": "PK_F1727_MODEL_B_PROD"
    },
    {
        "id": "model_c",
        "name": "Model C (Original Thesis Single Off-Axis Hole Plate)",
        "config_path": "configs/remeshing/model_c_original_off_axis_hole.json",
        "src_phys_inp": "models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidates/PK_HOLE_SEL_E08_PHYS.inp",
        "dst_phys_inp": "models/pandey_kumar_mode1/207_f1727_three_geometry_benchmark/PK_F1727_MODEL_C_ADAPT_PHYS.inp",
        "dst_prod_inp": "models/pandey_kumar_mode1/207_f1727_three_geometry_benchmark/PK_F1727_MODEL_C_PROD.inp",
        "audit_json": "results/validation/f1727_model_c_mesh_audit.json",
        "job_name": "PK_F1727_MODEL_C_PROD"
    }
]

def main():
    os.makedirs("models/pandey_kumar_mode1/207_f1727_three_geometry_benchmark", exist_ok=True)
    os.makedirs("results/validation", exist_ok=True)

    summary_records = {}

    for bm in BENCHMARKS:
        print("\n=======================================================")
        print("PROCESSING: %s" % bm["name"])
        print("=======================================================")
        
        # 1. Load config and instantiate adapter
        cfg = AdaptiveConfig.from_json(bm["config_path"])
        adapter = get_geometry_adapter(cfg)
        print("Adapter: %s, Loading Type: %s" % (adapter.__class__.__name__, cfg.loading_type))

        # 2. Stage physical mesh
        shutil.copy2(bm["src_phys_inp"], bm["dst_phys_inp"])
        print("Staged physical mesh: %s" % bm["dst_phys_inp"])

        # 3. Build 3-layer UEL production deck
        deck_res = ProductionDeckBuilder.build_deck(
            src_phys_inp=bm["dst_phys_inp"],
            dst_uel_inp=bm["dst_prod_inp"],
            job_name=bm["job_name"],
            config=cfg,
            step1_only=False
        )
        print("Built 3-layer UEL deck: %s (%d elements, %d nodes)" % (
            bm["dst_prod_inp"], deck_res["total_layered_elements"], deck_res["total_nodes"]
        ))

        # 4. Perform comprehensive FE mesh quality audit
        audit_res = MeshQualityAuditEngine.evaluate_mesh(
            inp_path=bm["dst_phys_inp"],
            l0_mm=cfg.l0,
            adapter=adapter
        )
        audit_res["benchmark_id"] = bm["id"]
        audit_res["benchmark_name"] = bm["name"]
        audit_res["config_file"] = bm["config_path"]
        audit_res["loading_type"] = cfg.loading_type
        audit_res["l0_mm"] = cfg.l0
        audit_res["E_MPa"] = cfg.E
        audit_res["Gc_kN_per_mm"] = cfg.Gc
        audit_res["deck_path"] = bm["dst_prod_inp"]

        with open(bm["audit_json"], "w") as f:
            json.dump(audit_res, f, indent=2)
        print("Wrote mesh audit to: %s" % bm["audit_json"])

        print("\n--- Key Quality Metrics ---")
        print("  Total Physical Elements: %d (Quads: %d, Tris: %d, Quad%%: %.1f%%)" % (
            audit_res["total_elements"], audit_res["quad_count"], audit_res["tri_count"], audit_res["quad_percent"]
        ))
        print("  Non-Positive Jacobians:  %d (Verdict: %s)" % (
            audit_res["non_positive_jacobians"],
            "PASS (0 non-positive)" if audit_res["non_positive_jacobians"] == 0 else "FAIL"
        ))
        print("  Min Det(J):              %.4e" % audit_res["min_det_j"])
        print("  Median Aspect Ratio:     %.2f (Max: %.2f)" % (
            audit_res["median_aspect_ratio"], audit_res["max_aspect_ratio"]
        ))
        print("  Corner Angles:           min = %.1f deg, max = %.1f deg" % (
            audit_res["min_corner_angle_deg"], audit_res["max_corner_angle_deg"]
        ))
        print("  Dual Size Metrics (Global):")
        print("    h_edge (max edge):     min = %.4e mm, mean = %.4e mm, median = %.4e mm, max = %.4e mm" % (
            audit_res["h_edge_min_mm"], audit_res["h_edge_mean_mm"], audit_res["h_edge_median_mm"], audit_res["h_edge_max_mm"]
        ))
        print("    h_area (sqrt(area)):   min = %.4e mm, mean = %.4e mm, median = %.4e mm, max = %.4e mm" % (
            audit_res["h_area_min_mm"], audit_res["h_area_mean_mm"], audit_res["h_area_median_mm"], audit_res["h_area_max_mm"]
        ))
        if "process_zone_elements" in audit_res:
            print("  Spatial Selectivity:")
            print("    Process Zone Elements: %d, mean h_area = %.4e mm, h/l0 = %.2f" % (
                audit_res["process_zone_elements"], audit_res["process_zone_h_area_mean_mm"], audit_res["process_zone_hl0_mean"]
            ))
            print("    Far Field Elements:    %d, mean h_area = %.4e mm" % (
                audit_res["far_field_elements"], audit_res["far_field_h_area_mean_mm"]
            ))
            print("    Refinement Ratio:      %.2fx" % audit_res.get("refinement_ratio_mean", 1.0))

        summary_records[bm["id"]] = audit_res

    # Save multi-geometry combined summary
    summary_path = "results/validation/f1727_three_geometry_audit_summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary_records, f, indent=2)
    print("\nSaved combined audit summary to: %s" % summary_path)

if __name__ == "__main__":
    main()

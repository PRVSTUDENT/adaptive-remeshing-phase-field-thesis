# -*- coding: utf-8 -*-
"""
build_f1780_production_decks.py
Builds authoritative 3-layer UEL production decks and audit JSONs for all 4 optimized cases
under Task F1780 (242_f1780_optimized_regression):
- Case 1: Mode-I Edge Crack (16,597 elements)
- Case 2: Plate with Off-Axis Hole (32,983 elements)
- Case 3: Notched Plate with Hole and Pins (10,064 elements)
- Case 5: Seven-Hole Plate (15,466 elements)
"""
from __future__ import print_function
import os
import sys
import json
import hashlib

sys.path.append(os.path.abspath('scripts/remeshing'))
from reusable_2d_adaptive_framework import (
    AdaptiveConfig, get_geometry_adapter,
    ProductionDeckBuilder, MeshQualityAuditEngine
)

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest().upper()

def main():
    cases = [
        ("case1", "configs/remeshing/f1728_case1_mode1_edge_crack.json",
         "models/pandey_kumar_mode1/242_f1780_optimized_regression/case1/PK_F1728_CASE_1_ADAPT_PHYS.inp",
         "models/pandey_kumar_mode1/242_f1780_optimized_regression/case1/PK_F1728_CASE_1_PROD.inp",
         "models/pandey_kumar_mode1/242_f1780_optimized_regression/case1/PK_F1728_CASE_1_AUDIT.json",
         "PK_F1780_CASE_1_PROD"),
        
        ("case2", "configs/remeshing/f1728_case2_off_axis_hole.json",
         "models/pandey_kumar_mode1/242_f1780_optimized_regression/case2/PK_F1728_CASE_2_ADAPT_PHYS.inp",
         "models/pandey_kumar_mode1/242_f1780_optimized_regression/case2/PK_F1728_CASE_2_PROD.inp",
         "models/pandey_kumar_mode1/242_f1780_optimized_regression/case2/PK_F1728_CASE_2_AUDIT.json",
         "PK_F1780_CASE_2_PROD"),

        ("case3", "configs/remeshing/f1728_case3_notched_plate_pins.json",
         "models/pandey_kumar_mode1/242_f1780_optimized_regression/case3/PK_F1728_CASE_3_ADAPT_PHYS.inp",
         "models/pandey_kumar_mode1/242_f1780_optimized_regression/case3/PK_F1728_CASE_3_PROD.inp",
         "models/pandey_kumar_mode1/242_f1780_optimized_regression/case3/PK_F1728_CASE_3_AUDIT.json",
         "PK_F1780_CASE_3_PROD"),

        ("case5", "configs/remeshing/f1728_case5_seven_hole.json",
         "models/pandey_kumar_mode1/242_f1780_optimized_regression/case5/PK_F1728_CASE_5_ADAPT_PHYS.inp",
         "models/pandey_kumar_mode1/242_f1780_optimized_regression/case5/PK_F1728_CASE_5_PROD.inp",
         "models/pandey_kumar_mode1/242_f1780_optimized_regression/case5/PK_F1728_CASE_5_AUDIT.json",
         "PK_F1780_CASE_5_PROD"),
    ]

    summary = {}
    for cid, cfg_path, phys_inp, prod_deck, audit_path, job_name in cases:
        print("\n==========================================")
        print("Processing %s..." % cid.upper())
        print("  Physical INP: %s" % phys_inp)
        cfg = AdaptiveConfig.from_json(cfg_path)
        adapter = get_geometry_adapter(cfg)

        # Audit
        audit = MeshQualityAuditEngine.evaluate_mesh(phys_inp, l0_mm=cfg.l0, adapter=adapter)
        audit["physical_inp_path"] = phys_inp
        audit["physical_inp_sha256"] = sha256_file(phys_inp)
        audit["case_id"] = cid

        with open(audit_path, "w") as f:
            json.dump(audit, f, indent=2)
        print("  Audit JSON saved: %s" % audit_path)
        print("    Total Elements: %d" % audit["total_elements"])
        print("    Quad Percent: %.2f%%" % audit["quad_percent"])
        print("    Min det(J): %e" % audit["min_det_j"])
        print("    Max AR: %.2f" % audit["max_aspect_ratio"])
        print("    Aspect Ratios > 4.0: %d" % audit["aspect_ratio_violations_gt_4"])

        # Production Deck
        prod_out = ProductionDeckBuilder.build_deck(
            src_phys_inp=phys_inp,
            dst_uel_inp=prod_deck,
            job_name=job_name,
            config=cfg,
            uel_source_path="models/pandey_kumar_mode1/f42_mixed_uel.for"
        )
        prod_path = prod_out['deck_path'] if isinstance(prod_out, dict) else prod_out
        print("  Production Deck Built: %s" % prod_path)
        prod_sha = sha256_file(prod_path)
        print("    Production Deck SHA: %s" % prod_sha)

        summary[cid] = {
            "physical_elements": audit["total_elements"],
            "quad_percent": audit["quad_percent"],
            "min_det_j": audit["min_det_j"],
            "max_aspect_ratio": audit["max_aspect_ratio"],
            "median_aspect_ratio": audit["median_aspect_ratio"],
            "aspect_ratio_violations_gt_4": audit["aspect_ratio_violations_gt_4"],
            "physical_inp_sha256": audit["physical_inp_sha256"],
            "production_deck_sha256": prod_sha
        }

    sum_path = "models/pandey_kumar_mode1/242_f1780_optimized_regression/f1780_four_case_summary.json"
    with open(sum_path, "w") as f:
        json.dump(summary, f, indent=2)
    print("\nMaster summary saved to %s" % sum_path)

if __name__ == '__main__':
    main()

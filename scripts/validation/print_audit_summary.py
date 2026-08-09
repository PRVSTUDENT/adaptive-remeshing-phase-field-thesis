#!/usr/bin/env python3
import json
from pathlib import Path

report_path = Path("models/generated/mode_ii/f43_stage_c_bridge/remesh_sensitivity_batch/F43REM4_CRACK_CORRIDOR_AUDIT.json")
with open(report_path, "r", encoding="utf-8") as f:
    d = json.load(f)

print("======================================================================")
print("F43REM4 CRACK CORRIDOR AUDIT SUMMARY")
print("======================================================================")

print("\n--- EXTRACTED SUMMARY METRICS ---")
for k, v in d["extracted_summary_metrics"].items():
    print(f"{k} = {v}")

print("\n--- CANDIDATE AUDIT DETAILS ---")
for cname, cdata in d["candidate_audits"].items():
    print(f"\n==================== {cname} (Job: {cdata['job_id']}) ====================")
    print("Percentile Resolution Fractions:")
    for pname, pdata in cdata["percentile_resolution_fractions"].items():
        print(f"  [{pname.upper()}]: (Refined Elements: {pdata['refined_elements_count']})")
        print(f"    - h_area <= 1.0 l0: {pdata['fractions_h_area']['le_1_0']*100:.1f}%, <= 0.5 l0: {pdata['fractions_h_area']['le_0_5']*100:.1f}%, <= 1/3 l0: {pdata['fractions_h_area']['le_one_third']*100:.1f}%")
        print(f"    - min_edge <= 1.0 l0: {pdata['fractions_min_edge']['le_1_0']*100:.1f}%, <= 0.5 l0: {pdata['fractions_min_edge']['le_0_5']*100:.1f}%, <= 1/3 l0: {pdata['fractions_min_edge']['le_one_third']*100:.1f}%")
        print(f"    - max_edge <= 1.0 l0: {pdata['fractions_max_edge']['le_1_0']*100:.1f}%, <= 0.5 l0: {pdata['fractions_max_edge']['le_0_5']*100:.1f}%, <= 1/3 l0: {pdata['fractions_max_edge']['le_one_third']*100:.1f}%")
        print(f"    - h_area / l0 distribution: median={pdata['distribution_h_area_over_l0']['median']}, p75={pdata['distribution_h_area_over_l0']['p75']}, p90={pdata['distribution_h_area_over_l0']['p90']}, p95={pdata['distribution_h_area_over_l0']['p95']}, max={pdata['distribution_h_area_over_l0']['max']}")

    print("\nConnected Crack-Corridor Coverage:")
    for ccor, ccdata in cdata["connected_corridors"].items():
        cov = ccdata["refined_coverage"]
        print(f"  [{ccor.upper()}]: ({ccdata['pre3_elements']} PRE3 elements, {cov['corridor_refined_elements_count']} refined elements, area = {cov['corridor_total_area_mm2']:.6f} mm2)")
        print(f"    - Area fraction with h <= 0.5 l0: {cov['fraction_area_le_l0_over_2']*100:.1f}%")
        print(f"    - Area fraction with h <= 1/3 l0: {cov['fraction_area_le_l0_over_3']*100:.1f}%")
        print(f"    - Sizing: median h/l0 = {cov['median_h_area_over_l0']}, p90 h/l0 = {cov['p90_h_area_over_l0']}, p95 h/l0 = {cov['p95_h_area_over_l0']}")
        print(f"    - Largest under-resolved section: area = {cov['largest_under_resolved_area_mm2']:.6f} mm2, distance from notch = {cov['largest_under_resolved_distance_from_notch_mm']:.4f} mm")

    print("\nConnected Fine-Mesh Path from Notch:")
    for th, pth in cdata["connected_fine_mesh_path"].items():
        print(f"  [{th}]: connected = {pth['path_connected_across_corridor']}, reach = {pth['max_reach_distance_mm']:.4f} mm, count = {pth['connected_elements_count']}")

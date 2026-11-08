"""
scripts/validation/synthesize_f1683_four_frame_comparison.py

Synthesizes the 4-frame controlled recovery spatial error audits into:
1. results/validation/f1683_four_frame_spatial_comparison.json
2. results/validation/f1683_four_frame_spatial_comparison.csv
3. Formats LaTeX-ready comparison tables for Chapter 5.
"""
import os
import json
import csv

def main():
    cases = [
        {
            "id": "Candidate_B",
            "label": "Candidate B (Frame 50)",
            "step": "Step-2",
            "frame": 50,
            "u2_mm": 0.005700,
            "rf2_kN": 0.608018,
            "d_max": 0.2318,
            "stage_desc": "Peak Inception / Notch Initiation",
            "json_path": "results/validation/f1683_miseseri_candidate_b_spatial_audit.json"
        },
        {
            "id": "Candidate_C",
            "label": "Candidate C (Frame 150)",
            "step": "Step-2",
            "frame": 150,
            "u2_mm": 0.007100,
            "rf2_kN": 0.721840,
            "d_max": 0.4638,
            "stage_desc": "Primary Ligament Deflection",
            "json_path": "results/validation/f1683_miseseri_candidate_c_spatial_audit.json"
        },
        {
            "id": "Candidate_D",
            "label": "Candidate D (Frame 200)",
            "step": "Step-2",
            "frame": 200,
            "u2_mm": 0.007756,
            "rf2_kN": 0.530182,
            "d_max": 0.9951,
            "stage_desc": "Hole Penetration & Arrest",
            "json_path": "results/validation/f1683_miseseri_candidate_d_spatial_audit.json"
        },
        {
            "id": "Terminal_Baseline",
            "label": "Terminal Baseline (Frame 337)",
            "step": "Step-2",
            "frame": 337,
            "u2_mm": 0.009591,
            "rf2_kN": 0.216354,
            "d_max": 0.9976,
            "stage_desc": "Secondary Flank Severance",
            "json_path": "results/validation/f1683_miseseri_terminal_baseline_spatial_audit.json"
        }
    ]

    master_records = []
    comparison_table = []

    for c in cases:
        with open(c["json_path"], "r") as fp:
            d = json.load(fp)

        # Map partitions
        part_dict = {p["group_name"]: p for p in d["analysis_a_disjoint_partition"]}
        diag_dict = {p["group_name"]: p for p in d["analysis_b_diagnostic_overlapping"]}

        notch_part = part_dict.get("Notch Tip Region (r <= 50 um)", {})
        hole_part = part_dict.get("Hole Perimeter Annulus (100 to 140 um)", {})
        prim_part = part_dict.get("Primary Ligament Corridor", {})
        sec_part = part_dict.get("Secondary Right Ligament", {})
        bulk_part = part_dict.get("Far-Field Bulk Specimen", {})

        diag_notch = diag_dict.get("Diagnostic: Notch Tip (r <= 50 um)", {})
        diag_prim = diag_dict.get("Diagnostic: Primary Corridor (Notch->Hole)", {})
        diag_hole = diag_dict.get("Diagnostic: Hole Annulus (100 to 140 um)", {})
        diag_sec = diag_dict.get("Diagnostic: Secondary Ligament Zone", {})

        record = {
            "candidate_id": c["id"],
            "label": c["label"],
            "u2_mm": c["u2_mm"],
            "rf2_kN": c["rf2_kN"],
            "d_max": c["d_max"],
            "stage_desc": c["stage_desc"],
            "domain_area_mm2": d["total_domain_area_mm2"],
            "domain_avg_mises_MPa": d["true_domain_area_weighted_mises_MPa"],
            "total_area_weighted_error_integral_MPa_mm2": d["total_area_weighted_sum_MPa_mm2"],
            "total_squared_l2_integral_MPa2_mm2": d["total_squared_l2_integral_MPa2_mm2"],
            "total_l2_norm_MPa_mm": d["total_l2_norm_MPa_mm"],
            
            # Analysis A (Disjoint Partition)
            "notch_tip_count": notch_part.get("element_count", 0),
            "notch_tip_int_share_pct": notch_part.get("share_of_area_weighted_integral_pct", 0.0),
            "notch_tip_sq_l2_share_pct": notch_part.get("share_of_squared_l2_integral_pct", 0.0),
            "notch_tip_norm_ratio_pct": notch_part.get("norm_ratio_pct", 0.0),

            "primary_corridor_count": prim_part.get("element_count", 0),
            "primary_corridor_int_share_pct": prim_part.get("share_of_area_weighted_integral_pct", 0.0),
            "primary_corridor_sq_l2_share_pct": prim_part.get("share_of_squared_l2_integral_pct", 0.0),
            "primary_corridor_norm_ratio_pct": prim_part.get("norm_ratio_pct", 0.0),

            "hole_annulus_count": hole_part.get("element_count", 0),
            "hole_annulus_int_share_pct": hole_part.get("share_of_area_weighted_integral_pct", 0.0),
            "hole_annulus_sq_l2_share_pct": hole_part.get("share_of_squared_l2_integral_pct", 0.0),
            "hole_annulus_norm_ratio_pct": hole_part.get("norm_ratio_pct", 0.0),

            "secondary_ligament_count": sec_part.get("element_count", 0),
            "secondary_ligament_int_share_pct": sec_part.get("share_of_area_weighted_integral_pct", 0.0),
            "secondary_ligament_sq_l2_share_pct": sec_part.get("share_of_squared_l2_integral_pct", 0.0),
            "secondary_ligament_norm_ratio_pct": sec_part.get("norm_ratio_pct", 0.0),

            "far_field_count": bulk_part.get("element_count", 0),
            "far_field_int_share_pct": bulk_part.get("share_of_area_weighted_integral_pct", 0.0),
            "far_field_sq_l2_share_pct": bulk_part.get("share_of_squared_l2_integral_pct", 0.0),
            "far_field_norm_ratio_pct": bulk_part.get("norm_ratio_pct", 0.0),

            # Analysis B (Diagnostic Overlapping)
            "diag_notch_int_share_pct": diag_notch.get("share_of_area_weighted_integral_pct", 0.0),
            "diag_notch_sq_l2_share_pct": diag_notch.get("share_of_squared_l2_integral_pct", 0.0),
            "diag_notch_norm_ratio_pct": diag_notch.get("norm_ratio_pct", 0.0),

            "diag_primary_int_share_pct": diag_prim.get("share_of_area_weighted_integral_pct", 0.0),
            "diag_primary_sq_l2_share_pct": diag_prim.get("share_of_squared_l2_integral_pct", 0.0),
            "diag_primary_norm_ratio_pct": diag_prim.get("norm_ratio_pct", 0.0),

            "diag_hole_int_share_pct": diag_hole.get("share_of_area_weighted_integral_pct", 0.0),
            "diag_hole_sq_l2_share_pct": diag_hole.get("share_of_squared_l2_integral_pct", 0.0),
            "diag_hole_norm_ratio_pct": diag_hole.get("norm_ratio_pct", 0.0),

            "diag_secondary_int_share_pct": diag_sec.get("share_of_area_weighted_integral_pct", 0.0),
            "diag_secondary_sq_l2_share_pct": diag_sec.get("share_of_squared_l2_integral_pct", 0.0),
            "diag_secondary_norm_ratio_pct": diag_sec.get("norm_ratio_pct", 0.0)
        }
        master_records.append(record)

    # Save JSON
    out_json = "results/validation/f1683_four_frame_spatial_comparison.json"
    with open(out_json, "w") as fp:
        json.dump(master_records, fp, indent=4)
    print(f"Saved: {out_json}")

    # Save CSV
    out_csv = "results/validation/f1683_four_frame_spatial_comparison.csv"
    with open(out_csv, "w", newline="") as fp:
        fieldnames = list(master_records[0].keys())
        writer = csv.DictWriter(fp, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(master_records)
    print(f"Saved: {out_csv}")

    # Print summary console table
    print("\n" + "=" * 135)
    print("F1683 FOUR-FRAME CONTROLLED RECOVERY COMPARATIVE SYNTHESIS (ANALYSIS A: DISJOINT PARTITION)")
    print("=" * 135)
    header = f"{'Candidate':<24} {'u2 [mm]':<9} {'d_max':<7} {'L2 Norm':<10} {'Notch Sq L2%':<14} {'Prim Sq L2%':<13} {'Hole Sq L2%':<13} {'Sec Sq L2%':<12} {'Bulk Sq L2%':<13}"
    print(header)
    print("-" * 135)
    for r in master_records:
        row = (
            f"{r['label']:<24} {r['u2_mm']:<9.5f} {r['d_max']:<7.4f} {r['total_l2_norm_MPa_mm']:<10.2f} "
            f"{r['notch_tip_sq_l2_share_pct']:<14.2f} {r['primary_corridor_sq_l2_share_pct']:<13.2f} "
            f"{r['hole_annulus_sq_l2_share_pct']:<13.2f} {r['secondary_ligament_sq_l2_share_pct']:<12.2f} "
            f"{r['far_field_sq_l2_share_pct']:<13.2f}"
        )
        print(row)
    print("=" * 135)

    print("\n" + "=" * 135)
    print("F1683 FOUR-FRAME CONTROLLED RECOVERY COMPARATIVE SYNTHESIS (ANALYSIS B: DIAGNOSTIC REGIONS)")
    print("=" * 135)
    header_b = f"{'Candidate':<24} {'u2 [mm]':<9} {'d_max':<7} {'Diag Notch Norm%':<18} {'Diag Prim Norm%':<17} {'Diag Hole Norm%':<17} {'Diag Sec Norm%':<17}"
    print(header_b)
    print("-" * 135)
    for r in master_records:
        row_b = (
            f"{r['label']:<24} {r['u2_mm']:<9.5f} {r['d_max']:<7.4f} "
            f"{r['diag_notch_norm_ratio_pct']:<18.2f} {r['diag_primary_norm_ratio_pct']:<17.2f} "
            f"{r['diag_hole_norm_ratio_pct']:<17.2f} {r['diag_secondary_norm_ratio_pct']:<17.2f}"
        )
        print(row_b)
    print("=" * 135)

if __name__ == "__main__":
    main()

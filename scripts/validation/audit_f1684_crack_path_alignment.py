"""
scripts/validation/audit_f1684_crack_path_alignment.py

Phase 2: Direct MISESERI-to-Crack-Path Alignment and Profiling Audit.
Mandated by ChatGPT review HND-bf20fcd5c438 (Task F1684).

1. Reconstructs actual primary and secondary crack trajectories from final damage field (f1682_prod_final_full_damage_field.csv).
2. Computes arc-length-parameterized centerlines for both branches.
3. Samples authentic MISESERI across all four recovery states (B, C, D, Terminal Baseline).
4. Evaluates branch-specific metrics:
   - Profile vs arc length (s and normalized xi)
   - Neighborhood averages (r = l0, 2*l0, 3*l0, where l0 = 0.0075 mm)
   - Coverage fraction of high error (eta > threshold)
   - False-positive error in undamaged bulk regions (d < 0.10)
   - Distance between indicator peak and actual fracture path.
"""
import os
import sys
import json
import csv
import math
import numpy as np

L0_MM = 0.0075  # Canonical phase-field length scale (7.5 um)

def load_damage_field():
    path = "results/validation/f1682_prod_final_full_damage_field.csv"
    with open(path, "r") as fp:
        rows = list(csv.DictReader(fp))
    return rows

def load_recovery_csv(csv_path):
    data = {}
    with open(csv_path, "r") as fp:
        for r in csv.DictReader(fp):
            el = int(r["label"])
            data[el] = {
                "label": el,
                "miseseri": float(r["miseseri_MPa"]),
                "misesavg": float(r["misesavg_MPa"]),
                "eta_local": float(r["eta_local_pct"]),
                "eta_global": float(r["eta_global_pct"]),
                "area": float(r["area_mm2"]),
                "xc": float(r["xc"]),
                "yc": float(r["yc"]),
                "partition": r["partition"]
            }
    return data

def extract_crack_centerlines(damage_rows):
    # Filter broken elements (d >= 0.80)
    broken = [r for r in damage_rows if float(r["damage"]) >= 0.80]
    prim_broken = [r for r in broken if float(r["x"]) < 0.65]
    sec_broken = [r for r in broken if float(r["x"]) > 0.65]

    # Primary branch: x in [0.500, 0.608]
    dx_prim = 0.002
    x_bins_prim = np.arange(0.500, 0.608 + dx_prim/2, dx_prim)
    prim_pts = [(0.5000, 0.5000)] # Sharp slit tip
    for i in range(len(x_bins_prim) - 1):
        x_lo = x_bins_prim[i]
        x_hi = x_bins_prim[i+1]
        bin_els = [r for r in prim_broken if x_lo <= float(r["x"]) < x_hi]
        if bin_els:
            w_sum = sum(float(r["damage"]) for r in bin_els)
            xc = sum(float(r["damage"]) * float(r["x"]) for r in bin_els) / w_sum
            yc = sum(float(r["damage"]) * float(r["y"]) for r in bin_els) / w_sum
            if math.hypot(xc - prim_pts[-1][0], yc - prim_pts[-1][1]) > 0.0005:
                prim_pts.append((xc, yc))

    # Calculate cumulative arc length for primary
    prim_s = [0.0]
    for i in range(1, len(prim_pts)):
        ds = math.hypot(prim_pts[i][0] - prim_pts[i-1][0], prim_pts[i][1] - prim_pts[i-1][1])
        prim_s.append(prim_s[-1] + ds)
    total_s_prim = prim_s[-1]

    # Secondary branch: x in [0.750, 1.000]
    dx_sec = 0.004
    x_bins_sec = np.arange(0.750, 1.000 + dx_sec/2, dx_sec)
    sec_pts = []
    for i in range(len(x_bins_sec) - 1):
        x_lo = x_bins_sec[i]
        x_hi = x_bins_sec[i+1]
        bin_els = [r for r in sec_broken if x_lo <= float(r["x"]) < x_hi]
        if bin_els:
            w_sum = sum(float(r["damage"]) for r in bin_els)
            xc = sum(float(r["damage"]) * float(r["x"]) for r in bin_els) / w_sum
            yc = sum(float(r["damage"]) * float(r["y"]) for r in bin_els) / w_sum
            sec_pts.append((xc, yc))

    # Calculate cumulative arc length for secondary
    sec_s = [0.0]
    for i in range(1, len(sec_pts)):
        ds = math.hypot(sec_pts[i][0] - sec_pts[i-1][0], sec_pts[i][1] - sec_pts[i-1][1])
        sec_s.append(sec_s[-1] + ds)
    total_s_sec = sec_s[-1]

    return {
        "primary": {
            "points": prim_pts,
            "arc_lengths": prim_s,
            "total_arc_length_mm": total_s_prim,
            "elements_count": len(prim_broken)
        },
        "secondary": {
            "points": sec_pts,
            "arc_lengths": sec_s,
            "total_arc_length_mm": total_s_sec,
            "elements_count": len(sec_broken)
        }
    }

def sample_miseseri_along_branch(pts, arc_lengths, total_s, branch_name, recovery_data):
    elems = list(recovery_data.values())
    el_coords = np.array([[e["xc"], e["yc"]] for e in elems])
    el_mises = np.array([e["miseseri"] for e in elems])
    el_misesavg = np.array([e["misesavg"] for e in elems])
    el_eta_local = np.array([e["eta_local"] for e in elems])
    el_eta_global = np.array([e["eta_global"] for e in elems])
    el_areas = np.array([e["area"] for e in elems])

    radii = [L0_MM, 2 * L0_MM, 3 * L0_MM]
    profile_rows = []

    for idx, (pt, s) in enumerate(zip(pts, arc_lengths)):
        px, py = pt
        xi = s / total_s if total_s > 0 else 0.0
        dists = np.hypot(el_coords[:, 0] - px, el_coords[:, 1] - py)
        nearest_idx = np.argmin(dists)

        row = {
            "branch": branch_name,
            "point_index": idx,
            "x": px,
            "y": py,
            "s_mm": s,
            "xi_norm": xi,
            "nearest_miseseri_MPa": float(el_mises[nearest_idx]),
            "nearest_misesavg_MPa": float(el_misesavg[nearest_idx]),
            "nearest_eta_local_pct": float(el_eta_local[nearest_idx]),
            "nearest_eta_global_pct": float(el_eta_global[nearest_idx]),
            "dist_to_nearest_elem_mm": float(dists[nearest_idx]),
        }

        # Neighborhood weighted averages
        for r_factor, r_val in zip([1, 2, 3], radii):
            mask = dists <= r_val
            if np.any(mask):
                w_area = el_areas[mask]
                avg_mises = np.sum(el_mises[mask] * w_area) / np.sum(w_area)
                avg_global = np.sum(el_eta_global[mask] * w_area) / np.sum(w_area)
            else:
                avg_mises = float(el_mises[nearest_idx])
                avg_global = float(el_eta_global[nearest_idx])
            row[f"avg_miseseri_r{r_factor}l0_MPa"] = float(avg_mises)
            row[f"avg_eta_global_r{r_factor}l0_pct"] = float(avg_global)

        profile_rows.append(row)

    return profile_rows

def compute_branch_summary(profile_rows, recovery_data, branch_name):
    mises_vals = [r["nearest_miseseri_MPa"] for r in profile_rows]
    eta_global_vals = [r["nearest_eta_global_pct"] for r in profile_rows]
    xi_vals = [r["xi_norm"] for r in profile_rows]

    # Length fraction supported by indicator above thresholds
    # We test eta_global > 20% and > 50%
    frac_gt_20 = sum(1 for v in eta_global_vals if v >= 20.0) / len(eta_global_vals) if eta_global_vals else 0.0
    frac_gt_50 = sum(1 for v in eta_global_vals if v >= 50.0) / len(eta_global_vals) if eta_global_vals else 0.0

    return {
        "branch": branch_name,
        "sample_points": len(profile_rows),
        "miseseri_min_MPa": float(min(mises_vals)),
        "miseseri_median_MPa": float(np.median(mises_vals)),
        "miseseri_mean_MPa": float(np.mean(mises_vals)),
        "miseseri_max_MPa": float(max(mises_vals)),
        "eta_global_min_pct": float(min(eta_global_vals)),
        "eta_global_median_pct": float(np.median(eta_global_vals)),
        "eta_global_mean_pct": float(np.mean(eta_global_vals)),
        "eta_global_max_pct": float(max(eta_global_vals)),
        "length_fraction_eta_gt_20pct": float(frac_gt_20),
        "length_fraction_eta_gt_50pct": float(frac_gt_50),
    }

def main():
    print("=== Phase 2: Direct MISESERI-to-Crack-Path Alignment Audit ===")
    damage_rows = load_damage_field()
    centerlines = extract_crack_centerlines(damage_rows)

    # Save centerlines JSON
    out_centerline_json = "results/validation/f1684_crack_path_centerlines.json"
    with open(out_centerline_json, "w") as fp:
        json.dump(centerlines, fp, indent=4)
    print(f"Centerlines saved to {out_centerline_json}")
    print(f"  Primary: {len(centerlines['primary']['points'])} points, L = {centerlines['primary']['total_arc_length_mm']:.4f} mm")
    print(f"  Secondary: {len(centerlines['secondary']['points'])} points, L = {centerlines['secondary']['total_arc_length_mm']:.4f} mm")

    candidates = [
        ("Candidate_B", "results/validation/f1683_miseseri_candidate_b_element_level_audit.csv"),
        ("Candidate_C", "results/validation/f1683_miseseri_candidate_c_element_level_audit.csv"),
        ("Candidate_D", "results/validation/f1683_miseseri_candidate_d_element_level_audit.csv"),
        ("Terminal_Baseline", "results/validation/f1683_miseseri_terminal_baseline_element_level_audit.csv"),
    ]

    master_profiles = []
    alignment_summary = {}

    for cand_id, csv_path in candidates:
        print(f"\nProcessing {cand_id}...")
        rec_data = load_recovery_csv(csv_path)

        # Profile primary
        prim_profile = sample_miseseri_along_branch(
            centerlines["primary"]["points"],
            centerlines["primary"]["arc_lengths"],
            centerlines["primary"]["total_arc_length_mm"],
            "primary",
            rec_data
        )
        for r in prim_profile:
            r["candidate"] = cand_id
        master_profiles.extend(prim_profile)

        # Profile secondary
        sec_profile = sample_miseseri_along_branch(
            centerlines["secondary"]["points"],
            centerlines["secondary"]["arc_lengths"],
            centerlines["secondary"]["total_arc_length_mm"],
            "secondary",
            rec_data
        )
        for r in sec_profile:
            r["candidate"] = cand_id
        master_profiles.extend(sec_profile)

        # Summaries
        prim_sum = compute_branch_summary(prim_profile, rec_data, "primary")
        sec_sum = compute_branch_summary(sec_profile, rec_data, "secondary")

        # Global false-positive: far-field partition share of sq L2 norm
        total_sq = sum((e["miseseri"]**2)*e["area"] for e in rec_data.values())
        far_sq = sum((e["miseseri"]**2)*e["area"] for e in rec_data.values() if e["partition"] == "Far_Field_Bulk_Partition")
        far_share = far_sq / total_sq * 100.0 if total_sq > 0 else 0.0

        # Distance from global peak to nearest crack centerline
        max_el = max(rec_data.values(), key=lambda e: e["miseseri"])
        peak_x, peak_y = max_el["xc"], max_el["yc"]
        all_pts = centerlines["primary"]["points"] + centerlines["secondary"]["points"]
        dist_to_crack = min(math.hypot(px - peak_x, py - peak_y) for px, py in all_pts)

        alignment_summary[cand_id] = {
            "primary_branch": prim_sum,
            "secondary_branch": sec_sum,
            "global_peak_MPa": float(max_el["miseseri"]),
            "global_peak_coord": [float(peak_x), float(peak_y)],
            "global_peak_partition": max_el["partition"],
            "min_dist_to_crack_path_mm": float(dist_to_crack),
            "far_field_false_positive_share_pct": float(far_share)
        }

    # Save profiles CSV
    out_profile_csv = "results/validation/f1684_crack_path_miseseri_profiles.csv"
    if master_profiles:
        fieldnames = list(master_profiles[0].keys())
        with open(out_profile_csv, "w", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(master_profiles)
        print(f"\nMaster profiles saved to {out_profile_csv} ({len(master_profiles)} records)")

    # Save alignment summary JSON
    out_summary_json = "results/validation/f1684_crack_path_alignment_summary.json"
    with open(out_summary_json, "w") as fp:
        json.dump(alignment_summary, fp, indent=4)
    print(f"Alignment summary saved to {out_summary_json}")

    # Print summary table
    print("\n=== Alignment Summary Across Four Donor States ===")
    print(f"{'Candidate':<18} | {'Prim Med (MPa)':<14} | {'Prim Med (%)':<12} | {'Sec Med (MPa)':<13} | {'Sec Med (%)':<11} | {'Dist-to-Crack (mm)':<18} | {'Far-Field (%)':<13}")
    print("-" * 115)
    for c_id, s in alignment_summary.items():
        pm = s["primary_branch"]["miseseri_median_MPa"]
        pe = s["primary_branch"]["eta_global_median_pct"]
        sm = s["secondary_branch"]["miseseri_median_MPa"]
        se = s["secondary_branch"]["eta_global_median_pct"]
        d_c = s["min_dist_to_crack_path_mm"]
        ff = s["far_field_false_positive_share_pct"]
        print(f"{c_id:<18} | {pm:<14.2f} | {pe:<12.1f} | {sm:<13.2f} | {se:<11.1f} | {d_c:<18.4f} | {ff:<13.2f}")

if __name__ == "__main__":
    main()

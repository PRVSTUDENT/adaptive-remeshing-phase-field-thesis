#!/usr/bin/env python3
"""
process_spatial_profiles_and_plots.py
Computes L2 / Linf profile errors, crack front differences, path deviations,
and produces publication-ready figures.
"""
import os
import json
import csv
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

def interpolate_profile(pts, x_grid):
    if not pts:
        return np.zeros_like(x_grid)
    x_orig = [p["x"] for p in pts]
    d_orig = [p["d"] for p in pts]
    # Remove duplicate x values
    x_clean = []
    d_clean = []
    for x, d in sorted(zip(x_orig, d_orig)):
        if not x_clean or abs(x - x_clean[-1]) > 1e-6:
            x_clean.append(x)
            d_clean.append(d)
    if len(x_clean) < 2:
        return np.zeros_like(x_grid)
    return np.interp(x_grid, x_clean, d_clean, left=d_clean[0], right=d_clean[-1])

def process_spatial_data(summary_json_path, out_dir):
    with open(summary_json_path, "r") as f:
        all_cases = json.load(f)
        
    case_dict = {c["case_id"]: c for c in all_cases}
    s1_case = case_dict.get("S1_h0030_15k")
    if not s1_case:
        print("S1 case missing!")
        return
        
    x_grid = np.linspace(0.50, 1.00, 501)
    
    # 1. Compute quantitative comparison metrics against S1
    comparison_results = []
    
    target_disps = [0.0050, 0.0055, 0.00570, 0.00585, 0.00600, 0.00620]
    
    for c_id, c_data in case_dict.items():
        states_by_tu = {s["target_u_mm"]: s for s in c_data["states"]}
        s1_states_by_tu = {s["target_u_mm"]: s for s in s1_case["states"]}
        
        for tu in target_disps:
            if tu not in states_by_tu or tu not in s1_states_by_tu:
                continue
            st = states_by_tu[tu]
            s1_st = s1_states_by_tu[tu]
            
            d_case_interp = interpolate_profile(st["ligament_profile"], x_grid)
            d_s1_interp = interpolate_profile(s1_st["ligament_profile"], x_grid)
            
            # L2 and Linf errors
            diff = d_case_interp - d_s1_interp
            l2_abs = math.sqrt(np.mean(diff**2))
            l2_s1 = math.sqrt(np.mean(d_s1_interp**2))
            l2_rel_pct = (l2_abs / l2_s1 * 100.0) if l2_s1 > 1e-6 else 0.0
            linf_abs = float(np.max(np.abs(diff)))
            
            # Front positions
            x_f05_case = st["x_front"].get("0.5", 0.5)
            x_f05_s1 = s1_st["x_front"].get("0.5", 0.5)
            dx_f05 = x_f05_case - x_f05_s1
            
            x_f90_case = st["x_front"].get("0.9", 0.5)
            x_f90_s1 = s1_st["x_front"].get("0.9", 0.5)
            dx_f90 = x_f90_case - x_f90_s1
            
            x_f95_case = st["x_front"].get("0.95", 0.5)
            x_f95_s1 = s1_st["x_front"].get("0.95", 0.5)
            dx_f95 = x_f95_case - x_f95_s1
            
            comparison_results.append({
                "case_id": c_id,
                "target_u_mm": tu,
                "actual_u_mm": st["actual_u_mm"],
                "delta_u_mm": st["delta_u_mm"],
                "max_d": st["max_d"],
                "l2_abs": l2_abs,
                "l2_rel_pct": l2_rel_pct,
                "linf_abs": linf_abs,
                "x_front_05": x_f05_case,
                "dx_front_05_mm": dx_f05,
                "x_front_90": x_f90_case,
                "dx_front_90_mm": dx_f90,
                "x_front_95": x_f95_case,
                "dx_front_95_mm": dx_f95,
                "max_vertical_dev_d05_mm": st["max_vertical_dev_d05_mm"],
                "max_vertical_dev_d90_mm": st["max_vertical_dev_d90_mm"],
                "loc_width_at_x055_mm": st["loc_width_at_x055_mm"]
            })
            
    # Save comparison CSV
    csv_comp_path = os.path.join(out_dir, "GATE6B_SPATIAL_PHASE_FIELD_METRICS.csv")
    with open(csv_comp_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "case_id", "target_u_mm", "actual_u_mm", "delta_u_mm", "max_d",
            "l2_abs", "l2_rel_pct", "linf_abs",
            "x_front_05", "dx_front_05_mm", "x_front_90", "dx_front_90_mm", "x_front_95", "dx_front_95_mm",
            "max_vertical_dev_d05_mm", "max_vertical_dev_d90_mm", "loc_width_at_x055_mm"
        ])
        writer.writeheader()
        writer.writerows(comparison_results)
    print("Saved comparison CSV to %s" % csv_comp_path)
    
    # -------------------------------------------------------------
    # PLOTS
    # -------------------------------------------------------------
    # Plot style setup
    plt.rcParams.update({
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 13,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'figure.titlesize': 14,
        'lines.linewidth': 1.8
    })
    
    # FIGURE 1: S1/S2/S3/S4 Fixed-mesh matched-u ligament profiles
    fig, axes = plt.subplots(2, 2, figsize=(12, 10), sharex=True, sharey=True)
    plot_u_list = [0.0050, 0.0055, 0.00585, 0.00620]
    fixed_cases = ["S1_h0030_15k", "S2_h0020_32k", "S3_h0015_42k", "S4_h00125_51k"]
    fixed_labels = ["S1 (h=3.0 um, 15k)", "S2 (h=2.0 um, 32k)", "S3 (h=1.5 um, 42k)", "S4 (h=1.25 um, 51k)"]
    fixed_colors = ['black', 'blue', 'green', 'red']
    
    for ax_idx, tu in enumerate(plot_u_list):
        ax = axes[ax_idx // 2, ax_idx % 2]
        for c_id, c_lbl, c_col in zip(fixed_cases, fixed_labels, fixed_colors):
            c_data = case_dict.get(c_id)
            if not c_data:
                continue
            st = next((s for s in c_data["states"] if s["target_u_mm"] == tu), None)
            if st and st["ligament_profile"]:
                d_prof = interpolate_profile(st["ligament_profile"], x_grid)
                ax.plot(x_grid, d_prof, label=c_lbl, color=c_col)
        ax.set_title(f"Displacement $u = {tu:.5f}$ mm")
        ax.set_xlabel("Ligament coordinate $x$ [mm]")
        ax.set_ylabel("Phase field $d(x, y=0.5)$")
        ax.set_xlim([0.48, 1.00])
        ax.set_ylim([-0.05, 1.05])
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend(loc='upper right')
        
    fig.suptitle("Figure 1: Spatial Phase-Field Ligament Profiles (Static Uniform Mesh Suite)", fontsize=14, y=0.98)
    plt.tight_layout()
    fig1_path = os.path.join(out_dir, "fig1_fixed_mesh_ligament_profiles.png")
    plt.savefig(fig1_path, dpi=300)
    plt.close()
    print("Saved %s" % fig1_path)
    
    # FIGURE 2: A1/A2/A3/A4 Adaptive-mesh matched-u ligament profiles
    fig, axes = plt.subplots(2, 2, figsize=(12, 10), sharex=True, sharey=True)
    adapt_cases = ["S1_h0030_15k", "A1_adapt_1pct_71k", "A2_adapt_2pct_15k_corrected", "A3_adapt_3pct_8k_corrected", "A4_adapt_5pct_4k_corrected"]
    adapt_labels = ["S1 Reference (15k)", "A1 1% Adapt (71k)", "A2 2% Adapt (15k)", "A3 3% Adapt (7.6k)", "A4 5% Adapt (4.2k)"]
    adapt_colors = ['black', 'darkred', 'darkblue', 'purple', 'darkorange']
    adapt_styles = ['--', '-', '-', '-', '-']
    
    for ax_idx, tu in enumerate(plot_u_list):
        ax = axes[ax_idx // 2, ax_idx % 2]
        for c_id, c_lbl, c_col, c_sty in zip(adapt_cases, adapt_labels, adapt_colors, adapt_styles):
            c_data = case_dict.get(c_id)
            if not c_data:
                continue
            st = next((s for s in c_data["states"] if s["target_u_mm"] == tu), None)
            if st and st["ligament_profile"]:
                d_prof = interpolate_profile(st["ligament_profile"], x_grid)
                ax.plot(x_grid, d_prof, label=c_lbl, color=c_col, linestyle=c_sty)
        ax.set_title(f"Displacement $u = {tu:.5f}$ mm")
        ax.set_xlabel("Ligament coordinate $x$ [mm]")
        ax.set_ylabel("Phase field $d(x, y=0.5)$")
        ax.set_xlim([0.48, 1.00])
        ax.set_ylim([-0.05, 1.05])
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend(loc='upper right')
        
    fig.suptitle("Figure 2: Spatial Phase-Field Ligament Profiles (Adaptive Mesh Suite vs Reference)", fontsize=14, y=0.98)
    plt.tight_layout()
    fig2_path = os.path.join(out_dir, "fig2_adaptive_mesh_ligament_profiles.png")
    plt.savefig(fig2_path, dpi=300)
    plt.close()
    print("Saved %s" % fig2_path)
    
    # FIGURE 3: Threshold-dependent crack front trajectory x_front(u)
    fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
    thresholds = ["0.5", "0.9", "0.95"]
    th_titles = ["Threshold $d = 0.50$ (Damage Midpoint)", "Threshold $d = 0.90$ (High Localization)", "Threshold $d = 0.95$ (Crack Separation)"]
    
    all_plot_cases = [
        ("S1_h0030_15k", "S1 Ref (15k)", "black", "-"),
        ("S3_h0015_42k", "S3 Fine (42k)", "green", "-."),
        ("A1_adapt_1pct_71k", "A1 Adapt 1% (71k)", "darkred", "-"),
        ("A2_adapt_2pct_15k_corrected", "A2 Adapt 2% (15k)", "darkblue", "-"),
        ("A3_adapt_3pct_8k_corrected", "A3 Adapt 3% (7.6k)", "purple", "-"),
        ("A4_adapt_5pct_4k_corrected", "A4 Adapt 5% (4.2k)", "darkorange", ":"),
    ]
    
    for th_idx, (th_key, th_title) in enumerate(zip(thresholds, th_titles)):
        ax = axes[th_idx]
        for c_id, c_lbl, c_col, c_sty in all_plot_cases:
            c_data = case_dict.get(c_id)
            if not c_data:
                continue
            u_vals = [s["actual_u_mm"] for s in c_data["states"] if th_key in s["x_front"]]
            xf_vals = [s["x_front"][th_key] for s in c_data["states"] if th_key in s["x_front"]]
            if u_vals:
                ax.plot(u_vals, xf_vals, label=c_lbl, color=c_col, linestyle=c_sty, marker='o', markersize=4)
        ax.set_title(th_title)
        ax.set_xlabel("Prescribed displacement $u$ [mm]")
        if th_idx == 0:
            ax.set_ylabel("Crack-front position $x_{\\mathrm{front}}$ [mm]")
        ax.set_xlim([0.0048, 0.0066])
        ax.set_ylim([0.48, 1.02])
        ax.grid(True, linestyle='--', alpha=0.6)
        ax.legend(loc='upper left', fontsize=9)
        
    fig.suptitle("Figure 3: Crack-Front Position Evolution $x_{\\mathrm{front}}(u)$ across Damage Thresholds", fontsize=14, y=1.02)
    plt.tight_layout()
    fig3_path = os.path.join(out_dir, "fig3_crack_front_trajectories.png")
    plt.savefig(fig3_path, dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved %s" % fig3_path)
    
    # FIGURE 4: Vertical localization path deviation |y - 0.5| vs u
    fig, ax = plt.subplots(figsize=(9, 6))
    for c_id, c_lbl, c_col, c_sty in all_plot_cases:
        c_data = case_dict.get(c_id)
        if not c_data:
            continue
        u_vals = [s["actual_u_mm"] for s in c_data["states"]]
        dev_vals = [s["max_vertical_dev_d05_mm"] * 1000.0 for s in c_data["states"]] # in microns
        if u_vals:
            ax.plot(u_vals, dev_vals, label=c_lbl, color=c_col, linestyle=c_sty, marker='s', markersize=4)
    ax.set_title("Figure 4: Maximum Vertical Localization Deviation $|y - 0.5|$ ($d \\geq 0.5$)")
    ax.set_xlabel("Prescribed displacement $u$ [mm]")
    ax.set_ylabel("Max Vertical Deviation $\\max |y - 0.5|$ [$\\mu$m]")
    ax.set_xlim([0.0048, 0.0066])
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.legend(loc='upper right')
    plt.tight_layout()
    fig4_path = os.path.join(out_dir, "fig4_vertical_path_localization_deviation.png")
    plt.savefig(fig4_path, dpi=300)
    plt.close()
    print("Saved %s" % fig4_path)
    
    # FIGURE 5: Profile error vs spatial mesh cases at u = 0.00585 mm (near peak)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    peak_comp = [r for r in comparison_results if abs(r["target_u_mm"] - 0.00585) < 1e-6]
    
    case_names = [r["case_id"] for r in peak_comp if r["case_id"] != "S1_h0030_15k"]
    l2_errs = [r["l2_rel_pct"] for r in peak_comp if r["case_id"] != "S1_h0030_15k"]
    linf_errs = [r["linf_abs"] for r in peak_comp if r["case_id"] != "S1_h0030_15k"]
    
    x_pos = np.arange(len(case_names))
    ax1.bar(x_pos, l2_errs, color='steelblue', edgecolor='black', alpha=0.85)
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(case_names, rotation=35, ha='right', fontsize=9)
    ax1.set_ylabel("Relative $L_2$ Ligament Profile Error [%]")
    ax1.set_title("Relative $L_2$ Error vs S1 ($u = 0.00585$ mm)")
    ax1.grid(True, axis='y', linestyle='--', alpha=0.6)
    
    ax2.bar(x_pos, linf_errs, color='coral', edgecolor='black', alpha=0.85)
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(case_names, rotation=35, ha='right', fontsize=9)
    ax2.set_ylabel("$L_\\infty$ Max Difference $\\max |d - d_{\\mathrm{S1}}|$")
    ax2.set_title("$L_\\infty$ Error vs S1 ($u = 0.00585$ mm)")
    ax2.grid(True, axis='y', linestyle='--', alpha=0.6)
    
    fig.suptitle("Figure 5: Quantitative Ligament Profile Differences Relative to S1 Reference Solution", fontsize=14, y=1.02)
    plt.tight_layout()
    fig5_path = os.path.join(out_dir, "fig5_spatial_profile_errors_vs_mesh.png")
    plt.savefig(fig5_path, dpi=300, bbox_inches='tight')
    plt.close()
    print("Saved %s" % fig5_path)

if __name__ == "__main__":
    brain_dir = r"C:\Users\pruth\.gemini\antigravity-cli\brain\88f4ccfe-ee55-40ea-a2e9-7238a72c1ef4"
    json_path = os.path.join(brain_dir, "SPATIAL_PHASE_FIELD_CONVERGENCE_SUMMARY.json")
    process_spatial_data(json_path, brain_dir)

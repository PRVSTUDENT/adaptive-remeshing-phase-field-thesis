"""
scripts/visualization/plot_f1686_candidate_mesh_comparison.py
=============================================================
Task F1686: Method A Narrow Crack-Following Selective Adaptive Remeshing Optimization
Generates publication figures for Master Thesis Chapter 5:
  1. fig_f1686_mesh_selectivity_comparison:
     - Panel (a): Combined Baseline (e_tgt = 5%/5%, 21,569 elements, waste 86.5%, W_90% = 197.1 um)
     - Panel (b): Selected Candidate E10 (e_tgt = 5%/10%, 9,164 elements, waste 65.4%, W_90% = 36.8 um)
     - Panel (c): Selected Candidate E12 (e_tgt = 5%/12%, 8,046 elements, waste 59.3%, W_90% = 33.7 um)
     All panels color-coded by local element size h_max [um] on log scale with overlaid authentic crack centerlines.
  2. fig_f1686_pareto_frontier:
     - Panel (a): Element count and Out-of-corridor waste vs secondary error target
     - Panel (b): Transverse refinement width W_90% and secondary corridor resolution vs secondary error target
     Highlights the optimal Pareto window e_tgt_sec in [10%, 12%].
"""
import os
import sys
import math
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import matplotlib.colors as mcolors

def setup_style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 11,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "figure.titlesize": 12,
        "lines.linewidth": 1.6,
        "lines.markersize": 5,
        "grid.alpha": 0.35,
        "grid.linestyle": ":",
        "axes.grid": True,
        "savefig.dpi": 300,
        "savefig.bbox": "tight"
    })

def parse_mesh_for_plotting(inp_path):
    print(f"Reading mesh: {inp_path}")
    nodes = {}
    elements = []
    h_sizes = []

    in_nodes = False
    in_elements = False
    current_type = None

    with open(inp_path, "r") as fp:
        for line in fp:
            line = line.strip()
            if not line or line.startswith("**"):
                continue
            if line.startswith("*"):
                in_nodes = False
                in_elements = False
                upline = line.upper()
                if upline.startswith("*NODE"):
                    in_nodes = True
                elif upline.startswith("*ELEMENT"):
                    if "CPE4" in upline or "CPS4" in upline:
                        in_elements = True
                        current_type = "QUAD"
                    elif "CPE3" in upline or "CPS3" in upline:
                        in_elements = True
                        current_type = "TRI"
                    else:
                        current_type = None
                continue

            parts = [p.strip() for p in line.split(",") if p.strip()]
            if in_nodes:
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        nodes[nid] = (float(parts[1]), float(parts[2]))
                    except ValueError:
                        pass
            elif in_elements:
                if current_type == "QUAD" and len(parts) >= 5:
                    try:
                        conn = [int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4])]
                        elements.append(conn)
                    except ValueError:
                        pass
                elif current_type == "TRI" and len(parts) >= 4:
                    try:
                        conn = [int(parts[1]), int(parts[2]), int(parts[3])]
                        elements.append(conn)
                    except ValueError:
                        pass

    polygons = []
    for conn in elements:
        pts = [nodes[nid] for nid in conn]
        polygons.append(pts)
        n_pts = len(pts)
        edges = [math.hypot(pts[(i+1)%n_pts][0] - pts[i][0], pts[(i+1)%n_pts][1] - pts[i][1]) for i in range(n_pts)]
        h_sizes.append(max(edges) * 1000.0) # um

    print(f"  Loaded {len(polygons)} element polygons.")
    return polygons, np.array(h_sizes)

def plot_mesh_comparison(candidates_dir, centerlines_path, dest_dirs):
    inp_baseline = os.path.join(candidates_dir, "PK_HOLE_SEL_E05_PHYS.inp")
    inp_e10 = os.path.join(candidates_dir, "PK_HOLE_SEL_E10_PHYS.inp")
    inp_e12 = os.path.join(candidates_dir, "PK_HOLE_SEL_E12_PHYS.inp")

    with open(centerlines_path, "r") as fp:
        cdata = json.load(fp)
    prim_cl = np.array(cdata["primary"]["points"])
    sec_cl = np.array(cdata["secondary"]["points"])

    poly_base, h_base = parse_mesh_for_plotting(inp_baseline)
    poly_e10, h_e10 = parse_mesh_for_plotting(inp_e10)
    poly_e12, h_e12 = parse_mesh_for_plotting(inp_e12)

    fig, axes = plt.subplots(1, 3, figsize=(18, 6.2), constrained_layout=True)

    norm = mcolors.LogNorm(vmin=1.2, vmax=25.0)
    cmap = plt.cm.viridis_r

    configs = [
        {
            "ax": axes[0],
            "title": "(a) Combined Baseline ($e_{\\mathrm{tgt}}^{\\mathrm{prim}}=5\\%, e_{\\mathrm{tgt}}^{\\mathrm{sec}}=5\\%$)\n(21,569 elements, Broad Diffuse Refinement)",
            "poly": poly_base,
            "h": h_base,
            "sub": "21,569 FEs | Waste: 86.52% | $W_{90\\%} = 197.10\\,\\mu\\mathrm{m}$\nPrim: $h_{\\mathrm{med}} = 2.49\\,\\mu\\mathrm{m}$ | Sec: $h_{\\mathrm{med}} = 1.91\\,\\mu\\mathrm{m}$"
        },
        {
            "ax": axes[1],
            "title": "(b) Selected Candidate E10 ($e_{\\mathrm{tgt}}^{\\mathrm{prim}}=5\\%, e_{\\mathrm{tgt}}^{\\mathrm{sec}}=10\\%$)\n(9,164 elements, Narrow Crack-Following)",
            "poly": poly_e10,
            "h": h_e10,
            "sub": "9,164 FEs (-57.5%) | Waste: 65.35% | $W_{90\\%} = 36.81\\,\\mu\\mathrm{m}$ ($5.35\\times$ narrower)\nPrim: $h_{\\mathrm{med}} = 2.37\\,\\mu\\mathrm{m}$ | Sec: $h_{\\mathrm{med}} = 2.13\\,\\mu\\mathrm{m}$"
        },
        {
            "ax": axes[2],
            "title": "(c) Selected Candidate E12 ($e_{\\mathrm{tgt}}^{\\mathrm{prim}}=5\\%, e_{\\mathrm{tgt}}^{\\mathrm{sec}}=12\\%$)\n(8,046 elements, Lean Crack-Following)",
            "poly": poly_e12,
            "h": h_e12,
            "sub": "8,046 FEs (-62.7%) | Waste: 59.29% | $W_{90\\%} = 33.69\\,\\mu\\mathrm{m}$ ($5.85\\times$ narrower)\nPrim: $h_{\\mathrm{med}} = 2.35\\,\\mu\\mathrm{m}$ | Sec: $h_{\\mathrm{med}} = 2.41\\,\\mu\\mathrm{m}$"
        }
    ]

    for cfg in configs:
        ax = cfg["ax"]
        polys = cfg["poly"]
        h_vals = cfg["h"]

        coll = PolyCollection(polys, array=h_vals, cmap=cmap, norm=norm, edgecolors='black', linewidths=0.15)
        ax.add_collection(coll)

        # Plot crack trajectories
        ax.plot(prim_cl[:, 0], prim_cl[:, 1], color='#00e5ff', lw=1.8, ls='-', label='Primary Branch ($d \\geq 0.80$)', zorder=5)
        ax.plot(sec_cl[:, 0], sec_cl[:, 1], color='#76ff03', lw=1.8, ls='--', label='Secondary Branch ($d \\geq 0.80$)', zorder=5)

        # Plot hole perimeter
        circle = plt.Circle((0.65, 0.65), 0.10, color='white', ec='black', lw=1.2, zorder=4)
        ax.add_patch(circle)

        # Plot initial slit
        ax.plot([0.0, 0.50], [0.50, 0.50], color='red', lw=1.5, zorder=6, label='Initial Slit ($a_0 = 0.5\\,\\mathrm{mm}$)')

        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        ax.set_aspect('equal')
        ax.set_xlabel('$x$ [mm]', fontsize=11)
        ax.set_ylabel('$y$ [mm]', fontsize=11)
        ax.set_title(cfg["title"], fontsize=12, fontweight='bold', pad=10)

        # Add subtitle box
        ax.text(0.50, 0.04, cfg["sub"], transform=ax.transAxes, ha='center', va='bottom',
                fontsize=9.0, fontweight='semibold',
                bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#888888', alpha=0.92))

    # Add shared colorbar
    cbar = fig.colorbar(coll, ax=axes, orientation='horizontal', fraction=0.04, pad=0.08, aspect=45)
    cbar.set_label('Element Size $h_{\\max}$ [$\\mu\\mathrm{m}$] (Log Scale; $\\ell_0 = 7.50\\,\\mu\\mathrm{m}$)', fontsize=11, fontweight='semibold')
    cbar.set_ticks([1.5, 2.5, 3.75, 5.0, 7.5, 10.0, 15.0, 20.0, 25.0])
    cbar.set_ticklabels(['$1.5\\,(\\ell_0/5)$', '$2.5\\,(\\ell_0/3)$', '$3.75\\,(\\ell_0/2)$', '5.0', '$7.5\\,(\\ell_0)$', '10.0', '15.0', '20.0', '25.0'])

    axes[1].legend(loc='upper left', fontsize=8.5, framealpha=0.92, edgecolor='#888888')

    for d in dest_dirs:
        pdf_out = os.path.join(d, "fig_f1686_mesh_selectivity_comparison.pdf")
        png_out = os.path.join(d, "fig_f1686_mesh_selectivity_comparison.png")
        fig.savefig(pdf_out, dpi=300, bbox_inches='tight')
        fig.savefig(png_out, dpi=300, bbox_inches='tight')
        print(f"Saved: {pdf_out}")
        print(f"Saved: {png_out}")

    plt.close(fig)

def plot_pareto_frontier(eval_json_path, dest_dirs):
    with open(eval_json_path, "r") as fp:
        candidates = json.load(fp)

    e_tgts = []
    n_elems = []
    wastes = []
    w90s = []
    sec_h_meds = []
    sec_pct_half = []

    # Map candidate name to secondary error target percentage
    tgt_map = {
        "PK_HOLE_SEL_E05_PHYS": 5.0,
        "PK_HOLE_SEL_E08_PHYS": 8.0,
        "PK_HOLE_SEL_E10_PHYS": 10.0,
        "PK_HOLE_SEL_E12_PHYS": 12.0,
        "PK_HOLE_SEL_E15_PHYS": 15.0,
        "PK_HOLE_SEL_E20_PHYS": 20.0,
        "PK_HOLE_SEL_E25_PHYS": 25.0,
        "PK_HOLE_SEL_E30_PHYS": 30.0,
        "PK_HOLE_SEL_E40_PHYS": 40.0,
        "PK_HOLE_SEL_E50_PHYS": 50.0,
    }

    for c in candidates:
        name = c["candidate_name"]
        if name in tgt_map:
            e_tgts.append(tgt_map[name])
            n_elems.append(c["n_elements"])
            wastes.append(c["waste_area_pct"])
            w90s.append(c["w90_um"])
            sec_h_meds.append(c["secondary_corridor"]["h_med_um"])
            sec_pct_half.append(c["secondary_corridor"]["pct_le_half_l0"])

    sort_idx = np.argsort(e_tgts)
    e_tgts = np.array(e_tgts)[sort_idx]
    n_elems = np.array(n_elems)[sort_idx]
    wastes = np.array(wastes)[sort_idx]
    w90s = np.array(w90s)[sort_idx]
    sec_h_meds = np.array(sec_h_meds)[sort_idx]
    sec_pct_half = np.array(sec_pct_half)[sort_idx]

    fig, (ax1, ax3) = plt.subplots(1, 2, figsize=(14, 5.2), constrained_layout=True)

    # Panel (a): DOF & Out-of-Corridor Waste vs Secondary Error Target
    color1 = "#1565c0"
    ax1.plot(e_tgts, n_elems, color=color1, marker="o", lw=2.0, label="Total Physical Elements")
    ax1.set_xlabel("Secondary Ligament Error Target $e_{\\mathrm{tgt}}^{\\mathrm{sec}}$ [%]", fontsize=11)
    ax1.set_ylabel("Total Physical Elements", color=color1, fontsize=11)
    ax1.tick_params(axis="y", labelcolor=color1)
    ax1.set_ylim(4000, 24000)

    # Secondary axis for waste
    ax2 = ax1.twinx()
    color2 = "#d32f2f"
    ax2.plot(e_tgts, wastes, color=color2, marker="s", ls="--", lw=1.8, label="Out-of-Corridor Waste Area [%]")
    ax2.set_ylabel("Out-of-Corridor Waste Area [%]", color=color2, fontsize=11)
    ax2.tick_params(axis="y", labelcolor=color2)
    ax2.set_ylim(40, 95)
    ax2.grid(False)

    # Optimal window shading on panel (a)
    ax1.axvspan(10.0, 12.0, color="#c8e6c9", alpha=0.55, label="Optimal Pareto Window (E10 - E12)")
    ax1.set_title("(a) Degree of Freedom and Waste vs. Sizing Rule", fontsize=11.5, fontweight="bold")

    # Combine legends for panel (a)
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper right", fontsize=8.5, framealpha=0.92)

    # Panel (b): Transverse Width & Secondary Resolution vs Target
    color3 = "#6a1b9a"
    ax3.plot(e_tgts, w90s, color=color3, marker="^", lw=2.0, label="Refinement Width $W_{90\\%}$ [$\\mu\\mathrm{m}$]")
    ax3.set_xlabel("Secondary Ligament Error Target $e_{\\mathrm{tgt}}^{\\mathrm{sec}}$ [%]", fontsize=11)
    ax3.set_ylabel("Refinement Width $W_{90\\%}$ [$\\mu\\mathrm{m}$]", color=color3, fontsize=11)
    ax3.tick_params(axis="y", labelcolor=color3)
    ax3.set_ylim(20, 220)

    # Secondary axis for resolution
    ax4 = ax3.twinx()
    color4 = "#2e7d32"
    ax4.plot(e_tgts, sec_h_meds, color=color4, marker="D", ls="-.", lw=1.8, label="Sec. Corridor Median $h_{\\mathrm{med}}$ [$\\mu\\mathrm{m}$]")
    ax4.axhline(3.75, color="red", ls=":", lw=1.8, label="Resolution Limit $\\ell_0/2 = 3.75\\,\\mu\\mathrm{m}$")
    ax4.set_ylabel("Secondary Corridor Median $h_{\\mathrm{med}}$ [$\\mu\\mathrm{m}$]", color=color4, fontsize=11)
    ax4.tick_params(axis="y", labelcolor=color4)
    ax4.set_ylim(1.0, 7.5)
    ax4.grid(False)

    ax3.axvspan(10.0, 12.0, color="#c8e6c9", alpha=0.55, label="Optimal Pareto Window (E10 - E12)")
    ax3.set_title("(b) Spatial Refinement Width and Process Zone Resolution", fontsize=11.5, fontweight="bold")

    lines3, labels3 = ax3.get_legend_handles_labels()
    lines4, labels4 = ax4.get_legend_handles_labels()
    ax3.legend(lines3 + lines4, labels3 + labels4, loc="center right", fontsize=8.5, framealpha=0.92)

    for d in dest_dirs:
        pdf_out = os.path.join(d, "fig_f1686_pareto_frontier.pdf")
        png_out = os.path.join(d, "fig_f1686_pareto_frontier.png")
        fig.savefig(pdf_out, dpi=300, bbox_inches='tight')
        fig.savefig(png_out, dpi=300, bbox_inches='tight')
        print(f"Saved: {pdf_out}")
        print(f"Saved: {png_out}")

    plt.close(fig)

def main():
    setup_style()
    dest_dirs = [
        "MA_AdaptiveRemeshing_Report_2026/figures",
        "docs/MA_AdaptiveRemeshing_Report_2026_main/figures"
    ]
    for d in dest_dirs:
        os.makedirs(d, exist_ok=True)

    candidates_dir = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidates"
    centerlines_path = "results/validation/f1684_crack_path_centerlines.json"
    eval_json_path = "results/validation/f1686_stage_c_candidate_evaluation.json"

    print("Generating Figure 1: Three-way mesh selectivity comparison...")
    plot_mesh_comparison(candidates_dir, centerlines_path, dest_dirs)

    print("Generating Figure 2: Pareto frontier and trade-off curves...")
    plot_pareto_frontier(eval_json_path, dest_dirs)

    print("SUCCESS: All Task F1686 visualization artifacts generated successfully!")

if __name__ == "__main__":
    main()

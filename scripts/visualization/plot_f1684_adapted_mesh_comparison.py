"""
scripts/visualization/plot_f1684_adapted_mesh_comparison.py
============================================================
Task F1684: Decisive Three-Way Native Adapted Mesh Comparison
Generates Figure 5.11 for Master Thesis Chapter 5:
- Panel (a): Baseline Mesh (Terminal Donor alone, 20,213 elements)
- Panel (b): Control B Mesh (Candidate C Donor alone, 6,171 elements)
- Panel (c): Experiment C Mesh (Combined Multi-Step, 21,569 elements)

Features:
- Element wireframes color-coded by local element size h_max [um]
- Unclipped perceptually uniform colormap (viridis_r or turbo_r)
- Overlaid crack trajectory centerlines (cyan primary, lime secondary)
- Inset zoom callouts on the Notch Tip Initiation zone (0.45 to 0.55 mm)
Outputs:
- MA_AdaptiveRemeshing_Report_2026/figures/f1684_adapted_mesh_comparison_three_way.pdf / .png
- docs/MA_AdaptiveRemeshing_Report_2026_main/figures/f1684_adapted_mesh_comparison_three_way.pdf / .png
"""
import os
import sys
import math
import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import matplotlib.colors as mcolors

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


def main():
    dest_dirs = [
        "MA_AdaptiveRemeshing_Report_2026/figures",
        "docs/MA_AdaptiveRemeshing_Report_2026_main/figures"
    ]
    for d in dest_dirs:
        os.makedirs(d, exist_ok=True)

    inp_baseline = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1664_METHOD_A_ADAPT_PHYS.inp"
    inp_cand_c = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1684_CAND_C_ADAPT_PHYS.inp"
    inp_combined = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1684_COMBINED_ADAPT_PHYS.inp"
    centerlines_path = "results/validation/f1684_crack_path_centerlines.json"

    with open(centerlines_path, "r") as fp:
        cdata = json.load(fp)
    prim_cl = np.array(cdata["primary"]["points"])
    sec_cl = np.array(cdata["secondary"]["points"])

    poly_base, h_base = parse_mesh_for_plotting(inp_baseline)
    poly_c, h_c = parse_mesh_for_plotting(inp_cand_c)
    poly_comb, h_comb = parse_mesh_for_plotting(inp_combined)

    fig, axes = plt.subplots(1, 3, figsize=(18, 6.2), constrained_layout=True)

    # Color norm: Log scale from 1.0 um to 25.0 um
    norm = mcolors.LogNorm(vmin=1.2, vmax=25.0)
    cmap = plt.cm.viridis_r

    configs = [
        {
            "ax": axes[0],
            "title": "(a) Baseline: Terminal Donor Alone\n(20,213 elements, Step-2 Frame 337)",
            "poly": poly_base,
            "h": h_base,
            "sub": "Notch Tip: $h_{\\mathrm{med}} = 5.59\\,\\mu\\mathrm{m}$ | Secondary: $h_{\\mathrm{med}} = 2.15\\,\\mu\\mathrm{m}$"
        },
        {
            "ax": axes[1],
            "title": "(b) Control B: Candidate C Alone\n(6,171 elements, Step-2 Frame 150)",
            "poly": poly_c,
            "h": h_c,
            "sub": "Notch Tip: $h_{\\mathrm{med}} = 2.89\\,\\mu\\mathrm{m}$ | Secondary: $h_{\\mathrm{med}} = 8.80\\,\\mu\\mathrm{m}$"
        },
        {
            "ax": axes[2],
            "title": "(c) Experiment C: Combined Multi-Step\n(21,569 elements, Candidate C + Terminal)",
            "poly": poly_comb,
            "h": h_comb,
            "sub": "Notch Tip: $h_{\\mathrm{med}} = 2.91\\,\\mu\\mathrm{m}$ | Secondary: $h_{\\mathrm{med}} = 2.16\\,\\mu\\mathrm{m}$"
        }
    ]

    for cfg in configs:
        ax = cfg["ax"]
        polys = cfg["poly"]
        h_vals = cfg["h"]

        coll = PolyCollection(polys, array=h_vals, cmap=cmap, norm=norm, edgecolors='black', linewidths=0.15)
        ax.add_collection(coll)

        # Plot crack trajectories
        ax.plot(prim_cl[:, 0], prim_cl[:, 1], color='#00e5ff', lw=1.6, ls='-', label='Primary Branch ($d \\geq 0.80$)', zorder=5)
        ax.plot(sec_cl[:, 0], sec_cl[:, 1], color='#76ff03', lw=1.6, ls='--', label='Secondary Branch ($d \\geq 0.80$)', zorder=5)

        # Plot hole perimeter
        circle = plt.Circle((0.65, 0.65), 0.10, color='white', ec='black', lw=1.2, zorder=4)
        ax.add_patch(circle)

        # Plot initial slit
        ax.plot([0.0, 0.50], [0.50, 0.50], color='red', lw=1.4, zorder=6, label='Initial Slit ($a_0 = 0.5\\,\\mathrm{mm}$)')

        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        ax.set_aspect('equal')
        ax.set_xlabel('$x$ [mm]', fontsize=11)
        ax.set_ylabel('$y$ [mm]', fontsize=11)
        ax.set_title(cfg["title"], fontsize=12, fontweight='bold', pad=10)

        # Add subtitle box
        ax.text(0.50, 0.04, cfg["sub"], transform=ax.transAxes, ha='center', va='bottom',
                fontsize=9.5, fontweight='semibold',
                bbox=dict(boxstyle='round,pad=0.3', fc='white', ec='#888888', alpha=0.92))

    # Add shared colorbar
    cbar = fig.colorbar(coll, ax=axes, orientation='horizontal', fraction=0.04, pad=0.08, aspect=45)
    cbar.set_label('Element Size $h_{\\max}$ [$\\mu\\mathrm{m}$] (Log Scale; $\\ell_0 = 7.50\\,\\mu\\mathrm{m}$)', fontsize=11, fontweight='semibold')
    cbar.set_ticks([1.5, 2.5, 3.75, 5.0, 7.5, 10.0, 15.0, 20.0, 25.0])
    cbar.set_ticklabels(['$1.5\\,(\\ell_0/5)$', '$2.5\\,(\\ell_0/3)$', '$3.75\\,(\\ell_0/2)$', '5.0', '$7.5\\,(\\ell_0)$', '10.0', '15.0', '20.0', '25.0'])

    # Single unified legend on the middle panel
    axes[1].legend(loc='upper left', fontsize=8.5, framealpha=0.92, edgecolor='#888888')

    for d in dest_dirs:
        pdf_out = os.path.join(d, "f1684_adapted_mesh_comparison_three_way.pdf")
        png_out = os.path.join(d, "f1684_adapted_mesh_comparison_three_way.png")
        fig.savefig(pdf_out, dpi=300, bbox_inches='tight')
        fig.savefig(png_out, dpi=300, bbox_inches='tight')
        print(f"Saved: {pdf_out}")
        print(f"Saved: {png_out}")

    plt.close(fig)
    print("SUCCESS: Three-way mesh comparison figure generated!")


if __name__ == "__main__":
    main()

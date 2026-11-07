# scripts/visualization/plot_f1662_figures.py
"""
Task F1662: Diagnostic & Publication Figures for Mesh Quality, Resolution, and FPZ Support Qualification

Generates:
Figure F1662: Comprehensive 3-Panel Mesh Qualification & Physical FPZ Support Synthesis
  Panel (a): Full adapted mesh (77,211 elements) colored by h_max with donor damage contours (d = 0.20, 0.50, 0.80) overlaid.
  Panel (b): Zoomed Fracture Process Zone (ligament, hole, opposite flank) with element mesh and physical damage contours.
  Panel (c): Finite-element quality distributions: Signed Isoparametric Jacobian det(J), Aspect Ratio, and Corner Angle.
"""
import os
import sys
import math
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import matplotlib.colors as mcolors
import scipy.interpolate as interp

output_dirs = [
    os.path.abspath("MA_AdaptiveRemeshing_Report_2026/figures"),
    os.path.abspath("docs/MA_AdaptiveRemeshing_Report_2026_main/figures")
]

plt.rcParams.update({
    'font.size': 10,
    'font.family': 'sans-serif',
    'axes.labelsize': 11,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.titlesize': 13
})

def main():
    print("======================================================================")
    print("TASK F1662: GENERATING PUBLICATION FIGURE F1662")
    print("======================================================================")

    # 1. Load F1662 audit JSON
    audit_json_path = os.path.abspath("models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1662_MESH_QUALITY_AND_FPZ_AUDIT.json")
    with open(audit_json_path, "r") as fp:
        audit_data = json.load(fp)

    # 2. Parse INP for polygons
    inp_path = os.path.abspath("models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1661_METHOD_A_ADAPT_PHYS.inp")
    print("Parsing adapted mesh from: %s" % inp_path)
    nodes = {}
    elems = []
    sec = None
    with open(inp_path, 'r') as fp:
        for line in fp:
            line = line.strip()
            if not line or line.startswith('**'):
                continue
            u = line.upper()
            if u.startswith('*NODE') and not u.startswith('*NODE OUTPUT') and not u.startswith('*NODE PRINT'):
                sec = 'N'
                continue
            elif u.startswith('*ELEMENT') and not u.startswith('*ELEMENT OUTPUT'):
                sec = 'E'
                continue
            elif u.startswith('*'):
                sec = None
                continue
            if sec == 'N':
                parts = [p.strip() for p in line.split(',')]
                try:
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                except:
                    pass
            elif sec == 'E':
                parts = [p.strip() for p in line.split(',')]
                try:
                    elems.append([int(p) for p in parts[1:]])
                except:
                    pass

    n_elems = len(elems)
    print("Parsed %d nodes and %d elements." % (len(nodes), n_elems))

    # Pre-extract polygons, centroids, and edge lengths
    poly_coords = []
    h_max_list = []
    centroids = []
    for conn in elems:
        pts = [nodes[nid] for nid in conn]
        n = len(pts)
        lens = [math.hypot(pts[(i+1)%n][0] - pts[i][0], pts[(i+1)%n][1] - pts[i][1]) * 1000.0 for i in range(n)]
        h_max_list.append(max(lens))
        cx = sum([p[0] for p in pts]) / float(n)
        cy = sum([p[1] for p in pts]) / float(n)
        centroids.append((cx, cy))
        poly_coords.append(pts)

    h_arr = np.array(h_max_list)
    c_arr = np.array(centroids)

    # 3. Load donor damage sampling points for contour overlay
    donor_lookup = os.path.abspath("models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1659_IP_DAMAGE_LOOKUP.txt")
    donor_pts = []
    donor_d = []
    with open(donor_lookup, "r") as fp:
        for line in fp:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) >= 5:
                donor_pts.append((float(parts[2]), float(parts[3])))
                donor_d.append(float(parts[4]))

    donor_pts = np.array(donor_pts)
    donor_d = np.array(donor_d)

    # Create grid for damage contours
    gx = np.linspace(0.40, 0.90, 200)
    gy = np.linspace(0.40, 0.90, 200)
    GX, GY = np.meshgrid(gx, gy)
    GD = interp.griddata(donor_pts, donor_d, (GX, GY), method='linear', fill_value=0.0)

    # Mask hole in grid
    hole_mask = ((GX - 0.65)**2 + (GY - 0.65)**2) <= (0.10**2)
    # Mask notch slit (y ~ 0.50, x <= 0.50)
    notch_mask = (GX <= 0.50) & (np.abs(GY - 0.50) < 0.005)
    GD[hole_mask] = np.nan
    GD[notch_mask] = np.nan

    # 4. Load plot data for quality metrics
    with open("f1662_plot_data.json", "r") as fp:
        plot_data = json.load(fp)

    ar_arr = np.array(plot_data["ar_arr"])
    min_ang_arr = np.array(plot_data["min_ang_arr"])
    jac_arr = np.array(plot_data["jac_arr"])

    # --------------------------------------------------------------------------
    # BUILD PUBLICATION FIGURE F1662 (3 Panels: (a) Full Mesh, (b) Zoomed FPZ, (c) Quality Histograms)
    # --------------------------------------------------------------------------
    print("\nRendering Figure F1662...")
    fig = plt.figure(figsize=(16, 5.5), constrained_layout=True)
    gs = fig.add_gridspec(1, 3, width_ratios=[1.05, 1.05, 1.15])

    ax1 = fig.add_subplot(gs[0, 0])
    ax2 = fig.add_subplot(gs[0, 1])
    ax3 = fig.add_subplot(gs[0, 2])

    cmap = plt.cm.viridis_r
    norm = mcolors.LogNorm(vmin=1.0, vmax=25.0)

    # --------------------------------------------------------------------------
    # Panel (a): Full Plate Mesh & Damage Contours
    # --------------------------------------------------------------------------
    coll1 = PolyCollection(poly_coords, array=h_arr, cmap=cmap, norm=norm, edgecolors='black', linewidths=0.10)
    ax1.add_collection(coll1)
    ax1.set_xlim(0.0, 1.0)
    ax1.set_ylim(0.0, 1.0)
    ax1.set_aspect('equal')
    ax1.set_xlabel("$x$ [mm]")
    ax1.set_ylabel("$y$ [mm]")
    ax1.set_title("(a) Authentic Method A Native Adapted Mesh\n(77,211 elements, 97.5% quads, $h_{\\min} = 0.855\\;\\mu$m)", fontweight='bold')

    # Overlaid damage contour levels
    cs1 = ax1.contour(GX, GY, GD, levels=[0.20, 0.50, 0.80], colors=['deepskyblue', 'orange', 'red'], linewidths=[1.2, 1.4, 1.6])
    
    # Notch and Hole geometry
    ax1.plot([0.0, 0.50], [0.50, 0.50], color='white', lw=2.2, label='Notch ($a_0 = 0.5$ mm)')
    theta = np.linspace(0, 2*np.pi, 200)
    ax1.plot(0.65 + 0.10*np.cos(theta), 0.65 + 0.10*np.sin(theta), color='white', ls='--', lw=1.8, label='Hole ($R = 0.1$ mm)')

    # Custom legend for panel a
    from matplotlib.lines import Line2D
    legend_elements1 = [
        Line2D([0], [0], color='red', lw=1.6, label='Crack Core ($d \\geq 0.80$)'),
        Line2D([0], [0], color='orange', lw=1.4, label='Softening Zone ($d \\geq 0.50$)'),
        Line2D([0], [0], color='deepskyblue', lw=1.2, label='Process Zone ($d \\geq 0.20$)'),
        Line2D([0], [0], color='white', lw=1.8, label='Notch & Hole')
    ]
    ax1.legend(handles=legend_elements1, loc='lower left', framealpha=0.85, fontsize=8)

    cb1 = fig.colorbar(coll1, ax=ax1, orientation='vertical', fraction=0.046, pad=0.04)
    cb1.set_label("Element Longest Edge $h_{\\max}$ [$\\mu$m] (Log Scale)")

    # --------------------------------------------------------------------------
    # Panel (b): Zoomed Fracture Process Zone
    # --------------------------------------------------------------------------
    zoom_box = [0.45, 0.85, 0.45, 0.80] # [xmin, xmax, ymin, ymax]
    zoom_mask = (c_arr[:, 0] >= zoom_box[0]) & (c_arr[:, 0] <= zoom_box[1]) & \
                (c_arr[:, 1] >= zoom_box[2]) & (c_arr[:, 1] <= zoom_box[3])

    zoom_polys = [poly_coords[i] for i in range(len(poly_coords)) if zoom_mask[i]]
    zoom_h = h_arr[zoom_mask]

    coll2 = PolyCollection(zoom_polys, array=zoom_h, cmap=cmap, norm=norm, edgecolors='black', linewidths=0.20)
    ax2.add_collection(coll2)
    ax2.set_xlim(zoom_box[0], zoom_box[1])
    ax2.set_ylim(zoom_box[2], zoom_box[3])
    ax2.set_aspect('equal')
    ax2.set_xlabel("$x$ [mm]")
    ax2.set_ylabel("$y$ [mm]")
    ax2.set_title("(b) Zoomed FPZ Support & Crack Trajectory\n(Core $h_{\\text{median}} = 1.97\\;\\mu$m; 2,561 elements $\\leq 1.5\\;\\mu$m)", fontweight='bold')

    cs2 = ax2.contour(GX, GY, GD, levels=[0.20, 0.50, 0.80], colors=['deepskyblue', 'orange', 'red'], linewidths=[1.4, 1.6, 2.0])
    ax2.plot([0.45, 0.50], [0.50, 0.50], color='red', lw=2.5, label='Notch Tip ($x=0.50$ mm)')
    ax2.plot(0.65 + 0.10*np.cos(theta), 0.65 + 0.10*np.sin(theta), color='white', ls='--', lw=2.0)

    # Inset annotations
    ax2.text(0.53, 0.58, "Primary Ligament\n($h \\approx 1.2\\text{--}1.9\\;\\mu$m)", color='white', fontsize=8, fontweight='bold',
             bbox=dict(boxstyle="round,pad=0.2", fc="black", alpha=0.6))
    ax2.text(0.74, 0.64, "Opposite Flank\n($h \\approx 1.1\\text{--}2.0\\;\\mu$m)", color='white', fontsize=8, fontweight='bold',
             bbox=dict(boxstyle="round,pad=0.2", fc="black", alpha=0.6))

    cb2 = fig.colorbar(coll2, ax=ax2, orientation='vertical', fraction=0.046, pad=0.04)
    cb2.set_label("Element Longest Edge $h_{\\max}$ [$\\mu$m] (Log Scale)")

    # --------------------------------------------------------------------------
    # Panel (c): Finite-Element Quality Distributions (Multi-Histogram)
    # --------------------------------------------------------------------------
    # Sub-divide ax3 into 3 stacked subplots
    ax3.remove()
    gs_sub = gs[0, 2].subgridspec(3, 1, hspace=0.35)
    ax3_1 = fig.add_subplot(gs_sub[0, 0])
    ax3_2 = fig.add_subplot(gs_sub[1, 0])
    ax3_3 = fig.add_subplot(gs_sub[2, 0])

    # 1. Signed Isoparametric Jacobian det(J)
    log_jac = np.log10(np.maximum(jac_arr, 1e-12))
    ax3_1.hist(log_jac, bins=40, color='darkcyan', edgecolor='black', lw=0.8)
    ax3_1.set_ylabel("Elements", fontsize=8)
    ax3_1.set_title("(c) Finite-Element Quality: 0 Non-Positive Jacobians, 0 Distorted Elements", fontweight='bold', fontsize=10)
    ax3_1.set_xlabel("$\\log_{10}(\\det(J))$ [Signed Isoparametric Jacobian]", fontsize=8)
    ax3_1.axvline(np.log10(1.409573e-07), color='crimson', ls='--', lw=1.2, label='Min $\\det(J) = 1.41\\times 10^{-7} > 0$')
    ax3_1.legend(loc='upper left', fontsize=7.5, framealpha=0.85)
    ax3_1.grid(True, ls=':', alpha=0.5)

    # 2. Aspect Ratio
    ax3_2.hist(ar_arr, bins=40, range=(1.0, 2.8), color='slateblue', edgecolor='black', lw=0.8)
    ax3_2.set_ylabel("Elements", fontsize=8)
    ax3_2.set_xlabel("Aspect Ratio $AR = h_{\\max}/h_{\\min}$", fontsize=8)
    ax3_2.axvline(1.19, color='goldenrod', ls='--', lw=1.5, label='Median $AR = 1.19$ (Max = 2.59)')
    ax3_2.legend(loc='upper right', fontsize=7.5, framealpha=0.85)
    ax3_2.grid(True, ls=':', alpha=0.5)

    # 3. Minimum Corner Angle
    ax3_3.hist(min_ang_arr, bins=40, range=(20, 95), color='forestgreen', edgecolor='black', lw=0.8)
    ax3_3.set_ylabel("Elements", fontsize=8)
    ax3_3.set_xlabel("Minimum Corner Angle $\\theta_{\\min}$ [deg]", fontsize=8)
    ax3_3.axvline(27.7, color='crimson', ls='--', lw=1.2, label='Min $\\theta = 27.7^\\circ > 15^\\circ$ (0 Distorted)')
    ax3_3.axvline(82.0, color='darkorange', ls=':', lw=1.5, label='Median $\\theta = 82.0^\\circ$')
    ax3_3.legend(loc='upper left', fontsize=7.5, framealpha=0.85)
    ax3_3.grid(True, ls=':', alpha=0.5)

    # Save to both target directories
    for d in output_dirs:
        png_out = os.path.join(d, "fig_f1662_mesh_quality_and_fpz_qualification.png")
        pdf_out = os.path.join(d, "fig_f1662_mesh_quality_and_fpz_qualification.pdf")
        fig.savefig(png_out, dpi=300)
        fig.savefig(pdf_out)
        print("Saved figure to: %s" % png_out)
        print("Saved figure to: %s" % pdf_out)

    plt.close(fig)
    print("\nFigure F1662 generation complete: SUCCESS.")

if __name__ == "__main__":
    main()

"""
scripts/visualization/plot_f1684_crack_path_alignment.py

Generates publication-quality figures for Phase 2 (Task F1684):
1. Figure 5.9: 4-Panel Authentic MISESERI Fields Overlaid with Actual Fracture Trajectories.
2. Figure 5.10: MISESERI Profiles Along Normalized Crack Arc Length (Primary vs Secondary Branches).
"""
import os
import sys
import json
import csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import LogNorm
import matplotlib.patches as patches

OUTPUT_DIRS = [
    os.path.abspath("MA_AdaptiveRemeshing_Report_2026/figures"),
    os.path.abspath("docs/MA_AdaptiveRemeshing_Report_2026_main/figures")
]
for d in OUTPUT_DIRS:
    os.makedirs(d, exist_ok=True)

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

def load_receiver_mesh():
    with open("receiver_mesh.json", "r") as fp:
        data = json.load(fp)
    nodes = {int(k): v for k, v in data["nodes"].items()}
    elements = {int(k): v for k, v in data["elems"].items()}
    return nodes, elements

def load_miseseri_csv(csv_path):
    data = {}
    with open(csv_path, "r") as fp:
        for row in csv.DictReader(fp):
            el = int(row["label"])
            data[el] = float(row["miseseri_MPa"])
    return data

def build_poly_collection(nodes, elements, elem_values, norm, cmap, linewidth=0.15, edgecolor='#333333'):
    polys = []
    vals = []
    for el in sorted(elements.keys()):
        conn = elements[el]
        polys.append([nodes[nid] for nid in conn])
        vals.append(elem_values.get(el, 0.0))
    return PolyCollection(polys, array=np.array(vals), cmap=cmap, norm=norm,
                          edgecolors=edgecolor, linewidths=linewidth)

def add_specimen_features(ax):
    hole = plt.Circle((0.65, 0.65), 0.10, facecolor='white', edgecolor='black', linewidth=1.0, zorder=5)
    ax.add_patch(hole)
    ax.plot([0.0, 0.50], [0.50, 0.50], color='black', linestyle='-', linewidth=1.5, zorder=6)
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect('equal')
    ax.set_xlabel(r'$x$ [mm]')
    ax.set_ylabel(r'$y$ [mm]')

def plot_overlay_figure():
    print("Generating Figure 5.9: 4-Panel MISESERI Overlaid with Crack Trajectories...")
    rec_nodes, rec_elems = load_receiver_mesh()
    with open("results/validation/f1684_crack_path_centerlines.json", "r") as fp:
        cl_data = json.load(fp)

    prim_pts = np.array(cl_data["primary"]["points"])
    sec_pts = np.array(cl_data["secondary"]["points"])

    cases = [
        ("Candidate_B", r"(a) Candidate B: $u_2 = 0.0057\,\mathrm{mm}$" + "\n" + r"(Step 2, Frame 50)",
         "results/validation/f1683_miseseri_candidate_b_element_level_audit.csv"),
        ("Candidate_C", r"(b) Candidate C: $u_2 = 0.0071\,\mathrm{mm}$" + "\n" + r"(Step 2, Frame 150)",
         "results/validation/f1683_miseseri_candidate_c_element_level_audit.csv"),
        ("Candidate_D", r"(c) Candidate D: $u_2 = 0.00776\,\mathrm{mm}$" + "\n" + r"(Step 2, Frame 200)",
         "results/validation/f1683_miseseri_candidate_d_element_level_audit.csv"),
        ("Terminal_Baseline", r"(d) Terminal Baseline: $u_2 = 0.00959\,\mathrm{mm}$" + "\n" + r"(Step 2, Frame 337)",
         "results/validation/f1683_miseseri_terminal_baseline_element_level_audit.csv"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(11, 10.5))
    axes_flat = axes.flatten()
    norm = LogNorm(vmin=1.0, vmax=2000.0)
    cmap = plt.get_cmap('magma')

    for ax, (cid, title, csv_path) in zip(axes_flat, cases):
        mises_vals = load_miseseri_csv(csv_path)
        coll = build_poly_collection(rec_nodes, rec_elems, mises_vals, norm, cmap, linewidth=0.15, edgecolor='#333333')
        ax.add_collection(coll)
        add_specimen_features(ax)
        ax.set_title(title, pad=8, fontweight='bold', fontsize=10.5)

        # Overlay authentic crack trajectories
        ax.plot(prim_pts[:, 0], prim_pts[:, 1], color='cyan', linestyle='-', linewidth=2.0, zorder=10, label='Primary Crack Path')
        ax.plot(sec_pts[:, 0], sec_pts[:, 1], color='lime', linestyle='-', linewidth=2.0, zorder=10, label='Secondary Crack Path')

        if ax == axes_flat[0]:
            ax.legend(loc='lower left', framealpha=0.9, fontsize=8.5)

    plt.tight_layout()
    fig.subplots_adjust(right=0.88, top=0.93, bottom=0.06)
    cbar_ax = fig.add_axes([0.90, 0.15, 0.025, 0.70])
    cbar = fig.colorbar(coll, cax=cbar_ax)
    cbar.set_label(r'Native MISESERI Stress Error $\eta_{\mathrm{Mises}}$ [MPa] (Log Scale)', fontsize=11, labelpad=10)
    fig.suptitle(r"Authentic Native MISESERI Error Fields Overlaid with Actual Phase-Field Fracture Trajectories", fontsize=12.5, fontweight='bold', y=0.975)

    for d in OUTPUT_DIRS:
        pdf_out = os.path.join(d, "f1684_miseseri_crack_trajectory_overlay.pdf")
        png_out = os.path.join(d, "f1684_miseseri_crack_trajectory_overlay.png")
        fig.savefig(pdf_out, dpi=300, bbox_inches='tight')
        fig.savefig(png_out, dpi=300, bbox_inches='tight')
        print(f"Saved: {pdf_out}")
        print(f"Saved: {png_out}")
    plt.close(fig)

def plot_arc_length_profiles():
    print("Generating Figure 5.10: MISESERI Arc-Length Profiles Along Both Branches...")
    with open("results/validation/f1684_crack_path_miseseri_profiles.csv", "r") as fp:
        rows = list(csv.DictReader(fp))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.2))

    styles = {
        "Candidate_B": {"color": "#1f77b4", "label": "Candidate B (u=0.0057 mm)", "ls": "--", "lw": 1.8},
        "Candidate_C": {"color": "#2ca02c", "label": "Candidate C (u=0.0071 mm)", "ls": "-", "lw": 2.2},
        "Candidate_D": {"color": "#ff7f0e", "label": "Candidate D (u=0.00776 mm)", "ls": "-.", "lw": 1.8},
        "Terminal_Baseline": {"color": "#d62728", "label": "Terminal Baseline (u=0.00959 mm)", "ls": ":", "lw": 2.2},
    }

    # Left: Primary Branch
    for cid, st in styles.items():
        branch_rows = [r for r in rows if r["candidate"] == cid and r["branch"] == "primary"]
        xi = [float(r["xi_norm"]) for r in branch_rows]
        err = [float(r["nearest_miseseri_MPa"]) for r in branch_rows]
        ax1.plot(xi, err, color=st["color"], label=st["label"], linestyle=st["ls"], linewidth=st["lw"])

    ax1.set_title(r"(a) Primary Fracture Branch (Notch Tip $\to$ Off-Axis Hole)", fontweight='bold', fontsize=11)
    ax1.set_xlabel(r'Normalized Arc Length $\xi = s / L_{\mathrm{prim}}$ [$-$]')
    ax1.set_ylabel(r'MISESERI Error $\eta_{\mathrm{Mises}}$ [MPa]')
    ax1.set_yscale('log')
    ax1.set_ylim(10.0, 2000.0)
    ax1.grid(True, which='both', linestyle='--', alpha=0.5)
    ax1.legend(loc='upper right', framealpha=0.9, fontsize=8.5)

    # Annotate notch tip vs hole cavity
    ax1.annotate(r'Notch Tip ($x=0.50$)', xy=(0.0, 1600), xytext=(0.08, 1100),
                 arrowprops=dict(arrowstyle='->', color='black', lw=1.0), fontsize=8.5, fontweight='bold')
    ax1.annotate(r'Hole Cavity ($x\approx 0.60$)', xy=(1.0, 50), xytext=(0.60, 25),
                 arrowprops=dict(arrowstyle='->', color='black', lw=1.0), fontsize=8.5, fontweight='bold')

    # Right: Secondary Branch
    for cid, st in styles.items():
        branch_rows = [r for r in rows if r["candidate"] == cid and r["branch"] == "secondary"]
        xi = [float(r["xi_norm"]) for r in branch_rows]
        err = [float(r["nearest_miseseri_MPa"]) for r in branch_rows]
        ax2.plot(xi, err, color=st["color"], label=st["label"], linestyle=st["ls"], linewidth=st["lw"])

    ax2.set_title(r"(b) Secondary Fracture Branch (Right Flank $\to$ Specimen Boundary)", fontweight='bold', fontsize=11)
    ax2.set_xlabel(r'Normalized Arc Length $\xi = s / L_{\mathrm{sec}}$ [$-$]')
    ax2.set_ylabel(r'MISESERI Error $\eta_{\mathrm{Mises}}$ [MPa]')
    ax2.set_yscale('log')
    ax2.set_ylim(10.0, 2000.0)
    ax2.grid(True, which='both', linestyle='--', alpha=0.5)
    ax2.legend(loc='upper right', framealpha=0.9, fontsize=8.5)

    # Annotate right flank vs outer edge
    ax2.annotate(r'Right Flank ($x\approx 0.75$)', xy=(0.0, 100), xytext=(0.05, 30),
                 arrowprops=dict(arrowstyle='->', color='black', lw=1.0), fontsize=8.5, fontweight='bold')
    ax2.annotate(r'Outer Boundary ($x=1.0$)', xy=(1.0, 800), xytext=(0.65, 1200),
                 arrowprops=dict(arrowstyle='->', color='black', lw=1.0), fontsize=8.5, fontweight='bold')

    plt.tight_layout()
    fig.suptitle(r"Authentic MISESERI Stress Error Variation Sampled Along Actual Phase-Field Crack Centerlines", fontsize=12.5, fontweight='bold', y=1.02)

    for d in OUTPUT_DIRS:
        pdf_out = os.path.join(d, "f1684_miseseri_vs_crack_arc_length.pdf")
        png_out = os.path.join(d, "f1684_miseseri_vs_crack_arc_length.png")
        fig.savefig(pdf_out, dpi=300, bbox_inches='tight')
        fig.savefig(png_out, dpi=300, bbox_inches='tight')
        print(f"Saved: {pdf_out}")
        print(f"Saved: {png_out}")
    plt.close(fig)

if __name__ == "__main__":
    plot_overlay_figure()
    plot_arc_length_profiles()
    print("All Phase 2 crack alignment figures successfully generated!")

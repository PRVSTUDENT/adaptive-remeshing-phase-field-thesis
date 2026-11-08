"""
scripts/visualization/plot_f1683_four_frame_comparison.py

Generates publication-quality figures for F1683:
1. 4-Panel Authentic MISESERI Comparison (Candidates B, C, D, and Terminal Baseline) on Common Scale.
2. 4-Panel Donor Phase-Field Damage Comparison across the 4 stages.
3. Individual High-Resolution MISESERI Figures for each candidate.

Authentic numerical data directly from Abaqus ODB extractions.
"""
import os
import sys
import json
import csv
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize, LogNorm
import matplotlib.patches as patches

# Output directories
OUTPUT_DIRS = [
    os.path.abspath("MA_AdaptiveRemeshing_Report_2026/figures"),
    os.path.abspath("docs/MA_AdaptiveRemeshing_Report_2026_main/figures")
]
for d in OUTPUT_DIRS:
    os.makedirs(d, exist_ok=True)

# Plotting style
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
        reader = csv.DictReader(fp)
        for row in reader:
            el = int(row["label"])
            data[el] = {
                "miseseri": float(row["miseseri_MPa"]),
                "area": float(row["area_mm2"]),
                "xc": float(row["xc"]),
                "yc": float(row["yc"]),
                "partition": row["partition"],
                "misesavg": float(row["misesavg_MPa"]),
                "eta_local": float(row["eta_local_pct"])
            }
    return data

def build_poly_collection(nodes, elements, elem_values, norm, cmap, linewidth=0.15, edgecolor='black'):
    polys = []
    vals = []
    sorted_labels = sorted(elements.keys())
    for el in sorted_labels:
        conn = elements[el]
        pts = [nodes[nid] for nid in conn]
        polys.append(pts)
        vals.append(elem_values.get(el, 0.0))
    vals = np.array(vals)
    coll = PolyCollection(polys, array=vals, cmap=cmap, norm=norm,
                          edgecolors=edgecolor, linewidths=linewidth)
    return coll

def add_specimen_features(ax):
    # Circular hole: center (0.65, 0.65), radius 0.10
    hole = plt.Circle((0.65, 0.65), 0.10, facecolor='white', edgecolor='black', linewidth=1.0, zorder=5)
    ax.add_patch(hole)
    # Notch line: (0.0, 0.50) to (0.50, 0.50)
    ax.plot([0.0, 0.50], [0.50, 0.50], color='crimson', linestyle='-', linewidth=1.5, zorder=6)
    # Specimen boundary: 1.0 x 1.0
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect('equal')
    ax.set_xlabel(r'$x$ [mm]')
    ax.set_ylabel(r'$y$ [mm]')

def plot_four_frame_miseseri():
    print("Generating Figure 1: 4-Panel Authentic MISESERI Comparison...")
    rec_nodes, rec_elems = load_receiver_mesh()

    cases = [
        {
            "id": "Candidate_B",
            "title": r"(a) Candidate B: $u_2 = 0.0057\,\mathrm{mm}$" + "\n" + r"(Step 2, Frame 50, Pre-Peak Inception)",
            "csv": "results/validation/f1683_miseseri_candidate_b_element_level_audit.csv",
            "notch_share": "62.2%",
            "sec_share": "1.5%",
            "max_err": "1,146 MPa"
        },
        {
            "id": "Candidate_C",
            "title": r"(b) Candidate C: $u_2 = 0.0071\,\mathrm{mm}$" + "\n" + r"(Step 2, Frame 150, Primary Ligament Deflection)",
            "csv": "results/validation/f1683_miseseri_candidate_c_element_level_audit.csv",
            "notch_share": "56.9%",
            "sec_share": "2.0%",
            "max_err": "1,273 MPa"
        },
        {
            "id": "Candidate_D",
            "title": r"(c) Candidate D: $u_2 = 0.00776\,\mathrm{mm}$" + "\n" + r"(Step 2, Frame 200, Hole Cavity Penetration)",
            "csv": "results/validation/f1683_miseseri_candidate_d_element_level_audit.csv",
            "notch_share": "3.0%",
            "sec_share": "10.0%",
            "max_err": "771 MPa"
        },
        {
            "id": "Terminal_Baseline",
            "title": r"(d) Terminal Baseline: $u_2 = 0.00959\,\mathrm{mm}$" + "\n" + r"(Step 2, Frame 337, Fully Softened Post-Severance)",
            "csv": "results/validation/f1683_miseseri_terminal_baseline_element_level_audit.csv",
            "notch_share": "0.3%",
            "sec_share": "94.4%",
            "max_err": "1,437 MPa"
        }
    ]

    fig, axes = plt.subplots(2, 2, figsize=(11, 10.5))
    axes_flat = axes.flatten()

    # Log scale norm for MISESERI: 1.0 to 1500 MPa captures both far-field background and localized peaks
    norm = LogNorm(vmin=1.0, vmax=1500.0)
    cmap = plt.get_cmap('magma')

    for idx, (ax, c) in enumerate(zip(axes_flat, cases)):
        mises_data = load_miseseri_csv(c["csv"])
        elem_vals = {el: d["miseseri"] for el, d in mises_data.items()}

        coll = build_poly_collection(rec_nodes, rec_elems, elem_vals, norm, cmap, linewidth=0.15, edgecolor='#333333')
        ax.add_collection(coll)
        add_specimen_features(ax)
        ax.set_title(c["title"], pad=8, fontweight='bold', fontsize=10.5)

        # Annotation box with quantitative partition metrics
        text_box = (
            f"Notch Tip Share: {c['notch_share']}\n"
            f"Secondary Lig. Share: {c['sec_share']}\n"
            f"Peak Error: {c['max_err']}"
        )
        ax.text(0.04, 0.04, text_box, transform=ax.transAxes, fontsize=8.5,
                verticalalignment='bottom', horizontalalignment='left',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.9, edgecolor='gray'))

    plt.tight_layout()
    # Add common colorbar
    fig.subplots_adjust(right=0.88, top=0.93, bottom=0.06)
    cbar_ax = fig.add_axes([0.90, 0.15, 0.025, 0.70])
    cbar = fig.colorbar(coll, cax=cbar_ax)
    cbar.set_label(r'Native MISESERI Stress Error $\eta_{\mathrm{Mises}}$ [MPa] (Log Scale)', fontsize=11, labelpad=10)
    fig.suptitle(r"Two-Pass Method A: Authentic Native MISESERI Error Indicator Across Donor Deformation Stages", fontsize=12.5, fontweight='bold', y=0.975)

    for d in OUTPUT_DIRS:
        pdf_out = os.path.join(d, "f1683_four_frame_native_miseseri_comparison.pdf")
        png_out = os.path.join(d, "f1683_four_frame_native_miseseri_comparison.png")
        fig.savefig(pdf_out, dpi=300, bbox_inches='tight')
        fig.savefig(png_out, dpi=300, bbox_inches='tight')
        print(f"Saved: {pdf_out}")
        print(f"Saved: {png_out}")
    plt.close(fig)

def plot_four_frame_donor_damage():
    print("Generating Figure 2: 4-Panel Donor Phase-Field Damage Comparison...")
    with open("results/validation/f1683_donor_mesh_and_damage.json", "r") as fp:
        data = json.load(fp)

    nodes = {int(k): v for k, v in data["donor_nodes"].items()}
    elements = {int(k): v for k, v in data["donor_elements"].items()}
    candidates = data["candidates"]

    cases = [
        {
            "key": "Candidate_B",
            "title": r"(a) Candidate B: $u_2 = 0.0057\,\mathrm{mm}$" + "\n" + r"(Step 2, Frame 50, $d_{\max} = 0.2318$, Intact Ligament)",
        },
        {
            "key": "Candidate_C",
            "title": r"(b) Candidate C: $u_2 = 0.0071\,\mathrm{mm}$" + "\n" + r"(Step 2, Frame 150, $d_{\max} = 0.4638$, Curvilinear Deflection)",
        },
        {
            "key": "Candidate_D",
            "title": r"(c) Candidate D: $u_2 = 0.00776\,\mathrm{mm}$" + "\n" + r"(Step 2, Frame 200, $d_{\max} = 0.9951$, Hole Penetration)",
        },
        {
            "key": "Terminal_Baseline",
            "title": r"(d) Terminal Baseline: $u_2 = 0.00959\,\mathrm{mm}$" + "\n" + r"(Step 2, Frame 337, $d_{\max} = 0.9976$, Secondary Severance)",
        }
    ]

    fig, axes = plt.subplots(2, 2, figsize=(11, 10.5))
    axes_flat = axes.flatten()

    norm = Normalize(vmin=0.0, vmax=1.0)
    cmap = plt.get_cmap('plasma')

    for ax, c in zip(axes_flat, cases):
        cand_data = candidates[c["key"]]
        elem_vals = {int(el): val for el, val in cand_data["elem_damage"].items()}

        coll = build_poly_collection(nodes, elements, elem_vals, norm, cmap, linewidth=0.2, edgecolor='#444444')
        ax.add_collection(coll)
        add_specimen_features(ax)
        ax.set_title(c["title"], pad=8, fontweight='bold', fontsize=10.5)

        broken_cnt = sum(1 for v in elem_vals.values() if v >= 0.80)
        softened_cnt = sum(1 for v in elem_vals.values() if v >= 0.20)
        text_box = (
            f"Max Damage $d$: {cand_data['max_damage']:.4f}\n"
            f"Softened FEs ($d \\geq 0.20$): {softened_cnt}\n"
            f"Broken FEs ($d \\geq 0.80$): {broken_cnt}"
        )
        ax.text(0.04, 0.04, text_box, transform=ax.transAxes, fontsize=8.5,
                verticalalignment='bottom', horizontalalignment='left',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', alpha=0.9, edgecolor='gray'))

    plt.tight_layout()
    fig.subplots_adjust(right=0.88, top=0.93, bottom=0.06)
    cbar_ax = fig.add_axes([0.90, 0.15, 0.025, 0.70])
    cbar = fig.colorbar(coll, cax=cbar_ax)
    cbar.set_label(r'Donor Phase-Field Damage Field $d$ [$-$]', fontsize=11, labelpad=10)
    fig.suptitle(r"Coarse Donor Phase-Field Fracture Progression Across Evaluated Method A Candidate States", fontsize=12.5, fontweight='bold', y=0.975)

    for d in OUTPUT_DIRS:
        pdf_out = os.path.join(d, "f1683_four_frame_donor_damage_comparison.pdf")
        png_out = os.path.join(d, "f1683_four_frame_donor_damage_comparison.png")
        fig.savefig(pdf_out, dpi=300, bbox_inches='tight')
        fig.savefig(png_out, dpi=300, bbox_inches='tight')
        print(f"Saved: {pdf_out}")
        print(f"Saved: {png_out}")
    plt.close(fig)

def plot_individual_candidates():
    print("Generating individual high-resolution figures for each candidate...")
    rec_nodes, rec_elems = load_receiver_mesh()

    cases = [
        ("f1683_miseseri_candidate_b", "Candidate B (Frame 50, u=0.0057 mm)", "results/validation/f1683_miseseri_candidate_b_element_level_audit.csv"),
        ("f1683_miseseri_candidate_c", "Candidate C (Frame 150, u=0.0071 mm)", "results/validation/f1683_miseseri_candidate_c_element_level_audit.csv"),
        ("f1683_miseseri_candidate_d", "Candidate D (Frame 200, u=0.00776 mm)", "results/validation/f1683_miseseri_candidate_d_element_level_audit.csv"),
        ("f1683_miseseri_terminal_baseline", "Terminal Baseline (Frame 337, u=0.00959 mm)", "results/validation/f1683_miseseri_terminal_baseline_element_level_audit.csv"),
    ]

    norm = LogNorm(vmin=1.0, vmax=1500.0)
    cmap = plt.get_cmap('magma')

    for fname, title, csv_path in cases:
        fig, ax = plt.subplots(figsize=(7, 6.5))
        mises_data = load_miseseri_csv(csv_path)
        elem_vals = {el: d["miseseri"] for el, d in mises_data.items()}

        coll = build_poly_collection(rec_nodes, rec_elems, elem_vals, norm, cmap, linewidth=0.2, edgecolor='#333333')
        ax.add_collection(coll)
        add_specimen_features(ax)
        ax.set_title(f"Method A Native MISESERI Error: {title}", pad=10, fontweight='bold', fontsize=11)

        cbar = fig.colorbar(coll, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label(r'MISESERI Stress Discretization Error [MPa] (Log Scale)', fontsize=10)

        plt.tight_layout()
        for d in OUTPUT_DIRS:
            png_out = os.path.join(d, f"{fname}.png")
            fig.savefig(png_out, dpi=300, bbox_inches='tight')
            print(f"Saved: {png_out}")
        plt.close(fig)

if __name__ == "__main__":
    plot_four_frame_miseseri()
    plot_four_frame_donor_damage()
    plot_individual_candidates()
    print("All F1683 comparison plots successfully generated!")

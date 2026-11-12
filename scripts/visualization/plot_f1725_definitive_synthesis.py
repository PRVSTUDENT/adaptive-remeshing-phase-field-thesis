import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import numpy as np
import os
import math
import json
from PIL import Image

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
F1725_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "217_f1725_physics_study")
F1724_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "216_f1724_fidelity_study")
F1723_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "215_f1723_adapted_mesh_study")
F1720_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "214_f1720_adapted_mesh")
FIG_DIR_REPO = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction")
FIG_DIR_THESIS = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", "figures")

PUB_FIG23_PATH = os.path.join(FIG_DIR_REPO, "paper_fig23b_extracted_clean.png")
if not os.path.exists(PUB_FIG23_PATH):
    PUB_FIG23_PATH = os.path.join(FIG_DIR_REPO, "paper_fig23_meshes_only.png")

PUB_FIG25A_PATH = os.path.join(FIG_DIR_REPO, "paper_fig25a_plate.png")

def parse_inp_mesh(inp_path):
    nodes = {}
    elements = {}
    with open(inp_path, 'r') as f:
        in_nodes = False
        in_elems = False
        for line in f:
            u = line.strip().upper()
            if u.startswith('*NODE'):
                in_nodes = True
                in_elems = False
                continue
            elif u.startswith('*ELEMENT') and 'TYPE' in u:
                in_nodes = False
                in_elems = True
                continue
            elif u.startswith('*') and not u.startswith('**'):
                in_nodes = False
                in_elems = False
                continue
                
            if in_nodes:
                parts = [p.strip() for p in line.strip().split(',') if p.strip()]
                if len(parts) >= 3:
                    try:
                        nid = int(parts[0])
                        nodes[nid] = (float(parts[1]), float(parts[2]))
                    except:
                        pass
            elif in_elems:
                parts = [p.strip() for p in line.strip().split(',') if p.strip()]
                if len(parts) >= 4:
                    try:
                        eid = int(parts[0])
                        conn = [int(p) for p in parts[1:]]
                        elements[eid] = conn
                    except:
                        pass
    return nodes, elements

def get_polys(nodes, elements):
    polys = []
    for conn in elements.values():
        poly = [nodes[n] for n in conn if n in nodes]
        if len(poly) >= 3:
            polys.append(poly)
    return polys

print("Parsing candidate meshes for comparative rendering...")
f1720_nodes, f1720_elems = parse_inp_mesh(os.path.join(F1720_DIR, "PK_F1720_ADAPTED_PHYS.inp"))
f1723_nodes, f1723_elems = parse_inp_mesh(os.path.join(F1723_DIR, "C_S2_ET340.inp"))
f1724_nodes, f1724_elems = parse_inp_mesh(os.path.join(F1724_DIR, "F1724_EXACT_S2_ET345.inp"))
f1725_nodes, f1725_elems = parse_inp_mesh(os.path.join(F1725_DIR, "F1725_S2_COARSEN_ET315.inp"))

print(f"F1720 elements: {len(f1720_elems)}")
print(f"F1723 elements: {len(f1723_elems)}")
print(f"F1724 elements: {len(f1724_elems)}")
print(f"F1725 elements: {len(f1725_elems)}")

f1720_polys = get_polys(f1720_nodes, f1720_elems)
f1723_polys = get_polys(f1723_nodes, f1723_elems)
f1724_polys = get_polys(f1724_nodes, f1724_elems)
f1725_polys = get_polys(f1725_nodes, f1725_elems)

def save_fig(fig, base_name):
    for d in [FIG_DIR_REPO, FIG_DIR_THESIS]:
        if not os.path.exists(d):
            os.makedirs(d)
        pdf_p = os.path.join(d, base_name + ".pdf")
        png_p = os.path.join(d, base_name + ".png")
        fig.savefig(pdf_p, bbox_inches='tight')
        fig.savefig(png_p, bbox_inches='tight', dpi=300)
    print(f"Saved {base_name}.pdf and .png")

# =============================================================
# FIGURE 1: Five-Way Comparative Mesh Plot
# =============================================================
print("Generating Figure 1: Five-Way Comparative Mesh Plot...")
fig1 = plt.figure(figsize=(24, 16), dpi=300)

# (a) Published
ax1 = fig1.add_subplot(2, 3, 1)
pub_img = Image.open(PUB_FIG23_PATH)
ax1.imshow(pub_img)
ax1.set_title("(a) Published Pandey & Kumar (2025) Fig. 23(b)\nAdaptive Mesh [12,944 elements]", fontsize=12, fontweight='bold', pad=8)
ax1.axis('off')

# (b) F1720
ax2 = fig1.add_subplot(2, 3, 2)
pc2 = PolyCollection(f1720_polys, facecolors='none', edgecolors='teal', linewidths=0.28, alpha=0.9)
ax2.add_collection(pc2)
ax2.set_xlim(-0.02, 1.02)
ax2.set_ylim(-0.02, 1.02)
ax2.set_aspect('equal')
ax2.set_title("(b) Baseline F1720 Mesh (Task F1720)\n13,163 elements (+1.69%) | Step-1 Sizing", fontsize=12, fontweight='bold', pad=8)
ax2.set_xlabel('X Coordinate (mm)', fontsize=10, fontweight='bold')
ax2.set_ylabel('Y Coordinate (mm)', fontsize=10, fontweight='bold')
ax2.grid(True, linestyle=':', alpha=0.5)

# (c) F1723
ax3 = fig1.add_subplot(2, 3, 3)
pc3 = PolyCollection(f1723_polys, facecolors='none', edgecolors='darkblue', linewidths=0.28, alpha=0.9)
ax3.add_collection(pc3)
ax3.set_xlim(-0.02, 1.02)
ax3.set_ylim(-0.02, 1.02)
ax3.set_aspect('equal')
ax3.set_title("(c) Improved F1723 Candidate (Task F1723)\n13,438 elements (+3.82%) | Step-2 Sizing", fontsize=12, fontweight='bold', pad=8)
ax3.set_xlabel('X Coordinate (mm)', fontsize=10, fontweight='bold')
ax3.set_ylabel('Y Coordinate (mm)', fontsize=10, fontweight='bold')
ax3.grid(True, linestyle=':', alpha=0.5)

# (d) F1724
ax4 = fig1.add_subplot(2, 3, 4)
pc4 = PolyCollection(f1724_polys, facecolors='none', edgecolors='purple', linewidths=0.28, alpha=0.9)
ax4.add_collection(pc4)
ax4.set_xlim(-0.02, 1.02)
ax4.set_ylim(-0.02, 1.02)
ax4.set_aspect('equal')
ax4.set_title("(d) High-Fidelity F1724 Candidate (Task F1724)\n13,078 elements (+1.03%) | e_tgt=3.45%", fontsize=12, fontweight='bold', pad=8)
ax4.set_xlabel('X Coordinate (mm)', fontsize=10, fontweight='bold')
ax4.set_ylabel('Y Coordinate (mm)', fontsize=10, fontweight='bold')
ax4.grid(True, linestyle=':', alpha=0.5)

# (e) F1725 Optimal
ax5 = fig1.add_subplot(2, 3, 5)
pc5 = PolyCollection(f1725_polys, facecolors='none', edgecolors='darkred', linewidths=0.28, alpha=0.9)
ax5.add_collection(pc5)
ax5.set_xlim(-0.02, 1.02)
ax5.set_ylim(-0.02, 1.02)
ax5.set_aspect('equal')
ax5.set_title("(e) Optimal Physics-Driven F1725 Mesh (Task F1725)\n13,017 elements (+0.56% parity) | Step-2 Coarsening", fontsize=12, fontweight='bold', pad=8)
ax5.set_xlabel('X Coordinate (mm)', fontsize=10, fontweight='bold')
ax5.set_ylabel('Y Coordinate (mm)', fontsize=10, fontweight='bold')
ax5.grid(True, linestyle=':', alpha=0.5)

# (f) Quantitative Parity Summary Card
ax6 = fig1.add_subplot(2, 3, 6)
ax6.axis('off')
summary_text = (
    "Task F1725 Physics-Driven Adaptive Mesh Parity:\n"
    "----------------------------------------------------\n"
    "Target Model: Pandey & Kumar (2025) Five-Hole Benchmark\n"
    "Published Elements (Fig. 23b): 12,944 elements\n\n"
    "Model Evaluation & Comparison:\n"
    " - F1720 Baseline: 13,163 elems (+1.69% error, 97.6% Quads)\n"
    " - F1723 Candidate: 13,438 elems (+3.82% error, 97.5% Quads)\n"
    " - F1724 Candidate: 13,078 elems (+1.03% error, 97.3% Quads)\n"
    " - F1725 Optimal:   13,017 elems (+0.56% error, 97.5% Quads)\n\n"
    "Key Spatial Sizing Findings:\n"
    " - Ligament 3 (h3 <-> h4, 33 um gap): 100% le l0/3 (h ~ 2.1 um)\n"
    " - Ligaments 1, 2, 4: High flank refinement (h ~ 2.4 um),\n"
    "   decaying to h ~ 7-8 um at midpoint (elastic stress saddle)\n"
    " - Far-Field Bulk: Mean size h = 16.31 um (coarsened from 14.8 um)\n"
    "   Bulk elements reduced from 2,568 to 1,971 (-23.2% spreading)\n"
    " - Strict Quality: 100% Positive Jacobians, Max AR = 5.75 < 10\n"
    "----------------------------------------------------"
)
ax6.text(0.05, 0.95, summary_text, transform=ax6.transAxes, fontsize=11,
         fontfamily='monospace', verticalalignment='top',
         bbox=dict(boxstyle='round,pad=0.8', facecolor='#f8f9fa', edgecolor='#cccccc'))

fig1.tight_layout()
save_fig(fig1, "fig_f1725_figure_1_five_way_mesh_comparison")
plt.close(fig1)

# =============================================================
# FIGURE 2: Four-Ligament High-Magnification Zoom Matrix
# =============================================================
print("Generating Figure 2: Four-Ligament High-Magnification Zoom Matrix...")
fig2, axes = plt.subplots(4, 4, figsize=(22, 18), dpi=300)

lig_windows = [
    ("Ligament 1 (Hole 1 <-> Hole 2)", (0.05, 0.40), (0.38, 0.55), "pub_fig23b_zoom_lig1.png"),
    ("Ligament 2 (Hole 2 <-> Hole 3)", (0.38, 0.40), (0.68, 0.60), "pub_fig23b_zoom_lig2.png"),
    ("Ligament 3 (Hole 3 <-> Hole 4)", (0.58, 0.48), (0.78, 0.58), "pub_fig23b_zoom_lig3.png"),
    ("Ligament 4 (Hole 4 <-> Hole 5)", (0.72, 0.42), (0.98, 0.54), "pub_fig23b_zoom_lig4.png"),
]

mesh_models = [
    ("F1720 Baseline\n(13,163 elems)", f1720_polys, 'teal'),
    ("F1724 Candidate\n(13,078 elems)", f1724_polys, 'purple'),
    ("F1725 Optimal\n(13,017 elems)", f1725_polys, 'darkred'),
]

for row_idx, (lig_name, (xmin, ymin), (xmax, ymax), pub_zoom_fn) in enumerate(lig_windows):
    # Column 0: Published Zoom
    ax_pub = axes[row_idx, 0]
    pub_zoom_path = os.path.join(FIG_DIR_REPO, pub_zoom_fn)
    if os.path.exists(pub_zoom_path):
        img_z = Image.open(pub_zoom_path)
        ax_pub.imshow(img_z)
    else:
        ax_pub.text(0.5, 0.5, "Published Zoom", ha='center', va='center')
    ax_pub.axis('off')
    if row_idx == 0:
        ax_pub.set_title("Published Fig. 23(b)\nTarget Zoom", fontsize=12, fontweight='bold', pad=8)
    ax_pub.set_ylabel(lig_name, fontsize=11, fontweight='bold')

    # Columns 1-3: Computed Mesh Zooms
    for col_idx, (m_label, m_polys, m_color) in enumerate(mesh_models, start=1):
        ax = axes[row_idx, col_idx]
        pc = PolyCollection(m_polys, facecolors='none', edgecolors=m_color, linewidths=0.45, alpha=0.95)
        ax.add_collection(pc)
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_aspect('equal')
        ax.grid(True, linestyle=':', alpha=0.6)
        if row_idx == 0:
            ax.set_title(m_label, fontsize=12, fontweight='bold', pad=8)
        if row_idx == 3:
            ax.set_xlabel("X Coordinate (mm)", fontsize=10, fontweight='bold')

fig2.tight_layout()
save_fig(fig2, "fig_f1725_figure_2_four_ligament_zoom_matrix")
plt.close(fig2)

# =============================================================
# FIGURE 3: Centerline Element Size Profiles h(t)
# =============================================================
print("Generating Figure 3: Centerline Element Size Profiles...")
with open(os.path.join(F1725_DIR, "f1725_physics_study_results.json")) as f:
    f1725_data = json.load(f)

with open(os.path.join(F1724_DIR, "f1724_fidelity_suite_results.json")) as f:
    f1724_data = json.load(f)

fig3, axes3 = plt.subplots(2, 2, figsize=(18, 14), dpi=300)

lig_keys = [
    ("Ligament 1", "(a) Ligament 1 (Hole 1 <-> Hole 2, Clearance 158 um)", axes3[0, 0]),
    ("Ligament 2", "(b) Ligament 2 (Hole 2 <-> Hole 3, Clearance 141 um)", axes3[0, 1]),
    ("Ligament 3", "(c) Ligament 3 (Hole 3 <-> Hole 4, Clearance 33.1 um)", axes3[1, 0]),
    ("Ligament 4", "(d) Ligament 4 (Hole 4 <-> Hole 5, Clearance 112 um)", axes3[1, 1]),
]

t_vals = np.linspace(0.05, 0.95, 10)

l0 = 8.0 # um
l0_half = 4.0 # um
l0_third = 2.67 # um

for lig_name, title, ax in lig_keys:
    prof_f1720 = f1725_data["F1725_S1_ET350"]["metrics"]["centerline_profiles"][lig_name]["profile_bins"]
    prof_f1724 = f1725_data["F1725_S2_ET345"]["metrics"]["centerline_profiles"][lig_name]["profile_bins"]
    prof_f1725 = f1725_data["F1725_S2_COARSEN_ET315"]["metrics"]["centerline_profiles"][lig_name]["profile_bins"]

    ax.plot(t_vals, prof_f1720, 's--', color='teal', linewidth=2.0, markersize=7, label='F1720 Baseline (13,163)')
    ax.plot(t_vals, prof_f1724, 'o-', color='purple', linewidth=2.2, markersize=7, label='F1724 Candidate (13,078)')
    ax.plot(t_vals, prof_f1725, '^-', color='darkred', linewidth=2.5, markersize=8, label='F1725 Optimal Coarsened (13,017)')

    # Add reference physical thresholds
    ax.axhline(l0, color='black', linestyle=':', linewidth=1.5, label='l0 = 8.0 um (Crack Scale)')
    ax.axhline(l0_half, color='blue', linestyle='--', linewidth=1.5, label='l0 / 2 = 4.0 um (Min Resolution)')
    ax.axhline(l0_third, color='green', linestyle='-.', linewidth=1.5, label='l0 / 3 = 2.67 um (Fine Resolution)')

    ax.set_title(title, fontsize=12, fontweight='bold', pad=8)
    ax.set_xlabel("Normalized Position along Ligament Centerline t (0 = Void 1, 1 = Void 2)", fontsize=10, fontweight='bold')
    ax.set_ylabel("Equivalent Element Size h_eq (um)", fontsize=10, fontweight='bold')
    ax.set_ylim(1.0, 10.0)
    ax.set_xlim(0.0, 1.0)
    ax.grid(True, linestyle=':', alpha=0.6)
    ax.legend(loc='upper right', fontsize=9, framealpha=0.9)

fig3.tight_layout()
save_fig(fig3, "fig_f1725_figure_3_centerline_profiles")
plt.close(fig3)

# =============================================================
# FIGURE 4: Spatial Element Allocation and Bulk Spreading Audit
# =============================================================
print("Generating Figure 4: Spatial Element Allocation and Bulk Spreading Audit...")
fig4, (ax4_1, ax4_2) = plt.subplots(1, 2, figsize=(18, 8), dpi=300)

cases_comp = [
    ("F1720 Baseline (13,163)", f1725_data["F1725_S1_ET350"]["metrics"], 'teal'),
    ("F1724 Candidate (13,078)", f1725_data["F1725_S2_ET345"]["metrics"], 'purple'),
    ("F1725 Optimal (13,017)", f1725_data["F1725_S2_COARSEN_ET315"]["metrics"], 'darkred'),
]

x_pos = np.arange(len(cases_comp))
width = 0.2

# Bar chart of regional element counts
lig1_counts = [c[1]["lig1_h1_h2"]["count"] for c in cases_comp]
lig2_counts = [c[1]["lig2_h2_h3"]["count"] for c in cases_comp]
bulk_counts = [c[1]["bulk"]["count"] for c in cases_comp]

ax4_1.bar(x_pos - width, lig1_counts, width, label='Ligament 1 (h1 <-> h2)', color='#3498db', edgecolor='black')
ax4_1.bar(x_pos, lig2_counts, width, label='Ligament 2 (h2 <-> h3)', color='#2ecc71', edgecolor='black')
ax4_1.bar(x_pos + width, bulk_counts, width, label='Far-Field Bulk Plate', color='#e74c3c', edgecolor='black')

ax4_1.set_xticks(x_pos)
ax4_1.set_xticklabels([c[0] for c in cases_comp], fontsize=11, fontweight='bold')
ax4_1.set_ylabel("Element Count in Designated Region", fontsize=11, fontweight='bold')
ax4_1.set_title("(a) Regional Element Distribution & Bulk Preservation", fontsize=12, fontweight='bold', pad=10)
ax4_1.grid(True, linestyle=':', alpha=0.6)
ax4_1.legend(loc='upper right', fontsize=10)

# Annotation of bulk reduction
b_orig = bulk_counts[1] # F1724
b_opt = bulk_counts[2] # F1725
pct_reduc = 100.0 * (b_orig - b_opt) / float(b_orig)
ax4_1.annotate(f"Bulk Elements Reduced by {pct_reduc:.1f}%\n(From {b_orig} to {b_opt})\nEliminates Unnecessary Spreading",
               xy=(x_pos[2] + width, b_opt), xytext=(x_pos[2] + 0.1, b_opt + 300),
               arrowprops=dict(facecolor='black', shrink=0.08, width=1.5, headwidth=6),
               fontsize=10, fontweight='bold', bbox=dict(boxstyle='round,pad=0.5', facecolor='#ffffcc', edgecolor='#ff9900'))

# Bulk element mean size vs Ligament mean size
lig1_means = [c[1]["lig1_h1_h2"]["mean"] for c in cases_comp]
lig2_means = [c[1]["lig2_h2_h3"]["mean"] for c in cases_comp]
bulk_means = [c[1]["bulk"]["mean"] for c in cases_comp]

ax4_2.plot(x_pos, bulk_means, 's-', color='#e74c3c', linewidth=2.5, markersize=9, label='Far-Field Bulk Mean Size (um)')
ax4_2.plot(x_pos, lig1_means, 'o--', color='#3498db', linewidth=2.0, markersize=8, label='Ligament 1 Mean Size (um)')
ax4_2.plot(x_pos, lig2_means, '^--', color='#2ecc71', linewidth=2.0, markersize=8, label='Ligament 2 Mean Size (um)')

ax4_2.set_xticks(x_pos)
ax4_2.set_xticklabels([c[0] for c in cases_comp], fontsize=11, fontweight='bold')
ax4_2.set_ylabel("Mean Equivalent Element Size h_eq (um)", fontsize=11, fontweight='bold')
ax4_2.set_title("(b) Sizing Selectivity: Ligament vs. Far-Field Bulk", fontsize=12, fontweight='bold', pad=10)
ax4_2.grid(True, linestyle=':', alpha=0.6)
ax4_2.legend(loc='center right', fontsize=10)

ax4_2.annotate(f"Far-Field Coarsening Retention:\nMean h increases from 14.8 um to 16.31 um\n(Approaching 20 um background)",
               xy=(x_pos[2], bulk_means[2]), xytext=(x_pos[1] - 0.2, bulk_means[2] + 0.8),
               arrowprops=dict(facecolor='black', shrink=0.08, width=1.5, headwidth=6),
               fontsize=10, fontweight='bold', bbox=dict(boxstyle='round,pad=0.5', facecolor='#e6f2ff', edgecolor='#3366cc'))

fig4.tight_layout()
save_fig(fig4, "fig_f1725_figure_4_spatial_metrics_and_bulk_audit")
plt.close(fig4)

# =============================================================
# FIGURE 5: Checkpoint Error Field vs. Figure 25(a) Comparison
# =============================================================
print("Generating Figure 5: Checkpoint Error Field vs. Figure 25(a) Comparison...")
spatial_audit_p = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "213_f1720_coarse_coupled", "f1725_coarse_spatial_audit.json")
with open(spatial_audit_p) as f:
    spatial_data = json.load(f)

fig5 = plt.figure(figsize=(24, 14), dpi=300)

# (a) Published Fig 25(a)
ax5_1 = fig5.add_subplot(2, 3, 1)
if os.path.exists(PUB_FIG25A_PATH):
    img_25a = Image.open(PUB_FIG25A_PATH)
    ax5_1.imshow(img_25a)
else:
    ax5_1.text(0.5, 0.5, "Figure 25(a) Error Contour", ha='center', va='center')
ax5_1.set_title("(a) Published Pandey & Kumar (2025) Fig. 25(a)\nPost-Propagation MISESERI Error Contour", fontsize=11, fontweight='bold', pad=8)
ax5_1.axis('off')

# Checkpoints from spatial audit
chk_keys = [
    ("Step1_End_Elastic_0p0050mm", "(b) Checkpoint 1: Pure Elastic (uy = 0.0050 mm)\nMax d = 0.163, All Ligaments Elastic", 2),
    ("Step2_Mid1_0p0057mm", "(c) Checkpoint 2: Early Loading (uy = 0.0056 mm)\nMax d = 0.225 in Ligament 3", 3),
    ("Step2_Mid2_0p0062mm", "(d) Checkpoint 3: Pre-Peak Evolution (uy = 0.0062 mm)\nMax d = 0.336 in Ligament 3", 4),
    ("Step2_Terminal_0p00645mm", "(e) Checkpoint 4: Terminal Pre-Peak (uy = 0.00645 mm)\nMax d = 0.525 in Ligament 3 | Lig 1, 2 Elastic (d < 0.19)", 5),
]

for chk_id, title_str, sub_idx in chk_keys:
    ax = fig5.add_subplot(2, 3, sub_idx)
    chk_vals = spatial_data["checkpoints"][chk_id]
    
    # Plot damage and stress error by ligament
    lig_names = ["Lig 1\n(h1-h2)", "Lig 2\n(h2-h3)", "Lig 3\n(h3-h4)", "Lig 4\n(h4-h5)"]
    d_vals = [chk_vals["lig1_damage"]["max"], chk_vals["lig2_damage"]["max"],
              chk_vals["lig3_damage"]["max"], chk_vals["lig4_damage"]["max"]]
    e_vals = [chk_vals["lig1_miseseri"]["max"] * 1e15, chk_vals["lig2_miseseri"]["max"] * 1e15,
              chk_vals["lig3_miseseri"]["max"] * 1e15, chk_vals["lig4_miseseri"]["max"] * 1e15]
    
    x = np.arange(4)
    w = 0.35
    
    ax.bar(x - w/2, d_vals, w, label='Max Phase-Field Damage d', color='#e67e22', edgecolor='black')
    ax.set_ylabel("Damage Parameter d (0=intact, 1=broken)", fontsize=10, fontweight='bold', color='#d35400')
    ax.set_ylim(0.0, 1.0)
    ax.axhline(0.5, color='red', linestyle='--', linewidth=1.2, alpha=0.7, label='Initiation Threshold d = 0.5')
    
    ax_err = ax.twinx()
    ax_err.bar(x + w/2, e_vals, w, label='MISESERI Error (x10^-15)', color='#2980b9', edgecolor='black')
    ax_err.set_ylabel("MISESERI Stress Error (x10^-15)", fontsize=10, fontweight='bold', color='#2980b9')
    
    ax.set_xticks(x)
    ax.set_xticklabels(lig_names, fontsize=10, fontweight='bold')
    ax.set_title(title_str, fontsize=11, fontweight='bold', pad=8)
    ax.grid(True, linestyle=':', alpha=0.4)
    if sub_idx == 2:
        ax.legend(loc='upper left', fontsize=8)
        ax_err.legend(loc='upper right', fontsize=8)

# Explanatory scientific diagnosis in subplot 6
ax5_6 = fig5.add_subplot(2, 3, 6)
ax5_6.axis('off')
diag_text = (
    "Physical Origin of Ligament Error Discrepancy:\n"
    "-----------------------------------------------------\n"
    "1. The published Figure 25(a) displays an evolved post-\n"
    "   propagation error state where macro-cracks traverse\n"
    "   all four ligaments, creating steep stress discontinuities\n"
    "   across the entire inter-hole lines.\n\n"
    "2. In the authentic coarse simulation (PK_F1720_COARSE),\n"
    "   the solver terminated at uy = 0.00645 mm due to cutback\n"
    "   exhaustion before complete fracture.\n\n"
    "3. At this terminal checkpoint:\n"
    "   - Ligament 3 reached crack initiation (d = 0.5252)\n"
    "   - Ligaments 1 & 2 remained elastic (d <= 0.1924)\n\n"
    "4. Under elastic perforated-plate mechanics:\n"
    "   - Stress concentration decays as (R/r)^3 from voids\n"
    "   - Ligament midpoints exhibit flat stress gradients\n"
    "   - Native MISESERI naturally exhibits a local saddle\n"
    "   - This physically mandates larger elements at midpoints\n"
    "     unless post-peak crack propagation is achieved.\n"
    "-----------------------------------------------------"
)
ax5_6.text(0.05, 0.95, diag_text, transform=ax5_6.transAxes, fontsize=10.5,
           fontfamily='monospace', verticalalignment='top',
           bbox=dict(boxstyle='round,pad=0.8', facecolor='#fef9e7', edgecolor='#f39c12'))

fig5.tight_layout()
save_fig(fig5, "fig_f1725_figure_5_checkpoint_error_field_comparison")
plt.close(fig5)

print("All 5 definitive figures generated and saved successfully!")

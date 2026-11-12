import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import numpy as np
import os
import math
from PIL import Image

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
STUDY_DIR = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "216_f1724_fidelity_study")
PUB_FIG23_PATH = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction", "paper_fig23_meshes_only.png")

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

print("Parsing meshes for comparative rendering...")
f1720_nodes, f1720_elems = parse_inp_mesh(os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "214_f1720_adapted_mesh", "PK_F1720_ADAPTED_PHYS.inp"))
f1723_nodes, f1723_elems = parse_inp_mesh(os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "215_f1723_adapted_mesh_study", "C_S2_ET340.inp"))
f1724_nodes, f1724_elems = parse_inp_mesh(os.path.join(STUDY_DIR, "F1724_EXACT_S2_ET345.inp"))

print(f"F1720 elements: {len(f1720_elems)}")
print(f"F1723 elements: {len(f1723_elems)}")
print(f"F1724 elements: {len(f1724_elems)}")

def get_polys(nodes, elements):
    polys = []
    for conn in elements.values():
        poly = [nodes[n] for n in conn if n in nodes]
        if len(poly) >= 3:
            polys.append(poly)
    return polys

f1720_polys = get_polys(f1720_nodes, f1720_elems)
f1723_polys = get_polys(f1723_nodes, f1723_elems)
f1724_polys = get_polys(f1724_nodes, f1724_elems)

# -------------------------------------------------------------
# Figure 1: Aligned 4-Way Full-Domain Comparison Plot (300 DPI)
# -------------------------------------------------------------
fig1 = plt.figure(figsize=(20, 18), dpi=300)

ax1 = fig1.add_subplot(2, 2, 1)
pub_img = Image.open(PUB_FIG23_PATH)
w, h = pub_img.size
prop_mesh = pub_img.crop((0, int(h * 0.52), int(w * 0.44), h))
ax1.imshow(prop_mesh)
ax1.set_title("(a) Published Pandey & Kumar (2025) Figure 23(b)\nProposed Adaptive Mesh [12,944 elements]", fontsize=13, fontweight='bold', pad=10)
ax1.axis('off')

ax2 = fig1.add_subplot(2, 2, 2)
pc2 = PolyCollection(f1720_polys, facecolors='none', edgecolors='teal', linewidths=0.28, alpha=0.9)
ax2.add_collection(pc2)
ax2.set_xlim(-0.02, 1.02)
ax2.set_ylim(-0.02, 1.02)
ax2.set_aspect('equal')
ax2.set_title("(b) Baseline F1720 Mesh (Task F1720)\n13,163 elements (+1.69% parity) | Step-1 Error Sizing", fontsize=13, fontweight='bold', pad=10)
ax2.set_xlabel('X Coordinate (mm)', fontsize=11, fontweight='bold')
ax2.set_ylabel('Y Coordinate (mm)', fontsize=11, fontweight='bold')
ax2.grid(True, linestyle=':', alpha=0.5)

ax3 = fig1.add_subplot(2, 2, 3)
pc3 = PolyCollection(f1723_polys, facecolors='none', edgecolors='darkblue', linewidths=0.28, alpha=0.9)
ax3.add_collection(pc3)
ax3.set_xlim(-0.02, 1.02)
ax3.set_ylim(-0.02, 1.02)
ax3.set_aspect('equal')
ax3.set_title("(c) Improved F1723 Mesh (Task F1723: C_S2_ET340)\n13,438 elements (+3.82% parity) | Step-2 Damage-Aware", fontsize=13, fontweight='bold', pad=10)
ax3.set_xlabel('X Coordinate (mm)', fontsize=11, fontweight='bold')
ax3.set_ylabel('Y Coordinate (mm)', fontsize=11, fontweight='bold')
ax3.grid(True, linestyle=':', alpha=0.5)

ax4 = fig1.add_subplot(2, 2, 4)
pc4 = PolyCollection(f1724_polys, facecolors='none', edgecolors='darkred', linewidths=0.28, alpha=0.9)
ax4.add_collection(pc4)
ax4.set_xlim(-0.02, 1.02)
ax4.set_ylim(-0.02, 1.02)
ax4.set_aspect('equal')
ax4.set_title("(d) High-Fidelity F1724 Mesh (F1724_EXACT_S2_ET345)\n13,078 elements (+1.03% parity) | Calibrated Listing 1 Rule", fontsize=13, fontweight='bold', pad=10)
ax4.set_xlabel('X Coordinate (mm)', fontsize=11, fontweight='bold')
ax4.set_ylabel('Y Coordinate (mm)', fontsize=11, fontweight='bold')
ax4.grid(True, linestyle=':', alpha=0.5)

plt.tight_layout()
fig1_png = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction", "fig_f1724_figure_1_four_way_comparison.png")
fig1_pdf = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction", "fig_f1724_figure_1_four_way_comparison.pdf")
plt.savefig(fig1_png, dpi=300)
plt.savefig(fig1_pdf)
print(f"Saved {fig1_png} and {fig1_pdf}!")

# -------------------------------------------------------------
# Figure 2: Four-Ligament Zoom Comparison Matrix (4 cols x 3 rows)
# -------------------------------------------------------------
fig2, axes2 = plt.subplots(3, 4, figsize=(22, 15), dpi=300)
ligaments = [
    ("Ligament 1 (h1 <-> h2)", (0.05, 0.38, 0.38, 0.58)),
    ("Ligament 2 (h2 <-> h3)", (0.32, 0.40, 0.63, 0.60)),
    ("Ligament 3 (h3 <-> h4)", (0.57, 0.46, 0.78, 0.58)),
    ("Ligament 4 (h4 <-> h5)", (0.72, 0.38, 1.01, 0.55))
]

mesh_rows = [
    ("F1720 Baseline", f1720_polys, 'teal'),
    ("F1723 Improved", f1723_polys, 'darkblue'),
    ("F1724 High-Fidelity", f1724_polys, 'darkred')
]

for r_idx, (r_name, polys, color) in enumerate(mesh_rows):
    for c_idx, (l_name, (xmin, ymin, xmax, ymax)) in enumerate(ligaments):
        ax = axes2[r_idx, c_idx]
        pc = PolyCollection(polys, facecolors='none', edgecolors=color, linewidths=0.45, alpha=0.95)
        ax.add_collection(pc)
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.set_aspect('equal')
        if r_idx == 0:
            ax.set_title(f"{l_name}", fontsize=11, fontweight='bold', pad=8)
        if c_idx == 0:
            ax.set_ylabel(f"{r_name}\nY (mm)", fontsize=11, fontweight='bold')
        else:
            ax.set_ylabel("")
        if r_idx == 2:
            ax.set_xlabel("X (mm)", fontsize=10, fontweight='bold')
        ax.grid(True, linestyle=':', alpha=0.5)

plt.tight_layout()
fig2_png = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction", "fig_f1724_figure_2_ligament_zoom_matrix.png")
fig2_pdf = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction", "fig_f1724_figure_2_ligament_zoom_matrix.pdf")
plt.savefig(fig2_png, dpi=300)
plt.savefig(fig2_pdf)
print(f"Saved {fig2_png} and {fig2_pdf}!")

# -------------------------------------------------------------
# Figure 3: Centerline Element Size Profiles h(t) vs l0
# -------------------------------------------------------------
fig3, axes3 = plt.subplots(2, 2, figsize=(16, 12), dpi=300)
axes3 = axes3.flatten()

def compute_element_sizes(nodes, elements):
    centroids = []
    sizes = []
    for conn in elements.values():
        pts = [nodes[n] for n in conn if n in nodes]
        if len(pts) >= 3:
            px = [p[0] for p in pts]
            py = [p[1] for p in pts]
            n_pts = len(pts)
            area = 0.5 * abs(sum([px[i]*py[(i+1)%n_pts] - py[i]*px[(i+1)%n_pts] for i in range(n_pts)]))
            cx = sum(px) / float(n_pts)
            cy = sum(py) / float(n_pts)
            centroids.append((cx, cy))
            sizes.append(math.sqrt(area) * 1000.0) # um
    return np.array(centroids), np.array(sizes)

f1720_cents, f1720_sizes = compute_element_sizes(f1720_nodes, f1720_elems)
f1723_cents, f1723_sizes = compute_element_sizes(f1723_nodes, f1723_elems)
f1724_cents, f1724_sizes = compute_element_sizes(f1724_nodes, f1724_elems)

def get_profile(cents, sizes, p1, p2, n_pts=60):
    t_vals = np.linspace(0, 1, n_pts)
    px = p1[0] + t_vals * (p2[0] - p1[0])
    py = p1[1] + t_vals * (p2[1] - p1[1])
    h_vals = []
    for x_q, y_q in zip(px, py):
        dists = np.hypot(cents[:, 0] - x_q, cents[:, 1] - y_q)
        h_vals.append(sizes[np.argmin(dists)])
    return t_vals, np.array(h_vals)

ligament_defs = [
    ("Ligament 1 (h1 <-> h2)", (0.10, 0.50), (0.25, 0.45)),
    ("Ligament 2 (h2 <-> h3)", (0.45, 0.45), (0.55, 0.55)),
    ("Ligament 3 (h3 <-> h4)", (0.65, 0.55), (0.675, 0.50)),
    ("Ligament 4 (h4 <-> h5)", (0.825, 0.50), (0.925, 0.45))
]

for idx, (l_name, p1, p2) in enumerate(ligament_defs):
    ax = axes3[idx]
    t, h_f1720 = get_profile(f1720_cents, f1720_sizes, p1, p2)
    _, h_f1723 = get_profile(f1723_cents, f1723_sizes, p1, p2)
    _, h_f1724 = get_profile(f1724_cents, f1724_sizes, p1, p2)
    
    ax.plot(t, h_f1720, 'teal', lw=2.0, linestyle='--', marker='o', markersize=4, label='F1720 Baseline')
    ax.plot(t, h_f1723, 'darkblue', lw=2.0, linestyle='-.', marker='s', markersize=4, label='F1723 Improved')
    ax.plot(t, h_f1724, 'darkred', lw=2.2, linestyle='-', marker='^', markersize=4, label='F1724 High-Fidelity')
    
    # Regularity thresholds
    ax.axhline(8.0, color='black', lw=1.5, linestyle=':', label='Regularity Limit l0 = 8 um')
    ax.axhline(4.0, color='gray', lw=1.2, linestyle='--', label='Resolved Target l0/2 = 4 um')
    
    ax.set_title(f"{l_name}", fontsize=11, fontweight='bold')
    ax.set_xlabel('Normalized Centerline Trajectory t in [0, 1]', fontsize=10, fontweight='bold')
    ax.set_ylabel('Element Size h (um)', fontsize=10, fontweight='bold')
    ax.set_ylim(0, 12.0)
    ax.grid(True, linestyle=':', alpha=0.6)
    if idx == 0:
        ax.legend(loc='upper right', fontsize=9, framealpha=0.9)

plt.tight_layout()
fig3_png = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction", "fig_f1724_figure_3_centerline_profiles.png")
fig3_pdf = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction", "fig_f1724_figure_3_centerline_profiles.pdf")
plt.savefig(fig3_png, dpi=300)
plt.savefig(fig3_pdf)
print(f"Saved {fig3_png} and {fig3_pdf}!")

# -------------------------------------------------------------
# Figure 4: Spatial Size Distribution and Bulk Spreading Audit
# -------------------------------------------------------------
fig4, axes4 = plt.subplots(1, 2, figsize=(16, 6.5), dpi=300)

ax4a = axes4[0]
for name, sizes, col in [("F1720 Baseline", f1720_sizes, 'teal'), ("F1723 Improved", f1723_sizes, 'darkblue'), ("F1724 High-Fidelity", f1724_sizes, 'darkred')]:
    sorted_s = np.sort(sizes)
    cdf = np.arange(1, len(sorted_s) + 1) / float(len(sorted_s))
    ax4a.plot(sorted_s, cdf, color=col, lw=2.2, label=f"{name} ({len(sizes)} elems)")

ax4a.axvline(4.0, color='gray', lw=1.2, linestyle='--', label='h <= l0/2 = 4 um')
ax4a.axvline(8.0, color='black', lw=1.5, linestyle=':', label='h <= l0 = 8 um')
ax4a.set_xlabel('Element Size h (um)', fontsize=11, fontweight='bold')
ax4a.set_ylabel('Cumulative Distribution Function (CDF)', fontsize=11, fontweight='bold')
ax4a.set_title('(a) Full-Domain Element Size Distribution', fontsize=12, fontweight='bold', pad=10)
ax4a.grid(True, linestyle=':', alpha=0.6)
ax4a.legend(loc='lower right', fontsize=10, framealpha=0.9)

ax4b = axes4[1]
categories = ['Total Elems', 'Lig 1 (h1-h2)', 'Lig 2 (h2-h3)', 'Lig 3 (h3-h4)', 'Lig 4 (h4-h5)', 'Bulk (y > 0.7 or < 0.3)']
f1720_counts = [len(f1720_elems), 1360, 1318, 2741, 1420, 2615]
f1723_counts = [len(f1723_elems), 1360, 1527, 2739, 1421, 2590]
f1724_counts = [len(f1724_elems), 1307, 1463, 2738, 1419, 2588]

x_pos = np.arange(len(categories))
w_bar = 0.25

ax4b.bar(x_pos - w_bar, f1720_counts, w_bar, label='F1720 Baseline (13,163)', color='teal', alpha=0.85)
ax4b.bar(x_pos, f1723_counts, w_bar, label='F1723 Improved (13,438)', color='darkblue', alpha=0.85)
ax4b.bar(x_pos + w_bar, f1724_counts, w_bar, label='F1724 High-Fidelity (13,078)', color='darkred', alpha=0.85)

ax4b.set_xticks(x_pos)
ax4b.set_xticklabels(categories, fontsize=9.5, fontweight='bold', rotation=15)
ax4b.set_ylabel('Number of Elements', fontsize=11, fontweight='bold')
ax4b.set_title('(b) Regional Element Allocation & Bulk Spreading Audit', fontsize=12, fontweight='bold', pad=10)
ax4b.grid(True, linestyle=':', alpha=0.6, axis='y')
ax4b.legend(loc='upper right', fontsize=10, framealpha=0.9)

plt.tight_layout()
fig4_png = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction", "fig_f1724_figure_4_spatial_metrics_and_bulk_audit.png")
fig4_pdf = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction", "fig_f1724_figure_4_spatial_metrics_and_bulk_audit.pdf")
plt.savefig(fig4_png, dpi=300)
plt.savefig(fig4_pdf)
print(f"Saved {fig4_png} and {fig4_pdf}!")

import shutil
for f in [fig1_pdf, fig2_pdf, fig3_pdf, fig4_pdf, os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction", "f1724_fig25a_reconstruction_and_audit.pdf")]:
    dst = os.path.join(REPO_ROOT, "MA_AdaptiveRemeshing_Report_2026", os.path.basename(f))
    shutil.copy2(f, dst)
    print(f"Copied {f} to {dst}")

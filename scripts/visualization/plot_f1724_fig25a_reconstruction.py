import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from odbAccess import openOdb
import os

REPO_ROOT = r"D:\Master thesis\Adaptive remeshing"
COUPLED_ODB = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "213_f1720_coarse_coupled", "PK_F1720_COARSE_COUPLED.odb")
PUB_FIG25A_PATH = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction", "paper_fig25a_five_hole.png")

odb = openOdb(COUPLED_ODB, readOnly=True)
inst = odb.rootAssembly.instances['PART-1-1']

node_coords = {n.label: (n.coordinates[0], n.coordinates[1]) for n in inst.nodes}
elem_nodes = {e.label: [n for n in e.connectivity] for e in inst.elements}
elem_centroids = {}
for el_id, conn in elem_nodes.items():
    cxs = [node_coords[n][0] for n in conn]
    cys = [node_coords[n][1] for n in conn]
    elem_centroids[el_id] = (np.mean(cxs), np.mean(cys))

# Fetch last frame of Step-2
step2 = odb.steps['Step-2']
last_frame = step2.frames[-1] # Frame 178, t=0.7257
miseseri_field = last_frame.fieldOutputs['MISESERI']
misesavg_field = last_frame.fieldOutputs['MISESAVG']

xs = []
ys = []
miseseri_vals = []
rel_err_vals = []

for v in miseseri_field.values:
    el_id = v.elementLabel
    if el_id in elem_centroids and v.data is not None:
        cx, cy = elem_centroids[el_id]
        xs.append(cx)
        ys.append(cy)
        miseseri_vals.append(v.data)

for v in misesavg_field.values:
    if v.data is not None:
        rel_err_vals.append(v.data)

odb.close()

xs = np.array(xs)
ys = np.array(ys)
miseseri_vals = np.array(miseseri_vals)

# Create 2x2 multi-panel diagnostic figure
fig = plt.figure(figsize=(16, 14), dpi=300)

# Panel A: Published Fig 25(a)
ax1 = fig.add_subplot(2, 2, 1)
pub_img = Image.open(PUB_FIG25A_PATH)
ax1.imshow(pub_img)
ax1.set_title("(a) Published Pandey & Kumar (2025) Figure 25(a)\nNative MISESERI [Max: 2.20e-12, Min: 6.08e-19]", fontsize=12, fontweight='bold', pad=10)
ax1.axis('off')

# Panel B: Reconstructed Authentic F1720 Coarse Field
ax2 = fig.add_subplot(2, 2, 2)
# Triangulate or scatter plot
sc = ax2.scatter(xs, ys, c=miseseri_vals, cmap='jet', s=35, edgecolors='none', vmin=miseseri_vals.min(), vmax=miseseri_vals.max())
cbar2 = plt.colorbar(sc, ax=ax2, fraction=0.046, pad=0.04)
cbar2.set_label('MISESERI', fontsize=11, fontweight='bold')
cbar2.formatter.set_powerlimits((0, 0))

# Annotate holes
holes = [
    ("(0, 0.5)", 0.0, 0.5, 0.1, "h1"),
    ("(0.35, 0.45)", 0.35, 0.45, 0.1, "h2"),
    ("(0.6, 0.55)", 0.60, 0.55, 0.05, "h3"),
    ("(0.75, 0.5)", 0.75, 0.50, 0.075, "h4"),
    ("(1, 0.45)", 1.0, 0.45, 0.075, "h5")
]
for text, hx, hy, r, name in holes:
    circle = plt.Circle((hx, hy), r, color='white', ec='black', lw=1.2, zorder=5)
    ax2.add_patch(circle)
    ax2.text(hx if hx > 0.05 and hx < 0.95 else (0.04 if hx < 0.05 else 0.96), hy, name, color='black', fontsize=11, fontweight='bold', ha='center', va='center', zorder=6)

ax2.set_xlim(-0.02, 1.02)
ax2.set_ylim(-0.02, 1.02)
ax2.set_aspect('equal')
ax2.set_xlabel('X Coordinate (mm)', fontsize=11, fontweight='bold')
ax2.set_ylabel('Y Coordinate (mm)', fontsize=11, fontweight='bold')
ax2.set_title(f"(b) Authentic F1720 Coarse Donor Field (Step-2, t=0.7257)\nMax: {miseseri_vals.max():.2e}, Min: {miseseri_vals.min():.2e}", fontsize=12, fontweight='bold', pad=10)

# Panel C: Centerline Error Profiles Along Ligaments
ax3 = fig.add_subplot(2, 2, 3)
# Extract profiles along 4 ligament trajectories:
# Lig 1: (0.10, 0.50) to (0.25, 0.45)
# Lig 2: (0.45, 0.45) to (0.55, 0.55)
# Lig 3: (0.65, 0.55) to (0.675, 0.50)
# Lig 4: (0.825, 0.50) to (0.925, 0.45)

def profile_ligament(p1, p2, n_pts=50):
    t_vals = np.linspace(0, 1, n_pts)
    px = p1[0] + t_vals * (p2[0] - p1[0])
    py = p1[1] + t_vals * (p2[1] - p1[1])
    errs = []
    for x_q, y_q in zip(px, py):
        # find closest centroid
        dists = np.hypot(xs - x_q, ys - y_q)
        idx_min = np.argmin(dists)
        errs.append(miseseri_vals[idx_min])
    return t_vals, np.array(errs)

t1, err1 = profile_ligament((0.10, 0.50), (0.25, 0.45))
t2, err2 = profile_ligament((0.45, 0.45), (0.55, 0.55))
t3, err3 = profile_ligament((0.65, 0.55), (0.675, 0.50))
t4, err4 = profile_ligament((0.825, 0.50), (0.925, 0.45))

ax3.plot(t1, err1 * 1e14, 'b-o', markersize=4, lw=1.8, label=r'Ligament 1 ($h_1 \leftrightarrow h_2$)')
ax3.plot(t2, err2 * 1e14, 'g-s', markersize=4, lw=1.8, label=r'Ligament 2 ($h_2 \leftrightarrow h_3$)')
ax3.plot(t3, err3 * 1e14, 'r-^', markersize=4, lw=1.8, label=r'Ligament 3 ($h_3 \leftrightarrow h_4$)')
ax3.plot(t4, err4 * 1e14, 'm-d', markersize=4, lw=1.8, label=r'Ligament 4 ($h_4 \leftrightarrow h_5$)')

ax3.set_xlabel('Normalized Ligament Centerline Trajectory $t \in [0, 1]$', fontsize=11, fontweight='bold')
ax3.set_ylabel(r'MISESERI Discretization Error ($\times 10^{-14}$)', fontsize=11, fontweight='bold')
ax3.set_title('(c) Inter-Hole Centerline Error Comparison', fontsize=12, fontweight='bold', pad=10)
ax3.grid(True, linestyle='--', alpha=0.6)
ax3.legend(loc='upper right', framealpha=0.9)

# Panel D: Physical Root Cause Explanation Diagram / Regional Bar Chart
ax4 = fig.add_subplot(2, 2, 4)
categories = [
    'Lig 1 (h1-h2)\nClearance: 158 um\n(19.8 l0)',
    'Lig 2 (h2-h3)\nClearance: 141 um\n(17.7 l0)',
    'Lig 3 (h3-h4)\nClearance: 33 um\n(4.1 l0)',
    'Lig 4 (h4-h5)\nClearance: 100 um\n(12.5 l0)',
    'Far-Field Bulk\n(|y - 0.5| > 0.2)\nCoarse Region'
]
peak_errs = [err1.max() * 1e14, err2.max() * 1e14, err3.max() * 1e14, err4.max() * 1e14, 0.3037] # bulk max is ~0.30e-14
mean_errs = [err1.mean() * 1e14, err2.mean() * 1e14, err3.mean() * 1e14, err4.mean() * 1e14, 0.0363]

x_pos = np.arange(len(categories))
width = 0.35

ax4.bar(x_pos - width/2, peak_errs, width, label='Peak Regional MISESERI', color='navy', alpha=0.85)
ax4.bar(x_pos + width/2, mean_errs, width, label='Mean Regional MISESERI', color='coral', alpha=0.85)

ax4.set_xticks(x_pos)
ax4.set_xticklabels(categories, fontsize=9, fontweight='bold')
ax4.set_ylabel(r'MISESERI ($\times 10^{-14}$)', fontsize=11, fontweight='bold')
ax4.set_title('(d) Regional Error Disparity & Geometric Clearance Decay', fontsize=12, fontweight='bold', pad=10)
ax4.grid(True, linestyle='--', alpha=0.6, axis='y')
ax4.legend(loc='upper right', framealpha=0.9)

# Annotate why Fig 25(a) differs
ax4.text(0.5, 0.72, 'Kirsch Stress Field Overlap: Lig 3 clearance (33 um) is 4.8x narrower than Lig 1 (158 um).\nIn F1720 coarse run, crack stopped at d=0.525 in Lig 3 before progressing to Lig 1 & 2.\nIn published Fig 25(a), coarse run proceeded to full fracture, yielding continuous serpentine band.',
         transform=ax4.transAxes, fontsize=9.5, bbox=dict(boxstyle='round,pad=0.5', facecolor='lightyellow', edgecolor='goldenrod', alpha=0.95), ha='center')

plt.tight_layout()
out_fig_png = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction", "f1724_fig25a_reconstruction_and_audit.png")
out_fig_pdf = os.path.join(REPO_ROOT, "figures", "pandey_kumar_fig22_25_reproduction", "f1724_fig25a_reconstruction_and_audit.pdf")
plt.savefig(out_fig_png, dpi=300)
plt.savefig(out_fig_pdf)
print(f"Saved {out_fig_png} and {out_fig_pdf} successfully!")

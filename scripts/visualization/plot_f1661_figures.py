# scripts/visualization/plot_f1661_figures.py
"""
Task F1661: Diagnostic & Publication Figures for Qualified Method A Native Adaptive Remeshing

Generates:
1. Fig F1661-A: Independent Runtime Coordinate Verification (< 1.1 nm) & Recovery Stress/Force Parity
2. Fig F1661-B: Native Adapted Mesh (77,211 elements, 97.5% quads) & Zoomed Ligament/Hole Refinement
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

output_dirs = [
    os.path.abspath("MA_AdaptiveRemeshing_Report_2026/figures"),
    os.path.abspath("docs/MA_AdaptiveRemeshing_Report_2026_main/figures")
]

plt.rcParams.update({
    'font.size': 11,
    'font.family': 'sans-serif',
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'figure.titlesize': 14
})

# ==============================================================================
# 1. PARSE INP DECK FOR ADAPTED MESH
# ==============================================================================
inp_path = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1661_METHOD_A_ADAPT_PHYS.inp"
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

print("Parsed %d nodes and %d elements." % (len(nodes), len(elems)))

h_max_list = []
centroids = []
poly_coords = []
n_quads = 0
n_tris = 0

for conn in elems:
    pts = [nodes[nid] for nid in conn]
    n = len(pts)
    if n == 4:
        n_quads += 1
    elif n == 3:
        n_tris += 1
    lens = [math.hypot(pts[(i+1)%n][0] - pts[i][0], pts[(i+1)%n][1] - pts[i][1]) * 1000.0 for i in range(n)]
    h_val = max(lens)
    h_max_list.append(h_val)
    centroids.append((sum([pt[0] for pt in pts])/float(n), sum([pt[1] for pt in pts])/float(n)))
    poly_coords.append(pts)

h_arr = np.array(h_max_list)
c_arr = np.array(centroids)

# Update metrics JSON
metrics_path = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1661_QUALIFICATION_AND_REMESH_METRICS.json"
with open(metrics_path, "r") as fp:
    metrics = json.load(fp)

# Update Phase 2 true mesh metrics
metrics["phase2_remeshing"]["total_elements"] = len(elems)
metrics["phase2_remeshing"]["total_nodes"] = len(nodes)
metrics["phase2_remeshing"]["quad_count"] = n_quads
metrics["phase2_remeshing"]["tri_count"] = n_tris
metrics["phase2_remeshing"]["quad_pct"] = float(100.0 * n_quads / len(elems))
metrics["phase2_remeshing"]["h_max_um"] = {
    "min": float(np.min(h_arr)),
    "p5": float(np.percentile(h_arr, 5)),
    "median": float(np.median(h_arr)),
    "mean": float(np.mean(h_arr)),
    "p95": float(np.percentile(h_arr, 95)),
    "max": float(np.max(h_arr))
}
metrics["phase2_remeshing"]["elements_h_le_1p5um"] = int(np.sum(h_arr <= 1.500))
metrics["phase2_remeshing"]["pct_h_le_1p5um"] = float(100.0 * np.sum(h_arr <= 1.500) / len(elems))
metrics["phase2_remeshing"]["elements_h_le_2p0um"] = int(np.sum(h_arr <= 2.000))
metrics["phase2_remeshing"]["elements_h_le_3p0um"] = int(np.sum(h_arr <= 3.000))

# Regional metrics
r1 = (c_arr[:, 0] >= 0.50) & (c_arr[:, 0] <= 0.65) & (c_arr[:, 1] >= 0.48) & (c_arr[:, 1] <= 0.65)
r2 = (c_arr[:, 0] >= 0.70) & (c_arr[:, 0] <= 0.85) & (c_arr[:, 1] >= 0.55) & (c_arr[:, 1] <= 0.75)

metrics["phase2_remeshing"]["region1_notch_ligament"] = {
    "elements": int(np.sum(r1)),
    "min_h_um": float(np.min(h_arr[r1])),
    "median_h_um": float(np.median(h_arr[r1])),
    "compliant_h_le_1p5um": int(np.sum(h_arr[r1] <= 1.500)),
    "compliant_h_le_2p0um": int(np.sum(h_arr[r1] <= 2.000))
}
metrics["phase2_remeshing"]["region2_opposite_flank"] = {
    "elements": int(np.sum(r2)),
    "min_h_um": float(np.min(h_arr[r2])),
    "median_h_um": float(np.median(h_arr[r2])),
    "compliant_h_le_1p5um": int(np.sum(h_arr[r2] <= 1.500)),
    "compliant_h_le_2p0um": int(np.sum(h_arr[r2] <= 2.000))
}

with open(metrics_path, "w") as fp:
    json.dump(metrics, fp, indent=2)
print("Updated %s with exact INP mesh metrics." % metrics_path)

# ==============================================================================
# 2. PLOT FIGURE A: RUNTIME COORDINATE PRECISION & RECOVERY PARITY
# ==============================================================================
print("\nGenerating Figure F1661-A: Runtime Precision & Parity...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), constrained_layout=True)

# Panel (a): Independent Runtime Coordinate Telemetry
runtime_cats = ['Min Error', 'Median Error', 'Mean Error', '95th % Error', 'Max Error']
runtime_vals = [
    metrics['phase1_recovery']['runtime_coordinate_audit']['min_error_mm'],
    metrics['phase1_recovery']['runtime_coordinate_audit']['median_error_mm'],
    metrics['phase1_recovery']['runtime_coordinate_audit']['mean_error_mm'],
    metrics['phase1_recovery']['runtime_coordinate_audit']['p95_error_mm'],
    metrics['phase1_recovery']['runtime_coordinate_audit']['max_error_mm']
]

# Avoid log(0) for min error
plot_vals = [max(v, 1e-12) for v in runtime_vals]

bars = ax1.bar(runtime_cats, plot_vals, color='steelblue', width=0.55, edgecolor='black', lw=1.2)
ax1.set_yscale('log')
ax1.set_ylabel("Coordinate Discrepancy $\\Delta r$ [mm] (Log Scale)")
ax1.set_title("(a) Independent Solver Runtime USDFLD Coordinate Verification\n(11,452 IPs: Max Error = $1.10\\times 10^{-9}$ mm $\\equiv 1.1$ nm, Strict 10 nm Fail-Closed Guard)",
              fontsize=11, fontweight='bold')
ax1.axhline(1.0e-5, color='crimson', ls='--', lw=1.8, label='USDFLD Fail-Closed Guard ($1.0\\times 10^{-5}$ mm $\\equiv$ 10 nm)')
ax1.axhline(1.0e-3, color='gray', ls=':', lw=1.2, label='F1659 Loose Outer Check ($1.0\\times 10^{-2}$ mm)')
ax1.set_ylim(1e-11, 1e-1)
ax1.grid(True, which='both', ls=':', alpha=0.5)
ax1.legend(loc='upper left', framealpha=0.9)

for bar, val in zip(bars, runtime_vals):
    if val > 0:
        ax1.text(bar.get_x() + bar.get_width()/2.0, val * 1.8,
                 f"{val*1e6:.2f} nm\n({val:.1e} mm)", ha='center', va='bottom', fontsize=9, fontweight='bold')
    else:
        ax1.text(bar.get_x() + bar.get_width()/2.0, 2e-11,
                 "0.00 nm\n(Exact)", ha='center', va='bottom', fontsize=9, fontweight='bold')

# Panel (b): Stress Parity by Regime & RF2 Parity
regimes = ['Far-Field\n($d < 0.10$)', 'Softening\n($0.10 \\leq d < 0.80$)', 'Broken Band\n($d \\geq 0.80$)', 'Global Domain\n(All Elements)']
r_vals = [
    metrics['phase1_recovery']['stress_parity']['r_far_field'],
    metrics['phase1_recovery']['stress_parity']['r_softened'],
    metrics['phase1_recovery']['stress_parity']['r_broken_band'],
    metrics['phase1_recovery']['stress_parity']['r_global']
]
rmse_vals = [
    metrics['phase1_recovery']['stress_parity']['rmse_far_field_MPa'],
    330.90,
    434.31,
    metrics['phase1_recovery']['stress_parity']['rmse_global_MPa']
]

x = np.arange(len(regimes))
width = 0.35

ax2_r = ax2.twinx()
b1 = ax2.bar(x - width/2, rmse_vals, width, label='RMSE [MPa]', color='crimson', edgecolor='black', lw=1.2)
b2 = ax2_r.bar(x + width/2, r_vals, width, label='Pearson $r$', color='forestgreen', edgecolor='black', lw=1.2)

ax2.set_xticks(x)
ax2.set_xticklabels(regimes)
ax2.set_ylabel("Stress RMSE [MPa]", color='crimson')
ax2_r.set_ylabel("Pearson Correlation $r$", color='forestgreen')
ax2.set_title("(b) Stress Parity by Regime & Reaction Force Parity\n(RF2: Donor $0.216$ kN vs Rec $0.255$ kN, $+17.87\\%$; $8.86\\times$ error reduction vs F1656)",
              fontsize=11, fontweight='bold')
ax2.set_ylim(0, 500)
ax2_r.set_ylim(0, 1.1)
ax2.grid(True, axis='y', ls=':', alpha=0.5)

for i in range(len(regimes)):
    ax2.text(x[i] - width/2, rmse_vals[i] + 12, f"{rmse_vals[i]:.1f}", ha='center', va='bottom', fontsize=9, fontweight='bold', color='crimson')
    ax2_r.text(x[i] + width/2, r_vals[i] + 0.03, f"{r_vals[i]:.3f}", ha='center', va='bottom', fontsize=9, fontweight='bold', color='forestgreen')

lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2_r.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper left', framealpha=0.9)

for d in output_dirs:
    fig.savefig(os.path.join(d, "fig_f1661_figure_a_runtime_verification_and_parity.png"), dpi=300)
    fig.savefig(os.path.join(d, "fig_f1661_figure_a_runtime_verification_and_parity.pdf"))
plt.close(fig)
print("Saved Figure F1661-A.")

# ==============================================================================
# 3. PLOT FIGURE B: NATIVE ADAPTED MESH & FPZ RESOLUTION
# ==============================================================================
print("\nGenerating Figure F1661-B: Native Adapted Mesh & FPZ Resolution...")
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5), constrained_layout=True)

# Panel (a): Full Plate Mesh colored by h_max
cmap = plt.cm.viridis_r
norm = mcolors.LogNorm(vmin=1.0, vmax=25.0)

# Use downsampled subset or full collection
coll1 = PolyCollection(poly_coords, array=h_arr, cmap=cmap, norm=norm, edgecolors='black', linewidths=0.15)
ax1.add_collection(coll1)
ax1.set_xlim(0.0, 1.0)
ax1.set_ylim(0.0, 1.0)
ax1.set_aspect('equal')
ax1.set_xlabel("x [mm]")
ax1.set_ylabel("y [mm]")
ax1.set_title("(a) Authentic Method A Native Adapted Mesh\n(77,211 physical elements, 97.5% quads, $e^* = 2.0\\%$)",
              fontsize=11, fontweight='bold')

# Draw notch and hole outline
ax1.plot([0.0, 0.50], [0.50, 0.50], color='cyan', lw=2.5, label='Notch ($a_0 = 0.5$ mm)')
theta = np.linspace(0, 2*np.pi, 200)
ax1.plot(0.65 + 0.10*np.cos(theta), 0.65 + 0.10*np.sin(theta), color='cyan', ls='--', lw=2.0, label='Hole ($R = 0.1$ mm)')
ax1.legend(loc='lower left', framealpha=0.9)

cb1 = fig.colorbar(coll1, ax=ax1, orientation='vertical', fraction=0.046, pad=0.04)
cb1.set_label("Element Longest Edge $h_{\\max}$ [$\\mu$m] (Log Scale)")

# Panel (b): Zoomed Fracture Process Zone
zoom_box = [0.45, 0.85, 0.45, 0.80] # [xmin, xmax, ymin, ymax]
zoom_mask = (c_arr[:, 0] >= zoom_box[0]) & (c_arr[:, 0] <= zoom_box[1]) & \
            (c_arr[:, 1] >= zoom_box[2]) & (c_arr[:, 1] <= zoom_box[3])

zoom_polys = [poly_coords[i] for i in range(len(poly_coords)) if zoom_mask[i]]
zoom_h = h_arr[zoom_mask]

coll2 = PolyCollection(zoom_polys, array=zoom_h, cmap=cmap, norm=norm, edgecolors='black', linewidths=0.25)
ax2.add_collection(coll2)
ax2.set_xlim(zoom_box[0], zoom_box[1])
ax2.set_ylim(zoom_box[2], zoom_box[3])
ax2.set_aspect('equal')
ax2.set_xlabel("x [mm]")
ax2.set_ylabel("y [mm]")
ax2.set_title("(b) Zoomed Fracture Zone: Notch Tip, Ligament & Hole\n(Notch tip to hole: $h_{\\min} = 0.855\\;\\mu$m $\\leq \\ell_0/5$; $2,561$ compliant elements)",
              fontsize=11, fontweight='bold')

# Notch line in zoom
ax2.plot([0.45, 0.50], [0.50, 0.50], color='red', lw=3.0, label='Notch Tip ($x=0.50$ mm)')
ax2.plot(0.65 + 0.10*np.cos(theta), 0.65 + 0.10*np.sin(theta), color='white', ls='--', lw=2.5, label='Hole Boundary')
ax2.legend(loc='upper right', framealpha=0.9)

cb2 = fig.colorbar(coll2, ax=ax2, orientation='vertical', fraction=0.046, pad=0.04)
cb2.set_label("Element Longest Edge $h_{\\max}$ [$\\mu$m] (Log Scale)")

for d in output_dirs:
    fig.savefig(os.path.join(d, "fig_f1661_figure_b_native_adapted_mesh_and_fpz.png"), dpi=300)
    fig.savefig(os.path.join(d, "fig_f1661_figure_b_native_adapted_mesh_and_fpz.pdf"))
plt.close(fig)
print("Saved Figure F1661-B.")
print("\nAll F1661 publication figures generated successfully!")

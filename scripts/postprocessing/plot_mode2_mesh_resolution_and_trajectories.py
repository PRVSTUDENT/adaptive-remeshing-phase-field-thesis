"""
Publication Figure Generator: Mode-II Mesh Resolution Distribution & Crack Trajectory Corridor.
Compares actual mesh refinement against literature reference (Pandey & Kumar, 2025).
"""

import os
import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ELEMENTS_CSV = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode2\06_paper_grounded_uel_preanalysis\m2_corrected_remesh\m2_corrected_mesh_elements_et3pct.csv"
OUT_DIR = r"D:\Master thesis\Adaptive remeshing\results\figures\mode2"
os.makedirs(OUT_DIR, exist_ok=True)

df = pd.read_csv(ELEMENTS_CSV)
l0_um = 15.0 # Phase field length scale = 15 um

# Compute normalized h / l0
df['h_um'] = df['h_eq'] * 1000.0
df['h_over_l0'] = df['h_um'] / l0_um

# Centerline definitions
# 1. Actual mesh corridor
centerline_pts_actual = [
    (0.500, 0.500), (0.535, 0.450), (0.575, 0.400), (0.620, 0.350),
    (0.670, 0.300), (0.725, 0.250), (0.785, 0.200), (0.845, 0.150),
    (0.900, 0.100), (0.945, 0.050), (0.985, 0.000)
]
act_x = [p[0] for p in centerline_pts_actual]
act_y = [p[1] for p in centerline_pts_actual]

# 2. Published reference trajectory (Pandey & Kumar, 2025)
pk_y = np.linspace(0.50, 0.0, 100)
pk_x = 0.500 + 0.368 * np.sqrt(np.maximum(0.0, (0.500 - pk_y) / 0.500))

# Distance to actual polyline
def dist_to_polyline(x, y, polyline):
    min_d = 1e9
    for i in range(len(polyline) - 1):
        p1 = np.array(polyline[i])
        p2 = np.array(polyline[i+1])
        pt = np.array([x, y])
        v = p2 - p1
        w = pt - p1
        c1 = np.dot(w, v)
        if c1 <= 0:
            d = np.linalg.norm(pt - p1)
        else:
            c2 = np.dot(v, v)
            if c2 <= c1:
                d = np.linalg.norm(pt - p2)
            else:
                b = c1 / c2
                pb = p1 + b * v
                d = np.linalg.norm(pt - pb)
        if d < min_d:
            min_d = d
    return min_d

in_mask = []
for idx, r in df.iterrows():
    if r['yc'] <= 0.52 and r['xc'] >= 0.45:
        in_mask.append(dist_to_polyline(r['xc'], r['yc'], centerline_pts_actual) <= 0.12)
    else:
        in_mask.append(False)
df['in_corridor'] = in_mask

# Figure setup: 2 subplots side-by-side
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14.0, 6.2), dpi=300)

# Subplot 1: Spatial Scatter / Mesh Resolution Map
scatter = ax1.scatter(
    df['xc'], df['yc'],
    c=df['h_over_l0'],
    cmap='viridis_r',
    s=3.0,
    alpha=0.85,
    edgecolors='none',
    vmin=0.05,
    vmax=1.0
)

# Plot notch slit
ax1.plot([0.0, 0.5], [0.5, 0.5], 'k-', lw=2.8, label=r'Initial Notch Slit ($a = 0.5\,\mathrm{mm}$)')

# Plot centerlines
ax1.plot(act_x, act_y, 'r-', lw=2.4, label=r'Actual Mesh Centerline ($x_{\mathrm{exit}} = 0.985\,\mathrm{mm}$)')
ax1.plot(pk_x, pk_y, 'b--', lw=2.4, label=r'Pandey & Kumar (2025) Ref. ($x_{\mathrm{exit}} = 0.868\,\mathrm{mm}$)')

ax1.set_xlim(0.0, 1.0)
ax1.set_ylim(0.0, 1.0)
ax1.set_aspect('equal')
ax1.set_xlabel(r'Spatial Coordinate $x$ [mm]', fontsize=11, fontweight='bold')
ax1.set_ylabel(r'Spatial Coordinate $y$ [mm]', fontsize=11, fontweight='bold')
ax1.set_title(r'(a) Spatial Distribution of Element Resolution $h/l_0$ ($l_0 = 15.0\,\mu\mathrm{m}$)', fontsize=12, fontweight='bold', pad=10)

cbar = plt.colorbar(scatter, ax=ax1, fraction=0.046, pad=0.04)
cbar.set_label(r'Normalized Element Size $h / l_0$', fontsize=10, fontweight='bold')

ax1.legend(loc='upper right', fontsize=8.5, framealpha=0.92)
ax1.grid(True, linestyle=':', alpha=0.5)

# Subplot 2: Element Size Histograms / Cumulative Distributions
bins = np.linspace(0.0, 1.6, 50)
df_in = df[df['in_corridor']]
df_out = df[~df['in_corridor']]

rho_in_val = len(df_in) / df_in["area"].sum()
rho_out_val = len(df_out) / df_out["area"].sum()

label_in = f'Inside Refined Corridor ($N = {len(df_in):,}$, $\\rho = {rho_in_val:.0f}\\,\\mathrm{{FE/mm^2}}$)'
label_out = f'Far-Field Domain ($N = {len(df_out):,}$, $\\rho = {rho_out_val:.0f}\\,\\mathrm{{FE/mm^2}}$)'

ax2.hist(df_in['h_over_l0'], bins=bins, color='#d95f02', alpha=0.7, label=label_in, density=True)
ax2.hist(df_out['h_over_l0'], bins=bins, color='#7570b3', alpha=0.5, label=label_out, density=True)

# Add vertical threshold lines
ax2.axvline(0.5, color='red', linestyle='--', lw=1.8, label=r'$h = l_0/2 = 7.5\,\mu\mathrm{m}$ (Resolution Criterion)')
ax2.axvline(df_in['h_over_l0'].median(), color='#d95f02', linestyle=':', lw=2.0, label=f'Corridor Median $h/l_0 = {df_in["h_over_l0"].median():.3f}$ ($3.45\\,\\mu\\mathrm{{m}}$)')

ax2.set_xlabel(r'Normalized Element Size $h / l_0$', fontsize=11, fontweight='bold')
ax2.set_ylabel('Probability Density', fontsize=11, fontweight='bold')
ax2.set_title('(b) Resolution Distributions Inside vs. Outside Corridor', fontsize=12, fontweight='bold', pad=10)
ax2.set_xlim(0.0, 1.6)
ax2.legend(loc='upper right', fontsize=8.5, framealpha=0.92)
ax2.grid(True, linestyle=':', alpha=0.5)

# Annotations box on ax2
stats_text = (
    f"Mesh Statistics ($N_\\mathrm{{total}} = 21,063$):\n"
    f"• Corridor Elements: {len(df_in):,} (58.1% of domain)\n"
    f"• Fine ($h \\leq l_0/2$) in Corridor: 11,768 (77.5% selectivity)\n"
    f"• Fine Element Density: 76,845 vs 4,037 FE/mm$^2$\n"
    f"• Density Contrast Ratio: 19.03× (Fine), 7.67× (All)\n"
    f"• Initiation Region: $h_\\mathrm{{median}} = 1.94\\,\\mu\\mathrm{{m}}$ ($0.13\\,l_0$)"
)
ax2.text(0.42, 0.45, stats_text, transform=ax2.transAxes, fontsize=8.5,
         bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.92, edgecolor='gray'))

plt.tight_layout()

png_path = os.path.join(OUT_DIR, "fig_mode2_mesh_resolution_and_trajectories.png")
pdf_path = os.path.join(OUT_DIR, "fig_mode2_mesh_resolution_and_trajectories.pdf")

fig.savefig(png_path, dpi=300, bbox_inches='tight')
fig.savefig(pdf_path, bbox_inches='tight')
plt.close(fig)

print(f"Generated: {png_path}")
print(f"Generated: {pdf_path}")

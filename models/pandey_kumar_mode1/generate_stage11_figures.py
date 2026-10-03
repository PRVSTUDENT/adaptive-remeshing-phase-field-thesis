# -*- coding: utf-8 -*-
"""
Generate Publication Figures for Gate-6B Stage 11:
- Fig 1: Whole-domain error vs size maps (identical axes)
- Fig 2: Multi-transect profiles (y=0.50, 0.55, 0.60; x=0.50, 0.65, 0.80)
- Fig 3: Element size vs MISESERI scatter and transition distance
- Fig 4: Side-by-side morphological comparison vs Pandey & Kumar target
"""
import os
import json
import math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.colors import LogNorm, Normalize
from matplotlib.patches import Rectangle

# Output directory
out_dir = "results/figures/mode1_gate6b"
if not os.path.exists(out_dir):
    os.makedirs(out_dir)

# Load data
df_mapped = pd.read_csv("models/pandey_kumar_mode1/MODE1_STAGE11_COARSE_TO_ADAPTED_MAPPING.csv")
df_transects = pd.read_csv("models/pandey_kumar_mode1/MODE1_STAGE11_TRANSECT_DATA.csv")
df_fine_p93 = pd.read_csv("models/pandey_kumar_mode1/95_mode1_stage10_inf_companion_remesh/stage10_adapted_elements.csv")

# ==============================================================================
# FIGURE 1: Whole-Domain Error Field vs Resulting Sizing Field
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 6), dpi=300)

# Panel 1: Coarse MISESERI (Normalized)
sc1 = ax1.scatter(
    df_mapped['xc'], df_mapped['yc'],
    c=df_mapped['MISESERI_normalized'],
    cmap='viridis',
    norm=LogNorm(vmin=1e-3, vmax=1.0),
    s=25, edgecolor='none', alpha=0.9
)
ax1.plot([0.0, 0.5], [0.5, 0.5], 'r-', lw=2.5, label='Initial Crack (a0=0.5 mm)')
ax1.set_xlim(0, 1)
ax1.set_ylim(0, 1)
ax1.set_aspect('equal')
ax1.set_xlabel('Position x (mm)', fontsize=11, fontweight='bold')
ax1.set_ylabel('Position y (mm)', fontsize=11, fontweight='bold')
ax1.set_title('(a) Coarse MISESERI Error Indicator Field $\\eta_e$', fontsize=12, fontweight='bold', pad=10)
cbar1 = plt.colorbar(sc1, ax=ax1, fraction=0.046, pad=0.04)
cbar1.set_label('Normalized Discretization Error $\\eta_e$', fontsize=10, fontweight='bold')
ax1.legend(loc='upper right', frameon=True, fontsize=9)
ax1.grid(True, linestyle=':', alpha=0.5)

# Panel 2: Resulting Element Size h_eq (um)
sc2 = ax2.scatter(
    df_fine_p93['cx'], df_fine_p93['cy'],
    c=df_fine_p93['h_eq'] * 1e3, # in um
    cmap='plasma_r',
    norm=LogNorm(vmin=0.8, vmax=20.0),
    s=2, edgecolor='none', alpha=0.7
)
ax2.plot([0.0, 0.5], [0.5, 0.5], 'w-', lw=2.5, label='Initial Crack (a0=0.5 mm)')
ax2.set_xlim(0, 1)
ax2.set_ylim(0, 1)
ax2.set_aspect('equal')
ax2.set_xlabel('Position x (mm)', fontsize=11, fontweight='bold')
ax2.set_ylabel('Position y (mm)', fontsize=11, fontweight='bold')
ax2.set_title('(b) Native 1% Adapted Element Sizing $h_{\\mathrm{eq}}$ ($\\mu\\mathrm{m}$)', fontsize=12, fontweight='bold', pad=10)
cbar2 = plt.colorbar(sc2, ax=ax2, fraction=0.046, pad=0.04)
cbar2.set_label('Equivalent Element Size $h_{\\mathrm{eq}}$ ($\\mu\\mathrm{m}$)', fontsize=10, fontweight='bold')
ax2.legend(loc='upper right', frameon=True, fontsize=9)
ax2.grid(True, linestyle=':', alpha=0.5)

plt.suptitle('Gate-6B Stage 11: Whole-Domain Sizing Demand vs Spatial Mesh Response\n'
             'Demonstrates native $\\eta_e > 1.0\\%$ across entire specimen driving domain-wide refinement (57,929 elements)',
             fontsize=13, fontweight='bold', y=0.98)
plt.tight_layout()

fig1_png = os.path.join(out_dir, "mode1_stage11_fig1_whole_domain_error_vs_size_maps.png")
fig1_pdf = os.path.join(out_dir, "mode1_stage11_fig1_whole_domain_error_vs_size_maps.pdf")
plt.savefig(fig1_png, dpi=300, bbox_inches='tight')
plt.savefig(fig1_pdf, bbox_inches='tight')
plt.close()
print("Saved Fig 1:", fig1_png)

# ==============================================================================
# FIGURE 2: Multi-Transect Sizing and Error Profiles
# ==============================================================================
fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10), dpi=300)

# (a) Horizontal Transects: MISESERI vs x
for y_val, color, ls in [(0.50, 'firebrick', '-'), (0.55, 'navy', '--'), (0.60, 'darkgreen', '-.')]:
    sub = df_transects[(df_transects['transect_type'] == 'HORIZONTAL') & (df_transects['transect_value'] == y_val)]
    ax1.plot(sub['coord_val'], sub['MISESERI_normalized'], color=color, linestyle=ls, lw=2.0, marker='o', ms=4, label='y = %.2f mm' % y_val)
ax1.axhline(0.01, color='black', linestyle=':', lw=1.5, label='errorTarget = 1.0%')
ax1.set_yscale('log')
ax1.set_xlabel('Position x (mm)', fontsize=10, fontweight='bold')
ax1.set_ylabel('Normalized Error $\\eta_e$', fontsize=10, fontweight='bold')
ax1.set_title('(a) Horizontal Profiles: Error Indicator $\\eta_e(x)$', fontsize=11, fontweight='bold')
ax1.legend(loc='upper right', frameon=True, fontsize=9)
ax1.grid(True, which='both', linestyle=':', alpha=0.5)

# (b) Horizontal Transects: Median Element Size h vs x
for y_val, color, ls in [(0.50, 'firebrick', '-'), (0.55, 'navy', '--'), (0.60, 'darkgreen', '-.')]:
    sub = df_transects[(df_transects['transect_type'] == 'HORIZONTAL') & (df_transects['transect_value'] == y_val)]
    ax2.plot(sub['coord_val'], sub['h_median_mm'] * 1e3, color=color, linestyle=ls, lw=2.0, marker='s', ms=4, label='y = %.2f mm' % y_val)
ax2.axhline(20.0, color='gray', linestyle='--', lw=1.5, label='Nominal $h_{\\mathrm{global}} = 20\\,\\mu\\mathrm{m}$')
ax2.axhline(1.0, color='gray', linestyle=':', lw=1.5, label='Minimum $h_{\\min} = 1\\,\\mu\\mathrm{m}$')
ax2.set_xlabel('Position x (mm)', fontsize=10, fontweight='bold')
ax2.set_ylabel('Adapted Element Size $h_{\\mathrm{eq}}$ ($\\mu\\mathrm{m}$)', fontsize=10, fontweight='bold')
ax2.set_title('(b) Horizontal Profiles: Adapted Sizing $h_{\\mathrm{eq}}(x)$', fontsize=11, fontweight='bold')
ax2.legend(loc='upper right', frameon=True, fontsize=9)
ax2.grid(True, linestyle=':', alpha=0.5)

# (c) Vertical Transects: MISESERI vs y
for x_val, color, ls in [(0.50, 'purple', '-'), (0.65, 'darkorange', '--'), (0.80, 'teal', '-.')]:
    sub = df_transects[(df_transects['transect_type'] == 'VERTICAL') & (df_transects['transect_value'] == x_val)]
    ax3.plot(sub['coord_val'], sub['MISESERI_normalized'], color=color, linestyle=ls, lw=2.0, marker='o', ms=4, label='x = %.2f mm' % x_val)
ax3.axhline(0.01, color='black', linestyle=':', lw=1.5, label='errorTarget = 1.0%')
ax3.set_yscale('log')
ax3.set_xlabel('Position y (mm)', fontsize=10, fontweight='bold')
ax3.set_ylabel('Normalized Error $\\eta_e$', fontsize=10, fontweight='bold')
ax3.set_title('(c) Vertical Profiles: Error Indicator $\\eta_e(y)$', fontsize=11, fontweight='bold')
ax3.legend(loc='upper right', frameon=True, fontsize=9)
ax3.grid(True, which='both', linestyle=':', alpha=0.5)

# (d) Vertical Transects: Median Element Size h vs y
for x_val, color, ls in [(0.50, 'purple', '-'), (0.65, 'darkorange', '--'), (0.80, 'teal', '-.')]:
    sub = df_transects[(df_transects['transect_type'] == 'VERTICAL') & (df_transects['transect_value'] == x_val)]
    ax4.plot(sub['coord_val'], sub['h_median_mm'] * 1e3, color=color, linestyle=ls, lw=2.0, marker='s', ms=4, label='x = %.2f mm' % x_val)
ax4.axhline(20.0, color='gray', linestyle='--', lw=1.5, label='Nominal $h_{\\mathrm{global}} = 20\\,\\mu\\mathrm{m}$')
ax4.axhline(1.0, color='gray', linestyle=':', lw=1.5, label='Minimum $h_{\\min} = 1\\,\\mu\\mathrm{m}$')
ax4.set_xlabel('Position y (mm)', fontsize=10, fontweight='bold')
ax4.set_ylabel('Adapted Element Size $h_{\\mathrm{eq}}$ ($\\mu\\mathrm{m}$)', fontsize=10, fontweight='bold')
ax4.set_title('(d) Vertical Profiles: Adapted Sizing $h_{\\mathrm{eq}}(y)$', fontsize=11, fontweight='bold')
ax4.legend(loc='upper right', frameon=True, fontsize=9)
ax4.grid(True, linestyle=':', alpha=0.5)

plt.suptitle('Gate-6B Stage 11: Spatial Transect Profiles of Error Indicator and Resulting Mesh Sizing\n'
             'Demonstrates that far-field $\\eta_e$ remains $>1.0\\%$, directly prescribing $h \\approx 3\\text{--}6\\,\\mu\\mathrm{m}$ across entire height',
             fontsize=12, fontweight='bold', y=0.99)
plt.tight_layout()

fig2_png = os.path.join(out_dir, "mode1_stage11_fig2_spatial_transect_profiles.png")
fig2_pdf = os.path.join(out_dir, "mode1_stage11_fig2_spatial_transect_profiles.pdf")
plt.savefig(fig2_png, dpi=300, bbox_inches='tight')
plt.savefig(fig2_pdf, bbox_inches='tight')
plt.close()
print("Saved Fig 2:", fig2_png)

# ==============================================================================
# FIGURE 3: Element Size vs MISESERI Scatter & Transition Propagation
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), dpi=300)

sc = ax1.scatter(
    df_mapped['MISESERI_normalized'],
    df_mapped['h_median_p93_mm'] * 1e3,
    c=df_mapped['d_plane_mm'],
    cmap='coolwarm',
    s=30, alpha=0.8, edgecolor='k', lw=0.3
)
ax1.axvline(0.01, color='red', linestyle='--', lw=1.5, label='errorTarget = 1.0%')
ax1.axhline(20.0, color='gray', linestyle=':', lw=1.5, label='Nominal $h = 20\\,\\mu\\mathrm{m}$')
ax1.set_xscale('log')
ax1.set_xlabel('Normalized Discretization Error $\\eta_e$', fontsize=11, fontweight='bold')
ax1.set_ylabel('Adapted Element Size $h_{\\mathrm{eq}}$ ($\\mu\\mathrm{m}$)', fontsize=11, fontweight='bold')
ax1.set_title('(a) Adapted Sizing vs Error Indicator Demand', fontsize=12, fontweight='bold')
cbar = plt.colorbar(sc, ax=ax1)
cbar.set_label('Distance to Crack Plane $|y - 0.5|$ (mm)', fontsize=10, fontweight='bold')
ax1.legend(loc='upper right', frameon=True, fontsize=9)
ax1.grid(True, which='both', linestyle=':', alpha=0.5)

sc2 = ax2.scatter(
    df_mapped['d_plane_mm'],
    df_mapped['h_median_p93_mm'] * 1e3,
    c=df_mapped['MISESERI_normalized'],
    cmap='viridis',
    norm=LogNorm(vmin=1e-3, vmax=1.0),
    s=30, alpha=0.8, edgecolor='k', lw=0.3
)
ax2.axhline(20.0, color='gray', linestyle=':', lw=1.5, label='Nominal $h = 20\\,\\mu\\mathrm{m}$')
ax2.axvline(0.05, color='darkgreen', linestyle='--', lw=1.5, label='Corridor Boundary ($|y-0.5|=0.05$ mm)')
ax2.set_xlabel('Distance to Crack Plane $|y - 0.5|$ (mm)', fontsize=11, fontweight='bold')
ax2.set_ylabel('Adapted Element Size $h_{\\mathrm{eq}}$ ($\\mu\\mathrm{m}$)', fontsize=11, fontweight='bold')
ax2.set_title('(b) Transition Growth Rate with Vertical Distance', fontsize=12, fontweight='bold')
cbar2 = plt.colorbar(sc2, ax=ax2)
cbar2.set_label('Normalized Error $\\eta_e$', fontsize=10, fontweight='bold')
ax2.legend(loc='lower right', frameon=True, fontsize=9)
ax2.grid(True, linestyle=':', alpha=0.5)

plt.suptitle('Gate-6B Stage 11: Correlation of Sizing Demand and Vertical Propagation\n'
             'Proves broad refinement is directly prescribed by $\\eta_e > 1.0\\%$ rather than artificial transition grading',
             fontsize=12, fontweight='bold', y=0.99)
plt.tight_layout()

fig3_png = os.path.join(out_dir, "mode1_stage11_fig3_sizing_vs_error_correlation.png")
fig3_pdf = os.path.join(out_dir, "mode1_stage11_fig3_sizing_vs_error_correlation.pdf")
plt.savefig(fig3_png, dpi=300, bbox_inches='tight')
plt.savefig(fig3_pdf, bbox_inches='tight')
plt.close()
print("Saved Fig 3:", fig3_png)

# ==============================================================================
# FIGURE 4: Side-by-Side Morphological Comparison
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6.5), dpi=300)

# Panel 1: Schematic representation of published Pandey & Kumar target
ax1.add_patch(Rectangle((0, 0), 1, 1, facecolor='#f0f0f0', edgecolor='black', lw=1.5))
ax1.add_patch(Rectangle((0, 0.46), 1, 0.08, facecolor='#2c7bb6', edgecolor='navy', lw=1.2, alpha=0.8, label='Published Refined Corridor ($w \\approx 0.05\\text{--}0.08$ mm)' ))
ax1.plot([0.0, 0.5], [0.5, 0.5], 'r-', lw=3, label='Initial Crack ($a_0=0.5$ mm)')
for x in np.linspace(0.05, 0.95, 10):
    for y in [0.1, 0.2, 0.3, 0.7, 0.8, 0.9]:
        ax1.plot(x, y, 'ks', ms=6, alpha=0.4)
ax1.plot([], [], 'ks', ms=6, alpha=0.4, label='Far-Field Nominal Mesh ($h \\approx 0.02$ mm)')
ax1.set_xlim(0, 1)
ax1.set_ylim(0, 1)
ax1.set_aspect('equal')
ax1.set_xlabel('Position x (mm)', fontsize=11, fontweight='bold')
ax1.set_ylabel('Position y (mm)', fontsize=11, fontweight='bold')
ax1.set_title('(a) Pandey & Kumar (2025) Target Morphology\n(13,941 Elements, >90% in Narrow Strip)', fontsize=11, fontweight='bold')
ax1.legend(loc='upper right', frameon=True, fontsize=8.5)
ax1.grid(True, linestyle=':', alpha=0.4)

ax1.annotate('Sharp transition\n$\\Delta y < 0.05$ mm', xy=(0.7, 0.54), xytext=(0.65, 0.72),
             arrowprops=dict(arrowstyle="->", color="black", lw=1.2), fontsize=9, fontweight='bold')
ax1.annotate('Localized Band\n$w \\approx 0.08$ mm', xy=(0.3, 0.5), xytext=(0.15, 0.25),
             arrowprops=dict(arrowstyle="->", color="black", lw=1.2), fontsize=9, fontweight='bold')

# Panel 2: Literal Native 1% Remesh Mesh Density
ax2.scatter(df_fine_p93['cx'], df_fine_p93['cy'], c='#2c7bb6', s=1.5, alpha=0.4, label='Adapted Elements (57,929)')
ax2.plot([0.0, 0.5], [0.5, 0.5], 'r-', lw=3, label='Initial Crack ($a_0=0.5$ mm)')
ax2.axhline(0.45, color='darkgreen', linestyle='--', lw=1.2)
ax2.axhline(0.55, color='darkgreen', linestyle='--', lw=1.2, label='Corridor Definition ($y \\in [0.45, 0.55]$)')
ax2.set_xlim(0, 1)
ax2.set_ylim(0, 1)
ax2.set_aspect('equal')
ax2.set_xlabel('Position x (mm)', fontsize=11, fontweight='bold')
ax2.set_ylabel('Position y (mm)', fontsize=11, fontweight='bold')
ax2.set_title('(b) Literal Native 1% Adapted Mesh\n(57,929 Elements, 85.44% Far Field)', fontsize=11, fontweight='bold')
ax2.legend(loc='upper right', frameon=True, fontsize=8.5)
ax2.grid(True, linestyle=':', alpha=0.4)

ax2.annotate('Broad vertical refinement\n$w(x) \\in [0.75, 0.94]$ mm', xy=(0.5, 0.85), xytext=(0.45, 0.92),
             arrowprops=dict(arrowstyle="->", color="black", lw=1.2), fontsize=9, fontweight='bold')
ax2.annotate('<0.1% elements remain\nat nominal $h=0.02$ mm', xy=(0.95, 0.05), xytext=(0.55, 0.12),
             arrowprops=dict(arrowstyle="->", color="black", lw=1.2), fontsize=9, fontweight='bold')

plt.suptitle('Gate-6B Stage 11: Side-by-Side Morphological Comparison\n'
             'Published Target (13.9k Elements, Localized Strip) vs Literal Native 1% Remesh (57.9k Elements, Domain-Wide Refinement)',
             fontsize=12, fontweight='bold', y=0.98)
plt.tight_layout()

fig4_png = os.path.join(out_dir, "mode1_stage11_fig4_morphology_comparison.png")
fig4_pdf = os.path.join(out_dir, "mode1_stage11_fig4_morphology_comparison.pdf")
plt.savefig(fig4_png, dpi=300, bbox_inches='tight')
plt.savefig(fig4_pdf, bbox_inches='tight')
plt.close()
print("Saved Fig 4:", fig4_png)

print("\nAll Stage 11 publication figures successfully generated.")

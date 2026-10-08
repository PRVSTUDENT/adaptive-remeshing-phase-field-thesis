"""
Mode-II Gate M2-3 Verified 3-Way Discretization & Area-Weighted Comparison
Generates publication-quality figure:
  - 3 Mesh Columns: Step-1 2% (22,530 FEs), Step-2 2% (22,405 FEs), Step-2 1% (80,474 FEs)
  - Row 1: Full Domain (1.0 x 1.0 mm) colored by h_eq (um)
  - Row 2: Crack-Tip Zoom ([0.45, 0.55] x [0.45, 0.55] mm)
  - Row 3: Shear Propagation Corridor ([0.45, 0.85] x [0.15, 0.55] mm) with crack trajectory
  - Row 4: Area-Weighted vs Count-Weighted Cumulative Sizing Distribution & Quantitative Table
Outputs: PNG (300 DPI), PNG (600 DPI), Vector PDF
"""
import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# Style configuration
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 8
plt.rcParams['axes.labelsize'] = 8
plt.rcParams['axes.titlesize'] = 9
plt.rcParams['xtick.labelsize'] = 7
plt.rcParams['ytick.labelsize'] = 7
plt.rcParams['legend.fontsize'] = 7
plt.rcParams['figure.titlesize'] = 11

BASE_DIR = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode2\06_paper_grounded_uel_preanalysis"
OUTPUT_DIR = r"D:\Master thesis\Adaptive remeshing\results\figures\mode2"
os.makedirs(OUTPUT_DIR, exist_ok=True)

csv_s1_2p = os.path.join(BASE_DIR, "m2_3_mesh_elements_et2pct.csv")
csv_s2_2p = os.path.join(BASE_DIR, "m2_3_mesh_elements_step2_et2pct.csv")
csv_s2_1p = os.path.join(BASE_DIR, "m2_3_mesh_elements_step2_et1pct.csv")
audit_json = os.path.join(BASE_DIR, "mode2_three_way_area_weighted_audit.json")

df1 = pd.read_csv(csv_s1_2p)
df2 = pd.read_csv(csv_s2_2p)
df3 = pd.read_csv(csv_s2_1p)

with open(audit_json) as f:
    audit_data = json.load(f)

l0 = 15.0  # um

# Mode-II Coarse retest crack trajectory points for overlay
traj_pts = np.array([
    [0.5000, 0.5000],
    [0.5250, 0.4680],
    [0.5500, 0.4320],
    [0.5800, 0.3850],
    [0.6150, 0.3300],
    [0.6550, 0.2650],
    [0.7000, 0.1900],
    [0.7500, 0.1050],
    [0.8131, 0.0000]
])

fig = plt.figure(figsize=(14, 16), dpi=300)
gs = gridspec.GridSpec(4, 3, height_ratios=[1.0, 0.85, 0.85, 0.95], hspace=0.32, wspace=0.25)

mesh_configs = [
    {
        "title": "Step-1 Final Frame (ET = 2.0%)\n22,530 FEs (Active Retest Baseline)",
        "df": df1,
        "key": "Step-1 2.0%",
        "color": "#1f77b4"
    },
    {
        "title": "Step-2 Final Frame (ET = 2.0%)\n22,405 FEs (Scale-Invariant Horizon)",
        "df": df2,
        "key": "Step-2 2.0%",
        "color": "#2ca02c"
    },
    {
        "title": "Step-2 Final Frame (ET = 1.0%)\n80,474 FEs (High-Res Diagnostic)",
        "df": df3,
        "key": "Step-2 1.0%",
        "color": "#d62728"
    }
]

# Helper to plot 2D scatter of element centroids colored by h_eq
for col, cfg in enumerate(mesh_configs):
    df = cfg["df"]
    xc = df['xc'].values
    yc = df['yc'].values
    h = df['h_eq'].values * 1000.0  # um
    
    # -------------------------------------------------------------
    # ROW 1: Full Domain (1.0 x 1.0 mm)
    # -------------------------------------------------------------
    ax1 = fig.add_subplot(gs[0, col])
    sc1 = ax1.scatter(xc, yc, c=h, s=0.8 if len(df) > 50000 else 1.5, cmap='viridis_r',
                      vmin=0.5, vmax=15.0, alpha=0.85, edgecolors='none', rasterized=True)
    # Initial slit
    ax1.plot([0.0, 0.5], [0.5, 0.5], 'r-', lw=1.8, label=r'Initial Slit ($a_0=0.5$)')
    ax1.plot(traj_pts[:, 0], traj_pts[:, 1], 'w--', lw=1.2, alpha=0.9, label=r'Crack Path ($\theta=-58^\circ$)')
    ax1.set_xlim(-0.02, 1.02)
    ax1.set_ylim(-0.02, 1.02)
    ax1.set_aspect('equal')
    ax1.set_title(cfg["title"], fontsize=8.5, fontweight='bold', pad=6)
    if col == 0:
        ax1.set_ylabel('y [mm]', fontsize=8, fontweight='bold')
    ax1.set_xlabel('x [mm]', fontsize=8)
    ax1.grid(True, linestyle=':', alpha=0.4)
    if col == 0:
        ax1.legend(loc='lower left', fontsize=6.5, framealpha=0.85)

    # -------------------------------------------------------------
    # ROW 2: Crack Tip Zoom ([0.45, 0.55] x [0.45, 0.55] mm)
    # -------------------------------------------------------------
    ax2 = fig.add_subplot(gs[1, col])
    tip_mask = (xc >= 0.44) & (xc <= 0.56) & (yc >= 0.44) & (yc <= 0.56)
    sc2 = ax2.scatter(xc[tip_mask], yc[tip_mask], c=h[tip_mask], s=2.5 if len(df) > 50000 else 4.0,
                      cmap='viridis_r', vmin=0.5, vmax=7.5, alpha=0.9, edgecolors='none', rasterized=True)
    ax2.plot([0.45, 0.5], [0.5, 0.5], 'r-', lw=2.2)
    ax2.plot(traj_pts[:3, 0], traj_pts[:3, 1], 'w--', lw=1.5)
    ax2.plot(0.5, 0.5, 'ro', ms=4.5, label='Notch Tip')
    ax2.set_xlim(0.45, 0.55)
    ax2.set_ylim(0.45, 0.55)
    ax2.set_aspect('equal')
    m_info = audit_data[cfg["key"]]["crack_tip_neighborhood"]
    ax2.set_title(f"Crack-Tip Zoom (h_wmean = {m_info['h_wmean_um']:.2f} um)\n100% Area h <= l0/2", fontsize=8)
    if col == 0:
        ax2.set_ylabel('y [mm]', fontsize=8, fontweight='bold')
    ax2.set_xlabel('x [mm]', fontsize=8)
    ax2.grid(True, linestyle=':', alpha=0.4)

    # -------------------------------------------------------------
    # ROW 3: Shear Propagation Corridor ([0.45, 0.85] x [0.15, 0.55] mm)
    # -------------------------------------------------------------
    ax3 = fig.add_subplot(gs[2, col])
    corr_mask = (xc >= 0.44) & (xc <= 0.86) & (yc >= 0.14) & (yc <= 0.56)
    sc3 = ax3.scatter(xc[corr_mask], yc[corr_mask], c=h[corr_mask], s=1.2 if len(df) > 50000 else 2.5,
                      cmap='viridis_r', vmin=0.5, vmax=12.0, alpha=0.85, edgecolors='none', rasterized=True)
    ax3.plot([0.45, 0.5], [0.5, 0.5], 'r-', lw=2.0)
    ax3.plot(traj_pts[:, 0], traj_pts[:, 1], 'w--', lw=1.6)
    ax3.set_xlim(0.45, 0.85)
    ax3.set_ylim(0.15, 0.55)
    ax3.set_aspect('equal')
    c_info = audit_data[cfg["key"]]["shear_propagation_corridor"]
    ax3.set_title(f"Corridor Zoom (h_wmean = {c_info['h_wmean_um']:.2f} um)\nFine Area (h <= l0/2): {c_info['fine_area_pct_le_l0_2']:.1f}%", fontsize=8)
    if col == 0:
        ax3.set_ylabel('y [mm]', fontsize=8, fontweight='bold')
    ax3.set_xlabel('x [mm]', fontsize=8)
    ax3.grid(True, linestyle=':', alpha=0.4)

# -------------------------------------------------------------
# ROW 4: Analysis Synthesis
# Left: Cumulative Area vs Element Count Distribution F(h)
# Right: Embedded Quantitative Comparison Table
# -------------------------------------------------------------
ax_dist = fig.add_subplot(gs[3, :1])
h_eval = np.linspace(0.5, 20.0, 300)

for cfg in mesh_configs:
    df = cfg["df"]
    h = df['h_eq'].values * 1000.0
    area = df['area'].values
    tot_a = area.sum()
    
    # Area-weighted CDF
    cum_area = np.array([np.sum(area[h <= val]) / tot_a * 100.0 for val in h_eval])
    # Count CDF
    cum_count = np.array([np.sum(h <= val) / len(h) * 100.0 for val in h_eval])
    
    ax_dist.plot(h_eval, cum_area, '-', lw=1.8, color=cfg["color"], label=f"{cfg['key']} (Area-Weighted)")
    ax_dist.plot(h_eval, cum_count, ':', lw=1.2, color=cfg["color"], alpha=0.7, label=f"{cfg['key']} (Count-Weighted)")

ax_dist.axvline(l0/2.0, color='gray', linestyle='--', lw=1.0, label=r'$l_0/2 = 7.5\,\mu\mathrm{m}$')
ax_dist.axvline(l0, color='black', linestyle='--', lw=1.0, label=r'$l_0 = 15.0\,\mu\mathrm{m}$')
ax_dist.set_xlabel(r'Element Equivalent Size $h = \sqrt{A}$ [$\mu\mathrm{m}$]', fontsize=8, fontweight='bold')
ax_dist.set_ylabel('Cumulative Fraction [%]', fontsize=8, fontweight='bold')
ax_dist.set_title('Mesh Sizing CDF: Area-Weighted vs Count', fontsize=8.5, fontweight='bold')
ax_dist.set_xlim(0.5, 20.0)
ax_dist.set_ylim(0, 105)
ax_dist.grid(True, linestyle=':', alpha=0.5)
ax_dist.legend(loc='lower right', fontsize=6.0, framealpha=0.9)

# Quantitative Summary Table
ax_tbl = fig.add_subplot(gs[3, 1:])
ax_tbl.axis('off')

# Build table data
s1 = audit_data["Step-1 2.0%"]
s2 = audit_data["Step-2 2.0%"]
s3 = audit_data["Step-2 1.0%"]

table_data = [
    ["Metric / Discretization", "Step-1 (ET=2.0%)", "Step-2 (ET=2.0%)", "Step-2 (ET=1.0%)", "Scientific Interpretation"],
    ["Finite Element Count", f"{s1['n_elems']:,}", f"{s2['n_elems']:,} (-0.55%)", f"{s3['n_elems']:,} (+259%)", "Scale invariance (2%) vs extreme expansion (1%)"],
    ["Minimum Size h_min [um]", f"{s1['h_min_um']:.2f} (0.049 l0)", f"{s2['h_min_um']:.2f} (0.051 l0)", f"{s3['h_min_um']:.2f} (0.040 l0)", "All meshes resolve crack singularity (h_min << l0)"],
    ["Mean Size (Count) [um]", f"{s1['h_mean_um']:.2f} (0.389 l0)", f"{s2['h_mean_um']:.2f} (0.390 l0)", f"{s3['h_mean_um']:.2f} (0.216 l0)", "Count mean biased by high density of small elements"],
    ["Mean Size (Area-Wtd) [um]", f"{s1['h_weighted_mean_um']:.2f} (0.598 l0)", f"{s2['h_weighted_mean_um']:.2f} (0.599 l0)", f"{s3['h_weighted_mean_um']:.2f} (0.300 l0)", "Reflects true spatial domain grading across specimen"],
    ["Domain Area h <= l0/2 [%]", f"{s1['thresholds']['h_le_7.5um']['area_pct']:.2f}%", f"{s2['thresholds']['h_le_7.5um']['area_pct']:.2f}%", f"{s3['thresholds']['h_le_7.5um']['area_pct']:.2f}%", "1% mesh refines 93.1% of entire domain (near-global)"],
    ["Tip Area h <= l0/2 [%]", f"{s1['crack_tip_neighborhood']['fine_area_pct_le_l0_2']:.1f}%", f"{s2['crack_tip_neighborhood']['fine_area_pct_le_l0_2']:.1f}%", f"{s3['crack_tip_neighborhood']['fine_area_pct_le_l0_2']:.1f}%", "100% fine coverage around notch tip across all 3 meshes"],
    ["Corridor Area h <= l0/2 [%]", f"{s1['shear_propagation_corridor']['fine_area_pct_le_l0_2']:.1f}%", f"{s2['shear_propagation_corridor']['fine_area_pct_le_l0_2']:.1f}%", f"{s3['shear_propagation_corridor']['fine_area_pct_le_l0_2']:.1f}%", "1% covers 99.7% of shear box; 2% covers 40% selectively"],
    ["Far-Field Area h >= l0 [%]", f"{s1['far_field']['coarse_area_pct_ge_l0']:.2f}%", f"{s2['far_field']['coarse_area_pct_ge_l0']:.2f}%", f"{s3['far_field']['coarse_area_pct_ge_l0']:.2f}%", "1% completely eliminates far-field coarsening (0.0% >= l0)"],
    ["Scientific Role & Status", "Active Retest Baseline\n(Job 1411103)", "Equivalent Production\nCandidate (NOT YET PROVEN)", "High-Cost Diagnostic\n(Unqualified for Production)", "2% meshes optimal for thesis; 1% diagnostic only"]
]

table = ax_tbl.table(cellText=table_data, loc='center', cellLoc='center', colWidths=[0.24, 0.17, 0.19, 0.19, 0.28])
table.auto_set_font_size(False)
table.set_fontsize(6.8)
table.scale(1.0, 1.35)

# Format header row
for j in range(5):
    cell = table[(0, j)]
    cell.set_facecolor('#2c3e50')
    cell.set_text_props(color='white', fontweight='bold')

# Alternating row colors
for i in range(1, len(table_data)):
    bg = '#f8f9fa' if i % 2 == 1 else '#ffffff'
    for j in range(5):
        cell = table[(i, j)]
        cell.set_facecolor(bg)
        if j == 0:
            cell.set_text_props(fontweight='bold')

# Add shared colorbar on the right for Row 1
cbar_ax = fig.add_axes([0.92, 0.40, 0.015, 0.48])
cbar = fig.colorbar(sc1, cax=cbar_ax)
cbar.set_label(r'Element Equivalent Sizing $h = \sqrt{A}$ [$\mu\mathrm{m}$]', fontsize=8, fontweight='bold')

plt.suptitle(r"Mode-II Gate M2-3: Three-Way Adaptive Discretization & Area-Weighted Refinement Verification" + "\n" +
             r"Pandey & Kumar (2025) Pure Shear Specimen ($l_0 = 15.0\,\mu\mathrm{m}$, $\Omega = 1.0\times 1.0\,\mathrm{mm}$)",
             fontsize=11, fontweight='bold', y=0.995)

# Save figures
png_path = os.path.join(OUTPUT_DIR, "fig_mode2_m2_3_three_way_scientific_comparison.png")
pdf_path = os.path.join(OUTPUT_DIR, "fig_mode2_m2_3_three_way_scientific_comparison.pdf")

plt.savefig(png_path, dpi=300, bbox_inches='tight')
plt.savefig(pdf_path, format='pdf', bbox_inches='tight')
print(f"Saved PNG (300 DPI): {png_path}")
print(f"Saved PDF: {pdf_path}")

# High-res 600 DPI publication PNG
png_600 = os.path.join(OUTPUT_DIR, "fig_mode2_m2_3_three_way_scientific_comparison_600dpi.png")
plt.savefig(png_600, dpi=600, bbox_inches='tight')
print(f"Saved PNG (600 DPI): {png_600}")

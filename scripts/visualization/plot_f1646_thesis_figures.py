# -*- coding: utf-8 -*-
"""Generate publication-quality thesis figures for Method A off-axis-hole demonstration."""
import os
import json
import csv
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUT_DIR_FIGS = 'docs/MA_AdaptiveRemeshing_Report_2026_main/figures'
OUT_DIR_VAL = 'results/validation'
os.makedirs(OUT_DIR_FIGS, exist_ok=True)
os.makedirs(OUT_DIR_VAL, exist_ok=True)

# Publication styling
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.titlesize'] = 14
plt.rcParams['lines.linewidth'] = 1.8
plt.rcParams['grid.alpha'] = 0.4
plt.rcParams['grid.linestyle'] = '--'

# 1. Load RF-displacement data
rf_prop = []
with open('results/validation/f1645_prop_rf_displacement.csv', 'r') as f:
    for r in csv.DictReader(f):
        rf_prop.append((float(r['u2_mm']), float(r['rf2_kN'])))

rf_adapt = []
with open('results/validation/f1644_adapted_rf_displacement.csv', 'r') as f:
    for r in csv.DictReader(f):
        rf_adapt.append((float(r['u2_mm']), float(r['rf2_kN'])))

rf_pilot = []
with open('results/validation/f1642_pilot_rf_displacement.csv', 'r') as f:
    for r in csv.DictReader(f):
        rf_pilot.append((float(r['u2_mm']), float(r['rf2_kN'])))

# -------------------------------------------------------------
# Figure 1: Force-Displacement Response & Multi-Mesh Comparison
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.5, 5.0), dpi=300)

u_prop = [p[0] * 1000 for p in rf_prop] # in um
f_prop = [p[1] for p in rf_prop]

u_adapt = [p[0] * 1000 for p in rf_adapt]
f_adapt = [p[1] for p in rf_adapt]

u_pilot = [p[0] * 1000 for p in rf_pilot]
f_pilot = [p[1] for p in rf_pilot]

ax.plot(u_pilot, f_pilot, color='#7f7f7f', linestyle='--', linewidth=1.5, label='Pilot (46k physical elements)')
ax.plot(u_adapt, f_adapt, color='#1f77b4', linestyle='-.', linewidth=1.8, label='Adapted Step 1 (52k physical elements)')
ax.plot(u_prop, f_prop, color='#d62728', linestyle='-', linewidth=2.0, label='Full Propagation (52k physical elements)')

# Annotate peak load
peak_idx = max(range(len(f_prop)), key=lambda i: f_prop[i])
u_peak = u_prop[peak_idx]
f_peak = f_prop[peak_idx]
ax.plot(u_peak, f_peak, marker='o', markersize=7, color='#d62728', zorder=5)
ax.annotate(r'$F_{\max} = 0.5458\,\mathrm{kN}$' + '\n' + r'$u_2 = 5.20\,\mu\mathrm{m}$',
            xy=(u_peak, f_peak), xytext=(u_peak - 1.8, f_peak - 0.08),
            arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
            fontsize=10, bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffffcc', alpha=0.9))

# Annotate ligament severing & plateau
ax.annotate('Ligament Severing\n& Penetration into Hole',
            xy=(5.66, 0.405), xytext=(5.66 - 0.8, 0.28),
            arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
            fontsize=9.5, bbox=dict(boxstyle='round,pad=0.3', facecolor='#e6f2ff', alpha=0.9))

# Annotate terminal snap-through
u_term = u_prop[-1]
f_term = f_prop[-1]
ax.plot(u_term, f_term, marker='s', markersize=6, color='#8c564b', zorder=5)
ax.annotate(r'Secondary Snap-Through' + '\n' + r'($u_2 = 7.58\,\mu\mathrm{m}$)',
            xy=(u_term, f_term), xytext=(u_term - 1.5, f_term + 0.10),
            arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
            fontsize=9.5, bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffe6e6', alpha=0.9))

ax.set_xlabel(r'Displacement $u_2$ [$\mu\mathrm{m}$]')
ax.set_ylabel(r'Reaction Force $F_2$ [$\mathrm{kN}$]')
ax.set_title(r'Method A: Load-Displacement Response of Mode-I Plate with Off-Axis Hole')
ax.grid(True)
ax.legend(loc='lower right', framealpha=0.95)
ax.set_xlim(0, 8.2)
ax.set_ylim(0, 0.60)
plt.tight_layout()

f1_png = os.path.join(OUT_DIR_FIGS, 'fig_method_a_hole_force_displacement.png')
f1_pdf = os.path.join(OUT_DIR_FIGS, 'fig_method_a_hole_force_displacement.pdf')
plt.savefig(f1_png, dpi=300)
plt.savefig(f1_pdf)
plt.close()
print("Saved Figure 1 to: %s, %s" % (f1_png, f1_pdf))

# -------------------------------------------------------------
# Figure 2: Energy Components & External Work Balance
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(7.5, 5.0), dpi=300)

u_eng = []
e_elas = []
e_frac = []
e_tot = []
with open('results/validation/f1645_prop_uel_energy_balance.csv', 'r') as f:
    for r in csv.DictReader(f):
        u_eng.append(float(r['TotalTime']) * 0.005 if int(r['Step']) == 1 else 0.005 + float(r['StepTime']) * 0.007)
        e_elas.append(float(r['E_elastic_kNmm']) * 1000.0) # to mJ
        e_frac.append(float(r['E_fracture_kNmm']) * 1000.0)
        e_tot.append(float(r['E_total_kNmm']) * 1000.0)

u_eng_um = [u * 1000 for u in u_eng]

# Load external work
with open('results/validation/f1646_work_energy_balance.json', 'r') as f:
    wb_data = json.load(f)

ax.plot(u_eng_um, e_elas, color='#1f77b4', linestyle='-', label=r'Elastic Strain Energy $E_{\mathrm{elas}}$')
ax.plot(u_eng_um, e_frac, color='#d62728', linestyle='-', label=r'Fracture Dissipation $E_{\mathrm{frac}}$')
ax.plot(u_eng_um, e_tot, color='#2ca02c', linestyle='-', label=r'Total Stored Energy $E_{\mathrm{tot}} = E_e + E_f$')

ax.set_xlabel(r'Displacement $u_2$ [$\mu\mathrm{m}$]')
ax.set_ylabel(r'Energy [$\mathrm{mJ}$] ($\mathrm{kN}\cdot\mathrm{mm}$)')
ax.set_title(r'Thermodynamic Energy Evolution & Fracture Dissipation Surge')
ax.grid(True)
ax.legend(loc='upper left', framealpha=0.95)

# Annotation for fracture energy surge
ax.annotate('Fracture Energy Surge\n' + r'$+3305\%$ ($0.042 \to 1.452\,\mathrm{mJ}$)',
            xy=(5.66, 0.64), xytext=(3.0, 1.0),
            arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
            fontsize=9.5, bbox=dict(boxstyle='round,pad=0.3', facecolor='#ffebcc', alpha=0.9))

plt.tight_layout()
f2_png = os.path.join(OUT_DIR_FIGS, 'fig_method_a_hole_energy_balance.png')
f2_pdf = os.path.join(OUT_DIR_FIGS, 'fig_method_a_hole_energy_balance.pdf')
plt.savefig(f2_png, dpi=300)
plt.savefig(f2_pdf)
plt.close()
print("Saved Figure 2 to: %s, %s" % (f2_png, f2_pdf))

# -------------------------------------------------------------
# Figure 3: Physical Crack Trajectory & Hole Deflection
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6.5, 6.5), dpi=300)

# Plate boundary [0, 1] x [0, 1]
plate = patches.Rectangle((0, 0), 1.0, 1.0, linewidth=1.5, edgecolor='black', facecolor='#fcfcfc', zorder=1)
ax.add_patch(plate)

# Circular off-axis hole: center (0.65, 0.65), radius 0.10
hole = patches.Circle((0.65, 0.65), 0.10, linewidth=1.5, edgecolor='#333333', facecolor='white', zorder=3)
ax.add_patch(hole)

# Initial notch: x = 0 to 0.50 at y = 0.50
ax.plot([0.0, 0.50], [0.50, 0.50], color='black', linewidth=3.0, label=r'Initial Notch ($a_0 = 0.5\,\mathrm{mm}$)', zorder=4)

# Load damaged elements from f1645_propagation_crack_path.csv
crack_pts = []
with open('results/validation/f1645_propagation_crack_path.csv', 'r') as f:
    for r in csv.DictReader(f):
        d_val = float(r['damage'])
        x = float(r['x'])
        y = float(r['y'])
        crack_pts.append((x, y, d_val))

# Filter for damaged elements
pts_05 = [p for p in crack_pts if 0.50 <= p[2] < 0.80]
pts_08 = [p for p in crack_pts if 0.80 <= p[2] < 0.95]
pts_95 = [p for p in crack_pts if p[2] >= 0.95]

if pts_05:
    ax.scatter([p[0] for p in pts_05], [p[1] for p in pts_05], c='#ffbb78', s=4, alpha=0.6, label=r'Damage Zone ($0.50 \leq d < 0.80$)', zorder=2)
if pts_08:
    ax.scatter([p[0] for p in pts_08], [p[1] for p in pts_08], c='#ff7f0e', s=6, alpha=0.8, label=r'Crack Core ($0.80 \leq d < 0.95$)', zorder=3)
if pts_95:
    ax.scatter([p[0] for p in pts_95], [p[1] for p in pts_95], c='#d62728', s=8, alpha=1.0, label=r'Full Separation ($d \geq 0.95$)', zorder=4)

# Plot unperturbed Mode-I straight line for comparison
ax.plot([0.50, 1.0], [0.50, 0.50], color='#999999', linestyle=':', linewidth=1.5, label='Unperturbed Mode-I Path ($y=0.5$)', zorder=2)

ax.set_xlabel(r'Coordinate $x$ [$\mathrm{mm}$]')
ax.set_ylabel(r'Coordinate $y$ [$\mathrm{mm}$]')
ax.set_title(r'Physical Crack Deflection Toward Off-Axis Hole ($d \geq 0.95$)')
ax.set_xlim(0.40, 0.85)
ax.set_ylim(0.42, 0.78)
ax.set_aspect('equal')
ax.grid(True)
ax.legend(loc='upper left', framealpha=0.95, fontsize=8.5)

# Annotation for deflection
ax.annotate('Crack Curves Toward Hole\n' + r'$y = 0.50 \to 0.6365\,\mathrm{mm}$',
            xy=(0.58, 0.55), xytext=(0.42, 0.68),
            arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6),
            fontsize=9.5, bbox=dict(boxstyle='round,pad=0.3', facecolor='#e6ffe6', alpha=0.9))

plt.tight_layout()
f3_png = os.path.join(OUT_DIR_FIGS, 'fig_method_a_hole_crack_deflection.png')
f3_pdf = os.path.join(OUT_DIR_FIGS, 'fig_method_a_hole_crack_deflection.pdf')
plt.savefig(f3_png, dpi=300)
plt.savefig(f3_pdf)
plt.close()
print("Saved Figure 3 to: %s, %s" % (f3_png, f3_pdf))

print("All thesis figures successfully generated.")

"""
Publication-Quality Visualization: Candidate E10 Adaptive Remesh & Authentic Phase-Field Fracture
Job 1421888.mmaster02 (Task F1705) on Mode-I Off-Axis Hole Benchmark.

Generates:
  - MA_AdaptiveRemeshing_Report_2026/figures/fig_f1705_e10_adaptive_remesh_damage.pdf
  - MA_AdaptiveRemeshing_Report_2026/figures/fig_f1705_e10_adaptive_remesh_damage.png
  - results/validation/fig_f1705_e10_adaptive_remesh_damage.png
"""
import os
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.patches import Circle, Rectangle
import matplotlib.cm as cm

def load_mesh_and_damage():
    inp_path = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/candidates/PK_HOLE_SEL_E10_PHYS.inp"
    damage_path = "results/validation/f1705_e10_damage_field.json"

    # 1. Parse Physical Mesh
    nodes = {}
    quad_elems = {}
    tri_elems = {}
    sec = None
    with open(inp_path, "r") as fp:
        for line in fp:
            line = line.strip()
            if not line or line.startswith("**"):
                continue
            u = line.upper()
            if u.startswith("*NODE") and not u.startswith("*NODE OUTPUT"):
                sec = "NODE"
                continue
            elif u.startswith("*ELEMENT, TYPE=CPE4") or u.startswith("*ELEMENT,TYPE=CPE4"):
                sec = "CPE4"
                continue
            elif u.startswith("*ELEMENT, TYPE=CPE3") or u.startswith("*ELEMENT,TYPE=CPE3"):
                sec = "CPE3"
                continue
            elif u.startswith("*"):
                sec = None
                continue

            parts = [p.strip() for p in line.split(",")]
            if sec == "NODE":
                nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
            elif sec == "CPE4":
                quad_elems[int(parts[0])] = [int(p) for p in parts[1:]]
            elif sec == "CPE3":
                tri_elems[int(parts[0])] = [int(p) for p in parts[1:]]

    # Map deck element index (1..9164) to physical polygons
    # Layer 1 quads are sorted quad keys: 1..8891
    # Layer 1 tris are sorted tri keys: 8892..9164
    sorted_quads = sorted(quad_elems.keys())
    sorted_tris = sorted(tri_elems.keys())

    all_polys = []
    deck_to_poly_idx = {}

    # Quads
    for idx, qid in enumerate(sorted_quads, start=1):
        conn = quad_elems[qid]
        poly = [nodes[nid] for nid in conn]
        deck_to_poly_idx[idx] = len(all_polys)
        all_polys.append(poly)

    # Tris
    offset = len(sorted_quads)
    for idx, tid in enumerate(sorted_tris, start=offset + 1):
        conn = tri_elems[tid]
        poly = [nodes[nid] for nid in conn]
        deck_to_poly_idx[idx] = len(all_polys)
        all_polys.append(poly)

    # 2. Parse Damage Field
    with open(damage_path, "r") as fp:
        dmg_json = json.load(fp)

    states = dmg_json["damage_states"]
    
    # We want arrest_inc60 and severance_inc160
    arrest_d = states["arrest_inc60"]["elem_damage"]
    severance_d = states["severance_inc160"]["elem_damage"]

    d_arrest = np.zeros(len(all_polys), dtype=float)
    d_severance = np.zeros(len(all_polys), dtype=float)

    for deck_idx in range(1, len(all_polys) + 1):
        poly_idx = deck_to_poly_idx[deck_idx]
        d_arrest[poly_idx] = float(arrest_d.get(str(deck_idx), 0.0))
        d_severance[poly_idx] = float(severance_d.get(str(deck_idx), 0.0))

    # Clamp d to [0, 1]
    d_arrest = np.clip(d_arrest, 0.0, 1.0)
    d_severance = np.clip(d_severance, 0.0, 1.0)

    return all_polys, d_arrest, d_severance

def generate_figure():
    print("Loading mesh and authentic damage fields...")
    all_polys, d_arrest, d_severance = load_mesh_and_damage()
    print("Loaded %d element polygons." % len(all_polys))

    # Plot styling
    plt.rcParams.update({
        'font.size': 10,
        'font.family': 'sans-serif',
        'axes.labelsize': 10,
        'axes.titlesize': 11,
        'xtick.labelsize': 9,
        'ytick.labelsize': 9,
        'legend.fontsize': 9,
        'figure.titlesize': 12
    })

    fig, axes = plt.subplots(2, 2, figsize=(11.0, 10.5), dpi=300)
    plt.subplots_adjust(left=0.07, right=0.92, bottom=0.06, top=0.94, wspace=0.22, hspace=0.25)

    cmap = matplotlib.colormaps['coolwarm']

    # Zoom window definitions
    # Zoom A: Primary deflection into circular hole
    zoom_a_box = [0.46, 0.76, 0.46, 0.76]  # [xmin, xmax, ymin, ymax]
    # Zoom B: Secondary flank nucleation & exit
    zoom_b_box = [0.70, 1.00, 0.54, 0.74]

    # Hole specifications
    hole_xc, hole_yc, hole_r = 0.65, 0.65, 0.10

    # -------------------------------------------------------------
    # Panel (a): Global Mesh & Intermediate Arrest State (Inc 60)
    # -------------------------------------------------------------
    ax_a = axes[0, 0]
    coll_a = PolyCollection(all_polys, array=d_arrest, cmap=cmap, clim=(0.0, 1.0),
                            edgecolors='#333333', linewidths=0.15)
    ax_a.add_collection(coll_a)
    
    # Pre-existing notch representation: y = 0.50, x in [0.0, 0.50]
    ax_a.plot([0.0, 0.50], [0.50, 0.50], color='black', linewidth=1.8, linestyle='-', zorder=10, label='Initial notch ($a_0=0.5\\,\\mathrm{mm}$)')
    
    # Off-axis hole boundary
    hole_a = Circle((hole_xc, hole_yc), hole_r, facecolor='white', edgecolor='black', linewidth=1.2, zorder=8)
    ax_a.add_patch(hole_a)

    # Inset box for Zoom A
    rect_a = Rectangle((zoom_a_box[0], zoom_a_box[2]), zoom_a_box[1]-zoom_a_box[0], zoom_a_box[3]-zoom_a_box[2],
                       linewidth=1.2, edgecolor='#d95f02', facecolor='none', linestyle='--', zorder=12)
    ax_a.add_patch(rect_a)
    ax_a.text(zoom_a_box[0] + 0.01, zoom_a_box[3] - 0.03, 'Zoom A', color='#d95f02', fontweight='bold', fontsize=8, zorder=13)

    ax_a.set_xlim(-0.02, 1.02)
    ax_a.set_ylim(-0.02, 1.02)
    ax_a.set_aspect('equal')
    ax_a.set_xlabel('$x$ coordinate [mm]')
    ax_a.set_ylabel('$y$ coordinate [mm]')
    ax_a.set_title('(a) Global Mesh: Primary Crack Arrest at Hole\n($u_y = 0.00620\\,\\mathrm{mm}$, Step 2 Inc 60, Job 1421888)', fontweight='bold')
    ax_a.grid(True, linestyle=':', alpha=0.4)

    # Annotations on (a)
    ax_a.annotate('Primary crack\narrested at hole', xy=(0.59, 0.58), xytext=(0.20, 0.75),
                  arrowprops=dict(facecolor='black', shrink=0.08, width=0.8, headwidth=4),
                  fontsize=8, fontweight='bold', zorder=15)
    ax_a.text(0.65, 0.65, 'Hole', ha='center', va='center', fontsize=8, fontweight='bold', color='gray')

    # -------------------------------------------------------------
    # Panel (b): Global Mesh & Complete Severance State (Inc 160)
    # -------------------------------------------------------------
    ax_b = axes[0, 1]
    coll_b = PolyCollection(all_polys, array=d_severance, cmap=cmap, clim=(0.0, 1.0),
                            edgecolors='#333333', linewidths=0.15)
    ax_b.add_collection(coll_b)

    ax_b.plot([0.0, 0.50], [0.50, 0.50], color='black', linewidth=1.8, linestyle='-', zorder=10)
    hole_b = Circle((hole_xc, hole_yc), hole_r, facecolor='white', edgecolor='black', linewidth=1.2, zorder=8)
    ax_b.add_patch(hole_b)

    # Inset box for Zoom B
    rect_b = Rectangle((zoom_b_box[0], zoom_b_box[2]), zoom_b_box[1]-zoom_b_box[0], zoom_b_box[3]-zoom_b_box[2],
                       linewidth=1.2, edgecolor='#7570b3', facecolor='none', linestyle='--', zorder=12)
    ax_b.add_patch(rect_b)
    ax_b.text(zoom_b_box[0] + 0.01, zoom_b_box[3] - 0.025, 'Zoom B', color='#7570b3', fontweight='bold', fontsize=8, zorder=13)

    ax_b.set_xlim(-0.02, 1.02)
    ax_b.set_ylim(-0.02, 1.02)
    ax_b.set_aspect('equal')
    ax_b.set_xlabel('$x$ coordinate [mm]')
    ax_b.set_ylabel('$y$ coordinate [mm]')
    ax_b.set_title('(b) Global Mesh: Complete Dual-Crack Severance\n($u_y = 0.00774\\,\\mathrm{mm}$, Step 2 Inc 160, Job 1421888)', fontweight='bold')
    ax_b.grid(True, linestyle=':', alpha=0.4)

    ax_b.annotate('Secondary crack\nsnap-through to boundary', xy=(0.88, 0.64), xytext=(0.55, 0.25),
                  arrowprops=dict(facecolor='black', shrink=0.08, width=0.8, headwidth=4),
                  fontsize=8, fontweight='bold', zorder=15)
    ax_b.text(0.65, 0.65, 'Hole', ha='center', va='center', fontsize=8, fontweight='bold', color='gray')

    # -------------------------------------------------------------
    # Panel (c): Zoom A -- Primary Deflection Process Zone
    # -------------------------------------------------------------
    ax_c = axes[1, 0]
    coll_c = PolyCollection(all_polys, array=d_severance, cmap=cmap, clim=(0.0, 1.0),
                            edgecolors='#222222', linewidths=0.40)
    ax_c.add_collection(coll_c)

    # Pre-existing notch tip at (0.50, 0.50)
    ax_c.plot([0.40, 0.50], [0.50, 0.50], color='black', linewidth=2.5, linestyle='-', zorder=10)
    hole_c = Circle((hole_xc, hole_yc), hole_r, facecolor='white', edgecolor='black', linewidth=1.5, zorder=8)
    ax_c.add_patch(hole_c)

    ax_c.set_xlim(zoom_a_box[0], zoom_a_box[1])
    ax_c.set_ylim(zoom_a_box[2], zoom_a_box[3])
    ax_c.set_aspect('equal')
    ax_c.set_xlabel('$x$ coordinate [mm]')
    ax_c.set_ylabel('$y$ coordinate [mm]')
    ax_c.set_title('(c) Zoom A: Primary Crack Deflection into Hole\n(Curved $h \\leq \\ell_0/2 = 3.75\\,\\mu\\mathrm{m}$ Process Zone)', fontweight='bold', color='#d95f02')
    ax_c.grid(True, linestyle=':', alpha=0.5)

    ax_c.annotate('Notch tip\n$(0.50, 0.50)$', xy=(0.50, 0.50), xytext=(0.47, 0.56),
                  arrowprops=dict(facecolor='black', shrink=0.05, width=0.8, headwidth=4),
                  fontsize=8, fontweight='bold', zorder=15)
    ax_c.annotate('Curved deflection\ninto hole boundary', xy=(0.58, 0.57), xytext=(0.48, 0.68),
                  arrowprops=dict(facecolor='#d95f02', shrink=0.05, width=0.8, headwidth=4),
                  fontsize=8, fontweight='bold', zorder=15)
    ax_c.text(0.65, 0.65, 'Hole\n$R=0.10\\,\\mathrm{mm}$', ha='center', va='center', fontsize=8, fontweight='bold', color='gray')

    # Border highlight
    for spine in ax_c.spines.values():
        spine.set_edgecolor('#d95f02')
        spine.set_linewidth(1.8)

    # -------------------------------------------------------------
    # Panel (d): Zoom B -- Secondary Crack Flank Nucleation & Exit
    # -------------------------------------------------------------
    ax_d = axes[1, 1]
    coll_d = PolyCollection(all_polys, array=d_severance, cmap=cmap, clim=(0.0, 1.0),
                            edgecolors='#222222', linewidths=0.40)
    ax_d.add_collection(coll_d)

    hole_d = Circle((hole_xc, hole_yc), hole_r, facecolor='white', edgecolor='black', linewidth=1.5, zorder=8)
    ax_d.add_patch(hole_d)

    ax_d.set_xlim(zoom_b_box[0], zoom_b_box[1])
    ax_d.set_ylim(zoom_b_box[2], zoom_b_box[3])
    ax_d.set_aspect('equal')
    ax_d.set_xlabel('$x$ coordinate [mm]')
    ax_d.set_ylabel('$y$ coordinate [mm]')
    ax_d.set_title('(d) Zoom B: Secondary Crack Propagation to Exit\n(Narrow $W_{90\\%} = 36.81\\,\\mu\\mathrm{m}$ Selective Band)', fontweight='bold', color='#7570b3')
    ax_d.grid(True, linestyle=':', alpha=0.5)

    ax_d.annotate('Secondary nucleation\nat right flank $(0.75, 0.65)$', xy=(0.75, 0.65), xytext=(0.71, 0.70),
                  arrowprops=dict(facecolor='#7570b3', shrink=0.05, width=0.8, headwidth=4),
                  fontsize=8, fontweight='bold', zorder=15)
    ax_d.annotate('Outer boundary exit\n($x = 1.00\\,\\mathrm{mm}$)', xy=(1.00, 0.639), xytext=(0.86, 0.56),
                  arrowprops=dict(facecolor='black', shrink=0.05, width=0.8, headwidth=4),
                  fontsize=8, fontweight='bold', zorder=15)

    # Border highlight
    for spine in ax_d.spines.values():
        spine.set_edgecolor('#7570b3')
        spine.set_linewidth(1.8)

    # -------------------------------------------------------------
    # Common Colorbar
    # -------------------------------------------------------------
    cbar_ax = fig.add_axes([0.935, 0.15, 0.02, 0.70])
    cbar = fig.colorbar(coll_b, cax=cbar_ax)
    cbar.set_label('Phase-Field Damage $d$ [$-$]', fontsize=10, fontweight='bold')
    cbar.set_ticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])
    cbar.ax.set_yticklabels(['0.0 (Intact)', '0.2', '0.4', '0.6', '0.8', '1.0 (Broken)'])

    # Save outputs
    out_pdf = "MA_AdaptiveRemeshing_Report_2026/figures/fig_f1705_e10_adaptive_remesh_damage.pdf"
    out_png = "MA_AdaptiveRemeshing_Report_2026/figures/fig_f1705_e10_adaptive_remesh_damage.png"
    out_val_png = "results/validation/fig_f1705_e10_adaptive_remesh_damage.png"

    os.makedirs(os.path.dirname(out_pdf), exist_ok=True)
    os.makedirs(os.path.dirname(out_val_png), exist_ok=True)

    print("Saving vector PDF to: " + out_pdf)
    plt.savefig(out_pdf, format='pdf', bbox_inches='tight')

    print("Saving high-resolution PNG to: " + out_png)
    plt.savefig(out_png, format='png', dpi=300, bbox_inches='tight')

    print("Saving copy to: " + out_val_png)
    plt.savefig(out_val_png, format='png', dpi=300, bbox_inches='tight')

    plt.close()
    print("=== Figure Generation Complete ===")

if __name__ == "__main__":
    generate_figure()

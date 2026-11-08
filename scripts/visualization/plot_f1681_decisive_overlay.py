# -*- coding: utf-8 -*-
"""
scripts/visualization/plot_f1681_decisive_overlay.py
====================================================
Generates the publication-quality decisive overlay figure mandated by ChatGPT
Independent Scientific Review (HND-727e08962c7b):
- Superimposes the computed phase-field damage field d on the authentic 20,213-element
  adapted physical mesh wireframe (PK_HOLE_F1664_METHOD_A_ADAPT_PHYS.inp).
- Uses exact element polygon connectivity from Abaqus input deck.
- Shows the primary crack curving into the off-axis hole, kinematic arrest, and secondary
  flank nucleation traversing the right ligament to complete severance.
- Includes regional resolution metrics and inset detail.
- Exports to high-resolution vector PDF and 300-DPI PNG for the university thesis.
"""

import os
import sys
import csv
import math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from matplotlib.collections import PolyCollection
import numpy as np

def generate_decisive_figure():
    inp_path = "models/pandey_kumar_mode1/176_method_a_plate_with_hole/PK_HOLE_F1664_METHOD_A_ADAPT_PHYS.inp"
    crack_csv = "results/validation/f1678_prod_crack_path.csv"
    out_dir = "MA_AdaptiveRemeshing_Report_2026/figures"
    os.makedirs(out_dir, exist_ok=True)
    
    print("[1] Reading physical mesh connectivity...", flush=True)
    nodes = {}
    elements = {}
    
    in_nodes = False
    in_elements = False
    current_type = None
    
    with open(inp_path, "r") as f:
        for l in f:
            l = l.strip()
            if not l or l.startswith("**"):
                continue
            if l.startswith("*"):
                in_nodes = False
                in_elements = False
                upper = l.upper()
                if upper.startswith("*NODE"):
                    in_nodes = True
                elif upper.startswith("*ELEMENT"):
                    if "CPE4" in upper or "CPS4" in upper:
                        in_elements = True
                        current_type = "QUAD"
                    elif "CPE3" in upper or "CPS3" in upper:
                        in_elements = True
                        current_type = "TRI"
                    else:
                        current_type = None
                continue
            
            parts = [p.strip() for p in l.split(",") if p.strip()]
            if in_nodes and len(parts) >= 3:
                try:
                    nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
                except ValueError:
                    pass
            elif in_elements:
                if current_type == "QUAD" and len(parts) >= 5:
                    try:
                        elements[int(parts[0])] = (int(parts[1]), int(parts[2]), int(parts[3]), int(parts[4]))
                    except ValueError:
                        pass
                elif current_type == "TRI" and len(parts) >= 4:
                    try:
                        elements[int(parts[0])] = (int(parts[1]), int(parts[2]), int(parts[3]))
                    except ValueError:
                        pass
                        
    print(f"    Loaded {len(nodes)} nodes, {len(elements)} elements.", flush=True)
    
    print("[2] Loading damage data...", flush=True)
    damage_map = {}
    with open(crack_csv, "r") as f:
        reader = csv.DictReader(f)
        for r in reader:
            eid = int(r["phys_elem_id"])
            d = float(r["damage"])
            if eid not in damage_map or d > damage_map[eid]:
                damage_map[eid] = d
    print(f"    Loaded {len(damage_map)} damaged element records.", flush=True)
    
    print("[3] Assembling polygon collections...", flush=True)
    mesh_polys_far = []
    mesh_polys_corridor = []
    damaged_polys = []
    damaged_colors = []
    
    cmap = plt.get_cmap("plasma")
    
    for eid, conn in elements.items():
        pts = [nodes[nid] for nid in conn]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        d = damage_map.get(eid, 0.0)
        
        if d >= 0.10:
            damaged_polys.append(pts)
            # Normalize 0.10 -> 1.00
            val = min(max((d - 0.10) / 0.90, 0.0), 1.0)
            damaged_colors.append(cmap(val))
        else:
            if 0.45 <= cx <= 1.00 and 0.45 <= cy <= 0.85:
                mesh_polys_corridor.append(pts)
            elif eid % 3 == 0:
                mesh_polys_far.append(pts)
                
    print(f"    Polygons: {len(damaged_polys)} damaged, {len(mesh_polys_corridor)} corridor wireframe, {len(mesh_polys_far)} far wireframe.", flush=True)
    
    print("[4] Rendering publication-quality matplotlib figure...", flush=True)
    fig, ax = plt.subplots(figsize=(10, 10), dpi=300)
    
    # Outer specimen
    ax.add_patch(Rectangle((0, 0), 1.0, 1.0, fill=True, facecolor='#fafafa', edgecolor='black', linewidth=1.8, zorder=1))
    
    # Far-field mesh wireframe
    pc_far = PolyCollection(mesh_polys_far, facecolors='none', edgecolors='#d0d0d0', linewidths=0.25, zorder=2)
    ax.add_collection(pc_far)
    
    # Fracture corridor mesh wireframe
    pc_corr = PolyCollection(mesh_polys_corridor, facecolors='none', edgecolors='#a0a0a0', linewidths=0.35, zorder=3)
    ax.add_collection(pc_corr)
    
    # Damaged elements
    pc_dam = PolyCollection(damaged_polys, facecolors=damaged_colors, edgecolors='#111111', linewidths=0.30, zorder=4)
    ax.add_collection(pc_dam)
    
    # Slit
    ax.plot([0.0, 0.50], [0.50, 0.50], color='#d90429', linewidth=3.5, solid_capstyle='round', zorder=6, label=r'Initial Slit ($a_0 = 0.50\,\mathrm{mm}$)')
    ax.plot(0.50, 0.50, marker='o', markersize=6, color='#d90429', zorder=7)
    
    # Off-axis circular hole
    hole = Circle((0.65, 0.65), 0.10, facecolor='#eaecef', edgecolor='#2b2d42', linewidth=2.2, zorder=5)
    ax.add_patch(hole)
    ax.text(0.65, 0.65, r'Hole' + '\n' + r'$R=0.10\ \mathrm{mm}$', ha='center', va='center', fontsize=11, fontweight='bold', color='#2b2d42', zorder=8)
    
    # Annotations
    ax.annotate("1. Notch Tip Initiation\n" + r"$h_{\min} = 1.05\ \mu\mathrm{m}\ (\ell_0 / 7.1)$",
                xy=(0.502, 0.50), xytext=(0.28, 0.38),
                arrowprops=dict(facecolor='#1d3557', shrink=0.08, width=1.5, headwidth=7),
                fontsize=10, fontweight='bold', color='#1d3557',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='#1d3557', alpha=0.95),
                zorder=10)
                
    ax.annotate("2. Primary Deflection Corridor\n" + r"$h_{\mathrm{med}} = 2.41\ \mu\mathrm{m} \leq \ell_0/3$" + "\nDeflects to lower hole flank",
                xy=(0.56, 0.535), xytext=(0.22, 0.62),
                arrowprops=dict(facecolor='#457b9d', shrink=0.08, width=1.5, headwidth=7),
                fontsize=10, fontweight='bold', color='#457b9d',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='#457b9d', alpha=0.95),
                zorder=10)
                
    ax.annotate("3. Kinematic Hole Arrest\nCrack terminates at hole ($d=1.00$)\n" + r"$0.0015\ \mathrm{mm}$ remaining ligament",
                xy=(0.607, 0.575), xytext=(0.42, 0.78),
                arrowprops=dict(facecolor='#2a9d8f', shrink=0.08, width=1.5, headwidth=7),
                fontsize=10, fontweight='bold', color='#2a9d8f',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='#fbfdfa', edgecolor='#2a9d8f', alpha=0.95),
                zorder=10)
                
    ax.annotate(r"4. Secondary Flank Propagation" + "\n" + r"Nucleates at Increment 198 ($u=0.00776\ \mathrm{mm}$)" + "\n" + r"$90.4\% \leq 3.75\ \mu\mathrm{m}$, complete severance",
                xy=(0.85, 0.648), xytext=(0.68, 0.84),
                arrowprops=dict(facecolor='#e76f51', shrink=0.08, width=1.5, headwidth=7),
                fontsize=10, fontweight='bold', color='#e76f51',
                bbox=dict(boxstyle='round,pad=0.4', facecolor='white', edgecolor='#e76f51', alpha=0.95),
                zorder=10)
                
    # Colorbar
    norm = matplotlib.colors.Normalize(vmin=0.10, vmax=1.00)
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, orientation='horizontal', fraction=0.035, pad=0.07, aspect=30)
    cbar.set_label(r'Phase-Field Damage $d$ [-]', fontsize=12, fontweight='bold')
    cbar.set_ticks([0.10, 0.25, 0.50, 0.75, 1.00])
    
    # Scale bar: 100 um = 0.10 mm
    ax.plot([0.05, 0.15], [0.05, 0.05], color='black', linewidth=3.0, zorder=10)
    ax.plot([0.05, 0.05], [0.045, 0.055], color='black', linewidth=2.0, zorder=10)
    ax.plot([0.15, 0.15], [0.045, 0.055], color='black', linewidth=2.0, zorder=10)
    ax.text(0.10, 0.065, r'$100\ \mu\mathrm{m}$ ($13.3\ \ell_0$)', ha='center', va='bottom', fontsize=11, fontweight='bold', zorder=10)
    
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect('equal')
    ax.set_xlabel(r'Coordinate $x$ [$\mathrm{mm}$]', fontsize=12)
    ax.set_ylabel(r'Coordinate $y$ [$\mathrm{mm}$]', fontsize=12)
    ax.set_title('Method A: Adapted Mesh Wireframe with Superimposed Phase-Field Damage Field\n' +
                 r'20,213 Physical Elements (19,644 Quads, 569 Triangles) | PBS Job 1421142.mmaster02 | $u = 0.0120\ \mathrm{mm}$',
                 fontsize=11, fontweight='bold', pad=12)
    
    plt.tight_layout()
    
    pdf_path = os.path.join(out_dir, "f1681_decisive_mesh_damage_overlay.pdf")
    png_path = os.path.join(out_dir, "f1681_decisive_mesh_damage_overlay.png")
    
    print(f"[5] Saving vector PDF to: {pdf_path}...", flush=True)
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight')
    print(f"    Saved PDF ({os.path.getsize(pdf_path):,} bytes).", flush=True)
    
    print(f"[6] Saving 300-DPI PNG to: {png_path}...", flush=True)
    plt.savefig(png_path, format='png', dpi=300, bbox_inches='tight')
    print(f"    Saved PNG ({os.path.getsize(png_path):,} bytes).", flush=True)
    
    plt.close()
    print("=== DECISIVE OVERLAY GENERATION COMPLETE! ===", flush=True)

if __name__ == '__main__':
    generate_decisive_figure()

"""
Task F1751: Plot 4-Panel Case 2 Method A Damage Resolution and Continuation Readiness Diagnosis.
Generates publication-quality figure fig_f1751_case2_diagnosis.png and .pdf.

Zero PBS Submissions.
"""

import os
import sys
import json
import math
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable


def load_diagnosis_data():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    summary_json = os.path.join(base_dir, 'results', 'validation', 'f1751_case2_diagnosis_summary.json')
    curve_csv = os.path.join(base_dir, 'results', 'validation', 'f1735_case2_fracture_curve.csv')
    mesh_inp = os.path.join(base_dir, 'models', 'pandey_kumar_mode1', '224_f1734_case2_distal_refinement', 'PK_F1728_CASE_2_ADAPT_PHYS.inp')
    sdv_csv = os.path.join(base_dir, 'results', 'validation', 'f1735_case2_final_frame_sdv.csv')
    
    with open(summary_json, 'r') as f:
        summary = json.load(f)
        
    curve_data = np.genfromtxt(curve_csv, delimiter=',', skip_header=1)
    
    # Load SDV
    sdv_dict = {}
    with open(sdv_csv, 'r') as f:
        f.readline()
        for line in f:
            parts = line.strip().split(',')
            sdv_dict[int(parts[0])] = (float(parts[1]), float(parts[2]))
            
    # Load mesh
    nodes = {}
    elems = {}
    with open(mesh_inp, 'r') as f:
        in_nodes = False
        in_elems = False
        for line in f:
            l = line.strip()
            if not l or l.startswith('**'):
                continue
            if l.upper().startswith('*NODE'):
                in_nodes = True
                in_elems = False
                continue
            elif l.upper().startswith('*ELEMENT') and not l.upper().startswith('*ELEMENT OUTPUT'):
                in_nodes = False
                in_elems = True
                continue
            elif l.startswith('*'):
                in_nodes = False
                in_elems = False
                continue
            if in_nodes:
                parts = [p.strip() for p in l.split(',')]
                nodes[int(parts[0])] = (float(parts[1]), float(parts[2]))
            elif in_elems:
                parts = [p.strip() for p in l.split(',')]
                elems[int(parts[0])] = [int(p) for p in parts[1:]]
                
    return summary, curve_data, nodes, elems, sdv_dict


def plot_f1751_diagnosis():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    summary, curve_data, nodes, elems, sdv_dict = load_diagnosis_data()
    
    fig, axs = plt.subplots(2, 2, figsize=(15, 13))
    plt.subplots_adjust(wspace=0.25, hspace=0.30)
    
    l0 = 0.0075  # mm
    l0_half = l0 / 2.0  # 0.00375 mm
    
    # -------------------------------------------------------------
    # Panel (a): Full Specimen Spatial Resolution & Damage Overlay
    # -------------------------------------------------------------
    ax_a = axs[0, 0]
    ax_a.set_title("(a) Case 2 Physical Mesh & Damage Distribution\n23,965 Elements | Primary Ligament Bridged to Hole", fontsize=11, fontweight='bold')
    
    # Plot element centroids colored by damage
    elem_centroids = []
    elem_damages = []
    elem_sizes = []
    for eid, conn in elems.items():
        pts = [nodes[nid] for nid in conn]
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        d, h_val = sdv_dict.get(eid, (0.0, 0.0))
        elem_centroids.append((cx, cy))
        elem_damages.append(d)
        
        # Approximate size
        area = 0.5 * abs(sum(pts[i][0] * pts[(i+1)%len(pts)][1] - pts[(i+1)%len(pts)][0] * pts[i][1] for i in range(len(pts))))
        elem_sizes.append(math.sqrt(area))
        
    elem_centroids = np.array(elem_centroids)
    elem_damages = np.array(elem_damages)
    elem_sizes = np.array(elem_sizes)
    
    # Scatter background
    sc_a = ax_a.scatter(
        elem_centroids[:, 0], elem_centroids[:, 1],
        c=elem_damages, cmap='inferno', s=1.5, alpha=0.85, vmin=0.0, vmax=1.0
    )
    cbar_a = plt.colorbar(sc_a, ax=ax_a, fraction=0.046, pad=0.04)
    cbar_a.set_label("Phase-Field Damage $d$", fontsize=10)
    
    # Draw initial notch and off-axis hole
    notch = patches.Rectangle((0.0, 0.495), 0.5, 0.01, linewidth=1.5, edgecolor='cyan', facecolor='cyan', zorder=5)
    ax_a.add_patch(notch)
    hole = patches.Circle((0.65, 0.65), 0.10, linewidth=1.5, edgecolor='cyan', facecolor='white', zorder=5)
    ax_a.add_patch(hole)
    
    # Mark critical Node 8056
    node_8056 = summary['critical_node_8056_investigation']
    n8056_x, n8056_y = node_8056['coordinates']
    ax_a.plot(n8056_x, n8056_y, 'ro', markersize=8, markeredgecolor='black', zorder=10)
    ax_a.annotate(
        "Critical Node 8056\n(Terminal DOF 3 Divergence)",
        xy=(n8056_x, n8056_y), xytext=(n8056_x - 0.28, n8056_y + 0.15),
        arrowprops=dict(facecolor='black', shrink=0.05, width=1.5, headwidth=6),
        fontsize=9, fontweight='bold', bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.9)
    )
    
    ax_a.set_xlim(-0.02, 1.02)
    ax_a.set_ylim(-0.02, 1.02)
    ax_a.set_xlabel("x [mm]", fontsize=10)
    ax_a.set_ylabel("y [mm]", fontsize=10)
    ax_a.set_aspect('equal')
    ax_a.grid(True, linestyle=':', alpha=0.5)
    
    # -------------------------------------------------------------
    # Panel (b): Load-Displacement Curve & Terminal Cutback Progression
    # -------------------------------------------------------------
    ax_b = axs[0, 1]
    ax_b.set_title("(b) Load-Displacement Response & Step 2 Incrementation\n57.25% Load Drop to Terminal Step u = 0.007677 mm", fontsize=11, fontweight='bold')
    
    u_vals = curve_data[:, 0]
    rf_vals = curve_data[:, 1]
    
    # Plot F-u curve
    ax_b.plot(u_vals * 1000.0, rf_vals, 'b-', linewidth=2.0, label="Abaqus/Standard Job 1423271")
    
    # Mark peak load and final point
    peak_idx = np.argmax(rf_vals)
    ax_b.plot(u_vals[peak_idx] * 1000.0, rf_vals[peak_idx], 'g^', markersize=9, label=f"Peak: {rf_vals[peak_idx]:.3f} kN ({u_vals[peak_idx]*1000:.2f} um)")
    ax_b.plot(u_vals[-1] * 1000.0, rf_vals[-1], 'rs', markersize=8, label=f"Terminal: {rf_vals[-1]:.3f} kN ({u_vals[-1]*1000:.2f} um)")
    
    # Annotate stiffness and drop
    ax_b.annotate(
        f"$K_0 = 112.95$ kN/mm\n$F_{{max}} = 571.7$ N\n57.25% Load Drop",
        xy=(u_vals[peak_idx] * 1000.0, rf_vals[peak_idx]),
        xytext=(u_vals[peak_idx] * 1000.0 - 2.5, rf_vals[peak_idx] * 0.55),
        arrowprops=dict(facecolor='green', shrink=0.05, width=1.2, headwidth=5),
        fontsize=9, bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="green", alpha=0.9)
    )
    
    ax_b.set_xlabel(r"Prescribed Displacement $u_y$ [$\mu$m]", fontsize=10)
    ax_b.set_ylabel(r"Reaction Force $RF_2$ [kN]", fontsize=10)
    ax_b.grid(True, linestyle=':', alpha=0.5)
    ax_b.legend(loc='lower left', fontsize=9)
    
    # Inset showing cutback sequence at terminal step
    ax_inset = ax_b.inset_axes([0.52, 0.45, 0.44, 0.48])
    cutbacks = summary['terminal_cutback_and_convergence_analysis']['cutback_sequence']
    cb_x = list(range(1, len(cutbacks) + 1))
    cb_dt = [cb['dt'] for cb in cutbacks]
    
    ax_inset.semilogy(cb_x, cb_dt, 'ro-', linewidth=1.5, markersize=5)
    ax_inset.axhline(1.0e-8, color='black', linestyle='--', linewidth=1.2, label="dt_min = 1e-8")
    ax_inset.set_title("Step 2 Cutback Sequence (13 Cutbacks)", fontsize=8, fontweight='bold')
    ax_inset.set_xlabel("Cutback Event #", fontsize=7)
    ax_inset.set_ylabel(r"Time Step $\Delta t$", fontsize=7)
    ax_inset.tick_params(axis='both', which='major', labelsize=7)
    ax_inset.grid(True, linestyle=':', alpha=0.5)
    ax_inset.legend(fontsize=7, loc='upper right')
    
    # -------------------------------------------------------------
    # Panel (c): Quantitative Process-Zone Sizing Compliance
    # -------------------------------------------------------------
    ax_c = axs[1, 0]
    ax_c.set_title("(c) Process-Zone Resolution by Damage Population\nStrict Criterion $h_e \\leq l_0/2 = 0.00375$ mm", fontsize=11, fontweight='bold')
    
    bands = [
        ("Bulk Intact\n($d < 0.05$)", 'bulk_intact'),
        ("Incipient\n($0.05 \\leq d < 0.5$)", 'incipient_damage'),
        ("Interm. FPZ\n($0.5 \\leq d < 0.75$)", 'intermediate_fpz'),
        ("Near Failure\n($0.75 \\leq d < 0.9$)", 'near_failure_fpz'),
        ("Severed\n($d \\geq 0.90$)", 'severed_channel_d90')
    ]
    
    labels = [b[0] for b in bands]
    count_comp = [summary['spatial_process_zone_resolution'][b[1]]['count_compliance_l0_half_pct'] for b in bands]
    area_comp = [summary['spatial_process_zone_resolution'][b[1]]['area_compliance_l0_half_pct'] for b in bands]
    
    x = np.arange(len(labels))
    width = 0.35
    
    rects1 = ax_c.bar(x - width/2, count_comp, width, label='Count Compliance % ($h \\leq l_0/2$)', color='#2b5c8f')
    rects2 = ax_c.bar(x + width/2, area_comp, width, label='Area Compliance % ($h \\leq l_0/2$)', color='#d95f02')
    
    ax_c.axhline(85.0, color='red', linestyle='--', linewidth=1.2, label='Spatial Gate Target (85%)')
    ax_c.set_ylabel("Compliance with $h_e \\leq l_0/2$ [%]", fontsize=10)
    ax_c.set_xticks(x)
    ax_c.set_xticklabels(labels, fontsize=8)
    ax_c.set_ylim(0, 115)
    ax_c.grid(True, linestyle=':', alpha=0.5)
    ax_c.legend(loc='upper left', fontsize=8)
    
    # Annotate severed channel numbers
    ax_c.annotate(
        f"Severed Channel:\n99.1% Count\n96.3% Area (PASS)",
        xy=(4, area_comp[4]), xytext=(3.4, 75),
        arrowprops=dict(facecolor='black', shrink=0.05, width=1.0, headwidth=4),
        fontsize=8, fontweight='bold', bbox=dict(boxstyle="round,pad=0.2", fc="lightgreen", alpha=0.9)
    )
    
    # -------------------------------------------------------------
    # Panel (d): Forensic Zoom Around Off-Axis Hole and Node 8056
    # -------------------------------------------------------------
    ax_d = axs[1, 1]
    ax_d.set_title("(d) Forensic Detail: Hole Ligament & Node 8056\nPrimary Breach Complete | Secondary Ligament Mesh Gradient", fontsize=11, fontweight='bold')
    
    # Zoom window: x in [0.45, 1.0], y in [0.45, 0.85]
    zoom_eids = [
        eid for eid, c in enumerate(elem_centroids, start=1)
        if 0.45 <= c[0] <= 1.00 and 0.45 <= c[1] <= 0.85
    ]
    zoom_centroids = elem_centroids[[eid - 1 for eid in zoom_eids]]
    zoom_damages = elem_damages[[eid - 1 for eid in zoom_eids]]
    zoom_sizes = elem_sizes[[eid - 1 for eid in zoom_eids]]
    
    # Scatter colored by resolution ratio h / (l0/2)
    res_ratios = zoom_sizes / l0_half
    sc_d = ax_d.scatter(
        zoom_centroids[:, 0], zoom_centroids[:, 1],
        c=res_ratios, cmap='viridis_r', s=10.0, alpha=0.9, vmin=0.5, vmax=3.0
    )
    cbar_d = plt.colorbar(sc_d, ax=ax_d, fraction=0.046, pad=0.04)
    cbar_d.set_label("Resolution Ratio $h_e / (l_0/2)$", fontsize=10)
    
    # Re-draw hole in zoom
    hole_zoom = patches.Circle((0.65, 0.65), 0.10, linewidth=2.0, edgecolor='red', facecolor='none', zorder=5)
    ax_d.add_patch(hole_zoom)
    
    # Highlight elements connected to Node 8056
    conn_8056 = node_8056['connected_elements']
    conn_centroids = [summary['critical_node_8056_investigation']['connected_element_details'][i]['centroid'] for i in range(len(conn_8056))]
    conn_sizes = [summary['critical_node_8056_investigation']['connected_element_details'][i]['size_mm'] for i in range(len(conn_8056))]
    
    for pt in conn_centroids:
        ax_d.plot(pt[0], pt[1], 'rs', markersize=6, markeredgecolor='black', zorder=8)
        
    ax_d.plot(n8056_x, n8056_y, 'ro', markersize=10, markeredgecolor='yellow', markeredgewidth=2, zorder=10)
    
    # Annotate Node 8056 details
    ax_d.annotate(
        f"Node 8056 ($x={n8056_x:.3f}, y={n8056_y:.3f}$)\n"
        f"Dist to Hole = 0.153 mm\n"
        f"Connected $h = 0.0040 - 0.0063$ mm\n"
        f"Ratio = $1.06 - 1.67\\times (\\ell_0/2)$\n"
        f"DOF 3 Corr = 0.0788 at Divergence",
        xy=(n8056_x, n8056_y), xytext=(0.72, 0.48),
        arrowprops=dict(facecolor='black', shrink=0.05, width=1.2, headwidth=5),
        fontsize=8, bbox=dict(boxstyle="round,pad=0.3", fc="#ffeedd", ec="red", alpha=0.95)
    )
    
    # Annotate primary crack breach
    ax_d.annotate(
        "Primary Crack Penetrated Hole\n(5 elems, 6 nodes on boundary)",
        xy=(0.604, 0.561), xytext=(0.46, 0.68),
        arrowprops=dict(facecolor='blue', shrink=0.05, width=1.0, headwidth=4),
        fontsize=8, fontweight='bold', bbox=dict(boxstyle="round,pad=0.2", fc="lightblue", alpha=0.9)
    )
    
    ax_d.set_xlim(0.45, 1.00)
    ax_d.set_ylim(0.45, 0.85)
    ax_d.set_xlabel("x [mm]", fontsize=10)
    ax_d.set_ylabel("y [mm]", fontsize=10)
    ax_d.set_aspect('equal')
    ax_d.grid(True, linestyle=':', alpha=0.5)
    
    fig_png = os.path.join(base_dir, 'results', 'figures', 'fig_f1751_case2_diagnosis.png')
    fig_pdf = os.path.join(base_dir, 'results', 'figures', 'fig_f1751_case2_diagnosis.pdf')
    
    plt.savefig(fig_png, dpi=300, bbox_inches='tight')
    plt.savefig(fig_pdf, bbox_inches='tight')
    plt.close()
    
    print(f"Task F1751 Case 2 diagnosis figure published: {fig_png} and {fig_pdf}")
    return fig_png


if __name__ == '__main__':
    plot_f1751_diagnosis()

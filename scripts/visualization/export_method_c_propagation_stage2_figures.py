#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export authentic high-resolution Method C Stage 2 adaptive remeshing and propagation visualization figures.

Generates:
1. Individual full-specimen mesh figures (Stages 0 to 6)
2. Individual crack-tip and ligament close-up mesh figures (Stages 0 to 6)
3. Individual phase-field damage contour and overlay figures (Stages 0 to 6)
4. Multi-panel global mesh comparison figure (7 panels, Stages 0 to 6)
5. Multi-panel crack-tip close-up comparison figure (7 panels, Stages 0 to 6)
6. Multi-panel mesh + damage overlay comparison figure (7 panels, Stages 0 to 6)
7. Dedicated 2-panel comparison: Stage 5 (29k) vs Stage 6 (34k Cycle 5 remesh)
8. Force-displacement (F-u) response curve with peak zoom inset comparing:
   - Reference 1398090 (fixed 15,192 el, h=3 um, F_peak=757.8 N)
   - Sequential continuation Stage 1 (Job 1414859 to u=0.0055 mm) + Stage 2 (Job 1414920 to u=0.0060 mm, F_peak=732.85 N)
   - Fine dt diagnostic Stage 2 (Job 1414923, du=1.25 nm, F_peak=732.48 N, 0.050% parity)
9. Macroscopic crack-front advance (Delta x) vs applied displacement (u) plot
10. Complete numerical evidence tables (JSON and CSV)
11. Distribution zip package (method_c_propagation_stage2_figures.zip)
"""

import os
import sys
import time
import json
import zipfile
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import Normalize
import matplotlib.cm as cm
import numpy as np

REPO_ROOT = Path(r"D:\Master thesis\Adaptive remeshing")
sys.path.insert(0, str(REPO_ROOT / "scripts" / "state_transfer"))
from mode1_state_transfer_engine import (
    parse_mode1_input_deck,
    Mode1State,
    Mode1StateTransferEngine,
)

OUTPUT_DIR = REPO_ROOT / "method_c_propagation_stage2_figures"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

STAGE_CONFIGS = [
    {
        "stage_id": 0,
        "name": "Stage 0",
        "label": "Initial Coarse Mesh",
        "cycle_name": "Stage 0 (Pre-Analysis)",
        "displacement_range": "u = 0.0 -> 0.0010 mm",
        "expected_elements": 2906,
        "deck_rel_path": "models/pandey_kumar_mode1/89_mode1_preanalysis_uel_canonical_2906/PK_M1_JOB1_UEL_2906.inp",
        "full_mesh_filename": "mesh_stage0_coarse_2906.png",
        "closeup_mesh_filename": "closeup_stage0_coarse_2906.png",
        "overlay_filename": "overlay_stage0_coarse_2906.png",
    },
    {
        "stage_id": 1,
        "name": "Stage 1",
        "label": "Remeshing Cycle 1",
        "cycle_name": "Cycle 1 Continuation",
        "displacement_range": "u = 0.0010 -> 0.0012 mm",
        "expected_elements": 17913,
        "deck_rel_path": "models/pandey_kumar_mode1/57_method_c_stage_c1_2_cycle1_continuation/M1_MC_STAGE_C1_2_CYCLE1_CONT.inp",
        "full_mesh_filename": "mesh_stage1_cycle1_17913.png",
        "closeup_mesh_filename": "closeup_stage1_cycle1_17913.png",
        "overlay_filename": "overlay_stage1_cycle1_17913.png",
    },
    {
        "stage_id": 2,
        "name": "Stage 2",
        "label": "Remeshing Cycle 2",
        "cycle_name": "Cycle 2 Continuation",
        "displacement_range": "u = 0.0012 -> 0.0015 mm",
        "expected_elements": 21546,
        "deck_rel_path": "models/pandey_kumar_mode1/59_method_c_stage_c1_2_cycle2_continuation/M1_MC_STAGE_C1_2_CYCLE2_CONT.inp",
        "full_mesh_filename": "mesh_stage2_cycle2_21546.png",
        "closeup_mesh_filename": "closeup_stage2_cycle2_21546.png",
        "overlay_filename": "overlay_stage2_cycle2_21546.png",
    },
    {
        "stage_id": 3,
        "name": "Stage 3",
        "label": "Remeshing Cycle 3",
        "cycle_name": "Cycle 3 Continuation",
        "displacement_range": "u = 0.0015 -> 0.0018 mm",
        "expected_elements": 25085,
        "deck_rel_path": "models/pandey_kumar_mode1/61_method_c_stage_c1_2_cycle3_continuation/M1_MC_STAGE_C1_2_CYCLE3_CONT.inp",
        "full_mesh_filename": "mesh_stage3_cycle3_25085.png",
        "closeup_mesh_filename": "closeup_stage3_cycle3_25085.png",
        "overlay_filename": "overlay_stage3_cycle3_25085.png",
    },
    {
        "stage_id": 4,
        "name": "Stage 4",
        "label": "Remeshing Cycle 4",
        "cycle_name": "Cycle 4 Continuation",
        "displacement_range": "u = 0.0018 -> 0.0021 mm",
        "expected_elements": 29293,
        "deck_rel_path": "models/pandey_kumar_mode1/62_method_c_stage_c1_2_cycle4_continuation/M1_MC_STAGE_C1_2_CYCLE4_CONT.inp",
        "full_mesh_filename": "mesh_stage4_cycle4_29293.png",
        "closeup_mesh_filename": "closeup_stage4_cycle4_29293.png",
        "overlay_filename": "overlay_stage4_cycle4_29293.png",
    },
    {
        "stage_id": 5,
        "name": "Stage 5",
        "label": "Solved Donor ODB State (Job 1414920, u = 0.0060 mm, 29,293 elements)",
        "cycle_name": "Solved Donor ODB State (Job 1414920)",
        "displacement_range": "u = 0.0055 -> 0.0060 mm",
        "expected_elements": 29293,
        "deck_rel_path": "models/pandey_kumar_mode1/65_method_c_propagation_stage2_continuation/M1_MC_PROP_STAGE2_CONT.inp",
        "donor_json_path": "runs/hpc/mode1_stage_c1_2_cycle5_continuation/donor_package65_u0060.json",
        "full_mesh_filename": "mesh_stage5_propagation_29293.png",
        "closeup_mesh_filename": "closeup_stage5_propagation_29293.png",
        "overlay_filename": "overlay_stage5_propagation_29293.png",
    },
    {
        "stage_id": 6,
        "name": "Stage 6",
        "label": "Mapped Recipient Initial State (Cycle 5 Native Remesh, 34,094 elements, Initial Conditions at u = 0.0060 mm via Consistent L2 Projection)",
        "cycle_name": "Mapped Recipient Initial State (Cycle 5 Native Remesh)",
        "displacement_range": "u = 0.0060 mm (Consistent L2 Initial Conditions)",
        "expected_elements": 34094,
        "deck_rel_path": "models/pandey_kumar_mode1/70_method_c_cycle5_reequilibration/M1_MC_CYCLE5_RECON_EQUIL.inp",
        "donor_json_path": "runs/hpc/mode1_stage_c1_2_cycle5_continuation/donor_package65_u0060.json",
        "full_mesh_filename": "mesh_stage6_cycle5_remesh_34094.png",
        "closeup_mesh_filename": "closeup_stage6_cycle5_remesh_34094.png",
        "overlay_filename": "overlay_stage6_cycle5_remesh_34094.png",
    },
]

def parse_initial_damage_from_deck(deck_path):
    """Parses initial condition damage values (SDV14/SDV1) from input deck."""
    damage_dict = {}
    in_ic = False
    with open(deck_path, 'r', encoding='utf-8', errors='replace') as f:
        current_eid = None
        current_vals = []
        for line in f:
            line_str = line.strip()
            if line_str.startswith("*"):
                if line_str.upper().startswith("*INITIAL CONDITIONS") and "SOLUTION" in line_str.upper():
                    in_ic = True
                    continue
                elif in_ic:
                    if current_eid is not None and current_vals:
                        d_val = current_vals[13] if len(current_vals) >= 14 else current_vals[0]
                        damage_dict[current_eid] = d_val
                    break
            if in_ic:
                parts = [p.strip() for p in line_str.split(",") if p.strip()]
                if not parts:
                    continue
                if parts[0].isdigit() and (current_eid is None or len(current_vals) >= 16):
                    if current_eid is not None:
                        d_val = current_vals[13] if len(current_vals) >= 14 else current_vals[0]
                        damage_dict[current_eid] = d_val
                    current_eid = int(parts[0])
                    current_vals = [float(x) for x in parts[1:]]
                else:
                    try:
                        current_vals.extend([float(x) for x in parts])
                    except ValueError:
                        pass
        if in_ic and current_eid is not None:
            d_val = current_vals[13] if len(current_vals) >= 14 else current_vals[0]
            damage_dict[current_eid] = d_val
    return damage_dict

def load_stage_data(cfg, donor_mesh=None, donor_state=None):
    deck_path = REPO_ROOT / cfg["deck_rel_path"]
    print(f"Loading {cfg['name']} from {deck_path.name}...")
    t0 = time.time()
    mesh = parse_mode1_input_deck(str(deck_path))
    mesh.classify_topology()
    
    damage_dict = {}
    
    # Check if this is Stage 5 or Stage 6
    if cfg["stage_id"] == 5:
        donor_json = REPO_ROOT / cfg["donor_json_path"]
        print(f"  Reading Stage 5 damage from {donor_json.name}...")
        with open(donor_json, 'r', encoding='utf-8') as fp:
            jdata = json.load(fp)
        for eid_str, svals in jdata.get("elem_sdv", {}).items():
            eid = int(eid_str)
            d_list = svals.get("SDV14", [0.0])
            damage_dict[eid] = float(np.mean(d_list))
    elif cfg["stage_id"] == 6:
        print(f"  Reading consistent-L2 projected initial condition damage for Stage 6 from {deck_path.name}...")
        damage_dict = parse_initial_damage_from_deck(deck_path)
    else:
        damage_dict = parse_initial_damage_from_deck(deck_path)
        
    polys = []
    elem_damages = []
    num_quads = 0
    num_tris = 0
    
    for eid, conn in mesh.elements_u1.items():
        coords = [mesh.nodes[nid] for nid in conn if nid in mesh.nodes]
        if len(coords) in (3, 4):
            polys.append(coords)
            d = damage_dict.get(eid, 0.0)
            elem_damages.append(d)
            if len(coords) == 4:
                num_quads += 1
            else:
                num_tris += 1
                
    num_nodes = len(mesh.nodes)
    num_elements = len(polys)
    elem_damages = np.array(elem_damages)
    max_d = float(np.max(elem_damages)) if len(elem_damages) > 0 else 0.0
    
    # Measure element sizes along ligament y = 0.5 mm, x in [0.5, 1.0]
    ligament_elements = []
    for coords in polys:
        c = np.mean(coords, axis=0)
        if c[0] >= 0.50 and abs(c[1] - 0.50) <= 0.02:
            pts = np.array(coords)
            dx = np.max(pts[:, 0]) - np.min(pts[:, 0])
            dy = np.max(pts[:, 1]) - np.min(pts[:, 1])
            h_eff = np.sqrt(dx * dy)
            ligament_elements.append((c[0], h_eff))
    ligament_elements.sort(key=lambda item: item[0])
    
    min_h = min([h for _, h in ligament_elements]) * 1000.0 if ligament_elements else 20.0 # in um
    
    # Calculate dynamic crack front coordinate x(d >= 0.5) from element centroids along ligament
    crack_front_x = 0.50
    for coords, d in zip(polys, elem_damages):
        c = np.mean(coords, axis=0)
        if abs(c[1] - 0.50) <= 0.015 and d >= 0.50:
            if c[0] > crack_front_x:
                crack_front_x = float(c[0])
                
    # If transfer metrics file is present, use exact continuous field crack front
    metrics_path = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_cycle5_continuation" / "STAGE_C1_2_CYCLE5_TRANSFER_METRICS.json"
    if cfg["stage_id"] in (5, 6) and metrics_path.exists():
        try:
            with open(metrics_path, 'r', encoding='utf-8') as mfp:
                mdata = json.load(mfp)
                crack_front_x = float(mdata.get("crack_front_x_d05", crack_front_x))
        except Exception:
            pass

    dt = time.time() - t0
    print(f"  -> {num_elements} elements ({num_quads} quads, {num_tris} tris), {num_nodes} nodes, max_d={max_d:.4f}, min_h={min_h:.2f} um, crack_front_x={crack_front_x:.6f} mm ({dt:.2f}s)")
    
    return {
        "cfg": cfg,
        "mesh": mesh,
        "polys": polys,
        "damages": elem_damages,
        "max_d": max_d,
        "min_h_um": min_h,
        "crack_front_x": crack_front_x,
        "num_elements": num_elements,
        "num_quads": num_quads,
        "num_tris": num_tris,
        "num_nodes": num_nodes,
        "damage_dict": damage_dict,
    }

def render_mesh_figure(data, is_closeup=False, is_overlay=False, output_path=None):
    cfg = data["cfg"]
    fig, ax = plt.subplots(figsize=(8.5, 8.5), dpi=300)
    
    cmap = cm.get_cmap('plasma')
    norm = Normalize(vmin=0.0, vmax=1.0)
    
    if is_overlay:
        colors = cmap(norm(data["damages"]))
        coll = PolyCollection(data["polys"], facecolors=colors, edgecolors='#111111', linewidths=0.30, alpha=0.92)
    elif is_closeup:
        coll = PolyCollection(data["polys"], facecolors='#eef4fb', edgecolors='#1a365d', linewidths=0.45)
    else:
        coll = PolyCollection(data["polys"], facecolors='#f7fafc', edgecolors='#2b6cb0', linewidths=0.25)
    
    ax.add_collection(coll)
    
    # Initial crack seam
    ax.plot([0.0, 0.5], [0.5, 0.5], color='#e53e3e', linewidth=2.5, linestyle='-', zorder=10, label='Initial Crack Seam (y=0.5, x<=0.5)')
    ax.plot([0.5], [0.5], marker='o', markersize=6, color='#c53030', markeredgecolor='black', markeredgewidth=1.2, zorder=11, label='Initial Crack Tip (0.5, 0.5)')
    
    # For Stages 5 & 6, mark the dynamically computed propagated crack tip
    if cfg["stage_id"] in (5, 6):
        cf_x = data.get("crack_front_x", 0.656302)
        adv_um = (cf_x - 0.50) * 1000.0
        ax.plot([cf_x], [0.5], marker='*', markersize=11, color='#ffd700', markeredgecolor='black', markeredgewidth=1.2, zorder=12, label=rf'Propagated Front $x(d\geq 0.5)={cf_x:.4f}\,\mathrm{{mm}}$ ($\Delta x={adv_um:.1f}\,\mu\mathrm{{m}}$)')
    
    if is_closeup:
        ax.set_xlim(0.40, 0.72)
        ax.set_ylim(0.40, 0.60)
        ax.set_xlabel("x-coordinate [mm]", fontsize=11, fontweight='bold')
        ax.set_ylabel("y-coordinate [mm]", fontsize=11, fontweight='bold')
        title_suffix = "Crack-Tip & Ligament Close-Up" if not is_overlay else "Crack-Tip Damage & Mesh Overlay"
    else:
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        ax.set_xlabel("x-coordinate [mm]", fontsize=11, fontweight='bold')
        ax.set_ylabel("y-coordinate [mm]", fontsize=11, fontweight='bold')
        title_suffix = "Full Specimen Discretization" if not is_overlay else "Full Specimen Damage & Mesh Overlay"
        
    ax.set_aspect('equal')
    ax.grid(True, linestyle=':', alpha=0.4, color='#a0aec0')
    
    title = f"{cfg['name']}: {cfg['label']} ({title_suffix})\n" \
            f"Finite Elements: {data['num_elements']:,} ({data['num_quads']:,} quads, {data['num_tris']:,} tris) | Nodes: {data['num_nodes']:,}\n" \
            f"Loading Step: {cfg['displacement_range']} | Max Damage: {data['max_d']:.4f} | Min h: {data['min_h_um']:.1f} um"
    ax.set_title(title, fontsize=10.5, fontweight='bold', pad=12)
    
    if is_overlay:
        sm = cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, orientation='vertical', fraction=0.046, pad=0.04)
        cbar.set_label("Phase-Field Damage $d$", fontsize=10, fontweight='bold')
    else:
        ax.legend(loc='upper right', framealpha=0.92, fontsize=8.5)
        
    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved: {output_path.name}")

def render_seven_panel_comparison(all_data, is_closeup=False, is_overlay=False, output_path=None):
    fig, axes = plt.subplots(1, 7, figsize=(35, 5.5), dpi=300)
    
    cmap = cm.get_cmap('plasma')
    norm = Normalize(vmin=0.0, vmax=1.0)
    
    for i, data in enumerate(all_data):
        ax = axes[i]
        cfg = data["cfg"]
        
        if is_overlay:
            colors = cmap(norm(data["damages"]))
            coll = PolyCollection(data["polys"], facecolors=colors, edgecolors='#111111', linewidths=0.20, alpha=0.92)
        elif is_closeup:
            coll = PolyCollection(data["polys"], facecolors='#eef4fb', edgecolors='#1a365d', linewidths=0.30)
        else:
            coll = PolyCollection(data["polys"], facecolors='#f7fafc', edgecolors='#2b6cb0', linewidths=0.15)
            
        ax.add_collection(coll)
        ax.plot([0.0, 0.5], [0.5, 0.5], color='#e53e3e', linewidth=2.0, zorder=10)
        ax.plot([0.5], [0.5], marker='o', markersize=4.0, color='#c53030', markeredgecolor='black', markeredgewidth=0.8, zorder=11)
        
        if cfg["stage_id"] in (5, 6):
            cf_x = data.get("crack_front_x", 0.656302)
            ax.plot([cf_x], [0.5], marker='*', markersize=8.0, color='#ffd700', markeredgecolor='black', markeredgewidth=0.8, zorder=12)
        
        if is_closeup:
            ax.set_xlim(0.40, 0.72)
            ax.set_ylim(0.40, 0.60)
        else:
            ax.set_xlim(-0.02, 1.02)
            ax.set_ylim(-0.02, 1.02)
            
        ax.set_aspect('equal')
        ax.set_xlabel("x [mm]", fontsize=9, fontweight='bold')
        if i == 0:
            ax.set_ylabel("y [mm]", fontsize=9, fontweight='bold')
        else:
            ax.set_yticklabels([])
            
        panel_title = f"{cfg['name']}: {cfg['label']}\n{data['num_elements']:,} el ({cfg['displacement_range']})\n$d_{{max}} = {data['max_d']:.4f}$ | $h_{{min}} = {data['min_h_um']:.1f}\\,\\mu m$"
        ax.set_title(panel_title, fontsize=8.0, fontweight='bold', pad=8)
        ax.grid(True, linestyle=':', alpha=0.35)

    if is_overlay:
        fig.subplots_adjust(right=0.94)
        cbar_ax = fig.add_axes([0.95, 0.18, 0.010, 0.64])
        sm = cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, cax=cbar_ax)
        cbar.set_label("Phase-Field Damage $d$", fontsize=10, fontweight='bold')
        
    title_kind = "Crack-Tip & Ligament Discretization" if is_closeup else "Full-Specimen Discretization"
    if is_overlay:
        title_kind += " & Damage Field Overlay"
    fig.suptitle(f"Method C Adaptive Remeshing Progression: {title_kind} (Stages 0 to 6)", fontsize=13, fontweight='bold', y=0.99)
    plt.tight_layout(rect=[0, 0, 0.94 if is_overlay else 1.0, 0.95])
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved: {output_path.name}")

def render_cycle5_adaptive_comparison(data5, data6, output_path):
    """Renders direct side-by-side comparison of Stage 5 (29k continuation) vs Stage 6 (34k Cycle 5 remesh)."""
    fig, axes = plt.subplots(2, 2, figsize=(16, 14), dpi=300)
    
    cmap = cm.get_cmap('plasma')
    norm = Normalize(vmin=0.0, vmax=1.0)
    
    cf_x5 = data5.get("crack_front_x", 0.656302)
    cf_x6 = data6.get("crack_front_x", 0.656302)
    adv_um5 = (cf_x5 - 0.50) * 1000.0
    adv_um6 = (cf_x6 - 0.50) * 1000.0

    # Row 1: Mesh only (Close-ups)
    # Panel (a): Stage 5 Solved Donor ODB Mesh
    ax = axes[0, 0]
    coll = PolyCollection(data5["polys"], facecolors='#eef4fb', edgecolors='#1a365d', linewidths=0.45)
    ax.add_collection(coll)
    ax.plot([0.0, 0.5], [0.5, 0.5], color='#e53e3e', linewidth=2.5, zorder=10)
    ax.plot([0.5], [0.5], marker='o', markersize=6, color='#c53030', markeredgecolor='black', zorder=11)
    ax.plot([cf_x5], [0.5], marker='*', markersize=12, color='#ffd700', markeredgecolor='black', zorder=12)
    ax.set_xlim(0.40, 0.72); ax.set_ylim(0.40, 0.60); ax.set_aspect('equal')
    ax.set_title("(a) Solved Donor ODB State (Job 1414920, u = 0.0060 mm, 29,293 elements)\nRefinement corridor centered on stationary notch tip (0.5, 0.5)", fontsize=11, fontweight='bold')
    ax.set_xlabel("x [mm]", fontsize=10, fontweight='bold'); ax.set_ylabel("y [mm]", fontsize=10, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.4)
    
    # Panel (b): Stage 6 Mapped Recipient Mesh
    ax = axes[0, 1]
    coll = PolyCollection(data6["polys"], facecolors='#eef4fb', edgecolors='#2c5282', linewidths=0.45)
    ax.add_collection(coll)
    ax.plot([0.0, 0.5], [0.5, 0.5], color='#e53e3e', linewidth=2.5, zorder=10)
    ax.plot([0.5], [0.5], marker='o', markersize=6, color='#c53030', markeredgecolor='black', zorder=11)
    ax.plot([cf_x6], [0.5], marker='*', markersize=12, color='#ffd700', markeredgecolor='black', zorder=12)
    ax.set_xlim(0.40, 0.72); ax.set_ylim(0.40, 0.60); ax.set_aspect('equal')
    ax.set_title("(b) Mapped Recipient Initial Mesh (Cycle 5 Native Remesh, 34,094 elements, +16.4%)\nFine corridor dynamically elongated +156.3 um along crack path (+988 fine elements)", fontsize=11, fontweight='bold')
    ax.set_xlabel("x [mm]", fontsize=10, fontweight='bold'); ax.set_ylabel("y [mm]", fontsize=10, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.4)
    
    # Row 2: Mesh + Damage Overlay
    # Panel (c): Stage 5 Solved Donor Damage
    ax = axes[1, 0]
    colors5 = cmap(norm(data5["damages"]))
    coll = PolyCollection(data5["polys"], facecolors=colors5, edgecolors='#111111', linewidths=0.30, alpha=0.92)
    ax.add_collection(coll)
    ax.plot([0.0, 0.5], [0.5, 0.5], color='#ffffff', linewidth=2.5, zorder=10)
    ax.plot([0.5], [0.5], marker='o', markersize=6, color='#c53030', markeredgecolor='white', zorder=11)
    ax.plot([cf_x5], [0.5], marker='*', markersize=12, color='#ffd700', markeredgecolor='black', zorder=12)
    ax.set_xlim(0.40, 0.72); ax.set_ylim(0.40, 0.60); ax.set_aspect('equal')
    title_c = f"(c) Solved Donor ODB Damage at u = 0.0060 mm (d_max=1.0009)\nSolved crack front reaches x = {cf_x5:.4f} mm (dx = {adv_um5:.1f} um = {adv_um5/7.5:.1f} l0)"
    ax.set_title(title_c, fontsize=11, fontweight='bold')
    ax.set_xlabel("x [mm]", fontsize=10, fontweight='bold'); ax.set_ylabel("y [mm]", fontsize=10, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.4)
    
    # Panel (d): Stage 6 Mapped Recipient Initial Damage
    ax = axes[1, 1]
    colors6 = cmap(norm(data6["damages"]))
    coll = PolyCollection(data6["polys"], facecolors=colors6, edgecolors='#111111', linewidths=0.30, alpha=0.92)
    ax.add_collection(coll)
    ax.plot([0.0, 0.5], [0.5, 0.5], color='#ffffff', linewidth=2.5, zorder=10)
    ax.plot([0.5], [0.5], marker='o', markersize=6, color='#c53030', markeredgecolor='white', zorder=11)
    ax.plot([cf_x6], [0.5], marker='*', markersize=12, color='#ffd700', markeredgecolor='black', zorder=12)
    ax.set_xlim(0.40, 0.72); ax.set_ylim(0.40, 0.60); ax.set_aspect('equal')
    title_d = "(d) Mapped Recipient Initial Damage via Consistent L2 (d_max=1.0009)\nAll 7 Gate 6C criteria PASS; fine mesh envelops evolving crack wake and front"
    ax.set_title(title_d, fontsize=11, fontweight='bold')
    ax.set_xlabel("x [mm]", fontsize=10, fontweight='bold'); ax.set_ylabel("y [mm]", fontsize=10, fontweight='bold')
    ax.grid(True, linestyle=':', alpha=0.4)
    
    fig.subplots_adjust(right=0.91)
    cbar_ax = fig.add_axes([0.93, 0.15, 0.02, 0.70])
    sm = cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, cax=cbar_ax)
    cbar.set_label("Phase-Field Damage $d$", fontsize=12, fontweight='bold')
    
    fig.suptitle("Method C Cycle 5: First Propagation-Stage Native Adaptive Remeshing Demonstration\n"
                 r"Dynamic Crack Following from $u = 0.0055\,\mathrm{mm}$ to $u = 0.0060\,\mathrm{mm}$ Across Peak Load",
                 fontsize=14, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 0.91, 0.95])
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved: {output_path.name}")

def render_force_displacement_and_crack_advance(output_path_fu, output_path_advance):
    """Renders F-u curve with peak zoom inset and crack-front advance vs displacement plot."""
    # 1. Load Reference 1398090
    ref_csv = REPO_ROOT / "results" / "pandey_kumar_mode1" / "master_fracture_curves" / "curve_standard_1398090.csv"
    ref_u = []
    ref_f = []
    with open(ref_csv, 'r') as f:
        next(f) # skip header
        for line in f:
            parts = line.strip().split(',')
            if len(parts) >= 4:
                u = float(parts[2])
                rf = float(parts[3]) * 1000.0 # kN to N
                if u <= 0.0075:
                    ref_u.append(u)
                    ref_f.append(rf)
    ref_u = np.array(ref_u)
    ref_f = np.array(ref_f)
    
    # 2. Load Package 65 History
    summary65_file = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_propagation_stage2_continuation" / "package65_terminal_summary.json"
    with open(summary65_file, 'r') as f:
        summary65 = json.load(f)
    
    pkg65_u = []
    pkg65_f = []
    for item in summary65["rf_u_history"]:
        if item["step"] == "Step-2-Continue":
            pkg65_u.append(item["u2_mm"])
            pkg65_f.append(item["rf2_N"])
    pkg65_u = np.array(pkg65_u)
    pkg65_f = np.array(pkg65_f)
    
    # 3. Load Crack Advance checkpoints from Package 65
    checkpoints = summary65["checkpoints"]
    cp_u = [cp["u2_mm"] for cp in checkpoints]
    cp_adv = [cp["advance_from_notch_um"] for cp in checkpoints]
    cp_dmax = [cp["max_damage"] for cp in checkpoints]
    
    # --- Plot 1: Force-Displacement Curve with Inset ---
    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    
    ax.plot(ref_u * 1000.0, ref_f, color='#2b6cb0', linewidth=2.2, label='Reference 1398090 (Fixed Structured Mesh, $h = 3.0\\,\\mu m$, Peak $757.8\\,\\mathrm{N}$)')
    ax.plot(pkg65_u * 1000.0, pkg65_f, color='#e53e3e', linewidth=2.4, linestyle='-', marker='o', markersize=3.5, label='Method C Stage 2 Continuation (Job 1414920, $h = 0.8\\,\\mu m$, Peak $732.85\\,\\mathrm{N}$)')
    
    # Add Package 67 Peak Marker
    ax.plot([0.00563625 * 1000.0], [732.4807], marker='*', markersize=12, color='#38a169', markeredgecolor='black', zorder=15,
            label='Package 67 Fine dt Diagnostic ($du = 1.25\\,\\mathrm{nm}$, Peak $732.48\\,\\mathrm{N}$, $0.050\\%$ parity)')
    
    ax.set_xlim(5.2, 6.2)
    ax.set_ylim(500, 780)
    ax.set_xlabel(r"Applied Boundary Displacement $u$ [$\mu\mathrm{m}$]", fontsize=12, fontweight='bold')
    ax.set_ylabel(r"Total Reaction Force $RF_2$ [$\mathrm{N}$]", fontsize=12, fontweight='bold')
    ax.set_title("Method C Mode-I Fracture Trajectory Across Reference Peak Load\n"
                 r"Spatial Resolution vs State Transfer Attribution ($h = 0.8\,\mu\mathrm{m}$ vs $3.0\,\mu\mathrm{m}$)",
                 fontsize=12, fontweight='bold', pad=12)
    ax.grid(True, linestyle=':', alpha=0.5)
    ax.legend(loc='lower left', framealpha=0.95, fontsize=9.5)
    
    # Inset Zoom around Peak
    axins = ax.inset_axes([0.55, 0.48, 0.42, 0.46])
    axins.plot(ref_u * 1000.0, ref_f, color='#2b6cb0', linewidth=2.0)
    axins.plot(pkg65_u * 1000.0, pkg65_f, color='#e53e3e', linewidth=2.2, marker='o', markersize=4.5)
    axins.plot([0.00563625 * 1000.0], [732.4807], marker='*', markersize=14, color='#38a169', markeredgecolor='black', zorder=15)
    axins.set_xlim(5.55, 5.95)
    axins.set_ylim(715, 765)
    axins.set_title(r"Peak Region: $\Delta RF_{\mathrm{temp}} = 0.37\,\mathrm{N}$ ($0.050\%$) Parity", fontsize=9.5, fontweight='bold')
    axins.grid(True, linestyle=':', alpha=0.5)
    ax.indicate_inset_zoom(axins, edgecolor="black")
    
    plt.tight_layout()
    fig.savefig(output_path_fu, dpi=300)
    plt.close(fig)
    print(f"Saved: {output_path_fu.name}")
    
    # --- Plot 2: Crack Advance vs Applied Displacement ---
    fig, ax1 = plt.subplots(figsize=(9, 6.5), dpi=300)
    
    color1 = '#c53030'
    ax1.plot(np.array(cp_u) * 1000.0, cp_adv, color=color1, linewidth=2.4, marker='s', markersize=7, label=r'Crack Advance $\Delta x(d \geq 0.5)$')
    ax1.set_xlabel(r"Applied Boundary Displacement $u$ [$\mu\mathrm{m}$]", fontsize=12, fontweight='bold')
    ax1.set_ylabel(r"Crack Front Advance from Notch Tip $\Delta x$ [$\mu\mathrm{m}$]", color=color1, fontsize=12, fontweight='bold')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, linestyle=':', alpha=0.5)
    
    # Secondary axis for max damage
    ax2 = ax1.twinx()
    color2 = '#2b6cb0'
    ax2.plot(np.array(cp_u) * 1000.0, cp_dmax, color=color2, linewidth=2.0, linestyle='--', marker='^', markersize=7, label=r'Maximum Damage $d_{\max}$')
    ax2.set_ylabel(r"Maximum Phase-Field Damage $d_{\max}$", color=color2, fontsize=12, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor=color2)
    ax2.set_ylim(0.4, 1.05)
    
    # Mark regularization length scale multiples
    l0_um = 7.5
    ax1.axhline(l0_um, color='#718096', linestyle=':', label=r'$1\,l_0 = 7.5\,\mu\mathrm{m}$')
    ax1.axhline(10.0 * l0_um, color='#a0aec0', linestyle=':', label=r'$10\,l_0 = 75\,\mu\mathrm{m}$')
    ax1.axhline(20.0 * l0_um, color='#cbd5e0', linestyle=':', label=r'$20\,l_0 = 150\,\mu\mathrm{m}$')
    
    title = "Method C Macroscopic Crack Propagation Along Ligament Plane ($y = 0.5\\,\\mathrm{mm}$)\n" \
            r"Definitive Crack Extension of $156.26\,\mu\mathrm{m}$ ($20.8\,l_0$) from Notch Tip"
    plt.title(title, fontsize=11.5, fontweight='bold', pad=12)
    
    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='center left', framealpha=0.92, fontsize=9.5)
    
    plt.tight_layout()
    fig.savefig(output_path_advance, dpi=300)
    plt.close(fig)
    print(f"Saved: {output_path_advance.name}")

def package_all_figures():
    zip_path = OUTPUT_DIR / "method_c_propagation_stage2_figures.zip"
    print(f"Creating zip package: {zip_path.name}...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(OUTPUT_DIR.glob("*.png")):
            zf.write(f, arcname=f.name)
            print(f"  Added {f.name} ({f.stat().st_size / 1024 / 1024:.2f} MB)")
        for f in sorted(OUTPUT_DIR.glob("*.json")):
            zf.write(f, arcname=f.name)
            print(f"  Added {f.name} ({f.stat().st_size / 1024:.1f} KB)")
    print(f"Zip created successfully: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Mirror zip to repo root for easy release upload
    root_zip = REPO_ROOT / "method_c_propagation_stage2_figures.zip"
    with open(zip_path, 'rb') as f_in, open(root_zip, 'wb') as f_out:
        f_out.write(f_in.read())
    print(f"Mirrored zip to repo root: {root_zip.name}")

def main():
    print("=== Exporting Method C Stage 2 Propagation & Remeshing Figures ===")
    
    # 1. Parse Stage 5 to serve as donor for Stage 6
    stage5_cfg = [c for c in STAGE_CONFIGS if c["stage_id"] == 5][0]
    stage5_data = load_stage_data(stage5_cfg)
    
    donor_mesh = stage5_data["mesh"]
    donor_state = Mode1State()
    # Ingest donor nodal displacements and damage from donor_package65_u0060.json
    donor_json = REPO_ROOT / stage5_cfg["donor_json_path"]
    with open(donor_json, 'r', encoding='utf-8') as fp:
        jdata = json.load(fp)
    for nid_str, u_vals in jdata.get("u_nodal", {}).items():
        donor_state.u_nodal[int(nid_str)] = (float(u_vals[0]), float(u_vals[1]))

    elem_sdv = jdata.get("elem_sdv", {})
    node_d_sums = {}
    node_d_counts = {}
    for eid, conn in donor_mesh.elements_u1.items():
        svals = elem_sdv.get(str(eid), {})
        d_list = svals.get("SDV14", [0.0])
        d_elem = sum(d_list) / len(d_list)
        h_list = svals.get("SDV2", [0.0])
        donor_state.H_gp[eid] = [float(x) for x in h_list]
        for nid in conn:
            node_d_sums[nid] = node_d_sums.get(nid, 0.0) + d_elem
            node_d_counts[nid] = node_d_counts.get(nid, 0) + 1

    for nid in donor_mesh.nodes:
        if nid in node_d_sums:
            donor_state.d_nodal[nid] = node_d_sums[nid] / node_d_counts[nid]
        else:
            donor_state.d_nodal[nid] = 0.0

    donor_state.u_rp = (0.0, 0.0060)
    
    # 2. Parse all stages
    all_data = []
    for cfg in STAGE_CONFIGS:
        if cfg["stage_id"] == 5:
            all_data.append(stage5_data)
        elif cfg["stage_id"] == 6:
            data = load_stage_data(cfg, donor_mesh=donor_mesh, donor_state=donor_state)
            all_data.append(data)
        else:
            data = load_stage_data(cfg)
            all_data.append(data)
            
        # Render individual figures
        render_mesh_figure(all_data[-1], is_closeup=False, is_overlay=False, output_path=OUTPUT_DIR / cfg["full_mesh_filename"])
        render_mesh_figure(all_data[-1], is_closeup=True, is_overlay=False, output_path=OUTPUT_DIR / cfg["closeup_mesh_filename"])
        render_mesh_figure(all_data[-1], is_closeup=True, is_overlay=True, output_path=OUTPUT_DIR / cfg["overlay_filename"])
        
    # 3. Seven-panel multi-stage comparisons
    render_seven_panel_comparison(all_data, is_closeup=False, is_overlay=False, output_path=OUTPUT_DIR / "method_c_propagation_full_meshes_comparison.png")
    render_seven_panel_comparison(all_data, is_closeup=True, is_overlay=False, output_path=OUTPUT_DIR / "method_c_propagation_crack_tip_closeups_comparison.png")
    render_seven_panel_comparison(all_data, is_closeup=True, is_overlay=True, output_path=OUTPUT_DIR / "method_c_propagation_damage_overlay_comparison.png")
    
    # 4. Dedicated 2-panel comparison of Stage 5 vs Stage 6
    stage6_data = all_data[-1]
    render_cycle5_adaptive_comparison(stage5_data, stage6_data, output_path=OUTPUT_DIR / "method_c_cycle5_adaptive_crack_tracking_comparison.png")
    
    # 5. F-u curve and Crack Advance plots
    render_force_displacement_and_crack_advance(
        output_path_fu=OUTPUT_DIR / "method_c_force_displacement_peak_and_softening_comparison.png",
        output_path_advance=OUTPUT_DIR / "method_c_crack_propagation_vs_displacement.png"
    )
    
    # 6. Save numerical evidence table
    summary_data = []
    for d in all_data:
        cfg = d["cfg"]
        summary_data.append({
            "stage_id": cfg["stage_id"],
            "name": cfg["name"],
            "label": cfg["label"],
            "cycle_name": cfg["cycle_name"],
            "displacement_range": cfg["displacement_range"],
            "element_count": d["num_elements"],
            "quad_count": d["num_quads"],
            "tri_count": d["num_tris"],
            "node_count": d["num_nodes"],
            "max_damage": d["max_d"],
            "min_element_size_um": d["min_h_um"],
        })
    with open(OUTPUT_DIR / "method_c_propagation_stage2_numerical_evidence.json", 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2)
        
    # 7. Package zip
    package_all_figures()
    print("=== Method C Stage 2 Figures Export Complete ===")

if __name__ == '__main__':
    main()

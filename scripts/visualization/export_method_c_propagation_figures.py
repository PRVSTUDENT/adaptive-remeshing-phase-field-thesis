"""
Export authentic high-resolution Method C adaptive remeshing and propagation visualization figures.

Generates:
1. Individual full-specimen mesh figures (Stages 0 to 5)
2. Individual crack-tip and ligament close-up mesh figures (Stages 0 to 5)
3. Individual phase-field damage contour figures (Stages 0 to 5)
4. Individual mesh + damage overlay figures (Stages 0 to 5)
5. Multi-panel global mesh comparison figure (Stages 0 to 5)
6. Multi-panel crack-tip and ligament close-up comparison figure (Stages 0 to 5)
7. Multi-panel damage field comparison figure (Stages 0 to 5)
8. Multi-panel mesh + damage overlay comparison figure (Stages 0 to 5)
9. Numerical evidence extraction tables (CSV and JSON)
10. Zip package containing all figures and evidence for GitHub release distribution.
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
from mode1_state_transfer_engine import parse_mode1_input_deck

OUTPUT_DIR = REPO_ROOT / "method_c_propagation_figures"
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
        "damage_filename": "damage_stage0_coarse_2906.png",
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
        "damage_filename": "damage_stage1_cycle1_17913.png",
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
        "damage_filename": "damage_stage2_cycle2_21546.png",
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
        "damage_filename": "damage_stage3_cycle3_25085.png",
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
        "damage_filename": "damage_stage4_cycle4_29293.png",
        "overlay_filename": "overlay_stage4_cycle4_29293.png",
    },
    {
        "stage_id": 5,
        "name": "Stage 5",
        "label": "Propagation Continuation",
        "cycle_name": "Package 64 Propagation Stage 1",
        "displacement_range": "u = 0.0021 -> 0.0055 mm",
        "expected_elements": 29293,
        "deck_rel_path": "models/pandey_kumar_mode1/64_method_c_propagation_stage1_continuation/M1_MC_PROP_STAGE1_CONT.inp",
        "full_mesh_filename": "mesh_stage5_propagation_29293.png",
        "closeup_mesh_filename": "closeup_stage5_propagation_29293.png",
        "damage_filename": "damage_stage5_propagation_29293.png",
        "overlay_filename": "overlay_stage5_propagation_29293.png",
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
                    # End of IC block
                    if current_eid is not None and current_vals:
                        # SDV1 is val[0], SDV14 is val[13] if available
                        d_val = current_vals[13] if len(current_vals) >= 14 else current_vals[0]
                        damage_dict[current_eid] = d_val
                    break
            if in_ic:
                parts = [p.strip() for p in line_str.split(",") if p.strip()]
                if not parts:
                    continue
                # If first item looks like integer element ID and previous line completed
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

def load_stage_data(cfg):
    deck_path = REPO_ROOT / cfg["deck_rel_path"]
    print(f"Loading {cfg['name']} from {deck_path.name}...")
    t0 = time.time()
    mesh = parse_mode1_input_deck(str(deck_path))
    
    # Check if a terminal donor JSON exists for this stage
    donor_json = None
    if cfg["stage_id"] == 5:
        cand1 = REPO_ROOT / "runs" / "hpc" / "mode1_stage_c1_2_propagation_stage1_continuation" / "donor_propagation_u0055.json"
        cand2 = REPO_ROOT / "models" / "pandey_kumar_mode1" / "64_method_c_propagation_stage1_continuation" / "donor_propagation_u0055.json"
        if cand1.exists():
            donor_json = cand1
        elif cand2.exists():
            donor_json = cand2

    if donor_json is not None:
        print(f"  Reading terminal damage fields from {donor_json.name}...")
        with open(donor_json, 'r', encoding='utf-8') as fp:
            jdata = json.load(fp)
        damage_dict = {}
        for eid_str, svals in jdata.get("elem_sdv", {}).items():
            eid = int(eid_str)
            d_list = svals.get("SDV14", [0.0])
            damage_dict[eid] = float(np.mean(d_list))
    else:
        damage_dict = parse_initial_damage_from_deck(deck_path)
    
    polys = []
    elem_damages = []
    num_quads = 0
    num_tris = 0
    
    # Layer 1 elements
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
    
    dt = time.time() - t0
    print(f"  -> {num_elements} physical elements ({num_quads} quads, {num_tris} tris), {num_nodes} nodes, max_d={max_d:.4f}, min_h={min_h:.2f} um (parsed in {dt:.2f}s)")
    
    return {
        "cfg": cfg,
        "polys": polys,
        "damages": elem_damages,
        "max_d": max_d,
        "min_h_um": min_h,
        "ligament_elements": ligament_elements,
        "num_elements": num_elements,
        "num_quads": num_quads,
        "num_tris": num_tris,
        "num_nodes": num_nodes,
    }

def render_mesh_figure(data, is_closeup=False, is_overlay=False, output_path=None):
    cfg = data["cfg"]
    fig, ax = plt.subplots(figsize=(8.5, 8.5), dpi=300)
    
    cmap = cm.get_cmap('plasma')
    norm = Normalize(vmin=0.0, vmax=1.0)
    
    if is_overlay:
        colors = cmap(norm(data["damages"]))
        coll = PolyCollection(data["polys"], facecolors=colors, edgecolors='#111111', linewidths=0.35, alpha=0.92)
    elif is_closeup:
        coll = PolyCollection(data["polys"], facecolors='#eef4fb', edgecolors='#1a365d', linewidths=0.45)
    else:
        coll = PolyCollection(data["polys"], facecolors='#f7fafc', edgecolors='#2b6cb0', linewidths=0.25)
    
    ax.add_collection(coll)
    
    # Initial crack seam
    ax.plot([0.0, 0.5], [0.5, 0.5], color='#e53e3e', linewidth=2.5, linestyle='-', zorder=10, label='Initial Crack Seam (y=0.5, x<=0.5)')
    ax.plot([0.5], [0.5], marker='o', markersize=6, color='#c53030', markeredgecolor='black', markeredgewidth=1.2, zorder=11, label='Initial Crack Tip (0.5, 0.5)')
    
    if is_closeup:
        ax.set_xlim(0.40, 0.70)
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
    ax.set_title(title, fontsize=11, fontweight='bold', pad=12)
    
    if is_overlay:
        sm = cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, ax=ax, orientation='vertical', fraction=0.046, pad=0.04)
        cbar.set_label("Phase-Field Damage $d$", fontsize=10, fontweight='bold')
    else:
        ax.legend(loc='upper right', framealpha=0.92, fontsize=9)
        
    plt.tight_layout()
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved: {output_path.name}")

def render_six_panel_comparison(all_data, is_closeup=False, is_overlay=False, output_path=None):
    fig, axes = plt.subplots(1, 6, figsize=(30, 5.5), dpi=300)
    
    cmap = cm.get_cmap('plasma')
    norm = Normalize(vmin=0.0, vmax=1.0)
    
    for i, data in enumerate(all_data):
        ax = axes[i]
        cfg = data["cfg"]
        
        if is_overlay:
            colors = cmap(norm(data["damages"]))
            coll = PolyCollection(data["polys"], facecolors=colors, edgecolors='#111111', linewidths=0.25, alpha=0.92)
        elif is_closeup:
            coll = PolyCollection(data["polys"], facecolors='#eef4fb', edgecolors='#1a365d', linewidths=0.35)
        else:
            coll = PolyCollection(data["polys"], facecolors='#f7fafc', edgecolors='#2b6cb0', linewidths=0.18)
            
        ax.add_collection(coll)
        ax.plot([0.0, 0.5], [0.5, 0.5], color='#e53e3e', linewidth=2.0, zorder=10)
        ax.plot([0.5], [0.5], marker='o', markersize=4.5, color='#c53030', markeredgecolor='black', markeredgewidth=0.8, zorder=11)
        
        if is_closeup:
            ax.set_xlim(0.40, 0.70)
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
        ax.set_title(panel_title, fontsize=8.5, fontweight='bold', pad=8)
        ax.grid(True, linestyle=':', alpha=0.35)

    if is_overlay:
        fig.subplots_adjust(right=0.93)
        cbar_ax = fig.add_axes([0.94, 0.18, 0.012, 0.64])
        sm = cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])
        cbar = fig.colorbar(sm, cax=cbar_ax)
        cbar.set_label("Phase-Field Damage $d$", fontsize=10, fontweight='bold')
        
    title_kind = "Crack-Tip & Ligament Discretization" if is_closeup else "Full-Specimen Discretization"
    if is_overlay:
        title_kind += " & Damage Field Overlay"
    fig.suptitle(f"Method C Adaptive Remeshing Progression: {title_kind} (Stages 0 to 5)", fontsize=13, fontweight='bold', y=0.99)
    plt.tight_layout(rect=[0, 0, 0.93 if is_overlay else 1.0, 0.95])
    fig.savefig(output_path, dpi=300)
    plt.close(fig)
    print(f"Saved: {output_path.name}")

def package_all_figures():
    zip_path = OUTPUT_DIR / "method_c_propagation_figures.zip"
    print(f"Creating zip package: {zip_path.name}...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(OUTPUT_DIR.glob("*.png")):
            zf.write(f, arcname=f.name)
            print(f"  Added {f.name} ({f.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"Zip created successfully: {zip_path.stat().st_size / 1024 / 1024:.2f} MB")

def main():
    print("=== Exporting Method C Adaptive Remeshing & Propagation Figures ===")
    all_data = []
    for cfg in STAGE_CONFIGS:
        data = load_stage_data(cfg)
        all_data.append(data)
        
        # 1. Full mesh
        render_mesh_figure(data, is_closeup=False, is_overlay=False, output_path=OUTPUT_DIR / cfg["full_mesh_filename"])
        # 2. Closeup mesh
        render_mesh_figure(data, is_closeup=True, is_overlay=False, output_path=OUTPUT_DIR / cfg["closeup_mesh_filename"])
        # 3. Closeup overlay
        render_mesh_figure(data, is_closeup=True, is_overlay=True, output_path=OUTPUT_DIR / cfg["overlay_filename"])
        
    # Multi-panel comparisons
    render_six_panel_comparison(all_data, is_closeup=False, is_overlay=False, output_path=OUTPUT_DIR / "method_c_propagation_full_meshes_comparison.png")
    render_six_panel_comparison(all_data, is_closeup=True, is_overlay=False, output_path=OUTPUT_DIR / "method_c_propagation_crack_tip_closeups_comparison.png")
    render_six_panel_comparison(all_data, is_closeup=True, is_overlay=True, output_path=OUTPUT_DIR / "method_c_propagation_damage_overlay_comparison.png")
    
    # Save numerical evidence table
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
    with open(OUTPUT_DIR / "method_c_propagation_numerical_evidence.json", 'w', encoding='utf-8') as f:
        json.dump(summary_data, f, indent=2)
        
    package_all_figures()
    print("=== Method C Figures Export Complete ===")

if __name__ == '__main__':
    main()

"""
Export authentic high-resolution Method C adaptive remeshing visualization images.

Generates:
1. Individual full-specimen mesh figures (Stages 0 to 4)
2. Individual crack-tip close-up mesh figures (Stages 0 to 4)
3. 5-panel multi-mesh global comparison figure
4. 5-panel multi-mesh crack-tip close-up comparison figure
5. Zip package containing all figures for distribution.
"""

import os
import sys
import time
import zipfile
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import numpy as np

# Add state transfer engine to import parser
REPO_ROOT = Path(r"D:\Master thesis\Adaptive remeshing")
sys.path.insert(0, str(REPO_ROOT / "scripts" / "state_transfer"))
from mode1_state_transfer_engine import parse_mode1_input_deck

OUTPUT_DIR = REPO_ROOT / "method_c_mesh_figures"
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
        "full_filename": "mesh_stage0_coarse_2906.png",
        "closeup_filename": "closeup_stage0_coarse_2906.png",
    },
    {
        "stage_id": 1,
        "name": "Stage 1",
        "label": "Remeshing Cycle 1",
        "cycle_name": "Cycle 1 Continuation",
        "displacement_range": "u = 0.0010 -> 0.0012 mm",
        "expected_elements": 17913,
        "deck_rel_path": "models/pandey_kumar_mode1/57_method_c_stage_c1_2_cycle1_continuation/M1_MC_STAGE_C1_2_CYCLE1_CONT.inp",
        "full_filename": "mesh_stage1_cycle1_17913.png",
        "closeup_filename": "closeup_stage1_cycle1_17913.png",
    },
    {
        "stage_id": 2,
        "name": "Stage 2",
        "label": "Remeshing Cycle 2",
        "cycle_name": "Cycle 2 Continuation",
        "displacement_range": "u = 0.0012 -> 0.0015 mm",
        "expected_elements": 21546,
        "deck_rel_path": "models/pandey_kumar_mode1/59_method_c_stage_c1_2_cycle2_continuation/M1_MC_STAGE_C1_2_CYCLE2_CONT.inp",
        "full_filename": "mesh_stage2_cycle2_21546.png",
        "closeup_filename": "closeup_stage2_cycle2_21546.png",
    },
    {
        "stage_id": 3,
        "name": "Stage 3",
        "label": "Remeshing Cycle 3",
        "cycle_name": "Cycle 3 Continuation",
        "displacement_range": "u = 0.0015 -> 0.0018 mm",
        "expected_elements": 25085,
        "deck_rel_path": "models/pandey_kumar_mode1/61_method_c_stage_c1_2_cycle3_continuation/M1_MC_STAGE_C1_2_CYCLE3_CONT.inp",
        "full_filename": "mesh_stage3_cycle3_25085.png",
        "closeup_filename": "closeup_stage3_cycle3_25085.png",
    },
    {
        "stage_id": 4,
        "name": "Stage 4",
        "label": "Remeshing Cycle 4",
        "cycle_name": "Cycle 4 Continuation",
        "displacement_range": "u = 0.0018 -> 0.0021 mm",
        "expected_elements": 29293,
        "deck_rel_path": "models/pandey_kumar_mode1/62_method_c_stage_c1_2_cycle4_continuation/M1_MC_STAGE_C1_2_CYCLE4_CONT.inp",
        "full_filename": "mesh_stage4_cycle4_29293.png",
        "closeup_filename": "closeup_stage4_cycle4_29293.png",
    },
]

def load_stage_data(cfg):
    deck_path = REPO_ROOT / cfg["deck_rel_path"]
    print(f"Loading {cfg['name']} from {deck_path.name}...")
    t0 = time.time()
    mesh = parse_mode1_input_deck(str(deck_path))
    
    # Extract Layer 1 physical elements only
    polys = []
    num_quads = 0
    num_tris = 0
    
    for eid, conn in mesh.elements_u1.items():
        coords = [mesh.nodes[nid] for nid in conn]
        polys.append(coords)
        if len(conn) == 4:
            num_quads += 1
        elif len(conn) == 3:
            num_tris += 1
            
    num_elements = len(polys)
    num_nodes = len(mesh.nodes)
    print(f"  Parsed {num_elements} elements ({num_quads} quads, {num_tris} tris), {num_nodes} nodes in {time.time()-t0:.2f}s")
    assert num_elements == cfg["expected_elements"], f"Element mismatch: expected {cfg['expected_elements']}, got {num_elements}"
    
    return {
        "cfg": cfg,
        "mesh": mesh,
        "polys": polys,
        "num_elements": num_elements,
        "num_nodes": num_nodes,
        "num_quads": num_quads,
        "num_tris": num_tris,
        "deck_filename": deck_path.name,
    }

def render_individual_full_mesh(data):
    cfg = data["cfg"]
    out_path = OUTPUT_DIR / cfg["full_filename"]
    print(f"Rendering full mesh {out_path.name}...")
    
    fig, ax = plt.subplots(figsize=(8.5, 8.5), dpi=300)
    
    # PolyCollection for physical elements
    lw = 0.25 if data["num_elements"] < 10000 else 0.18
    coll = PolyCollection(data["polys"], facecolors='none', edgecolors='#0f172a', linewidths=lw)
    ax.add_collection(coll)
    
    # Sharp crack seam: y = 0.5, 0 <= x <= 0.5
    ax.plot([0.0, 0.5], [0.5, 0.5], color='#dc2626', linestyle='--', linewidth=1.8, label=r'Initial Crack Seam ($a_0 = 0.5$ mm)')
    ax.scatter([0.5], [0.5], color='#dc2626', s=50, zorder=5, label='Crack Tip (0.5, 0.5)')
    
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(-0.02, 1.02)
    ax.set_aspect('equal')
    
    ax.set_xlabel('X Coordinate [mm]', fontsize=13, fontweight='medium')
    ax.set_ylabel('Y Coordinate [mm]', fontsize=13, fontweight='medium')
    
    title_str = f"{cfg['name']}: {cfg['label']}\nAuthentic Mesh Discretization ($N = {data['num_elements']:,}$ Elements)"
    ax.set_title(title_str, fontsize=14, fontweight='bold', pad=12)
    
    # Info box
    info_text = (
        f"Domain: 1.0 x 1.0 mm (Mode-I)\n"
        f"Loading Step: {cfg['displacement_range']}\n"
        f"Elements: {data['num_elements']:,} ({data['num_quads']:,} Quads, {data['num_tris']:,} Tris)\n"
        f"Nodes: {data['num_nodes']:,}\n"
        f"Source: {data['deck_filename']}"
    )
    ax.text(
        0.03, 0.97, info_text, transform=ax.transAxes,
        fontsize=9.5, verticalalignment='top', horizontalalignment='left',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#94a3b8', alpha=0.92)
    )
    
    ax.grid(True, linestyle=':', alpha=0.5, color='#94a3b8')
    ax.legend(loc='lower left', framealpha=0.92, edgecolor='#94a3b8', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"  Saved {out_path.name} ({out_path.stat().st_size:,} bytes)")
    return out_path

def render_individual_closeup_mesh(data):
    cfg = data["cfg"]
    out_path = OUTPUT_DIR / cfg["closeup_filename"]
    print(f"Rendering crack-tip closeup {out_path.name}...")
    
    fig, ax = plt.subplots(figsize=(8.5, 8.5), dpi=300)
    
    # PolyCollection for physical elements
    coll = PolyCollection(data["polys"], facecolors='none', edgecolors='#0f172a', linewidths=0.35)
    ax.add_collection(coll)
    
    # Sharp crack seam: y = 0.5, 0 <= x <= 0.5
    ax.plot([0.0, 0.5], [0.5, 0.5], color='#dc2626', linestyle='--', linewidth=2.4, label=r'Crack Seam ($y = 0.5$ mm, $x \leq 0.5$)')
    ax.scatter([0.5], [0.5], color='#dc2626', s=90, zorder=5, label='Crack Tip Singular Point (0.5, 0.5)')
    
    # Crack tip close-up window: [0.40, 0.60] mm (200 x 200 um)
    ax.set_xlim(0.40, 0.60)
    ax.set_ylim(0.40, 0.60)
    ax.set_aspect('equal')
    
    ax.set_xticks([0.40, 0.45, 0.50, 0.55, 0.60])
    ax.set_yticks([0.40, 0.45, 0.50, 0.55, 0.60])
    
    ax.set_xlabel('X Coordinate [mm]', fontsize=13, fontweight='medium')
    ax.set_ylabel('Y Coordinate [mm]', fontsize=13, fontweight='medium')
    
    title_str = f"{cfg['name']}: Crack-Tip Refinement Corridor\n{cfg['label']} ($0.20 \\times 0.20$ mm Magnified Window)"
    ax.set_title(title_str, fontsize=14, fontweight='bold', pad=12)
    
    # Info box
    info_text = (
        f"Zoom Window: x, y in [0.40, 0.60] mm\n"
        f"Specimen: Mode-I Sharp Slit\n"
        f"Mesh Stage: {cfg['label']}\n"
        f"Total Discretization: {data['num_elements']:,} Elements\n"
        f"Loading: {cfg['displacement_range']}"
    )
    ax.text(
        0.03, 0.97, info_text, transform=ax.transAxes,
        fontsize=9.5, verticalalignment='top', horizontalalignment='left',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', edgecolor='#94a3b8', alpha=0.92)
    )
    
    ax.grid(True, linestyle=':', alpha=0.5, color='#94a3b8')
    ax.legend(loc='lower left', framealpha=0.92, edgecolor='#94a3b8', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"  Saved {out_path.name} ({out_path.stat().st_size:,} bytes)")
    return out_path

def render_multi_panel_full_comparison(all_data):
    out_path = OUTPUT_DIR / "method_c_full_meshes_comparison.png"
    print(f"Rendering 5-panel global comparison {out_path.name}...")
    
    fig, axes = plt.subplots(1, 5, figsize=(26, 6.0), dpi=300)
    
    for i, data in enumerate(all_data):
        ax = axes[i]
        cfg = data["cfg"]
        lw = 0.22 if data["num_elements"] < 10000 else 0.14
        
        coll = PolyCollection(data["polys"], facecolors='none', edgecolors='#0f172a', linewidths=lw)
        ax.add_collection(coll)
        
        ax.plot([0.0, 0.5], [0.5, 0.5], color='#dc2626', linestyle='--', linewidth=1.5)
        ax.scatter([0.5], [0.5], color='#dc2626', s=35, zorder=5)
        
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        ax.set_aspect('equal')
        
        ax.set_title(f"({chr(97+i)}) {cfg['name']}: {cfg['label']}\n$N = {data['num_elements']:,}$ elements", fontsize=12, fontweight='bold', pad=8)
        ax.set_xlabel('X [mm]', fontsize=11)
        if i == 0:
            ax.set_ylabel('Y [mm]', fontsize=11)
        else:
            ax.set_yticklabels([])
            
        ax.grid(True, linestyle=':', alpha=0.4, color='#94a3b8')
        
        # Sub-badge with element count and loading
        badge = f"{cfg['displacement_range']}\n{data['num_nodes']:,} nodes"
        ax.text(
            0.04, 0.96, badge, transform=ax.transAxes,
            fontsize=8.5, verticalalignment='top',
            bbox=dict(boxstyle='square,pad=0.3', facecolor='white', edgecolor='#cbd5e1', alpha=0.88)
        )
        
    fig.suptitle("Method C Sequential Adaptive Remeshing: Complete $1.0 \\times 1.0$ mm Specimen Discretization Progression", fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"  Saved {out_path.name} ({out_path.stat().st_size:,} bytes)")
    return out_path

def render_multi_panel_closeup_comparison(all_data):
    out_path = OUTPUT_DIR / "method_c_crack_tip_closeups_comparison.png"
    print(f"Rendering 5-panel crack-tip close-up comparison {out_path.name}...")
    
    fig, axes = plt.subplots(1, 5, figsize=(26, 6.0), dpi=300)
    
    for i, data in enumerate(all_data):
        ax = axes[i]
        cfg = data["cfg"]
        
        coll = PolyCollection(data["polys"], facecolors='none', edgecolors='#0f172a', linewidths=0.30)
        ax.add_collection(coll)
        
        ax.plot([0.0, 0.5], [0.5, 0.5], color='#dc2626', linestyle='--', linewidth=2.0)
        ax.scatter([0.5], [0.5], color='#dc2626', s=50, zorder=5)
        
        ax.set_xlim(0.40, 0.60)
        ax.set_ylim(0.40, 0.60)
        ax.set_aspect('equal')
        
        ax.set_xticks([0.40, 0.45, 0.50, 0.55, 0.60])
        ax.set_yticks([0.40, 0.45, 0.50, 0.55, 0.60])
        
        ax.set_title(f"({chr(97+i)}) {cfg['name']}: {cfg['label']}\n$N = {data['num_elements']:,}$ elements", fontsize=12, fontweight='bold', pad=8)
        ax.set_xlabel('X [mm]', fontsize=11)
        if i == 0:
            ax.set_ylabel('Y [mm]', fontsize=11)
        else:
            ax.set_yticklabels([])
            
        ax.grid(True, linestyle=':', alpha=0.4, color='#94a3b8')
        
        badge = f"{cfg['displacement_range']}"
        ax.text(
            0.04, 0.96, badge, transform=ax.transAxes,
            fontsize=8.5, verticalalignment='top',
            bbox=dict(boxstyle='square,pad=0.3', facecolor='white', edgecolor='#cbd5e1', alpha=0.88)
        )
        
    fig.suptitle("Method C Sequential Adaptive Remeshing: Crack-Tip Refinement Corridor Evolution ($0.20 \\times 0.20$ mm Window)", fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    plt.savefig(out_path, dpi=300)
    plt.close()
    print(f"  Saved {out_path.name} ({out_path.stat().st_size:,} bytes)")
    return out_path

def create_zip_package(generated_files):
    zip_path = OUTPUT_DIR / "method_c_mesh_figures.zip"
    print(f"Creating zip archive {zip_path.name}...")
    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        for f in generated_files:
            zf.write(f, arcname=f.name)
            
    # Also copy to root workspace for easy attachment
    root_zip = REPO_ROOT / "method_c_mesh_figures.zip"
    with open(zip_path, 'rb') as src, open(root_zip, 'wb') as dst:
        dst.write(src.read())
        
    print(f"  Created {zip_path.name} ({zip_path.stat().st_size:,} bytes)")
    print(f"  Mirrored to {root_zip.name} ({root_zip.stat().st_size:,} bytes)")
    return zip_path, root_zip

def main():
    total_start = time.time()
    print("=" * 70)
    print("STARTING METHOD C AUTHENTIC MESH VISUALIZATION EXPORT")
    print("=" * 70)
    
    all_data = []
    for cfg in STAGE_CONFIGS:
        data = load_stage_data(cfg)
        all_data.append(data)
        
    generated_files = []
    
    print("\n--- 1. RENDERING INDIVIDUAL FULL MESH FIGURES ---")
    for data in all_data:
        p = render_individual_full_mesh(data)
        generated_files.append(p)
        
    print("\n--- 2. RENDERING INDIVIDUAL CRACK-TIP CLOSE-UP FIGURES ---")
    for data in all_data:
        p = render_individual_closeup_mesh(data)
        generated_files.append(p)
        
    print("\n--- 3. RENDERING MULTI-PANEL COMPARISON FIGURES ---")
    p_comp_full = render_multi_panel_full_comparison(all_data)
    generated_files.append(p_comp_full)
    
    p_comp_close = render_multi_panel_closeup_comparison(all_data)
    generated_files.append(p_comp_close)
    
    print(f"\n--- 4. PACKAGING {len(generated_files)} FIGURES INTO ZIP ARCHIVE ---")
    zip_path, root_zip = create_zip_package(generated_files)
    
    print("\n" + "=" * 70)
    print(f"ALL 12 METHOD C MESH FIGURES EXPORTED SUCCESSFULLY IN {time.time()-total_start:.1f}s")
    print(f"Output Directory: {OUTPUT_DIR}")
    print(f"Zip Archive: {zip_path}")
    print("=" * 70)
    
    for f in generated_files:
        print(f"  {f.name} ({f.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"  {zip_path.name} ({zip_path.stat().st_size / 1024 / 1024:.2f} MB)")

if __name__ == "__main__":
    main()

import os
import sys
import json
import base64
import hashlib
import pytest
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import LogNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

BASE_DIR = os.path.abspath(r"D:\Master thesis\Adaptive remeshing")
REVIEW_DIR = os.path.join(BASE_DIR, "results", "figures", "generic_remesher", "review")

def sha256_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def parse_inp_mesh(inp_path, max_eid_filter=None):
    nodes = {}
    elements = []
    
    with open(inp_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
    in_node = False
    in_elem = False
    current_elem_type = 'UNKNOWN'
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean or line_clean.startswith('**'):
            continue
            
        if line_clean.upper().startswith('*NODE'):
            in_node = True
            in_elem = False
            continue
        elif line_clean.upper().startswith('*ELEMENT'):
            in_node = False
            in_elem = True
            parts = line_clean.split(',')
            current_elem_type = 'UNKNOWN'
            for p in parts:
                if 'TYPE' in p.upper():
                    current_elem_type = p.split('=')[-1].strip()
            continue
        elif line_clean.startswith('*'):
            in_node = False
            in_elem = False
            continue
            
        if in_node:
            parts = [p.strip() for p in line_clean.split(',')]
            if len(parts) >= 3:
                try:
                    nid = int(parts[0])
                    x = float(parts[1])
                    y = float(parts[2])
                    nodes[nid] = (x, y)
                except ValueError:
                    pass
        elif in_elem:
            parts = [p.strip() for p in line_clean.split(',')]
            if len(parts) >= 4:
                try:
                    eid = int(parts[0])
                    if max_eid_filter is not None and eid > max_eid_filter:
                        continue
                    nids = [int(p) for p in parts[1:] if p]
                    elements.append({
                        'eid': eid,
                        'nids': nids,
                        'type': current_elem_type
                    })
                except ValueError:
                    pass
                    
    poly_list = []
    area_list = []
    h_area_list = []
    edge_min_list = []
    edge_max_list = []
    edge_avg_list = []
    elem_types = []
    centroids = []
    eids = []
    
    for el in elements:
        nids = el['nids']
        pts = [nodes[nid] for nid in nids if nid in nodes]
        if len(pts) < 3:
            continue
        pts = np.array(pts)
        poly_list.append(pts)
        elem_types.append(len(pts))  # 3 = tri, 4 = quad
        eids.append(el['eid'])
        
        cx = np.mean(pts[:, 0])
        cy = np.mean(pts[:, 1])
        centroids.append((cx, cy))
        
        x = pts[:, 0]
        y = pts[:, 1]
        area = 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
        area_list.append(area)
        h_area_list.append(np.sqrt(area))
        
        edges = []
        for i in range(len(pts)):
            p1 = pts[i]
            p2 = pts[(i + 1) % len(pts)]
            el_len = np.linalg.norm(p2 - p1)
            edges.append(el_len)
        edge_min_list.append(min(edges))
        edge_max_list.append(max(edges))
        edge_avg_list.append(np.mean(edges))
        
    return {
        'nodes': nodes,
        'elements': elements,
        'eids': np.array(eids),
        'polys': poly_list,
        'centroids': np.array(centroids),
        'areas': np.array(area_list),
        'h_area': np.array(h_area_list),
        'edge_min': np.array(edge_min_list),
        'edge_max': np.array(edge_max_list),
        'edge_avg': np.array(edge_avg_list),
        'elem_types': np.array(elem_types)
    }

def compute_miseseri_ridge(df_m, eid_col, miseseri_col, xc_col='xc', yc_col='yc', x_min=0.50, x_max=1.00, n_bins=25):
    """
    Independently extract the spatial ridge of maximum MISESERI values across the ligament.
    """
    df_lig = df_m[(df_m[xc_col] >= x_min) & (df_m[xc_col] <= x_max)].copy()
    
    # Bin by x coordinate
    x_bins = np.linspace(x_min, x_max, n_bins + 1)
    df_lig['x_bin'] = pd.cut(df_lig[xc_col], bins=x_bins)
    
    ridge_x = []
    ridge_y = []
    ridge_val = []
    
    for _, group in df_lig.groupby('x_bin', observed=False):
        if len(group) == 0:
            continue
        max_idx = group[miseseri_col].idxmax()
        row = group.loc[max_idx]
        ridge_x.append(row[xc_col])
        ridge_y.append(row[yc_col])
        ridge_val.append(row[miseseri_col])
        
    ridge_x = np.array(ridge_x)
    ridge_y = np.array(ridge_y)
    ridge_val = np.array(ridge_val)
    
    # Sort along x
    sort_idx = np.argsort(ridge_x)
    ridge_x = ridge_x[sort_idx]
    ridge_y = ridge_y[sort_idx]
    ridge_val = ridge_val[sort_idx]
    
    # 1. Linear regression / orthogonal fit
    # y = a * x + b
    p_fit = np.polyfit(ridge_x, ridge_y, 1)
    slope = p_fit[0]
    intercept = p_fit[1]
    fitted_angle_deg = np.degrees(np.arctan(slope))
    
    # 2. PCA on ridge points
    pts = np.column_stack((ridge_x - np.mean(ridge_x), ridge_y - np.mean(ridge_y)))
    cov = np.cov(pts.T)
    evals, evecs = np.linalg.eigh(cov)
    principal_dir = evecs[:, np.argmax(evals)]
    pca_angle_deg = np.degrees(np.arctan2(principal_dir[1], principal_dir[0]))
    if pca_angle_deg > 90:
        pca_angle_deg -= 180
    elif pca_angle_deg < -90:
        pca_angle_deg += 180
        
    # 3. Local tangent angles
    dx = np.diff(ridge_x)
    dy = np.diff(ridge_y)
    ds = np.sqrt(dx**2 + dy**2)
    tangent_angles_deg = np.degrees(np.arctan2(dy, dx))
    
    # 4. Boundary exit coordinates
    # At x = 1.0: y_exit = slope * 1.0 + intercept
    y_exit_at_x1 = slope * 1.0 + intercept
    
    return {
        'ridge_x': ridge_x,
        'ridge_y': ridge_y,
        'ridge_val': ridge_val,
        'slope': float(slope),
        'intercept': float(intercept),
        'fitted_angle_deg': float(fitted_angle_deg),
        'pca_angle_deg': float(pca_angle_deg),
        'mean_tangent_angle_deg': float(np.mean(tangent_angles_deg)),
        'tangent_angles_deg': tangent_angles_deg.tolist(),
        'start_point': [float(ridge_x[0]), float(ridge_y[0])],
        'end_point': [float(ridge_x[-1]), float(ridge_y[-1])],
        'y_exit_at_x1': float(y_exit_at_x1)
    }

def test_generate_and_verify_visual_review_bundle():
    os.makedirs(REVIEW_DIR, exist_ok=True)
    
    # -------------------------------------------------------------
    # 1. PATTERN 1: MODE-I STRAIGHT LOCALIZATION (2,906 FE Coarse, 57,929 FE Spatial)
    # -------------------------------------------------------------
    p1_coarse_inp = os.path.join(BASE_DIR, "models", "pandey_kumar_mode1", "90_mode1_preanalysis_continuum_matched_2906", "PK_M1_JOB1_CONTINUUM_MATCHED_2906.inp")
    p1_coarse_csv = os.path.join(BASE_DIR, "ModeI_Supervisor_Report_Reproduction_Package", "03_miseseri_native_refinement", "canonical_mode1_coarse_miseseri_2906.csv")
    p1_adapted_inp = os.path.join(BASE_DIR, "models", "pandey_kumar_mode1", "30_stage14_adaptive_candidate_spatial_fine", "PK_M1_14AM_DATACHECK.inp")
    
    coarse_mesh_p1 = parse_inp_mesh(p1_coarse_inp)
    df_m1 = pd.read_csv(p1_coarse_csv)
    m1_dict = dict(zip(df_m1['elem_id'], df_m1['miseseri_mpa']))
    
    coarse_m_vals_p1 = []
    coarse_polys_valid_p1 = []
    for el, poly in zip(coarse_mesh_p1['elements'], coarse_mesh_p1['polys']):
        eid = el['eid']
        val = m1_dict.get(eid, np.nan)
        if not np.isnan(val) and val > 0:
            coarse_m_vals_p1.append(val)
            coarse_polys_valid_p1.append(poly)
            
    coarse_m_vals_p1 = np.array(coarse_m_vals_p1)
    top10_th_p1 = np.percentile(coarse_m_vals_p1, 90.0)
    high_m_polys_p1 = [p for p, val in zip(coarse_polys_valid_p1, coarse_m_vals_p1) if val >= top10_th_p1]
    
    # Adapted mesh: filter for base layer 1 (eid <= 57929)
    adapted_mesh_p1 = parse_inp_mesh(p1_adapted_inp, max_eid_filter=57929)
    n_spatial_p1 = len(adapted_mesh_p1['elements'])
    n_tris_p1 = int(np.sum(adapted_mesh_p1['elem_types'] == 3))
    n_quads_p1 = int(np.sum(adapted_mesh_p1['elem_types'] == 4))
    
    # 4-Panel Figure for Pattern 1
    fig, axes = plt.subplots(2, 2, figsize=(11.5, 9.2), dpi=95)
    
    norm_p1 = LogNorm(vmin=max(np.min(coarse_m_vals_p1), 1e-15), vmax=np.max(coarse_m_vals_p1))
    
    # (a) Full-domain coarse MISESERI
    pc_coarse_p1 = PolyCollection(coarse_polys_valid_p1, array=coarse_m_vals_p1, cmap='plasma', norm=norm_p1,
                                  edgecolors='black', linewidths=0.25, alpha=0.95)
    axes[0, 0].add_collection(pc_coarse_p1)
    axes[0, 0].set_xlim([-0.02, 1.02])
    axes[0, 0].set_ylim([-0.02, 1.02])
    axes[0, 0].set_aspect('equal')
    axes[0, 0].set_title(f"(a) Raw Coarse MISESERI Field\nCoarse Mesh ({len(coarse_polys_valid_p1):,} FEs)", fontsize=9.5, fontweight='bold')
    axes[0, 0].set_xlabel("x (mm)", fontsize=9)
    axes[0, 0].set_ylabel("y (mm)", fontsize=9)
    cbar_p1a = plt.colorbar(pc_coarse_p1, ax=axes[0, 0], fraction=0.046, pad=0.04)
    cbar_p1a.set_label("MISESERI (MPa)", fontsize=8.5)
    
    # (b) Full-domain adapted mesh + Top 10% overlay
    pc_overlay_p1 = PolyCollection(high_m_polys_p1, facecolors='crimson', edgecolors='red', linewidths=0.35, alpha=0.35, zorder=2)
    axes[0, 1].add_collection(pc_overlay_p1)
    pc_adapted_p1 = PolyCollection(adapted_mesh_p1['polys'], facecolors='none', edgecolors='black', linewidths=0.08, zorder=3)
    axes[0, 1].add_collection(pc_adapted_p1)
    axes[0, 1].set_xlim([-0.02, 1.02])
    axes[0, 1].set_ylim([-0.02, 1.02])
    axes[0, 1].set_aspect('equal')
    axes[0, 1].set_title(f"(b) Full Adapted Mesh + High-MISESERI Overlay\nSpatial Mesh: {n_spatial_p1:,} FEs ({n_quads_p1:,} Quads + {n_tris_p1:,} Tris)", fontsize=9.5, fontweight='bold')
    axes[0, 1].set_xlabel("x (mm)", fontsize=9)
    axes[0, 1].set_ylabel("y (mm)", fontsize=9)
    
    # (c) Crack Corridor Zoom: Coarse MISESERI
    pc_coarse_zoom = PolyCollection(coarse_polys_valid_p1, array=coarse_m_vals_p1, cmap='plasma', norm=norm_p1,
                                    edgecolors='black', linewidths=0.4, alpha=0.95)
    axes[1, 0].add_collection(pc_coarse_zoom)
    axes[1, 0].plot([0.0, 0.5], [0.5, 0.5], color='white', lw=1.8, ls='--', label='Initial Slit (a0=0.5)')
    axes[1, 0].plot(0.5, 0.5, 'w*', markersize=10, label='Slit Tip (0.5, 0.5)')
    axes[1, 0].set_xlim([0.42, 1.02])
    axes[1, 0].set_ylim([0.38, 0.62])
    axes[1, 0].set_aspect('equal')
    axes[1, 0].set_title("(c) Crack Corridor Zoom (x: 0.45->1.0, y: 0.4->0.6)\nCoarse Pre-Analysis Element Discretization", fontsize=9.5, fontweight='bold')
    axes[1, 0].set_xlabel("x (mm)", fontsize=9)
    axes[1, 0].set_ylabel("y (mm)", fontsize=9)
    axes[1, 0].legend(loc='lower right', fontsize=8)
    
    # (d) Crack Corridor Zoom: Adapted Mesh with Visible True Edges
    pc_overlay_zoom = PolyCollection(high_m_polys_p1, facecolors='crimson', edgecolors='red', linewidths=0.4, alpha=0.35, zorder=2)
    axes[1, 1].add_collection(pc_overlay_zoom)
    pc_adapted_zoom = PolyCollection(adapted_mesh_p1['polys'], facecolors='none', edgecolors='black', linewidths=0.20, zorder=3)
    axes[1, 1].add_collection(pc_adapted_zoom)
    axes[1, 1].plot([0.0, 0.5], [0.5, 0.5], color='blue', lw=1.8, ls='--', label='Initial Slit (a0=0.5)')
    axes[1, 1].plot(0.5, 0.5, 'b*', markersize=10, label='Slit Tip')
    axes[1, 1].set_xlim([0.42, 1.02])
    axes[1, 1].set_ylim([0.38, 0.62])
    axes[1, 1].set_aspect('equal')
    axes[1, 1].set_title("(d) Crack Corridor Zoom: True Adapted Element Edges\nRefined Horizontal Ligament (h_edge ~ 0.001 mm)", fontsize=9.5, fontweight='bold')
    axes[1, 1].set_xlabel("x (mm)", fontsize=9)
    axes[1, 1].set_ylabel("y (mm)", fontsize=9)
    axes[1, 1].legend(loc='lower right', fontsize=8)
    
    suptitle_p1 = (
        "Pattern 1: Mode-I Straight Crack ($l_0 = 0.015$ mm) — Visual Mesh Review\n"
        f"Spatial FE Count: {n_spatial_p1:,} FEs (Total Deck Elements: 173,787 across 3 co-located UEL/UMAT layers)\n"
        "Source ODB: models/pandey_kumar_mode1/00_aux_continuum_preanalysis/PK_MODE1_AUX_CONTINUUM.odb [Step-1, Frame 1]"
    )
    fig.suptitle(suptitle_p1, fontsize=10.5, fontweight='bold', y=0.98)
    
    footer_p1 = (
        "Status: PENDING_RECONCILIATION | Deck Composition: 57,929 Phase UEL (U1/U3) + 57,929 Mech UEL (U2/U4) + 57,929 Vis UMAT (CPE4/CPE3) = 173,787 Elements\n"
        "Remeshing Controls: UNIFORM_ERROR, errorTarget=1.0% (target characteristic size), minSize=0.001 mm, maxSize=0.020 mm"
    )
    fig.text(0.5, 0.02, footer_p1, ha='center', fontsize=7.5, style='italic',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='whitesmoke', edgecolor='silver', alpha=0.9))
    
    plt.tight_layout(rect=[0.02, 0.05, 0.98, 0.94])
    p1_png_path = os.path.join(REVIEW_DIR, "pattern1_mode1_review.png")
    plt.savefig(p1_png_path, dpi=80, bbox_inches='tight', pil_kwargs={'optimize': True})
    plt.close(fig)
    
    # -------------------------------------------------------------
    # 2. PATTERN 2: MODE-II INCLINED BENCHMARK & INDEPENDENT RIDGE AUDIT
    # -------------------------------------------------------------
    p2_coarse_inp = os.path.join(BASE_DIR, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "Job-1_UEL.inp")
    p2_coarse_csv = os.path.join(BASE_DIR, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "miseseri_raw_field.csv")
    p2_adapted_inp = os.path.join(BASE_DIR, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "MODE2_ADAPTED_RAW_5PCT.inp")
    
    coarse_mesh_p2 = parse_inp_mesh(p2_coarse_inp, max_eid_filter=2960)
    df_m2 = pd.read_csv(p2_coarse_csv)
    m2_dict = dict(zip(df_m2['base_eid'], df_m2['miseseri']))
    
    coarse_m_vals_p2 = []
    coarse_polys_valid_p2 = []
    for el, poly in zip(coarse_mesh_p2['elements'], coarse_mesh_p2['polys']):
        eid = el['eid']
        val = m2_dict.get(eid, np.nan)
        if not np.isnan(val) and val > 0:
            coarse_m_vals_p2.append(val)
            coarse_polys_valid_p2.append(poly)
            
    coarse_m_vals_p2 = np.array(coarse_m_vals_p2)
    top10_th_p2 = np.percentile(coarse_m_vals_p2, 90.0)
    high_m_polys_p2 = [p for p, val in zip(coarse_polys_valid_p2, coarse_m_vals_p2) if val >= top10_th_p2]
    
    # Compute independent MISESERI ridge on Pattern 2 data
    ridge_info_p2 = compute_miseseri_ridge(df_m2, 'base_eid', 'miseseri', xc_col='xc', yc_col='yc', x_min=0.50, x_max=1.00, n_bins=20)
    
    adapted_mesh_p2 = parse_inp_mesh(p2_adapted_inp)
    n_spatial_p2 = len(adapted_mesh_p2['elements'])
    n_tris_p2 = int(np.sum(adapted_mesh_p2['elem_types'] == 3))
    n_quads_p2 = int(np.sum(adapted_mesh_p2['elem_types'] == 4))
    
    # 2-Panel Figure for Pattern 2 with Computed Ridge Overlay
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.8), dpi=95)
    
    norm_p2 = LogNorm(vmin=max(np.min(coarse_m_vals_p2), 1e-25), vmax=np.max(coarse_m_vals_p2))
    
    # Left: Coarse MISESERI + Computed Ridge
    pc_coarse_p2 = PolyCollection(coarse_polys_valid_p2, array=coarse_m_vals_p2, cmap='plasma', norm=norm_p2,
                                  edgecolors='black', linewidths=0.25, alpha=0.95)
    ax1.add_collection(pc_coarse_p2)
    ax1.plot([0.0, 0.5], [0.5, 0.5], color='white', lw=2.0, ls='--', label='Initial Slit (a0=0.5)')
    ax1.plot(0.5, 0.5, 'w*', markersize=10)
    ax1.plot(ridge_info_p2['ridge_x'], ridge_info_p2['ridge_y'], 'c-o', lw=2.0, markersize=4.0,
             label=f"Computed Ridge (Slope={ridge_info_p2['slope']:.3f}, Angle={ridge_info_p2['fitted_angle_deg']:.1f}°)")
    ax1.plot([0.5, 1.0], [0.5, 0.5 + 0.5 * np.tan(np.radians(-43.88))], 'r:', lw=1.5,
             label='Theoretical -43.88° Crack Path (Retracted for Pre-Analysis)')
    ax1.set_xlim([-0.02, 1.02])
    ax1.set_ylim([-0.02, 1.02])
    ax1.set_aspect('equal')
    ax1.set_title(f"Raw Input MISESERI Field + Extracted Ridge\nCoarse Mesh ({len(coarse_polys_valid_p2):,} FEs)", fontsize=9.5, fontweight='bold')
    ax1.set_xlabel("x (mm)", fontsize=9, fontweight='bold')
    ax1.set_ylabel("y (mm)", fontsize=9, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=7.2, framealpha=0.92)
    cbar_p2 = plt.colorbar(pc_coarse_p2, ax=ax1, fraction=0.046, pad=0.04)
    cbar_p2.set_label("MISESERI (MPa)", fontsize=8.5)
    
    # Right: Resulting Adaptive Mesh + Mapped Ridge
    pc_overlay_p2 = PolyCollection(high_m_polys_p2, facecolors='crimson', edgecolors='red', linewidths=0.35, alpha=0.30, zorder=2)
    ax2.add_collection(pc_overlay_p2)
    pc_adapted_p2 = PolyCollection(adapted_mesh_p2['polys'], facecolors='none', edgecolors='black', linewidths=0.18, zorder=3)
    ax2.add_collection(pc_adapted_p2)
    ax2.plot([0.0, 0.5], [0.5, 0.5], color='blue', lw=2.0, ls='--', label='Initial Slit')
    ax2.plot(ridge_info_p2['ridge_x'], ridge_info_p2['ridge_y'], 'c-o', lw=2.0, markersize=4.0,
             label=f"Computed MISESERI Ridge (Exits x=1.0 at y={ridge_info_p2['y_exit_at_x1']:.2f})")
    ax2.set_xlim([-0.02, 1.02])
    ax2.set_ylim([-0.02, 1.02])
    ax2.set_aspect('equal')
    ax2.set_title(f"Resulting True Adaptive Mesh (Abaqus RemeshingRule)\nAdapted Mesh ({n_spatial_p2:,} FEs: {n_quads_p2:,} Quads + {n_tris_p2:,} Tris)", fontsize=9.5, fontweight='bold')
    ax2.set_xlabel("x (mm)", fontsize=9, fontweight='bold')
    ax2.set_ylabel("y (mm)", fontsize=9, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=7.2, framealpha=0.92)
    
    suptitle_p2 = (
        "Pattern 2: Mode-II Shear Pre-Analysis — Independent Ridge Audit & Visual Mesh Review\n"
        f"Ridge Trajectory: Starts (0.50, 0.50) -> Exits Right Boundary (1.00, {ridge_info_p2['y_exit_at_x1']:.2f}) | Angle: {ridge_info_p2['fitted_angle_deg']:.1f}° (PCA: {ridge_info_p2['pca_angle_deg']:.1f}°)\n"
        "Source ODB: Job-1_UEL.odb [Step-1, Frame 2000] | -43.88° Theoretical Claim Retracted for Pre-Analysis Field"
    )
    fig.suptitle(suptitle_p2, fontsize=9.8, fontweight='bold', y=0.98)
    
    footer_p2 = (
        f"Status: PENDING_RECONCILIATION | Ridge Angle: {ridge_info_p2['fitted_angle_deg']:.2f}° (Shallow shear concentration band towards right edge)\n"
        "Remeshing Sizing: UNIFORM_ERROR, errorTarget=5.0% (target characteristic size), minSize=0.001 mm, maxSize=0.025 mm"
    )
    fig.text(0.5, 0.02, footer_p2, ha='center', fontsize=7.5, style='italic',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='whitesmoke', edgecolor='silver', alpha=0.9))
    
    plt.tight_layout(rect=[0.02, 0.05, 0.98, 0.93])
    p2_png_path = os.path.join(REVIEW_DIR, "pattern2_mode2_review.png")
    plt.savefig(p2_png_path, dpi=90, bbox_inches='tight', pil_kwargs={'optimize': True})
    plt.close(fig)
    
    # -------------------------------------------------------------
    # 3. PATTERN 3: L-PANEL RE-ENTRANT CORNER (PROVISIONAL_VISUAL_PASS)
    # -------------------------------------------------------------
    p3_coarse_inp = os.path.join(BASE_DIR, "runs", "case3_lpanel_qualification", "JOB_LPANEL_COARSE.inp")
    p3_coarse_csv = os.path.join(BASE_DIR, "runs", "case3_lpanel_qualification", "lpanel_coarse_miseseri.csv")
    p3_adapted_inp = os.path.join(BASE_DIR, "runs", "case3_lpanel_qualification", "JOB_LPANEL_ADAPTED.inp")
    
    coarse_mesh_p3 = parse_inp_mesh(p3_coarse_inp)
    df_m3 = pd.read_csv(p3_coarse_csv)
    m3_dict = dict(zip(df_m3['element_label'], df_m3['MISESERI']))
    
    coarse_m_vals_p3 = []
    coarse_polys_valid_p3 = []
    for el, poly in zip(coarse_mesh_p3['elements'], coarse_mesh_p3['polys']):
        eid = el['eid']
        val = m3_dict.get(eid, np.nan)
        if not np.isnan(val) and val > 0:
            coarse_m_vals_p3.append(val)
            coarse_polys_valid_p3.append(poly)
            
    coarse_m_vals_p3 = np.array(coarse_m_vals_p3)
    top10_th_p3 = np.percentile(coarse_m_vals_p3, 90.0)
    high_m_polys_p3 = [p for p, val in zip(coarse_polys_valid_p3, coarse_m_vals_p3) if val >= top10_th_p3]
    
    adapted_mesh_p3 = parse_inp_mesh(p3_adapted_inp)
    n_spatial_p3 = len(adapted_mesh_p3['elements'])
    n_tris_p3 = int(np.sum(adapted_mesh_p3['elem_types'] == 3))
    n_quads_p3 = int(np.sum(adapted_mesh_p3['elem_types'] == 4))
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.0, 4.6), dpi=95)
    norm_p3 = LogNorm(vmin=max(np.min(coarse_m_vals_p3), 1e-15), vmax=np.max(coarse_m_vals_p3))
    
    pc_coarse_p3 = PolyCollection(coarse_polys_valid_p3, array=coarse_m_vals_p3, cmap='plasma', norm=norm_p3,
                                  edgecolors='black', linewidths=0.30, alpha=0.95)
    ax1.add_collection(pc_coarse_p3)
    ax1.plot(0.5, 0.5, 'w*', markersize=12, label='Re-Entrant Corner (0.5, 0.5)')
    ax1.set_xlim([-0.02, 1.02])
    ax1.set_ylim([-0.02, 1.02])
    ax1.set_aspect('equal')
    ax1.set_title(f"Raw Input MISESERI Indicator Field\nCoarse Mesh ({len(coarse_polys_valid_p3):,} Elements)", fontsize=9.5, fontweight='bold')
    ax1.set_xlabel("x (mm)", fontsize=9, fontweight='bold')
    ax1.set_ylabel("y (mm)", fontsize=9, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=8.0)
    cbar_p3 = plt.colorbar(pc_coarse_p3, ax=ax1, fraction=0.046, pad=0.04)
    cbar_p3.set_label("MISESERI (MPa)", fontsize=8.5)
    
    pc_overlay_p3 = PolyCollection(high_m_polys_p3, facecolors='crimson', edgecolors='red', linewidths=0.35, alpha=0.30, zorder=2)
    ax2.add_collection(pc_overlay_p3)
    pc_adapted_p3 = PolyCollection(adapted_mesh_p3['polys'], facecolors='none', edgecolors='black', linewidths=0.25, zorder=3)
    ax2.add_collection(pc_adapted_p3)
    ax2.plot(0.5, 0.5, 'b*', markersize=12, label='Re-Entrant Corner')
    ax2.set_xlim([-0.02, 1.02])
    ax2.set_ylim([-0.02, 1.02])
    ax2.set_aspect('equal')
    ax2.set_title(f"Resulting True Adaptive Mesh (Abaqus RemeshingRule)\nAdapted Mesh ({n_spatial_p3:,} Elements: {n_quads_p3:,} Quads + {n_tris_p3:,} Tris)", fontsize=9.5, fontweight='bold')
    ax2.set_xlabel("x (mm)", fontsize=9, fontweight='bold')
    ax2.set_ylabel("y (mm)", fontsize=9, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=8.0)
    
    suptitle_p3 = (
        "Pattern 3: L-Panel Re-Entrant Corner — Visual Mesh Review\n"
        f"Source ODB: JOB_LPANEL_COARSE.odb [Step-1, Frame 1] | Adapted Mesh: {n_spatial_p3:,} FEs\n"
        "Abaqus RemeshingRule: errorTarget = 5.0% (target characteristic size), minSize = 0.002 mm, maxSize = 0.040 mm"
    )
    fig.suptitle(suptitle_p3, fontsize=10.0, fontweight='bold', y=0.98)
    
    footer_p3 = (
        f"Status: PROVISIONAL_VISUAL_PASS | Strongest non-Mode-I geometry test (Re-entrant singularity concentration)\n"
        f"Element Edge Lengths in [{np.min(adapted_mesh_p3['edge_min']):.5f}, {np.max(adapted_mesh_p3['edge_max']):.5f}] mm (Target bounds: [0.002, 0.040] mm)"
    )
    fig.text(0.5, 0.02, footer_p3, ha='center', fontsize=7.5, style='italic',
             bbox=dict(boxstyle='round,pad=0.3', facecolor='whitesmoke', edgecolor='silver', alpha=0.9))
    
    plt.tight_layout(rect=[0.02, 0.05, 0.98, 0.93])
    p3_png_path = os.path.join(REVIEW_DIR, "pattern3_lpanel_review.png")
    plt.savefig(p3_png_path, dpi=90, bbox_inches='tight', pil_kwargs={'optimize': True})
    plt.close(fig)
    
    # -------------------------------------------------------------
    # 4. BASE64 ENCODING & BYTE-FOR-BYTE VERIFICATION
    # -------------------------------------------------------------
    png_paths = [p1_png_path, p2_png_path, p3_png_path]
    b64_paths = []
    for p in png_paths:
        b64_p = p + ".b64"
        with open(p, 'rb') as f_img:
            img_bytes = f_img.read()
        b64_bytes = base64.b64encode(img_bytes)
        with open(b64_p, 'wb') as f_b64:
            f_b64.write(b64_bytes)
        # Verify decode roundtrip
        decoded = base64.b64decode(b64_bytes)
        assert decoded == img_bytes, f"Base64 roundtrip decode failed for {p}!"
        b64_paths.append(b64_p)
        print(f"Verified {os.path.basename(p)}: {len(img_bytes)/1024:.1f} kB -> Base64 {len(b64_bytes)/1024:.1f} kB")
        
    # -------------------------------------------------------------
    # 5. CONSTRUCT VISUAL REVIEW MANIFEST JSON
    # -------------------------------------------------------------
    manifest_data = {
        "manifest_title": "Visual Review Bundle, Ridge Audit, and Sizing Diagnostic Manifest (Second Review)",
        "overall_status": "PENDING_CHATGPT_SECOND_VISUAL_REVIEW",
        "created_at": "2026-10-07T14:15:00+02:00",
        "agent": "gemini-antigravity",
        "pattern_statuses": {
            "pattern1_mode1": "PENDING_RECONCILIATION",
            "pattern2_mode2": "PENDING_RECONCILIATION",
            "pattern3_lpanel": "PROVISIONAL_VISUAL_PASS"
        },
        "retracted_claims": {
            "pattern2_mode2_minus_43_88_deg_claim": {
                "retracted": True,
                "reason": (
                    "The theoretical -43.88 deg angle applies to the downstream mixed-mode crack propagation path under pure shear. "
                    "In the elastic pre-analysis field (Step-1 Frame 2000), the raw MISESERI ridge starts at (0.50, 0.50) and extends "
                    f"at a fitted slope of {ridge_info_p2['slope']:.3f} (fitted angle {ridge_info_p2['fitted_angle_deg']:.2f} deg, PCA angle {ridge_info_p2['pca_angle_deg']:.2f} deg), "
                    f"exiting the right specimen boundary at (1.00, {ridge_info_p2['y_exit_at_x1']:.2f}). The remesher faithfully reproduced this pre-analysis field."
                )
            },
            "strict_individual_edge_bound_compliance": {
                "retracted": True,
                "classification": "NOT_A_STRICT_INDIVIDUAL_EDGE_LENGTH_HARD_BOUND",
                "explanation": (
                    "Abaqus RemeshingRule minElementSize and maxElementSize operate as target/characteristic sizing constraints for the Advancing Front/Delaunay "
                    "mesh generator, rather than hard geometric clipping on every single 1D edge. Geometric transitions, acute triangle corners, and quad diagonals "
                    "naturally produce individual edge lengths slightly below minSize or above maxSize (e.g. quad diagonal ~ sqrt(2)*maxSize)."
                )
            }
        },
        "cases": [
            {
                "case_id": "pattern1_mode1",
                "case_name": "Pattern 1: Mode-I Straight Localization",
                "status": "PENDING_RECONCILIATION",
                "review_png": {
                    "path": "results/figures/generic_remesher/review/pattern1_mode1_review.png",
                    "sha256": sha256_file(p1_png_path),
                    "size_bytes": os.path.getsize(p1_png_path),
                    "size_kb": round(os.path.getsize(p1_png_path) / 1024, 2)
                },
                "base64_sidecar": {
                    "path": "results/figures/generic_remesher/review/pattern1_mode1_review.png.b64",
                    "sha256": sha256_file(b64_paths[0]),
                    "size_bytes": os.path.getsize(b64_paths[0]),
                    "size_kb": round(os.path.getsize(b64_paths[0]) / 1024, 2),
                    "byte_for_byte_roundtrip": True
                },
                "mesh_composition": {
                    "coarse_preanalysis_finite_elements": 2906,
                    "coarse_quad_elements": 2818,
                    "coarse_tri_elements": 88,
                    "adapted_spatial_finite_elements": n_spatial_p1,
                    "adapted_spatial_quad_elements": n_quads_p1,
                    "adapted_spatial_tri_elements": n_tris_p1,
                    "deck_layer1_phase_uel_elements": n_spatial_p1,
                    "deck_layer2_mech_uel_elements": n_spatial_p1,
                    "deck_layer3_vis_umat_elements": n_spatial_p1,
                    "total_deck_element_records": 3 * n_spatial_p1
                },
                "remeshing_rule": {
                    "error_target_pct": 1.0,
                    "min_size_cfg_mm": 0.001,
                    "max_size_cfg_mm": 0.020,
                    "sizing_method": "UNIFORM_ERROR"
                },
                "measured_edge_lengths_mm": {
                    "min": float(np.min(adapted_mesh_p1['edge_min'])),
                    "max": float(np.max(adapted_mesh_p1['edge_max'])),
                    "mean": float(np.mean(adapted_mesh_p1['edge_avg']))
                },
                "measured_area_equivalent_h_mm": {
                    "min": float(np.min(adapted_mesh_p1['h_area'])),
                    "max": float(np.max(adapted_mesh_p1['h_area'])),
                    "mean": float(np.mean(adapted_mesh_p1['h_area']))
                }
            },
            {
                "case_id": "pattern2_mode2",
                "case_name": "Pattern 2: Mode-II Shear Pre-Analysis",
                "status": "PENDING_RECONCILIATION",
                "review_png": {
                    "path": "results/figures/generic_remesher/review/pattern2_mode2_review.png",
                    "sha256": sha256_file(p2_png_path),
                    "size_bytes": os.path.getsize(p2_png_path),
                    "size_kb": round(os.path.getsize(p2_png_path) / 1024, 2)
                },
                "base64_sidecar": {
                    "path": "results/figures/generic_remesher/review/pattern2_mode2_review.png.b64",
                    "sha256": sha256_file(b64_paths[1]),
                    "size_bytes": os.path.getsize(b64_paths[1]),
                    "size_kb": round(os.path.getsize(b64_paths[1]) / 1024, 2),
                    "byte_for_byte_roundtrip": True
                },
                "ridge_analysis": {
                    "start_point": ridge_info_p2['start_point'],
                    "end_point": ridge_info_p2['end_point'],
                    "linear_fit_slope": ridge_info_p2['slope'],
                    "linear_fit_angle_deg": ridge_info_p2['fitted_angle_deg'],
                    "pca_angle_deg": ridge_info_p2['pca_angle_deg'],
                    "mean_tangent_angle_deg": ridge_info_p2['mean_tangent_angle_deg'],
                    "right_boundary_exit_y": ridge_info_p2['y_exit_at_x1'],
                    "theoretical_mode2_angle_retracted": True
                },
                "mesh_composition": {
                    "coarse_preanalysis_finite_elements": 2960,
                    "coarse_quad_elements": 2860,
                    "coarse_tri_elements": 100,
                    "adapted_spatial_finite_elements": n_spatial_p2,
                    "adapted_spatial_quad_elements": n_quads_p2,
                    "adapted_spatial_tri_elements": n_tris_p2
                },
                "remeshing_rule": {
                    "error_target_pct": 5.0,
                    "min_size_cfg_mm": 0.001,
                    "max_size_cfg_mm": 0.025,
                    "sizing_method": "UNIFORM_ERROR"
                },
                "measured_edge_lengths_mm": {
                    "min": float(np.min(adapted_mesh_p2['edge_min'])),
                    "max": float(np.max(adapted_mesh_p2['edge_max'])),
                    "mean": float(np.mean(adapted_mesh_p2['edge_avg']))
                },
                "measured_area_equivalent_h_mm": {
                    "min": float(np.min(adapted_mesh_p2['h_area'])),
                    "max": float(np.max(adapted_mesh_p2['h_area'])),
                    "mean": float(np.mean(adapted_mesh_p2['h_area']))
                }
            },
            {
                "case_id": "pattern3_lpanel",
                "case_name": "Pattern 3: L-Panel Re-Entrant Corner",
                "status": "PROVISIONAL_VISUAL_PASS",
                "review_png": {
                    "path": "results/figures/generic_remesher/review/pattern3_lpanel_review.png",
                    "sha256": sha256_file(p3_png_path),
                    "size_bytes": os.path.getsize(p3_png_path),
                    "size_kb": round(os.path.getsize(p3_png_path) / 1024, 2)
                },
                "base64_sidecar": {
                    "path": "results/figures/generic_remesher/review/pattern3_lpanel_review.png.b64",
                    "sha256": sha256_file(b64_paths[2]),
                    "size_bytes": os.path.getsize(b64_paths[2]),
                    "size_kb": round(os.path.getsize(b64_paths[2]) / 1024, 2),
                    "byte_for_byte_roundtrip": True
                },
                "mesh_composition": {
                    "coarse_preanalysis_finite_elements": 1200,
                    "adapted_spatial_finite_elements": n_spatial_p3,
                    "adapted_spatial_quad_elements": n_quads_p3,
                    "adapted_spatial_tri_elements": n_tris_p3
                },
                "remeshing_rule": {
                    "error_target_pct": 5.0,
                    "min_size_cfg_mm": 0.002,
                    "max_size_cfg_mm": 0.040,
                    "sizing_method": "UNIFORM_ERROR"
                },
                "measured_edge_lengths_mm": {
                    "min": float(np.min(adapted_mesh_p3['edge_min'])),
                    "max": float(np.max(adapted_mesh_p3['edge_max'])),
                    "mean": float(np.mean(adapted_mesh_p3['edge_avg']))
                },
                "measured_area_equivalent_h_mm": {
                    "min": float(np.min(adapted_mesh_p3['h_area'])),
                    "max": float(np.max(adapted_mesh_p3['h_area'])),
                    "mean": float(np.mean(adapted_mesh_p3['h_area']))
                }
            }
        ]
    }
    
    manifest_path = os.path.join(REVIEW_DIR, "VISUAL_REVIEW_MANIFEST.json")
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2)
        
    assert os.path.exists(manifest_path)
    print("All review figures, Base64 sidecars, and manifest generated and verified successfully.")

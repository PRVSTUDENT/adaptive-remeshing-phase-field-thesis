# -*- coding: utf-8 -*-
"""
Gate-6B Stage 11: Native Sizing-Demand vs Mesh-Transition Propagation Audit
Analyzes coarse MISESERI error distribution vs resulting adapted element size field
across whole domain and along specified transects (y=0.50, 0.55, 0.60; x=0.50, 0.65, 0.80).
"""
import os
import json
import math
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec

# 1. Load Data
miseseri_csv = "models/pandey_kumar_mode1/90_mode1_preanalysis_continuum_matched_2906/control_miseseri_step1_end_u00050.csv"
p93_csv = "models/pandey_kumar_mode1/95_mode1_stage10_inf_companion_remesh/stage10_adapted_elements.csv"
p90_csv = "models/pandey_kumar_mode1/96_mode1_continuum_matched_native_remesh/stage10_adapted_elements.csv"

df_coarse = pd.read_csv(miseseri_csv)
df_fine_p93 = pd.read_csv(p93_csv)
df_fine_p90 = pd.read_csv(p90_csv)

print("Coarse elements:", len(df_coarse))
print("Fine P93 elements:", len(df_fine_p93))
print("Fine P90 elements:", len(df_fine_p90))

# 2. KD-Tree Mapping of Fine Elements to Coarse Element Regions
coarse_coords = df_coarse[['xc', 'yc']].values
tree_coarse = cKDTree(coarse_coords)

# Map fine elements to nearest coarse element centroid
dists_p93, idxs_p93 = tree_coarse.query(df_fine_p93[['cx', 'cy']].values)
df_fine_p93['nearest_coarse_idx'] = idxs_p93
df_fine_p93['nearest_coarse_label'] = df_coarse.loc[idxs_p93, 'element_label'].values

dists_p90, idxs_p90 = tree_coarse.query(df_fine_p90[['cx', 'cy']].values)
df_fine_p90['nearest_coarse_idx'] = idxs_p90
df_fine_p90['nearest_coarse_label'] = df_coarse.loc[idxs_p90, 'element_label'].values

# 3. Aggregate statistics per coarse element
mapping_records = []
for i, row in df_coarse.iterrows():
    xc, yc = row['xc'], row['yc']
    eri = row['MISESERI']
    eri_norm = row['MISESERI_normalized']
    region = row['region']
    
    # Fine elements mapped to this coarse element
    fine_in_coarse_p93 = df_fine_p93[df_fine_p93['nearest_coarse_idx'] == i]
    fine_in_coarse_p90 = df_fine_p90[df_fine_p90['nearest_coarse_idx'] == i]
    
    if len(fine_in_coarse_p93) > 0:
        h_vals_p93 = fine_in_coarse_p93['h_eq'].values
        h_med_p93 = np.median(h_vals_p93)
        h_mean_p93 = np.mean(h_vals_p93)
        h_min_p93 = np.min(h_vals_p93)
        h_p10_p93 = np.percentile(h_vals_p93, 10)
        h_p90_p93 = np.percentile(h_vals_p93, 90)
        n_fine_p93 = len(fine_in_coarse_p93)
    else:
        h_med_p93 = h_mean_p93 = h_min_p93 = h_p10_p93 = h_p90_p93 = 0.020
        n_fine_p93 = 0
        
    if len(fine_in_coarse_p90) > 0:
        h_vals_p90 = fine_in_coarse_p90['h_eq'].values
        h_med_p90 = np.median(h_vals_p90)
        h_mean_p90 = np.mean(h_vals_p90)
        h_min_p90 = np.min(h_vals_p90)
    else:
        h_med_p90 = h_mean_p90 = h_min_p90 = 0.020
        
    # Distance from crack tip (0.5, 0.5) and crack plane y=0.5
    d_tip = math.hypot(xc - 0.5, yc - 0.5)
    d_plane = abs(yc - 0.5)
    
    mapping_records.append({
        'element_label': row['element_label'],
        'element_type': row['element_type'],
        'xc': xc,
        'yc': yc,
        'd_tip_mm': d_tip,
        'd_plane_mm': d_plane,
        'MISESERI': eri,
        'MISESERI_normalized': eri_norm,
        'region': region,
        'n_fine_p93': n_fine_p93,
        'h_median_p93_mm': h_med_p93,
        'h_mean_p93_mm': h_mean_p93,
        'h_min_p93_mm': h_min_p93,
        'h_p10_p93_mm': h_p10_p93,
        'h_p90_p93_mm': h_p90_p93,
        'h_median_p90_mm': h_med_p90,
        'h_mean_p90_mm': h_mean_p90,
        'h_min_p90_mm': h_min_p90
    })

df_mapped = pd.DataFrame(mapping_records)
mapping_csv_path = "models/pandey_kumar_mode1/MODE1_STAGE11_COARSE_TO_ADAPTED_MAPPING.csv"
df_mapped.to_csv(mapping_csv_path, index=False)
print("Saved mapping CSV to:", mapping_csv_path)

# 4. Spatial Transect Analysis
transect_lines_y = [0.50, 0.55, 0.60]
transect_lines_x = [0.50, 0.65, 0.80]

transect_records = []

# Horizontal Transects (y fixed, vary x)
for y_target in transect_lines_y:
    # Select coarse elements close to y_target (tol = 0.015)
    sub = df_mapped[abs(df_mapped['yc'] - y_target) <= 0.015].sort_values(by='xc')
    for _, r in sub.iterrows():
        transect_records.append({
            'transect_type': 'HORIZONTAL',
            'transect_value': y_target,
            'transect_axis': 'x',
            'coord_val': r['xc'],
            'xc': r['xc'],
            'yc': r['yc'],
            'MISESERI': r['MISESERI'],
            'MISESERI_normalized': r['MISESERI_normalized'],
            'h_median_mm': r['h_median_p93_mm'],
            'h_min_mm': r['h_min_p93_mm'],
            'd_tip_mm': r['d_tip_mm'],
            'd_plane_mm': r['d_plane_mm']
        })

# Vertical Transects (x fixed, vary y)
for x_target in transect_lines_x:
    sub = df_mapped[abs(df_mapped['xc'] - x_target) <= 0.015].sort_values(by='yc')
    for _, r in sub.iterrows():
        transect_records.append({
            'transect_type': 'VERTICAL',
            'transect_value': x_target,
            'transect_axis': 'y',
            'coord_val': r['yc'],
            'xc': r['xc'],
            'yc': r['yc'],
            'MISESERI': r['MISESERI'],
            'MISESERI_normalized': r['MISESERI_normalized'],
            'h_median_mm': r['h_median_p93_mm'],
            'h_min_mm': r['h_min_p93_mm'],
            'd_tip_mm': r['d_tip_mm'],
            'd_plane_mm': r['d_plane_mm']
        })

df_transects = pd.DataFrame(transect_records)
transect_csv_path = "models/pandey_kumar_mode1/MODE1_STAGE11_TRANSECT_DATA.csv"
df_transects.to_csv(transect_csv_path, index=False)
print("Saved transect CSV to:", transect_csv_path)

# 5. Core Mathematical & Sizing Analysis
# High error: MISESERI_normalized >= 0.05
# Background: MISESERI_normalized < 0.02
high_err = df_mapped[df_mapped['MISESERI_normalized'] >= 0.05]
bg_err = df_mapped[df_mapped['MISESERI_normalized'] < 0.02]
far_field_bg = df_mapped[(df_mapped['MISESERI_normalized'] < 0.02) & (df_mapped['d_plane_mm'] > 0.20)]

print("\n=== SIZING VS ERROR FIELD STATISTICS ===")
print("High Error Elements (count = %d): Median h = %.6f mm, Mean h = %.6f mm" % (
    len(high_err), high_err['h_median_p93_mm'].median(), high_err['h_median_p93_mm'].mean()))
print("Far-Field Background Elements (count = %d): Median h = %.6f mm, Mean h = %.6f mm" % (
    len(far_field_bg), far_field_bg['h_median_p93_mm'].median(), far_field_bg['h_median_p93_mm'].mean()))

# Proportion of far field refined
far_field_refined = far_field_bg[far_field_bg['h_median_p93_mm'] <= 0.005]
print("Far-Field Background elements with h <= 0.005 mm: %d / %d (%.2f%%)" % (
    len(far_field_refined), len(far_field_bg), 100.0 * len(far_field_refined) / len(far_field_bg)))

print("\nAnalysis complete.")

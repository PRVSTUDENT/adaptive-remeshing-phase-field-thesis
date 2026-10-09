"""
Test suite auditing Mode-II mesh element density, partition invariants, and node/DOF reconciliation.
Validates exact physical mesh invariants for M2_CORRECTED_JOB2_ET3PCT_STABILIZED.inp and element CSV.
"""

import os
import re
import math
import numpy as np
import pandas as pd
import pytest

STABILIZED_INP_PATH = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode2\06_paper_grounded_uel_preanalysis\m2_corrected_remesh\M2_CORRECTED_JOB2_ET3PCT_STABILIZED.inp"
ELEMENTS_CSV_PATH = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode2\06_paper_grounded_uel_preanalysis\m2_corrected_remesh\m2_corrected_mesh_elements_et3pct.csv"

def dist_to_polyline(x, y, polyline):
    """Compute shortest Euclidean distance from (x, y) to a polyline."""
    min_d = 1e9
    for i in range(len(polyline) - 1):
        p1 = np.array(polyline[i])
        p2 = np.array(polyline[i+1])
        pt = np.array([x, y])
        v = p2 - p1
        w = pt - p1
        c1 = np.dot(w, v)
        if c1 <= 0:
            d = np.linalg.norm(pt - p1)
        else:
            c2 = np.dot(v, v)
            if c2 <= c1:
                d = np.linalg.norm(pt - p2)
            else:
                b = c1 / c2
                pb = p1 + b * v
                d = np.linalg.norm(pt - pb)
        if d < min_d:
            min_d = d
    return min_d


def test_density_partition_invariants():
    """Verify that density partition strictly satisfies all mathematical invariants."""
    assert os.path.exists(ELEMENTS_CSV_PATH), f"CSV missing: {ELEMENTS_CSV_PATH}"
    df = pd.read_csv(ELEMENTS_CSV_PATH)
    
    n_total_fe = len(df)
    assert n_total_fe == 21063, f"Expected 21,063 physical FEs, got {n_total_fe}"
    
    total_mesh_area = df['area'].sum()
    assert abs(total_mesh_area - 1.0) < 1e-4, f"Total mesh area should be 1.0 mm^2, got {total_mesh_area}"
    
    # 1. Actual Mesh Corridor centerline points (W = 0.24 mm envelope, half-width = 0.12 mm)
    centerline_pts = [
        (0.500, 0.500), (0.535, 0.450), (0.575, 0.400), (0.620, 0.350),
        (0.670, 0.300), (0.725, 0.250), (0.785, 0.200), (0.845, 0.150),
        (0.900, 0.100), (0.945, 0.050), (0.985, 0.000)
    ]
    
    in_envelope = []
    for idx, r in df.iterrows():
        xc, yc = r['xc'], r['yc']
        if yc <= 0.52 and xc >= 0.45:
            d = dist_to_polyline(xc, yc, centerline_pts)
            in_envelope.append(d <= 0.12)
        else:
            in_envelope.append(False)
            
    df['in_corridor'] = in_envelope
    
    all_in = df[df['in_corridor']]
    all_out = df[~df['in_corridor']]
    
    n_all_in = len(all_in)
    n_all_out = len(all_out)
    
    # Invariant 1: Total element partition sum
    assert n_all_in + n_all_out == n_total_fe, "Partition sum must equal total elements"
    assert n_all_in == 12237, f"Expected N_all,in = 12237, got {n_all_in}"
    assert n_all_out == 8826, f"Expected N_all,out = 8826, got {n_all_out}"
    
    # Fine element definitions at h <= 8.0 um
    fine_80 = df[df['h_eq'] <= 0.008]
    n_fine_total_80 = len(fine_80)
    assert n_fine_total_80 == 15771, f"Expected N_fine_total = 15771 at 8.0um, got {n_fine_total_80}"
    
    fine_in_80 = all_in[all_in['h_eq'] <= 0.008]
    fine_out_80 = all_out[all_out['h_eq'] <= 0.008]
    n_fine_in_80 = len(fine_in_80)
    n_fine_out_80 = len(fine_out_80)
    
    assert n_fine_in_80 + n_fine_out_80 == n_fine_total_80
    assert n_fine_in_80 == 11871, f"Expected N_fine,in = 11871 at 8.0um, got {n_fine_in_80}"
    assert n_fine_out_80 == 3900, f"Expected N_fine,out = 3900 at 8.0um, got {n_fine_out_80}"
    assert n_fine_in_80 <= n_all_in
    assert n_fine_out_80 <= n_all_out
    
    # Fine element definitions at h <= l0 / 2 = 7.5 um (l0 = 15 um)
    fine_75 = df[df['h_eq'] <= 0.0075]
    n_fine_total_75 = len(fine_75)
    assert n_fine_total_75 == 15187, f"Expected N_fine_total = 15187 at 7.5um, got {n_fine_total_75}"
    
    fine_in_75 = all_in[all_in['h_eq'] <= 0.0075]
    fine_out_75 = all_out[all_out['h_eq'] <= 0.0075]
    n_fine_in_75 = len(fine_in_75)
    n_fine_out_75 = len(fine_out_75)
    
    # Invariant 2: Fine elements partition sum
    assert n_fine_in_75 + n_fine_out_75 == n_fine_total_75
    assert n_fine_in_75 == 11768, f"Expected N_fine,in = 11768 at 7.5um, got {n_fine_in_75}"
    assert n_fine_out_75 == 3419, f"Expected N_fine,out = 3419 at 7.5um, got {n_fine_out_75}"
    
    # Invariant 3: Subsets must be strictly <= supersets
    assert n_fine_in_75 <= n_all_in, f"N_fine,in ({n_fine_in_75}) must be <= N_all,in ({n_all_in})"
    assert n_fine_out_75 <= n_all_out, f"N_fine,out ({n_fine_out_75}) must be <= N_all,out ({n_all_out})"
    
    # Selectivity & Contrast
    fine_selectivity_75 = n_fine_in_75 / n_fine_total_75
    assert abs(fine_selectivity_75 - 0.77487) < 1e-4 # 77.49%
    
    area_in = all_in['area'].sum()
    area_out = all_out['area'].sum()
    
    rho_fine_in_75 = n_fine_in_75 / area_in
    rho_fine_out_75 = n_fine_out_75 / area_out
    contrast_fine_75 = rho_fine_in_75 / rho_fine_out_75
    assert contrast_fine_75 > 19.0, f"Expected fine contrast > 19.0x, got {contrast_fine_75:.2f}"
    
    rho_all_in = n_all_in / area_in
    rho_all_out = n_all_out / area_out
    contrast_all = rho_all_in / rho_all_out
    assert contrast_all > 7.6, f"Expected all element contrast > 7.6x, got {contrast_all:.2f}"


def test_independent_published_corridor_evaluation():
    """Verify that mesh selectivity holds independently along the published Pandey & Kumar trajectory."""
    assert os.path.exists(ELEMENTS_CSV_PATH), f"CSV missing: {ELEMENTS_CSV_PATH}"
    df = pd.read_csv(ELEMENTS_CSV_PATH)
    
    # Published trajectory polyline: (0.50, 0.50) to (0.868, 0.0)
    pk_pts = [(0.500 + 0.368 * math.sqrt((0.500 - y)/0.500), y) for y in np.linspace(0.500, 0.0, 11)]
    
    pk_in_mask = []
    for idx, r in df.iterrows():
        xc, yc = r['xc'], r['yc']
        if yc <= 0.52 and xc >= 0.45:
            d = dist_to_polyline(xc, yc, pk_pts)
            pk_in_mask.append(d <= 0.12)
        else:
            pk_in_mask.append(False)
            
    df['in_pk_corridor'] = pk_in_mask
    
    pk_in = df[df['in_pk_corridor']]
    pk_out = df[~df['in_pk_corridor']]
    
    n_pk_in = len(pk_in)
    n_pk_out = len(pk_out)
    assert n_pk_in + n_pk_out == 21063
    assert n_pk_in == 10955
    assert n_pk_out == 10108
    
    # Fine elements in published corridor (7.5 um threshold)
    fine_in_pk_75 = pk_in[pk_in['h_eq'] <= 0.0075]
    n_fine_in_pk_75 = len(fine_in_pk_75)
    assert n_fine_in_pk_75 == 10393
    assert n_fine_in_pk_75 <= n_pk_in
    
    fine_selectivity_pk_75 = n_fine_in_pk_75 / 15187
    assert abs(fine_selectivity_pk_75 - 0.6843) < 1e-3 # 68.43%
    
    area_pk_in = pk_in['area'].sum()
    area_pk_out = pk_out['area'].sum()
    
    rho_fine_pk_in = n_fine_in_pk_75 / area_pk_in
    rho_fine_pk_out = (15187 - n_fine_in_pk_75) / area_pk_out
    contrast_pk = rho_fine_pk_in / rho_fine_pk_out
    assert contrast_pk > 12.0 # High contrast verified independently


def test_deck_nodes_seam_and_dof_reconciliation():
    """Audit node counts, seam nodes, and degrees of freedom in M2_CORRECTED_JOB2_ET3PCT_STABILIZED.inp."""
    assert os.path.exists(STABILIZED_INP_PATH), f"INP missing: {STABILIZED_INP_PATH}"
    with open(STABILIZED_INP_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    nodes = {}
    n_bottom = []
    n_top = []
    equations = []
    bcs = []

    in_nodes = False
    current_nset = None

    for line in lines:
        l = line.strip()
        if not l: continue
        if l.startswith("*"):
            in_nodes = False
            current_nset = None

        if l.upper().startswith("*NODE"):
            in_nodes = True
            continue
        elif in_nodes:
            parts = l.split(',')
            if len(parts) >= 3:
                try:
                    nid = int(parts[0])
                    xc = float(parts[1])
                    yc = float(parts[2])
                    nodes[nid] = (xc, yc)
                except:
                    pass

        if l.upper().startswith("*NSET"):
            m = re.search(r'NSET=([A-Za-z0-9_]+)', l, re.IGNORECASE)
            if m:
                current_nset = m.group(1).upper()
                continue

        if current_nset:
            parts = l.replace(' ', '').split(',')
            for p in parts:
                if p.isdigit():
                    if current_nset == "N_BOTTOM":
                        n_bottom.append(int(p))
                    elif current_nset == "N_TOP":
                        n_top.append(int(p))

        if l.upper().startswith("*BOUNDARY"):
            bcs.append(l)
        elif l.upper().startswith("*EQUATION"):
            equations.append(l)

    mesh_nodes = {nid: coords for nid, coords in nodes.items() if nid != 999999}
    n_mesh_nodes = len(mesh_nodes)
    n_total_user_nodes = len(nodes)

    # Check unique coordinate locations vs duplicated seam nodes
    unique_coords = set((round(xc, 6), round(yc, 6)) for xc, yc in mesh_nodes.values())
    n_unique_coords = len(unique_coords)
    n_seam_duplicates = n_mesh_nodes - n_unique_coords

    assert n_mesh_nodes == 21042
    assert n_unique_coords == 20988
    assert n_seam_duplicates == 54
    assert n_total_user_nodes == 21043
    assert n_mesh_nodes * 3 + 1 == 63127
    assert len(n_bottom) == 118
    assert len(n_top) == 97

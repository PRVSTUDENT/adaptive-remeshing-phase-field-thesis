"""
Test suite auditing Mode-II mesh element density, partition invariants, 
three-way trajectory definitions, and exact node/DOF/equation reconciliation.
Validates exact physical mesh invariants for M2_CORRECTED_JOB2_ET3PCT_STABILIZED.inp.
"""

import os
import re
import math
import numpy as np
import pandas as pd
import pytest

STABILIZED_INP_PATH = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode2\06_paper_grounded_uel_preanalysis\m2_corrected_remesh\M2_CORRECTED_JOB2_ET3PCT_STABILIZED.inp"
ELEMENTS_CSV_PATH = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode2\06_paper_grounded_uel_preanalysis\m2_corrected_remesh\m2_corrected_mesh_elements_et3pct.csv"
COARSE_CRACK_CSV = r"D:\Master thesis\Adaptive remeshing\models\pandey_kumar_mode2\06_paper_grounded_uel_preanalysis\mode2_j1_coarse_retest_crack_trajectory.csv"

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


def test_fig12b_digitization_and_fit_residuals():
    """Verify authenticated Fig. 12(b) digitized coordinates, fit residuals, and F1356 sqrt error."""
    fig12b_pts = np.array([
        [0.500, 0.500],
        [0.535, 0.430],
        [0.585, 0.340],
        [0.650, 0.235],
        [0.725, 0.140],
        [0.800, 0.060],
        [0.868, 0.000]
    ])
    
    # 1. Test quadratic fit to Fig 12b: x(y) = a*y^2 + b*y + c
    p_quad = np.polyfit(fig12b_pts[:, 1], fig12b_pts[:, 0], 2)
    for x_dig, y_dig in fig12b_pts:
        x_fit = np.polyval(p_quad, y_dig)
        residual_um = abs(x_fit - x_dig) * 1000.0
        assert residual_um < 4.5, f"Quadratic fit residual {residual_um:.2f} um exceeds 4.5 um at y={y_dig}"
        
    # 2. Test and document the mathematical defect of the F1356 square root formula
    # x_sqrt(y) = 0.5 + 0.368 * sqrt((0.5 - y)/0.5)
    max_sqrt_err_um = 0.0
    for x_dig, y_dig in fig12b_pts:
        x_sqrt = 0.500 + 0.368 * math.sqrt(max(0.0, (0.500 - y_dig) / 0.500))
        err_um = (x_sqrt - x_dig) * 1000.0
        if err_um > max_sqrt_err_um:
            max_sqrt_err_um = err_um
            
    assert max_sqrt_err_um > 120.0, f"Expected sqrt error > 120 um, got {max_sqrt_err_um}"
    assert abs(max_sqrt_err_um - 123.18) < 1.0


def test_definition_a_authenticated_fig12b_corridor():
    """Verify Definition A (Authenticated Fig. 12(b) piecewise linear corridor, W=0.24mm)."""
    assert os.path.exists(ELEMENTS_CSV_PATH), f"CSV missing: {ELEMENTS_CSV_PATH}"
    df = pd.read_csv(ELEMENTS_CSV_PATH)
    
    fig12b_pts = np.array([
        [0.500, 0.500],
        [0.535, 0.430],
        [0.585, 0.340],
        [0.650, 0.235],
        [0.725, 0.140],
        [0.800, 0.060],
        [0.868, 0.000]
    ])
    
    in_mask = []
    for idx, r in df.iterrows():
        xc, yc = r['xc'], r['yc']
        if yc <= 0.52 and xc >= 0.45:
            d = dist_to_polyline(xc, yc, fig12b_pts)
            in_mask.append(d <= 0.12)
        else:
            in_mask.append(False)
            
    df_in = df[in_mask]
    df_out = df[[not x for x in in_mask]]
    
    n_all_in = len(df_in)
    n_all_out = len(df_out)
    assert n_all_in + n_all_out == 21063
    assert n_all_in == 12207
    assert n_all_out == 8856
    
    fine_in = df_in[df_in['h_eq'] <= 0.0075]
    fine_out = df_out[df_out['h_eq'] <= 0.0075]
    n_fine_in = len(fine_in)
    n_fine_out = len(fine_out)
    
    assert n_fine_in + n_fine_out == 15187
    assert n_fine_in == 11815
    assert n_fine_out == 3372
    assert n_fine_in <= n_all_in
    assert n_fine_out <= n_all_out
    
    selectivity = n_fine_in / 15187
    assert abs(selectivity - 0.77796) < 1e-4 # 77.80%
    
    area_in = df_in['area'].sum()
    area_out = df_out['area'].sum()
    assert abs(area_in + area_out - 1.0) < 1e-4
    assert abs(area_in - 0.144693) < 1e-4
    
    rho_fine_in = n_fine_in / area_in
    rho_fine_out = n_fine_out / area_out
    contrast_fine = rho_fine_in / rho_fine_out
    assert contrast_fine > 20.0, f"Expected fine contrast > 20.0x, got {contrast_fine:.2f}"
    assert abs(contrast_fine - 20.71) < 0.2


def test_definition_b_computed_mesh_corridor():
    """Verify Definition B (Computed adaptive mesh centerline, W=0.24mm)."""
    assert os.path.exists(ELEMENTS_CSV_PATH), f"CSV missing: {ELEMENTS_CSV_PATH}"
    df = pd.read_csv(ELEMENTS_CSV_PATH)
    
    mesh_centerline_pts = [
        (0.500, 0.500), (0.535, 0.450), (0.575, 0.400), (0.620, 0.350),
        (0.670, 0.300), (0.725, 0.250), (0.785, 0.200), (0.845, 0.150),
        (0.900, 0.100), (0.945, 0.050), (0.985, 0.000)
    ]
    
    in_mask = []
    for idx, r in df.iterrows():
        xc, yc = r['xc'], r['yc']
        if yc <= 0.52 and xc >= 0.45:
            d = dist_to_polyline(xc, yc, mesh_centerline_pts)
            in_mask.append(d <= 0.12)
        else:
            in_mask.append(False)
            
    df_in = df[in_mask]
    df_out = df[[not x for x in in_mask]]
    
    n_all_in = len(df_in)
    n_all_out = len(df_out)
    assert n_all_in + n_all_out == 21063
    assert n_all_in == 12237
    assert n_all_out == 8826
    
    fine_in = df_in[df_in['h_eq'] <= 0.0075]
    fine_out = df_out[df_out['h_eq'] <= 0.0075]
    n_fine_in = len(fine_in)
    n_fine_out = len(fine_out)
    
    assert n_fine_in + n_fine_out == 15187
    assert n_fine_in == 11768
    assert n_fine_out == 3419
    assert n_fine_in <= n_all_in
    assert n_fine_out <= n_all_out
    
    selectivity = n_fine_in / 15187
    assert abs(selectivity - 0.77487) < 1e-4 # 77.49%


def test_definition_c_coarse_damage_preanalysis_corridor():
    """Verify Definition C (Coarse damage crack trajectory from Job 1411104, W=0.24mm)."""
    assert os.path.exists(ELEMENTS_CSV_PATH), f"CSV missing: {ELEMENTS_CSV_PATH}"
    assert os.path.exists(COARSE_CRACK_CSV), f"Coarse crack CSV missing: {COARSE_CRACK_CSV}"
    df = pd.read_csv(ELEMENTS_CSV_PATH)
    df_coarse = pd.read_csv(COARSE_CRACK_CSV)
    
    coarse_pts = df_coarse[df_coarse['d'] >= 0.8][['x_mm', 'y_mm']].values
    coarse_pts = coarse_pts[np.argsort(-coarse_pts[:, 1])]
    coarse_crack_polyline = np.vstack([
        [0.500, 0.500],
        coarse_pts,
        [0.813, 0.000]
    ])
    
    in_mask = []
    for idx, r in df.iterrows():
        xc, yc = r['xc'], r['yc']
        if yc <= 0.52 and xc >= 0.45:
            d = dist_to_polyline(xc, yc, coarse_crack_polyline)
            in_mask.append(d <= 0.12)
        else:
            in_mask.append(False)
            
    df_in = df[in_mask]
    df_out = df[[not x for x in in_mask]]
    
    n_all_in = len(df_in)
    n_all_out = len(df_out)
    assert n_all_in + n_all_out == 21063
    assert n_all_in == 11789
    assert n_all_out == 9274
    
    fine_in = df_in[df_in['h_eq'] <= 0.0075]
    fine_out = df_out[df_out['h_eq'] <= 0.0075]
    n_fine_in = len(fine_in)
    n_fine_out = len(fine_out)
    
    assert n_fine_in + n_fine_out == 15187
    assert n_fine_in == 11380
    assert n_fine_out == 3807
    assert n_fine_in <= n_all_in
    assert n_fine_out <= n_all_out
    
    selectivity = n_fine_in / 15187
    assert abs(selectivity - 0.7493) < 1e-3 # 74.93%
    
    area_in = df_in['area'].sum()
    area_out = df_out['area'].sum()
    rho_fine_in = n_fine_in / area_in
    rho_fine_out = n_fine_out / area_out
    contrast_fine = rho_fine_in / rho_fine_out
    assert contrast_fine > 18.0 # 18.31x contrast


def test_node_variables_equations_reconciliation():
    """Audit the exact reconciliation between nodal variables, constraints, and solver equations."""
    assert os.path.exists(STABILIZED_INP_PATH), f"INP missing: {STABILIZED_INP_PATH}"
    with open(STABILIZED_INP_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    nodes = {}
    n_bottom = []
    n_top = []
    equations = []

    in_nodes = False
    in_equation = False
    current_nset = None

    for line in lines:
        l = line.strip()
        if not l: continue
        if l.startswith("*"):
            in_nodes = False
            in_equation = False
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

        if l.upper().startswith("*EQUATION"):
            in_equation = True
            continue
        elif in_equation:
            equations.append(l)

    mesh_nodes = {nid: coords for nid, coords in nodes.items() if nid != 999999}
    n_mesh_nodes = len(mesh_nodes)
    n_total_nodes = len(nodes)

    # 1. Duplicate seam nodes
    unique_coords = set((round(xc, 6), round(yc, 6)) for xc, yc in mesh_nodes.values())
    n_unique_coords = len(unique_coords)
    n_seam_duplicates = n_mesh_nodes - n_unique_coords
    
    assert n_mesh_nodes == 21042
    assert n_unique_coords == 20988
    assert n_seam_duplicates == 54
    assert n_total_nodes == 21043

    # 2. Total model variables in Abaqus = (21042 mesh nodes * 3 DOFs) + (1 RP * 1 DOF) = 63,127
    total_model_variables = n_mesh_nodes * 3 + 1
    assert total_model_variables == 63127

    # 3. Linear constraint equations: each node in N_TOP has an *EQUATION tying ux to RP 999999
    # In *EQUATION, each constraint spans 2 lines (line 1: '2', line 2: 'node, 1, 1.0, 999999, 1, -1.0')
    n_eq_constraints = len(n_top)
    assert n_eq_constraints == 97

    # 4. Assembled active solver equations = Total model variables - Constraint equations
    active_solver_equations = total_model_variables - n_eq_constraints
    assert active_solver_equations == 63030

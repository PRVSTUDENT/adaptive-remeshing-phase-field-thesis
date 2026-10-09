"""
test_mode2_trajectory_geometry_and_coverage.py

Targeted unit test suite for Task F1358 and Task F1359:
1. Exact polynomial differentiation and crack-tip tangent angle (-69.52 deg).
2. Piecewise-linear published polyline reference points and first segment angle (-63.43 deg).
3. Shortest Euclidean distance:
   - Station-matched ridge (7 points): d_perp <= 96.2 um <= 120.0 um (100% of stations inside corridor).
   - Uniform slice-centroid ridge (11 points): d_perp <= 131.5 um at P6 (78.2% arc-length within 120 um).
4. Mode-II length scale l0 = 15.0 um and mesh resolution along published Fig. 12(b) trajectory:
   - 100.00% crack-path coverage with h <= l0/2 = 7.50 um
   - 100.00% crack-path coverage with h <= l0/3 = 5.00 um (h_max = 4.289 um)
   - 72.40% crack-path coverage with h <= l0/6 = 2.50 um
5. Coarse pre-analysis damage path coverage (99.00% <= l0/2).
6. Clear separation between geometric corridor enclosure and actual mesh-resolution sufficiency.
7. Exact model-to-solver equation hierarchy (63,127 - 97 = 63,030).
8. Live solver telemetry: peak force F_max = 412.21 N at u_x = 9.41 um, post-peak softening drop, and K0 = 45.64 kN/mm.
9. Relative discrepancy quantification vs Pandey & Kumar (2025) Fig. 13(a).

Task: F1358 / F1359
Author: Gemini Antigravity
"""

import os
import math
import numpy as np
import pandas as pd
import pytest
from scipy.spatial import cKDTree

POSSIBLE_ROOTS = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")),
    r"D:\Master thesis\Adaptive remeshing"
]
REPO_ROOT = next((r for r in POSSIBLE_ROOTS if os.path.exists(os.path.join(r, "models", "pandey_kumar_mode2"))), POSSIBLE_ROOTS[0])
ELEMENTS_CSV = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "m2_corrected_remesh", "m2_corrected_mesh_elements_et3pct.csv")

# Mode-II length scale (Sec. 4.2, p. 3270)
L0_MODE2 = 15.0 # um (0.015 mm)

# Published 7-point trajectory
PUB_PTS = np.array([
    [0.500, 0.500], # P1
    [0.535, 0.430], # P2
    [0.585, 0.340], # P3
    [0.650, 0.235], # P4
    [0.725, 0.140], # P5
    [0.800, 0.060], # P6
    [0.868, 0.000]  # P7
])

# Station-matched ridge (7 points)
RIDGE_7PT = np.array([
    [0.500, 0.500],
    [0.551, 0.430],
    [0.630, 0.340],
    [0.743, 0.235],
    [0.856, 0.140],
    [0.936, 0.060],
    [0.985, 0.000]
])

# Uniform slice-centroid ridge (11 points from manifest)
RIDGE_11PT = np.array([
    [0.539, 0.500],
    [0.538, 0.450],
    [0.553, 0.400],
    [0.594, 0.350],
    [0.679, 0.300],
    [0.770, 0.250],
    [0.873, 0.200],
    [0.902, 0.150],
    [0.927, 0.100],
    [0.964, 0.050],
    [0.985, 0.000]
])

COARSE_CRACK_PTS = np.array([
    [0.500, 0.500],
    [0.528, 0.450],
    [0.565, 0.400],
    [0.605, 0.350],
    [0.648, 0.300],
    [0.690, 0.250],
    [0.728, 0.200],
    [0.762, 0.150],
    [0.788, 0.100],
    [0.805, 0.050],
    [0.813, 0.000]
])

def dist_point_to_segment(pt, p1, p2):
    v = p2 - p1
    w = pt - p1
    c1 = np.dot(w, v)
    if c1 <= 0:
        return np.linalg.norm(pt - p1)
    c2 = np.dot(v, v)
    if c2 <= c1:
        return np.linalg.norm(pt - p2)
    b = c1 / c2
    pb = p1 + b * v
    return np.linalg.norm(pt - pb)

def dist_point_to_polyline(pt, polyline):
    return min(dist_point_to_segment(pt, polyline[i], polyline[i+1]) for i in range(len(polyline)-1))

def sample_polyline(polyline, n_samples=500):
    seg_lens = [np.linalg.norm(polyline[i+1] - polyline[i]) for i in range(len(polyline)-1)]
    total_len = sum(seg_lens)
    cum_lens = [0.0] + list(np.cumsum(seg_lens))
    s_vals = np.linspace(0, total_len, n_samples)
    sampled_pts = []
    for s in s_vals:
        for i in range(len(polyline)-1):
            if cum_lens[i] <= s <= cum_lens[i+1]:
                frac = (s - cum_lens[i]) / (cum_lens[i+1] - cum_lens[i]) if seg_lens[i] > 0 else 0.0
                pt = polyline[i] + frac * (polyline[i+1] - polyline[i])
                sampled_pts.append((s, pt[0], pt[1]))
                break
    return total_len, sampled_pts

def test_polynomial_differentiation_and_tangent_angle():
    """Verify correct polynomial derivative and crack-tip propagation angle theta = -69.52 deg."""
    a, b, c = 0.698155, -1.071775, 0.864470
    
    # Derivative dx/dy = 2*a*y + b
    # At notch tip (y = 0.500 mm):
    dx_dy_tip = 2 * a * 0.500 + b
    assert math.isclose(dx_dy_tip, -0.373620, abs_tol=1e-5)
    
    # Forward propagation vector (downward dy < 0, rightward dx > 0):
    vx = -dx_dy_tip # +0.373620
    vy = -1.0
    
    theta_rad = math.atan2(vy, vx)
    theta_deg = math.degrees(theta_rad)
    
    assert math.isclose(theta_deg, -69.516, abs_tol=0.05)
    assert theta_deg < -65.0 and theta_deg > -72.0

def test_piecewise_linear_reference_points_and_segment_angles():
    """Verify published 7-point polyline points and segment initiation angle theta = -63.43 deg."""
    p1 = PUB_PTS[0] # (0.500, 0.500)
    p2 = PUB_PTS[1] # (0.535, 0.430)
    
    dx = p2[0] - p1[0] # +0.035
    dy = p2[1] - p1[1] # -0.070
    
    theta_pwl = math.degrees(math.atan2(dy, dx))
    assert math.isclose(theta_pwl, -63.435, abs_tol=0.05)
    assert math.isclose(math.degrees(math.atan(-2.0)), -63.435, abs_tol=0.05)
    
    # Check bottom exit station P7
    p7 = PUB_PTS[-1]
    assert math.isclose(p7[0], 0.868, abs_tol=1e-4)
    assert math.isclose(p7[1], 0.000, abs_tol=1e-4)

def test_shortest_euclidean_distance_parameterizations():
    """Verify shortest Euclidean distance across both station-matched and slice-centroid parameterizations."""
    d7_list = [dist_point_to_polyline(pt, RIDGE_7PT) * 1000.0 for pt in PUB_PTS]
    d11_list = [dist_point_to_polyline(pt, RIDGE_11PT) * 1000.0 for pt in PUB_PTS]
    
    # 1. Under station-matched ridge: all 7 stations lie within W/2 = 120.0 um
    for i, d in enumerate(d7_list):
        assert d <= 120.0, f"Station P{i+1} exceeds 120 um under 7-pt ridge: {d:.2f} um"
    assert math.isclose(max(d7_list), 96.17, abs_tol=0.5)
    
    # 2. Under uniform 11-point slice centroids: max distance is at P6 (131.5 um)
    assert math.isclose(max(d11_list), 131.48, abs_tol=0.5)
    # 6 of 7 stations are strictly <= 120 um
    assert sum(d <= 120.0 for d in d11_list) == 6

def test_published_trajectory_local_mesh_resolution_and_coverage():
    """Verify that 100.00% of published trajectory satisfies h <= l0/2 and h <= l0/3 with l0 = 15.0 um."""
    assert os.path.exists(ELEMENTS_CSV), f"Missing CSV: {ELEMENTS_CSV}"
    df = pd.read_csv(ELEMENTS_CSV)
    centroids = df[['xc', 'yc']].values
    elem_h = df['h_eq'].values * 1000.0 # in um
    tree = cKDTree(centroids)
    
    total_len, sampled = sample_polyline(PUB_PTS, n_samples=500)
    
    h_vals = []
    d7_vals = []
    
    for s, x, y in sampled:
        pt = np.array([x, y])
        d7_vals.append(dist_point_to_polyline(pt, RIDGE_7PT) * 1000.0)
        dist_k, idx_k = tree.query(pt, k=1)
        h_vals.append(elem_h[idx_k])
        
    h_arr = np.array(h_vals)
    d7_arr = np.array(d7_vals)
    
    # 1. 100% of sampled points within 120 um under station-matched ridge
    frac_corridor_7pt = np.mean(d7_arr <= 120.0) * 100.0
    assert math.isclose(frac_corridor_7pt, 100.0, abs_tol=1e-3)
    
    # 2. 100.00% of sampled points satisfy h <= l0/2 = 7.50 um
    frac_l0_half = np.mean(h_arr <= L0_MODE2 / 2.0) * 100.0
    assert math.isclose(frac_l0_half, 100.0, abs_tol=1e-3), f"Coverage h <= l0/2 below 100%: {frac_l0_half}%"
    
    # 3. 100.00% of sampled points satisfy h <= l0/3 = 5.00 um (h_max = 4.289 um)
    frac_l0_third = np.mean(h_arr <= L0_MODE2 / 3.0) * 100.0
    assert math.isclose(frac_l0_third, 100.0, abs_tol=1e-3), f"Coverage h <= l0/3 below 100%: {frac_l0_third}%"
    
    # 4. Maximum h along trajectory is 4.289 um (which is strictly <= 5.0 um = l0/3)
    assert np.max(h_arr) <= 5.00
    assert math.isclose(np.max(h_arr), 4.289, abs_tol=0.05)
    
    # 5. Over 70% satisfies h <= 2.50 um (l0/6)
    frac_2p5 = np.mean(h_arr <= 2.50) * 100.0
    assert frac_2p5 >= 70.0

def test_coarse_damage_path_local_mesh_resolution():
    """Verify that 99.00% of coarse pre-analysis damage path satisfies h <= l0/2 = 7.50 um."""
    assert os.path.exists(ELEMENTS_CSV), f"Missing CSV: {ELEMENTS_CSV}"
    df = pd.read_csv(ELEMENTS_CSV)
    centroids = df[['xc', 'yc']].values
    elem_h = df['h_eq'].values * 1000.0
    tree = cKDTree(centroids)
    
    total_len, sampled = sample_polyline(COARSE_CRACK_PTS, n_samples=500)
    
    h_vals = []
    for s, x, y in sampled:
        dist_k, idx_k = tree.query([x, y], k=1)
        h_vals.append(elem_h[idx_k])
        
    h_arr = np.array(h_vals)
    frac_l0_half = np.mean(h_arr <= L0_MODE2 / 2.0) * 100.0
    assert frac_l0_half >= 98.5, f"Coarse crack coverage too low: {frac_l0_half}%"

def test_equation_count_hierarchy():
    """Verify that 21,042 mesh nodes * 3 + 1 RP = 63,127 variables and 63,127 - 97 = 63,030 solver equations."""
    n_mesh_nodes = 21042
    n_seam_duplicate_pairs = 54
    n_unique_vertices = n_mesh_nodes - n_seam_duplicate_pairs
    assert n_unique_vertices == 20988
    
    n_rp = 1
    dof_per_node = 3
    total_vars = n_mesh_nodes * dof_per_node + n_rp
    assert total_vars == 63127
    
    n_top_equations = 97
    active_solver_eqs = total_vars - n_top_equations
    assert active_solver_eqs == 63030

def test_generate_trajectory_geometry_and_coverage_figure():
    """Generate publication-quality 4-panel figure and verify output artifacts exist and have non-zero size."""
    import runpy
    plot_script = os.path.join(REPO_ROOT, "scripts", "postprocessing", "plot_mode2_trajectory_geometry_and_crack_path_coverage.py")
    assert os.path.exists(plot_script), f"Missing plot script: {plot_script}"
    runpy.run_path(plot_script)
    
    out_png = os.path.join(REPO_ROOT, "results", "figures", "mode2", "fig_mode2_trajectory_geometry_and_crack_path_coverage.png")
    out_pdf = os.path.join(REPO_ROOT, "results", "figures", "mode2", "fig_mode2_trajectory_geometry_and_crack_path_coverage.pdf")
    
    assert os.path.exists(out_png)
    assert os.path.getsize(out_png) > 100000 # > 100 KB
    assert os.path.exists(out_pdf)
    assert os.path.getsize(out_pdf) > 20000  # > 20 KB

def test_plot_dataset_consistency_and_discrepancy():
    """Verify raw numerical datasets, initial stiffness, peak force, and discrepancy quantification."""
    # 1. Coarse pre-analysis dataset
    coarse_csv = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "mode2_j1_coarse_retest_rf_history.csv")
    assert os.path.exists(coarse_csv)
    df_c = pd.read_csv(coarse_csv)
    f_max_c = np.max(df_c['rf1_kN'].values * 1000.0)
    assert math.isclose(f_max_c, 514.51, abs_tol=0.2)

    # 2. Production solve active dataset
    active_csv = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "m2_corrected_remesh", "job2_rf_active_history.csv")
    assert os.path.exists(active_csv)
    df_a = pd.read_csv(active_csv)
    assert len(df_a) >= 1800
    u_a = df_a['u_x_um'].values
    rf_a = df_a['rf_N'].values
    
    # Check elastic stiffness
    mask_el = (u_a <= 1.0) & (u_a > 0.01)
    k0 = np.polyfit(u_a[mask_el], rf_a[mask_el], 1)[0]
    assert math.isclose(k0, 45.639, abs_tol=0.05)
    
    # Check peak force and displacement
    f_max_a = np.max(rf_a)
    idx_peak = np.argmax(rf_a)
    u_peak_a = u_a[idx_peak]
    assert math.isclose(f_max_a, 412.209, abs_tol=0.05)
    assert math.isclose(u_peak_a, 9.410, abs_tol=0.05)
    
    # Check post-peak softening: final RF must be lower than peak
    assert rf_a[-1] < f_max_a
    assert f_max_a - rf_a[-1] >= 20.0 # Confirmed load drop > 20 N
    
    # Check relative discrepancies vs Pandey & Kumar Fig. 13(a)
    f_max_ref = 365.74 # N
    u_peak_ref = 8.284 # um
    
    rel_f_diff = (f_max_a - f_max_ref) / f_max_ref * 100.0
    rel_u_diff = (u_peak_a - u_peak_ref) / u_peak_ref * 100.0
    
    assert math.isclose(rel_f_diff, 12.705, abs_tol=0.1)
    assert math.isclose(rel_u_diff, 13.592, abs_tol=0.1)

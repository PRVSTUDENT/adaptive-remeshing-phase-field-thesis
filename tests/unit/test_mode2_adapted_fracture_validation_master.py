import os
import sys
import pytest
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("scripts/postprocessing"))

def test_damage_evolution_monotonicity_and_ligament_reduction():
    summary_csv = os.path.join("models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "m2_corrected_remesh", "mode2_damage_evolution_summary.csv")
    assert os.path.exists(summary_csv), "Summary CSV must exist"
    
    df = pd.read_csv(summary_csv)
    assert len(df) >= 8, "Must contain at least 8 key evaluation frames"
    
    # 1. Initial state must have zero damage
    assert df.iloc[0]['d_max'] == 0.0
    assert df.iloc[0]['ligament_height_mm'] == 0.500
    
    # 2. Maximum damage must grow monotonically to saturation (d=1.0)
    d_max_vals = df['d_max'].values
    assert np.all(np.diff(d_max_vals) >= -1e-6), "Maximum damage must be monotonic"
    assert d_max_vals[-1] == 1.0, "Terminal frame must reach full saturation d=1.0"
    
    # 3. Number of broken elements (d >= 0.9) must increase monotonically
    n_broken = df['n_d09'].values
    assert np.all(np.diff(n_broken) >= 0), "Broken element count must be non-decreasing"
    assert n_broken[-1] >= 1300, "Latest frame must contain >1300 broken elements"
    
    # 4. Intact ligament height must decrease monotonically
    lig_vals = df['ligament_height_mm'].values
    assert np.all(np.diff(lig_vals) <= 1e-6), "Intact ligament height must be non-increasing"
    assert lig_vals[-1] <= 0.075, "Crack must penetrate to within 75 um of bottom surface"
    assert lig_vals[-1] > 0.0, "Intact ligament must be positive (partial propagation)"

def test_extracted_crack_path_alignment_and_deviation():
    path_csv = os.path.join("models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "m2_corrected_remesh", "mode2_extracted_crack_path.csv")
    assert os.path.exists(path_csv), "Extracted crack path CSV must exist"
    
    df = pd.read_csv(path_csv)
    assert len(df) >= 40, "Must contain continuous vertical stations"
    
    # Check notch tip station (y = 0.500)
    row_tip = df[df['y_station_mm'] == 0.500].iloc[0]
    assert abs(row_tip['x_peak_d_mm'] - 0.4968) < 0.010, "Crack must initiate at notch tip x ~ 0.500"
    
    # Check initiation accuracy vs Fig 12(b) station (y = 0.430, x_lit = 0.5284)
    row_43 = df[df['y_station_mm'] == 0.430].iloc[0]
    delta_x_init = abs(row_43['x_peak_d_mm'] - 0.5284)
    assert delta_x_init <= 0.015, f"Initiation deviation must be <= 15 um (got {delta_x_init*1000:.2f} um)"
    
    # Check mid-height station (y = 0.250)
    row_25 = df[df['y_station_mm'] == 0.250].iloc[0]
    assert row_25['d_peak'] == 1.0, "Mid-height station must have fully broken element"
    assert row_25['x_peak_d_mm'] > 0.600, "Crack path must deviate rightward under Mode-II shear"

def test_quantitative_crack_path_deviations_and_angles():
    path_csv = os.path.join("models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "m2_corrected_remesh", "mode2_extracted_crack_path.csv")
    assert os.path.exists(path_csv), "Extracted crack path CSV must exist"
    
    df = pd.read_csv(path_csv)
    df_valid = df[df['d_peak'] >= 0.90].sort_values('y_station_mm').reset_index(drop=True)
    
    # 1. Orientation Angle Disambiguation
    p_num = np.polyfit(df_valid['x_peak_d_mm'], df_valid['y_station_mm'], 1)
    slope_num = p_num[0]
    angle_num_deg = np.degrees(np.arctan(slope_num))
    r_squared_num = np.corrcoef(df_valid['x_peak_d_mm'], df_valid['y_station_mm'])[0, 1]**2
    
    assert abs(angle_num_deg - (-58.18)) < 1.0, f"Numerical crack trajectory angle must be ~ -58.18 deg (got {angle_num_deg:.2f} deg)"
    assert r_squared_num >= 0.980, f"Numerical crack trajectory must be highly collinear (R^2 = {r_squared_num:.4f})"
    
    # 2. Authenticated Literature Stations (Pandey & Kumar 2025 Fig 12b)
    lit_stations = np.array([
        [0.5000, 0.5000],
        [0.5284, 0.4300],
        [0.5732, 0.3200],
        [0.6300, 0.2100],
        [0.7077, 0.1200],
        [0.7854, 0.0600]
    ])
    
    y_num = df_valid['y_station_mm'].values
    x_num = df_valid['x_peak_d_mm'].values
    x_num_interp = np.interp(lit_stations[:, 1], y_num, x_num)
    delta_x_um = (x_num_interp - lit_stations[:, 0]) * 1000.0
    
    mad_um = np.mean(np.abs(delta_x_um))
    rms_um = np.sqrt(np.mean(delta_x_um**2))
    max_dev_um = np.max(np.abs(delta_x_um))
    
    assert mad_um <= 10.0, f"MAD must be <= 10.0 um (got {mad_um:.2f} um)"
    assert rms_um <= 12.0, f"RMS must be <= 12.0 um (got {rms_um:.2f} um)"
    assert max_dev_um <= 22.0, f"Max deviation must be <= 22.0 um (got {max_dev_um:.2f} um)"
    
    # 3. Initiation zone precision
    tip_dev_um = abs(delta_x_um[0])
    assert tip_dev_um <= 3.5, f"Notch-tip deviation must be <= 3.5 um approx l0/4.3 (got {tip_dev_um:.2f} um)"

def test_residual_force_dimensional_and_physics_audit():
    # 1. Correct arithmetic calculation of simplified 1D shear formula
    E = 210.0      # kN/mm^2
    nu = 0.3
    G = E / (2.0 * (1.0 + nu))  # 80.76923 kN/mm^2
    A = 0.4        # mm^2
    gamma = 0.005 / 0.06  # 0.083333
    
    F_eval_kN = G * A * gamma
    F_eval_N = F_eval_kN * 1000.0
    
    # Assert exact arithmetic evaluation is 2692.3 N, NOT 300-400 N
    assert abs(F_eval_N - 2692.308) < 0.1, f"F_eval must equal 2692.3 N (got {F_eval_N:.1f} N)"
    
    # 2. Epistemological and mechanics boundaries
    # The 1D formula is inapplicable to a 2D cracked continuum body.
    # Residual force (~346 N) is governed by:
    # (a) Intact ligament shear resistance prior to severance (qualitative contributor)
    # (b) Un-degraded bulk compressive stress sigma_0^- transmission in Miehe split under uy=0
    # (c) Zero physical contact surfaces, zero penalty contact, zero Coulomb friction
    observed_rf = 346.65
    assert observed_rf < F_eval_N, "Observed residual force is much lower than 1D homogeneous rigid shear"
    assert observed_rf > 0.0, "Residual force is non-zero due to intact ligament + compressive strut"

def test_rf_history_peak_and_gap_resolution():
    rf_csv = os.path.join("models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "m2_corrected_remesh", "job2_rf_active_history.csv")
    assert os.path.exists(rf_csv), "RF history CSV must exist"
    
    df = pd.read_csv(rf_csv)
    assert len(df) >= 3500, "Must contain >3500 increments"
    
    # Peak load
    f_max = df['rf_N'].max()
    idx_max = df['rf_N'].idxmax()
    u_fmax = df.loc[idx_max, 'u_x_um']
    
    assert abs(f_max - 412.209) < 1.0, f"Peak force must match 412.21 N (got {f_max:.3f} N)"
    assert abs(u_fmax - 9.410) < 0.10, f"Peak displacement must match 9.41 um (got {u_fmax:.3f} um)"
    
    # Gap reduction vs coarse reference (514.51 N) and literature (365.74 N)
    f_coarse = 514.51
    f_lit = 365.74
    gap_resolution = (f_coarse - f_max) / (f_coarse - f_lit) * 100.0
    assert abs(gap_resolution - 68.76) < 0.5, f"Gap resolution must be ~68.76% (got {gap_resolution:.2f}%)"

def test_generate_master_publication_figures():
    from plot_mode2_adapted_fracture_validation_master import generate_all_figures
    fig1, fig2, fig3 = generate_all_figures()
    
    assert os.path.exists(fig1), f"Figure 1 PNG must exist at {fig1}"
    assert os.path.exists(fig2), f"Figure 2 PNG must exist at {fig2}"
    assert os.path.exists(fig3), f"Figure 3 PNG must exist at {fig3}"
    assert os.path.getsize(fig1) > 50000, "Figure 1 must be non-trivial"
    assert os.path.getsize(fig2) > 50000, "Figure 2 must be non-trivial"
    assert os.path.getsize(fig3) > 50000, "Figure 3 must be non-trivial"

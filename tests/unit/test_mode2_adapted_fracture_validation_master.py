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

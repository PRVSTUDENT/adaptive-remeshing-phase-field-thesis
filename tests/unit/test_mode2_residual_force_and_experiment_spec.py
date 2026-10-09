import os
import sys
import pytest
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("scripts/postprocessing"))

def test_macro_mechanical_response_and_postpeak_reloading():
    rf_csv = os.path.join("models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "m2_corrected_remesh", "job2_rf_active_history.csv")
    assert os.path.exists(rf_csv), "RF history CSV must exist"
    
    df = pd.read_csv(rf_csv)
    assert len(df) >= 4000, "Must contain full horizon increments (>4000)"
    
    # 1. Peak Force and Location
    idx_max = df['rf_N'].idxmax()
    f_max = df.loc[idx_max, 'rf_N']
    u_max = df.loc[idx_max, 'u_x_um']
    assert abs(f_max - 412.209) < 0.1, f"Peak force must be 412.21 N (got {f_max:.3f} N)"
    assert abs(u_max - 9.410) < 0.05, f"Peak displacement must be 9.41 um (got {u_max:.3f} um)"
    
    # 2. Post-Peak Local Minimum
    df_post_peak = df.loc[idx_max:].reset_index(drop=True)
    idx_min = df_post_peak['rf_N'].idxmin()
    f_min = df_post_peak.loc[idx_min, 'rf_N']
    u_min = df_post_peak.loc[idx_min, 'u_x_um']
    assert abs(f_min - 301.824) < 0.2, f"Post-peak minimum must be ~301.82 N (got {f_min:.3f} N)"
    assert abs(u_min - 12.420) < 0.1, f"Minimum displacement must be ~12.42 um (got {u_min:.3f} um)"
    
    # 3. Terminal Load and Post-Peak Reloading Magnitude
    f_terminal = df.iloc[-1]['rf_N']
    u_terminal = df.iloc[-1]['u_x_um']
    assert abs(u_terminal - 20.000) < 0.01, f"Terminal displacement must be 20.0 um (got {u_terminal:.3f} um)"
    assert abs(f_terminal - 380.418) < 0.2, f"Terminal force must be ~380.42 N (got {f_terminal:.3f} N)"
    
    reloading_delta_n = f_terminal - f_min
    reloading_pct = (reloading_delta_n / f_min) * 100.0
    assert abs(reloading_delta_n - 78.594) < 0.5, f"Reloading increase must be ~78.59 N (got {reloading_delta_n:.3f} N)"
    assert abs(reloading_pct - 26.04) < 0.5, f"Reloading percentage must be ~26.04% (got {reloading_pct:.2f}%)"

def test_external_work_integration_and_gap_closure():
    rf_csv = os.path.join("models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "m2_corrected_remesh", "job2_rf_active_history.csv")
    coarse_csv = os.path.join("models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "mode2_j1_coarse_retest_rf_history.csv")
    lit_csv = os.path.join("references", "derived", "pandey_kumar_2025_fig13a_authoritative_redigitized.csv")
    
    assert os.path.exists(rf_csv), "Adapted RF CSV must exist"
    assert os.path.exists(coarse_csv), "Coarse RF CSV must exist"
    assert os.path.exists(lit_csv), "Literature CSV must exist"
    
    df_adapt = pd.read_csv(rf_csv)
    df_coarse = pd.read_csv(coarse_csv)
    df_lit = pd.read_csv(lit_csv)
    
    # Adapt: u_x_um, rf_N
    u_adapt_mm = df_adapt['u_x_um'].values / 1000.0
    rf_adapt_n = df_adapt['rf_N'].values
    
    # Coarse: ux_mm, rf1_kN
    u_coarse_mm = df_coarse['ux_mm'].values
    rf_coarse_n = df_coarse['rf1_kN'].values * 1000.0
    
    # 1. Full Horizon External Work (0 -> 20 um)
    # W = \int F du (N * mm = mJ)
    w_adapt_full_mj = np.trapezoid(rf_adapt_n, u_adapt_mm)
    w_coarse_full_mj = np.trapezoid(rf_coarse_n, u_coarse_mm)
    
    assert abs(w_adapt_full_mj - 5.5479) < 0.05, f"Adapted full work must be ~5.548 mJ (got {w_adapt_full_mj:.4f} mJ)"
    assert abs(w_coarse_full_mj - 6.9949) < 0.05, f"Coarse full work must be ~6.995 mJ (got {w_coarse_full_mj:.4f} mJ)"
    
    work_reduction_pct = (w_coarse_full_mj - w_adapt_full_mj) / w_coarse_full_mj * 100.0
    assert abs(work_reduction_pct - 20.69) < 0.5, f"Work reduction must be ~20.69% (got {work_reduction_pct:.2f}%)"
    
    # 2. Published Window External Work (0 -> 16 um)
    mask_adapt_16 = u_adapt_mm <= 0.0160001
    w_adapt_16_mj = np.trapezoid(rf_adapt_n[mask_adapt_16], u_adapt_mm[mask_adapt_16])
    
    mask_coarse_16 = u_coarse_mm <= 0.0160001
    w_coarse_16_mj = np.trapezoid(rf_coarse_n[mask_coarse_16], u_coarse_mm[mask_coarse_16])
    
    u_lit_mm = df_lit['displacement_mm'].values
    rf_lit_n = df_lit['proposed_pfm_N'].values
    w_lit_16_mj = np.trapezoid(rf_lit_n, u_lit_mm)
    
    assert abs(w_lit_16_mj - 3.5167) < 0.05, f"Literature work must be ~3.517 mJ (got {w_lit_16_mj:.4f} mJ)"
    assert abs(w_adapt_16_mj - 4.1353) < 0.05, f"Adapted work (16um) must be ~4.135 mJ (got {w_adapt_16_mj:.4f} mJ)"
    
    # Work gap closure
    work_gap_closure = (w_coarse_16_mj - w_adapt_16_mj) / (w_coarse_16_mj - w_lit_16_mj) * 100.0
    assert abs(work_gap_closure - 63.74) < 1.0, f"Work gap closure must be ~63.74% (got {work_gap_closure:.2f}%)"

def test_coarse_companion_reloading_and_kinematic_trait():
    coarse_csv = os.path.join("models", "pandey_kumar_mode2", "06_paper_grounded_uel_preanalysis", "mode2_j1_coarse_retest_rf_history.csv")
    df_coarse = pd.read_csv(coarse_csv)
    
    u_coarse_um = df_coarse['ux_mm'].values * 1000.0
    rf_coarse_n = df_coarse['rf1_kN'].values * 1000.0
    
    idx_max = np.argmax(rf_coarse_n)
    rf_post = rf_coarse_n[idx_max:]
    u_post = u_coarse_um[idx_max:]
    
    idx_min_rel = np.argmin(rf_post)
    f_min_coarse = rf_post[idx_min_rel]
    u_min_coarse = u_post[idx_min_rel]
    f_term_coarse = rf_coarse_n[-1]
    
    # Coarse also has a local minimum followed by terminal reloading
    assert abs(f_min_coarse - 428.90) < 1.0, f"Coarse minimum must be ~428.90 N (got {f_min_coarse:.2f} N)"
    assert abs(u_min_coarse - 19.31) < 0.5, f"Coarse min displacement must be ~19.31 um (got {u_min_coarse:.2f} um)"
    assert f_term_coarse > f_min_coarse, "Coarse model must also exhibit terminal reloading confirming kinematic structural trait"

def test_experiment_specification_governance_and_schema():
    spec_path = os.path.join("docs", "mode2", "MODE2_EXPERIMENT_SPECIFICATION_POSTPEAK_RELOAD_AND_RESOLUTION.md")
    assert os.path.exists(spec_path), "Experiment specification document must exist"
    
    with open(spec_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Verify all 3 experiments are defined
    assert "M2-EXP1" in content, "Must define Experiment M2-EXP1"
    assert "M2-EXP2" in content, "Must define Experiment M2-EXP2"
    assert "M2-EXP3" in content, "Must define Experiment M2-EXP3"
    
    # Verify governance boundaries (no unauthorized qsub)
    assert "execution_authorized: false" in content, "Execution must be unauthorized by default"
    assert "automatic_retry: false" in content, "Automatic retry must be false"
    assert "CLOSED_PASSED_WITH_LIMITATIONS" in content, "Gate M2-4 must be assessed with limitations"

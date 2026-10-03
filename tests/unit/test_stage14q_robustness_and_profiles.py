import os
import json
import pytest
import numpy as np
import pandas as pd

REPORT_JSON_PATH = "models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/MODE1_STAGE14Q_ROBUSTNESS_AND_U003_AUDIT_REPORT.json"
EXTRACTED_JSON_PATH = "models/pandey_kumar_mode1/25_stage14_adaptive_candidate_14k/stage14q_adaptive_extracted_profiles.json"
REF_CSV_PATH = "models/pandey_kumar_mode1/16_energy_qualification_reference_15k/mode1_reference_ligament_profiles.csv"
FIGURES_DIR = "results/figures/mode1_gate6b"

@pytest.fixture(scope="module")
def audit_report():
    assert os.path.exists(REPORT_JSON_PATH), f"Report JSON not found: {REPORT_JSON_PATH}"
    with open(REPORT_JSON_PATH, 'r') as f:
        return json.load(f)

@pytest.fixture(scope="module")
def extracted_data():
    assert os.path.exists(EXTRACTED_JSON_PATH), f"Extracted profiles JSON not found: {EXTRACTED_JSON_PATH}"
    with open(EXTRACTED_JSON_PATH, 'r') as f:
        return json.load(f)

@pytest.fixture(scope="module")
def ref_df():
    assert os.path.exists(REF_CSV_PATH), f"Reference CSV not found: {REF_CSV_PATH}"
    return pd.read_csv(REF_CSV_PATH)

def test_stage14q_grid_resolution_invariance(audit_report):
    """Verify that continuous L2 and Linf metrics are invariant across N=501, 1001, 2001 grids."""
    evaluated_states = audit_report['evaluated_states']
    
    for u_str in ['0.001', '0.003']:
        assert u_str in evaluated_states, f"State {u_str} missing in audit report"
        state_data = evaluated_states[u_str]
        grid_sens = state_data['grid_sensitivity']
        
        # Check all 3 grids are evaluated
        assert 'Grid_501_1um' in grid_sens
        assert 'Grid_1001_0.5um' in grid_sens
        assert 'Grid_2001_0.25um' in grid_sens
        
        base_l2 = grid_sens['Grid_1001_0.5um']['rel_l2_percent']
        base_linf = grid_sens['Grid_1001_0.5um']['l_inf']
        
        # Relative L2 variation across grids must be < 0.5% absolute difference
        for gn in ['Grid_501_1um', 'Grid_2001_0.25um']:
            l2_val = grid_sens[gn]['rel_l2_percent']
            linf_val = grid_sens[gn]['l_inf']
            assert abs(l2_val - base_l2) < 0.5, f"L2 grid variation too large for {gn}: {l2_val} vs {base_l2}"
            assert abs(linf_val - base_linf) < 1e-4, f"L_inf variation too large for {gn}: {linf_val} vs {base_linf}"

def test_stage14q_sampling_hypothesis_consistency(audit_report, extracted_data, ref_df):
    """Verify that the discrete sampling hypothesis is supported by discrete node/centroid positions and discrepancy decay."""
    evaluated_states = audit_report['evaluated_states']
    s1 = evaluated_states['0.001']
    s3 = evaluated_states['0.003']
    
    # Check peak location and element sizing
    assert s1['x_d_max_adapt_mm'] < s1['x_d_max_ref_mm']
    assert s3['x_d_max_adapt_mm'] < s3['x_d_max_ref_mm']
    assert np.isclose(s1['x_d_max_adapt_mm'], 0.50108, atol=1e-4)
    assert np.isclose(s1['x_d_max_ref_mm'], 0.50150, atol=1e-4)
    
    # Check direct sampling hypothesis record
    hyp1 = s1['direct_sampling_hypothesis']
    assert hyp1['hypothesis_status'] == 'EVIDENCE_SUPPORTED_DISCRETIZATION_SAMPLING_CONSISTENT'
    
    # Far-field discrepancy decay checks:
    # State 1 (u = 0.0010 mm)
    ref1 = ref_df[np.isclose(ref_df['u_target_mm'], 0.001)].sort_values('x_mm')
    x_ref1 = ref1['x_mm'].values
    d_ref1 = ref1['d'].values
    lig1 = extracted_data['extracted_states']['0.001']['ligament_profile']
    x_ad1 = np.array([p['xc'] for p in lig1])
    d_ad1 = np.array([p['d_sdv14'] for p in lig1])
    d_ref_int1 = np.interp(x_ad1, x_ref1, d_ref1)
    diff1 = np.abs(d_ad1 - d_ref_int1)
    assert np.max(diff1[x_ad1 >= 0.55]) < 5e-5
    
    # State 2 (u = 0.0030 mm)
    ref3 = ref_df[np.isclose(ref_df['u_target_mm'], 0.003)].sort_values('x_mm')
    x_ref3 = ref3['x_mm'].values
    d_ref3 = ref3['d'].values
    lig3 = extracted_data['extracted_states']['0.003']['ligament_profile']
    x_ad3 = np.array([p['xc'] for p in lig3])
    d_ad3 = np.array([p['d_sdv14'] for p in lig3])
    d_ref_int3 = np.interp(x_ad3, x_ref3, d_ref3)
    diff3 = np.abs(d_ad3 - d_ref_int3)
    assert np.max(diff3[x_ad3 >= 0.60]) < 1e-4

def test_stage14q_multistate_damage_and_crack_tip_status(audit_report, extracted_data):
    """Verify multi-state damage levels and explicit reporting of crack-tip threshold."""
    evaluated_states = audit_report['evaluated_states']
    
    # State 1 (u = 0.0010 mm)
    s1 = evaluated_states['0.001']
    assert 0.0090 < s1['d_max_ref'] < 0.0093
    assert 0.0094 < s1['d_max_adapt'] < 0.0097
    assert 4.0 < s1['d_max_delta_percent'] < 5.5
    assert not s1['crack_tip_status']['crack_tip_detected']
    assert s1['crack_tip_status']['x_tip_mm'] is None
    
    # State 2 (u = 0.0030 mm)
    s3 = evaluated_states['0.003']
    assert 0.085 < s3['d_max_ref'] < 0.090
    assert 0.090 < s3['d_max_adapt'] < 0.095
    assert 4.5 < s3['d_max_delta_percent'] < 5.5
    assert not s3['crack_tip_status']['crack_tip_detected']
    assert s3['crack_tip_status']['x_tip_mm'] is None
    
    # Check SDV1 vs SDV14 parity
    for u_str in ['0.001', '0.003']:
        parity_diff = extracted_data['extracted_states'][u_str]['max_sdv1_sdv14_parity_diff']
        assert parity_diff < 1e-12, f"SDV1 vs SDV14 parity violation in state {u_str}: {parity_diff}"

def test_stage14q_governed_classification_and_epistemological_structure(audit_report):
    """Verify governed classification and epistemological corrections."""
    assert audit_report['task_id'] == 'F1194-GATE6B-STAGE14Q-ROBUSTNESS-AND-U003-QUALIFICATION-20261003'
    assert audit_report['governing_verdict'] == 'STAGE14Q_ROBUSTNESS_AND_U003_QUALIFICATION_COMPLETED'
    assert audit_report['spatial_profile_governed_classification'] == 'STABLE'
    
    epist = audit_report['epistemological_framework']
    assert epist['causal_proof_withdrawn'] is True
    assert epist['hypothesis_classification'] == 'EVIDENCE_SUPPORTED_DISCRETIZATION_SAMPLING_CONSISTENT'
    
    # Evolution summary
    evol = audit_report['multistate_evolution']
    assert evol['evolution_trends']['localization_profile_preserved'] is True

def test_stage14q_figure_artifacts_exist():
    """Verify all 4 publication figure pairs (PNG + PDF) exist and are non-empty."""
    expected_figures = [
        "fig_mode1_stage14q_multistate_overlay.png",
        "fig_mode1_stage14q_multistate_overlay.pdf",
        "fig_mode1_stage14q_neartip_zoom.png",
        "fig_mode1_stage14q_neartip_zoom.pdf",
        "fig_mode1_stage14q_discrepancy_and_gradient.png",
        "fig_mode1_stage14q_discrepancy_and_gradient.pdf",
        "fig_mode1_stage14q_grid_invariance.png",
        "fig_mode1_stage14q_grid_invariance.pdf"
    ]
    for fig_name in expected_figures:
        fig_path = os.path.join(FIGURES_DIR, fig_name)
        assert os.path.exists(fig_path), f"Figure not found: {fig_path}"
        assert os.path.getsize(fig_path) > 1000, f"Figure file too small: {fig_path}"

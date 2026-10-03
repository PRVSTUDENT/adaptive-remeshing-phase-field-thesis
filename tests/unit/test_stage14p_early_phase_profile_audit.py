import os
import json
import pytest

def test_stage14p_audit_report_structure_and_verdict():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    report_json_path = os.path.join(
        base_dir,
        "models",
        "pandey_kumar_mode1",
        "25_stage14_adaptive_candidate_14k",
        "MODE1_STAGE14P_EARLY_PHASE_PROFILE_AUDIT_REPORT.json"
    )
    assert os.path.exists(report_json_path), f"Report JSON not found: {report_json_path}"
    
    with open(report_json_path, 'r') as f:
        data = json.load(f)
        
    assert data["task_id"] == "F1193-GATE6B-STAGE14P-EARLY-PHASE-PROFILE-AUDIT-20261003"
    assert data["governing_verdict"] == "STAGE14_EARLY_SPATIAL_PHASE_PROFILE_AUDIT"
    assert data["spatial_phase_field_classification"] == "STABLE"
    assert "audit_metrics_u_0_0010mm" in data

def test_stage14p_spatial_norms_and_bounds():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    report_json_path = os.path.join(
        base_dir,
        "models",
        "pandey_kumar_mode1",
        "25_stage14_adaptive_candidate_14k",
        "MODE1_STAGE14P_EARLY_PHASE_PROFILE_AUDIT_REPORT.json"
    )
    with open(report_json_path, 'r') as f:
        data = json.load(f)
        
    metrics = data["audit_metrics_u_0_0010mm"]["comparison_metrics"]
    
    # 1. Continuous L2 relative difference across [0.50, 1.00] mm < 5.0%
    rel_l2 = metrics["rel_continuous_l2_pct"]
    assert 0.0 < rel_l2 < 5.0, f"Continuous L2 error {rel_l2}% exceeds 5.0% bound"
    
    # 2. Maximum point-wise discrepancy L_inf < 0.0010
    l_inf = metrics["l_inf_diff"]
    assert 0.0 < l_inf < 0.0010, f"L_infinity discrepancy {l_inf} exceeds 0.0010"
    
    # 3. L_inf location is localized at crack tip (x in [0.500, 0.505] mm)
    x_l_inf = metrics["x_l_inf_mm"]
    assert 0.500 <= x_l_inf <= 0.505, f"L_infinity discrepancy location {x_l_inf} mm not at tip root"

def test_stage14p_crack_tip_and_damage_state():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    report_json_path = os.path.join(
        base_dir,
        "models",
        "pandey_kumar_mode1",
        "25_stage14_adaptive_candidate_14k",
        "MODE1_STAGE14P_EARLY_PHASE_PROFILE_AUDIT_REPORT.json"
    )
    with open(report_json_path, 'r') as f:
        data = json.load(f)
        
    m = data["audit_metrics_u_0_0010mm"]
    ref_tip = m["reference_model"]["tip_position_d90_mm"]
    adapt_tip = m["adaptive_candidate"]["tip_position_d90_mm"]
    
    assert ref_tip == 0.5000, f"Reference tip position unexpected: {ref_tip}"
    assert adapt_tip == 0.5000, f"Adaptive tip position unexpected: {adapt_tip}"
    
    # Phase field peak < 0.02 (pre-propagation elastic anchor)
    assert m["reference_model"]["global_d_max"] < 0.02
    assert m["adaptive_candidate"]["global_d_max"] < 0.02

def test_stage14p_figure_artifacts_exist():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    fig_dir = os.path.join(base_dir, "results", "figures", "mode1_gate6b")
    
    expected_figures = [
        "fig_mode1_stage14p_ligament_profile_overlay.png",
        "fig_mode1_stage14p_ligament_profile_overlay.pdf",
        "fig_mode1_stage14p_crack_tip_zoom.png",
        "fig_mode1_stage14p_crack_tip_zoom.pdf",
        "fig_mode1_stage14p_profile_difference.png",
        "fig_mode1_stage14p_profile_difference.pdf"
    ]
    
    for fig_name in expected_figures:
        fig_path = os.path.join(fig_dir, fig_name)
        assert os.path.exists(fig_path), f"Figure not found: {fig_path}"
        assert os.path.getsize(fig_path) > 1000, f"Figure file too small: {fig_path}"

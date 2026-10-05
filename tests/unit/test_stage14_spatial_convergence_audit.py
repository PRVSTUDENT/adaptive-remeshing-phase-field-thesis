import os
import json
import pytest
import numpy as np
import pandas as pd

REF_DIR = os.path.join("models", "pandey_kumar_mode1", "16_energy_qualification_reference_15k")
ADAPT_DIR = os.path.join("models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k")
AUDIT_JSON = os.path.join(ADAPT_DIR, "MODE1_BASELINE_SPATIAL_PHASE_FIELD_AND_CRACK_PATH_AUDIT.json")


def test_spatial_audit_json_structure():
    """Verify that the baseline spatial audit JSON exists and conforms to protocol version 2."""
    assert os.path.exists(AUDIT_JSON), f"Missing audit JSON at {AUDIT_JSON}"
    with open(AUDIT_JSON, "r") as f:
        data = json.load(f)
    assert data["protocol_version"] == 2
    assert "F1247" in data["task_id"] or "F1246" in data["task_id"]
    assert "governing_baselines" in data
    assert "spatial_audit_records" in data
    assert len(data["spatial_audit_records"]) == 9


def test_unmatched_displacement_blocked():
    """Verify that spatial comparison strictly enforces matched displacement milestones."""
    with open(AUDIT_JSON, "r") as f:
        data = json.load(f)
    
    valid_disps = {0.001, 0.003, 0.005, 0.005733, 0.005857, 0.006, 0.0065, 0.007, 0.007889}
    for rec in data["spatial_audit_records"]:
        target_u = rec["target_u_mm"]
        assert target_u in valid_disps, f"Invalid unmatched target displacement: {target_u}"


def test_zero_forward_filling_enforced():
    """Verify that no forward-filling occurs beyond terminal solved displacement u = 0.007889 mm."""
    ad_summary_path = os.path.join(ADAPT_DIR, "mode1_stage14_adaptive_matched_states_summary.csv")
    df_ad = pd.read_csv(ad_summary_path)
    
    terminal_u = 0.007889
    # States targeted at 0.008, 0.009, 0.010 must have actual_u <= 0.007889 and must not claim u=0.010 solved state
    beyond_states = df_ad[df_ad["u_target_mm"] > terminal_u]
    assert len(beyond_states) > 0, "Expected target entries beyond terminal displacement"
    for _, row in beyond_states.iterrows():
        assert np.isclose(row["u_actual_mm"], terminal_u, atol=1e-5), \
            f"Actual displacement {row['u_actual_mm']} unexpectedly exceeded terminal {terminal_u}"


def test_invalid_uel_abi_job_excluded():
    """Verify that invalidated Job 1409947 (inverted UEL ABI) is not used as governing fracture baseline."""
    with open(AUDIT_JSON, "r") as f:
        data = json.load(f)
    
    adapt_meta = data["governing_baselines"]["adaptive_et1_baseline"]
    assert adapt_meta["job_id"] == "1409982.mmaster02", f"Expected Job 1409982, got {adapt_meta['job_id']}"
    assert adapt_meta["job_id"] != "1409947.mmaster02", "Invalidated Job 1409947 must be excluded!"


def test_reaction_force_parity_and_authenticity():
    """Verify that reference reaction force values reflect true non-linear history rather than linear placeholder."""
    with open(AUDIT_JSON, "r") as f:
        data = json.load(f)
    
    # Check at u = 0.0050 mm: authentic non-linear force is ~0.662 kN (linear placeholder would be ~0.6896 kN)
    rec_50 = next(r for r in data["spatial_audit_records"] if np.isclose(r["target_u_mm"], 0.0050))
    assert np.isclose(rec_50["ref_force_kN"], 0.662052, atol=1e-3), \
        f"Expected authentic non-linear F_ref ~0.662 kN, got {rec_50['ref_force_kN']}"
    assert not np.isclose(rec_50["ref_force_kN"], 0.6896, atol=1e-3), \
        "F_ref at u=0.0050 mm must not be the linear-elastic formula 137.924 * 0.005!"
    
    # Check at peak u = 0.005857 mm: F_ref is 0.757778 kN
    rec_peak = next(r for r in data["spatial_audit_records"] if np.isclose(r["target_u_mm"], 0.005857))
    assert np.isclose(rec_peak["ref_force_kN"], 0.757778, atol=1e-4)


def test_spatial_dmax_field_authenticity():
    """Verify that reference d_max values reflect authentic integration point field data."""
    with open(AUDIT_JSON, "r") as f:
        data = json.load(f)
    
    # Check at u = 0.0050 mm: authentic d_max is ~0.298
    rec_50 = next(r for r in data["spatial_audit_records"] if np.isclose(r["target_u_mm"], 0.0050))
    assert np.isclose(rec_50["ref_d_max"], 0.298088, atol=1e-3), \
        f"Expected authentic d_max ~0.298, got {rec_50['ref_d_max']}"
    
    # Check at u = 0.005857 mm: authentic d_max is ~0.630
    rec_peak = next(r for r in data["spatial_audit_records"] if np.isclose(r["target_u_mm"], 0.005857))
    assert np.isclose(rec_peak["ref_d_max"], 0.629736, atol=1e-3), \
        f"Expected authentic d_max ~0.630, got {rec_peak['ref_d_max']}"


def test_element_size_metric_definitions_explicit():
    """Verify that minimum element size definitions (area-equivalent vs nominal edge length) are explicit."""
    with open(AUDIT_JSON, "r") as f:
        data = json.load(f)
    
    adapt_meta = data["governing_baselines"]["adaptive_et1_baseline"]
    assert "h_min_area_equivalent_um" in adapt_meta
    assert "h_min_nominal_edge_um" in adapt_meta
    assert np.isclose(adapt_meta["h_min_area_equivalent_um"], 0.7605, atol=1e-3)
    assert np.isclose(adapt_meta["h_min_nominal_edge_um"], 1.09, atol=0.05)


def test_crack_tip_threshold_definitions_explicit():
    """Verify that crack-tip threshold definitions are explicit and multi-threshold (0.50, 0.70, 0.90)."""
    with open(AUDIT_JSON, "r") as f:
        data = json.load(f)
    
    for rec in data["spatial_audit_records"]:
        assert "ref_xtip_d50_mm" in rec and "adapt_xtip_d50_mm" in rec
        assert "ref_xtip_d70_mm" in rec and "adapt_xtip_d70_mm" in rec
        assert "ref_xtip_d90_mm" in rec and "adapt_xtip_d90_mm" in rec
        # When unbroken (u <= 0.005), all thresholds yield notch root 0.500 mm
        if rec["target_u_mm"] <= 0.005:
            assert np.isclose(rec["ref_xtip_d50_mm"], 0.500, atol=1e-4)
            assert np.isclose(rec["ref_xtip_d70_mm"], 0.500, atol=1e-4)
            assert np.isclose(rec["ref_xtip_d90_mm"], 0.500, atol=1e-4)
            assert np.isclose(rec["adapt_xtip_d50_mm"], 0.500, atol=1e-4)
            assert np.isclose(rec["adapt_xtip_d70_mm"], 0.500, atol=1e-4)
            assert np.isclose(rec["adapt_xtip_d90_mm"], 0.500, atol=1e-4)
        elif rec["target_u_mm"] >= 0.006:
            # When fully severed, all thresholds agree at boundary x ~ 0.9985 mm
            assert np.isclose(rec["ref_xtip_d90_mm"], 0.998496, atol=1e-4)
            assert np.isclose(rec["adapt_xtip_d90_mm"], 0.998490, atol=1e-4)


def test_pre_peak_spatial_convergence_metrics():
    """Verify pre-peak spatial convergence: K0 agrees within 0.1%, stationary crack tip at 0.500 mm."""
    with open(AUDIT_JSON, "r") as f:
        data = json.load(f)
    
    k0_ref = data["governing_baselines"]["fixed_reference"]["K0_kN_per_mm"]
    k0_ad = data["governing_baselines"]["adaptive_et1_baseline"]["K0_kN_per_mm"]
    rel_k0_diff = abs(k0_ad - k0_ref) / k0_ref
    assert rel_k0_diff < 0.001, f"Stiffness difference {rel_k0_diff*100:.4f}% exceeds 0.1%"
    
    for rec in data["spatial_audit_records"]:
        if rec["target_u_mm"] <= 0.0050:
            assert rec["spatial_verdict"] == "SPATIAL_FIELD_BASELINE_AGREEMENT"
            assert np.isclose(rec["ref_xtip_d90_mm"], 0.500000, atol=1e-4)
            assert np.isclose(rec["adapt_xtip_d90_mm"], 0.500000, atol=1e-4)
            assert abs(rec["adapt_d_max"] - rec["ref_d_max"]) < 0.025


def test_mode1_symmetry_preservation():
    """Verify that Mode-I symmetry is strictly preserved: off-axis centroid deviation < 1.0 um."""
    with open(AUDIT_JSON, "r") as f:
        data = json.load(f)
    
    for rec in data["spatial_audit_records"]:
        if rec["target_u_mm"] >= 0.0060:
            ref_dev = rec["ref_offaxis_dev_um"]
            ad_dev = rec["adapt_offaxis_dev_um"]
            assert ref_dev < 1.0, f"Ref off-axis deviation {ref_dev} um exceeds 1.0 um bound"
            assert ad_dev < 1.0, f"Adaptive off-axis deviation {ad_dev} um exceeds 1.0 um bound"


def test_final_spatial_convergence_gated_on_58k_candidate():
    """Verify that final spatial-resolution convergence is explicitly gated on Job 1410179 (58k candidate)."""
    cs_path = os.path.join("project_coordination", "CURRENT_STATE.md")
    assert os.path.exists(cs_path)
    with open(cs_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    assert "1410179" in content, "Job 1410179 (58k spatial candidate) must be explicitly listed in CURRENT_STATE"
    assert "PK_M1_14AM_SOLVE" in content, "PK_M1_14AM_SOLVE must be recorded in CURRENT_STATE"

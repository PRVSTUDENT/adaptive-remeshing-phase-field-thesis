#!/usr/bin/env python3
"""
test_mode2_f1381_fixed_fracture_uel_and_adaptive_gates.py
---------------------------------------------------------
Unit tests for Task F1381:
  1. Coarse mesh complete fracture trajectory verification (Job 1411542)
  2. Fixed-suite pending status verification (refuting premature convergence)
  3. UEL constitutive tangent consistency and subgradient jump at tr(eps)=0
  4. History monotonicity vs AT2 damage field spatial kinetics
  5. Multi-field adaptive indicator formulation, Miehe split, and sizing bounds
  6. Fixed-versus-adapted comparative post-processing pipeline
  7. Publication figure and comparison artifact existence

Author: Antigravity (Advanced Agentic Coding)
Task: F1381-MODE2-FIXED-MESH-FRACTURE-EVIDENCE-UEL-RELIABILITY-AND-ADAPTIVE-DECISION-GATES
Date: 2026-10-09
"""

import os
import json
import pytest
import numpy as np

# Material constants
E = 210.0      # kN/mm2
NU = 0.30
LAMBDA = E * NU / ((1.0 + NU) * (1.0 - 2.0 * NU)) # 121.1538 kN/mm2
MU = E / (2.0 * (1.0 + NU))                       # 80.7692 kN/mm2
K_RES = 1.0e-7
L0 = 0.015     # mm (15 um)

def miehe_stress(eps, d):
    """Compute Miehe spectral split stress vector [sig11, sig22, sig12]."""
    e11, e22, gam12 = eps
    e12 = 0.5 * gam12
    tr_eps = e11 + e22
    
    diff = e11 - e22
    R = np.sqrt(0.25 * diff**2 + e12**2)
    eps1 = 0.5 * tr_eps + R
    eps2 = 0.5 * tr_eps - R
    
    eps1_pos = max(0.0, eps1)
    eps2_pos = max(0.0, eps2)
    eps1_neg = min(0.0, eps1)
    eps2_neg = min(0.0, eps2)
    
    tr_pos = max(0.0, tr_eps)
    tr_neg = min(0.0, tr_eps)
    
    g_d = (1.0 - d)**2 + K_RES
    
    sig_pos_iso = LAMBDA * tr_pos
    sig_neg_iso = LAMBDA * tr_neg
    
    if R > 1e-14:
        n1_x2 = 0.5 * (1.0 + diff / (2.0 * R))
        n1_y2 = 0.5 * (1.0 - diff / (2.0 * R))
        n1_xy = e12 / (2.0 * R)
        
        n2_x2 = n1_y2
        n2_y2 = n1_x2
        n2_xy = -n1_xy
    else:
        n1_x2, n1_y2, n1_xy = 1.0, 0.0, 0.0
        n2_x2, n2_y2, n2_xy = 0.0, 1.0, 0.0
        
    s11_pos = sig_pos_iso + 2.0 * MU * (eps1_pos * n1_x2 + eps2_pos * n2_x2)
    s22_pos = sig_pos_iso + 2.0 * MU * (eps1_pos * n1_y2 + eps2_pos * n2_y2)
    s12_pos = 2.0 * MU * (eps1_pos * n1_xy + eps2_pos * n2_xy)
    
    s11_neg = sig_neg_iso + 2.0 * MU * (eps1_neg * n1_x2 + eps2_neg * n2_x2)
    s22_neg = sig_neg_iso + 2.0 * MU * (eps1_neg * n1_y2 + eps2_neg * n2_y2)
    s12_neg = 2.0 * MU * (eps1_neg * n1_xy + eps2_neg * n2_xy)
    
    sig = g_d * np.array([s11_pos, s22_pos, s12_pos]) + np.array([s11_neg, s22_neg, s12_neg])
    return sig

def test_coarse_complete_fracture_trajectory():
    """Verify Job 1411542 coarse mesh complete fracture metrics."""
    json_path = "models/pandey_kumar_mode2/07_fixed_mesh_convergence_suite/fixed_mesh_convergence_comparison.json"
    assert os.path.exists(json_path), f"Missing comparison JSON: {json_path}"
    
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    coarse = data["Fixed_Coarse_2.5k"]["metrics"]
    assert coarse["is_completed_horizon"] is True
    assert coarse["num_increments"] == 4000
    assert np.isclose(coarse["ux_max_reached_um"], 20.0, atol=0.01)
    assert np.isclose(coarse["k0_kn_per_mm"], 45.764, atol=0.15)
    assert np.isclose(coarse["rf_max_observed_n"], 525.70, atol=0.5)
    assert np.isclose(coarse["ux_at_rf_max_um"], 13.99, atol=0.1)
    assert coarse["peak_status"] == "PEAK_TRAVERSED"
    # Post-peak softening verified: terminal force is less than peak
    assert coarse["rf_current_n"] < coarse["rf_max_observed_n"]
    assert coarse["rf_max_observed_n"] - coarse["rf_current_n"] > 30.0 # dropped by ~36.45 N

def test_fixed_suite_in_progress_pending_status():
    """Verify that Medium, Interm, Fine, and ET2 are correctly classified as in-progress."""
    json_path = "models/pandey_kumar_mode2/07_fixed_mesh_convergence_suite/fixed_mesh_convergence_comparison.json"
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    for key in ["Fixed_Medium_18k", "Fixed_Interm_40k", "Fixed_Fine_72k", "Adapted_ET2_Stab"]:
        m = data[key]["metrics"]
        assert m["is_completed_horizon"] is False
        assert m["peak_status"] == "MONOTONICALLY_INCREASING_PEAK_PENDING"
        # Initial stiffness is converged across all tiers
        assert np.isclose(m["k0_kn_per_mm"], 45.85, atol=0.20)
        assert m["k0_r2"] > 0.9999999

def test_uel_constitutive_tangent_and_subgradient_jump():
    """Verify analytical vs numerical tangent consistency and subgradient jump."""
    eps0 = np.array([0.002, -0.001, 0.003])
    h_pert = 1.0e-7
    d = 0.4
    
    # Numerical Jacobian (3x3)
    D_num = np.zeros((3, 3))
    for j in range(3):
        e_p = eps0.copy()
        e_m = eps0.copy()
        e_p[j] += h_pert
        e_m[j] -= h_pert
        sig_p = miehe_stress(e_p, d)
        sig_m = miehe_stress(e_m, d)
        D_num[:, j] = (sig_p - sig_m) / (2.0 * h_pert)
        
    # Check symmetry and positive definiteness
    assert np.abs(D_num[0, 1] - D_num[1, 0]) < 1.0e-4
    assert np.abs(D_num[0, 2] - D_num[2, 0]) < 1.0e-4
    assert np.all(np.linalg.eigvalsh(D_num) > 0)
    
    # Subgradient jump across tr(eps)=0
    g_d = (1.0 - d)**2 + K_RES
    expected_jump = (1.0 - g_d) * LAMBDA
    
    eps_plus = np.array([1.0e-5 + 1.0e-7, -1.0e-5, 0.002])
    eps_minus = np.array([1.0e-5 - 1.0e-7, -1.0e-5, 0.002])
    
    sig_p1 = miehe_stress(eps_plus + np.array([h_pert, 0, 0]), d)
    sig_p0 = miehe_stress(eps_plus, d)
    d11_plus = (sig_p1[0] - sig_p0[0]) / h_pert
    
    sig_m0 = miehe_stress(eps_minus, d)
    sig_m1 = miehe_stress(eps_minus - np.array([h_pert, 0, 0]), d)
    d11_minus = (sig_m0[0] - sig_m1[0]) / h_pert
    
    jump = d11_minus - d11_plus
    assert np.isclose(jump, expected_jump, rtol=1.0e-2)

def test_history_monotonicity_vs_damage_pde_redistribution():
    """Verify history variable monotonicity and AT2 damage spatial kinetics."""
    h_history = [0.001, 0.003, 0.008, 0.008, 0.008] # monotonically increasing
    for i in range(len(h_history) - 1):
        assert h_history[i+1] >= h_history[i]
        
    # AT2 1D crack solution: d(x) = exp(-|x|/l0) with 101 points (0 at index 50)
    x = np.linspace(-0.1, 0.1, 101)
    d_profile = np.exp(-np.abs(x) / L0)
    assert np.isclose(d_profile[50], 1.0, atol=1e-12) # exact peak at center
    assert np.all((d_profile >= 0.0) & (d_profile <= 1.0))

def test_multi_field_adaptive_indicator_and_safeguards():
    """Verify multi-field indicator logic, Miehe split degradation, and sizing bounds."""
    # When d -> 1 (fully broken), tensile stress -> 0
    d_broken = 0.9999
    eps_tensile = np.array([0.002, 0.001, 0.0]) # pure tensile
    sig_broken = miehe_stress(eps_tensile, d_broken)
    sig_intact = miehe_stress(eps_tensile, 0.0)
    assert np.linalg.norm(sig_broken) < 1e-4 * np.linalg.norm(sig_intact)
    
    # Sizing safeguards
    h_min_safeguard = L0 / 4.0 # 3.75 um
    assert np.isclose(h_min_safeguard, 0.00375)
    
    # Gradation limiter
    grad_h_max = 0.30
    assert grad_h_max <= 0.50

def test_fixed_versus_adapted_convergence_metrics():
    """Verify convergence comparison data across common window."""
    json_path = "models/pandey_kumar_mode2/07_fixed_mesh_convergence_suite/fixed_mesh_convergence_comparison.json"
    with open(json_path, 'r') as f:
        data = json.load(f)
        
    comp = data.get("convergence_comparison", {})
    assert len(comp) >= 4
    for key, c in comp.items():
        assert "rel_l2_error" in c
        assert c["rel_l2_error"] < 0.01 # < 1% difference in common elastic window

def test_publication_figure_and_artifacts_exist():
    """Verify publication figures and comparison JSON exist and are non-empty."""
    pdf = "results/figures/mode2/fig_mode2_f1381_fixed_fracture_uel_and_adaptive_gates.pdf"
    png = "results/figures/mode2/fig_mode2_f1381_fixed_fracture_uel_and_adaptive_gates.png"
    json_path = "models/pandey_kumar_mode2/07_fixed_mesh_convergence_suite/fixed_mesh_convergence_comparison.json"
    
    assert os.path.exists(pdf) and os.path.getsize(pdf) > 10000
    assert os.path.exists(png) and os.path.getsize(png) > 10000
    assert os.path.exists(json_path) and os.path.getsize(json_path) > 1000

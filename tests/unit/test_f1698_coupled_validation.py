# -*- coding: utf-8 -*-
"""
tests/unit/test_f1698_coupled_validation.py
============================================
Task F1698 Acceptance Tests:
Validates the numerical and physical findings of Task F1698:
1. Minimal Patch Passivity & Stress Parity (Gate A)
2. Mechanical non-passivity of simultaneous companion stress feedback (Force doubling)
3. Physical legitimacy of sequential damage-informed stress recovery
4. Multi-state Section 4.3 evaluation of single-frame vs envelope recovery (Gates C & D)
5. Bitwise inviolability of production UEL subroutine
"""

import os
import sys
import json
import hashlib
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULTS_DIR = os.path.join(REPO_ROOT, "results", "validation")
PATCH_JSON = os.path.join(RESULTS_DIR, "f1698_minimal_patch_validation.json")
SEC43_JSON = os.path.join(RESULTS_DIR, "f1698_sec43_five_state_recovery_analysis.json")
BASE_UEL = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
EXPECTED_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"

def test_production_uel_hash_preservation():
    """Verify bitwise inviolability of production UEL f42_mixed_uel.for."""
    assert os.path.exists(BASE_UEL), "f42_mixed_uel.for missing"
    with open(BASE_UEL, "rb") as f:
        actual_hash = hashlib.sha256(f.read()).hexdigest().lower()
    assert actual_hash == EXPECTED_UEL_SHA256, (
        "Production UEL modified! Expected %s, got %s" % (EXPECTED_UEL_SHA256, actual_hash)
    )

def test_minimal_patch_validation_exists():
    """Verify that minimal patch validation results JSON exists."""
    assert os.path.exists(PATCH_JSON), "f1698_minimal_patch_validation.json missing"
    with open(PATCH_JSON, "r") as f:
        data = json.load(f)
    assert "models" in data, "No models key in patch validation JSON"
    assert len(data["models"]) == 15, "Expected 15 test models in patch validation JSON"

def test_minimal_patch_model_a_analytical_accuracy():
    """Model A (Pure UEL) must match analytical reference within 1e-4 relative error."""
    with open(PATCH_JSON, "r") as f:
        data = json.load(f)
    
    models = data["models"]
    refs = data["analytical_references"]
    
    for sname in ["intact", "partially_damaged", "strongly_damaged"]:
        job_name = "PATCH_A_" + ("INTACT" if sname == "intact" else ("PARTIAL" if sname == "partially_damaged" else "STRONG"))
        m = models[job_name]
        ref_rf = refs[sname]["analytical_rf_y"]
        sim_rf = m["rf_y_total"]
        rel_err = abs(sim_rf - ref_rf) / ref_rf
        assert rel_err < 1e-4, (
            "Model A relative error on %s is %.2e, exceeds 1e-4" % (sname, rel_err)
        )
        assert m["exit_code"] == 0, "%s failed with non-zero exit code" % job_name

def test_minimal_patch_model_b1_equilibrium_and_zero_error():
    """Model B1 (STRESS=0, DDSDDE=1e-11) must preserve reference equilibrium but yield zero MISESERI."""
    with open(PATCH_JSON, "r") as f:
        data = json.load(f)
    
    models = data["models"]
    for sname in ["INTACT", "PARTIAL", "STRONG"]:
        mA = models["PATCH_A_" + sname]
        mB1 = models["PATCH_B1_" + sname]
        # Equilibrium preserved: RF matches Model A to within 1e-5
        rel_diff = abs(mB1["rf_y_total"] - mA["rf_y_total"]) / mA["rf_y_total"]
        assert rel_diff < 1e-5, "Model B1 failed to preserve equilibrium: rel_diff=%.2e" % rel_diff
        # Zero stress and zero error
        assert mB1["sigma_yy"] == 0.0, "Model B1 should have zero sigma_yy"
        assert mB1["miseseri_max"] == 0.0, "Model B1 should have zero MISESERI"

def test_minimal_patch_force_doubling_in_simultaneous_coupling():
    """Models B2 and B3 must demonstrate force doubling (200% of reference) due to companion Cauchy stress."""
    with open(PATCH_JSON, "r") as f:
        data = json.load(f)
    
    models = data["models"]
    for sname in ["INTACT", "PARTIAL", "STRONG"]:
        mA = models["PATCH_A_" + sname]
        mB2 = models["PATCH_B2_" + sname]
        mB3 = models["PATCH_B3_" + sname]
        
        ratio_b2 = mB2["rf_y_total"] / mA["rf_y_total"]
        ratio_b3 = mB3["rf_y_total"] / mA["rf_y_total"]
        
        # Exact 200% (2.0) within 1e-4
        assert abs(ratio_b2 - 2.0) < 1e-4, "Model B2 failed force doubling check: ratio=%.4f" % ratio_b2
        assert abs(ratio_b3 - 2.0) < 1e-4, "Model B3 failed force doubling check: ratio=%.4f" % ratio_b3

def test_minimal_patch_model_c_sequential_recovery_fidelity():
    """Model C must reproduce reference RF (100% of Model A) and active MISESERI."""
    with open(PATCH_JSON, "r") as f:
        data = json.load(f)
    
    models = data["models"]
    refs = data["analytical_references"]
    
    for sname in ["intact", "partially_damaged", "strongly_damaged"]:
        job_tag = "INTACT" if sname == "intact" else ("PARTIAL" if sname == "partially_damaged" else "STRONG")
        mA = models["PATCH_A_" + job_tag]
        mC = models["PATCH_C_" + job_tag]
        
        # RF matches Model A within 1e-4
        rel_diff = abs(mC["rf_y_total"] - mA["rf_y_total"]) / mA["rf_y_total"]
        assert rel_diff < 1e-4, "Model C RF mismatch on %s: rel_diff=%.2e" % (sname, rel_diff)
        
        # Stress matches analytical stress
        ref_syy = refs[sname]["analytical_sigma_yy"]
        sim_syy = mC["sigma_yy"]
        rel_s_err = abs(sim_syy - ref_syy) / ref_syy
        assert rel_s_err < 1e-4, "Model C sigma_yy mismatch on %s: rel_err=%.2e" % (sname, rel_s_err)
        
        # MISESERI is available
        assert mC["miseseri_available"] is True, "Model C should have active MISESERI"

def test_sec43_five_state_analysis_results():
    """Verify Section 4.3 multi-state recovery metrics and single-frame secondary corridor failure."""
    assert os.path.exists(SEC43_JSON), "f1698_sec43_five_state_recovery_analysis.json missing"
    with open(SEC43_JSON, "r") as f:
        data = json.load(f)
    
    states = data["states"]
    assert len(states) == 5, "Expected 5 analyzed states"
    
    # Every single-frame state must fail the secondary corridor at 0.00% <= l0/2
    for sid, st in states.items():
        assert st["pct_secondary_refined_h_le_half_l0"] == 0.0, (
            "State %s unexpectedly refined secondary corridor: %.2f%%" % (
                sid, st["pct_secondary_refined_h_le_half_l0"]
            )
        )
    
    # Verify State 4 has secondary corridor error jump (ratio > 2.0)
    st4 = states["state_4_sec_midprop"]
    assert st4["corridor_ratio_sec_to_prim"] > 2.0, (
        "State 4 should show secondary error dominance, got ratio=%.2f" % st4["corridor_ratio_sec_to_prim"]
    )
    
    # Multi-frame envelope
    env = data["multi_frame_envelope"]
    assert env["max_miseseri_secondary"] > 0.20, "Envelope secondary error should be > 0.20"

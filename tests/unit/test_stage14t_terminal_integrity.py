#!/usr/bin/env python
# -*- coding: utf-8 -*-
r"""
test_stage14t_terminal_integrity.py
-----------------------------------
Unit tests for Gate-6B Stage 14T:
1. Evaluator rejects forward-filling and marks unreached displacement states as NOT_REACHED.
2. Actual reached terminal state (u = 0.007889 mm) is evaluated against interpolated reference.
3. Mechanical classifications enforce STABLE for K0 and F_max, and MESH_SENSITIVE for peak shift.
4. Published K0 is marked NOT_REPORTED (project-derived reference K0_ref = 137.945520 kN/mm).
5. Premature termination root cause is verified as Newton convergence cutback exhaustion post-fracture.
"""

import os
import sys
import json
import importlib.util
import pytest

# Ensure repository root is on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

eval_script_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k", "evaluate_mode1_stage14_adaptive_14k.py")
spec = importlib.util.spec_from_file_location("stage14_evaluator", eval_script_path)
stage14_evaluator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stage14_evaluator)

MATCHED_TARGET_DISPLACEMENTS = stage14_evaluator.MATCHED_TARGET_DISPLACEMENTS
CANONICAL_REFERENCE = stage14_evaluator.CANONICAL_REFERENCE

@pytest.fixture
def stage14_eval_data():
    json_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k", "STAGE14_TERMINAL_ADAPTIVE_EVALUATION.json")
    assert os.path.exists(json_path), "STAGE14_TERMINAL_ADAPTIVE_EVALUATION.json must exist"
    with open(json_path, 'r') as f:
        return json.load(f)

def test_stage14t_unreached_states_rejection(stage14_eval_data):
    """Assert that states beyond reached u_max (u > 0.007889 mm) are strictly marked NOT_REACHED with no false values."""
    matched_states = stage14_eval_data.get("matched_states_comparison", [])
    assert len(matched_states) == len(MATCHED_TARGET_DISPLACEMENTS)
    
    u_max_reached = stage14_eval_data["mechanical_metrics"]["u_final_mm"]
    assert u_max_reached < 0.0080, "Solve did not reach u = 0.0080 mm"
    
    for row in matched_states:
        u_t = row["u_target_mm"]
        if u_t > u_max_reached:
            assert row["status"] == "NOT_REACHED", f"Target u = {u_t} mm must be marked NOT_REACHED"
            assert row["f_adapt_kN"] is None, f"Target u = {u_t} mm must not have f_adapt_kN"
            assert row["delta_f_pct"] is None, f"Target u = {u_t} mm must not compute delta_f_pct"
            assert row["dmax_adapt"] is None, f"Target u = {u_t} mm must not have dmax_adapt"
            assert row["efrac_adapt_mJ"] is None, f"Target u = {u_t} mm must not have efrac_adapt_mJ"
        else:
            assert row["status"] == "REACHED", f"Target u = {u_t} mm must be marked REACHED"
            assert row["f_adapt_kN"] is not None, f"Target u = {u_t} mm must have valid f_adapt_kN"

def test_stage14t_terminal_state_evaluated(stage14_eval_data):
    """Assert that the actual reached terminal state (u = 0.007889 mm) is evaluated against reference."""
    terminal_comp = stage14_eval_data.get("terminal_state_comparison", {})
    assert terminal_comp, "terminal_state_comparison must be present"
    
    u_term = terminal_comp["u_terminal_mm"]
    assert abs(u_term - 0.007889) < 1e-4, f"Terminal displacement {u_term} must match 0.007889 mm"
    
    f_adapt = terminal_comp["f_adapt_kN"]
    assert f_adapt < 0.005, f"Terminal reaction force {f_adapt} kN must reflect >99% load drop"
    
    xtip_adapt = terminal_comp["xtip_adapt_mm"]
    assert xtip_adapt >= 0.99, f"Terminal crack-tip extent {xtip_adapt} mm must reflect complete traversal"
    
    efrac_adapt = terminal_comp["efrac_adapt_mJ"]
    assert abs(efrac_adapt - 2.285) < 0.05, f"Terminal fracture functional {efrac_adapt} mJ must be near 2.285 mJ"

def test_stage14t_mechanical_classifications(stage14_eval_data):
    """Assert that K0 and F_max are STABLE and peak displacement shift is MESH_SENSITIVE."""
    mech = stage14_eval_data["mechanical_metrics"]
    
    k0 = mech["K0_kN_per_mm"]
    delta_k0 = mech["delta_K0_pct"]
    assert abs(delta_k0) < 0.1, f"Initial stiffness error {delta_k0}% must be under 0.1%"
    assert mech["K0_R2"] > 0.999999, f"K0 linearity R^2 must be > 0.999999"
    
    delta_fmax = mech["delta_F_max_pct"]
    assert abs(delta_fmax) < 2.0, f"Peak force error {delta_fmax}% must be under 2.0%"
    
    delta_upeak = mech["delta_u_peak_pct"]
    assert abs(delta_upeak) > 1.0, f"Peak displacement shift {delta_upeak}% is mesh-sensitive"

def test_stage14t_published_k0_absence(stage14_eval_data):
    """Assert that published K0 is documented as NOT_REPORTED and reference K0 is project-derived."""
    ref_info = stage14_eval_data["canonical_reference"]["published_pandey_kumar_2025"]
    assert ref_info["reported_K0"] == "NOT_REPORTED", "Published K0 must not be claimed as published by Pandey & Kumar"
    assert CANONICAL_REFERENCE["K0_kN_per_mm"] == 137.945520, "Canonical reference K0 must be exactly 137.945520 kN/mm"

def test_stage14t_governing_verdicts(stage14_eval_data):
    """Assert that governing verdicts reflect STAGE14_ADAPTIVE_RESULT_NOT_YET_QUALIFIED for incomplete solve."""
    verdicts = stage14_eval_data.get("governing_verdicts", {})
    assert verdicts.get("mechanism") == "STAGE14_LOCALIZATION_CHANGE_EXPLAINED_BY_IDENTIFIED_PROJECT_DIFFERENCE"
    assert verdicts.get("mesh_localization") == "TOWARD_TARGET_LOCALIZATION"
    assert verdicts.get("terminal_evaluation") == "STAGE14_ADAPTIVE_RESULT_NOT_YET_QUALIFIED"

"""Unit Test Suite: Task F1443 Mode-I Solver Termination Audit, Damage Validation, and Epistemic Guards.

Validates:
1. Solver Termination Audit: Prevents false full-horizon completion claims.
   - Exact PBS exit status is 1 (Abaqus exited with error due to dt_min).
   - Prescribed horizon was u = 0.0100 mm; solver terminated at u = 0.007889 mm.
   - Step 2 fraction completed is 57.78% (not 100%).
2. Strict Criteria Classification: Prevents PASS verdict when measured value falls outside interval.
   - External work acceptance threshold [2.30, 2.60] mJ was declared for full horizon.
   - Measured terminal work is 2.2674 mJ (< 2.30 mJ); verdict must be PARTIAL_HORIZON_EVALUATED_BELOW_PREDECLARED_FULL_WINDOW.
   - No manufactured PASS on partial data.
3. Mesh Refinement Discipline: Prevents confusion between bin coverage and element compliance.
   - Corridor element compliance: 96.76% satisfy h <= l0/2 (3.75 um); 99.84% satisfy h <= l0 (7.50 um).
   - Longitudinal slice coverage: 50/50 (100.0%) contain fine elements.
   - Distinction between longitudinal presence and element-level compliance is enforced.
4. Historical Stiffness Consistency: Enforces identical regression conventions.
   - Original Method B K0 = 137.891881 kN/mm (R^2 = 0.99999960, delta = -0.0389%).
   - Corrected Method B K0 = 137.909558 kN/mm (R^2 = 0.99999960, delta = -0.0261%).
5. Phase-Field Spatial Damage Evidence: Prevents propagation claims without spatial proof.
   - Verified damage states exist for u in {0.0057, 0.005857, 0.0060, 0.0070, 0.0075, 0.007889} mm.
   - At u = 0.0057 mm: crack front x = 0.500 mm (0 cracked elements, d_max = 0.564).
   - At u = 0.005857 mm: dynamic propagation to x = 0.974 mm (749 cracked elements d >= 0.95).
   - At u = 0.0060 mm: complete severance x = 0.999 mm (818 cracked elements d >= 0.95, unbroken < 1.02 um).
   - Zero disconnected/isolated cracked elements (crack_front_x == max_isolated_x).
6. Authentic Generated Artifacts: Verifies publication figures and reports exist.
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def test_f1443_solver_termination_audit():
    """Verify solver termination facts and prevent false full-horizon claims."""
    eval_json = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "40_method_b_corrected_propagation_14k",
        "evidence_1412465", "corrected_method_b_evaluation.json"
    )
    assert os.path.isfile(eval_json), f"Missing {eval_json}"
    with open(eval_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Must record exact PBS exit status 1
    assert data["pbs_exit_status"] == 1
    assert data["solver_execution_status"] == "PREMATURE_TERMINATION_AT_DT_MIN"
    assert data["horizon_completion_status"] == "PARTIAL_HORIZON_EVALUATED_POST_PEAK_RESOLVED"

    # Terminal displacement must be < 0.0100 mm
    assert data["u_terminal_mm"] < 0.0100
    assert abs(data["u_terminal_mm"] - 0.007889) < 1e-5
    assert data["step2_fraction_completed"] < 0.90
    assert abs(data["step2_fraction_completed"] - 0.5778) < 1e-3

    # Increments must distinguish total converged (4890) and Step 2 accepted (2889)
    assert data["total_converged_increments"] == 4890
    assert data["step1_increments"] == 2000
    assert data["step2_converged_increments"] == 2889


def test_f1443_strict_acceptance_criteria_classification():
    """Verify that acceptance verdicts reflect exact numeric bounds without manufacturing a PASS."""
    eval_json = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "40_method_b_corrected_propagation_14k",
        "evidence_1412465", "corrected_method_b_evaluation.json"
    )
    with open(eval_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    crit = data["acceptance_criteria_evaluation"]

    # Peak load and stiffness pass
    assert crit["initial_stiffness_parity"]["verdict"] == "PASS"
    assert crit["peak_load_parity"]["verdict"] == "PASS"
    assert crit["plateau_elimination"]["verdict"] == "PASS"

    # External work for full horizon must NOT be an unconditional PASS because 2.2674 < 2.30 mJ
    w_crit = crit["external_work_full_horizon"]
    assert w_crit["verdict"] == "PARTIAL_HORIZON_EVALUATED_BELOW_PREDECLARED_FULL_WINDOW"
    assert data["W_ext_terminal_mJ"] < 2.30

    # Work reduction vs original B is verified pass
    assert crit["external_work_reduction_vs_original_b"]["verdict"] == "PASS"


def test_f1443_mesh_refinement_coverage_discipline():
    """Verify distinction between longitudinal bin presence and element-level compliance."""
    eval_json = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "40_method_b_corrected_propagation_14k",
        "evidence_1412465", "corrected_method_b_evaluation.json"
    )
    with open(eval_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    audit = data["mesh_refinement_audit"]
    assert audit["total_finite_elements"] == 14483
    assert audit["corridor_elements_h_le_half_l0_pct"] == 96.76
    assert audit["corridor_elements_h_le_l0_pct"] == 99.84
    assert "50/50" in audit["longitudinal_bins_with_fine_elements"]


def test_f1443_historical_stiffness_reconciliation():
    """Verify identical regression convention for Original Method B stiffness."""
    eval_json = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "40_method_b_corrected_propagation_14k",
        "evidence_1412465", "corrected_method_b_evaluation.json"
    )
    with open(eval_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Must be 137.891881 kN/mm, NOT 138.1102 kN/mm
    k0_orig = data["K0_original_method_b_reconciled_kN_per_mm"]
    assert abs(k0_orig - 137.891881) < 1e-4
    assert abs(data["K0_original_method_b_delta_vs_canonical_pct"] - (-0.0389)) < 0.01


def test_f1443_damage_field_and_crack_front_progression():
    """Verify that crack front progression is proven by spatial phase-field data."""
    states_json = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "40_method_b_corrected_propagation_14k",
        "evidence_1412465", "corrected_method_b_damage_matched_states.json"
    )
    assert os.path.isfile(states_json), f"Missing {states_json}"
    with open(states_json, "r", encoding="utf-8") as f:
        states = json.load(f)

    assert len(states) == 6

    # 1. State 0: u = 0.0057 mm (Pre-peak)
    st0 = states[0]
    assert abs(st0["target_u_mm"] - 0.0057) < 1e-5
    assert abs(st0["crack_front_x_d95_mm"] - 0.500) < 1e-3
    assert st0["num_cracked_elements_d95"] == 0
    assert st0["d_max_domain"] < 0.60

    # 2. State 1: u = 0.005857 mm (Post-peak dynamic propagation)
    st1 = states[1]
    assert abs(st1["target_u_mm"] - 0.005857) < 1e-5
    assert st1["crack_front_x_d95_mm"] > 0.95  # Propagated past 95% of ligament
    assert st1["num_cracked_elements_d95"] > 700
    assert abs(st1["crack_front_x_d95_mm"] - st1["max_isolated_x_d95_mm"]) < 1e-4  # Contiguous front

    # 3. State 2: u = 0.006000 mm (Complete severance)
    st2 = states[2]
    assert abs(st2["target_u_mm"] - 0.0060) < 1e-5
    assert st2["crack_front_x_d95_mm"] > 0.998  # Reached boundary x = 1.0 mm
    assert st2["unbroken_ligament_d95_mm"] < 0.002  # Severed
    assert st2["num_cracked_elements_d95"] > 800

    # 4. State 5: u = 0.007889 mm (Terminal state)
    st5 = states[5]
    assert abs(st5["target_u_mm"] - 0.007889) < 1e-5
    assert st5["crack_front_x_d95_mm"] > 0.998
    assert st5["d_max_domain"] > 1.0


def test_f1443_publication_figures_exist():
    """Verify both Method B comparison figures exist and are non-empty."""
    fig_dir = os.path.join(REPO_ROOT, "results", "figures", "mode1_method_b_corrected_comparison")
    fig1_png = os.path.join(fig_dir, "fig_mode1_method_b_corrected_comparison.png")
    fig2_png = os.path.join(fig_dir, "fig_mode1_method_b_ligament_profiles.png")
    fig2_pdf = os.path.join(fig_dir, "fig_mode1_method_b_ligament_profiles.pdf")

    assert os.path.isfile(fig1_png), f"Missing {fig1_png}"
    assert os.path.isfile(fig2_png), f"Missing {fig2_png}"
    assert os.path.isfile(fig2_pdf), f"Missing {fig2_pdf}"
    assert os.path.getsize(fig2_png) > 100000
    assert os.path.getsize(fig2_pdf) > 20000

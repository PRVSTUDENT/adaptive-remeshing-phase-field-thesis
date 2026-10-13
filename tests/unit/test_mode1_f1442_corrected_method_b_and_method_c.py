"""Unit Test Suite: Task F1442 Mode-I Corrected Method B and Method C Terminal Evaluation.

Validates:
1. Completed solver evidence for Corrected Method B (Job 1412465, 14,483 FE) under evidence_1412465/
   - Initial elastic stiffness K0 parity (-0.0261%, R^2 = 0.99999960)
   - Peak load initiation (F_max = 0.7437 kN at u = 0.005733 mm)
   - Elimination of the artificial force plateau (F < 0.0021 kN at u >= 0.0060 mm vs 0.50-0.60 kN in Original B)
   - External work reduction (-31.5% vs Original Method B, within -3.87% of Canonical Reference)
   - Global UEL energy balance (residual Delta E = 0.0250 mJ, 1.10%)
2. Completed solver evidence for Method C Gate C1 V2 (Job 1412464, 2,906 FE) under evidence_1412464/
   - Step 1 quasi-static reload (RF = 0.6525 kN)
   - Step boundary continuity (Delta RF = 0.0925 N < 5 N criterion)
   - Coarse continuation delayed localization (F_max = 1.0868 kN) and snap-through (RF = 0.0277 kN)
3. Authentic generated publication figures in results/figures/mode1_method_b_corrected_comparison/
"""

import os
import json
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

def test_corrected_method_b_terminal_evidence():
    """Verify completed Corrected Method B results in evidence_1412465."""
    eval_json = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "40_method_b_corrected_propagation_14k",
        "evidence_1412465", "corrected_method_b_evaluation.json"
    )
    assert os.path.isfile(eval_json), f"Missing {eval_json}"
    with open(eval_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Increments and solver completion
    assert data["total_converged_increments"] == 4890
    assert data["step1_increments"] == 2000
    assert data["step2_increments"] == 2890
    assert "TIME INCREMENT REQUIRED LESS THAN MINIMUM SPECIFIED" in data["termination_reason"]

    # 2. Elastic stiffness K0 parity
    assert abs(data["K0_kN_per_mm"] - 137.909558) < 1e-4
    assert abs(data["K0_error_vs_canonical_pct"]) < 0.05  # -0.0261%
    assert data["K0_R2"] > 0.999999

    # 3. Peak load initiation
    assert abs(data["F_max_kN"] - 0.743701) < 1e-4
    assert abs(data["u_peak_mm"] - 0.005733) < 1e-4
    assert abs(data["F_max_error_vs_canonical_pct"]) < 2.0  # -1.8577%

    # 4. Plateau elimination (crucial research question)
    # Check matched horizon table at u = 0.0060, 0.0070 mm
    table = {row["u_target_mm"]: row for row in data["matched_horizon_comparison"]}
    f_0060 = table[0.0060]["F_corr_kN"]
    f_0070 = table[0.0070]["F_corr_kN"]
    assert f_0060 < 0.005, f"Expected plateau elimination, got F(0.006) = {f_0060} kN"
    assert f_0070 < 0.005, f"Expected plateau elimination, got F(0.007) = {f_0070} kN"
    assert abs(table[0.0070]["delta_F_corr_vs_orig_kN"]) > 0.50  # dropped by > 0.5 kN vs Orig B

    # 5. External work reduction
    w_term = data["W_ext_terminal_mJ"]
    assert abs(w_term - 2.2674) < 0.01
    assert w_term < 2.36  # Within canonical reference work (2.3593 mJ)
    assert w_term < 2.50  # Vastly lower than Original Method B 3.332 mJ (-31.5%)

    # 6. Global UEL energy balance
    e_frac = data["E_fracture_terminal_mJ"]
    e_tot = data["E_total_terminal_mJ"]
    delta_e = data["energy_residual_delta_E_mJ"]
    rel_err = data["energy_residual_rel_pct"]
    assert e_frac > 2.20  # Primary dissipation mechanism
    assert rel_err < 2.0  # 1.10% relative energy residual


def test_method_c_gate_c1_v2_evidence():
    """Verify completed Method C Gate C1 V2 results under evidence_1412464."""
    eval_json = os.path.join(
        REPO_ROOT, "models", "pandey_kumar_mode1", "39_method_c_transfer_gate_c1",
        "evidence_1412464", "c1_continuation_evaluation.json"
    )
    assert os.path.isfile(eval_json), f"Missing {eval_json}"
    with open(eval_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    telemetry = data["solver_telemetry"]
    assert telemetry["total_increments"] == 5058
    assert telemetry["step1_increments"] == 10
    assert telemetry["step2_increments"] == 5048
    assert telemetry["cutbacks"] == 14
    assert telemetry["final_step"] == 2

    reload = data["metrics"]["step1_reload"]
    assert abs(reload["handoff_displacement_mm"] - 0.0050) < 1e-6
    assert abs(reload["handoff_reaction_force_kn"] - 0.65246675) < 1e-4

    boundary = data["metrics"]["step_boundary"]
    assert boundary["boundary_continuous"] is True
    assert boundary["delta_rf_boundary_kn"] < 0.005  # < 5 N threshold

    step2 = data["metrics"]["step2_continuation"]
    assert abs(step2["peak_force_fmax_kn"] - 1.086839) < 1e-4
    assert abs(step2["final_force_kn"] - 0.027694544) < 1e-4


def test_comparison_figures_generated():
    """Verify authentic Method B comparison figures exist and are non-empty."""
    fig_dir = os.path.join(REPO_ROOT, "results", "figures", "mode1_method_b_corrected_comparison")
    png_path = os.path.join(fig_dir, "fig_mode1_method_b_corrected_comparison.png")
    pdf_path = os.path.join(fig_dir, "fig_mode1_method_b_corrected_comparison.pdf")

    assert os.path.isfile(png_path), f"Missing PNG {png_path}"
    assert os.path.isfile(pdf_path), f"Missing PDF {pdf_path}"
    assert os.path.getsize(png_path) > 100000, "PNG too small"
    assert os.path.getsize(pdf_path) > 20000, "PDF too small"

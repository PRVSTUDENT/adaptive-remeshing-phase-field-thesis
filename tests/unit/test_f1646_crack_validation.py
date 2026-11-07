# -*- coding: utf-8 -*-
"""Unit tests for F1646 source-backed crack-propagation validation and external work balance."""
import json
import csv
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def test_f1646_external_work_energy_balance():
    json_path = REPO_ROOT / "results" / "validation" / "f1646_work_energy_balance.json"
    assert json_path.exists(), "Work-energy balance JSON must exist"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Step 1 work-energy parity (< 0.01% error)
    step1 = data["step1_work_energy"]
    assert step1["relative_error"] < 1e-4, f"Step 1 work-energy relative error {step1['relative_error']} exceeds 1e-4"

    # Full propagation work-energy balance (< 5% error across all 246 increments)
    rel_err = data["work_energy_relative_error"]
    assert rel_err < 0.05, f"Full analysis work-energy relative error {rel_err} exceeds 5%"
    assert data["e_fracture_kNmm"] > 1.4e-3, f"Fracture dissipation must exceed 1.4 mJ, got {data['e_fracture_kNmm']}"

def test_f1646_crack_connectivity_across_thresholds():
    json_path = REPO_ROOT / "results" / "validation" / "f1646_crack_connectivity_analysis.json"
    assert json_path.exists(), "Crack connectivity analysis JSON must exist"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    thresh = data["threshold_sensitivity"]

    # Verify connection from notch tip to hole across all thresholds
    for t_str in ["0.5", "0.6", "0.7", "0.8", "0.85", "0.9", "0.95"]:
        assert t_str in thresh, f"Threshold {t_str} must be present in sensitivity analysis"
        res = thresh[t_str]
        assert res["connects_notch_to_hole"] is True, f"Crack must connect notch to hole at threshold d >= {t_str}"
        assert res["connected_to_notch_count"] >= 900, f"Connected elements count at d >= {t_str} must be >= 900"

def test_f1646_crack_deflection_trajectory():
    json_path = REPO_ROOT / "results" / "validation" / "f1646_crack_connectivity_analysis.json"
    assert json_path.exists(), "Crack connectivity analysis JSON must exist"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    thresh_09 = data["threshold_sensitivity"]["0.9"]
    # Unperturbed Mode-I has y = 0.50. Deflection toward hole at y=0.65 requires avg_y > 0.52
    assert thresh_09["avg_y_ahead_of_notch"] > 0.52, f"Crack path must deflect toward y=0.65, got {thresh_09['avg_y_ahead_of_notch']}"
    assert thresh_09["max_x"] > 0.60, f"Crack must reach hole region x > 0.60, got {thresh_09['max_x']}"

def test_f1646_uel_h_units_verification():
    uel_path = REPO_ROOT / "models" / "pandey_kumar_mode1" / "176_method_a_plate_with_hole" / "f42_mixed_uel.for"
    assert uel_path.exists(), "Frozen UEL file must exist"
    text = uel_path.read_text(encoding="utf-8")

    # Verify constitutive formulation
    assert "C11_0 = E_MOD*(ONE - E_NU)/((ONE + E_NU)*(ONE - TWO*E_NU))" in text
    assert "POS_M = HALF*C12_0*(E_POS**2) +" in text
    assert "STATEV(2)  = SV_H_TRIAL(PHYSIDX, KPT_IDX)" in text

def test_f1646_terminal_failure_diagnosis():
    json_path = REPO_ROOT / "results" / "validation" / "f1646_crack_connectivity_analysis.json"
    assert json_path.exists(), "Crack connectivity analysis JSON must exist"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    term = data["terminal_diagnosis"]
    assert term["total_increments"] == 246, "Must record 246 total increments"
    assert term["last_converged_increment"] == 195, "Last converged increment in Step 2 must be 195"
    assert term["first_failed_increment"] == 196, "First failed increment must be 196"
    assert term["limiting_mechanism"] == "MINIMUM_TIME_INCREMENT_EXCEEDED_AT_SNAPTHROUGH"
    assert 0.0075 <= term["last_converged_displacement_mm"] <= 0.0076, "Displacement must be in [0.0075, 0.0076] mm"

def test_f1646_thesis_figures_generated():
    figs_dir = REPO_ROOT / "docs" / "MA_AdaptiveRemeshing_Report_2026_main" / "figures"
    fig_files = [
        "fig_method_a_hole_force_displacement.png",
        "fig_method_a_hole_force_displacement.pdf",
        "fig_method_a_hole_energy_balance.png",
        "fig_method_a_hole_energy_balance.pdf",
        "fig_method_a_hole_crack_deflection.png",
        "fig_method_a_hole_crack_deflection.pdf"
    ]
    for fn in fig_files:
        fp = figs_dir / fn
        assert fp.exists() and fp.stat().st_size > 1000, f"Figure {fn} must exist and be non-empty"

# -*- coding: utf-8 -*-
"""Unit tests for F1644 Method A hole adapted mesh solve and comparison evidence."""
import json
import csv
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def test_f1644_analysis_completion():
    sta_path = REPO_ROOT / "results" / "validation" / "f1644_adapted_PK_HOLE_METHOD_A_ADAPT.sta"
    assert sta_path.exists(), "STA file must exist"
    text = sta_path.read_text(encoding="utf-8")
    assert "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in text, "Analysis must complete successfully"
    assert "1    50   1" in text, "All 50 increments of Step 1 must be present"

def test_f1644_pbs_exit_code():
    log_path = REPO_ROOT / "results" / "validation" / "f1644_adapted_pbs_execution.log"
    assert log_path.exists(), "PBS execution log must exist"
    text = log_path.read_text(encoding="utf-8")
    assert "Abaqus Finished with Exit Code: 0" in text, "Abaqus must exit with code 0"

def test_f1644_damage_and_history_bounds():
    summary_path = REPO_ROOT / "results" / "validation" / "f1644_adapted_extracted_summary.json"
    assert summary_path.exists(), "Extracted summary JSON must exist"
    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    frame = data["final_frame"]
    d_max = frame["damage_max"]
    d_min = frame["damage_min"]
    h_max = frame["history_max"]
    h_min = frame["history_min"]

    # Phase field bounds
    assert d_min >= 0.0, f"Damage must be non-negative, got {d_min}"
    assert d_max <= 1.0, f"Damage must be <= 1.0, got {d_max}"
    assert d_max >= 0.45, f"Damage must reach refined initiation levels (>= 0.45), got {d_max}"

    # History bounds
    assert h_min >= 0.0, f"History variable must be non-negative, got {h_min}"
    assert h_max >= 2.8, f"History maximum must reflect physical crack initiation (>= 2.8), got {h_max}"

    # Physical acceptance flags
    acceptance = frame["physical_acceptance"]
    assert acceptance["damage_bounds_valid"] is True
    assert acceptance["history_nonnegative"] is True
    assert acceptance["damage_initiation_detected"] is True

def test_f1644_energy_balance():
    csv_path = REPO_ROOT / "results" / "validation" / "f1644_adapted_uel_energy_balance.csv"
    assert csv_path.exists(), "Energy balance CSV must exist"

    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    assert len(rows) == 50, f"Must have 50 increment records, got {len(rows)}"

    final_row = rows[-1]
    e_elas = float(final_row["E_elastic_kNmm"])
    e_frac = float(final_row["E_fracture_kNmm"])
    e_tot = float(final_row["E_total_kNmm"])

    # Strict energy conservation: |E_elas + E_frac - E_tot| / E_tot < 1e-7 (single-precision Fortran output limit)
    residual = abs(e_elas + e_frac - e_tot) / e_tot
    assert residual < 1e-7, f"Energy conservation error {residual} exceeds 1e-7"

def test_f1644_reaction_force_parity():
    pilot_rf_path = REPO_ROOT / "results" / "validation" / "f1642_pilot_rf_displacement.csv"
    adapted_rf_path = REPO_ROOT / "results" / "validation" / "f1644_adapted_rf_displacement.csv"

    assert pilot_rf_path.exists() and adapted_rf_path.exists(), "Both RF CSV files must exist"

    with open(pilot_rf_path, "r", encoding="utf-8") as f:
        p_rows = list(csv.DictReader(f))
    with open(adapted_rf_path, "r", encoding="utf-8") as f:
        a_rows = list(csv.DictReader(f))

    assert len(p_rows) == 50 and len(a_rows) == 50, "Both runs must have 50 load increments"

    p_rf_final = float(p_rows[-1]["rf2_kN"])
    a_rf_final = float(a_rows[-1]["rf2_kN"])

    # Parity within 0.1%
    rel_diff = abs(a_rf_final - p_rf_final) / p_rf_final
    assert rel_diff < 0.001, f"Reaction force difference {rel_diff*100:.4f}% exceeds 0.1%"

def test_f1644_comparison_report_and_metrics():
    metrics_path = REPO_ROOT / "results" / "validation" / "f1644_comparison_metrics.json"
    report_path = REPO_ROOT / "results" / "validation" / "f1644_adapted_vs_pilot_comparison_report.md"

    assert metrics_path.exists(), "Comparison metrics JSON must exist"
    assert report_path.exists(), "Comparison report markdown must exist"

    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    assert metrics["task"] == "F1644-METHOD-A-HOLE-ADAPTED-SOLVE"
    assert metrics["adapted_f1644"]["job_id"] == "1421053.mmaster02"
    assert metrics["relative_differences_pct"]["damage_max_diff_pct"] > 5.0, "Damage peak must be >= 5% sharper"

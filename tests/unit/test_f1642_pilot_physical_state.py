# -*- coding: utf-8 -*-
"""Unit tests for F1642 Method A hole physical-state pilot execution evidence."""
import json
import csv
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def test_f1642_analysis_completion():
    sta_path = REPO_ROOT / "results" / "validation" / "f1642_pilot_PK_HOLE_METHOD_A_PROD.sta"
    assert sta_path.exists(), "STA file must exist"
    text = sta_path.read_text(encoding="utf-8")
    assert "THE ANALYSIS HAS COMPLETED SUCCESSFULLY" in text, "Analysis must complete successfully"
    assert "1    50   1" in text, "All 50 increments of Step 1 must be present"

def test_f1642_pbs_exit_code():
    log_path = REPO_ROOT / "results" / "validation" / "f1642_pilot_pbs_execution.log"
    assert log_path.exists(), "PBS execution log must exist"
    text = log_path.read_text(encoding="utf-8")
    assert "Abaqus Finished with Exit Code: 0" in text, "Abaqus must exit with code 0"

def test_f1642_damage_and_history_bounds():
    summary_path = REPO_ROOT / "results" / "validation" / "f1642_pilot_extracted_summary.json"
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
    assert d_max >= 0.40, f"Damage must reach initiation levels (>= 0.40), got {d_max}"

    # History bounds
    assert h_min >= 0.0, f"History variable must be non-negative, got {h_min}"
    assert h_max >= 2.0, f"History maximum must reflect physical crack initiation (>= 2.0), got {h_max}"

    # Physical acceptance flags
    acceptance = frame["physical_acceptance"]
    assert acceptance["damage_bounds_valid"] is True
    assert acceptance["history_nonnegative"] is True
    assert acceptance["damage_initiation_detected"] is True

def test_f1642_energy_balance():
    csv_path = REPO_ROOT / "results" / "validation" / "f1642_pilot_uel_energy_balance.csv"
    assert csv_path.exists(), "Energy balance CSV must exist"

    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    assert len(rows) == 50, f"Must have 50 increment records, got {len(rows)}"

    last = rows[-1]
    e_elas = float(last["E_elastic_kNmm"])
    e_frac = float(last["E_fracture_kNmm"])
    e_tot = float(last["E_total_kNmm"])

    assert e_elas > 0.0, "Elastic energy must be positive"
    assert e_frac > 0.0, "Fracture energy must be positive"
    rel_diff = abs((e_elas + e_frac) - e_tot) / e_tot
    assert rel_diff < 1e-6, f"Energy balance relative error must be < 1e-6, got {rel_diff}"

def test_f1642_load_displacement_history():
    rf_path = REPO_ROOT / "results" / "validation" / "f1642_pilot_rf_displacement.csv"
    assert rf_path.exists(), "RF displacement CSV must exist"

    rows = []
    with open(rf_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    assert len(rows) == 50, f"Must have 50 points, got {len(rows)}"
    final_u2 = float(rows[-1]["u2_mm"])
    final_rf2 = float(rows[-1]["rf2_kN"])

    assert pytest.approx(final_u2, abs=1e-5) == 0.0050
    assert final_rf2 > 0.50, f"Final reaction force should be ~0.53 kN, got {final_rf2}"

def test_f1642_spatial_damage_localization():
    dist_path = REPO_ROOT / "results" / "validation" / "f1642_pilot_damage_distribution.json"
    assert dist_path.exists(), "Damage distribution JSON must exist"
    with open(dist_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    max_elem = data["max_damage_element"]
    assert max_elem is not None
    # Slit tip is at (0.50, 0.50)
    assert abs(max_elem["x"] - 0.50) < 0.005, f"Max damage must be near slit tip x=0.50, got {max_elem['x']}"
    assert abs(max_elem["y"] - 0.50) < 0.005, f"Max damage must be near slit tip y=0.50, got {max_elem['y']}"

    # Damage zone d >= 0.10 must extend toward the hole at (0.65, 0.65)
    z01 = data["damage_zones"]["d_ge_0.10"]
    assert z01["count"] > 0
    assert z01["x_max"] > 0.65, f"Damage zone d>=0.10 should extend toward the hole (x>0.65), got {z01['x_max']}"
    assert z01["y_max"] > 0.60, f"Damage zone d>=0.10 should extend toward the hole (y>0.60), got {z01['y_max']}"

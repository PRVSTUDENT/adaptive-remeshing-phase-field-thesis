# -*- coding: utf-8 -*-
"""Unit tests for F1645 Method A hole crack propagation on adapted mesh."""
import json
import csv
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def test_f1645_analysis_completion():
    sta_path = REPO_ROOT / "results" / "validation" / "f1645_prop_PK_HOLE_METHOD_A_PROP.sta"
    assert sta_path.exists(), "STA file must exist"
    text = sta_path.read_text(encoding="utf-8")
    assert "1    50   1" in text, "All 50 increments of Step 1 must be present"
    assert "2     1   1" in text, "Step 2 must begin successfully"
    assert "2   196" in text, "Step 2 must advance to deep propagation (Inc 196)"

def test_f1645_pbs_execution():
    log_path = REPO_ROOT / "results" / "validation" / "f1645_prop_pbs_execution.log"
    assert log_path.exists(), "PBS execution log must exist"
    text = log_path.read_text(encoding="utf-8")
    assert "TOTAL OF        246  INCREMENTS" in text or "Run standard" in text, "Standard analysis must have executed"

def test_f1645_damage_and_history_bounds():
    summary_path = REPO_ROOT / "results" / "validation" / "f1645_propagation_extracted_summary.json"
    assert summary_path.exists(), "Extracted summary JSON must exist"
    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check step 2 frames
    s2_frames = data.get("steps", {}).get("Step-2", {}).get("frame_summaries", [])
    assert len(s2_frames) > 0, "Step 2 frame summaries must be present"

    final_frame = s2_frames[-1]
    d_max = final_frame["d_max"]
    d_min = final_frame["d_min"]
    h_max = final_frame["h_max"]

    assert d_min >= 0.0, f"Damage must be non-negative, got {d_min}"
    assert d_max <= 1.0 + 1e-4, f"Damage must be <= 1.0 (with float tol), got {d_max}"
    assert d_max >= 0.99, f"Crack must reach complete separation (d >= 0.99), got {d_max}"
    assert h_max >= 2.9, f"History variable must be >= 2.9 MPa, got {h_max}"

def test_f1645_crack_deflection():
    summary_path = REPO_ROOT / "results" / "validation" / "f1645_propagation_extracted_summary.json"
    assert summary_path.exists(), "Extracted summary JSON must exist"
    with open(summary_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    traj = data.get("crack_trajectory", {})
    assert "notch_tip" in traj, "Crack trajectory must contain notch_tip"
    assert traj["notch_tip"] == [0.50, 0.50], "Notch tip must be at (0.50, 0.50)"
    assert traj["hole_center"] == [0.65, 0.65], "Hole center must be at (0.65, 0.65)"

    # Verify deflection toward hole
    assert traj["fully_damaged_elements_count"] > 1000, f"Must have >1000 elements in crack band, got {traj['fully_damaged_elements_count']}"
    assert traj["max_crack_x"] > 0.65, f"Crack must penetrate past hole center x=0.65, got {traj['max_crack_x']}"
    assert traj["avg_y_crack"] > 0.55, f"Crack path must deflect upward toward hole y=0.65 (avg_y > 0.55), got {traj['avg_y_crack']}"
    assert data.get("crack_deflection_detected") is True, "Crack deflection toward hole must be detected"

def test_f1645_peak_load_and_softening():
    rf_path = REPO_ROOT / "results" / "validation" / "f1645_prop_rf_displacement.csv"
    assert rf_path.exists(), "RF displacement CSV must exist"

    with open(rf_path, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 246, f"Must have 246 increments, got {len(rows)}"

    max_rf_row = max(rows, key=lambda r: float(r["rf2_kN"]))
    max_rf = float(max_rf_row["rf2_kN"])
    u_at_peak = float(max_rf_row["u2_mm"])

    # Peak load criteria
    assert 0.53 <= max_rf <= 0.56, f"Peak reaction force must be in [0.53, 0.56] kN, got {max_rf}"
    assert 0.0051 <= u_at_peak <= 0.0053, f"Displacement at peak must be in [0.0051, 0.0053] mm, got {u_at_peak}"

    # Verify post-peak softening
    post_peak_rows = [r for r in rows if float(r["u2_mm"]) > 0.0055 and float(r["u2_mm"]) < 0.0065]
    assert len(post_peak_rows) > 0, "Must have post-peak softening points"
    min_post_peak_rf = min(float(r["rf2_kN"]) for r in post_peak_rows)
    assert min_post_peak_rf < max_rf * 0.85, f"Load must soften by at least 15% post-peak, got {min_post_peak_rf} vs peak {max_rf}"

def test_f1645_energy_balance():
    csv_path = REPO_ROOT / "results" / "validation" / "f1645_prop_uel_energy_balance.csv"
    assert csv_path.exists(), "Energy balance CSV must exist"

    rows = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)

    assert len(rows) >= 245, f"Must have >= 245 increments, got {len(rows)}"

    # Check energy conservation across all increments
    for row in rows:
        e_elas = float(row["E_elastic_kNmm"])
        e_frac = float(row["E_fracture_kNmm"])
        e_tot = float(row["E_total_kNmm"])
        if e_tot > 1e-5:
            residual = abs(e_elas + e_frac - e_tot) / e_tot
            assert residual < 1e-7, f"Energy conservation error {residual} exceeds 1e-7 at increment {row['Increment']}"

    # Check fracture energy surge
    initial_ef = float(rows[0]["E_fracture_kNmm"])
    final_ef = float(rows[-1]["E_fracture_kNmm"])
    assert final_ef > 1.0e-3, f"Final fracture energy must exceed 1.0e-3 kN mm, got {final_ef}"

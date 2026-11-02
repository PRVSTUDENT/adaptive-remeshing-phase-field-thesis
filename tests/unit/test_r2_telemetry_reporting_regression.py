"""Unit regression tests verifying R2 telemetry consistency, genuine contraction, and R8 execution.
Task: F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE
Protocol Version: 2
"""

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
R2_TELEMETRY = REPO_ROOT / "results" / "validation" / "package163_r2_live_telemetry_turn30.json"
INVESTIGATION_REPORT = REPO_ROOT / "results" / "validation" / "r2_telemetry_consistency_investigation.json"
R8_TELEMETRY = REPO_ROOT / "results" / "validation" / "package157_r8_live_telemetry_turn30.json"


def test_investigation_report_exists_and_passes():
    assert INVESTIGATION_REPORT.is_file(), f"Missing investigation report: {INVESTIGATION_REPORT}"
    with open(INVESTIGATION_REPORT, "r", encoding="utf-8") as f:
        rep = json.load(f)

    assert rep["schema"] == 1
    assert rep["investigation"] == "R2_TELEMETRY_CONSISTENCY_OUTER_119_VS_135"
    assert rep["job_id"] == "1419489.mmaster02"
    assert rep["comparison_119_vs_135"]["discrepancy_verdict"] == "NARRATIVE_REUSE_IN_REPORT"


def test_r2_outer_119_vs_135_genuine_contraction():
    assert R2_TELEMETRY.is_file(), f"Missing telemetry file: {R2_TELEMETRY}"
    with open(R2_TELEMETRY, "r", encoding="utf-8") as f:
        data = json.load(f)

    rec_119 = next((d for d in data if d["outer"] == 119), None)
    rec_135 = next((d for d in data if d["outer"] == 135), None)

    assert rec_119 is not None, "Outer 119 record missing"
    assert rec_135 is not None, "Outer 135 record missing"

    # Verify that solver telemetry was genuinely contracting, not plateaued
    assert rec_135["delta_u"] < rec_119["delta_u"]
    assert rec_135["delta_h"] < rec_119["delta_h"]

    # Verify exact authentic values
    assert rec_119["delta_u"] == pytest.approx(1.833239e-08, rel=1e-5)
    assert rec_135["delta_u"] == pytest.approx(1.142286e-08, rel=1e-5)
    assert rec_119["delta_h"] == pytest.approx(1.820626e-03, rel=1e-5)
    assert rec_135["delta_h"] == pytest.approx(1.119697e-03, rel=1e-5)

    # Active nodes pruned
    assert rec_135["pdas_active_count"] < rec_119["pdas_active_count"]
    assert rec_119["pdas_active_count"] == 3115
    assert rec_135["pdas_active_count"] == 3011


def test_r2_active_set_stabilization_and_near_convergence():
    with open(R2_TELEMETRY, "r", encoding="utf-8") as f:
        data = json.load(f)

    rec_152 = next((d for d in data if d["outer"] == 152), None)
    rec_153 = next((d for d in data if d["outer"] == 153), None)

    assert rec_152 is not None
    assert rec_153 is not None

    # Active set stabilized at 2951 nodes
    assert rec_152["pdas_active_count"] == 2951
    assert rec_153["pdas_active_count"] == 2951

    # Contraction accelerated: delta_d approaching coupled threshold (1.0e-5)
    assert rec_153["delta_d"] < rec_152["delta_d"]
    assert rec_153["delta_d"] == pytest.approx(1.045348e-05, rel=1e-5)
    assert rec_153["delta_u"] == pytest.approx(7.020749e-09, rel=1e-5)
    assert rec_153["delta_h"] == pytest.approx(6.802439e-04, rel=1e-5)

    # KKT satisfaction margin preserved
    assert rec_153["dual_error"] < 1.0e-6
    assert rec_153["free_error"] < 1.0e-6


def test_r8_live_execution_telemetry():
    assert R8_TELEMETRY.is_file(), f"Missing R8 telemetry file: {R8_TELEMETRY}"
    with open(R8_TELEMETRY, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) >= 1
    first = data[0]
    assert first["target_uy"] == pytest.approx(0.0018703125442191958, rel=1e-12)
    assert first["free_error"] < 1.0e-6
    assert first["dual_error"] < 1.0e-6

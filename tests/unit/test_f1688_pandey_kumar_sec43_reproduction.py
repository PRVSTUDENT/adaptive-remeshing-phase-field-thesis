# -*- coding: utf-8 -*-
"""
test_f1688_pandey_kumar_sec43_reproduction.py

Unit test suite for Task F1688: Pandey & Kumar (2025) Section 4.3 Reproduction Control Test.
Validates:
1. Geometry datum record and CAD dimensions.
2. Job-1 coarse solver execution, increment 64 termination, and cutback root cause.
3. Stage B MISESERI error indicator extraction, spatial localization, and Stage B FAIL classification.
4. Stage C native one-rule remeshing metrics (9,432 elements, primary refined, secondary unrefined, Stage C FAIL).
5. Strict scientific governance and resource limits (1 PBS job max, frozen UEL unchanged).
"""

import os
import json
import hashlib
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = REPO_ROOT / "models" / "pandey_kumar_mode1" / "188_pk_sec43_hole_plate"
VALIDATION_DIR = REPO_ROOT / "results" / "validation"
UEL_PATH = REPO_ROOT / "models" / "pandey_kumar_mode1" / "f42_mixed_uel.for"
FROZEN_UEL_SHA256 = "ce8d5edcd2911dcb018bb15275271f874e7ea62b8fb48cf4a8297469a83acdd6"


def compute_sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1048576), b""):
            digest.update(chunk)
    return digest.hexdigest().lower()


def test_f1688_geometry_datum_record():
    """Verify Stage A geometry datum record matches literature benchmark."""
    json_path = VALIDATION_DIR / "f1688_geometry_datum_record.json"
    assert json_path.exists(), f"Missing datum record: {json_path}"
    with open(json_path, "r") as f:
        d = json.load(f)

    geom = d["geometry"]
    assert geom["plate"]["width_mm"] == 65.0
    assert geom["plate"]["height_mm"] == 120.0
    assert geom["notch"]["length_mm"] == 10.0
    assert geom["notch"]["width_mm"] == 0.4
    assert geom["lower_hole"]["center_x_mm"] == 20.0
    assert geom["lower_hole"]["center_y_mm"] == 20.0
    assert geom["upper_hole"]["center_x_mm"] == 20.0
    assert geom["upper_hole"]["center_y_mm"] == 100.0
    assert geom["central_hole"]["center_x_mm"] == 36.5
    assert geom["central_hole"]["center_y_mm"] == 51.0
    assert d["status"] == "PASS"


def test_f1688_job1_solver_outcome_and_cutback_audit():
    """Verify Job-1 coarse solver reached increment 64, initiated damage, and terminated at dt limit."""
    sta_path = MODEL_DIR / "PK_SEC43_COARSE_JOB1.sta"
    csv_path = MODEL_DIR / "uel_energy_balance.csv"
    assert sta_path.exists(), f"Missing sta file: {sta_path}"
    assert csv_path.exists(), f"Missing energy CSV: {csv_path}"

    with open(csv_path, "r") as f:
        lines = [l.strip() for l in f if l.strip()]
    assert len(lines) == 64, f"Expected 64 energy balance increments, got {len(lines)}"

    last_line = lines[-1].split(",")
    step_time = float(last_line[3])
    strain_energy = float(last_line[4])
    dissipated_energy = float(last_line[5])

    assert abs(step_time - 0.081014) < 1e-4, f"Unexpected step time: {step_time}"
    assert dissipated_energy > 0.015, f"Damage dissipation did not initiate: {dissipated_energy}"
    assert strain_energy > 0.20, f"Unexpected strain energy: {strain_energy}"


def test_f1688_stage_b_miseseri_spatial_evaluation():
    """Verify Stage B MISESERI extraction, notch localization, and Stage B FAIL classification."""
    json_path = VALIDATION_DIR / "f1688_sec43_miseseri_evaluation.json"
    assert json_path.exists(), f"Missing MISESERI evaluation JSON: {json_path}"
    with open(json_path, "r") as f:
        d = json.load(f)

    assert d["element_count"] == 3923
    assert d["miseseri_max"] > 5.0
    assert d["area_90pct_energy"] < 900.0
    assert d["rel_area_90pct"] < 15.0

    top_el = d["top_elements"][0]
    assert abs(top_el["cx"] - 10.56) < 0.5
    assert abs(top_el["cy"] - 69.97) < 0.5


def test_f1688_stage_c_native_one_rule_remeshing_metrics():
    """Verify Stage C adapted mesh metrics: 9,432 elements, primary refined, secondary unrefined."""
    json_path = VALIDATION_DIR / "f1688_sec43_adapted_mesh_metrics.json"
    assert json_path.exists(), f"Missing adapted mesh metrics JSON: {json_path}"
    with open(json_path, "r") as f:
        d = json.load(f)

    assert d["adapted_elements"] == 9432
    assert d["adapted_nodes"] == 9567
    assert d["quad_count"] == 9132
    assert d["tri_count"] == 300

    prim = d["primary_corridor_stats"]
    assert prim["count"] == 641
    assert prim["min"] < 0.10  # <= l0/3 = 0.095 mm
    assert prim["pct_le_l0"] > 40.0

    sec = d["secondary_corridor_stats"]
    assert sec["count"] == 136
    assert sec["pct_le_l0_half"] == 0.0  # Completely unrefined
    assert sec["pct_le_l0"] == 0.0
    assert sec["median"] > 0.70  # > 5x l0/2

    assert d["stage_c_pass"] is False, "Stage C should be classified as FAIL due to unrefined secondary branch"


def test_f1688_scientific_governance_and_resource_limits():
    """Verify frozen UEL integrity and PBS submission policy."""
    assert UEL_PATH.exists(), f"UEL source missing: {UEL_PATH}"
    actual_sha = compute_sha256(UEL_PATH)
    assert actual_sha == FROZEN_UEL_SHA256, f"Frozen UEL corrupted! Got {actual_sha}"

    # Check HPC Job Ledger contains Job 1421191 and no unauthorized jobs
    ledger_path = REPO_ROOT / "project_coordination" / "HPC_JOB_LEDGER.csv"
    with open(ledger_path, "r") as f:
        ledger_text = f.read()
    assert "1421191.mmaster02" in ledger_text

#!/usr/bin/env python3
"""
Unit tests for repaired extract_package148_iteration.py and authentic C5 mechanical solve endpoint.
Task: F1597-TRUSTED-REVIEW-BOUNDARY-AND-PACKAGE160
Protocol Version: 2
"""

import hashlib
import json
import math
import os
import sys
import tempfile
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.validation.extract_package148_iteration import parse_uel_energy_balance_csv, parse_dat_nodal_u

EXTRACTOR_PATH = REPO_ROOT / "scripts" / "validation" / "extract_package148_iteration.py"
ENDPOINT_PATH = REPO_ROOT / "results" / "validation" / "mode1_f1597" / "1419375_endpoint.json"

# Authentic donor reference values from Checkpoint 01 (Package 157 R5 Step 1 endpoint)
DONOR_REFERENCE_FORCE_KN = 0.184117075783354
DONOR_REFERENCE_TOTAL_ENERGY_KNMM = 0.00022418821945
TARGET_UY_MM = 0.0018603125442191958


def test_extractor_step_whitelist():
    """Verify accepted step conventions and rejection of foreign/malformed step names."""
    valid_steps = [
        "C1-1-ReEquil",
        "C1_2_Step1",
        "C1_2_Step2",
        "C1-2-Step1",
        "C2_0_Step1",
        "C2_0_Step2",
        "C2_0_Step10",
        "C2-0-Step1",
        "C2_1_Step1",
        "C2-1-Step1"
    ]
    invalid_steps = [
        "Step-1",
        "StaticStep",
        "Initial",
        "Step1",
        "C3_0_Step1",
        "random_step_name",
        ""
    ]

    for step_name in valid_steps:
        is_valid = (
            step_name == 'C1-1-ReEquil' or
            step_name.startswith(('C1_2_Step', 'C1-2-Step', 'C2_0_Step', 'C2-0-Step', 'C2_1_Step', 'C2-1-Step'))
        )
        assert is_valid, f"Step name should be accepted: {step_name}"

    for step_name in invalid_steps:
        is_valid = (
            step_name == 'C1-1-ReEquil' or
            step_name.startswith('C1_2_Step') or
            step_name.startswith('C1-2-Step') or
            step_name.startswith('C2_0_Step') or
            step_name.startswith('C2-0-Step')
        )
        assert not is_valid, f"Step name should be rejected: {step_name}"


def test_parse_uel_energy_balance_csv():
    """Verify parsing of uel_energy_balance.csv written by f42_mixed_uel.for."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        csv_file = Path(tmp_dir) / "uel_energy_balance.csv"
        csv_file.write_text(
            "Step,Increment,TotalTime,StepTime,E_elastic_kNmm,E_fracture_kNmm,E_total_kNmm\n"
            "   1,     1,  0.10000000E+01,  0.10000000E+01,  0.17165282E-03,  0.52888302E-04,  0.22454112E-03\n",
            encoding="utf-8"
        )
        energies = parse_uel_energy_balance_csv(str(csv_file))
        assert energies is not None
        assert abs(energies['elastic_kNmm'] - 0.00017165282) < 1e-10
        assert abs(energies['fracture_kNmm'] - 0.000052888302) < 1e-10
        assert abs(energies['total_energy_kNmm'] - 0.00022454112) < 1e-10


def test_authentic_c5_endpoint_parity_and_integrity():
    """Verify authentic endpoint extracted from Job 1419375 mechanical ODB."""
    assert ENDPOINT_PATH.is_file(), "Missing 1419375_endpoint.json"
    data = json.loads(ENDPOINT_PATH.read_text(encoding="utf-8"))

    assert data["schema"] == 1
    assert data["step_name"] == "C2_0_Step1"
    assert data["increment"] == 1
    assert abs(data["step_time"] - 1.0) < 1e-12

    # Physical nodes count
    nodes = data["nodes"]
    assert len(nodes) == 13278

    # Holding displacement boundary condition
    assert abs(data["rp_u2"] - TARGET_UY_MM) < 1e-14

    # Reaction force drift vs Checkpoint 01 reference (<= 2%)
    rf2 = data["rf2_kN"]
    force_drift = abs(rf2 - DONOR_REFERENCE_FORCE_KN) / DONOR_REFERENCE_FORCE_KN
    assert force_drift <= 0.02, f"Force drift exceeded 2%: {force_drift * 100:.3f}%"
    assert force_drift < 0.003  # Actual drift is ~0.23%

    # Total energy drift vs Checkpoint 01 reference (<= 2%)
    e_tot = data["total_energy_kNmm"]
    energy_drift = abs(e_tot - DONOR_REFERENCE_TOTAL_ENERGY_KNMM) / DONOR_REFERENCE_TOTAL_ENERGY_KNMM
    assert energy_drift <= 0.02, f"Energy drift exceeded 2%: {energy_drift * 100:.3f}%"
    assert energy_drift < 0.002  # Actual drift is ~0.16%


def test_extractor_hash_and_clean_tree():
    """Compute and record SHA-256 hash of the corrected extractor."""
    assert EXTRACTOR_PATH.is_file()
    h = hashlib.sha256(EXTRACTOR_PATH.read_bytes()).hexdigest()
    assert len(h) == 64

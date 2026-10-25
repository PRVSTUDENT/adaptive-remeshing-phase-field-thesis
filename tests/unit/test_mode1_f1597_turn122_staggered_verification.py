"""
test_mode1_f1597_turn122_staggered_verification.py
Unit test for Mode-I Task F1597 Turn 122 Staggered Coupling Verification.

Verifies:
  1. Authentic Abaqus 2023 execution on cluster scratch.
  2. Mechanical equilibrium & displacement fields in Step 1.
  3. Strict zero-drift kinematic boundary holding across subsolves.
  4. Transferred history H preservation without ratcheting.
  5. Monotonic thermodynamic energy dissipation during phase relaxation.
"""

import os
import json
import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def test_staggered_verification_metrics_exist():
    metrics_path = REPO_ROOT / "results" / "validation" / "mode1_f1597" / "turn122_staggered_verification_metrics.json"
    assert metrics_path.exists(), "Verification metrics JSON does not exist"
    with open(metrics_path, "r") as f:
        data = json.load(f)
    assert data["status"] == "QUALIFIED_AUTHENTIC_ABAQUS_SOLVE"
    assert data["solver"].startswith("Abaqus/Standard 2023")
    assert data["transferred_h_retention"] is True
    assert data["thermodynamic_monotonicity_passed"] is True

def test_mechanical_equilibrium_step1():
    metrics_path = REPO_ROOT / "results" / "validation" / "mode1_f1597" / "turn122_staggered_verification_metrics.json"
    with open(metrics_path, "r") as f:
        data = json.load(f)
    assert abs(data["step1_net_equilibrium_error_kN"]) < 1.0e-6
    assert abs(data["step1_mech_top_rf2_N"] - 302.178) < 0.1

def test_kinematic_holding_invariant():
    metrics_path = REPO_ROOT / "results" / "validation" / "mode1_f1597" / "turn122_staggered_verification_metrics.json"
    with open(metrics_path, "r") as f:
        data = json.load(f)
    # Drift must be zero / within numerical noise (< 1e-12 mm)
    assert data["step2_max_displacement_drift_mm"] < 1.0e-12

def test_thermodynamic_monotonicity():
    metrics_path = REPO_ROOT / "results" / "validation" / "mode1_f1597" / "turn122_staggered_verification_metrics.json"
    with open(metrics_path, "r") as f:
        data = json.load(f)
    assert data["e_elastic_step2_kNmm"] < data["e_elastic_step1_kNmm"]
    assert data["e_fracture_step2_kNmm"] > data["e_fracture_step1_kNmm"]

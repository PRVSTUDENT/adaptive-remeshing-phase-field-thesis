"""
Unit test suite verifying the comprehensive F1603 numerical diagnosis artifact:
results/validation/f1603_c6_r6_numerical_diagnosis.json
"""

import hashlib
import json
import sys
from pathlib import Path
import pytest

WORKSPACE = Path(__file__).resolve().parents[2]
ARTIFACT_PATH = WORKSPACE / "results/validation/f1603_c6_r6_numerical_diagnosis.json"
SCRIPT_PATH = WORKSPACE / "scripts/validation/diagnose_f1603_r6_convergence_mechanisms.py"

if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))

from scripts.validation.diagnose_f1603_r6_convergence_mechanisms import run_diagnosis


def test_f1603_diagnosis_artifact_exists_and_valid():
    assert ARTIFACT_PATH.exists(), f"Missing diagnosis artifact: {ARTIFACT_PATH}"
    with open(ARTIFACT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("schema") == 1
    assert data.get("task_id") == "F1603-MODE1-C6-R6-NONCONVERGENCE-INVESTIGATION"
    assert data.get("verification_passed") is True

    # R1 assertions
    r1 = data.get("r1_undamped_benchmark", {})
    assert r1.get("omega_d") == 1.0
    assert r1.get("total_iterations") == 23
    assert r1.get("divergent_growth_factor") > 4.0

    # R6 assertions
    r6 = data.get("r6_damped_investigation", {})
    assert r6.get("omega_d") == 0.5
    assert r6.get("total_iterations") == 100
    assert abs(r6.get("terminal_delta_d") - 0.0083084) < 1e-5
    assert abs(r6.get("terminal_delta_u_mm") - 5.6421e-5) < 1e-7
    assert abs(r6.get("terminal_delta_h_MPa") - 378.74) < 0.1
    assert r6.get("active_set_contraction", {}).get("final_count") == 160
    assert r6.get("active_set_contraction", {}).get("reduction_percentage") > 98.0

    # Tail metrics
    tail30 = r6.get("tail_30_iterations", {})
    assert 0.985 < tail30.get("mean_contraction_ratio_d") < 0.995

    tail20 = r6.get("tail_20_iterations", {})
    assert tail20.get("coefficient_of_variation") < 0.10
    assert tail20.get("active_set_changes_total") == 174
    assert tail20.get("is_active_set_stabilized") is False

    # Spatial telemetry limitation
    spatial = data.get("spatial_evidence_evaluation", {})
    assert spatial.get("spatial_telemetry_logged_in_records") is False
    assert "EXPLICIT LIMITATION" in spatial.get("spatial_status_note")

    # Mathematical operator analysis
    math_diag = data.get("mathematical_diagnosis", {})
    assert math_diag.get("is_true_spectral_radius") is False
    assert "NON_STATIONARY_ACTIVE_SET_CONVERGENCE_PLATEAU" in math_diag.get("operator_nature")

    # Proposal
    prop = data.get("falsifiable_successor_proposal", {})
    assert prop.get("candidate_id") == "M1_C6_P171_R7_ADAPTIVE_DAMPED"
    assert len(prop.get("safeguards")) >= 4


def test_script_and_artifact_reproducibility():
    assert SCRIPT_PATH.exists()
    res = run_diagnosis()
    assert res.get("schema") == 1
    assert res.get("verification_passed") is True

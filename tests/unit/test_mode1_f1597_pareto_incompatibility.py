"""Unit tests for F1597 Pareto Incompatibility Theorem and State-Transfer Feasibility."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest
from scripts.validation.audit_f1597_pareto_incompatibility_and_feasibility import (
    load_canonical_measurements,
    compute_pareto_frontier,
    run_full_pareto_audit,
    EXPECTED_DONOR_SHA256,
    EXPECTED_UEL_SHA256,
    sha256_file,
    CANDIDATE_DONOR_PATH,
    PRODUCTION_UEL_PATH,
)


def test_canonical_measurements_loaded():
    m = load_canonical_measurements()
    assert abs(m["donor_target_rf2_N"] - 7.8512395) < 1e-4
    assert abs(m["frozen_baseline_rf2_N"] - 9.9785) < 1e-4
    assert abs(m["frozen_baseline_rf2_error_pct"] - 27.0949) < 1e-2
    assert abs(m["frozen_baseline_fracture_energy_error_pct"] - 0.793) < 1e-2
    assert abs(m["coupled_equilibrated_rf2_N"] - 0.3655) < 1e-4
    assert abs(m["coupled_equilibrated_rf2_error_pct"] - (-95.3441)) < 1e-2
    assert abs(m["crack_tip_surge_ratio"] - 12.6932) < 1e-2


def test_pareto_frontier_incompatibility_proof():
    pareto = compute_pareto_frontier()
    assert pareto["incompatibility_theorem_proven"] is True
    assert pareto["simultaneous_equilibrium_possible"] is False
    assert len(pareto["pareto_curve"]) == 21
    # Check that frozen state fails force tolerance
    frozen_pt = pareto["pareto_curve"][0]
    assert frozen_pt["rf2_pass_5pct"] is False
    assert frozen_pt["fracture_energy_pass_2pct"] is True
    # Check that equilibrated state fails both
    equil_pt = pareto["pareto_curve"][-1]
    assert equil_pt["rf2_pass_5pct"] is False
    assert equil_pt["fracture_energy_pass_2pct"] is False


def test_production_uel_and_candidate_donor_hashes():
    assert sha256_file(PRODUCTION_UEL_PATH) == EXPECTED_UEL_SHA256
    assert sha256_file(CANDIDATE_DONOR_PATH) == EXPECTED_DONOR_SHA256


def test_full_pareto_audit():
    import json
    res = run_full_pareto_audit()
    assert res["schema"] == 1
    assert res["task_id"] == "F1597-CORRECT-PACKAGE72-STATE-TRANSFER"
    assert res["status"] == "PREPARATION_COMPLETE"
    assert res["verification_passed"] is True
    assert len(res["finding"]) >= 20
    assert res["classification"] == "PARETO_INCOMPATIBILITY_THEOREM_PROVEN__DONOR_REFINEMENT_REQUIRED"
    assert res["pareto_analysis"]["incompatibility_theorem_proven"] is True

    # Save to results/validation
    out_file = REPO_ROOT / "results/validation/f1597_pareto_incompatibility_audit.json"
    res["evidence_sources"]["scripts/validation/audit_f1597_pareto_incompatibility_and_feasibility.py"] = sha256_file(REPO_ROOT / "scripts/validation/audit_f1597_pareto_incompatibility_and_feasibility.py")
    res["evidence_sources"]["tests/unit/test_mode1_f1597_pareto_incompatibility.py"] = sha256_file(Path(__file__).resolve())
    out_text = json.dumps(res, indent=2).replace("\r\n", "\n") + "\n"
    out_file.write_bytes(out_text.encode("utf-8"))
    assert out_file.exists()

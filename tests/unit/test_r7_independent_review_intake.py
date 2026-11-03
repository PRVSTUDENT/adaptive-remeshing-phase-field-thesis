"""
Unit test suite verifying Candidate M1_C6_P171_R7_ADAPTIVE_DAMPED
independent review intake audit and verification findings.
"""

import json
from pathlib import Path
import pytest

WORKSPACE = Path(__file__).resolve().parents[2]


def test_r7_independent_review_intake_audit():
    audit_path = WORKSPACE / "results/validation/r7_independent_review_intake_audit.json"
    assert audit_path.exists(), f"Missing audit artifact: {audit_path}"

    with open(audit_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("schema") == 1
    assert data.get("operation") == "independent_review_intake_audit"
    assert data.get("candidate_job") == "M1_C6_P171_R7_ADAPTIVE_DAMPED"
    assert data.get("correlation_id") == "HND-F1604-R7-REVIEW-0639CEEF"
    assert data.get("fingerprint") == "0639CEEFF9C2F1E14034B95DFADEF089A247723F6C914D8028BC7ADFD3BEED5E"
    assert data.get("status") == "REVIEW_PENDING"
    assert data.get("verification_passed") is True

    # Check scientific hypothesis details
    hyp = data.get("scientific_hypothesis", {})
    assert hyp.get("initial_damping_omega_d") == 0.5
    assert hyp.get("candidate_relaxation_omega_d") == 0.85
    assert hyp.get("membership_stabilization_threshold") == 2
    assert hyp.get("consecutive_iterations_required") == 3
    assert hyp.get("residual_growth_rollback_threshold_pct") == 5.0
    assert hyp.get("force_discrepancy_gate_pct") == 2.0
    assert hyp.get("energy_discrepancy_gate_pct") == 2.0
    assert hyp.get("frozen_uel_sha256") == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

    # Epistemic limitations
    epistemic = hyp.get("epistemic_limits", {})
    assert epistemic.get("spatial_coordinates_telemetry") == "ABSENT_IN_SOLVER_RECORDS"
    assert epistemic.get("convergence_in_35_to_50_iterations") == "UNPROVEN_EMPIRICAL_TARGET"

    # Validation checks
    checks = data.get("validation_checks", {})
    assert checks.get("candidate_definition_verified") is True
    assert checks.get("relaxation_hypothesis_verified") is True
    assert checks.get("active_set_membership_distinguished_from_cardinality") is True
    assert checks.get("rollback_safeguard_verified") is True
    assert checks.get("kkt_and_irreversibility_verified") is True
    assert checks.get("coupled_convergence_tolerances_verified") is True
    assert checks.get("epistemic_limits_acknowledged") is True
    assert checks.get("packet_fingerprint_verified") is True
    assert checks.get("review_correlation_id_matched") is True
    assert checks.get("review_fingerprint_matched") is True
    assert checks.get("review_outcome") == "REVIEW_PENDING"
    assert checks.get("no_unqualified_submission") is True

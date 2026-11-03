"""
Unit test suite verifying Candidate M1_C6_P171_R7_ADAPTIVE_DAMPED definition,
mathematical adaptive-relaxation specification, and review dispatch packet.
"""

import hashlib
import json
from pathlib import Path
import pytest
import sys

WORKSPACE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKSPACE / "scripts/controller"))


def test_r7_adaptive_relaxation_specification_schema_and_gates():
    spec_path = WORKSPACE / "results/validation/r7_adaptive_relaxation_specification.json"
    assert spec_path.exists(), f"Missing specification: {spec_path}"

    with open(spec_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("schema") == 1
    assert data.get("candidate_id") == "M1_C6_P171_R7_ADAPTIVE_DAMPED"
    assert data.get("verification_passed") is True

    # Check mathematical formulation
    math_form = data.get("mathematical_formulation", {})
    p1 = math_form.get("phase_1_relaxation", {})
    assert p1.get("damping_factor") == 0.5

    p2 = math_form.get("phase_2_candidate_relaxation", {})
    assert p2.get("candidate_damping_factor") == 0.85

    telemetry = math_form.get("active_set_telemetry_and_membership_criterion", {})
    assert telemetry.get("stabilization_threshold") == 2
    assert telemetry.get("consecutive_iterations_required") == 3
    assert "membership" in telemetry.get("cardinality_vs_membership_distinction", "").lower()

    rollback = math_form.get("safeguard_rollback_mechanism", {})
    assert rollback.get("growth_threshold_factor") == 1.05

    # Check epistemic limits
    epistemic = data.get("epistemic_limits_and_scientific_discipline", {})
    assert "spatial" in epistemic.get("spatial_coordinates_logging", "").lower()
    assert "empirical" in epistemic.get("convergence_rate_conjecture", "").lower()

    # Check acceptance criteria
    acc = data.get("acceptance_criteria", {})
    assert acc.get("delta_d_max") == 1e-05
    assert acc.get("delta_u_mm_max") == 1e-09
    assert acc.get("delta_h_MPa_max") == 0.0001
    assert acc.get("final_consistency_delta_u_mm_max") == 1e-09
    assert acc.get("final_consistency_delta_h_MPa_max") == 0.0001
    assert acc.get("signed_kkt_dual_kNmm_max") == 1e-06
    assert acc.get("signed_kkt_free_kNmm_max") == 1e-06
    assert acc.get("max_healing_tolerance") == 1e-06
    assert acc.get("force_discrepancy_pct_max") == 2.0
    assert acc.get("total_energy_discrepancy_pct_max") == 2.0
    assert acc.get("frozen_uel_sha256") == "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def test_r7_candidate_definition_and_evidence_hashes():
    cand_path = WORKSPACE / "project_coordination/candidate_definitions/execute_mode1_package171_r7_c6_coupled_reequilibration.json"
    assert cand_path.exists(), f"Missing candidate definition: {cand_path}"

    with open(cand_path, "r", encoding="utf-8") as f:
        cand = json.load(f)

    assert cand.get("schema") == 1
    assert cand.get("operation_id") == "execute_mode1_package171_r7_c6_coupled_reequilibration"
    assert cand.get("candidate_job") == "M1_C6_P171_R7_ADAPTIVE_DAMPED"
    assert cand.get("registration_status") == "PROPOSED_FOR_INDEPENDENT_REVIEW"
    assert cand.get("operation_mode") == "QUALIFIED_EXECUTION"

    sources = cand.get("evidence_sources", {})
    assert len(sources) >= 4

    for rel_path, expected_hash in sources.items():
        file_path = WORKSPACE / rel_path
        assert file_path.exists(), f"Evidence source missing: {file_path}"
        actual_hash = hashlib.sha256(file_path.read_bytes()).hexdigest().upper()
        assert actual_hash == expected_hash.upper(), f"Hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}"


def test_r7_review_dispatch_packet():
    from review_dispatcher import packet

    req = packet(WORKSPACE, "execute_mode1_package171_r7_c6_coupled_reequilibration")
    assert req.get("schema") == 1
    assert req.get("operation_id") == "execute_mode1_package171_r7_c6_coupled_reequilibration"
    assert len(req.get("fingerprint", "")) == 64
    assert len(req.get("hashes", {})) >= 5

    # Check request and dispatch state files
    fp = req["fingerprint"]
    req_path = WORKSPACE / f"project_coordination/review_dispatch/execute_mode1_package171_r7_c6_coupled_reequilibration-{fp}.request.json"
    assert req_path.exists(), f"Missing request file: {req_path}"

    manifest_key = hashlib.sha256((WORKSPACE / req["definition"]["manifest"]).read_bytes()).hexdigest().lower()
    disp_path = WORKSPACE / f"project_coordination/review_dispatch/execute_mode1_package171_r7_c6_coupled_reequilibration-{manifest_key}.json"
    assert disp_path.exists(), f"Missing dispatch state file: {disp_path}"

    with open(disp_path, "r", encoding="utf-8") as f:
        disp = json.load(f)

    assert disp.get("status") == "REVIEW_PENDING"
    assert disp.get("correlation_id", "").startswith("HND-F1604-R7-REVIEW-")
    assert disp.get("fingerprint") == fp

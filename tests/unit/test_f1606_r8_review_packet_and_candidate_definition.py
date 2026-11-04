#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit test suite for Candidate Package 171-R8 Candidate Definition and Review Packet
Task: F1606-MODE1-C6-R7-NONCONVERGENCE-INVESTIGATION
Successor: F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION
"""

import hashlib
import json
from pathlib import Path
import pytest

WORKSPACE = Path(__file__).resolve().parents[2]
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_OPERATION = "execute_mode1_package171_r8_c6_coupled_reequilibration"
EXPECTED_FINGERPRINT = "8D0545A3A733B1368DBA705880C71FD8E2D797B09AF4920FDB1E76688EA52D1F"
EXPECTED_CORRELATION = "HND-F1607-R8-REVIEW-8D0545A3"


def compute_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def test_frozen_uel_preservation():
    uel_path = WORKSPACE / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for"
    assert uel_path.exists(), f"UEL file missing: {uel_path}"
    assert compute_sha256(uel_path) == FROZEN_UEL_SHA256


def test_r8_candidate_definition_structure():
    cand_path = WORKSPACE / f"project_coordination/candidate_definitions/{EXPECTED_OPERATION}.json"
    assert cand_path.exists(), f"Candidate definition missing: {cand_path}"
    with open(cand_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["schema"] == 1
    assert data["operation_id"] == EXPECTED_OPERATION
    assert data["candidate_job"] == "M1_C6_P171_R8_ADAPTIVE_DAMPED"
    assert data["task_id"] == "F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION"
    assert data["stage"] == "C3-0"
    assert data["operation_mode"] == "QUALIFIED_EXECUTION"
    assert data["registration_status"] == "PROPOSED_FOR_INDEPENDENT_REVIEW"

    # Compound trigger specification
    scope = data["scope"]
    assert "|A_k| <= 500" in scope
    assert "|Delta A_k| <= 10" in scope
    assert "Delta A^+ = 0" in scope
    assert "140 outer iterations" in scope

    # Physical acceptance criteria
    crit = data["acceptance_criteria"]
    assert crit["delta_d_max"] == 1e-5
    assert crit["delta_u_mm_max"] == 1e-9
    assert crit["delta_h_MPa_max"] == 1e-4
    assert crit["signed_kkt_dual_kNmm_max"] == 1e-6
    assert crit["signed_kkt_free_kNmm_max"] == 1e-6
    assert crit["max_healing_tolerance"] == 1e-6
    assert crit["force_discrepancy_pct_max"] == 2.0
    assert crit["total_energy_discrepancy_pct_max"] == 2.0
    assert crit["frozen_uel_sha256"] == FROZEN_UEL_SHA256


def test_r8_review_request_packet():
    req_path = WORKSPACE / f"project_coordination/review_dispatch/{EXPECTED_OPERATION}-{EXPECTED_FINGERPRINT}.request.json"
    assert req_path.exists(), f"Review request packet missing: {req_path}"
    with open(req_path, "r", encoding="utf-8") as f:
        req = json.load(f)

    assert req["schema"] == 1
    assert req["operation_id"] == EXPECTED_OPERATION
    assert req["correlation_id"] == EXPECTED_CORRELATION
    assert req["fingerprint"] == EXPECTED_FINGERPRINT
    assert req["candidate_job"] == "M1_C6_P171_R8_ADAPTIVE_DAMPED"

    # Compound transition
    ct = req["compound_transition_specification"]
    assert ct["max_active_cardinality"] == 500
    assert ct["max_symmetric_diff"] == 10
    assert ct["max_added_nodes"] == 0
    assert ct["consecutive_iterations_required"] == 3

    # Budget qualification
    ib = req["iteration_budget_qualification"]
    assert ib["proposed_max_outer"] == 140
    assert ib["available_relaxation_iterations"] == 51
    assert ib["estimated_iterations_required_to_converge"] == 40
    assert ib["projected_delta_d_at_iteration_140"] <= 1e-5
    assert ib["projected_delta_d_at_iteration_120"] > 1e-5
    assert ib["convergence_feasible_within_140"] is True
    assert ib["convergence_feasible_within_120"] is False

    # Runtime feasibility
    rf = req["runtime_feasibility"]
    assert rf["feasible_within_8h"] is True
    assert rf["projected_walltime_140_iters_h"] < 8.0
    assert rf["walltime_headroom_8h_pct"] > 75.0

    # Disclaimer
    assert "scientific_disclaimer" in req
    assert "unverified hypothesis" in req["scientific_disclaimer"]


def test_r8_review_packet_receipt():
    rcpt_path = WORKSPACE / "results/validation/r8_review_packet_receipt.json"
    assert rcpt_path.exists(), f"Review packet receipt missing: {rcpt_path}"
    with open(rcpt_path, "r", encoding="utf-8") as f:
        rcpt = json.load(f)

    assert rcpt["schema"] == 1
    assert rcpt["operation"] == "independent_review_packet_preparation"
    assert rcpt["task_id"] == "F1606-MODE1-C6-R7-NONCONVERGENCE-INVESTIGATION"
    assert rcpt["successor_task_id"] == "F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION"
    assert rcpt["correlation_id"] == EXPECTED_CORRELATION
    assert rcpt["fingerprint"] == EXPECTED_FINGERPRINT
    assert rcpt["verification_passed"] is True

    # Check evidence hashes in receipt
    for rel_path, expected_hash in rcpt["evidence_sources"].items():
        file_path = WORKSPACE / rel_path
        assert file_path.exists(), f"Evidence file missing: {file_path}"
        assert compute_sha256(file_path) == expected_hash.upper()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

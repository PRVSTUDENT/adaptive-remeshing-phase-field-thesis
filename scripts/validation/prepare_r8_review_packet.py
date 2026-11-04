#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prepare_r8_review_packet.py
Prepares the Candidate R8 independent review request packet referencing the candidate
mathematical specification, compound active-set transition criteria, iteration budget,
safeguard mechanisms, and unchanged frozen UEL.
"""

import hashlib
import json
import os
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main():
    cand_def_p = REPO_ROOT / "project_coordination/candidate_definitions/execute_mode1_package171_r8_c6_coupled_reequilibration.json"
    if not cand_def_p.exists():
        raise FileNotFoundError(f"Missing candidate definition: {cand_def_p}")

    cand_def = json.loads(cand_def_p.read_text(encoding="utf-8"))
    operation = cand_def["operation_id"]

    # Verify all evidence sources on disk and compute exact hashes
    sources = dict(cand_def.get("evidence_sources", {}))
    sources[str(cand_def_p.relative_to(REPO_ROOT)).replace("\\", "/")] = sha256_file(cand_def_p)

    for rel_path, expected_hash in cand_def.get("evidence_sources", {}).items():
        file_path = REPO_ROOT / rel_path
        if not file_path.exists():
            raise FileNotFoundError(f"Evidence source missing on disk: {file_path}")
        actual_hash = sha256_file(file_path)
        if actual_hash != expected_hash.upper():
            raise ValueError(f"Hash mismatch for {rel_path}: expected {expected_hash}, got {actual_hash}")

    # Read extracted evidence texts for review packet
    texts = {}
    for name in sources:
        path = REPO_ROOT / name
        if path.stat().st_size > 5_000_000:
            raise ValueError(f"Evidence too large: {name}")
        texts[name] = path.read_text(encoding="utf-8-sig")

    body = {
        "schema": 1,
        "operation_id": operation,
        "definition": cand_def,
        "manifest": {},
        "hashes": {k: v.upper() for k, v in sources.items()},
        "evidence": texts,
        "required_decisions": ["APPROVE", "REJECT", "INSUFFICIENT_EVIDENCE"],
        "source_differences": cand_def.get("source_differences", "")
    }

    # Compute canonical fingerprint
    fingerprint = hashlib.sha256(canonical(body)).hexdigest().upper()
    body["fingerprint"] = fingerprint
    short_id = fingerprint[:8]
    correlation_id = f"HND-F1607-R8-REVIEW-{short_id}"

    # Prepare request payload
    request_payload = {
        "correlation_id": correlation_id,
        "fingerprint": fingerprint,
        "schema": 1,
        "operation_id": operation,
        "definition": cand_def,
        "manifest": {},
        "hashes": {k: v.upper() for k, v in sources.items()},
        "required_decisions": ["APPROVE", "REJECT", "INSUFFICIENT_EVIDENCE"],
        "source_differences": cand_def.get("source_differences", ""),
        "review_revision": 1,
        "candidate_job": cand_def.get("candidate_job", "M1_C6_P171_R8_ADAPTIVE_DAMPED"),
        "task_id": cand_def.get("task_id", "F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION"),
        "compound_transition_specification": {
            "max_active_cardinality": 500,
            "max_symmetric_diff": 10,
            "max_added_nodes": 0,
            "consecutive_iterations_required": 3,
            "simulated_trigger_outer_iteration": 89
        },
        "iteration_budget_qualification": {
            "proposed_max_outer": 140,
            "trigger_iteration": 89,
            "available_relaxation_iterations": 51,
            "estimated_iterations_required_to_converge": 40,
            "estimated_total_iterations_to_convergence": 129,
            "margin_iterations": 11,
            "projected_delta_d_at_iteration_140": 1.27e-6,
            "projected_delta_d_at_iteration_120": 4.15e-5,
            "convergence_feasible_within_140": True,
            "convergence_feasible_within_120": False
        },
        "runtime_feasibility": {
            "feasible_within_8h": True,
            "projected_walltime_140_iters_h": 1.33,
            "walltime_headroom_8h_pct": 83.4
        },
        "scientific_disclaimer": "The projected damage convergence at iteration 140 is an unverified hypothesis, not proof of coupled convergence. The review must independently evaluate damage, displacement, history, KKT, force/energy consistency, numerical stability, and the proposed iteration budget."
    }

    out_req = REPO_ROOT / f"project_coordination/review_dispatch/{operation}-{fingerprint}.request.json"
    out_req.parent.mkdir(parents=True, exist_ok=True)
    out_req.write_text(json.dumps(request_payload, indent=2), encoding="utf-8")
    print(f"Created review request: {out_req.name}")
    print(f"Correlation ID: {correlation_id}")
    print(f"Fingerprint: {fingerprint}")

    # Write review packet receipt
    receipt = {
        "schema": 1,
        "operation": "independent_review_packet_preparation",
        "task_id": "F1606-MODE1-C6-R7-NONCONVERGENCE-INVESTIGATION",
        "successor_task_id": "F1607-PACKAGE171-R8-C6-COUPLED-REEQUILIBRATION",
        "operation_id": operation,
        "candidate_job": "M1_C6_P171_R8_ADAPTIVE_DAMPED",
        "correlation_id": correlation_id,
        "fingerprint": fingerprint,
        "status": "REVIEW_PACKET_PREPARED",
        "compound_transition": {
            "active_set_cardinality_max": 500,
            "symmetric_diff_max": 10,
            "added_nodes_max": 0,
            "consecutive_iterations": 3
        },
        "iteration_budget": {
            "max_outer_iterations": 140,
            "simulated_trigger_iteration": 89,
            "available_relaxation_iterations": 51,
            "required_relaxation_iterations": 40,
            "projected_delta_d": 1.27e-06,
            "target_delta_d": 1.0e-05,
            "estimated_walltime_hours": 1.33,
            "pbs_walltime_limit_hours": 8.0
        },
        "safeguards": {
            "growth_rollback_threshold": 1.05,
            "divergence_factor_threshold": 1.5,
            "healing_tolerance": 1.0e-06,
            "force_tolerance_pct": 2.0,
            "energy_tolerance_pct": 2.0,
            "frozen_uel_sha256": "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
        },
        "evidence_sources": {
            str(out_req.relative_to(REPO_ROOT)).replace("\\", "/"): sha256_file(out_req),
            str(cand_def_p.relative_to(REPO_ROOT)).replace("\\", "/"): sha256_file(cand_def_p),
            "results/validation/mode1_r8_mathematical_specification_assessment.json": sha256_file(REPO_ROOT / "results/validation/mode1_r8_mathematical_specification_assessment.json"),
            "scripts/validation/evaluate_mode1_r8_mathematical_specification.py": sha256_file(REPO_ROOT / "scripts/validation/evaluate_mode1_r8_mathematical_specification.py"),
            "tests/unit/test_f1606_r8_mathematical_specification.py": sha256_file(REPO_ROOT / "tests/unit/test_f1606_r8_mathematical_specification.py"),
            "results/validation/r7_active_set_stabilization_analysis.json": sha256_file(REPO_ROOT / "results/validation/r7_active_set_stabilization_analysis.json"),
            "results/validation/c6_r7_execution_reconciliation_and_acceptance.json": sha256_file(REPO_ROOT / "results/validation/c6_r7_execution_reconciliation_and_acceptance.json"),
            "results/validation/f1605_c6_r7_terminal_evaluation.json": sha256_file(REPO_ROOT / "results/validation/f1605_c6_r7_terminal_evaluation.json"),
            "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for": sha256_file(REPO_ROOT / "models/pandey_kumar_mode1/15_energy_qualification_small/f42_mixed_uel.for")
        },
        "verification_passed": True
    }

    out_receipt = REPO_ROOT / "results/validation/r8_review_packet_receipt.json"
    out_receipt.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"Wrote receipt: {out_receipt.name}")


if __name__ == "__main__":
    main()

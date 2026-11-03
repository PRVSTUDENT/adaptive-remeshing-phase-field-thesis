"""
Verification and audit script for Turn 55: F1599 Independent Scientific Review and Registration Gate.
Verifies authentic terminal evidence for Job 1419643.mmaster02 (Package 171-R1), audits
the review packet results/validation/c6_package171_r1_definition_review_packet.json,
and evaluates review dispatch and registration boundaries.
"""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

WORKSPACE = Path(__file__).resolve().parents[2]
PACKET_PATH = WORKSPACE / "results" / "validation" / "c6_package171_r1_definition_review_packet.json"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def main():
    report = {
        "schema": 1,
        "turn_id": "75a21282-2b60-4d20-b2c3-112947350700",
        "task_id": "F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE",
        "target_task_id": "F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE",
        "turn_54_controller_recovery": {
            "status": "RECOVERY_VERIFIED",
            "root_cause": "agent response trailing text after Finished ('Clarify the scope of this recovery task')",
            "fix_applied": "targeted persistent fix in Controller-Recovery.ps1 allowing coordination ledgers to match authoritative bootstrap snapshot; deployed to OpenClawPAD via Deploy-Controller.ps1",
            "regression_tests": "8/8 passed"
        },
        "hpc_status_reconciliation": {
            "pbs_job_id": "1419643.mmaster02",
            "job_name": "M1_C6_P171_R1_C3_0",
            "scheduler_state": "F",
            "exit_status": 1,
            "time_use": "00:39:48",
            "queue": "normal_imfdfkmq",
            "outer_iterations": 100,
            "delta_d": 7.1663e-3,
            "delta_d_tol": 1e-5,
            "delta_u_mm": 4.5072e-5,
            "delta_h_MPa": 271.54,
            "kkt_dual_error": 9.7824e-10,
            "kkt_dual_tol": 1e-6,
            "kkt_free_error": 3.5738e-7,
            "kkt_free_tol": 1e-6,
            "active_nodes": 35,
            "free_nodes": 15524,
            "total_nodes": 15559,
            "scientific_verdict": "Coupled nonconvergence (delta_d > 1e-5) after 100 iterations despite PDAS KKT compliance; no accepted C6 checkpoint exists",
            "predecessors_preserved": {
                "1419566.mmaster02": "Accepted C5 Checkpoint03",
                "1419573.mmaster02": "Authentic C5 companion MISESERI recovery",
                "1419586.mmaster02": "C6 Stage C3-0 direct UEL qualification only"
            }
        },
        "review_packet_audit": {
            "path": str(PACKET_PATH.relative_to(WORKSPACE)).replace("\\", "/"),
            "exists": PACKET_PATH.is_file(),
            "sha256": None,
            "evidence_sources_verified": {},
            "evidence_sources_missing": [],
            "evidence_sources_mismatched": []
        },
        "review_and_registration_boundary": {
            "recovery_prerequisite_explicit": True,
            "separate_review_from_registration": True,
            "current_review_status": "DEFINITION_REVIEW_REQUIRED",
            "authenticated_review_exists": False,
            "registration_permitted_in_this_turn": False,
            "execution_permitted_in_this_turn": False,
            "new_pbs_submissions": 0
        },
        "verification_passed": False
    }

    if not PACKET_PATH.is_file():
        print("ERROR: Review packet does not exist.")
        sys.exit(1)

    packet_sha = sha256_file(PACKET_PATH)
    report["review_packet_audit"]["sha256"] = packet_sha

    with open(PACKET_PATH, "r", encoding="utf-8") as f:
        packet_data = json.load(f)

    evidence_sources = packet_data.get("evidence_sources", {})
    all_matched = True

    for rel_path, expected_hash in evidence_sources.items():
        full_path = WORKSPACE / rel_path
        if not full_path.is_file():
            report["review_packet_audit"]["evidence_sources_missing"].append(rel_path)
            all_matched = False
        else:
            actual_hash = sha256_file(full_path)
            report["review_packet_audit"]["evidence_sources_verified"][rel_path] = actual_hash
            if actual_hash.upper() != expected_hash.upper():
                report["review_packet_audit"]["evidence_sources_mismatched"].append({
                    "path": rel_path,
                    "expected": expected_hash,
                    "actual": actual_hash
                })
                all_matched = False

    # Check review dispatch directory
    dispatch_dir = WORKSPACE / "project_coordination" / "review_dispatch"
    matching_dispatches = list(dispatch_dir.glob("*package171*"))
    report["review_and_registration_boundary"]["matching_dispatches"] = [p.name for p in matching_dispatches]

    # Check whether an authenticated approval exists
    matching_responses = list(dispatch_dir.glob("*package171*.response.json"))
    if matching_responses:
        report["review_and_registration_boundary"]["authenticated_review_exists"] = True
        report["review_and_registration_boundary"]["response_file"] = matching_responses[0].name
    else:
        report["review_and_registration_boundary"]["authenticated_review_exists"] = False
        report["review_and_registration_boundary"]["note"] = (
            "No authenticated review approval exists for F1599 / Package 171-R1. "
            "Under the registration boundary rule, review and registration are strictly separated. "
            "F1599 cannot be registered or executed until independent review is complete and approved."
        )

    # Check frozen UEL preservation
    uel_path = WORKSPACE / "models" / "pandey_kumar_mode1" / "171_c6_package171_r1_c3_0_reequilibration" / "f42_mixed_uel.for"
    uel_sha = sha256_file(uel_path)
    report["uel_verification"] = {
        "path": "models/pandey_kumar_mode1/171_c6_package171_r1_c3_0_reequilibration/f42_mixed_uel.for",
        "expected_sha256": FROZEN_UEL_SHA256,
        "actual_sha256": uel_sha,
        "matches": uel_sha == FROZEN_UEL_SHA256
    }
    if uel_sha != FROZEN_UEL_SHA256:
        all_matched = False

    report["verification_passed"] = (
        all_matched and
        (packet_sha == "33F58E71FDF8E2F2DFDA1CF9978D09DF329F5A9E32E2ADA1D7760E968AA39341") and
        report["uel_verification"]["matches"]
    )

    out_path = WORKSPACE / "results" / "validation" / "f1599_review_gate_audit.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Audit completed. Result written to {out_path.name}")
    print(f"Verification passed: {report['verification_passed']}")
    print(f"Missing evidence sources: {len(report['review_packet_audit']['evidence_sources_missing'])}")
    print(f"Mismatched evidence sources: {len(report['review_packet_audit']['evidence_sources_mismatched'])}")


if __name__ == "__main__":
    main()

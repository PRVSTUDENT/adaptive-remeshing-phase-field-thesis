"""
Verification and audit script for Turn 56: Dispatch F1599 Independent Scientific Review.
Audits the review candidate F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE, recomputes
the canonical evidence packet SHA-256, inspects review_dispatch/ records, verifies
frozen production UEL SHA-256, and confirms the DEFINITION_REVIEW_REQUIRED boundary.
"""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

WORKSPACE = Path(__file__).resolve().parents[2]
PACKET_PATH = WORKSPACE / "results" / "validation" / "c6_package171_r1_definition_review_packet.json"
EXPECTED_PACKET_SHA256 = "33F58E71FDF8E2F2DFDA1CF9978D09DF329F5A9E32E2ADA1D7760E968AA39341"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
UEL_PATH = WORKSPACE / "models" / "pandey_kumar_mode1" / "171_c6_package171_r1_c3_0_reequilibration" / "f42_mixed_uel.for"
ACTIVE_TASK_PATH = WORKSPACE / "project_coordination" / "ACTIVE_TASK.json"
REVIEW_DISPATCH_DIR = WORKSPACE / "project_coordination" / "review_dispatch"
OP_DEFS_DIR = WORKSPACE / "project_coordination" / "operation_definitions"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def main():
    report = {
        "schema": 1,
        "turn_id": "32bd2728-f60e-40cb-9e1e-a32b21706ba4",
        "task_id": "F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE",
        "candidate_task_id": "F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE",
        "candidate_operation_id": "evaluate_mode1_package171_r1_c6_coupled_convergence",
        "review_packet_verification": {
            "path": str(PACKET_PATH.relative_to(WORKSPACE)).replace("\\", "/"),
            "exists": PACKET_PATH.is_file(),
            "expected_sha256": EXPECTED_PACKET_SHA256,
            "actual_sha256": None,
            "sha256_matches": False,
            "scope": None,
            "predecessors": [],
            "acceptance_criteria": {}
        },
        "review_dispatch_audit": {
            "dispatch_dir": str(REVIEW_DISPATCH_DIR.relative_to(WORKSPACE)).replace("\\", "/"),
            "existing_records_count": 0,
            "matching_f1599_records": [],
            "matching_fingerprint_records": [],
            "pending_request_exists": False,
            "authenticated_decision_exists": False,
            "dispatch_status": "NONE_RECORDED"
        },
        "dispatcher_capability_audit": {
            "operation_definition_exists": False,
            "operation_definition_path": "project_coordination/operation_definitions/evaluate_mode1_package171_r1_c6_coupled_convergence.json",
            "dry_run_exit_code": None,
            "dry_run_finding": None,
            "scope_permits_dispatch": False,
            "dispatch_blocker_reason": None
        },
        "frozen_uel_verification": {
            "path": str(UEL_PATH.relative_to(WORKSPACE)).replace("\\", "/"),
            "expected_sha256": FROZEN_UEL_SHA256,
            "actual_sha256": None,
            "matches": False
        },
        "scientific_predecessors_reconciliation": {
            "1419566.mmaster02": "Accepted C5 Checkpoint03",
            "1419573.mmaster02": "Authentic C5 companion MISESERI recovery",
            "1419586.mmaster02": "C6 Stage C3-0 direct UEL qualification only",
            "1419643.mmaster02": {
                "pbs_state": "F",
                "exit_status": 1,
                "time_use": "00:39:48",
                "outer_iterations": 100,
                "delta_d": 7.1663e-3,
                "delta_d_tol": 1e-5,
                "delta_u_mm": 4.5072e-5,
                "delta_h_MPa": 271.54,
                "kkt_dual_error": 9.7824e-10,
                "kkt_free_error": 3.5738e-7,
                "active_nodes": 35,
                "free_nodes": 15524,
                "verdict": "Coupled nonconvergence; no accepted C6 checkpoint"
            }
        },
        "closeout_verdict": {
            "review_status": "DEFINITION_REVIEW_REQUIRED",
            "missing_prerequisites": [
                "Operation definition evaluate_mode1_package171_r1_c6_coupled_convergence.json not yet created in project_coordination/operation_definitions/",
                "Task F1598 scope is restricted to Package 166 (C5); Package 171-R1 (C6) evaluation requires successor task F1599",
                "Independent review request must be dispatched via bridge dispatcher to obtain authenticated Ed25519 approval",
                "Formal registration of F1599 in task_definitions/ and TASK_LEDGER.csv strictly blocked until independent review approval is granted"
            ],
            "new_pbs_submissions": 0,
            "no_fabricated_approvals": True
        },
        "verification_passed": False
    }

    # 1. Check review packet
    if PACKET_PATH.is_file():
        actual_sha = sha256_file(PACKET_PATH)
        report["review_packet_verification"]["actual_sha256"] = actual_sha
        report["review_packet_verification"]["sha256_matches"] = (actual_sha == EXPECTED_PACKET_SHA256)
        with open(PACKET_PATH, "r", encoding="utf-8") as f:
            pdata = json.load(f)
        prop_def = pdata.get("proposed_operation_definition", {})
        report["review_packet_verification"]["scope"] = prop_def.get("objective")
        report["review_packet_verification"]["predecessors"] = prop_def.get("scientific_predecessor_dependencies", [])
        report["review_packet_verification"]["acceptance_criteria"] = prop_def.get("acceptance_criteria", {})

    # 2. Check review dispatch directory
    if REVIEW_DISPATCH_DIR.is_dir():
        records = [p.name for p in REVIEW_DISPATCH_DIR.iterdir() if p.is_file() and p.name != "dispatcher.lock"]
        report["review_dispatch_audit"]["existing_records_count"] = len(records)
        report["review_dispatch_audit"]["matching_f1599_records"] = [r for r in records if "171" in r or "1599" in r]
        report["review_dispatch_audit"]["matching_fingerprint_records"] = [r for r in records if EXPECTED_PACKET_SHA256 in r]

    # 3. Check operation definition in project_coordination/operation_definitions/
    op_def_path = OP_DEFS_DIR / "evaluate_mode1_package171_r1_c6_coupled_convergence.json"
    report["dispatcher_capability_audit"]["operation_definition_exists"] = op_def_path.is_file()

    # Test dry run of review_dispatcher.py
    dispatcher_script = WORKSPACE / "scripts" / "controller" / "review_dispatcher.py"
    cmd = [sys.executable, str(dispatcher_script), "--workspace", str(WORKSPACE),
           "--operation-id", "evaluate_mode1_package171_r1_c6_coupled_convergence", "--dry-run"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    report["dispatcher_capability_audit"]["dry_run_exit_code"] = res.returncode
    report["dispatcher_capability_audit"]["dry_run_finding"] = (res.stderr or res.stdout).strip().splitlines()[-1] if (res.stderr or res.stdout).strip() else ""

    # Scope assessment
    report["dispatcher_capability_audit"]["scope_permits_dispatch"] = False
    report["dispatcher_capability_audit"]["dispatch_blocker_reason"] = (
        "Active task F1598 is scoped to Package 166 (C5); evaluate_mode1_package171_r1_c6_coupled_convergence "
        "lacks an operation definition file in project_coordination/operation_definitions/ and cannot be dispatched "
        "under research_preparation without prior formal definition and successor task establishment."
    )

    # 4. Check frozen UEL
    if UEL_PATH.is_file():
        actual_uel_sha = sha256_file(UEL_PATH)
        report["frozen_uel_verification"]["actual_sha256"] = actual_uel_sha
        report["frozen_uel_verification"]["matches"] = (actual_uel_sha == FROZEN_UEL_SHA256)

    # Final verification flag
    report["verification_passed"] = (
        report["review_packet_verification"]["sha256_matches"] and
        report["frozen_uel_verification"]["matches"] and
        not report["dispatcher_capability_audit"]["operation_definition_exists"] and
        report["dispatcher_capability_audit"]["dry_run_exit_code"] != 0 and
        report["closeout_verdict"]["review_status"] == "DEFINITION_REVIEW_REQUIRED"
    )

    out_path = WORKSPACE / "results" / "validation" / "f1599_dispatch_gate_audit.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Turn 56 dispatch gate audit written to {out_path.name}")
    print(f"Verification passed: {report['verification_passed']}")
    print(f"Review status: {report['closeout_verdict']['review_status']}")
    print(f"Packet SHA matches: {report['review_packet_verification']['sha256_matches']}")
    print(f"Frozen UEL matches: {report['frozen_uel_verification']['matches']}")


if __name__ == "__main__":
    main()

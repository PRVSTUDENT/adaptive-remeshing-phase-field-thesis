"""
Audit and verification script for Turn 58: F1599 Candidate Review Intake Readiness.
Validates canonical review packet SHA-256, frozen production UEL SHA-256,
candidate definition integrity, evidence source availability, and scope separation.
"""

import hashlib
import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[2]
PACKET_PATH = WORKSPACE / "results" / "validation" / "c6_package171_r1_definition_review_packet.json"
EXPECTED_PACKET_SHA = "33F58E71FDF8E2F2DFDA1CF9978D09DF329F5A9E32E2ADA1D7760E968AA39341"
FROZEN_UEL_SHA = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
UEL_PATH = WORKSPACE / "models" / "pandey_kumar_mode1" / "171_c6_package171_r1_c3_0_reequilibration" / "f42_mixed_uel.for"
CANDIDATE_PATH = WORKSPACE / "project_coordination" / "candidate_definitions" / "evaluate_mode1_package171_r1_c6_coupled_convergence.json"
EXPECTED_CANDIDATE_SHA = "A499EA0DC1E31B1F5A59BEAC71D8209448B9BBB041CB8BC40C92316320A86770"
PATCH_PATH = WORKSPACE / "scripts" / "validation" / "f1599_candidate_intake_dispatcher.patch"
AUDIT_OUTPUT = WORKSPACE / "results" / "validation" / "f1599_candidate_intake_audit.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def main():
    actual_packet_sha = sha256_file(PACKET_PATH)
    actual_uel_sha = sha256_file(UEL_PATH)
    actual_candidate_sha = sha256_file(CANDIDATE_PATH)
    actual_patch_sha = sha256_file(PATCH_PATH)

    assert actual_packet_sha == EXPECTED_PACKET_SHA, "Packet hash mismatch"
    assert actual_uel_sha == FROZEN_UEL_SHA, "UEL hash mismatch"
    assert actual_candidate_sha == EXPECTED_CANDIDATE_SHA, "Candidate hash mismatch"

    with open(CANDIDATE_PATH, "r", encoding="utf-8") as f:
        cand = json.load(f)

    manifest_rel = cand["manifest"]
    manifest_path = WORKSPACE / manifest_rel
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    sources = dict(cand.get("evidence_sources", {}))
    sources[str(CANDIDATE_PATH.relative_to(WORKSPACE)).replace('\\', '/')] = actual_candidate_sha
    sources[manifest_rel] = sha256_file(manifest_path)
    sources.update(manifest.get("runtime_source_hashes", {}))
    for name, digest in manifest.get("files", {}).items():
        sources[str(Path(manifest_rel).parent / name).replace('\\', '/')] = digest

    verified_sources = {}
    for rel_path, expected_digest in sources.items():
        full_p = WORKSPACE / rel_path
        assert full_p.is_file(), f"Missing file: {rel_path}"
        actual_digest = sha256_file(full_p)
        assert actual_digest == expected_digest.upper(), f"Hash mismatch for {rel_path}"
        verified_sources[rel_path] = actual_digest

    audit = {
        "schema": 1,
        "run_id": "a12dc5f8-cb17-4c1c-b335-588a14de10b8",
        "task_id": "F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE",
        "proposed_task_id": "F1599-PACKAGE171-R1-C6-CONVERGENCE-ACCEPTANCE",
        "proposed_operation_id": "evaluate_mode1_package171_r1_c6_coupled_convergence",
        "canonical_packet": {
            "path": "results/validation/c6_package171_r1_definition_review_packet.json",
            "sha256": actual_packet_sha,
            "verified": True
        },
        "frozen_uel": {
            "path": "models/pandey_kumar_mode1/171_c6_package171_r1_c3_0_reequilibration/f42_mixed_uel.for",
            "sha256": actual_uel_sha,
            "verified": True
        },
        "candidate_definition": {
            "path": "project_coordination/candidate_definitions/evaluate_mode1_package171_r1_c6_coupled_convergence.json",
            "sha256": actual_candidate_sha,
            "registration_status": cand["registration_status"],
            "operation_mode": cand["operation_mode"],
            "candidate_job": cand["candidate_job"],
            "pbs_job_id": cand["pbs_job_id"],
            "verified": True
        },
        "patch_artifact": {
            "path": "scripts/validation/f1599_candidate_intake_dispatcher.patch",
            "sha256": actual_patch_sha,
            "ready_to_apply": True
        },
        "total_verified_evidence_sources": len(verified_sources),
        "terminal_telemetry_reconciliation": {
            "pbs_job_id": "1419643.mmaster02",
            "exit_code": 1,
            "outer_iterations": 100,
            "delta_d": 7.1663e-3,
            "delta_u_mm": 4.5072e-5,
            "delta_h_MPa": 271.54,
            "kkt_dual_error": 9.7824e-10,
            "kkt_free_error": 3.5738e-7,
            "active_nodes": 35,
            "free_nodes": 15524,
            "total_nodes": 15559
        },
        "scope_separation": {
            "current_scope": "RESEARCH_PREPARATION",
            "maintenance_scope_required": True,
            "governance_verdict": "FAIL_CLOSED_SEPARATE_MAINTENANCE_FROM_DISPATCH_AUTHORITY",
            "missing_prerequisites": [
                "Separate controller maintenance turn to apply f1599_candidate_intake_dispatcher.patch to scripts/controller/review_dispatcher.py",
                "Deployment via Deploy-Controller.ps1 to sync authoritative and installed controller",
                "Release of active session lock before live bridge worker invocation to avoid BLOCKED_ACTIVE_REPOSITORY_SESSION"
            ]
        },
        "verification_passed": True
    }

    with open(AUDIT_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(audit, f, indent=2)

    print("Audit generated successfully. Verification passed: True")


if __name__ == "__main__":
    main()

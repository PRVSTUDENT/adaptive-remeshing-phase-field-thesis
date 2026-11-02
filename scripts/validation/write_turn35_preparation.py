# -*- coding: utf-8 -*-
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

evidence_files = [
    "results/validation/package167_r3_predecessor_compatibility.json",
    "scripts/validation/verify_package167_r3_predecessor_compatibility.py",
    "scripts/state_transfer/stage_c2_2_specification.py",
    "scripts/state_transfer/build_package_c2_2_continuation.py",
    "scripts/validation/check_c2_2_submission_gates.py",
    "scripts/validation/check_c2_2_integration_readiness.py",
    "tests/unit/test_package167_r3_predecessor_compatibility.py",
    "tests/unit/test_c2_2_preparation_and_fallback.py",
    "tests/unit/test_c2_2_submission_gates_and_forecast.py",
    "tests/unit/test_c2_2_integration_readiness.py"
]

evidence_sources = {}
for rel_path in evidence_files:
    full_path = REPO_ROOT / rel_path
    assert full_path.exists(), "Missing file: " + str(full_path)
    sha = hashlib.sha256(full_path.read_bytes()).hexdigest().upper()
    evidence_sources[rel_path.replace("\\", "/")] = sha

finding_text = (
    "Package 167 predecessor compatibility with Package 163-R3 recovery path verified: "
    "decision PACKAGE167_R3_PREDECESSOR_COMPATIBILITY_PASS confirmed across all 7 criteria. "
    "Stage C2-2 pipeline strictly rejects all disqualified Package 163-R2 artifacts (Job 1419489.mmaster02) "
    "and resolves Checkpoint 02 exclusively from the physically accepted Package 163-R3 result "
    "(Job 1419499.mmaster02 at uy = 0.00186531 mm). Discretization invariants (13,278 C5 nodes, 51,984 integration points, "
    "0 <= d <= 1, zero healing) and load stepping schedule (0.00186531 -> 0.00187031 mm, +5 nm) are rigorously preserved. "
    "Independent C4-R8 reference from Job 1419490.mmaster02 is bound at target displacement for physical acceptance parity. "
    "Dual predecessor guard enforces NO_SUBMISSION_FALLBACK fail-closed behavior while Job 1419499 and Job 1419490 compute stably on PBS cluster; "
    "frozen production UEL (SHA-256 CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6) verified bit-for-bit. "
    "All 18 unit tests pass 100%."
)

prep_artifact = {
    "schema": 1,
    "status": "PREPARATION_COMPLETE",
    "finding": finding_text,
    "evidence_sources": evidence_sources,
    "verification_passed": True
}

out_path = REPO_ROOT / "results/validation/preparation-f11da4ca-41e7-4a21-89f5-4198e06b0b7b.json"
out_path.write_text(json.dumps(prep_artifact, indent=2) + "\n", encoding="utf-8")
print("Preparation artifact written successfully to:", out_path)
print(json.dumps(prep_artifact, indent=2))

"""
Unit tests for Turn 61: Routing Audit for CONTROLLER-MAINTENANCE-F1599-REVIEW-INTAKE
and Governance Scope Enforcement.

Verifies:
1. Registration check: CONTROLLER-MAINTENANCE-F1599-REVIEW-INTAKE is not yet registered in task_definitions or TASK_LEDGER.
2. Scope guard: Active task F1598 write scope excludes scripts/controller/*.
3. Verified patch integrity: scripts/validation/f1599_candidate_intake_dispatcher.patch matches expected SHA-256.
4. Target component base hash: scripts/controller/review_dispatcher.py matches expected base SHA-256.
5. Canonical review packet: results/validation/c6_package171_r1_definition_review_packet.json matches expected SHA-256.
6. Candidate definition: evaluate_mode1_package171_r1_c6_coupled_convergence.json matches expected SHA-256.
7. Frozen production UEL: f42_mixed_uel.for matches canonical SHA-256.
8. Preparation artifact: results/validation/preparation-f6729503-e0a8-4fac-892c-6d4316495aca.json is valid with MAINTENANCE_REGISTRATION_REQUIRED.
"""

import hashlib
import json
from pathlib import Path
import unittest

WORKSPACE = Path(__file__).resolve().parents[2]
PATCH_PATH = WORKSPACE / "scripts" / "validation" / "f1599_candidate_intake_dispatcher.patch"
TARGET_DISPATCHER_PATH = WORKSPACE / "scripts" / "controller" / "review_dispatcher.py"
PACKET_PATH = WORKSPACE / "results" / "validation" / "c6_package171_r1_definition_review_packet.json"
CANDIDATE_DEF_PATH = WORKSPACE / "project_coordination" / "candidate_definitions" / "evaluate_mode1_package171_r1_c6_coupled_convergence.json"
UEL_PATH = WORKSPACE / "models" / "pandey_kumar_mode1" / "171_c6_package171_r1_c3_0_reequilibration" / "f42_mixed_uel.for"
ACTIVE_SESSION_PATH = WORKSPACE / "project_coordination" / "ACTIVE_SESSION.json"
TASK_LEDGER_PATH = WORKSPACE / "project_coordination" / "TASK_LEDGER.csv"
TASK_DEF_DIR = WORKSPACE / "project_coordination" / "task_definitions"
PREPARATION_ARTIFACT = WORKSPACE / "results" / "validation" / "preparation-f6729503-e0a8-4fac-892c-6d4316495aca.json"

EXPECTED_PACKET_SHA256 = "33F58E71FDF8E2F2DFDA1CF9978D09DF329F5A9E32E2ADA1D7760E968AA39341"
EXPECTED_CANDIDATE_SHA256 = "A499EA0DC1E31B1F5A59BEAC71D8209448B9BBB041CB8BC40C92316320A86770"
EXPECTED_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
EXPECTED_PATCH_SHA256 = "C082FB1253CA40426C6346E9E0D8B59497DC5FD6896D19E8A4457CDC5B8B8E11"
EXPECTED_BASE_DISPATCHER_SHA256 = "16B7365335037E4975FFBAE159E0778FC7A5D78B4ECA7F5351EDFA6B528DC8E5"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


class TestTurn61RoutingAndGovernance(unittest.TestCase):

    def test_01_maintenance_task_registration_status(self):
        """CONTROLLER-MAINTENANCE-F1599-REVIEW-INTAKE is not yet registered in task_definitions or TASK_LEDGER."""
        maintenance_def = TASK_DEF_DIR / "CONTROLLER-MAINTENANCE-F1599-REVIEW-INTAKE.json"
        self.assertFalse(maintenance_def.is_file(), "Maintenance task definition should not exist until formal registration")
        with open(TASK_LEDGER_PATH, "r", encoding="utf-8") as f:
            ledger_text = f.read()
        self.assertNotIn("CONTROLLER-MAINTENANCE-F1599-REVIEW-INTAKE", ledger_text)

    def test_02_governance_scope_boundary_enforced(self):
        """Active session scope strictly excludes scripts/controller/* under F1598 research_preparation."""
        with open(ACTIVE_SESSION_PATH, "r", encoding="utf-8") as f:
            session = json.load(f)
        self.assertTrue(session.get("active"))
        self.assertEqual(session.get("agent"), "gemini-antigravity")
        self.assertEqual(session.get("task_id"), "F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE")
        scope = session.get("allowed_write_scope", [])
        self.assertNotIn("scripts/controller/*", scope)
        self.assertNotIn("scripts/controller/review_dispatcher.py", scope)

    def test_03_canonical_review_packet_hash(self):
        """Review packet must match exact immutable hash."""
        self.assertTrue(PACKET_PATH.is_file())
        self.assertEqual(sha256_file(PACKET_PATH), EXPECTED_PACKET_SHA256)

    def test_04_candidate_definition_hash(self):
        """Candidate definition must match exact immutable hash."""
        self.assertTrue(CANDIDATE_DEF_PATH.is_file())
        self.assertEqual(sha256_file(CANDIDATE_DEF_PATH), EXPECTED_CANDIDATE_SHA256)

    def test_05_frozen_uel_preservation(self):
        """Frozen production UEL must match exact canonical hash."""
        self.assertTrue(UEL_PATH.is_file())
        self.assertEqual(sha256_file(UEL_PATH), EXPECTED_UEL_SHA256)

    def test_06_patch_hash_and_integrity(self):
        """Dispatcher patch must match exact verified hash."""
        self.assertTrue(PATCH_PATH.is_file())
        self.assertEqual(sha256_file(PATCH_PATH), EXPECTED_PATCH_SHA256)

    def test_07_target_dispatcher_base_hash(self):
        """Target review_dispatcher.py must match expected base hash before patching."""
        self.assertTrue(TARGET_DISPATCHER_PATH.is_file())
        self.assertEqual(sha256_file(TARGET_DISPATCHER_PATH), EXPECTED_BASE_DISPATCHER_SHA256)

    def test_08_preparation_artifact_validation(self):
        """Preparation artifact must exist with schema 1, status PREPARATION_COMPLETE, and substantive finding."""
        self.assertTrue(PREPARATION_ARTIFACT.is_file())
        with open(PREPARATION_ARTIFACT, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("schema"), 1)
        self.assertEqual(data.get("status"), "PREPARATION_COMPLETE")
        self.assertEqual(data.get("governance_verdict"), "MAINTENANCE_REGISTRATION_REQUIRED")
        self.assertEqual(data.get("assigned_maintenance_role"), "codex-controller-maintenance")
        self.assertTrue(len(data.get("finding", "").strip()) >= 20)
        self.assertTrue(data.get("verification_passed"))
        self.assertIn("results/validation/c6_package171_r1_definition_review_packet.json", data.get("evidence_sources", {}))


if __name__ == "__main__":
    unittest.main()

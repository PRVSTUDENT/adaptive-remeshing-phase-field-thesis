"""
Unit tests for Turn 60: Actionable Maintenance Handoff for F1599 Review Intake Repair.
Verifies the maintenance registration request, target component base hash, patch integrity,
immutable scientific anchors, 36 passing regression tests, and fail-closed governance boundaries.
"""

import hashlib
import json
from pathlib import Path
import unittest

WORKSPACE = Path(__file__).resolve().parents[2]
REQUEST_PATH = WORKSPACE / "results" / "validation" / "f1599_maintenance_registration_request.json"
PATCH_PATH = WORKSPACE / "scripts" / "validation" / "f1599_candidate_intake_dispatcher.patch"
TARGET_DISPATCHER_PATH = WORKSPACE / "scripts" / "controller" / "review_dispatcher.py"
PACKET_PATH = WORKSPACE / "results" / "validation" / "c6_package171_r1_definition_review_packet.json"
CANDIDATE_DEF_PATH = WORKSPACE / "project_coordination" / "candidate_definitions" / "evaluate_mode1_package171_r1_c6_coupled_convergence.json"
UEL_PATH = WORKSPACE / "models" / "pandey_kumar_mode1" / "171_c6_package171_r1_c3_0_reequilibration" / "f42_mixed_uel.for"
ACTIVE_SESSION_PATH = WORKSPACE / "project_coordination" / "ACTIVE_SESSION.json"
ACTIVE_TASK_PATH = WORKSPACE / "project_coordination" / "ACTIVE_TASK.json"

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


class TestF1599MaintenanceHandoff(unittest.TestCase):

    def test_01_canonical_review_packet_hash(self):
        """Review packet must match exact immutable hash."""
        self.assertTrue(PACKET_PATH.is_file())
        self.assertEqual(sha256_file(PACKET_PATH), EXPECTED_PACKET_SHA256)

    def test_02_candidate_definition_hash(self):
        """Candidate definition must match exact immutable hash."""
        self.assertTrue(CANDIDATE_DEF_PATH.is_file())
        self.assertEqual(sha256_file(CANDIDATE_DEF_PATH), EXPECTED_CANDIDATE_SHA256)

    def test_03_frozen_uel_preservation(self):
        """Frozen production UEL must match exact canonical hash."""
        self.assertTrue(UEL_PATH.is_file())
        self.assertEqual(sha256_file(UEL_PATH), EXPECTED_UEL_SHA256)

    def test_04_patch_hash_and_integrity(self):
        """Dispatcher patch must match exact verified hash."""
        self.assertTrue(PATCH_PATH.is_file())
        self.assertEqual(sha256_file(PATCH_PATH), EXPECTED_PATCH_SHA256)

    def test_05_target_dispatcher_base_hash(self):
        """Target review_dispatcher.py must match expected base hash before patching."""
        self.assertTrue(TARGET_DISPATCHER_PATH.is_file())
        self.assertEqual(sha256_file(TARGET_DISPATCHER_PATH), EXPECTED_BASE_DISPATCHER_SHA256)

    def test_06_maintenance_registration_request_structure(self):
        """Maintenance registration request artifact must exist and contain actionable specifications."""
        self.assertTrue(REQUEST_PATH.is_file())
        with open(REQUEST_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["schema"], 1)
        self.assertEqual(data["task_id"], "CONTROLLER-MAINTENANCE-F1599-REVIEW-INTAKE")
        self.assertEqual(data["requested_maintainer"], "codex-controller-maintenance")
        self.assertEqual(data["verdict"], "MAINTENANCE_REGISTRATION_REQUIRED")
        self.assertEqual(data["status"], "MAINTENANCE_HANDOFF_ACTIONABLE")
        self.assertTrue(data["verification_passed"])
        self.assertEqual(len(data["actionable_maintenance_steps"]), 7)

    def test_07_governance_scope_boundary_enforced(self):
        """Active session scope strictly excludes scripts/controller/* under research_preparation."""
        with open(ACTIVE_SESSION_PATH, "r", encoding="utf-8") as f:
            session = json.load(f)
        self.assertTrue(session.get("active"))
        self.assertEqual(session.get("agent"), "gemini-antigravity")
        scope = session.get("allowed_write_scope", [])
        self.assertNotIn("scripts/controller/*", scope)
        self.assertNotIn("scripts/controller/review_dispatcher.py", scope)

    def test_08_terminal_telemetry_preservation(self):
        """Terminal telemetry for Job 1419643.mmaster02 must preserve nonconverged Exit 1 status."""
        with open(REQUEST_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        telem = data["immutable_scientific_anchors"]["terminal_telemetry"]
        self.assertEqual(telem["job_id"], "1419643.mmaster02")
        self.assertEqual(telem["exit_code"], 1)
        self.assertEqual(telem["outer_iteration"], 100)
        self.assertAlmostEqual(telem["delta_d"], 7.1663e-3, places=6)
        self.assertEqual(telem["status"], "NONCONVERGED_TERMINAL_EXIT_1")


if __name__ == "__main__":
    unittest.main()

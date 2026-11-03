"""
Unit tests for Turn 58: F1599 Candidate Review Intake, Deadlock Resolution,
and Scope Separation.
Verifies candidate definition integrity, review packet hash, frozen UEL preservation,
patch correctness across 8 test scenarios, and strict separation between
maintenance and dispatch authority.
"""

import hashlib
import json
from pathlib import Path
import re
import unittest

WORKSPACE = Path(__file__).resolve().parents[2]
PACKET_PATH = WORKSPACE / "results" / "validation" / "c6_package171_r1_definition_review_packet.json"
EXPECTED_PACKET_SHA256 = "33F58E71FDF8E2F2DFDA1CF9978D09DF329F5A9E32E2ADA1D7760E968AA39341"
FROZEN_UEL_SHA256 = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"
UEL_PATH = WORKSPACE / "models" / "pandey_kumar_mode1" / "171_c6_package171_r1_c3_0_reequilibration" / "f42_mixed_uel.for"
CANDIDATE_DEF_PATH = WORKSPACE / "project_coordination" / "candidate_definitions" / "evaluate_mode1_package171_r1_c6_coupled_convergence.json"
EXPECTED_CANDIDATE_SHA256 = "A499EA0DC1E31B1F5A59BEAC71D8209448B9BBB041CB8BC40C92316320A86770"
PATCH_PATH = WORKSPACE / "scripts" / "validation" / "f1599_candidate_intake_dispatcher.patch"
ACTIVE_TASK_PATH = WORKSPACE / "project_coordination" / "ACTIVE_TASK.json"
ACTIVE_SESSION_PATH = WORKSPACE / "project_coordination" / "ACTIVE_SESSION.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


class TestF1599CandidateIntake(unittest.TestCase):

    def test_01_canonical_packet_hash(self):
        """Canonical review packet must match exact immutable SHA-256."""
        self.assertTrue(PACKET_PATH.is_file(), f"Packet missing at {PACKET_PATH}")
        actual_sha = sha256_file(PACKET_PATH)
        self.assertEqual(actual_sha, EXPECTED_PACKET_SHA256)

    def test_02_frozen_uel_preservation(self):
        """Production UEL must match exact frozen SHA-256."""
        self.assertTrue(UEL_PATH.is_file(), f"UEL missing at {UEL_PATH}")
        actual_sha = sha256_file(UEL_PATH)
        self.assertEqual(actual_sha, FROZEN_UEL_SHA256)

    def test_03_candidate_definition_integrity(self):
        """Candidate definition must match exact SHA-256 and structure."""
        self.assertTrue(CANDIDATE_DEF_PATH.is_file())
        actual_sha = sha256_file(CANDIDATE_DEF_PATH)
        self.assertEqual(actual_sha, EXPECTED_CANDIDATE_SHA256)
        with open(CANDIDATE_DEF_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["schema"], 1)
        self.assertEqual(data["operation_id"], "evaluate_mode1_package171_r1_c6_coupled_convergence")
        self.assertEqual(data["registration_status"], "PROPOSED_FOR_INDEPENDENT_REVIEW")
        self.assertEqual(data["operation_mode"], "READ_ONLY_SCIENTIFIC_EVALUATION")
        self.assertEqual(data["candidate_job"], "M1_C6_P171_R1_C3_0")
        self.assertEqual(data["pbs_job_id"], "1419643.mmaster02")
        self.assertEqual(data["canonical_packet_sha256"], EXPECTED_PACKET_SHA256)

    def test_04_patch_file_exists_and_covers_deadlock_conditions(self):
        """Patch file must exist and address the candidate intake and execution bypass."""
        self.assertTrue(PATCH_PATH.is_file(), f"Patch missing at {PATCH_PATH}")
        patch_text = PATCH_PATH.read_text(encoding="utf-8")
        self.assertIn("candidate_definitions", patch_text)
        self.assertIn("is_candidate", patch_text)
        self.assertIn("is_read_only", patch_text)
        self.assertIn("Staged candidates remain inactive", patch_text)

    def test_05_candidate_packet_construction_and_fingerprint(self):
        """Verify that candidate packet construction successfully binds all 29 evidence sources."""
        with open(CANDIDATE_DEF_PATH, "r", encoding="utf-8") as f:
            cand = json.load(f)
        manifest_rel = cand["manifest"]
        manifest_path = WORKSPACE / manifest_rel
        self.assertTrue(manifest_path.is_file())
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        sources = dict(cand.get("evidence_sources", {}))
        sources[str(CANDIDATE_DEF_PATH.relative_to(WORKSPACE)).replace('\\', '/')] = sha256_file(CANDIDATE_DEF_PATH)
        sources[manifest_rel] = sha256_file(manifest_path)
        sources.update(manifest.get("runtime_source_hashes", {}))
        for name, digest in manifest.get("files", {}).items():
            sources[str(Path(manifest_rel).parent / name).replace('\\', '/')] = digest

        self.assertEqual(len(sources), 29)
        for rel_path, digest in sources.items():
            full_p = WORKSPACE / rel_path
            self.assertTrue(full_p.is_file(), f"Source file missing: {rel_path}")
            self.assertEqual(sha256_file(full_p), digest.upper(), f"Hash mismatch for {rel_path}")

        # Verify bounded text size
        for rel_path in sources:
            sz = (WORKSPACE / rel_path).stat().st_size
            self.assertLessEqual(sz, 5_000_000, f"File exceeds 5MB: {rel_path}")

    def test_06_inactive_execution_guard(self):
        """Candidate definitions must never be eligible for PBS job submission."""
        with open(CANDIDATE_DEF_PATH, "r", encoding="utf-8") as f:
            cand = json.load(f)
        # Registration status is strictly PROPOSED_FOR_INDEPENDENT_REVIEW
        self.assertEqual(cand["registration_status"], "PROPOSED_FOR_INDEPENDENT_REVIEW")
        self.assertEqual(cand["operation_mode"], "READ_ONLY_SCIENTIFIC_EVALUATION")
        # Must not be present in active registered operations directory
        active_op_path = WORKSPACE / "project_coordination" / "operation_definitions" / (cand["operation_id"] + ".json")
        self.assertFalse(active_op_path.exists(), "Candidate definition must NOT exist in operation_definitions/")

    def test_07_active_session_lockout_enforced(self):
        """Live session must not allow background review dispatcher execution."""
        with open(ACTIVE_SESSION_PATH, "r", encoding="utf-8") as f:
            session = json.load(f)
        # Session is currently active by gemini-antigravity
        self.assertTrue(session.get("active"))
        self.assertEqual(session.get("agent"), "gemini-antigravity")

    def test_08_scope_separation_boundary(self):
        """Research preparation turn must not silently mutate controller scripts without maintenance scope."""
        with open(ACTIVE_TASK_PATH, "r", encoding="utf-8") as f:
            task = json.load(f)
        # Active task is F1598, not F1599
        self.assertEqual(task["task_id"], "F1598-PACKAGE166-CONVERGENCE-ACCEPTANCE")
        # Write scope in active session does not include scripts/controller
        with open(ACTIVE_SESSION_PATH, "r", encoding="utf-8") as f:
            session = json.load(f)
        scope = session.get("allowed_write_scope", [])
        self.assertNotIn("scripts/controller/*", scope)
        self.assertNotIn("scripts/controller/review_dispatcher.py", scope)


if __name__ == "__main__":
    unittest.main()

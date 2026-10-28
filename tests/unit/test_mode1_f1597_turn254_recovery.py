"""Unit test for Turn 254: Evidence-only recovery of interrupted task F1597 (run 81f408c0).

Validates:
1. Interrupted checkpoint SHA256 and content
2. Interrupted controller turn record and session state
3. Reconciled predecessor audit artifacts (Package 125 vs Package 126 R4)
4. HPC ledger job receipt registration and queue state
"""

import hashlib
import json
import os
import unittest


class TestMode1F1597Turn254Recovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workspace = r"D:\Master thesis\Adaptive remeshing"
        cls.checkpoint_path = r"C:\Users\pruth\OpenClawPAD\controller_turn_checkpoint.json.81f408c0-5218-48fe-8c65-b8fc86f56e81.partial.txt"
        cls.expected_checkpoint_sha256 = (
            "51A48CFF38EB2E670983A67E4CE5AF0852B17AB31DB4EA871DF53768A905F277".lower()
        )

    def test_01_interrupted_checkpoint_integrity(self):
        self.assertTrue(
            os.path.isfile(self.checkpoint_path),
            f"Checkpoint file missing: {self.checkpoint_path}",
        )
        with open(self.checkpoint_path, "rb") as f:
            content = f.read()
        calculated_sha = hashlib.sha256(content).hexdigest().lower()
        self.assertEqual(
            calculated_sha,
            self.expected_checkpoint_sha256,
            "Interrupted checkpoint SHA256 mismatch",
        )
        text = content.decode("utf-8", errors="replace")
        self.assertIn("Controller restart after interruption", text)

    def test_02_interrupted_turn_record(self):
        turn_file = os.path.join(
            self.workspace,
            "project_coordination",
            "controller",
            "turn-81f408c0-5218-48fe-8c65-b8fc86f56e81.json",
        )
        self.assertTrue(
            os.path.isfile(turn_file), f"Turn file missing: {turn_file}"
        )
        with open(turn_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(
            data.get("controller_run_id"), "81f408c0-5218-48fe-8c65-b8fc86f56e81"
        )
        self.assertEqual(data.get("stage"), "BOOTSTRAP_COMPLETE")
        self.assertIsNone(data.get("scientific_checkpoint"))

    def test_03_predecessor_audit_artifact(self):
        audit_file = os.path.join(
            self.workspace,
            "results",
            "validation",
            "package125_vs_package126_r4_convergence_audit.json",
        )
        self.assertTrue(
            os.path.isfile(audit_file), f"Audit file missing: {audit_file}"
        )
        with open(audit_file, "r", encoding="utf-8") as f:
            audit = json.load(f)
        self.assertEqual(
            audit.get("classification"),
            "ACCELERATION_CAUSES_OSCILLATORY_ITERATION",
        )
        self.assertFalse(audit.get("controlled_future_hypothesis_recommended"))

    def test_04_hpc_ledger_accounting(self):
        ledger_file = os.path.join(
            self.workspace, "project_coordination", "HPC_JOB_LEDGER.csv"
        )
        self.assertTrue(
            os.path.isfile(ledger_file), f"Ledger file missing: {ledger_file}"
        )
        with open(ledger_file, "r", encoding="utf-8") as f:
            text = f.read()
        self.assertIn("1418006.mmaster02", text)
        self.assertIn("1417969.mmaster02", text)


if __name__ == "__main__":
    unittest.main()

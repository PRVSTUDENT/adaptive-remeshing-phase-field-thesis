#!/usr/bin/env python3
"""Unit tests for Stage F3 Batch Readiness and Notch Topology Correction."""

import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

from scripts.model_generation.build_mode_ii_h2_serial import build_package as build_a
from scripts.model_generation.build_mode_ii_miseseri_preanalysis import build_package as build_b
from scripts.validation.validate_mode_ii_h2_static import validate_h2_static
from scripts.validation.validate_mode_ii_miseseri_preanalysis_static import validate_miseseri_static


class TestStageF3BatchReadiness(unittest.TestCase):
    def test_job_a_static_validation(self):
        res = validate_h2_static()
        self.assertTrue(res["passed"], f"Job A static validation failed: {res['failures']}")
        self.assertEqual(res["job_name"], "mode_ii_h2_uniform_serial")

    def test_job_b_static_validation(self):
        res = validate_miseseri_static()
        self.assertTrue(res["passed"], f"Job B static validation failed: {res['failures']}")
        self.assertEqual(res["job_name"], "mode_ii_miseseri_preanalysis")

    def test_job_b_notch_topology_audit(self):
        topo_json = ROOT / "models/generated/mode_ii/miseseri_preanalysis/TOPOLOGY_AUDIT.json"
        self.assertTrue(topo_json.is_file(), "TOPOLOGY_AUDIT.json missing")
        topo_data = json.loads(topo_json.read_text(encoding="utf-8"))

        self.assertTrue(topo_data["true_slit_topology_established"])
        self.assertEqual(topo_data["upper_face_nodes_count"], 15)
        self.assertEqual(topo_data["lower_face_nodes_count"], 15)
        self.assertEqual(topo_data["coincident_node_pairs_count"], 15)
        self.assertEqual(topo_data["shared_nodes_across_slit_count"], 0)
        self.assertEqual(topo_data["shared_elements_across_slit_count"], 0)
        self.assertEqual(topo_data["notch_tip_coordinates"], {"x_mm": 0.0, "y_mm": 0.0})

    def test_deterministic_generation(self):
        with tempfile.TemporaryDirectory() as dir1, tempfile.TemporaryDirectory() as dir2:
            res1 = build_b(out_dir=Path(dir1))
            res2 = build_b(out_dir=Path(dir2))
            self.assertEqual(res1["deck_sha256"], res2["deck_sha256"])

        with tempfile.TemporaryDirectory() as dir1, tempfile.TemporaryDirectory() as dir2:
            res1_a = build_a(out_dir=Path(dir1))
            res2_a = build_a(out_dir=Path(dir2))
            self.assertEqual(res1_a["deck_sha256"], res2_a["deck_sha256"])

    def test_proposal_json_unapproved(self):
        proposal_file = ROOT / "runs/hpc/stage_f/MODE_II_STAGE_F3_AUTHORIZATION_PROPOSAL.json"
        self.assertTrue(proposal_file.is_file(), "Proposal JSON missing")
        proposal = json.loads(proposal_file.read_text(encoding="utf-8"))

        self.assertFalse(proposal["execution_authorized"])
        self.assertFalse(proposal["submission_approved"])
        self.assertEqual(proposal["maximum_jobs_now"], 0)
        self.assertEqual(len(proposal["candidate_jobs"]), 2)


if __name__ == "__main__":
    unittest.main()

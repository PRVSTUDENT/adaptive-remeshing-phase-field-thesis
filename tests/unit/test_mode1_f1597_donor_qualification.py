#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_mode1_f1597_donor_qualification.py
=======================================
Unit test verifying authentic 2.5 um donor state extraction, energy reconciliation,
and classification under Task F1597.
"""

import hashlib
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
AUDIT_JSON = REPO_ROOT / "results/validation/f1597_donor_h0025_qualification_audit.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


class TestMode1F1597DonorQualification(unittest.TestCase):
    def setUp(self):
        self.assertTrue(AUDIT_JSON.is_file(), f"Missing audit file: {AUDIT_JSON}")
        with open(AUDIT_JSON, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    def test_schema_and_status(self):
        self.assertEqual(self.data.get("schema"), 1)
        self.assertEqual(self.data.get("status"), "PREPARATION_COMPLETE")
        self.assertTrue(self.data.get("verification_passed"))
        self.assertEqual(self.data.get("classification"), "DONOR_STATE_AVAILABLE_WITH_LIMITATIONS")

    def test_hpc_provenance(self):
        prov = self.data["hpc_provenance"]
        self.assertEqual(prov["pbs_job_id"], "1416259.mmaster02")
        self.assertEqual(prov["total_solved_increments"], 197)
        self.assertAlmostEqual(prov["peak_rf2_N"], 186.2309, places=2)
        self.assertAlmostEqual(prov["peak_u_top_mm"], 0.001882, places=4)
        self.assertGreater(prov["terminal_step_time"], 0.90)

    def test_transfer_checkpoint(self):
        ckpt = self.data["transfer_checkpoint_u00254"]
        self.assertEqual(ckpt["target_u_top_mm"], 0.00254)
        self.assertEqual(ckpt["closest_discrete_inc"], 111)
        self.assertAlmostEqual(ckpt["interpolated_rf2_N"], 3.2662, places=3)
        self.assertAlmostEqual(ckpt["fracture_energy_mJ"], 0.303883, places=4)
        self.assertAlmostEqual(ckpt["elastic_energy_mJ"], 0.004148, places=4)

    def test_comparison_with_reference(self):
        comp = self.data["comparison_with_reference_5um"]
        self.assertAlmostEqual(comp["reference_rf2_N"], 7.851222, places=4)
        self.assertAlmostEqual(comp["donor_25um_rf2_N"], 3.266202, places=4)
        self.assertAlmostEqual(comp["delta_rf2_pct"], -58.40, places=1)
        self.assertAlmostEqual(comp["authentic_solved_e_frac_mJ"], 0.303883, places=4)

    def test_gate_c1_1_failed_status(self):
        gate = self.data["gate_c1_1_status"]
        self.assertEqual(gate["current_gate_state"], "FAILED")
        self.assertFalse(gate["force_continuity_criterion_met"])
        self.assertFalse(gate["fracture_energy_continuity_criterion_met"])

    def test_evidence_hashes(self):
        evidence = self.data["evidence_sources"]
        self.assertGreaterEqual(len(evidence), 6)
        for rel_path, expected_hash in evidence.items():
            full_path = REPO_ROOT / rel_path
            self.assertTrue(full_path.is_file(), f"Evidence file missing: {full_path}")
            actual_hash = sha256_file(full_path)
            self.assertEqual(actual_hash, expected_hash, f"Hash mismatch on {rel_path}")


if __name__ == "__main__":
    unittest.main()

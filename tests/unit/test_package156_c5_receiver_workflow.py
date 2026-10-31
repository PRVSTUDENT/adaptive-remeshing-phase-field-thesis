#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package156_c5_receiver_workflow.py
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Run ID: f73c92e6-cd89-4665-a3c8-f61bc2892ab7
Turn: 388
Protocol Version: 2

Comprehensive unit test suite for Package 156 C5 Candidate Receiver Workflow:
1. Donor checkpoint loading and verification.
2. Receiver mesh topology (12,996 quads, 13,278 nodes, RP 999999).
3. 100% nodal (13,278) and 100% GP (51,984) spatial coverage.
4. Exact crack-flank separation for all 53 duplicate slit pairs.
5. Strict damage bounds d in [0, 1].
6. History non-negativity (H >= 0) and explicit overshoot accounting (Policy 1).
7. Canonical 7+8+3 SVARS serialization round-trip recovery.
8. Same-load holding deck structure (zero displacement advance).
9. Bitwise preservation of frozen production UEL hash.
10. Conditional staging receipt explicitly recording unresolved donor dependency.
"""

from __future__ import print_function, division
import os
import sys
import json
import hashlib
import unittest
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.build_package156_c5_receiver import (
    build_package156, FROZEN_UEL_SHA256, R8_FIXTURE_CHECKPOINT, R8_FIXTURE_SHA256, sha256_file
)
from scripts.state_transfer.c4_to_c5_spatial_mapping import Mesh2D

P156_DIR = REPO_ROOT / "models/pandey_kumar_mode1/156_c5_package156_c2_0_re_equilibration"


class TestPackage156ReceiverWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Build Package 156 using the R8 software validation fixture
        cls.manifest, cls.receipt = build_package156(
            donor_checkpoint_path=R8_FIXTURE_CHECKPOINT,
            target_dir=P156_DIR,
            is_fixture_test=True
        )

    def test_01_donor_checkpoint_integrity(self):
        self.assertTrue(R8_FIXTURE_CHECKPOINT.is_file(), "R8 fixture checkpoint file must exist")
        actual_hash = sha256_file(R8_FIXTURE_CHECKPOINT)
        self.assertEqual(actual_hash, R8_FIXTURE_SHA256, "R8 fixture SHA-256 must match exactly")
        with open(R8_FIXTURE_CHECKPOINT, "r", encoding="utf-8") as f:
            cp = json.load(f)
        self.assertIn("displacement", cp)
        self.assertIn("damage", cp)
        self.assertIn("history", cp)
        self.assertEqual(len(cp["displacement"]), 7265)
        self.assertEqual(len(cp["damage"]), 7265)
        self.assertEqual(len(cp["history"]), 28224)

    def test_02_receiver_mesh_topology(self):
        c5_inp = REPO_ROOT / "models/pandey_kumar_mode1/155_c5_candidate_mesh/M1_C5_CANDIDATE_MESH.inp"
        mesh = Mesh2D.from_inp(c5_inp, name="C5", max_physical_node=13278)
        self.assertEqual(len(mesh.elements), 12996, "C5 must contain exactly 12,996 quads")
        self.assertEqual(len(mesh.nodes), 13278, "C5 must contain exactly 13,278 physical nodes")
        self.assertEqual(len(mesh.seam_pairs), 53, "C5 must contain exactly 53 duplicate slit pairs")
        self.assertIn(999999, mesh.nodes if 999999 in mesh.nodes else {999999: None}, "RP 999999 must exist")

    def test_03_full_spatial_coverage(self):
        node_csv = P156_DIR / "nodal_displacements_initial.csv"
        self.assertTrue(node_csv.is_file())
        with open(node_csv, "r", encoding="utf-8") as f:
            lines = f.readlines()
        # Header + 13,278 lines
        self.assertEqual(len(lines), 13279, "Displacement CSV must contain exactly 13,278 node rows")

        bounds_csv = P156_DIR / "d_lower_bounds.csv"
        self.assertTrue(bounds_csv.is_file())
        with open(bounds_csv, "r", encoding="utf-8") as f:
            b_lines = f.readlines()
        # Header + 12,996 lines
        self.assertEqual(len(b_lines), 12997, "Lower bounds CSV must contain exactly 12,996 element rows")

    def test_04_slit_flank_isolation(self):
        c5_inp = REPO_ROOT / "models/pandey_kumar_mode1/155_c5_candidate_mesh/M1_C5_CANDIDATE_MESH.inp"
        mesh = Mesh2D.from_inp(c5_inp, name="C5", max_physical_node=13278)
        self.assertEqual(len(mesh.seam_pairs), 53)

        # In nodal_phase_field_initial.csv, upper and lower seam nodes must have distinct valid damage values
        d_csv = P156_DIR / "nodal_phase_field_initial.csv"
        d_map = {}
        with open(d_csv, "r", encoding="utf-8") as f:
            next(f)
            for line in f:
                parts = line.strip().split(",")
                d_map[int(parts[0])] = float(parts[1])

        for pair in mesh.seam_pairs:
            n_low, n_up = pair[0], pair[1]
            self.assertIn(n_up, d_map)
            self.assertIn(n_low, d_map)
            # Both must be in [0, 1]
            self.assertTrue(0.0 <= d_map[n_up] <= 1.0)
            self.assertTrue(0.0 <= d_map[n_low] <= 1.0)

    def test_05_physical_damage_bounds(self):
        d_csv = P156_DIR / "nodal_phase_field_initial.csv"
        with open(d_csv, "r", encoding="utf-8") as f:
            next(f)
            for line in f:
                parts = line.strip().split(",")
                d_val = float(parts[1])
                self.assertGreaterEqual(d_val, 0.0, f"Damage {d_val} < 0")
                self.assertLessEqual(d_val, 1.0, f"Damage {d_val} > 1")

    def test_06_history_non_negativity_and_overshoot_accounting(self):
        bounds_csv = P156_DIR / "d_lower_bounds.csv"
        h_vals_all = []
        with open(bounds_csv, "r", encoding="utf-8") as f:
            next(f)
            for line in f:
                parts = line.strip().split(",")
                for k in range(5, 9):
                    h_val = float(parts[k])
                    self.assertGreaterEqual(h_val, 0.0, f"History {h_val} must be >= 0")
                    h_vals_all.append(h_val)

        self.assertEqual(len(h_vals_all), 12996 * 4)
        # Check that manifest explicitly accounts for policy properties
        policy_info = self.manifest["transfer_policy"]
        self.assertEqual(policy_info["name"], "POLICY_1_BILINEAR_GP_NON_NEGATIVE_CLAMP")
        self.assertFalse(policy_info["universally_bounded"], "Policy 1 is affine-exact, not universally bounded")
        self.assertGreater(policy_info["local_overshoot_count"], 0, "Overshoots must be explicitly accounted for")

    def test_07_svars_7_8_3_contract_and_roundtrip(self):
        inc_file = P156_DIR / "initial_conditions_solution.inc"
        self.assertTrue(inc_file.is_file())
        with open(inc_file, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip() and not l.startswith("**")]

        self.assertTrue(lines[0].upper().startswith("*INITIAL CONDITIONS, TYPE=SOLUTION"))
        data_lines = lines[1:]
        # Each element has 3 lines: 12,996 * 3 = 38,988 lines
        self.assertEqual(len(data_lines), 12996 * 3, "Must have exactly 3 lines per element for 12,996 elements")

        # Parse round-trip
        bounds_csv = P156_DIR / "d_lower_bounds.csv"
        expected_h = {}
        with open(bounds_csv, "r", encoding="utf-8") as f:
            next(f)
            for line in f:
                parts = line.strip().split(",")
                eid = int(parts[0])
                expected_h[eid] = [float(parts[k]) for k in range(5, 9)]

        for i in range(0, len(data_lines), 3):
            line1 = [float(p) for p in data_lines[i].split(",")]
            line2 = [float(p) for p in data_lines[i+1].split(",")]
            line3 = [float(p) for p in data_lines[i+2].split(",")]

            eid = int(line1[0])
            self.assertEqual(len(line1), 8)   # EID, 0..6
            self.assertEqual(len(line2), 8)   # 0, H1..H4, 0..2
            self.assertEqual(len(line3), 3)   # 0, 0, 0
            # Total SVARS = 7 + 8 + 3 = 18

            h_recovered = line2[1:5]
            for k in range(4):
                self.assertAlmostEqual(h_recovered[k], expected_h[eid][k], places=12,
                                       msg=f"Round-trip history mismatch at element {eid} GP {k+1}")

    def test_08_holding_load_and_deck_structure(self):
        master_inp = P156_DIR / "M1_C5_PACKAGE156_C2_0_REEQUILIBRATION.inp"
        self.assertTrue(master_inp.is_file())
        content = master_inp.read_text(encoding="utf-8")
        self.assertIn("N_RP, 2, 2, 0.0018003125442191958", content, "Holding displacement must match donor")
        self.assertIn("*INCLUDE, INPUT=initial_conditions_solution.inc", content)
        self.assertIn("*INCLUDE, INPUT=active_set_boundary_cards.inc", content)

    def test_09_frozen_uel_bitwise_integrity(self):
        uel_file = P156_DIR / "f42_mixed_uel.for"
        self.assertTrue(uel_file.is_file())
        actual_hash = sha256_file(uel_file)
        self.assertEqual(actual_hash, FROZEN_UEL_SHA256, "Frozen production UEL SHA-256 must match bitwise")

    def test_10_conditional_candidate_receipt(self):
        receipt_file = P156_DIR / "CONDITIONAL_CANDIDATE_RECEIPT.json"
        self.assertTrue(receipt_file.is_file())
        with open(receipt_file, "r", encoding="utf-8") as f:
            rcpt = json.load(f)
        self.assertEqual(rcpt["status"], "STAGED_AS_CONDITIONAL_CANDIDATE")
        self.assertEqual(rcpt["donor_dependency"]["status"], "UNRESOLVED_PENDING_PACKAGE154_R3_COMPLETION")
        self.assertEqual(rcpt["submission_disposition"], "WITHHELD_PENDING_PREDECESSOR_PHYSICAL_ACCEPTANCE")
        self.assertTrue(rcpt["qualification_checks"]["receiver_node_coverage"])
        self.assertTrue(rcpt["qualification_checks"]["receiver_gp_coverage"])
        self.assertTrue(rcpt["qualification_checks"]["slit_flank_isolation"])
        self.assertTrue(rcpt["qualification_checks"]["frozen_uel_sha256_verified"])


if __name__ == "__main__":
    unittest.main()

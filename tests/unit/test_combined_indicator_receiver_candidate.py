#!/usr/bin/env python3
"""
test_combined_indicator_receiver_candidate.py

Unit test suite for Method C Package 159 combined-indicator receiver restart readiness (Turn 435).
Verifies:
1. Manifest schema, status, and anchor state.
2. Mesh topology, Jacobians, and duplicate crack-flank seam nodes.
3. Physical energy conservation within <= 2.0% continuity gate.
4. Complete nodal and GP state transfer with zero cross-slit flank contamination.
5. Exact disk file existence and SHA-256 hash integrity.
6. Input deck equation constraints, boundary conditions, and frozen UEL preservation.
"""

import unittest
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path("D:/Master thesis/Adaptive remeshing")
PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/159_combined_indicator_receiver_candidate"
MANIFEST_PATH = PKG_DIR / "candidate_receiver_manifest.json"
FROZEN_UEL_HASH = "CE8D5EDCD2911DCB018BB15275271F874E7EA62B8FB48CF4A8297469A83ACDD6"

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()

class TestCombinedIndicatorReceiverCandidate(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.assertTrue(cls, MANIFEST_PATH.exists(), f"Manifest not found at {MANIFEST_PATH}")
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            cls.manifest = json.load(f)

    def test_manifest_schema_and_status(self):
        self.assertEqual(self.manifest.get("schema"), 1)
        self.assertEqual(self.manifest.get("package_name"), "PACKAGE_159_COMBINED_INDICATOR_RECEIVER_CANDIDATE")
        self.assertEqual(self.manifest.get("investigation"), "COMBINED_INDICATOR_RECEIVER_RESTART_READINESS")
        self.assertEqual(self.manifest.get("status"), "RECEIVER_INPUT_OFFLINE_VERIFIED")

    def test_mesh_topology(self):
        topo = self.manifest["mesh_topology"]
        self.assertEqual(topo["physical_quads"], 13924)
        self.assertEqual(topo["total_uel_elements"], 27848)
        self.assertEqual(topo["physical_nodes"], 14216)
        self.assertEqual(topo["reference_node_rp"], 999999)
        self.assertEqual(topo["duplicate_slit_flank_pairs"], 55)
        self.assertTrue(topo["positive_jacobians_verified"])
        self.assertGreater(topo["min_det_jacobian"], 0.0)
        self.assertLessEqual(topo["resolution_ratio_to_l0"], 1.0 / 10.0)

    def test_energy_conservation_gates(self):
        energies = self.manifest["energy_verification"]["energies_kNmm"]
        gates = self.manifest["energy_verification"]["energy_gates_satisfied"]
        self.assertLessEqual(energies["fracture_discrepancy_percent"], 2.0)
        self.assertLessEqual(energies["elastic_discrepancy_percent"], 2.0)
        self.assertLessEqual(energies["total_discrepancy_percent"], 2.0)
        self.assertTrue(gates["fracture_gate_pass"])
        self.assertTrue(gates["elastic_gate_pass"])
        self.assertTrue(gates["total_raw_gate_pass"])

    def test_transfer_integrity(self):
        tf = self.manifest["transfer_integrity"]
        self.assertEqual(tf["mapped_nodes"], 14216)
        self.assertEqual(tf["unmapped_nodes"], 0)
        self.assertEqual(tf["mapped_gps"], 55696)
        self.assertEqual(tf["unmapped_gps"], 0)
        self.assertEqual(tf["cross_slit_violations"], 0)
        self.assertEqual(tf["active_damage_nodes_count"], 119)
        self.assertTrue(tf["damage_monotonicity_satisfied"])
        self.assertTrue(tf["damage_bounds_satisfied"])

    def test_deck_hashes_and_files(self):
        deck_hashes = self.manifest["deck_hashes"]
        for filename, expected_hash in deck_hashes.items():
            fpath = PKG_DIR / filename
            self.assertTrue(fpath.is_file(), f"Missing expected file: {filename}")
            actual_hash = sha256_file(fpath)
            self.assertEqual(actual_hash, expected_hash, f"Hash mismatch for {filename}")

        # Frozen UEL exact verification
        uel_path = PKG_DIR / "f42_mixed_uel.for"
        self.assertEqual(sha256_file(uel_path), FROZEN_UEL_HASH)

    def test_input_deck_cards(self):
        # Inspect mechanical deck
        dc_mech = PKG_DIR / "P159_MECHANICAL_DC.inp"
        with open(dc_mech, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("*USER ELEMENT, TYPE=U1", content)
        self.assertIn("*USER ELEMENT, TYPE=U2", content)
        self.assertIn("*INCLUDE, INPUT=initial_conditions_solution.inc", content)
        self.assertIn("*INCLUDE, INPUT=active_set_boundary_cards.inc", content)
        self.assertIn("N_RP, 2, 2, 1.8603125442e-03", content)

    def test_comparison_with_package158(self):
        comp = self.manifest["comparison_with_package158"]
        self.assertEqual(comp["p158_elements"], 12544)
        self.assertEqual(comp["p159_elements"], 13924)
        self.assertEqual(comp["element_delta"], 1380)
        self.assertEqual(comp["p158_seam_pairs"], 52)
        self.assertEqual(comp["p159_seam_pairs"], 55)


if __name__ == "__main__":
    unittest.main()

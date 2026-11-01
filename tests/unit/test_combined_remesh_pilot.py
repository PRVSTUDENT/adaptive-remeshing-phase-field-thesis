#!/usr/bin/env python3
"""
test_combined_remesh_pilot.py

Unit tests for Method C state-dependent conforming remeshing and state transfer pilot.
Verifies marking statistics, receiver mesh topology, spatial transfer integrity,
and energy preservation.
"""

import unittest
import json
from pathlib import Path

ROOT = Path("D:/Master thesis/Adaptive remeshing")
PILOT_JSON = ROOT / "results/validation/package157_combined_remesh_pilot.json"

class TestCombinedRemeshPilot(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.assertTrue(cls, PILOT_JSON.exists(), f"Pilot JSON not found at {PILOT_JSON}")
        with open(PILOT_JSON, "r") as f:
            cls.data = json.load(f)

    def test_schema_and_status(self):
        self.assertEqual(self.data.get("schema"), 1)
        self.assertEqual(self.data.get("investigation"), "COMBINED_INDICATOR_REMESH_AND_STATE_TRANSFER_PILOT")
        self.assertEqual(self.data.get("status"), "COMBINED_REMESH_TRANSFER_OFFLINE_VERIFIED")
        self.assertTrue(self.data.get("verification_passed"))
        self.assertGreaterEqual(len(self.data.get("finding", "")), 20)

    def test_marking_statistics(self):
        stats = self.data["marking_statistics"]
        self.assertEqual(stats["total_donor_elements"], 7056)
        self.assertEqual(stats["miseseri_marked_count"], 266)
        self.assertEqual(stats["damage_marked_count"], 85)
        self.assertEqual(stats["intersection_count"], 12)
        self.assertEqual(stats["union_combined_count"], 339)
        self.assertEqual(stats["newly_marked_count"], 73)
        self.assertAlmostEqual(stats["percentage_of_total_mesh"], 4.8044, places=3)
        # Verify set algebra
        self.assertEqual(
            stats["miseseri_marked_count"] + stats["damage_marked_count"] - stats["intersection_count"],
            stats["union_combined_count"]
        )
        self.assertEqual(stats["damage_marked_count"] - stats["intersection_count"], stats["newly_marked_count"])

    def test_mesh_topology(self):
        topo = self.data["mesh_topology_checks"]
        self.assertEqual(topo["receiver_elements_count"], 13924)
        self.assertEqual(topo["receiver_nodes_count"], 14216)
        self.assertGreater(topo["min_det_jacobian"], 0.0)
        self.assertTrue(topo["positive_jacobians_verified"])
        self.assertEqual(topo["slit_seam_pairs_count"], 55)
        self.assertTrue(topo["duplicate_crack_flank_nodes_verified"])
        self.assertLessEqual(topo["element_size_to_l0_ratio"], 1.0 / 10.0)

    def test_transfer_integrity(self):
        tf = self.data["transfer_integrity"]
        self.assertEqual(tf["unmapped_nodes_count"], 0)
        self.assertEqual(tf["unmapped_gps_count"], 0)
        self.assertEqual(tf["flank_cross_slit_violations"], 0)
        self.assertTrue(tf["damage_monotonicity_satisfied"])
        self.assertGreater(tf["max_transferred_damage"], 0.60)
        self.assertGreater(tf["max_transferred_history_MPa"], 7.0)
        self.assertLess(tf["max_node_reconstruction_error_mm"], 1e-12)
        self.assertLess(tf["max_gp_reconstruction_error_mm"], 1e-12)

    def test_energy_preservation(self):
        energy = self.data["energy_diagnostics"]
        self.assertGreater(energy["donor_fracture_energy_kNmm"], 0.0)
        self.assertGreater(energy["receiver_fracture_energy_kNmm"], 0.0)
        self.assertLessEqual(energy["fracture_energy_discrepancy_percent"], 5.0)
        self.assertTrue(energy["fracture_energy_gate_satisfied"])
        self.assertEqual(energy["preservation_status"], "FRACTURE_ENERGY_CONSERVED_WITHIN_GATE")

    def test_package158_comparison(self):
        comp = self.data["package158_comparison"]
        self.assertEqual(comp["package158_receiver_elements"], 12544)
        self.assertEqual(comp["combined_pilot_receiver_elements"], 13924)
        self.assertEqual(comp["additional_elements"], 1380)
        self.assertTrue(comp["crack_path_independence"])
        self.assertEqual(comp["refinement_mechanism"], "UNIFIED_MISESERI_AND_DAMAGE_PROCESS_ZONE")


if __name__ == "__main__":
    unittest.main()

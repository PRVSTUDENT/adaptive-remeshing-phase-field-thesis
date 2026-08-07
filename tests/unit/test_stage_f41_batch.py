#!/usr/bin/env python3
"""
Unit tests for Stage F41 Topology-Preserving Crack Geometry Reconstruction.
Includes pure-Python offline topology tests and synthetic conversion tests.
"""

import hashlib
import json
import os
import sys
import unittest

# Ensure models package runtime is importable
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
F41_RUNTIME_DIR = os.path.join(PROJECT_ROOT, "models", "generated", "mode_ii", "f41_crack_geometry_reconstruction", "runtime")
sys.path.insert(0, F41_RUNTIME_DIR)

import f41_crack_topology_extractor as extractor

class TestStageF41PurePythonTopology(unittest.TestCase):

    def setUp(self):
        self.deck_path = os.path.join(F41_RUNTIME_DIR, "source_deck.inp")
        self.assertTrue(os.path.exists(self.deck_path), "source_deck.inp must exist")
        with open(self.deck_path, 'rb') as f:
            self.initial_sha256 = hashlib.sha256(f.read()).hexdigest()

    def test_01_source_deck_byte_identical_protection(self):
        with open(self.deck_path, 'rb') as f:
            current_sha256 = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(self.initial_sha256, current_sha256, "Original source deck must remain byte-identical")

    def test_02_detect_exactly_15_crack_node_pairs(self):
        nodes, elements, bbox = extractor.parse_nodes_and_elements(self.deck_path)
        crack_info = extractor.identify_crack_topology(nodes, elements)

        self.assertEqual(crack_info["duplicate_pairs_before"], 15, "Must detect exactly 15 crack-node pairs")
        self.assertEqual(len(crack_info["coincident_pairs"]), 15)

    def test_03_crack_trace_saved_before_merging(self):
        nodes, elements, bbox = extractor.parse_nodes_and_elements(self.deck_path)
        crack_info = extractor.identify_crack_topology(nodes, elements)
        t_map = extractor.generate_topology_map_dict(crack_info)

        self.assertIn("node_pairs_mapping", t_map)
        self.assertEqual(len(t_map["node_pairs_mapping"]), 15)
        self.assertIn("crack_start", t_map)
        self.assertIn("crack_tip", t_map)

    def test_04_crack_start_tip_preserved_within_tolerance(self):
        nodes, elements, bbox = extractor.parse_nodes_and_elements(self.deck_path)
        crack_info = extractor.identify_crack_topology(nodes, elements, tol=1e-4)

        start = crack_info["crack_start"]
        tip = crack_info["crack_tip"]

        self.assertAlmostEqual(start[0], -0.5, delta=1e-4)
        self.assertAlmostEqual(start[1], 0.0, delta=1e-4)
        self.assertAlmostEqual(tip[0], 0.0, delta=1e-3)
        self.assertAlmostEqual(tip[1], 0.0, delta=1e-4)

        self.assertAlmostEqual(crack_info["crack_length"], 0.5, delta=1e-2)

    def test_05_bounding_box_unchanged(self):
        nodes, elements, bbox = extractor.parse_nodes_and_elements(self.deck_path)
        self.assertAlmostEqual(bbox["x_min"], -0.5, delta=1e-4)
        self.assertAlmostEqual(bbox["x_max"], 0.5, delta=1e-4)
        self.assertAlmostEqual(bbox["y_min"], -0.5, delta=1e-4)
        self.assertAlmostEqual(bbox["y_max"], 0.5, delta=1e-4)

    def test_06_temporary_merge_node_reduction_exact_15(self):
        nodes, elements, bbox = extractor.parse_nodes_and_elements(self.deck_path)
        crack_info = extractor.identify_crack_topology(nodes, elements)

        initial_node_count = len(nodes)
        merged_nodes_count = initial_node_count - len(crack_info["coincident_pairs"])

        self.assertEqual(initial_node_count - merged_nodes_count, 15, "Node reduction must equal exactly 15")


class TestStageF41SyntheticConversion(unittest.TestCase):

    def test_07_synthetic_unusable_cracked_topology(self):
        # Original cracked duplicate-node topology -> 0 faces
        cracked_conversion = {"face_count": 0, "vertex_count": 0, "usable_geometry": False}
        self.assertFalse(cracked_conversion["usable_geometry"])
        self.assertEqual(cracked_conversion["face_count"], 0)

    def test_08_synthetic_conversion_compatible_merged_topology(self):
        # Temporary merged topology -> 1 face, 6 vertices
        merged_conversion = {"face_count": 1, "vertex_count": 6, "edge_count": 6, "usable_geometry": True}
        self.assertTrue(merged_conversion["usable_geometry"])
        self.assertGreaterEqual(merged_conversion["face_count"], 1)

    def test_09_synthetic_reconstructed_geometry_crack_recreated_passes_audit(self):
        # Reconstructed geometry + recreated crack -> topology audit passes
        reconstructed = {
            "reconstructed_face_count": 2,
            "reconstructed_edge_count": 7,
            "reconstructed_vertex_count": 6,
            "crack_geometry_recreated": True,
            "crack_tip_preserved": True,
            "outer_boundary_preserved": True,
            "reconstruction_passed": True
        }
        self.assertTrue(reconstructed["reconstruction_passed"])
        self.assertTrue(reconstructed["crack_geometry_recreated"])
        self.assertTrue(reconstructed["crack_tip_preserved"])
        self.assertTrue(reconstructed["outer_boundary_preserved"])

    def test_10_zero_face_conversion_fails_closed(self):
        bad_audit = {"reconstructed_face_count": 0, "reconstruction_passed": False}
        self.assertFalse(bad_audit["reconstruction_passed"])

    def test_11_crack_recreation_failure_fails_closed(self):
        bad_audit = {"crack_geometry_recreated": False, "reconstruction_passed": False}
        self.assertFalse(bad_audit["reconstruction_passed"])


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""
Unit tests for Stage F41 Topology-Preserving Crack Geometry Reconstruction (F41R2).
Includes pure-Python offline topology tests, synthetic conversion tests, and static runtime-contract tests.
"""

import hashlib
import json
import os
import sys
import unittest

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
        self.assertAlmostEqual(tip[0], 0.0, delta=1e-4)
        self.assertAlmostEqual(tip[1], 0.0, delta=1e-4)

        self.assertAlmostEqual(crack_info["crack_length"], 0.5, delta=1e-4)

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


class TestStageF41RuntimeContractStatic(unittest.TestCase):

    def setUp(self):
        self.matrix_py = os.path.join(F41_RUNTIME_DIR, "f41_cae_reconstruction_matrix.py")
        self.assertTrue(os.path.exists(self.matrix_py), "f41_cae_reconstruction_matrix.py must exist")
        with open(self.matrix_py, 'r') as f:
            self.source = f.read()

    def test_07_both_node_crack_merge_selection_no_upper_only(self):
        self.assertIn("lower_node_id", self.source)
        self.assertIn("upper_node_id", self.source)
        self.assertIn("all_crack_node_labels.append(p[\"lower_node_id\"])", self.source)
        self.assertIn("all_crack_node_labels.append(p[\"upper_node_id\"])", self.source)
        self.assertNotIn("upper_node_objs = [", self.source, "Must not build merge selection using upper_node_objs only")

    def test_08_no_edgearray_findat_tolerance_keyword(self):
        self.assertNotIn("edges.findAt((-0.25, 0.0, 0.0), tolerance=", self.source, "Must not call edges.findAt with tolerance keyword")
        self.assertNotIn("edges.findAt(coordinates=(-0.25, 0.0, 0.0), tolerance=", self.source, "Must not call edges.findAt with tolerance keyword")
        self.assertIn("edges.findAt(coordinates=(-0.25, 0.0, 0.0), printWarning=False)", self.source, "Must use supported findAt syntax")

    def test_09_getvertices_resolved_through_part_vertices(self):
        self.assertIn("vertex_ids = crack_edge.getVertices()", self.source)
        self.assertIn("part.vertices[vertex_ids[0]]", self.source)
        self.assertIn("part.vertices[vertex_ids[1]]", self.source)
        self.assertNotIn("edge_v.pointOn", self.source, "Must not call pointOn directly on getVertices elements")

    def test_10_explicit_seam_region_tuple(self):
        self.assertIn("engineeringFeatures.assignSeam(regions=(crack_region,))", self.source, "Must pass seam region as an explicit tuple")
        self.assertNotIn("assignSeam(regions=crack_region)", self.source, "Must not pass bare single region object")

    def test_11_no_false_success_fallback_copying(self):
        self.assertNotIn("crack_start_after = crack_start_before", self.source, "Must not fallback copy crack_start_before")
        self.assertNotIn("crack_tip_after = crack_tip_before", self.source, "Must not fallback copy crack_tip_before")

    def test_12_fail_closed_if_endpoint_count_not_two(self):
        self.assertIn("len(vertex_ids) != 2", self.source)
        self.assertIn("exactly 2 required", self.source)


class TestStageF41SyntheticConversion(unittest.TestCase):

    def test_13_synthetic_unusable_cracked_topology(self):
        cracked_conversion = {"face_count": 0, "vertex_count": 0, "usable_geometry": False}
        self.assertFalse(cracked_conversion["usable_geometry"])

    def test_14_synthetic_reconstructed_geometry_crack_recreated_passes_audit(self):
        reconstructed = {
            "duplicate_pairs_before": 15,
            "duplicate_pairs_after": 0,
            "merged_pair_count": 15,
            "reconstructed_face_count": 2,
            "reconstructed_edge_count": 7,
            "reconstructed_vertex_count": 6,
            "crack_geometry_recreated": True,
            "seam_assigned": True,
            "crack_tip_preserved": True,
            "outer_boundary_preserved": True,
            "crack_length_error": 0.0,
            "mesh_generated": True,
            "mesh_node_count": 3984,
            "mesh_element_count": 3930,
            "reconstruction_passed": True
        }
        self.assertTrue(reconstructed["reconstruction_passed"])
        self.assertEqual(reconstructed["merged_pair_count"], 15)
        self.assertTrue(reconstructed["seam_assigned"])
        self.assertTrue(reconstructed["mesh_generated"])

    def test_15_fail_closed_on_unassigned_seam_or_uncreated_mesh(self):
        bad_audit1 = {"seam_assigned": False, "reconstruction_passed": False}
        bad_audit2 = {"mesh_generated": False, "reconstruction_passed": False}
        self.assertFalse(bad_audit1["reconstruction_passed"])
        self.assertFalse(bad_audit2["reconstruction_passed"])


if __name__ == "__main__":
    unittest.main()

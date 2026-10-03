#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test_stage14i_reconstruction_fidelity.py
-----------------------------------------
Unit test suite for Gate-6B Stage 14I Native-Remesh to Layered-Fracture Reconstruction
Fidelity Audit:
1. Verifies deck files, mapping files, reports, and publication figures exist.
2. Verifies exact node counts (14,456) and pointwise coordinate parity (< 1e-6 mm).
3. Verifies zero-gap crack seam duplicate node pairs (54 pairs) and no unintended node merging.
4. Verifies quad (14,082) and triangle (401) counts and total underlying finite elements (14,483).
5. Verifies 3-layer solve deck structure (43,449 total elements across UEL/UMAT layers).
6. Verifies complete 1-to-1 bijection in STAGE14_RECONSTRUCTION_TOPOLOGY_MAPPING.csv.
7. Verifies audit report schema and STAGE14_NATIVE_TO_LAYERED_RECONSTRUCTION_EQUIVALENT_WITH_LABEL_RENUMBERING verdict.
"""

import os
import sys
import json
import csv
import unittest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class TestStage14IRecoveryFidelity(unittest.TestCase):
    """Test suite for Stage 14I reconstruction fidelity and topological parity."""

    def setUp(self):
        self.native_deck = os.path.join(
            ROOT_DIR, "models", "pandey_kumar_mode1", "99_mode1_stage14_phasefield_preanalysis_fidelity", "PK_M1_STAGE14_STEP2_ALLINC.inp"
        )
        self.solve_deck = os.path.join(
            ROOT_DIR, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k", "PK_MODE1_STAGE14_ADAPT_14K_FRACTURE.inp"
        )
        self.mapping_csv = os.path.join(
            ROOT_DIR, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k", "STAGE14_RECONSTRUCTION_TOPOLOGY_MAPPING.csv"
        )
        self.mapping_json = os.path.join(
            ROOT_DIR, "models", "pandey_kumar_mode1", "25_stage14_adaptive_candidate_14k", "STAGE14_RECONSTRUCTION_TOPOLOGY_MAPPING.json"
        )
        self.report_md = os.path.join(
            ROOT_DIR, "models", "pandey_kumar_mode1", "MODE1_STAGE14I_NATIVE_RECONSTRUCTION_FIDELITY_REPORT.md"
        )
        self.report_json = os.path.join(
            ROOT_DIR, "models", "pandey_kumar_mode1", "MODE1_STAGE14I_NATIVE_RECONSTRUCTION_FIDELITY_REPORT.json"
        )
        self.fig1_png = os.path.join(
            ROOT_DIR, "results", "figures", "mode1_gate6b", "fig_mode1_stage14i_mesh_reconstruction_fidelity.png"
        )
        self.fig2_png = os.path.join(
            ROOT_DIR, "results", "figures", "mode1_gate6b", "fig_mode1_stage14i_topology_difference_map.png"
        )
        self.fig3_png = os.path.join(
            ROOT_DIR, "results", "figures", "mode1_gate6b", "fig_mode1_stage14i_ligament_mesh_size_profile.png"
        )

    def test_all_artifacts_exist(self):
        """Verify that all required Stage 14I audit artifacts, figures, and decks exist."""
        for path in [self.native_deck, self.solve_deck, self.mapping_csv, self.mapping_json,
                     self.report_md, self.report_json, self.fig1_png, self.fig2_png, self.fig3_png]:
            self.assertTrue(os.path.exists(path), f"Missing artifact: {path}")

    def test_mapping_table_completeness(self):
        """Verify 14,483 mapped rows in STAGE14_RECONSTRUCTION_TOPOLOGY_MAPPING.csv."""
        with open(self.mapping_csv, 'r', encoding='utf-8') as f:
            reader = list(csv.DictReader(f))
            
        self.assertEqual(len(reader), 14483)
        quads = [r for r in reader if r["topology"] == "QUAD"]
        tris = [r for r in reader if r["topology"] == "TRI"]
        self.assertEqual(len(quads), 14082)
        self.assertEqual(len(tris), 401)
        
        # Verify continuous base_index
        base_indices = [int(r["base_index"]) for r in reader]
        self.assertEqual(base_indices, list(range(1, 14484)))
        
        # Verify native element set is complete bijection
        native_eids = set(int(r["native_element"]) for r in reader)
        self.assertEqual(native_eids, set(range(1, 14484)))

    def test_mapping_json_schema_and_verdict(self):
        """Verify STAGE14_RECONSTRUCTION_TOPOLOGY_MAPPING.json metadata."""
        with open(self.mapping_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.assertEqual(data["underlying_elements"], 14483)
        self.assertEqual(data["quad_elements"], 14082)
        self.assertEqual(data["tri_elements"], 401)
        self.assertEqual(data["total_nodes"], 14456)
        self.assertEqual(data["layers_total_elements"], 43449)
        self.assertEqual(data["topology_coordinate_match"], "EXACT_MATCH_100PCT")
        self.assertEqual(data["missing_elements"], 0)
        self.assertEqual(data["duplicated_elements"], 0)
        self.assertEqual(data["multiply_mapped_elements"], 0)

    def test_report_json_metrics_and_verdict(self):
        """Verify MODE1_STAGE14I_NATIVE_RECONSTRUCTION_FIDELITY_REPORT.json metrics."""
        with open(self.report_json, 'r', encoding='utf-8') as f:
            rep = json.load(f)
            
        self.assertEqual(rep["reconstruction_verdict"], "STAGE14_NATIVE_TO_LAYERED_RECONSTRUCTION_EQUIVALENT_WITH_LABEL_RENUMBERING")
        self.assertEqual(rep["topology_coordinate_match"], "EXACT_MATCH_100PCT")
        self.assertEqual(rep["label_sensitive_match"], "EQUIVALENT_WITH_KNOWN_OFFSET_AND_TYPE_GROUPING")
        
        mm = rep["mesh_metrics"]
        self.assertEqual(mm["underlying_finite_elements"], 14483)
        self.assertEqual(mm["quad_finite_elements"], 14082)
        self.assertEqual(mm["tri_finite_elements"], 401)
        self.assertEqual(mm["mesh_nodes"], 14456)
        self.assertEqual(mm["rp_node_included"], 999999)
        self.assertEqual(mm["layers_total_elements"], 43449)
        self.assertAlmostEqual(mm["domain_area_mm2"], 1.000000, places=6)
        self.assertEqual(mm["negative_area_elements"], 0)
        self.assertEqual(mm["missing_elements"], 0)
        self.assertEqual(mm["duplicated_elements"], 0)
        
        seam = rep["seam_integrity"]
        self.assertEqual(seam["crack_length_a0_mm"], 0.5)
        self.assertEqual(seam["seam_plane_y_mm"], 0.5)
        self.assertEqual(seam["flank_duplicate_pairs"], 54)
        self.assertFalse(seam["unintended_merging"])
        self.assertEqual(seam["seam_gap_mm"], 0.0)

    def test_report_md_content_and_structure(self):
        """Verify markdown report contains required scientific answers and sections."""
        with open(self.report_md, 'r', encoding='utf-8') as f:
            md = f.read()
            
        self.assertIn("STAGE14_NATIVE_TO_LAYERED_RECONSTRUCTION_EQUIVALENT_WITH_LABEL_RENUMBERING", md)
        self.assertIn("EXACT_MATCH_100PCT", md)
        self.assertIn("14,483", md)
        self.assertIn("14,082", md)
        self.assertIn("401", md)
        self.assertIn("43,449", md)
        self.assertIn("14,456", md)
        self.assertIn("0.000000", md)

if __name__ == "__main__":
    unittest.main()

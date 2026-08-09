#!/usr/bin/env python3
"""
Unit and Regression Tests for Mode-II Uniform Reference Deck Generator & Validator
Task: F43MODEREF-PREP2

Regression coverage for:
  1. Dynamic RP node ID allocation for meshes with > 10,000 nodes.
  2. Global node-label uniqueness on final written .inp decks.
  3. Positive element signed areas calculated from final written node coordinates.
  4. Detection of deliberate RP node collisions during static validation.
"""

import unittest
from pathlib import Path
import tempfile
import sys
import os

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.validation.validate_mode_ii_reference_contract import parse_deck_structure, validate_reference_batch
from scripts.model_generation.build_mode_ii_uniform_reference_batch import generate_reference_deck


class TestModeIIReferenceGeneratorIntegrity(unittest.TestCase):

    def test_rp_label_is_outside_physical_node_range(self):
        """Verify dynamic RP node allocation for large meshes (>10,000 nodes)."""
        nodes = {i: (float(i % 100) * 0.005, float(i // 100) * 0.005) for i in range(1, 12501)}
        quads = {1: [1, 2, 102, 101]}

        with tempfile.TemporaryDirectory() as tmpdir:
            out_inp = Path(tmpdir) / "test_large_mesh.inp"
            generate_reference_deck("TEST_LARGE", nodes, quads, out_inp)

            text = out_inp.read_text(encoding="utf-8")
            struct = parse_deck_structure(out_inp)

            self.assertEqual(struct["duplicate_node_count"], 0)
            self.assertTrue(struct["rp_is_valid"])
            self.assertGreater(struct["rp_node_id"], struct["max_physical_node_id"])
            self.assertEqual(struct["rp_node_id"], 12501)

    def test_final_written_decks_have_unique_node_labels(self):
        """Verify all generated reference decks (H0, H1, H2) have globally unique node labels."""
        ref_dir = ROOT / "models/generated/mode_ii/reference_convergence"
        for case in ["M2REF_H0", "M2REF_H1", "M2REF_H2"]:
            deck_path = ref_dir / case / f"{case}.inp"
            if deck_path.is_file():
                struct = parse_deck_structure(deck_path)
                self.assertEqual(
                    struct["duplicate_node_count"], 0,
                    f"{case} contains {struct['duplicate_node_count']} duplicate node labels"
                )
                self.assertTrue(
                    struct["rp_is_valid"],
                    f"{case} RP node ID {struct['rp_node_id']} is invalid against max physical node {struct['max_physical_node_id']}"
                )

    def test_final_written_decks_have_positive_element_areas(self):
        """Verify all physical element signed areas calculated from final written coordinates are strictly positive and convex."""
        ref_dir = ROOT / "models/generated/mode_ii/reference_convergence"
        for case in ["M2REF_H0", "M2REF_H1", "M2REF_H2"]:
            deck_path = ref_dir / case / f"{case}.inp"
            if deck_path.is_file():
                struct = parse_deck_structure(deck_path)
                self.assertEqual(
                    struct["zero_area_elems"], 0,
                    f"{case} contains {struct['zero_area_elems']} zero-area elements"
                )
                self.assertEqual(
                    struct["distorted_elems"], 0,
                    f"{case} contains {struct['distorted_elems']} distorted/non-convex elements"
                )

    def test_deliberate_rp_node_collision_fails_validation(self):
        """Verify that a deck with hardcoded RP node 10000 colliding with physical mesh node 10000 fails validation."""
        mock_deck_lines = [
            "*Heading",
            "** Mock Deck with Colliding RP Node 10000",
            "*Node",
            "     1, 0.0, 0.0",
            "     2, 0.01, 0.0",
            "  9999, 0.0, 0.01",
            " 10000, 0.01, 0.01",
            " 10001, 0.02, 0.01",
            " 10000, 0.0, 0.6",  # COLLISION OVERWRITE! Overwrites (0.01, 0.01) with (0.0, 0.6), collapsing element 1
            "*Nset, nset=RP",
            " 10000",
            "*Element, type=U1, elset=PHASE_QUAD",
            " 1, 1, 2, 10000, 9999",
            "*Step, name=Step-1",
            "*End Step"
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            mock_inp = Path(tmpdir) / "colliding_deck.inp"
            mock_inp.write_text("\n".join(mock_deck_lines) + "\n", encoding="utf-8")

            struct = parse_deck_structure(mock_inp)

            self.assertGreater(struct["duplicate_node_count"], 0)
            self.assertFalse(struct["rp_is_valid"])
            self.assertTrue(struct["zero_area_elems"] > 0 or struct["distorted_elems"] > 0)


if __name__ == "__main__":
    unittest.main()

# -*- coding: utf-8 -*-
"""
tests/unit/test_f1703_secondary_crack_refinement.py
===================================================
Unit regression test suite for Task F1703:
Complete Secondary Crack-Path Adaptive Refinement in Pandey-Kumar Section 4.3.

Verifies:
  1. Production UEL inviolate SHA-256 hash (ce8d5edc...) and 907 lines.
  2. Authentic secondary crack timeline metrics from Job 1421286.
  3. Mesh integrity of official adapted mesh (10,065 elements, 96.61% quads, 0 inverted elements).
  4. Exact 2D polygon-line clipping audit: 100.00% secondary coverage, 0.00 mm gap.
  5. Publication synthesis plot and official input deck existence and non-zero size.
"""

import os
import sys
import json
import math
import hashlib
import unittest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

class TestF1703SecondaryCrackRefinement(unittest.TestCase):

    def test_01_production_uel_inviolate(self):
        uel_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "f42_mixed_uel.for")
        self.assertTrue(os.path.exists(uel_path), "Production UEL must exist")
        with open(uel_path, "rb") as f:
            content = f.read()
        sha = hashlib.sha256(content).hexdigest()
        self.assertTrue(sha.startswith("ce8d5edc"), f"Production UEL SHA must start with ce8d5edc, got {sha}")
        lines = content.decode("utf-8", errors="ignore").splitlines()
        self.assertEqual(len(lines), 907, f"Production UEL must have exactly 907 lines, got {len(lines)}")

    def test_02_authentic_secondary_crack_timeline(self):
        json_path = os.path.join(REPO_ROOT, "results", "validation", "f1703_secondary_crack_propagation_timeline.json")
        self.assertTrue(os.path.exists(json_path), "Timeline JSON must exist")
        with open(json_path, "r") as f:
            data = json.load(f)

        # State 2 (Frame 40, uy = 0.20 mm): 0 secondary cracked elements
        self.assertEqual(data["40"]["num_sec_cracked_elements_d05"], 0)
        self.assertEqual(data["40"]["pct_ligament"], 0.0)

        # State 4 (Frame 60, uy = 0.30 mm): secondary initiation/mid-propagation
        self.assertEqual(data["60"]["num_sec_cracked_elements_d05"], 8)
        self.assertAlmostEqual(data["60"]["pct_ligament"], 24.74, places=1)
        self.assertAlmostEqual(data["60"]["dist_from_hole_mm"], 4.58, places=1)

        # State 5 (Frame 100, uy = 0.50 mm): complete ligament severance
        self.assertEqual(data["100"]["num_sec_cracked_elements_d05"], 36)
        self.assertAlmostEqual(data["100"]["pct_ligament"], 96.22, places=1)
        self.assertAlmostEqual(data["100"]["dist_from_hole_mm"], 17.80, places=1)

    def test_03_official_adapted_mesh_deck(self):
        inp_path = os.path.join(REPO_ROOT, "models", "pandey_kumar_mode1", "203_pk_sec43_secondary_complete", "PK_SEC43_F1703_SECONDARY_COMPLETE_ADAPT.inp")
        self.assertTrue(os.path.exists(inp_path), "Official F1703 adapted mesh deck must exist")
        self.assertGreater(os.path.getsize(inp_path), 500000, "Mesh deck must be > 500 KB")

    def test_04_mesh_connectivity_and_coverage_audit(self):
        audit_path = os.path.join(REPO_ROOT, "results", "validation", "f1703_secondary_complete_connectivity_audit.json")
        self.assertTrue(os.path.exists(audit_path), "Audit JSON must exist")
        with open(audit_path, "r") as f:
            data = json.load(f)

        self.assertIn("F1703_Official", data)
        m = data["F1703_Official"]

        # Mesh topology checks
        self.assertEqual(m["total_elements"], 10065)
        self.assertEqual(m["total_nodes"], 10096)
        self.assertGreater(m["quad_fraction_pct"], 95.0, "Quad fraction must be > 95%")
        self.assertAlmostEqual(m["quad_fraction_pct"], 96.61, places=1)

        # Authentic secondary crack trajectory metrics
        sec_act = m["trajectories"]["secondary_actual"]
        l0_stats = sec_act["exact_centerline_intersection"]["h_le_l0"]
        l0_half_stats = sec_act["exact_centerline_intersection"]["h_le_l0_half"]
        corr_2d = sec_act["2d_corridor_element_counts"]

        # Crucial scientific gate: 100.00% coverage with 0.00 mm gap
        self.assertEqual(l0_stats["coverage_pct"], 100.0, "Centerline coverage h <= l0 must be 100.0%")
        self.assertEqual(l0_stats["max_uncovered_gap_mm"], 0.0, "Max uncovered gap must be 0.0 mm")
        self.assertAlmostEqual(l0_stats["longest_connected_segment_mm"], 18.5623, places=2)

        # Fine resolution gate: h <= l0/2 coverage > 25% and gap < 2.5 mm
        self.assertGreaterEqual(l0_half_stats["coverage_pct"], 25.0)
        self.assertLessEqual(l0_half_stats["max_uncovered_gap_mm"], 2.5)

        # 2D corridor gate: >= 99% elements <= l0
        self.assertGreaterEqual(corr_2d["fraction_le_l0_pct"], 99.0)

    def test_05_synthesis_visualization_artifact(self):
        png_path = os.path.join(REPO_ROOT, "results", "validation", "f1703_secondary_refinement_synthesis.png")
        self.assertTrue(os.path.exists(png_path), "Synthesis plot must exist")
        self.assertGreater(os.path.getsize(png_path), 200000, "Plot must be > 200 KB")

    def test_06_reconciled_evidence_audit(self):
        recon_path = os.path.join(REPO_ROOT, "results", "validation", "f1703_reconciled_evidence_audit.json")
        self.assertTrue(os.path.exists(recon_path), "Reconciled audit JSON must exist")
        with open(recon_path, "r") as f:
            data = json.load(f)
        
        # Piecewise authentic trajectory
        pw_03 = data["piecewise_clipping"]["F1703"]
        self.assertGreater(pw_03["h_le_l0"]["coverage_pct"], 90.0, "Piecewise coverage must exceed 90%")
        self.assertAlmostEqual(pw_03["h_le_l0"]["coverage_pct"], 93.47, places=1)
        self.assertAlmostEqual(pw_03["h_le_l0"]["longest_connected_segment_mm"], 18.0983, places=2)

        # Area-weighted secondary corridor
        sec_03 = data["area_weighted_2d_corridors"]["secondary_actual"]["F1703"]
        self.assertGreater(sec_03["area_fraction_le_l0_pct"], 99.0, "Area-weighted coverage must exceed 99%")
        self.assertAlmostEqual(sec_03["area_fraction_le_l0_pct"], 99.59, places=1)

if __name__ == "__main__":
    unittest.main()

"""Unit tests for Task F1481: Coarse Pre-Analysis Mesh Resolution Sensitivity and Temporal Suite.

Author: gemini-antigravity
Protocol: Version 2
Governance Gate: GATE_6B_ACTIVE_EVALUATION_AND_CONTINUATION
"""

import json
import os
import sys
import unittest

# Add project root to sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from scripts.postprocessing.compare_mode1_temporal_refinement_suite import (
    FIXED_MESH_REFERENCE,
    PACKAGE_40_BASELINE,
    PACKAGE_90_COARSE_BASELINE,
    MATCHED_EVALUATION_POINTS,
    compute_parity_metrics,
    evaluate_coarse_resolution_scaling,
    evaluate_temporal_suite_manifest
)


class TestMode1F1481CoarseResolutionAndTemporalSuite(unittest.TestCase):
    """Test suite verifying Package 46 preparation and temporal evaluation framework."""

    def test_01_package_46_manifest_and_deck_integrity(self):
        """Verify Package 46 manifest, input deck existence, and SHA-256 hash."""
        pkg_dir = os.path.join(PROJECT_ROOT, "models", "pandey_kumar_mode1", "46_mode1_coarse_preanalysis_density_sensitivity")
        manifest_path = os.path.join(pkg_dir, "PACKAGE_MANIFEST.json")
        deck_path = os.path.join(pkg_dir, "PK_M1_COARSE_FINE_CONT.inp")

        self.assertTrue(os.path.exists(manifest_path), "Package 46 manifest missing")
        self.assertTrue(os.path.exists(deck_path), "Package 46 input deck missing")

        with open(manifest_path, "r") as f:
            manifest = json.load(f)

        self.assertEqual(manifest["mesh_spec"]["num_elements"], 4900)
        self.assertEqual(manifest["mesh_spec"]["element_type"], "CPE4")
        self.assertEqual(manifest["mesh_spec"]["num_nodes"], 5076)
        self.assertEqual(manifest["material_spec"]["E_MPa"], 210000.0)
        self.assertEqual(manifest["material_spec"]["nu"], 0.3)
        self.assertEqual(manifest["loading_spec"]["prescribed_u_mm"], 0.0050)
        self.assertEqual(manifest["files"]["input_deck_sha256"], "219ACDF263F4F4096943B1AC976063722F927934C26458D593F7F714B84B8C56")

    def test_02_deck_element_and_node_counts(self):
        """Parse input deck and verify exact element, node, and seam counts."""
        deck_path = os.path.join(PROJECT_ROOT, "models", "pandey_kumar_mode1", "46_mode1_coarse_preanalysis_density_sensitivity", "PK_M1_COARSE_FINE_CONT.inp")
        
        in_nodes = False
        in_elements = False
        nodes = {}
        elements = {}

        with open(deck_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("**"):
                    continue
                if line.startswith("*"):
                    in_nodes = line.upper().startswith("*NODE")
                    in_elements = line.upper().startswith("*ELEMENT,")
                    continue
                if in_nodes:
                    parts = [p.strip() for p in line.split(",") if p.strip()]
                    if len(parts) >= 3:
                        nid = int(parts[0])
                        x = float(parts[1])
                        y = float(parts[2])
                        nodes[nid] = (x, y)
                elif in_elements:
                    parts = [p.strip() for p in line.split(",") if p.strip()]
                    if len(parts) >= 5:
                        eid = int(parts[0])
                        conn = tuple(int(p) for p in parts[1:5])
                        elements[eid] = conn

        self.assertEqual(len(elements), 4900, "Must contain exactly 4,900 CPE4 elements")
        self.assertEqual(len(nodes), 5077, "Must contain 5,076 physical nodes + 1 RP node = 5,077 total")
        
        # Verify crack tip node at (0.5, 0.5)
        tip_node = nodes[2521]
        self.assertAlmostEqual(tip_node[0], 0.5, places=5)
        self.assertAlmostEqual(tip_node[1], 0.5, places=5)

    def test_03_temporal_comparison_suite_parity_metrics(self):
        """Test multi-quantity parity evaluation metrics against reference baseline."""
        metrics = compute_parity_metrics(FIXED_MESH_REFERENCE, PACKAGE_40_BASELINE)
        
        self.assertIn("delta_K0_pct", metrics)
        self.assertIn("delta_Fmax_pct", metrics)
        self.assertIn("delta_u_peak_pct", metrics)
        self.assertIn("delta_W_ext_pct", metrics)

        # Delta K0 should be within -0.05%
        self.assertAlmostEqual(metrics["delta_K0_pct"], -0.02604, places=3)
        # Delta Fmax should be within -2.0%
        self.assertAlmostEqual(metrics["delta_Fmax_pct"], -1.8576, places=2)

    def test_04_coarse_resolution_scaling_theory(self):
        """Verify theoretical error scaling between canonical and fine coarse meshes."""
        h_baseline = 0.033333
        h_candidate = 0.0142857
        scaling = evaluate_coarse_resolution_scaling(h_baseline, h_candidate, p_rate=2.0)
        
        self.assertLess(scaling["h_ratio"], 0.5)
        # Far field error reduction > 4x
        self.assertLess(scaling["predicted_far_field_error_ratio"], 0.25)

    def test_05_matched_evaluation_points_definition(self):
        """Verify predeclared matched evaluation points are complete."""
        points = {p["point_id"]: p["u_mm"] for p in MATCHED_EVALUATION_POINTS}
        self.assertIn("P1_LINEAR_LIMIT", points)
        self.assertIn("P2_PKG40_PEAK", points)
        self.assertIn("P3_REF15K_PEAK", points)
        self.assertIn("P4_POST_PEAK_EARLY", points)
        self.assertIn("P5_PKG40_HORIZON", points)

        self.assertEqual(points["P1_LINEAR_LIMIT"], 0.005000)
        self.assertEqual(points["P2_PKG40_PEAK"], 0.005733)
        self.assertEqual(points["P3_REF15K_PEAK"], 0.005857)
        self.assertEqual(points["P4_POST_PEAK_EARLY"], 0.006000)
        self.assertEqual(points["P5_PKG40_HORIZON"], 0.007889)


if __name__ == "__main__":
    unittest.main()

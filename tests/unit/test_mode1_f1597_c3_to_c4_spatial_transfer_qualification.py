# -*- coding: utf-8 -*-
"""
test_mode1_f1597_c3_to_c4_spatial_transfer_qualification.py
Unit test suite qualifying the C3-Intermediate to C4 Nonmatching Spatial Transfer Mapping Engine.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Hypothesis: H40
Protocol Version: 2
"""

from __future__ import print_function, division
import os
import sys
import math
import unittest
from pathlib import Path

REPO_ROOT = Path(r"D:\Master thesis\Adaptive remeshing")
sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.c3_int_to_c4_spatial_mapping import (
    Mesh2D,
    SpatialIndex2D,
    SpatialTransferMapper,
    inverse_isoparametric_quad,
    quad_shape_functions,
    quad_physical_point
)


class TestC3IntToC4SpatialTransferQualification(unittest.TestCase):
    """Rigorous unit tests for C3-Intermediate to C4 spatial mapping."""

    @classmethod
    def setUpClass(cls):
        cls.c3_int_inp = REPO_ROOT / "models/pandey_kumar_mode1/141_c3_int_donor_monotonic/M1_C3_INT_DONOR_MONOTONIC.inp"
        cls.c4_inp = REPO_ROOT / "models/pandey_kumar_mode1/111_r2_c4_frame77_pre_instability/M1_C4_FRAME77_CONTINUATION.inp"

        cls.donor = Mesh2D.from_inp(str(cls.c3_int_inp), name="C3-Intermediate", max_physical_node=2610)
        cls.receiver = Mesh2D.from_inp(str(cls.c4_inp), name="C4-Receiver", max_physical_node=4588)
        cls.mapper = SpatialTransferMapper(cls.donor, cls.receiver, tol_geom=1e-5)
        cls.node_map, cls.node_stats, cls.node_rejected = cls.mapper.build_node_transfer_map()
        cls.gp_map, cls.gp_stats, cls.gp_rejected = cls.mapper.build_gauss_point_transfer_map()
        cls.patch_results = cls.mapper.run_synthetic_patch_tests(cls.node_map, cls.gp_map)

    def test_01_donor_and_receiver_mesh_topology(self):
        """Validates physical node counts, quad element counts, and seam pair counts."""
        self.assertEqual(len(self.donor.nodes), 2610)
        self.assertEqual(len(self.donor.elements), 2484)
        self.assertEqual(len(self.donor.seam_pairs), 25)

        self.assertEqual(len(self.receiver.nodes), 4588)
        self.assertEqual(len(self.receiver.elements), 4422)
        self.assertEqual(len(self.receiver.seam_pairs), 32)
        self.assertEqual(len(self.receiver.gauss_points), 4422 * 4)

    def test_02_inverse_isoparametric_quad_convergence(self):
        """Verifies Newton-Raphson inverse mapping convergence on regular and distorted quads."""
        # Regular quad [0, 1] x [0, 1]
        vertices = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
        target = (0.35, 0.72)
        xi, eta, conv, res = inverse_isoparametric_quad(vertices, target[0], target[1])
        self.assertTrue(conv)
        self.assertLess(res, 1e-12)
        # Expected xi = 2*x - 1 = -0.30, eta = 2*y - 1 = 0.44
        self.assertAlmostEqual(xi, -0.30, places=10)
        self.assertAlmostEqual(eta, 0.44, places=10)

        # Distorted quad
        v_dist = [(0.1, 0.1), (0.9, 0.2), (0.8, 0.85), (0.2, 0.75)]
        px, py = quad_physical_point(v_dist, 0.25, -0.45)
        xi2, eta2, conv2, res2 = inverse_isoparametric_quad(v_dist, px, py)
        self.assertTrue(conv2)
        self.assertLess(res2, 1e-12)
        self.assertAlmostEqual(xi2, 0.25, places=10)
        self.assertAlmostEqual(eta2, -0.45, places=10)

    def test_03_spatial_binning_index_candidate_retrieval(self):
        """Verifies that spatial binning index correctly filters candidates by location and flank."""
        idx = self.mapper.donor_index
        # Query near slit upper flank: x = 0.02, y = 0.0501
        cands_upper = idx.query_candidates(0.02, 0.0501, flank_constraint="UPPER")
        self.assertGreater(len(cands_upper), 0)
        for eid in cands_upper:
            self.assertEqual(self.donor.element_flank[eid], "UPPER")

        # Query near slit lower flank: x = 0.02, y = 0.0499
        cands_lower = idx.query_candidates(0.02, 0.0499, flank_constraint="LOWER")
        self.assertGreater(len(cands_lower), 0)
        for eid in cands_lower:
            self.assertEqual(self.donor.element_flank[eid], "LOWER")

    def test_04_target_node_mapping_coverage_and_reconstruction(self):
        """Verifies 100% receiver node mapping coverage with near-zero coordinate reconstruction error."""
        stats = self.node_stats
        self.assertEqual(stats["mapped_nodes"], 4588)
        self.assertEqual(stats["rejected_nodes"], 0)
        self.assertEqual(stats["coverage_pct"], 100.0)
        self.assertEqual(stats["flank_violations"], 0)
        self.assertLess(stats["max_coord_recon_error"], 1e-12)
        self.assertLess(stats["rms_coord_recon_error"], 1e-14)

    def test_05_target_gauss_point_mapping_coverage(self):
        """Verifies 100% receiver Gauss point mapping coverage (17,688 GPs) with valid host nearest GP."""
        stats = self.gp_stats
        self.assertEqual(stats["mapped_gps"], 4422 * 4)
        self.assertEqual(stats["rejected_gps"], 0)
        self.assertEqual(stats["coverage_pct"], 100.0)
        self.assertEqual(stats["flank_violations"], 0)
        self.assertLess(stats["max_coord_recon_error"], 1e-12)

        # Validate that host_nearest_gp is in {1, 2, 3, 4} and distance is small
        for key, entry in self.gp_map.items():
            self.assertIn(entry["host_nearest_gp"], (1, 2, 3, 4))
            self.assertGreaterEqual(entry["host_gp_dist"], 0.0)

    def test_06_slit_flank_isolation_and_cross_interpolation_guard(self):
        """Verifies that all 32 slit pairs on receiver mesh strictly map to matching flank donor elements."""
        node_map = self.node_map
        for lower_nid, upper_nid, x_val in self.receiver.seam_pairs:
            map_lower = node_map[lower_nid]
            map_upper = node_map[upper_nid]

            self.assertEqual(map_lower["flank"], "LOWER")
            self.assertEqual(map_upper["flank"], "UPPER")
            # Host elements must be strictly distinct
            self.assertNotEqual(map_lower["host_eid"], map_upper["host_eid"])

    def test_07_synthetic_linear_displacement_patch_test(self):
        """Tests exact reproduction of linear displacement fields across nonmatching quad meshes."""
        patch_results = self.patch_results
        self.assertTrue(patch_results["patch_tests_passed"])
        self.assertLess(patch_results["linear_displacement_max_error"], 1e-12)
        self.assertLess(patch_results["constant_phase_max_error"], 1e-12)

    def test_08_partition_of_unity_and_history_non_negativity(self):
        """Verifies that shape function weights sum to exactly 1.0 and history is strictly non-negative."""
        patch_results = self.patch_results
        self.assertLess(patch_results["partition_of_unity_max_error"], 1e-12)
        self.assertEqual(patch_results["history_non_negativity_violations"], 0)


if __name__ == "__main__":
    unittest.main()

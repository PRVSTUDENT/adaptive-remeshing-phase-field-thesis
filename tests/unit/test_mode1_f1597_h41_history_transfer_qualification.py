# -*- coding: utf-8 -*-
"""
test_mode1_f1597_h41_history_transfer_qualification.py
Unit test suite qualifying the H41 History-Preserving Transfer Operators.
Task: F1597-CORRECT-PACKAGE72-STATE-TRANSFER
Hypothesis: H41
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
    SpatialTransferMapper
)


class TestH41HistoryTransferQualification(unittest.TestCase):
    """Rigorous unit tests for H41 history-preserving transfer operators."""

    @classmethod
    def setUpClass(cls):
        c3_int_inp = REPO_ROOT / "models/pandey_kumar_mode1/141_c3_int_donor_monotonic/M1_C3_INT_DONOR_MONOTONIC.inp"
        c4_inp = REPO_ROOT / "models/pandey_kumar_mode1/111_r2_c4_frame77_pre_instability/M1_C4_FRAME77_CONTINUATION.inp"

        cls.donor = Mesh2D.from_inp(str(c3_int_inp), name="C3-Intermediate", max_physical_node=2610)
        cls.receiver = Mesh2D.from_inp(str(c4_inp), name="C4-Receiver", max_physical_node=4588)
        cls.mapper = SpatialTransferMapper(cls.donor, cls.receiver, tol_geom=1e-5)
        cls.gp_map, cls.gp_stats, _ = cls.mapper.build_gauss_point_transfer_map()

    def test_01_constant_history_preservation(self):
        """Verifies exact preservation of constant history fields (max error < 1e-12)."""
        b = self.mapper.evaluate_history_field_benchmark(
            lambda x, y, flank: 25.0, self.gp_map, field_name="constant"
        )
        self.assertLess(b["host_nearest_gp"]["max_error"], 1e-12)
        self.assertLess(b["bilinear_gp"]["max_error"], 1e-12)
        self.assertEqual(b["host_nearest_gp"]["non_negativity_violations"], 0)

    def test_02_smooth_quadratic_history_comparison(self):
        """Verifies smooth field transfer and confirms bilinear GP higher-order convergence."""
        b = self.mapper.evaluate_history_field_benchmark(
            lambda x, y, flank: 10.0 + 200.0 * x * x + 100.0 * y * y,
            self.gp_map, field_name="smooth"
        )
        self.assertLess(b["host_nearest_gp"]["max_error"], 0.1)
        self.assertLess(b["bilinear_gp"]["max_error"], 0.01)
        # Bilinear GP has lower RMS error on smooth quadratic field
        self.assertLess(b["bilinear_gp"]["rms_error"], b["host_nearest_gp"]["rms_error"])

    def test_03_sharp_crack_tip_gradient_bounding(self):
        """Verifies that Host-Nearest GP bounds peak overshoots on sharp crack-tip gradient."""
        l0 = 0.0075
        tip_x, tip_y = 0.040, 0.050

        def field_crack_tip(x, y, flank):
            r = math.sqrt((x - tip_x) ** 2 + (y - tip_y) ** 2)
            h_sing = 150.0 * math.exp(-r / l0)
            h_wake = 120.0 if (x <= tip_x and abs(y - tip_y) <= 0.0015) else 0.0
            return max(0.0, h_sing + h_wake)

        b = self.mapper.evaluate_history_field_benchmark(field_crack_tip, self.gp_map, field_name="crack_tip")
        # HN-GP should have much lower maximum error than Bilinear-GP due to absence of extrapolation overshoot
        self.assertLess(b["host_nearest_gp"]["max_error"], b["bilinear_gp"]["max_error"])
        self.assertEqual(b["host_nearest_gp"]["non_negativity_violations"], 0)

    def test_04_discontinuous_slit_flank_isolation(self):
        """Verifies zero history leakage across discontinuous upper/lower crack flanks."""
        tip_x, l0 = 0.040, 0.0075

        def field_slit(x, y, flank):
            if x <= tip_x:
                return 85.0 if flank == "UPPER" else 25.0
            else:
                return 10.0 + 40.0 * math.exp(-(x - tip_x) / l0)

        donor_gp = {k: max(0.0, field_slit(pt[0], pt[1], pt[2])) for k, pt in self.donor.gauss_points.items()}
        target_hn = self.mapper.transfer_history_host_nearest(donor_gp, self.gp_map)

        # Check all target GPs on upper flank (x <= 0.040)
        for (teid, tgp), entry in self.gp_map.items():
            tx, ty, tflank = self.receiver.gauss_points[(teid, tgp)]
            if tx <= tip_x:
                val = target_hn[(teid, tgp)]
                if tflank == "UPPER":
                    self.assertGreaterEqual(val, 80.0)
                elif tflank == "LOWER":
                    self.assertLessEqual(val, 30.0)

    def test_05_two_stage_irreversibility_monotonicity(self):
        """Verifies that across two successive states H2 >= H1, transferred history is 100% monotonic."""
        l0 = 0.0075
        tip_x, tip_y = 0.040, 0.050

        def f1(x, y, flank):
            r = math.sqrt((x - tip_x) ** 2 + (y - tip_y) ** 2)
            return 100.0 * math.exp(-r / l0)

        def f2(x, y, flank):
            r1 = math.sqrt((x - tip_x) ** 2 + (y - tip_y) ** 2)
            r2 = math.sqrt((x - (tip_x + 0.002)) ** 2 + (y - tip_y) ** 2)
            return max(100.0 * math.exp(-r1 / l0), 120.0 * math.exp(-r2 / l0))

        d_h1 = {k: max(0.0, f1(pt[0], pt[1], pt[2])) for k, pt in self.donor.gauss_points.items()}
        d_h2 = {k: max(0.0, f2(pt[0], pt[1], pt[2])) for k, pt in self.donor.gauss_points.items()}

        t_h1 = self.mapper.transfer_history_host_nearest(d_h1, self.gp_map)
        t_h2 = self.mapper.transfer_history_host_nearest(d_h2, self.gp_map)

        violations = [k for k in t_h1 if t_h2[k] < t_h1[k] - 1e-12]
        self.assertEqual(len(violations), 0)

    def test_06_non_negativity_invariance(self):
        """Verifies strict H >= 0 across all 17,688 receiver Gauss points."""
        d_h = {k: 50.0 for k in self.donor.gauss_points}
        t_h = self.mapper.transfer_history_host_nearest(d_h, self.gp_map)
        self.assertEqual(len(t_h), 17688)
        for val in t_h.values():
            self.assertGreaterEqual(val, 0.0)


if __name__ == "__main__":
    unittest.main()

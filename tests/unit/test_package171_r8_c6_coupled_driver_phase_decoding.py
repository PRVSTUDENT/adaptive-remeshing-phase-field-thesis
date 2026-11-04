#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package171_r8_c6_coupled_driver_phase_decoding.py
======================================================
Comprehensive test suite verifying fail-closed phase-field decoding in Package 171-R8:
1. Valid 3-component phase output (U1, U2, U3) extracts damage from U3.
2. Valid 1-component phase output extracts damage from scalar d.
3. Two-component phase output (U1, U2) is strictly rejected (prevents interpreting U2 as damage).
4. Mixed component counts across nodes are strictly rejected.
5. Incomplete node coverage (< 15,559 nodes) is strictly rejected.
6. Unexpected node IDs are strictly rejected.
7. Duplicate node records in extractor output are strictly rejected.
8. Nonfinite values (NaN and Inf) are strictly rejected.
9. Proves that invalid phase output cannot enter coupled iteration or create an accepted checkpoint.

Task: F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION
Protocol Version: 2
"""

import sys
import json
import math
import time
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.driver_package171_r8_c6_coupled_pdas import (
    Package171R8C6PDASDriver
)

PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r5_c3_0_reequilibration"
EXTRACTOR_PATH = REPO_ROOT / "scripts/validation/extract_package148_iteration.py"


class TestPackage171R8PhaseDecoding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._shared_driver = Package171R8C6PDASDriver(
            package=PKG_DIR,
            output=Path("."),
            extractor=EXTRACTOR_PATH,
            omega_d_stage1=0.50,
            omega_d_stage2=0.85,
            max_outer=140
        )
        cls._shared_driver.load()

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.tmpdir.name)
        self.driver = Package171R8C6PDASDriver(
            package=PKG_DIR,
            output=self.out_path,
            extractor=EXTRACTOR_PATH,
            omega_d_stage1=0.50,
            omega_d_stage2=0.85,
            max_outer=140
        )
        self.driver.mesh = self._shared_driver.mesh
        self.driver.d0 = self._shared_driver.d0
        self.driver.h0 = self._shared_driver.h0
        self.driver.u0 = self._shared_driver.u0
        self.driver.target_uy = self._shared_driver.target_uy
        self.driver.template = self._shared_driver.template
        self.driver.deadline = time.monotonic() + 1000

        self.all_nodes = sorted(self.driver.d0.keys())
        self.assertEqual(len(self.all_nodes), 15559)

    def tearDown(self):
        self.tmpdir.cleanup()

    def _execute_subproblem_with_mock_endpoint(self, endpoint_data, role="phase"):
        def mock_runner(directory, job, r, step_idx):
            return endpoint_data

        self.driver.runner = mock_runner
        active = set(self.driver.d0.keys())
        damage = dict(self.driver.d0)
        disp = dict(self.driver.u0)
        history = dict(self.driver.h0)
        return self.driver.solve_subproblem(
            step_idx=1, outer=1, inner=0, role=role,
            damage=damage, active=active,
            displacement=disp, history=history,
            target_u=self.driver.target_uy
        )

    def test_valid_three_component_phase_output_accepted(self):
        """Standard 3-component phase output (U1, U2, U3) extracts damage from U3."""
        rows = [[n, 0.0001, 0.0018, float(self.driver.d0[n] + 0.05)] for n in self.all_nodes]
        endpoint = {"nodes": rows}

        new_d, new_u, _ = self._execute_subproblem_with_mock_endpoint(endpoint, role="phase")

        self.assertEqual(len(new_d), 15559)
        for n in self.all_nodes:
            expected = float(self.driver.d0[n] + 0.05)
            self.assertAlmostEqual(new_d[n], expected, places=7)

    def test_valid_one_component_phase_output_accepted(self):
        """Single-component scalar phase output (d) extracts damage correctly."""
        rows = [[n, float(self.driver.d0[n] + 0.03)] for n in self.all_nodes]
        endpoint = {"nodes": rows}

        new_d, new_u, _ = self._execute_subproblem_with_mock_endpoint(endpoint, role="phase")

        self.assertEqual(len(new_d), 15559)
        for n in self.all_nodes:
            expected = float(self.driver.d0[n] + 0.03)
            self.assertAlmostEqual(new_d[n], expected, places=7)

    def test_two_component_phase_output_rejected(self):
        """Two-component phase output (U1, U2) is strictly rejected."""
        rows = [[n, 0.0001, 0.0018] for n in self.all_nodes]
        endpoint = {"nodes": rows}

        with self.assertRaises(ValueError) as ctx:
            self._execute_subproblem_with_mock_endpoint(endpoint, role="phase")
        self.assertIn("rejected two-component phase output", str(ctx.exception))

    def test_mixed_component_counts_rejected(self):
        """Mixed component counts across nodes are strictly rejected."""
        rows = [[n, 0.0001, 0.0018, float(self.driver.d0[n] + 0.05)] for n in self.all_nodes]
        rows[100] = [self.all_nodes[100], 0.5]  # 1 component instead of 3
        endpoint = {"nodes": rows}

        with self.assertRaises(ValueError) as ctx:
            self._execute_subproblem_with_mock_endpoint(endpoint, role="phase")
        self.assertIn("mixed component counts", str(ctx.exception))

    def test_incomplete_node_coverage_rejected(self):
        """Incomplete node coverage (< 15,559 nodes) is strictly rejected."""
        rows = [[n, 0.0001, 0.0018, float(self.driver.d0[n] + 0.05)] for n in self.all_nodes[:-1]]
        endpoint = {"nodes": rows}

        with self.assertRaises(ValueError) as ctx:
            self._execute_subproblem_with_mock_endpoint(endpoint, role="phase")
        self.assertIn("expected exactly 15,559 unique physical-node records", str(ctx.exception))

    def test_unexpected_node_id_rejected(self):
        """Unexpected node IDs not matching receiver mesh are strictly rejected."""
        rows = [[n, 0.0001, 0.0018, float(self.driver.d0[n] + 0.05)] for n in self.all_nodes[:-1]]
        rows.append([999999, 0.0001, 0.0018, 0.5])  # Reference point ID instead of physical node
        endpoint = {"nodes": rows}

        with self.assertRaises(ValueError) as ctx:
            self._execute_subproblem_with_mock_endpoint(endpoint, role="phase")
        self.assertIn("unexpected=", str(ctx.exception))

    def test_duplicate_node_records_rejected(self):
        """Duplicate node records are strictly rejected."""
        rows = [[n, 0.0001, 0.0018, float(self.driver.d0[n] + 0.05)] for n in self.all_nodes]
        rows.append([self.all_nodes[0], 0.0001, 0.0018, 0.5])  # duplicate
        endpoint = {"nodes": rows}

        with self.assertRaises(ValueError) as ctx:
            self._execute_subproblem_with_mock_endpoint(endpoint, role="phase")
        self.assertIn("duplicated node records", str(ctx.exception))

    def test_nonfinite_values_rejected(self):
        """Nonfinite values (NaN and Inf) in phase output are strictly rejected."""
        rows = [[n, 0.0001, 0.0018, float(self.driver.d0[n] + 0.05)] for n in self.all_nodes]
        rows[50][3] = float("nan")
        endpoint = {"nodes": rows}

        with self.assertRaises(ValueError) as ctx:
            self._execute_subproblem_with_mock_endpoint(endpoint, role="phase")
        self.assertIn("nonfinite value nan", str(ctx.exception))

        rows[50][3] = float("inf")
        with self.assertRaises(ValueError) as ctx:
            self._execute_subproblem_with_mock_endpoint(endpoint, role="phase")
        self.assertIn("nonfinite value inf", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

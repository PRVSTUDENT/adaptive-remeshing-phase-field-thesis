#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package171_r6_c6_coupled_driver_phase_decoding.py
======================================================
Comprehensive test suite verifying fail-closed phase-field decoding in Package 171-R6:
1. Valid 3-component phase output (U1, U2, U3) extracts damage from U3.
2. Valid 1-component phase output extracts damage from scalar d.
3. Two-component phase output (U1, U2) is strictly rejected (prevents interpreting U2 as damage).
4. Mixed component counts across nodes are strictly rejected.
5. Incomplete node coverage (< 15,559 nodes) is strictly rejected.
6. Unexpected node IDs are strictly rejected.
7. Duplicate node records in extractor output are strictly rejected.
8. Nonfinite values (NaN and Inf) are strictly rejected.
9. Proves that invalid phase output cannot enter coupled iteration or create an accepted checkpoint.

Task: F1601-MODE1-C6-R2-DIAGNOSIS-PREPARATION -> R6 Candidate Qualification
Protocol Version: 2
"""

import sys
import json
import math
import time
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.driver_package171_r6_c6_coupled_pdas import (
    Package171R6C6PDASDriver
)

PKG_DIR = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r5_c3_0_reequilibration"
EXTRACTOR_PATH = REPO_ROOT / "scripts/validation/extract_package148_iteration.py"


class TestPackage171R6PhaseDecoding(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.tmpdir.name)
        self.driver = Package171R6C6PDASDriver(
            package=PKG_DIR,
            output=self.out_path,
            extractor=EXTRACTOR_PATH,
            damping_omega_d=0.5,
            max_outer=100
        )
        self.driver.load()
        self.driver.deadline = time.monotonic() + 3600

    def tearDown(self):
        self.tmpdir.cleanup()

    def _make_mock_runner(self, nodes_data):
        """Creates a mock runner returning endpoint with specified node output."""
        def mock_runner(sub_dir, job, role, step_idx):
            return {
                "schema": 1,
                "step_name": f"C3_0_Step{step_idx}_{role}",
                "rf2_kN": 0.17992419,
                "elastic_kNmm": 0.00016825,
                "fracture_kNmm": 5.814e-05,
                "nodes": nodes_data
            }
        return mock_runner

    def test_valid_three_component_phase_decoding(self):
        """Verify 3-component output (U1, U2, U3) decodes damage strictly from U3 (index 2)."""
        expected_d = 0.42
        nodes_data = [[n, 0.001, 0.002, expected_d] for n in range(1, 15560)]
        self.driver.runner = self._make_mock_runner(nodes_data)

        damage_in = dict(self.driver.d0)
        active = set(damage_in)
        displacement = dict(self.driver.u0)
        history = dict(self.driver.h0)

        new_d, new_u, endpoint = self.driver.solve_subproblem(
            step_idx=1, outer=1, inner=0, role="phase",
            damage=damage_in, active=active,
            displacement=displacement, history=history,
            target_u=0.00187
        )

        self.assertEqual(len(new_d), 15559)
        for n in range(1, 15560):
            # Must be max(d0, expected_d)
            self.assertEqual(new_d[n], max(self.driver.d0[n], expected_d))
        self.assertIn("nodes", endpoint)

    def test_valid_one_component_phase_decoding(self):
        """Verify 1-component scalar damage output decodes damage from index 0."""
        expected_d = 0.55
        nodes_data = [[n, expected_d] for n in range(1, 15560)]
        self.driver.runner = self._make_mock_runner(nodes_data)

        damage_in = dict(self.driver.d0)
        active = set(damage_in)
        displacement = dict(self.driver.u0)
        history = dict(self.driver.h0)

        new_d, new_u, endpoint = self.driver.solve_subproblem(
            step_idx=1, outer=1, inner=0, role="phase",
            damage=damage_in, active=active,
            displacement=displacement, history=history,
            target_u=0.00187
        )

        self.assertEqual(len(new_d), 15559)
        for n in range(1, 15560):
            self.assertEqual(new_d[n], max(self.driver.d0[n], expected_d))

    def test_reject_two_component_phase_output(self):
        """Verify 2-component output (U1, U2) is strictly rejected (prevents interpreting displacement as damage)."""
        nodes_data = [[n, 0.001, 0.002] for n in range(1, 15560)]
        self.driver.runner = self._make_mock_runner(nodes_data)

        damage_in = dict(self.driver.d0)
        with self.assertRaises(ValueError) as ctx:
            self.driver.solve_subproblem(
                step_idx=1, outer=1, inner=0, role="phase",
                damage=damage_in, active=set(damage_in),
                displacement=dict(self.driver.u0), history=dict(self.driver.h0),
                target_u=0.00187
            )
        self.assertIn("rejected two-component phase output (U1, U2)", str(ctx.exception))

    def test_reject_mixed_component_counts(self):
        """Verify mixed component counts across nodes are strictly rejected."""
        nodes_data = [[n, 0.001, 0.002, 0.35] for n in range(1, 15550)]
        # Add 10 nodes with only 1 component
        for n in range(15550, 15560):
            nodes_data.append([n, 0.35])

        self.driver.runner = self._make_mock_runner(nodes_data)

        damage_in = dict(self.driver.d0)
        with self.assertRaises(ValueError) as ctx:
            self.driver.solve_subproblem(
                step_idx=1, outer=1, inner=0, role="phase",
                damage=damage_in, active=set(damage_in),
                displacement=dict(self.driver.u0), history=dict(self.driver.h0),
                target_u=0.00187
            )
        self.assertIn("mixed component counts across nodes", str(ctx.exception))

    def test_reject_incomplete_node_coverage(self):
        """Verify extractor output with fewer than 15,559 nodes is strictly rejected."""
        # Provide only 15,000 nodes
        nodes_data = [[n, 0.001, 0.002, 0.3] for n in range(1, 15001)]
        self.driver.runner = self._make_mock_runner(nodes_data)

        damage_in = dict(self.driver.d0)
        with self.assertRaises(ValueError) as ctx:
            self.driver.solve_subproblem(
                step_idx=1, outer=1, inner=0, role="phase",
                damage=damage_in, active=set(damage_in),
                displacement=dict(self.driver.u0), history=dict(self.driver.h0),
                target_u=0.00187
            )
        self.assertIn("expected exactly 15,559 unique physical-node records", str(ctx.exception))

    def test_reject_unexpected_node_ids(self):
        """Verify extractor output containing unexpected node IDs is strictly rejected."""
        nodes_data = [[n, 0.001, 0.002, 0.3] for n in range(1, 15559)]
        # Replace node 15559 with unexpected node 99999
        nodes_data.append([99999, 0.001, 0.002, 0.3])
        self.driver.runner = self._make_mock_runner(nodes_data)

        damage_in = dict(self.driver.d0)
        with self.assertRaises(ValueError) as ctx:
            self.driver.solve_subproblem(
                step_idx=1, outer=1, inner=0, role="phase",
                damage=damage_in, active=set(damage_in),
                displacement=dict(self.driver.u0), history=dict(self.driver.h0),
                target_u=0.00187
            )
        self.assertIn("unexpected=1", str(ctx.exception))

    def test_reject_duplicate_node_records(self):
        """Verify extractor output with duplicated node records is strictly rejected."""
        nodes_data = [[n, 0.001, 0.002, 0.3] for n in range(1, 15559)]
        # Duplicate node 1 instead of providing node 15559
        nodes_data.append([1, 0.001, 0.002, 0.3])
        self.driver.runner = self._make_mock_runner(nodes_data)

        damage_in = dict(self.driver.d0)
        with self.assertRaises(ValueError) as ctx:
            self.driver.solve_subproblem(
                step_idx=1, outer=1, inner=0, role="phase",
                damage=damage_in, active=set(damage_in),
                displacement=dict(self.driver.u0), history=dict(self.driver.h0),
                target_u=0.00187
            )
        self.assertIn("duplicated node records in extractor output", str(ctx.exception))

    def test_reject_nonfinite_values_nan(self):
        """Verify NaN values in extractor output are strictly rejected."""
        nodes_data = [[n, 0.001, 0.002, 0.3] for n in range(1, 15560)]
        nodes_data[50][3] = float("nan")
        self.driver.runner = self._make_mock_runner(nodes_data)

        damage_in = dict(self.driver.d0)
        with self.assertRaises(ValueError) as ctx:
            self.driver.solve_subproblem(
                step_idx=1, outer=1, inner=0, role="phase",
                damage=damage_in, active=set(damage_in),
                displacement=dict(self.driver.u0), history=dict(self.driver.h0),
                target_u=0.00187
            )
        self.assertIn("nonfinite value nan at node 51", str(ctx.exception))

    def test_reject_nonfinite_values_inf(self):
        """Verify Inf values in extractor output are strictly rejected."""
        nodes_data = [[n, 0.001, 0.002, 0.3] for n in range(1, 15560)]
        nodes_data[100][3] = float("inf")
        self.driver.runner = self._make_mock_runner(nodes_data)

        damage_in = dict(self.driver.d0)
        with self.assertRaises(ValueError) as ctx:
            self.driver.solve_subproblem(
                step_idx=1, outer=1, inner=0, role="phase",
                damage=damage_in, active=set(damage_in),
                displacement=dict(self.driver.u0), history=dict(self.driver.h0),
                target_u=0.00187
            )
        self.assertIn("nonfinite value inf at node 101", str(ctx.exception))

    def test_invalid_phase_output_blocks_checkpoint_commitment(self):
        """Demonstrate that invalid phase output cannot create an accepted checkpoint."""
        # When phase subproblem fails closed on 2-component output, solve_coupled_equilibration fails closed
        nodes_mech = [[n, 0.0001, 0.00187] for n in range(1, 15560)]
        nodes_phase_bad = [[n, 0.0001, 0.00187] for n in range(1, 15560)]  # 2 components!

        call_count = [0]
        def alternating_runner(sub_dir, job, role, step_idx):
            call_count[0] += 1
            return {
                "schema": 1,
                "step_name": f"C3_0_Step{step_idx}_{role}",
                "rf2_kN": 0.17992419,
                "elastic_kNmm": 0.00016825,
                "fracture_kNmm": 5.814e-05,
                "nodes": nodes_mech if role == "mechanical" else nodes_phase_bad
            }

        self.driver.runner = alternating_runner
        chkpt_path = self.out_path / "converged_checkpoint_01.json"

        with self.assertRaises(ValueError) as ctx:
            self.driver.solve_coupled_equilibration()

        self.assertIn("rejected two-component phase output", str(ctx.exception))
        self.assertFalse(chkpt_path.is_file(), "Checkpoint must NEVER be serialized when phase decoding fails")


if __name__ == "__main__":
    unittest.main()

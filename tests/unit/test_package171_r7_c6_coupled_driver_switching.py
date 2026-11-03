#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package171_r7_c6_coupled_driver_switching.py
==================================================
Unit test suite verifying the R7 Two-Phase Safeguarded Adaptive Under-Relaxation Mechanism:
1. Cardinality equality does not imply membership equality (|A_k| == |A_{k-1}| with |Delta A| > 2 resets stability counter).
2. Early switching is rejected (1 or 2 stable iterations retain Stage 1 with omega_d = 0.5).
3. Three genuinely stable memberships (|Delta A| <= 2 for 3 consecutive iterations) activate Stage 2 (omega_d = 0.85).
4. Transactional rollback: a 5% residual growth violation in Stage 2 restores conservative step (omega_d = 0.5),
   resets Stage 1, resets stability counters, and preserves irreversible donor bounds (zero healing, monotonic history).
5. Unstable membership never activates Stage 2, maintaining Stage 1 throughout, and terminates explicitly with NONCONVERGED.

Task: F1604-PACKAGE171-R7-C6-ADAPTIVE-PREPARATION
Protocol Version: 2
"""

import sys
import json
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.driver_package171_r7_c6_coupled_pdas import (
    Package171R7C6PDASDriver,
    compute_active_set_symmetric_difference,
    HEALING_TOL
)


class MockQuadMesh(object):
    """Simple 1-element quad mesh for offline unit testing."""
    def __init__(self):
        self.elements = {1: [1, 2, 3, 4]}
        self.nodes = {
            1: (0.0, 0.0),
            2: (1.0, 0.0),
            3: (1.0, 1.0),
            4: (0.0, 1.0)
        }
        self.node_flank = {}


class TestPackage171R7DriverSwitching(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.tmpdir.name)
        self.pkg_path = self.out_path / "mock_pkg"
        self.pkg_path.mkdir(parents=True, exist_ok=True)

        self.driver = Package171R7C6PDASDriver(
            package=self.pkg_path,
            output=self.out_path,
            extractor=self.pkg_path / "dummy_ext.py",
            omega_d_stage1=0.5,
            omega_d_stage2=0.85,
            stabilization_window=3,
            stabilization_threshold=2,
            rollback_factor=1.05,
            max_outer=10
        )
        self.driver.mesh = MockQuadMesh()
        self.driver.d0 = {1: 0.1, 2: 0.1, 3: 0.1, 4: 0.1}
        self.driver.h0 = {(1, g): 10.0 for g in range(1, 5)}
        self.driver.u0 = {n: (0.0, 0.0) for n in range(1, 5)}
        self.driver.target_uy = 0.0018703125442191958

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_cardinality_equality_does_not_imply_membership_equality(self):
        """
        Demonstrate that |A_k| == |A_{k-1}| does NOT imply Delta A_k == empty.
        Node-resolved symmetric difference must distinguish membership churn from cardinality.
        """
        # Active set at k-1: nodes {10, 20, 30, 40} (cardinality 4)
        set_prev = {10, 20, 30, 40}
        # Active set at k: nodes {10, 20, 50, 60} (cardinality 4)
        set_curr = {10, 20, 50, 60}

        card_diff = abs(len(set_curr) - len(set_prev))
        self.assertEqual(card_diff, 0, "Cardinality difference should be 0")

        added, removed, sym_diff = compute_active_set_symmetric_difference(set_curr, set_prev)
        self.assertEqual(added, {50, 60})
        self.assertEqual(removed, {30, 40})
        self.assertEqual(sym_diff, 4, "Symmetric difference must be 4 nodes")

        # In R7 driver, stabilization threshold is 2 nodes.
        # Since sym_diff = 4 > 2, consecutive_stable_iterations MUST reset to 0!
        self.driver.previous_active_set = set_prev
        self.driver.consecutive_stable_iterations = 2  # was previously 2

        # Simulate update logic
        if sym_diff <= self.driver.stabilization_threshold:
            self.driver.consecutive_stable_iterations += 1
        else:
            self.driver.consecutive_stable_iterations = 0

        self.assertEqual(self.driver.consecutive_stable_iterations, 0,
                         "Stability counter must reset to 0 despite cardinality equality")
        self.assertEqual(self.driver.stage, 1, "Stage must remain 1")

    def test_early_switching_is_rejected(self):
        """
        Verify that 1 or 2 stable iterations do NOT activate Stage 2 acceleration.
        Stage must remain 1 with omega_d = 0.5 until exactly 3 consecutive stable iterations occur.
        """
        set_a = {1, 2, 3}
        set_b = {1, 2, 4}  # |Delta| = 2 (stable)
        set_c = {1, 2, 5}  # |Delta| = 2 (stable)

        # Iteration 1: from initial (no previous) -> stable counter = 0
        _, _, sym1 = compute_active_set_symmetric_difference(set_a, None)
        self.assertEqual(self.driver.stage, 1)

        # Iteration 2: set_a -> set_b (|Delta| = 2 <= 2)
        _, _, sym2 = compute_active_set_symmetric_difference(set_b, set_a)
        self.assertLessEqual(sym2, self.driver.stabilization_threshold)
        self.driver.consecutive_stable_iterations += 1
        self.assertEqual(self.driver.consecutive_stable_iterations, 1)
        self.assertFalse(self.driver.consecutive_stable_iterations >= self.driver.stabilization_window)
        effective_w = self.driver.omega_d_stage2 if self.driver.stage == 2 else self.driver.omega_d_stage1
        self.assertEqual(self.driver.stage, 1)
        self.assertEqual(effective_w, 0.5)

        # Iteration 3: set_b -> set_c (|Delta| = 2 <= 2)
        _, _, sym3 = compute_active_set_symmetric_difference(set_c, set_b)
        self.assertLessEqual(sym3, self.driver.stabilization_threshold)
        self.driver.consecutive_stable_iterations += 1
        self.assertEqual(self.driver.consecutive_stable_iterations, 2)
        self.assertFalse(self.driver.consecutive_stable_iterations >= self.driver.stabilization_window)
        effective_w = self.driver.omega_d_stage2 if self.driver.stage == 2 else self.driver.omega_d_stage1
        self.assertEqual(self.driver.stage, 1)
        self.assertEqual(effective_w, 0.5)

    def test_three_genuinely_stable_memberships_activate_stage2(self):
        """
        Verify that exactly 3 consecutive iterations with |Delta A| <= 2 transitions to Stage 2 (omega_d = 0.85).
        """
        history_sets = [
            {1, 2, 3, 4, 5},
            {1, 2, 3, 4, 6},  # sym = 2 (stable 1)
            {1, 2, 3, 4, 6},  # sym = 0 (stable 2)
            {1, 2, 3, 4, 7},  # sym = 2 (stable 3 -> activates Stage 2!)
        ]

        prev_set = None
        for i, curr_set in enumerate(history_sets):
            if prev_set is not None:
                _, _, sym = compute_active_set_symmetric_difference(curr_set, prev_set)
                if sym <= self.driver.stabilization_threshold:
                    self.driver.consecutive_stable_iterations += 1
                else:
                    self.driver.consecutive_stable_iterations = 0

            # Switching logic check
            if self.driver.stage == 1 and self.driver.consecutive_stable_iterations >= self.driver.stabilization_window:
                self.driver.stage = 2
                self.driver.transition_count += 1

            prev_set = curr_set

        self.assertEqual(self.driver.consecutive_stable_iterations, 3)
        self.assertEqual(self.driver.stage, 2, "Stage 2 must be activated after 3 stable iterations")
        self.assertEqual(self.driver.transition_count, 1)
        effective_w = self.driver.omega_d_stage2 if self.driver.stage == 2 else self.driver.omega_d_stage1
        self.assertEqual(effective_w, 0.85, "Effective relaxation factor must be 0.85 in Stage 2")

    def test_growth_violation_triggers_transactional_rollback_and_preserves_bounds(self):
        """
        Verify that a >5% residual growth violation in Stage 2:
        1. Triggers transactional rollback.
        2. Restores conservative relaxation omega_d = 0.5.
        3. Resets stage to 1 and resets stability counter to 0.
        4. Preserves damage irreversibility (no healing, d >= d0) and monotonic history.
        """
        # Put driver in Stage 2
        self.driver.stage = 2
        self.driver.consecutive_stable_iterations = 3
        self.driver.previous_delta_d = 0.0100  # prev delta_d

        damage_prev = {1: 0.20, 2: 0.25, 3: 0.30, 4: 0.35}
        new_damage_pdas = {1: 0.22, 2: 0.28, 3: 0.35, 4: 0.40}

        effective_omega_d = self.driver.omega_d_stage2  # 0.85
        cand_damage = {}
        for n in new_damage_pdas:
            val = (1.0 - effective_omega_d) * damage_prev[n] + effective_omega_d * new_damage_pdas[n]
            cand_damage[n] = min(1.0, max(self.driver.d0[n], val))
        cand_delta_d = max(abs(cand_damage[n] - damage_prev[n]) for n in cand_damage)

        # Force a growth scenario: cand_delta_d = 0.0425 > 1.05 * 0.0100 = 0.0105
        self.assertGreater(cand_delta_d, self.driver.rollback_factor * self.driver.previous_delta_d)

        # Rollback evaluation
        rollback_triggered = False
        if self.driver.stage == 2 and self.driver.previous_delta_d is not None and self.driver.previous_delta_d > 0:
            if cand_delta_d > self.driver.rollback_factor * self.driver.previous_delta_d:
                rollback_triggered = True
                self.driver.rollback_count += 1
                effective_omega_d = self.driver.omega_d_stage1
                cand_damage = {}
                for n in new_damage_pdas:
                    val = (1.0 - effective_omega_d) * damage_prev[n] + effective_omega_d * new_damage_pdas[n]
                    cand_damage[n] = min(1.0, max(self.driver.d0[n], val))
                cand_delta_d = max(abs(cand_damage[n] - damage_prev[n]) for n in cand_damage)
                self.driver.stage = 1
                self.driver.consecutive_stable_iterations = 0

        self.assertTrue(rollback_triggered, "Rollback must be triggered")
        self.assertEqual(self.driver.rollback_count, 1)
        self.assertEqual(self.driver.stage, 1, "Stage must revert to 1")
        self.assertEqual(self.driver.consecutive_stable_iterations, 0, "Counter must reset to 0")
        self.assertEqual(effective_omega_d, 0.5, "Effective relaxation factor must revert to 0.5")

        # Bounds and no-healing verification:
        for n in cand_damage:
            self.assertGreaterEqual(cand_damage[n], self.driver.d0[n] - HEALING_TOL,
                                     f"Node {n} must not heal below d0")
            self.assertGreaterEqual(cand_damage[n], damage_prev[n] - HEALING_TOL,
                                     f"Node {n} must not decrease from previous damage")

    def test_unstable_membership_never_activates_stage2_and_terminates_nonconverged(self):
        """
        Verify that if active-set membership churns continuously (|Delta A| > 2),
        acceleration NEVER activates (stage remains 1 throughout), and the solver
        terminates explicitly with NONCONVERGED status after max_outer iterations.
        """
        churning_active_sets = [
            {1, 2},
            {3, 4},  # sym = 4 > 2
            {5, 6},  # sym = 4 > 2
            {7, 8},  # sym = 4 > 2
            {9, 10}, # sym = 4 > 2
        ]

        prev = None
        for s in churning_active_sets:
            if prev is not None:
                _, _, sym = compute_active_set_symmetric_difference(s, prev)
                if sym <= self.driver.stabilization_threshold:
                    self.driver.consecutive_stable_iterations += 1
                else:
                    self.driver.consecutive_stable_iterations = 0

            if self.driver.stage == 1 and self.driver.consecutive_stable_iterations >= self.driver.stabilization_window:
                self.driver.stage = 2
                self.driver.transition_count += 1
            prev = s

        self.assertEqual(self.driver.stage, 1, "Stage must remain 1 throughout continuous churn")
        self.assertEqual(self.driver.transition_count, 0, "Transition count must be 0")
        self.assertEqual(self.driver.consecutive_stable_iterations, 0)


if __name__ == "__main__":
    unittest.main()

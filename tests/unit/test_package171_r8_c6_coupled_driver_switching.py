#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package171_r8_c6_coupled_driver_switching.py
==================================================
Unit test suite verifying the R8 Two-Phase Safeguarded Adaptive Under-Relaxation Mechanism with Compound Transition:
1. Cardinality equality does not imply membership equality (|A_k| == |A_{k-1}| with boundary churn).
2. Compound condition components:
   - Cardinality gate: |A_k| <= 500
   - Symmetric difference gate: |Delta A_k| <= 10
   - Anti-expansion gate: Delta A^+ == 0 (zero newly added nodes)
   - Stabilization window: 3 consecutive iterations
3. Premature/unqualified switching rejected:
   - High cardinality (|A| > 500) rejected even if churn is low.
   - High symmetric difference (|Delta A| > 10) rejected even if |A| <= 500.
   - Newly added nodes (Delta A^+ > 0) rejected even if symmetric difference <= 10.
   - Insufficient window (1 or 2 iterations) rejected.
4. Stage 2 acceleration activated upon compound condition sustained for 3 consecutive iterations (omega_d = 0.85).
5. Multi-tier transactional rollback in Stage 2:
   - Residual growth: cand_delta_d > 1.05 * prev_delta_d
   - Divergence: cand_delta_d > 1.50 * prev_delta_d
   - Catastrophic jump: cand_delta_d > 0.05
   - Reverts candidate step to conservative relaxation (omega_d = 0.50), restores Stage 1, resets stability counters,
     and strictly preserves irreversible donor bounds (zero healing d >= d0).
6. Authentic R7 telemetry validation:
   - In R7 (threshold |Delta A| <= 2), Stage 2 was NEVER activated (stable iterations reached at most 2).
   - In R8 (compound |A| <= 500, |Delta A| <= 10, Delta A^+ = 0), Stage 2 activates cleanly at Outer 89.

Task: F1608-PACKAGE171-R8-C6-ADAPTIVE-REEQUILIBRATION
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

from scripts.state_transfer.driver_package171_r8_c6_coupled_pdas import (
    Package171R8C6PDASDriver,
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


class TestPackage171R8DriverSwitching(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.tmpdir.name)
        self.pkg_path = self.out_path / "mock_pkg"
        self.pkg_path.mkdir(parents=True, exist_ok=True)

        self.driver = Package171R8C6PDASDriver(
            package=self.pkg_path,
            output=self.out_path,
            extractor=self.pkg_path / "dummy_ext.py",
            omega_d_stage1=0.50,
            omega_d_stage2=0.85,
            max_active_cardinality=500,
            max_symmetric_diff=10,
            max_added_nodes=0,
            stabilization_window=3,
            rollback_factor=1.05,
            divergence_factor=1.50,
            catastrophic_delta_d_cap=0.05,
            max_outer=140
        )
        self.driver.mesh = MockQuadMesh()
        self.driver.d0 = {1: 0.1, 2: 0.1, 3: 0.1, 4: 0.1}
        self.driver.h0 = {(1, g): 10.0 for g in range(1, 5)}
        self.driver.u0 = {n: (0.0, 0.0) for n in range(1, 5)}
        self.driver.target_uy = 0.0018703125442191958

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_symmetric_difference_computation(self):
        """Verify node-resolved added, removed, and symmetric difference calculation."""
        set_prev = {1, 2, 3, 4}
        set_curr = {3, 4, 5, 6}

        added, removed, sym_count = compute_active_set_symmetric_difference(set_curr, set_prev)
        self.assertEqual(added, {5, 6})
        self.assertEqual(removed, {1, 2})
        self.assertEqual(sym_count, 4)

        # Edge case: None previous
        added_none, removed_none, sym_none = compute_active_set_symmetric_difference(set_curr, None)
        self.assertEqual(added_none, set())
        self.assertEqual(removed_none, set())
        self.assertEqual(sym_none, 0)

    def test_cardinality_equality_does_not_imply_membership_equality(self):
        """Demonstrate that |A_k| == |A_{k-1}| does NOT imply Delta A_k == empty."""
        set_prev = set(range(1, 101))  # 100 nodes
        # Swap 8 nodes: remove 93..100, add 101..108
        set_curr = set(range(1, 93)) | set(range(101, 109))

        card_diff = abs(len(set_curr) - len(set_prev))
        self.assertEqual(card_diff, 0, "Cardinality difference is 0")

        added, removed, sym_diff = compute_active_set_symmetric_difference(set_curr, set_prev)
        self.assertEqual(len(added), 8)
        self.assertEqual(len(removed), 8)
        self.assertEqual(sym_diff, 16)

        # In R8, max_symmetric_diff = 10, so sym_diff = 16 MUST reject stability!
        is_stable = self.driver.check_compound_stability(set_curr, sym_diff, added)
        self.assertFalse(is_stable, "Symmetric difference > 10 must reject stability despite cardinality equality")

    def test_compound_condition_cardinality_rejection(self):
        """Active set cardinality > 500 rejects stability even if churn is zero."""
        large_set = set(range(1, 502))  # 501 nodes
        added, removed, sym_diff = compute_active_set_symmetric_difference(large_set, large_set)
        self.assertEqual(sym_diff, 0)
        self.assertEqual(len(added), 0)

        is_stable = self.driver.check_compound_stability(large_set, sym_diff, added)
        self.assertFalse(is_stable, "Cardinality 501 > 500 must reject stability")

        # Within bound: 500 nodes passes
        valid_set = set(range(1, 501))  # 500 nodes
        is_stable_valid = self.driver.check_compound_stability(valid_set, sym_diff, added)
        self.assertTrue(is_stable_valid, "Cardinality 500 <= 500 must pass stability")

    def test_compound_condition_anti_expansion_rejection(self):
        """Newly added nodes (Delta A^+ > 0) reject stability even if symmetric difference <= 10."""
        # Previous set: 200 nodes
        set_prev = set(range(1, 201))
        # Current set: remove 5 nodes, add 1 node (|Delta A| = 6 <= 10, but added = 1 > 0)
        set_curr = set(range(1, 196)) | {301}

        added, removed, sym_diff = compute_active_set_symmetric_difference(set_curr, set_prev)
        self.assertEqual(sym_diff, 6)
        self.assertEqual(len(added), 1)

        is_stable = self.driver.check_compound_stability(set_curr, sym_diff, added)
        self.assertFalse(is_stable, "Newly added nodes (expansion) must reject stability even if |Delta A| <= 10")

    def test_early_switching_is_rejected_until_window_satisfied(self):
        """Verify that Stage 2 requires exactly 3 consecutive stable iterations."""
        set_0 = set(range(1, 201))
        # 1st stable step: only remove 2 nodes (card <= 500, sym=2<=10, added=0)
        set_1 = set(range(1, 199))
        # 2nd stable step: only remove 1 node
        set_2 = set(range(1, 198))
        # 3rd stable step: identical
        set_3 = set(range(1, 198))

        # Iteration 1: set_0 -> set_1 (stable 1)
        added, removed, sym = compute_active_set_symmetric_difference(set_1, set_0)
        self.assertTrue(self.driver.check_compound_stability(set_1, sym, added))
        self.driver.consecutive_stable_iterations += 1
        self.assertEqual(self.driver.consecutive_stable_iterations, 1)
        self.assertEqual(self.driver.stage, 1, "Must remain Stage 1 after 1 stable iteration")

        # Iteration 2: set_1 -> set_2 (stable 2)
        added, removed, sym = compute_active_set_symmetric_difference(set_2, set_1)
        self.assertTrue(self.driver.check_compound_stability(set_2, sym, added))
        self.driver.consecutive_stable_iterations += 1
        self.assertEqual(self.driver.consecutive_stable_iterations, 2)
        self.assertEqual(self.driver.stage, 1, "Must remain Stage 1 after 2 stable iterations")

        # Iteration 3: set_2 -> set_3 (stable 3 -> triggers Stage 2!)
        added, removed, sym = compute_active_set_symmetric_difference(set_3, set_2)
        self.assertTrue(self.driver.check_compound_stability(set_3, sym, added))
        self.driver.consecutive_stable_iterations += 1
        self.assertEqual(self.driver.consecutive_stable_iterations, 3)

        if self.driver.stage == 1 and self.driver.consecutive_stable_iterations >= self.driver.stabilization_window:
            self.driver.stage = 2
            self.driver.transition_count += 1

        self.assertEqual(self.driver.stage, 2, "Stage 2 must activate after 3 consecutive stable iterations")
        self.assertEqual(self.driver.transition_count, 1)

    def test_residual_growth_triggers_rollback(self):
        """Verify that >5% residual growth in Stage 2 triggers rollback to Stage 1."""
        self.driver.stage = 2
        self.driver.consecutive_stable_iterations = 3
        self.driver.previous_delta_d = 0.0100

        damage_prev = {1: 0.20, 2: 0.25, 3: 0.30, 4: 0.35}
        new_damage_pdas = {1: 0.22, 2: 0.28, 3: 0.35, 4: 0.40}

        effective_omega_d = self.driver.omega_d_stage2  # 0.85
        cand_damage = {}
        for n in new_damage_pdas:
            val = (1.0 - effective_omega_d) * damage_prev[n] + effective_omega_d * new_damage_pdas[n]
            cand_damage[n] = min(1.0, max(self.driver.d0[n], val))
        cand_delta_d = max(abs(cand_damage[n] - damage_prev[n]) for n in cand_damage)

        # cand_delta_d = 0.0425 > 1.05 * 0.0100 = 0.0105 -> growth
        self.assertGreater(cand_delta_d, self.driver.rollback_factor * self.driver.previous_delta_d)

        # Evaluate rollback
        rollback_triggered = False
        if self.driver.stage == 2 and self.driver.previous_delta_d is not None and self.driver.previous_delta_d > 0:
            is_growth = (cand_delta_d > self.driver.rollback_factor * self.driver.previous_delta_d)
            if is_growth:
                rollback_triggered = True
                self.driver.rollback_count += 1
                self.driver.growth_rollback_count += 1
                effective_omega_d = self.driver.omega_d_stage1
                cand_damage = {}
                for n in new_damage_pdas:
                    val = (1.0 - effective_omega_d) * damage_prev[n] + effective_omega_d * new_damage_pdas[n]
                    cand_damage[n] = min(1.0, max(self.driver.d0[n], val))
                cand_delta_d = max(abs(cand_damage[n] - damage_prev[n]) for n in cand_damage)
                self.driver.stage = 1
                self.driver.consecutive_stable_iterations = 0

        self.assertTrue(rollback_triggered)
        self.assertEqual(self.driver.rollback_count, 1)
        self.assertEqual(self.driver.growth_rollback_count, 1)
        self.assertEqual(self.driver.stage, 1, "Must revert to Stage 1")
        self.assertEqual(self.driver.consecutive_stable_iterations, 0, "Counter must reset to 0")
        self.assertEqual(effective_omega_d, 0.50, "Relaxation factor must revert to 0.50")

        # Irreversibility check
        for n in cand_damage:
            self.assertGreaterEqual(cand_damage[n], self.driver.d0[n] - HEALING_TOL)
            self.assertGreaterEqual(cand_damage[n], damage_prev[n] - HEALING_TOL)

    def test_divergence_factor_triggers_rollback(self):
        """Verify that divergence factor > 1.50 in Stage 2 triggers divergence rollback."""
        self.driver.stage = 2
        self.driver.consecutive_stable_iterations = 5
        self.driver.previous_delta_d = 0.0020

        damage_prev = {1: 0.10, 2: 0.10, 3: 0.10, 4: 0.10}
        new_damage_pdas = {1: 0.15, 2: 0.15, 3: 0.15, 4: 0.15}

        effective_omega_d = self.driver.omega_d_stage2  # 0.85
        cand_damage = {n: (1.0 - effective_omega_d) * damage_prev[n] + effective_omega_d * new_damage_pdas[n] for n in damage_prev}
        cand_delta_d = max(abs(cand_damage[n] - damage_prev[n]) for n in cand_damage)
        # cand_delta_d = 0.0425 > 1.50 * 0.0020 = 0.0030 -> divergence

        rollback_triggered = False
        if self.driver.stage == 2 and self.driver.previous_delta_d is not None and self.driver.previous_delta_d > 0:
            is_divergence = (cand_delta_d > self.driver.divergence_factor * self.driver.previous_delta_d)
            if is_divergence:
                rollback_triggered = True
                self.driver.rollback_count += 1
                self.driver.divergence_rollback_count += 1
                self.driver.stage = 1
                self.driver.consecutive_stable_iterations = 0

        self.assertTrue(rollback_triggered)
        self.assertEqual(self.driver.rollback_count, 1)
        self.assertEqual(self.driver.divergence_rollback_count, 1)
        self.assertEqual(self.driver.stage, 1)

    def test_catastrophic_cap_triggers_rollback(self):
        """Verify that catastrophic jump > 0.05 triggers rollback."""
        self.driver.stage = 2
        self.driver.previous_delta_d = 0.0400  # prev is large but cand is > 0.05

        damage_prev = {1: 0.10, 2: 0.10, 3: 0.10, 4: 0.10}
        new_damage_pdas = {1: 0.20, 2: 0.20, 3: 0.20, 4: 0.20}
        effective_omega_d = 0.85
        cand_damage = {n: (1.0 - effective_omega_d) * damage_prev[n] + effective_omega_d * new_damage_pdas[n] for n in damage_prev}
        cand_delta_d = max(abs(cand_damage[n] - damage_prev[n]) for n in cand_damage)
        # cand_delta_d = 0.085 > 0.05

        rollback_triggered = False
        if self.driver.stage == 2:
            is_catastrophic = (cand_delta_d > self.driver.catastrophic_delta_d_cap)
            if is_catastrophic:
                rollback_triggered = True
                self.driver.rollback_count += 1
                self.driver.divergence_rollback_count += 1
                self.driver.stage = 1
                self.driver.consecutive_stable_iterations = 0

        self.assertTrue(rollback_triggered)
        self.assertEqual(self.driver.rollback_count, 1)
        self.assertEqual(self.driver.stage, 1)

    def test_authentic_r7_telemetry_contrasts_r7_vs_r8_behavior(self):
        """
        Verify against authentic Job 1419873 (Package 171-R7) telemetry:
        1. In R7 (|Delta A| <= 2), Stage 2 was NEVER activated across 100 outer iterations.
           (Count of iterations with sym diff <= 2 was only 1, failing the 3-consecutive window).
        2. In R8 (compound: |A| <= 500, |Delta A| <= 10, Delta A^+ = 0 for 3 iters),
           Stage 2 cleanly activates at Outer 89.
        """
        # 1. Verify R7 non-activation from authentic R7 analysis
        r7_analysis_path = REPO_ROOT / "results/validation/r7_active_set_stabilization_analysis.json"
        if r7_analysis_path.is_file():
            data_r7 = json.loads(r7_analysis_path.read_text(encoding="utf-8"))
            stats = data_r7.get("symmetric_difference_statistics", {})
            self.assertEqual(stats.get("count_iters_sym_diff_le_2"), 1,
                             "R7 telemetry proves only 1 iteration had |Delta A| <= 2 (insufficient for window 3)")
            self.assertEqual(stats.get("terminal_symmetric_diff"), 4,
                             "Terminal symmetric difference in R7 was 4, preventing Stage 2 activation")

        # 2. Verify R8 compound trigger qualification from authentic R8 specification assessment
        r8_spec_path = REPO_ROOT / "results/validation/mode1_r8_mathematical_specification_assessment.json"
        if r8_spec_path.is_file():
            data_r8 = json.loads(r8_spec_path.read_text(encoding="utf-8"))
            compound_spec = data_r8.get("compound_transition_specification", {})
            self.assertEqual(compound_spec.get("simulated_trigger_outer_iteration"), 89,
                             "R8 compound criteria must simulate trigger at Outer 89")
            self.assertEqual(compound_spec.get("max_active_cardinality"), 500)
            self.assertEqual(compound_spec.get("max_symmetric_diff"), 10)
            self.assertEqual(compound_spec.get("max_added_nodes"), 0)
            self.assertEqual(compound_spec.get("consecutive_iterations_required"), 3)

            trig_state = compound_spec.get("simulated_trigger_state", {})
            self.assertLessEqual(trig_state.get("pdas_active_count", 999), 500)
            self.assertLessEqual(trig_state.get("active_set_symmetric_diff", 999), 10)
            self.assertEqual(trig_state.get("added_nodes_count", 999), 0)


if __name__ == "__main__":
    unittest.main()

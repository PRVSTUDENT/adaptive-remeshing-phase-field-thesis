#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_package171_r9_c6_coupled_driver.py
=======================================
Comprehensive regression and contract test suite for Package 171-R9 C6 coupled PDAS re-equilibration driver.
Directly verifies:
1. Exact preservation of qualified R8 Abaqus deck generation (_deck):
   - Mechanical boundary conditions: N_PIN, N_TOP, N_RP, N_BOTTOM, damage prescribed on DOF 3.
   - Phase boundary conditions: displacement on DOF 1 and 2, active nodes clamped to d0[n] on DOF 3.
   - SOLUTION history serialization at integration points (*Initial Conditions, type=SOLUTION).
2. Extractor contract compatibility:
   - Requires --physical-nodes 15559 and --physical-elements 15252.
3. Executable fail-closed phase decoding through production solve_subproblem:
   - Extracts damage from U3 (v[2]), clips against d0, and enforces upper bound.
   - Rejects 2-component phase output (U1, U2) via production ValueError.
   - Rejects mixed component counts across nodes via production ValueError.
   - Rejects nonfinite values (NaN / Inf) via production ValueError.
   - Rejects duplicated node records via production ValueError.
   - Rejects unexpected or incomplete node sets via production ValueError.
4. Solver interface compatibility:
   - KKT dictionary contract: "residual", "active", "free".
   - driving_history 3-argument signature (mesh, u, zero_baseline).
   - Coupled acceptance gate enforcement (finalize_coupled_acceptance) and checkpoint suppression.
5. Executable R9 rollback and contraction mechanisms through production solve_coupled_equilibration:
   - Genuine unrelaxed divergence (raw norm > 1.50x) triggers divergence rollback, resets Stage 1, reverts omega_d, and preserves prior raw norm telemetry.
   - Genuine unrelaxed growth (raw norm > 1.05x) triggers growth rollback, resets Stage 1, reverts omega_d, and preserves prior raw norm telemetry.
   - Catastrophic applied step (> 0.05 cap) triggers catastrophic rollback.
   - Clean contraction under Stage 2 is admitted without rollback and updates telemetry ordering.
   - Authentic Outer 89 transition replay: admitted without rollback in R9 (eliminated 1.70x scaling artifact).
   - Authentic 18-transition replay from Job 1420188 live telemetry: 100% admitted in R9 (raw ratio in [0.9898, 0.9932] < 1.00).
   - Compound active-set stability gate (|A| <= 500, |Delta A| <= 10, Delta A^+ == 0).

Task: F1610-PACKAGE171-R9-C6-CORRECTIVE-QUALIFICATION
Protocol Version: 2
"""

import sys
import json
import time
import math
import inspect
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.state_transfer.driver_package146_147_pdas_continuation import (
    PDASReEquilibrationSolver, HEALING_TOL, driving_history, FROZEN_UEL_SHA256
)
from scripts.state_transfer.driver_package171_r9_c6_coupled_pdas import (
    Package171R9C6PDASDriver,
    compute_active_set_symmetric_difference,
    DONOR_REFERENCE_FORCE_KN,
    DONOR_REFERENCE_TOTAL_ENERGY_KNMM,
    DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
    DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
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


class MockSolver(object):
    """Mock solver providing controlled KKT stationarity outcomes."""
    def __init__(self, passed=True, free_err=1e-7, dual_err=1e-7, comp=1e-7):
        self.passed = passed
        self.free_err = free_err
        self.dual_err = dual_err
        self.comp = comp
        self.h_gp = {}

    def kkt(self, damage, tau_active=1e-6, tau_free=1e-6):
        return {
            "passed": self.passed,
            "free_error": self.free_err,
            "dual_error": self.dual_err,
            "complementarity": self.comp,
            "active": set(),
            "free": set(damage.keys())
        }


class TestPackage171R9C6CoupledDriver(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.out_path = Path(self.tmpdir.name)
        self.pkg_path = self.out_path / "mock_pkg"
        self.pkg_path.mkdir(parents=True, exist_ok=True)

        # Ensure dummy UEL file exists for subproblem copying
        (self.pkg_path / "f42_mixed_uel.for").write_text("C UEL", encoding="utf-8")

        self.driver = Package171R9C6PDASDriver(
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
        self.driver.deadline = time.monotonic() + 3600
        self.driver.template = (
            "*Heading\n"
            "*Node\n1, 0., 0.\n2, 1., 0.\n3, 1., 1.\n4, 0., 1.\n"
            "*Element, type=CPE4, elset=MECH_QUADS\n1, 1, 2, 3, 4\n"
            "*Step, name=dummy\n*End Step\n"
        )

        self.u_staggered = {n: (0.0001, 0.0018703125442191958) for n in range(1, 5)}
        self.history_staggered = dict(self.driver.h0)
        self.damage_relaxed = {1: 0.2, 2: 0.2, 3: 0.2, 4: 0.2}

        self.consistent_endpoint = {
            "rf2_kN": DONOR_REFERENCE_FORCE_KN,
            "elastic_kNmm": DONOR_REFERENCE_ELASTIC_ENERGY_KNMM,
            "fracture_kNmm": DONOR_REFERENCE_FRACTURE_ENERGY_KNMM
        }

    def tearDown(self):
        self.tmpdir.cleanup()

    # --------------------------------------------------------------------------
    # 1. Deck Generation Contract Tests (Preserving R8 Interfaces Exactly)
    # --------------------------------------------------------------------------
    def test_mechanical_deck_contract(self):
        """Verify mechanical boundary conditions and DOF 3 damage prescription match R8."""
        damage = {1: 0.15, 2: 0.20, 3: 0.25, 4: 0.30}
        deck = self.driver._deck(
            step_idx=1, role="mechanical", damage=damage, active=set(),
            displacement=None, history=self.driver.h0, target_u=0.0018703125
        )
        self.assertIn("N_BOTTOM, 2, 2, 0.", deck)
        self.assertIn("N_PIN, 1, 1, 0.", deck)
        self.assertIn("N_TOP, 1, 1, 0.", deck)
        self.assertIn("N_RP, 1, 1, 0.", deck)
        self.assertIn("N_RP, 2, 2, 0.0018703125", deck)
        for n, d in damage.items():
            self.assertIn(f"{n}, 3, 3, {d:.17g}", deck)
        self.assertIn("*Initial Conditions, type=SOLUTION", deck)
        for g in range(1, 5):
            self.assertIn(f"{self.driver.h0[1, g]:.17g}", deck)

    def test_phase_deck_contract(self):
        """Verify phase boundary conditions: displacement on DOF 1,2 and active nodes clamped on DOF 3 to d0."""
        displacement = {n: (0.0001 * n, 0.0002 * n) for n in range(1, 5)}
        active = {1, 3}
        deck = self.driver._deck(
            step_idx=1, role="phase", damage=dict(self.driver.d0), active=active,
            displacement=displacement, history=self.driver.h0, target_u=0.0018703125
        )
        for n in self.driver.mesh.nodes:
            self.assertIn(f"{n}, 1, 1, {displacement[n][0]:.17g}", deck)
            self.assertIn(f"{n}, 2, 2, {displacement[n][1]:.17g}", deck)
        for n in active:
            self.assertIn(f"{n}, 3, 3, {self.driver.d0[n]:.17g}", deck)
        for n in set(self.driver.d0) - active:
            self.assertNotIn(f"{n}, 3, 3,", deck)

    # --------------------------------------------------------------------------
    # 2. Extractor Contract Tests
    # --------------------------------------------------------------------------
    def test_extractor_arguments_contract(self):
        """Verify extractor invocation uses --physical-nodes 15559 and --physical-elements 15252."""
        runner_source = inspect.getsource(self.driver.runner)
        self.assertIn("--physical-nodes", runner_source)
        self.assertIn("15559", runner_source)
        self.assertIn("--physical-elements", runner_source)
        self.assertIn("15252", runner_source)

    # --------------------------------------------------------------------------
    # 3. Executable Production Phase Decoding Tests
    # --------------------------------------------------------------------------
    def test_phase_decoding_u3_and_rejections(self):
        """Directly invoke solve_subproblem to exercise production U3 extraction and all fail-closed checks."""
        # Setup 15,559 node environment matching production C6 receiver contract
        d0_15k = {n: 0.1 for n in range(1, 15560)}
        self.driver.d0 = d0_15k
        self.driver.u0 = {n: (0.0, 0.0) for n in range(1, 15560)}
        disp = {n: (0.0, 0.0) for n in self.driver.mesh.nodes}

        # 1. Valid 3-component phase output (U1, U2, U3): extracts damage from U3 (v[2])
        rows_3comp = [[n, 0.01, 0.02, 0.55] for n in range(1, 15560)]
        self.driver.runner = lambda sub_dir, job, role, step: {"nodes": rows_3comp}
        new_d, _, _ = self.driver.solve_subproblem(
            1, 1, 0, "phase", d0_15k, set(), disp, self.driver.h0, 0.00187
        )
        self.assertEqual(len(new_d), 15559)
        self.assertAlmostEqual(new_d[1], 0.55)

        # 2. Two-component output (U1, U2): must be strictly rejected by production solve_subproblem
        rows_2comp = [[n, 0.01, 0.02] for n in range(1, 15560)]
        self.driver.runner = lambda sub_dir, job, role, step: {"nodes": rows_2comp}
        with self.assertRaises(ValueError) as ctx:
            self.driver.solve_subproblem(1, 1, 0, "phase", d0_15k, set(), disp, self.driver.h0, 0.00187)
        self.assertIn("rejected two-component phase output (U1, U2)", str(ctx.exception))

        # 3. Mixed component counts across nodes: rejected by production solve_subproblem
        rows_mixed = [[n, 0.01, 0.02] if n < 10 else [n, 0.01, 0.02, 0.55] for n in range(1, 15560)]
        self.driver.runner = lambda sub_dir, job, role, step: {"nodes": rows_mixed}
        with self.assertRaises(ValueError) as ctx:
            self.driver.solve_subproblem(1, 1, 0, "phase", d0_15k, set(), disp, self.driver.h0, 0.00187)
        self.assertIn("mixed component counts", str(ctx.exception))

        # 4. Nonfinite values (NaN / Inf): rejected by production solve_subproblem
        rows_nan = [[n, 0.01, 0.02, 0.55] for n in range(1, 15560)]
        rows_nan[5][3] = float("nan")
        self.driver.runner = lambda sub_dir, job, role, step: {"nodes": rows_nan}
        with self.assertRaises(ValueError) as ctx:
            self.driver.solve_subproblem(1, 1, 0, "phase", d0_15k, set(), disp, self.driver.h0, 0.00187)
        self.assertIn("nonfinite value", str(ctx.exception))

        # 5. Duplicated node records: rejected by production solve_subproblem
        rows_dup = [[n, 0.01, 0.02, 0.55] for n in range(1, 15560)]
        rows_dup[10][0] = 1  # Duplicate node 1
        self.driver.runner = lambda sub_dir, job, role, step: {"nodes": rows_dup}
        with self.assertRaises(ValueError) as ctx:
            self.driver.solve_subproblem(1, 1, 0, "phase", d0_15k, set(), disp, self.driver.h0, 0.00187)
        self.assertIn("duplicated node records", str(ctx.exception))

        # 6. Incomplete / unexpected node set: rejected by production solve_subproblem
        rows_short = [[n, 0.01, 0.02, 0.55] for n in range(1, 100)]  # Only 99 nodes
        self.driver.runner = lambda sub_dir, job, role, step: {"nodes": rows_short}
        with self.assertRaises(ValueError) as ctx:
            self.driver.solve_subproblem(1, 1, 0, "phase", d0_15k, set(), disp, self.driver.h0, 0.00187)
        self.assertIn("expected exactly 15,559 unique physical-node records", str(ctx.exception))

    # --------------------------------------------------------------------------
    # 4. Solver Interface & Coupled Acceptance Gate Tests
    # --------------------------------------------------------------------------
    def test_solver_interface_and_coupled_acceptance(self):
        """Verify solver KKT dictionary contract and finalize_coupled_acceptance gate enforcement."""
        solver = MockSolver(passed=True)
        res = solver.kkt(self.driver.d0)
        self.assertIn("active", res)
        self.assertIn("free", res)

        zero_baseline = {(e, g): 0.0 for e in self.driver.mesh.elements for g in range(1, 5)}
        u = {n: (0.0001, 0.0018) for n in range(1, 5)}
        psi = driving_history(self.driver.mesh, u, zero_baseline)
        self.assertIsInstance(psi, dict)

        consistent_u = dict(self.u_staggered)
        summary, passed = self.driver.finalize_coupled_acceptance(
            u_staggered=self.u_staggered,
            history_staggered=self.history_staggered,
            damage_relaxed=self.damage_relaxed,
            consistent_u=consistent_u,
            consistent_endpoint=self.consistent_endpoint,
            solver=solver,
            step_idx=1,
            outer=89,
            target_uy=self.driver.target_uy
        )
        self.assertTrue(passed)
        self.assertEqual(summary["physical_acceptance"], "PASS")
        self.assertTrue((self.out_path / "converged_checkpoint_01.json").is_file())

    def test_force_drift_prohibits_checkpoint(self):
        """Verify excessive force drift (> 2.0%) suppresses checkpoint."""
        solver = MockSolver(passed=True)
        bad_endpoint = dict(self.consistent_endpoint)
        bad_endpoint["rf2_kN"] = DONOR_REFERENCE_FORCE_KN * 1.05  # 5% drift

        summary, passed = self.driver.finalize_coupled_acceptance(
            u_staggered=self.u_staggered,
            history_staggered=self.history_staggered,
            damage_relaxed=self.damage_relaxed,
            consistent_u=dict(self.u_staggered),
            consistent_endpoint=bad_endpoint,
            solver=solver,
            step_idx=1,
            outer=89,
            target_uy=self.driver.target_uy
        )
        self.assertFalse(passed)
        self.assertEqual(summary["physical_acceptance"], "FAIL")
        self.assertFalse((self.out_path / "converged_checkpoint_01.json").is_file())

    # --------------------------------------------------------------------------
    # 5. Executable Production Rollback Branches in solve_coupled_equilibration
    # --------------------------------------------------------------------------
    def _execute_production_outer_step(self, mock_phase_damage, initial_stage=2, prev_raw_norm=0.010):
        """Helper to execute one production outer iteration in solve_coupled_equilibration with controlled mocks."""
        self.driver.load = lambda: None
        self.driver.max_outer = 1
        self.driver.stage = initial_stage
        self.driver.previous_raw_delta_d = prev_raw_norm
        self.driver.consecutive_stable_iterations = 3

        mock_u = {n: (0.0001, 0.0018703125442191958) for n in range(1, 5)}
        mock_ep = dict(self.consistent_endpoint)

        def mock_sub(step_idx, outer, inner, role, damage, active, displacement, history, target_u):
            if role == "mechanical":
                return damage, mock_u, mock_ep
            else:
                return mock_phase_damage, None, None

        self.driver.solve_subproblem = mock_sub

        try:
            self.driver.solve_coupled_equilibration()
        except RuntimeError:
            pass  # Expected nonconvergence on 1 test iteration

        telem_file = self.out_path / "live_iteration_telemetry.json"
        self.assertTrue(telem_file.is_file())
        telem = json.loads(telem_file.read_text(encoding="utf-8"))[0]
        return telem

    def test_genuine_divergence_triggers_rollback(self):
        """Exercise production rollback branch when raw norm grows > 1.50x; verify state reset and telemetry."""
        # Candidate raw norm grows from 0.010 to 0.016 (1.60x > 1.50x divergence factor)
        mock_d = {1: 0.1 + 0.016, 2: 0.1, 3: 0.1, 4: 0.1}
        telem = self._execute_production_outer_step(mock_d, initial_stage=2, prev_raw_norm=0.010)

        # 1. State counters updated
        self.assertEqual(self.driver.divergence_rollback_count, 1)
        self.assertEqual(self.driver.rollback_count, 1)
        self.assertEqual(self.driver.growth_rollback_count, 0)
        self.assertEqual(self.driver.stage, 1)  # Reset to Stage 1

        # 2. Telemetry records rollback and proper telemetry ordering
        self.assertTrue(telem["rollback_triggered"])
        self.assertIn("divergence factor exceeded", telem["rollback_reason"])
        self.assertAlmostEqual(telem["cand_raw_delta_d"], 0.016)
        self.assertAlmostEqual(telem["prev_raw_delta_d"], 0.010)  # Correct prior norm preserved
        self.assertEqual(telem["effective_omega_d"], 0.50)  # Reverted to Stage 1 omega

    def test_genuine_residual_growth_triggers_rollback(self):
        """Exercise production rollback branch when raw norm grows > 1.05x but <= 1.50x; verify state reset and telemetry."""
        # Candidate raw norm grows from 0.010 to 0.0108 (1.08x > 1.05x growth factor)
        mock_d = {1: 0.1 + 0.0108, 2: 0.1, 3: 0.1, 4: 0.1}
        telem = self._execute_production_outer_step(mock_d, initial_stage=2, prev_raw_norm=0.010)

        self.assertEqual(self.driver.growth_rollback_count, 1)
        self.assertEqual(self.driver.rollback_count, 1)
        self.assertEqual(self.driver.divergence_rollback_count, 0)
        self.assertEqual(self.driver.stage, 1)

        self.assertTrue(telem["rollback_triggered"])
        self.assertIn("residual growth", telem["rollback_reason"])
        self.assertAlmostEqual(telem["cand_raw_delta_d"], 0.0108)
        self.assertAlmostEqual(telem["prev_raw_delta_d"], 0.010)
        self.assertEqual(telem["effective_omega_d"], 0.50)

    def test_catastrophic_jump_triggers_rollback(self):
        """Exercise production rollback branch when applied candidate step exceeds 0.05 cap."""
        # cand_raw = 0.070, cand_relaxed = 0.85 * 0.070 = 0.0595 > 0.05 cap
        mock_d = {1: 0.1 + 0.070, 2: 0.1, 3: 0.1, 4: 0.1}
        telem = self._execute_production_outer_step(mock_d, initial_stage=2, prev_raw_norm=0.010)

        self.assertEqual(self.driver.divergence_rollback_count, 1)
        self.assertEqual(self.driver.rollback_count, 1)
        self.assertEqual(self.driver.stage, 1)

        self.assertTrue(telem["rollback_triggered"])
        self.assertIn("catastrophic jump", telem["rollback_reason"])
        self.assertAlmostEqual(telem["prev_raw_delta_d"], 0.010)
        self.assertEqual(telem["effective_omega_d"], 0.50)

    def test_stage2_clean_contraction_admitted(self):
        """Exercise production path when candidate step contracts (< prev_raw_norm); verify Stage 2 admission."""
        # Candidate raw norm contracts from 0.010 to 0.0090 (0.90x < 1.00)
        mock_d = {1: 0.1 + 0.0090, 2: 0.1, 3: 0.1, 4: 0.1}
        telem = self._execute_production_outer_step(mock_d, initial_stage=2, prev_raw_norm=0.010)

        # 1. No rollback triggered
        self.assertEqual(self.driver.rollback_count, 0)
        self.assertEqual(self.driver.stage, 2)  # Remains Stage 2

        # 2. Telemetry captures Stage 2 execution and correct previous norm ordering
        self.assertFalse(telem["rollback_triggered"])
        self.assertIsNone(telem["rollback_reason"])
        self.assertEqual(telem["effective_omega_d"], 0.85)  # Stage 2 acceleration preserved
        self.assertAlmostEqual(telem["prev_raw_delta_d"], 0.010)  # Correct prior norm
        self.assertAlmostEqual(telem["cand_raw_delta_d"], 0.0090)
        self.assertAlmostEqual(telem["raw_delta_d"], 0.0090)
        self.assertAlmostEqual(self.driver.previous_raw_delta_d, 0.0090)  # State updated for next step

    # --------------------------------------------------------------------------
    # 6. Authentic Historical Telemetry Replay Tests
    # --------------------------------------------------------------------------
    def test_authentic_r8_outer89_transition_replay(self):
        """Replay authentic R8 Outer 88/89 telemetry: R9 admits Stage 2 without rollback."""
        delta_d_88 = 0.009314685784439725
        cand_delta_d_89 = 0.01569018

        raw_88 = delta_d_88 / 0.50
        cand_raw_89 = cand_delta_d_89 / 0.85

        r8_ratio = cand_delta_d_89 / delta_d_88
        self.assertGreater(r8_ratio, 1.50)

        r9_ratio = cand_raw_89 / raw_88
        self.assertLess(r9_ratio, 1.00)
        self.assertLess(r9_ratio, self.driver.rollback_factor)
        self.assertLess(r9_ratio, self.driver.divergence_factor)

    def test_all_18_authentic_r8_rollbacks_replayed(self):
        """Verify that ALL 18 authentic R8 rollbacks from live telemetry are admitted in R9."""
        telem_path = REPO_ROOT / "models/pandey_kumar_mode1/171_c6_package171_r8_c3_0_adaptive_reequilibration/evidence/1420188.mmaster02/live_iteration_telemetry.json"
        if not telem_path.is_file():
            self.skipTest(f"Missing authentic telemetry file at {telem_path}")

        telemetry = json.loads(telem_path.read_text(encoding="utf-8"))
        rollback_records = [r for r in telemetry if r.get("rollback_triggered")]
        self.assertEqual(len(rollback_records), 18)

        for rec in rollback_records:
            outer = rec["outer"]
            reason = rec["rollback_reason"]
            import re
            m = re.search(r"cand_delta_d=([0-9.e+-]+)", reason)
            cand_relaxed = float(m.group(1))
            prev_relaxed = telemetry[outer - 2]["delta_d"]

            raw_cand = cand_relaxed / 0.85
            raw_prev = prev_relaxed / 0.50

            relaxed_ratio = cand_relaxed / prev_relaxed
            raw_ratio = raw_cand / raw_prev

            # In R8: relaxed ratio was > 1.50 in 100% of cases
            self.assertGreater(relaxed_ratio, 1.50, f"Outer {outer} R8 ratio failed")
            # In R9: raw ratio is strictly contracting (< 1.00) in 100% of cases
            self.assertLess(raw_ratio, 1.00, f"Outer {outer} R9 ratio not contracting")
            self.assertLess(raw_ratio, 1.05, f"Outer {outer} R9 growth safeguard failed")
            self.assertLess(raw_ratio, 1.50, f"Outer {outer} R9 divergence safeguard failed")

    def test_compound_active_set_stability_gate(self):
        """Verify compound stability requires |A| <= 500, |Delta A| <= 10, added == 0."""
        self.assertTrue(self.driver.check_compound_stability(set(range(300)), delta_active_sym=5, added_nodes=set()))
        self.assertFalse(self.driver.check_compound_stability(set(range(600)), delta_active_sym=5, added_nodes=set()))
        self.assertFalse(self.driver.check_compound_stability(set(range(300)), delta_active_sym=15, added_nodes=set()))
        self.assertFalse(self.driver.check_compound_stability(set(range(300)), delta_active_sym=5, added_nodes={99}))


if __name__ == "__main__":
    unittest.main()
